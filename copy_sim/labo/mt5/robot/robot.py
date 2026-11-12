"""Robot du labo, version 6 : scalp presque continu sur la DEMO, XAUUSD, 0,01 lot par hypothese (essais NON prouves).

Neuf hypotheses en parallele, une position au plus chacune, stop chez le courtier sur chaque position, sortie au temps.
Trois tournent en continu en M1 (dont le temoin au hasard, a la meme cadence), six attendent un evenement.
ecart_midi_m5 vient de la grille du banc E (labo/banc_grille.py) : seul groupe au-dessus du hasard au reglage.
Le banc D (labo/banc_or.py) ne trouve d'avantage prouve pour aucune : le but est d'apprendre du vrai marche.
Chaque ouverture et chaque sortie est notee par pont.noter avec le nom de l'hypothese et l'heure du serveur."""
import json
import math
import random
import time

import bt_or

VERSION = 7
SYMBOLE = "XAUUSD"
LOTS = 0.01
SPREAD_MAX = 0.60          # en dollars : pas d'ouverture si le spread depasse (normal ~0,19)
FICHIER_ETAT = "etat_robot.json"
PAUSE = 1.0
PERIODES = ("M1", "M5", "M15")
#  nom : (periode, tenue en secondes, regle, reglage, sens : +1 on suit le signal, -1 on le contre)
# 12/11 (demande de Baptiste) : hypotheses arretees, plus aucune ouverture ; les positions en cours sortent normalement
ETEINTES = {"retour_m1"}   # retour_m1 : -0,55 $ par trade sur 277 trades, nettement pire que le temoin
HYPOTHESES = {
    "hasard_m1":   ("M1", 300, "hasard", 0, 1),       # temoin : pile ou face, meme cadence que les deux suivantes
    "elan_m1":     ("M1", 300, "elan", 3, 1),         # sens des 3 dernieres minutes
    "retour_m1":   ("M1", 300, "elan", 1, -1),        # contre la derniere minute
    "exces_m1":    ("M1", 720, "exces", 3, -1),       # bougie M1 > 3 ecarts-types : on la contre, 12 min
    "fcassure_m1": ("M1", 180, "cassure", 48, -1),    # sortie de la fourchette de 48 min : on la contre, 3 min
    "exces_m5":    ("M5", 900, "exces", 3, 1),        # bougie M5 > 3 ecarts-types : on la suit, 15 min
    "cassure_m15": ("M15", 10800, "cassure", 48, 1),  # sortie de la fourchette de 12 h : on la suit, 3 h
    "elan_m15":    ("M15", 10800, "elan", 12, 1),     # sens des 3 dernieres heures, 3 h
    "ecart_midi_m5": ("M5", 900, "ecart", 20, -1),    # a plus de 2 ecarts-types de la moyenne de 20 bougies M5 :
}                                                     # on parie sur le retour, 15 min, de 12 h a 15 h serveur seulement
HEURES = {"ecart_midi_m5": (12, 13, 14)}              # heures du serveur (Paris + 1 h) ou l'hypothese a le droit d'ouvrir


def regle(nom_regle, k, b, hasard=random):
    """Signal brut +1 / -1 / 0 d'une regle sur des bougies FERMEES b (anciennes -> recentes)."""
    c = [x[4] for x in b]
    if nom_regle == "hasard":
        return hasard.choice((-1, 1))
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
    if nom_regle == "ecart":
        if len(c) < k:
            return 0
        v = c[-k:]
        m = sum(v) / k
        e = (sum((x - m) ** 2 for x in v) / (k - 1)) ** 0.5
        if e <= 0:
            return 0
        z = (c[-1] - m) / e
        return (z > 2) - (z < -2)
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


def signal(nom, b, hasard=random):
    """Signal final d'une hypothese (regle x sens)."""
    _, _, nom_regle, k, sens = HYPOTHESES[nom]
    return sens * regle(nom_regle, k, b, hasard)


def agite(h1):
    """Regime de l'or : vrai si le mouvement H1 moyen des 24 dernieres heures depasse sa mediane sur ~60 jours.
    h1 = bougies H1 FERMEES. Rend None s'il n'y a pas assez d'historique. (Banc : agite +3,8 bp, calme +0,9 bp.)"""
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
    """Stop de secours : 4 fois l'amplitude moyenne des 48 dernieres bougies, au moins `minimum` dollars."""
    ext = b[-48:]
    a = sum(x[2] - x[3] for x in ext) / max(1, len(ext))
    return max(4 * a, minimum)


