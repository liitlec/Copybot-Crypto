"""Robot du labo, version 1 : essais en direct sur la DEMO, XAUUSD, 0,01 lot par hypothese (essais NON prouves).

Quatre hypotheses, une position au plus chacune, chaque position a un stop chez le courtier et sort au temps :
  hasard_m15   : pile ou face a chaque bougie M15, tenue 5 min. Temoin + mesure d'execution (spread, glissement).
  elan_m15     : sens du rendement des 12 dernieres bougies M15, tenue 3 h.
  cassure_m15  : cloture M15 au-dela du plus haut / plus bas des 48 bougies precedentes, on suit, tenue 3 h.
  exces_m5     : bougie M5 de plus de 3 ecarts-types (sur 100 bougies), on suit, tenue 15 min.
Le banc D (labo/banc_or.py) ne trouve d'avantage prouve pour aucune : le but est d'apprendre du vrai marche.
Chaque ouverture et chaque sortie est notee par pont.noter avec le nom de l'hypothese."""
import json
import random
import time

SYMBOLE = "XAUUSD"
LOTS = 0.01
SPREAD_MAX = 0.60          # en dollars : pas d'ouverture si le spread depasse (normal ~0,19)
FICHIER_ETAT = "etat_robot.json"
PAUSE = 2.0
#            nom            periode  tenue (s)
HYPOTHESES = {"hasard_m15": ("M15", 300), "elan_m15": ("M15", 10800), "cassure_m15": ("M15", 10800),
              "exces_m5": ("M5", 900)}


def signal(nom, b, hasard=random):
    """Signal +1 / -1 / 0 d'une hypothese sur des bougies FERMEES b (anciennes -> recentes)."""
    c = [x[4] for x in b]
    if nom == "hasard_m15":
        return hasard.choice((-1, 1))
    if nom == "elan_m15":
        if len(c) < 13:
            return 0
        d = c[-1] - c[-13]
        return (d > 0) - (d < 0)
    if nom == "cassure_m15":
        if len(b) < 49:
            return 0
        haut = max(x[2] for x in b[-49:-1])
        bas = min(x[3] for x in b[-49:-1])
        return (c[-1] > haut) - (c[-1] < bas)
    if nom == "exces_m5":
        if len(c) < 102:
            return 0
        r = [c[i] / c[i - 1] - 1 for i in range(len(c) - 101, len(c))]
        passe, dernier = r[:-1], r[-1]
        m = sum(passe) / len(passe)
        e = (sum((x - m) ** 2 for x in passe) / (len(passe) - 1)) ** 0.5
        if e <= 0:
            return 0
        z = dernier / e
        return (z > 3) - (z < -3)
    return 0


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
        connus = set()
        for nom, o in list(self.ouvert.items()):
            p = ps.get(o["ticket"])
            if p is None:
                self.pont.noter(evenement="sortie", hypothese=nom, raison="stop ou fermeture hors robot",
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
                    self.pont.noter(evenement="sortie", hypothese=nom, raison="temps", ticket=o["ticket"],
                                    sens=o["sens"], entree=p.get("prix_entree", o.get("entree")),
                                    prix_sortie=r.get("prix_obtenu"), profit=p.get("profit"), essai="non prouve")
                    del self.ouvert[nom]
                    self.sauver()
                else:                                    # marche ferme ou refus : on reessaie dans une minute
                    o["sortie"] = maintenant + 60

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
        r = self.pont.ouvrir(SYMBOLE, "achat" if sens > 0 else "vente", LOTS, stop=stop, id=nom)
        if r.get("ok") and r.get("ticket"):
            self.ouvert[nom] = {"ticket": r["ticket"], "sens": sens, "sortie": maintenant + HYPOTHESES[nom][1],
                                "entree": r.get("prix_obtenu"), "profit": 0.0}
            self.sauver()
        self.pont.noter(evenement="ouverture", hypothese=nom, sens=sens, ok=bool(r.get("ok")), refus=r.get("refus"),
                        bid=px["bid"], ask=px["ask"], spread=round(spread, 3), stop=stop,
                        prix_obtenu=r.get("prix_obtenu"), essai="non prouve")
        return r

    # -------------------------------------------------- un tour
    def tour(self, bougies=None):
        """Un passage de boucle. `bougies` (periode -> liste) sert aux essais ; sinon lues chez le courtier."""
        maintenant = self.heure()
        ps = self.reconcilier()
        self.sorties(maintenant, ps)
        if not self.pont.compte().get("ordres_autorises") or self.pont.garde_fou().get("ouvertures_bloquees"):
            return
        for periode in ("M5", "M15"):
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
            for nom, (per, _) in HYPOTHESES.items():
                if per != periode or nom in self.ouvert:
                    continue
                s = signal(nom, b, self.hasard)
                if s:
                    self.ouvrir(nom, s, b, maintenant)


def lancer(pont):
    robot = Robot(pont)
    pont.noter(evenement="demarrage", version=1, hypotheses=sorted(HYPOTHESES), lots=LOTS, repris=sorted(robot.ouvert))
    erreurs = 0
    while not pont.arret_demande():
        try:
            robot.tour()
            erreurs = 0
        except Exception as e:                           # ne jamais planter : on note et on attend
            erreurs += 1
            if erreurs <= 3 or erreurs % 100 == 0:
                pont.noter(evenement="erreur", texte=("%s: %s" % (type(e).__name__, e))[:200], suite=erreurs)
            time.sleep(min(60, 5 * erreurs))
        time.sleep(PAUSE)
    pont.noter(evenement="arret demande")
    while True:                                          # STOP_PONT : on ne fait plus rien, sans revenir
        time.sleep(30)
