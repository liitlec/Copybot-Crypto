"""Robot RÉEL du labo (compte STARTRADER cent), version 4 (27/11, accord écrit de Baptiste « Mets-le en place » :
sortie de bt_or_plus « point mort après le 3e renfort + paliers +2 / +4 R » du lot J, voir bt_or.niveau_protege ;
le panier ouvert à l'installation passe sous ces règles). Version 3 (26/11 soir, Lot H point A, demande écrite de Baptiste :
MISE PROPORTIONNELLE AU SOLDE). v2 : base bt_or_plus 0,05.
v3 : base bt_or_plus = 0,05 lot cent x (solde / 20 000 USC), arrondie vers le bas au pas de lot, choisie au DÉBUT de
chaque nouveau panier et gardée pour tous ses renforts (jamais changée en cours de panier), bornée par 5 x base <=
plafond local du pont (lots_max) ; règles courtes = 0,01 x (solde / 20 000), minimum 0,01, recalculées à chaque trade.
Solde = balance (sans les positions ouvertes). Chaque base choisie est notée (évènement « base »). Préparé le 25/11/2026 (PRIORITES « 25/11 23 h »).

Installé SEULEMENT par le lanceur du pont réel (`pont_mt5.py --reel`), qui refuse tout ordre sans le fichier
d'autorisation écrit par Baptiste sur son PC (voir copy_sim/forex/pont_reel.py et copy_sim/labo/LANCER_REEL.md).
Contenu (rien d'autre, ni témoin, ni variante) :
  bt_or_plus      : la mécanique bt_or (sens EMA 2 jours M5, entrées aux heures fixes, renforts tous les 0,25 ATR,
                    sortie au recul de 0,6667 ATR depuis le meilleur prix), renforts de taille croissante 1-2-3-4-5 x la
                    base, 5 positions au plus ; base 0,05 lot cent (arrondie au pas de lot du courtier, 5 x base <= plafond local du pont, 0,25 au plus) ;
  elan_m15, cassure_m15, exces_m1, exces_m5, retour_court_ar : les règles courtes de la démo, à 0,01 lot cent, mêmes
                    signaux, tenues et stops ; pause au calme comme en démo (sans variante _calme).
Le nom du symbole or (suffixe éventuel), le lot minimum, le pas de lot et la taille de contrat sont lus chez le
courtier (compte()["symbole_or"], symbole()), jamais supposés. Plafond propre : pas de règle courte au-delà de 8
positions (le pont refuse de toute façon au-delà de 10 et de 0,10 lot par position)."""
import json
import math
import time

import bt_or

VERSION = 4
SOLDE_REF = 20000.0                # USC : à ce solde, base 0,05 et règles courtes 0,01
FICHIER_ETAT = "etat_robot.json"
PAUSE = 1.0
PERIODES = ("M1", "M5", "M15")
BASE_BT, LOTS_COURTES, LOTS_MAX = 0.05, 0.01, 0.50   # v3 : LOTS_MAX = borne dure du pont ; le vrai plafond est lots_max local
SPREAD_MAX = 0.60                # en dollars (prix de l'or) : pas d'ouverture au-delà
PLAFOND_COURTES = 8
HYPOTHESES = {
    "exces_m1":    ("M1", 720, "exces", 3, -1),       # bougie M1 > 3 écarts-types : on la contre, 12 min
    "exces_m5":    ("M5", 900, "exces", 3, 1),        # bougie M5 > 3 écarts-types : on la suit, 15 min
    "cassure_m15": ("M15", 10800, "cassure", 48, 1),  # sortie de la fourchette de 12 h : on la suit, 3 h
    "elan_m15":    ("M15", 10800, "elan", 12, 1),     # sens des 3 dernières heures, 3 h
    "retour_court_ar": ("M15", 10800, "retour", 0, 1),   # retour à la moyenne, objectif milieu du range du jour
}
PAUSE_AU_CALME = {"elan_m15", "cassure_m15", "exces_m5", "exces_m1"}
# le nom de la règle voyage dans les centimes du stop (reprise après redémarrage) ; jamais 7 aux unités (paniers)
CODE = {n: c for n, c in zip(sorted(HYPOTHESES), (11, 22, 33, 44, 55))}
NOTE_DU_CODE = {c: n for n, c in CODE.items()}


def coder(stop, sens, note, chiffres=2):
    if chiffres != 2 or note not in CODE:
        return stop
    c = int(round(stop * 100))
    d = (c - CODE[note]) % 100 if sens > 0 else (CODE[note] - c) % 100
    return round((c - d) / 100.0 if sens > 0 else (c + d) / 100.0, 2)