class Robot:
    def __init__(self, pont, hasard=None, fichier=FICHIER_ETAT):
        self.pont, self.hasard, self.fichier = pont, hasard or random.Random(), fichier
        self.vu = {}            # periode -> heure de la derniere bougie fermee deja traitee
        self.ouvert = {}        # hypothese -> {"ticket", "sens", "sortie", "entree", "profit"}
        self.info = None
        self.bt = bt_or.PanierBT(pont)
        self.charger()

    # -------------------------------------------------- memoire (fichier dans le dossier du robot)
    def charger(self):
        try:
            with open(self.fichier, encoding="utf-8") as f:
                d = json.load(f)
            self.ouvert = {k: v for k, v in d.get("ouvert", {}).items() if k in HYPOTHESES}
        except (OSError, ValueError):
            self.ouvert = {}

    def sauver(self):
        try:
            with open(self.fichier, "w", encoding="utf-8") as f:
                json.dump({"ouvert": self.ouvert}, f)
        except OSError:
            pass

    def heure(self):
        return self.pont.prix(SYMBOLE)["heure_serveur"]

    # -------------------------------------------------- positions
    def reconcilier(self):
        """Aligne la memoire sur le compte : note les stops touches, ferme les positions orphelines."""
        ps = {p["ticket"]: p for p in self.pont.positions()}
        connus = set(self.bt.tickets())                 # les paniers bt_or sont geres par bt_or.py
        for nom, o in list(self.ouvert.items()):
            p = ps.get(o["ticket"])
            if p is None:
                self.pont.noter(evenement="sortie", hypothese=o.get("note", nom), raison="stop ou fermeture hors robot",
                                ticket=o["ticket"], sens=o["sens"], entree=o.get("entree"),
                                dernier_profit=o.get("profit"), essai="non prouve")
                del self.ouvert[nom]
                self.sauver()
            else:
                o["profit"] = p["profit"]
                connus.add(o["ticket"])
        for t, p in ps.items():
            if t not in connus:
                r = self.pont.fermer(t)
                self.pont.noter(evenement="orpheline fermee", ticket=t, profit=p["profit"], ok=r.get("ok"))
        return ps

    def sorties(self, maintenant, ps):
        for nom, o in list(self.ouvert.items()):
            if maintenant >= o["sortie"]:
                p = ps.get(o["ticket"], {})
                r = self.pont.fermer(o["ticket"])
                if r.get("ok"):
                    self.pont.noter(evenement="sortie", hypothese=o.get("note", nom), raison="temps", ticket=o["ticket"],
                                    sens=o["sens"], entree=p.get("prix_entree", o.get("entree")),
                                    h_serveur=time.gmtime(maintenant).tm_hour,
                                    prix_sortie=r.get("prix_obtenu"), profit=p.get("profit"), essai="non prouve")
                    del self.ouvert[nom]
                    self.sauver()
                else:                                    # marche ferme ou refus : on reessaie dans une minute
                    o["sortie"] = maintenant + 60

    def etiquette(self, nom, sens=0):
        """Nom sous lequel le trade est note. Le candidat de midi est note selon le regime de l'or du moment
        (agite / calme) et selon qu'il va dans le sens de la tendance de 20 h (_f) ou contre (_c)."""
        if nom != "ecart_midi_m5":
            return nom
        try:
            a = agite(self.pont.bougies(SYMBOLE, "H1", 1500)[:-1])
        except Exception:
            a = None
        base = {True: "midi_agite", False: "midi_calme"}.get(a, nom)
        try:
            c = [x[4] for x in self.pont.bougies(SYMBOLE, "M5", 245)[:-1]]
            fond = (c[-1] > sum(c[-240:]) / 240) - (c[-1] < sum(c[-240:]) / 240) if len(c) >= 240 else 0
        except Exception:
            fond = 0
        if a is None or not fond or not sens:
            return base
        return base + ("_f" if sens == fond else "_c")

    def ouvrir(self, nom, sens, b, maintenant):
        px = self.pont.prix(SYMBOLE)
        spread = px["ask"] - px["bid"]
        if spread > SPREAD_MAX or spread < 0:
            self.pont.noter(evenement="ouverture sautee", hypothese=nom, raison="spread", spread=round(spread, 3))
            return None
        if self.info is None:
            self.info = self.pont.symbole(SYMBOLE)
        mini = max(3.0, 3 * spread + self.info["niveau_stops_points"] * self.info["point"])
        e = ecart_stop(b, mini)
        ch = self.info["chiffres"]
        stop = round(px["bid"] - e, ch) if sens > 0 else round(px["ask"] + e, ch)
        nom_note = self.etiquette(nom, sens)
        r = self.pont.ouvrir(SYMBOLE, "achat" if sens > 0 else "vente", LOTS, stop=stop, id=nom_note)
        if r.get("ok") and r.get("ticket"):
            self.ouvert[nom] = {"ticket": r["ticket"], "sens": sens, "sortie": maintenant + HYPOTHESES[nom][1] - 2,
                                "entree": r.get("prix_obtenu"), "profit": 0.0, "note": nom_note}
            self.sauver()
        self.pont.noter(evenement="ouverture", hypothese=nom_note, sens=sens, ok=bool(r.get("ok")), refus=r.get("refus"),
                        bid=px["bid"], ask=px["ask"], spread=round(spread, 3), stop=stop,
                        h_serveur=time.gmtime(maintenant).tm_hour,
                        prix_obtenu=r.get("prix_obtenu"), essai="non prouve")
        return r

    # -------------------------------------------------- un tour
    def tour(self, bougies=None):
        """Un passage de boucle. `bougies` (periode -> liste) sert aux essais ; sinon lues chez le courtier."""
        maintenant = self.heure()
        ps = self.reconcilier()
        self.sorties(maintenant, ps)
        px = self.pont.prix(SYMBOLE)
        self.bt.surveiller(ps, px)
        if not self.pont.compte().get("ordres_autorises") or self.pont.garde_fou().get("ouvertures_bloquees"):
            return
        hs = time.gmtime(maintenant)
        if (hs.tm_hour == 23 and hs.tm_min >= 50) or hs.tm_hour == 0 or (hs.tm_hour == 1 and hs.tm_min < 10):
            return                                       # fermeture nocturne de l'or : trous de prix, pas d'ouverture
        for periode in PERIODES:
            b = bougies[periode] if bougies else self.pont.bougies(SYMBOLE, periode, 130)
            b = b[:-1]                                   # la derniere est en cours de formation
            if len(b) < 20:
                continue
            derniere = b[-1][0]
            if periode not in self.vu:                   # premier tour : on ne trade pas une bougie deja ancienne
                self.vu[periode] = derniere
                continue
            if derniere == self.vu[periode]:
                continue
            self.vu[periode] = derniere
            if periode == "M5":                          # panier bt_or : entrees et ajouts a chaque bougie M5 fermee
                long5 = bougies.get("M5long") if bougies else self.pont.bougies(SYMBOLE, "M5", 3000)
                d1 = bougies.get("D1") if bougies else self.pont.bougies(SYMBOLE, "D1", 30)
                if long5 and d1:
                    self.bt.bougie(long5[:-1], d1[:-1], 0 <= px["ask"] - px["bid"] <= SPREAD_MAX)
            for nom, hyp in HYPOTHESES.items():
                if hyp[0] != periode or nom in self.ouvert or nom in ETEINTES:
                    continue
                if nom in HEURES and time.gmtime(maintenant).tm_hour not in HEURES[nom]:
                    continue
                s = signal(nom, b, self.hasard)
                if s:
                    self.ouvrir(nom, s, b, maintenant)


def lancer(pont):
    robot = Robot(pont)
    pont.noter(evenement="demarrage", version=VERSION, hypotheses=sorted(HYPOTHESES), lots=LOTS, repris=sorted(robot.ouvert))
    erreurs = 0
    while not pont.arret_demande():
        try:
            robot.tour()
            erreurs = 0
        except Exception as e:                           # ne jamais planter : on note et on attend
            erreurs += 1
            if erreurs <= 3 or erreurs % 100 == 0:
                texte = ("%s: %s" % (type(e).__name__, e)).split("'")[0][:160]      # sans chemin de fichier
                pont.noter(evenement="erreur", texte=texte, suite=erreurs)
            time.sleep(min(60, 5 * erreurs))
        time.sleep(PAUSE)
    pont.noter(evenement="arret demande")
    while True:                                          # STOP_PONT : on ne fait plus rien, sans revenir
        time.sleep(30)