def regle(nom_regle, k, b):
    """Signal brut +1 / -1 / 0 sur des bougies FERMÉES b (anciennes -> récentes). Copie des règles de la démo."""
    c = [x[4] for x in b]
    if nom_regle == "elan":
        if len(c) < k + 1:
            return 0
        d = c[-1] - c[-1 - k]
        return (d > 0) - (d < 0)
    if nom_regle == "cassure":
        if len(b) < k + 1:
            return 0
        haut = max(x[2] for x in b[-k - 1:-1])
        bas = min(x[3] for x in b[-k - 1:-1])
        return (c[-1] > haut) - (c[-1] < bas)
    if nom_regle == "retour":
        if len(c) < 22:
            return 0
        v = c[-21:-1]
        m = sum(v) / 20
        e = (sum((x - m) ** 2 for x in v) / 19) ** 0.5
        if e > 0 and abs(c[-1] - m) > 2.5 * e:
            return -1 if c[-1] > m else 1
        jour = b[-1][0] // 86400
        avant = [x for x in b[:-2] if x[0] // 86400 == jour]
        if len(avant) >= 4 and b[-2][0] // 86400 == jour:
            h, l = max(x[2] for x in avant), min(x[3] for x in avant)
            if b[-2][2] > h and c[-1] < h:
                return -1
            if b[-2][3] < l and c[-1] > l:
                return 1
        return 0
    if nom_regle == "exces":
        if len(c) < 102:
            return 0
        r = [c[i] / c[i - 1] - 1 for i in range(len(c) - 101, len(c))]
        passe, dernier = r[:-1], r[-1]
        m = sum(passe) / len(passe)
        e = (sum((x - m) ** 2 for x in passe) / (len(passe) - 1)) ** 0.5
        if e <= 0:
            return 0
        z = dernier / e
        return (z > k) - (z < -k)
    return 0


def signal(nom, b):
    _, _, nom_regle, k, sens = HYPOTHESES[nom]
    return sens * regle(nom_regle, k, b)


def agite(h1):
    """Vrai si le mouvement H1 moyen des 24 dernières heures dépasse sa médiane sur ~60 jours (copie de la démo)."""
    c = [x[4] for x in h1]
    if len(c) < 750:
        return None
    r = [abs(math.log(c[i] / c[i - 1])) for i in range(1, len(c))]
    v, somme = [], sum(r[:24])
    v.append(somme / 24)
    for i in range(24, len(r)):
        somme += r[i] - r[i - 24]
        v.append(somme / 24)
    passe = sorted(v[-1441:-1])
    if len(passe) < 700:
        return None
    return v[-1] > passe[len(passe) // 2]


def ecart_stop(b, minimum):
    ext = b[-48:]
    a = sum(x[2] - x[3] for x in ext) / max(1, len(ext))
    return max(4 * a, minimum)


def sur_grille(lots, lot_min, pas):
    """Lot arrondi au pas du courtier (vers le bas), None s'il passe sous le minimum."""
    pas = pas or 0.01
    v = round(math.floor(lots / pas + 1e-9) * pas, 8)
    return v if v >= lot_min - 1e-9 else None


class PanierProp(bt_or.PanierBT):
    """bt_or_plus dont la base est choisie à l'ouverture de CHAQUE panier (lots0 du panier, gardé pour ses renforts et
    pour le calcul du R à la clôture). Un panier repris après redémarrage retrouve sa base par sa 1re position."""

    def __init__(self, pont, robot, **k):
        super().__init__(pont, **k)
        self.robot = robot

    def _ouvre(self, p, s, niveau, chiffres):
        if not p.get("lots0"):
            c = self.pont.compte()
            base = self.robot.base_bt(c)
            if base is None:
                self.robot._une_fois("base", evenement="attente", hypothese=self.nom,
                                     raison="base sous le lot minimum ou solde inconnu : pas de nouveau panier")
                return False
            p["lots0"] = base
            self.pont.noter(evenement="base", hypothese=self.nom, sens=s, base=base, solde=c.get("solde"),
                            plafond=self.robot.plafond(c), lots_max_panier=round(5 * base, 2))
        self.lots = p["lots0"]
        return super()._ouvre(p, s, niveau, chiffres)

    def _cloture(self, cle, raison, ps):
        self.lots = self.paniers[cle].get("lots0") or self.lots
        super()._cloture(cle, raison, ps)

    def completer(self, ps):
        """Paniers ouverts avant la v3 (sans lots0) : base retrouvée par la plus petite position du panier."""
        for p in self.paniers.values():
            if not p.get("lots0"):
                tailles = [ps[t].get("lots") for t in p["tickets"] if t in ps and ps[t].get("lots")]
                if tailles:
                    p["lots0"] = min(tailles)
                    self.sauver()

    def adopter(self, ps, m5, d1):
        super().adopter(ps, m5, d1)
        for p in self.paniers.values():
            if not p.get("lots0"):
                tailles = [ps[t].get("lots") for t in p["tickets"] if t in ps and ps[t].get("lots")]
                if tailles:
                    p["lots0"] = min(tailles)              # la 1re position du panier = 1 x base
        self.sauver()


class Robot:
    def __init__(self, pont, fichier=FICHIER_ETAT):
        self.pont, self.fichier = pont, fichier
        self.vu, self.ouvert, self.essais_orph = {}, {}, {}
        self.sym, self.info, self.btp, self.lots_c = None, None, None, None
        self.calme, self.calme_vu, self.muet = None, 0, set()
        try:
            with open(self.fichier, encoding="utf-8") as f:
                self.ouvert = {k: v for k, v in json.load(f).get("ouvert", {}).items() if k in HYPOTHESES}
        except (OSError, ValueError):
            self.ouvert = {}

    def sauver(self):
        try:
            with open(self.fichier, "w", encoding="utf-8") as f:
                json.dump({"ouvert": self.ouvert}, f)
        except OSError:
            pass

    def _une_fois(self, cle, **note):
        if cle not in self.muet:
            self.muet.add(cle)
            self.pont.noter(**note)

    # -------------------------------------------------- symbole et tailles, lus chez le courtier
    def preparer(self):
        if self.sym is not None:
            return True
        c = self.pont.compte()
        sym = c.get("symbole_or")
        if not sym:
            self._une_fois("symbole", evenement="attente", raison="symbole or inconnu (compte non autorise ?)",
                           arret=c.get("arret"))
            return False
        info = self.pont.symbole(sym)
        self.sym, self.info = sym, info
        bt_or.SYMBOLE = sym
        self.btp = PanierProp(self.pont, self, fichier="etat_bt_plus.json", symbole=sym, nom="bt_or_plus",
                              lots=None, taille=info["taille_contrat"], max_pos=5, croissant=True, protege=True)
        self.pont.noter(evenement="sortie v4", hypothese="bt_or_plus", regle="point mort des 4 positions + paliers +2/+4 R "
                        "(recul 0,6667 -> 0,5 -> 0,35 ATR)", paniers_en_cours=len(self.btp.paniers),
                        note="les paniers en cours (ou repris au premier tour) passent sous ces regles")
        b, lc, plaf, solde = self.base_bt(c), self.lots_courtes(c), self.plafond(c), c.get("solde")
        self.lots_c = lc
        self.pont.noter(evenement="tailles", symbole=sym, lot_min=info["lot_min"], pas_lot=info["pas_lot"],
                        taille_contrat=info["taille_contrat"], solde=solde, plafond=plaf, base_bt_or_plus=b,
                        lots_regles_courtes=lc, regle="base = 0,05 x solde / 20 000, recalculee a chaque panier")
        return True

    # -------------------------------------------------- v3 : mise proportionnelle au solde
    def plafond(self, c):
        lm = c.get("lots_max")
        if isinstance(lm, (int, float)) and not isinstance(lm, bool) and lm > 0:
            return min(float(lm), LOTS_MAX)
        return 0.10                                        # pont sans plafond annoncé : prudence

    def _solde(self, c):
        s = c.get("solde")
        return float(s) if isinstance(s, (int, float)) and not isinstance(s, bool) and s > 0 else None

    def base_bt(self, c=None):
        """Base du prochain panier bt_or_plus, ou None (solde inconnu, ou base sous le lot minimum)."""
        c = c or self.pont.compte()
        solde = self._solde(c)
        if solde is None or self.info is None:
            return None
        lm, pas = self.info["lot_min"], self.info["pas_lot"]
        plaf = self.plafond(c)
        base = sur_grille(BASE_BT * solde / SOLDE_REF, lm, pas)
        if base is not None and 5 * base > plaf + 1e-9:
            base = sur_grille(plaf / 5, lm, pas)
        return base

    def lots_courtes(self, c=None):
        """Lot d'une règle courte : 0,01 x solde / 20 000, au moins 0,01 (ou le minimum du courtier), sous le plafond."""
        c = c or self.pont.compte()
        solde = self._solde(c)
        if self.info is None:
            return None
        lm, pas = self.info["lot_min"], self.info["pas_lot"]
        v = sur_grille(LOTS_COURTES * (solde or SOLDE_REF) / SOLDE_REF, lm, pas)
        v = max(v or 0.0, sur_grille(LOTS_COURTES, lm, pas) or 0.0) or None
        if v is not None and v > self.plafond(c) + 1e-9:
            v = sur_grille(self.plafond(c), lm, pas)
        return v

    def heure(self):
        return self.pont.prix(self.sym)["heure_serveur"]

    # -------------------------------------------------- positions
    def reconcilier(self):
        ps = {p["ticket"]: p for p in self.pont.positions()}
        if self.btp:
            self.btp.completer(ps)
        connus = set(self.btp.tickets()) if self.btp else set()
        for nom, o in list(self.ouvert.items()):
            p = ps.get(o["ticket"])
            if p is None:
                self.pont.noter(evenement="sortie", hypothese=nom, raison="stop ou fermeture hors robot",
                                ticket=o["ticket"], sens=o["sens"], entree=o.get("entree"), dernier_profit=o.get("profit"))
                del self.ouvert[nom]
                self.sauver()
            else:
                o["profit"] = p["profit"]
                connus.add(o["ticket"])
        for t, p in ps.items():                          # reprise d'une règle courte par le code de son stop
            if t in connus or p.get("symbole") != self.sym or not p.get("stop"):
                continue
            nom = NOTE_DU_CODE.get(int(round(p["stop"] * 100)) % 100)
            if nom and nom not in self.ouvert:
                self.ouvert[nom] = {"ticket": t, "sens": 1 if p["sens"] == "achat" else -1,
                                    "sortie": (p.get("heure_serveur") or 0) + HYPOTHESES[nom][1] - 2,
                                    "entree": p.get("prix_entree"), "profit": p.get("profit") or 0.0}
                connus.add(t)
                self.pont.noter(evenement="reprise", hypothese=nom, ticket=t)
                self.sauver()
        inconnus = {t: p for t, p in ps.items() if t not in connus and p.get("stop")}
        if inconnus and self.btp:                        # paniers repris après un redémarrage (stop marqué 97)
            try:
                m5, d1 = self.pont.bougies(self.sym, "M5", 3000), self.pont.bougies(self.sym, "D1", 30)
            except Exception:
                m5 = d1 = None
            if m5 and d1:
                self.btp.adopter(inconnus, m5[:-1], d1[:-1])
                connus.update(self.btp.tickets())
            else:
                connus.update(t for t, p in inconnus.items() if self.btp.candidat(p))
        for t, p in ps.items():
            if t not in connus:
                if time.time() - self.essais_orph.get(t, 0) < 60:
                    continue
                self.essais_orph[t] = time.time()
                r = self.pont.fermer(t)
                self.pont.noter(evenement="orpheline fermee", ticket=t, profit=p["profit"], ok=r.get("ok"))
        return ps

    def sorties(self, maintenant, ps):
        for nom, o in list(self.ouvert.items()):
            if maintenant >= o["sortie"]:
                p = ps.get(o["ticket"], {})
                r = self.pont.fermer(o["ticket"])
                if r.get("ok"):
                    self.pont.noter(evenement="sortie", hypothese=nom, raison="temps", ticket=o["ticket"],
                                    sens=o["sens"], entree=p.get("prix_entree", o.get("entree")),
                                    prix_sortie=r.get("prix_obtenu"), profit=p.get("profit"))
                    del self.ouvert[nom]
                    self.sauver()
                else:
                    o["sortie"] = maintenant + 60

    def ouvrir(self, nom, sens, b, maintenant):
        px = self.pont.prix(self.sym)
        spread = px["ask"] - px["bid"]
        if spread > SPREAD_MAX or spread < 0:
            self.pont.noter(evenement="ouverture sautee", hypothese=nom, raison="spread", spread=round(spread, 3))
            return None
        info = self.info
        mini = max(3.0, 3 * spread + info.get("niveau_stops_points", 0) * info["point"])
        e = ecart_stop(b, mini)
        ch = info["chiffres"]
        stop = round(px["bid"] - e, ch) if sens > 0 else round(px["ask"] + e, ch)
        objectif = None
        if nom == "retour_court_ar":
            jour = b[-1][0] // 86400
            auj = [x for x in b if x[0] // 86400 == jour] or b[-4:]
            mil = round((max(x[2] for x in auj) + min(x[3] for x in auj)) / 2, ch)
            objectif = mil if (sens > 0 and mil > px["ask"] + spread) or (sens < 0 and mil < px["bid"] - spread) else None
            ext = max(x[2] for x in b[-2:]) + 0.5 if sens < 0 else min(x[3] for x in b[-2:]) - 0.5
            stop = round(min(ext, px["bid"] - mini) if sens > 0 else max(ext, px["ask"] + mini), ch)
        stop = coder(stop, sens, nom, ch)
        self.lots_c = self.lots_courtes()               # v3 : proportionnel au solde, à chaque trade
        if self.lots_c is None:
            return None
        r = self.pont.ouvrir(self.sym, "achat" if sens > 0 else "vente", self.lots_c, stop=stop, objectif=objectif, id=nom)
        if r.get("ok") and r.get("ticket"):
            self.ouvert[nom] = {"ticket": r["ticket"], "sens": sens, "sortie": maintenant + HYPOTHESES[nom][1] - 2,
                                "entree": r.get("prix_obtenu"), "profit": 0.0}
            self.sauver()
        self.pont.noter(evenement="ouverture", hypothese=nom, sens=sens, ok=bool(r.get("ok")), refus=r.get("refus"),
                        bid=px["bid"], ask=px["ask"], stop=stop, lots=self.lots_c, prix_obtenu=r.get("prix_obtenu"))
        return r

    def regime(self, maintenant, bougies=None):
        if maintenant - self.calme_vu < 900:
            return
        self.calme_vu = maintenant
        try:
            h1 = bougies.get("H1") if bougies else self.pont.bougies(self.sym, "H1", 1500)
            a = agite(h1[:-1]) if h1 else None
        except Exception:
            a = None
        nouveau = None if a is None else (not a)
        if nouveau != self.calme:
            self.pont.noter(evenement="regime", calme=nouveau, en_pause=sorted(PAUSE_AU_CALME) if nouveau else [])
        self.calme = nouveau

    # -------------------------------------------------- un tour
    def tour(self, bougies=None):
        if not self.preparer():
            return
        maintenant = self.heure()
        ps = self.reconcilier()
        self.sorties(maintenant, ps)
        px = self.pont.prix(self.sym)
        if self.btp:
            self.btp.surveiller(ps, px)
        permis = bool(self.pont.compte().get("ordres_autorises")) and not self.pont.garde_fou().get("ouvertures_bloquees")
        if not permis:
            return
        hs = time.gmtime(maintenant)
        if (hs.tm_hour == 23 and hs.tm_min >= 50) or hs.tm_hour == 0 or (hs.tm_hour == 1 and hs.tm_min < 10):
            return                                       # fermeture nocturne de l'or : pas d'ouverture
        self.regime(maintenant, bougies)
        spread_ok = 0 <= px["ask"] - px["bid"] <= SPREAD_MAX
        for periode in PERIODES:
            b = bougies[periode] if bougies else self.pont.bougies(self.sym, periode, 130)
            b = b[:-1]
            if len(b) < 20:
                continue
            derniere = b[-1][0]
            if periode not in self.vu:
                self.vu[periode] = derniere
                continue
            if derniere == self.vu[periode]:
                continue
            self.vu[periode] = derniere
            if periode == "M5" and self.btp:
                long5 = bougies.get("M5long") if bougies else self.pont.bougies(self.sym, "M5", 3000)
                d1 = bougies.get("D1") if bougies else self.pont.bougies(self.sym, "D1", 30)
                if long5 and d1:
                    self.btp.bougie(long5[:-1], d1[:-1], spread_ok, self.info["chiffres"])
            if self.lots_c is None:
                self._une_fois("lots", evenement="attente", raison="0,01 lot sous le minimum du courtier : regles courtes coupees")
                continue
            for nom, hyp in HYPOTHESES.items():
                if hyp[0] != periode or nom in self.ouvert:
                    continue
                if self.calme and nom in PAUSE_AU_CALME:
                    continue
                if len(self.pont.positions()) >= PLAFOND_COURTES:
                    continue
                s = signal(nom, b)
                if s:
                    self.ouvrir(nom, s, b, maintenant)


def lancer(pont):
    robot = Robot(pont)
    pont.noter(evenement="demarrage", version=VERSION, mode="reel", hypotheses=sorted(HYPOTHESES) + ["bt_or_plus"],
               repris=sorted(robot.ouvert))
    erreurs = 0
    while not pont.arret_demande():
        try:
            robot.tour()
            erreurs = 0
        except Exception as e:
            erreurs += 1
            if erreurs <= 3 or erreurs % 100 == 0:
                pont.noter(evenement="erreur", texte=("%s: %s" % (type(e).__name__, e)).split("'")[0][:160], suite=erreurs)
            time.sleep(min(60, 5 * erreurs))
        time.sleep(PAUSE)
    pont.noter(evenement="arret demande")
    while True:
        time.sleep(30)
