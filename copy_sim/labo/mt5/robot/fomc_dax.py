"""Variante fomc_dax_opt (v19, PRIORITES 17/11 17 h, point 3) : HORS totaux du test, taille minimale.
Banc : labo/banc_calendrier.py (Yahoo 1994-2026, walk-forward 10 -> 2 ans, 160 reglages, Bonferroni x 24) : achat du DAX
a la cloture au comptant deux seances avant une annonce de la Fed (FOMC), sortie a la cloture au comptant du jour de
l'annonce (17 h 30 Paris, AVANT l'annonce de 20 h) : 176 trades 2004-2026, +31,5 bp, t 3,6, moities +33 / +30, p = 0,003
apres correction. Reserves : porte par 2008-2009 et 2020-2023 ; 2024-2026 a peu pres nul ; non verifiable sur la D1 du
courtier (sa bougie ferme a 23 h). ~8 trades par an. Essai en direct pour le verifier.
Regles :
  jour J = jour d'annonce d'une reunion PREVUE (liste DATES ci-dessous, tiree de labo/donnees/fomc.csv) ;
  entree : achat de GER40+ a 17 h 29-17 h 40 heure de Paris, deux jours ouvres avant J (lundi-vendredi ; feries
           allemands ignores) ;
  sortie : a 17 h 29 heure de Paris le jour J (ou des que l'heure est passee) ; jamais pendant l'annonce ;
  stop   : de secours seulement, a 3 x ATR 20 jours.
Heure de Paris calculee depuis l'heure serveur (serveur = New York + 7 h, verifie au banc intrajour) avec les regles
d'heure d'ete des Etats-Unis et de l'Europe (serveur = Paris + 1 h, ou + 2 h les semaines de decalage).
REGLE D'ARRET (ecrite avant le premier trade) : arret si la somme des 16 derniers trades passe sous -300 bp, ou si la
moyenne est negative apres 24 trades. Sa position est connue par son fichier d'etat (etat_fomc.json) ; le robot la
retire de ce que repli_ind peut reprendre."""
import datetime as dt
import json

SYMBOLE, NOM = "GER40+", "fomc_dax_opt"
DATES = ("2026-12-09", "2027-01-27", "2027-03-17", "2027-04-28", "2027-06-09", "2027-07-28", "2027-09-15",
         "2027-10-27", "2027-11-17")
HEURE_PARIS = 17 * 60 + 29           # minutes
FENETRE = 11                         # minutes pour entrer apres 17 h 29
STOP_ATR, ATR_N, SPREAD_MAX_BP, NOTIONNEL_MAX = 3.0, 20, 3.0, 30000.0
FICHIER = "etat_fomc.json"


def _dimanche(annee, mois, rang):
    """rang-ieme dimanche du mois (rang = -1 : le dernier)."""
    if rang > 0:
        d = dt.date(annee, mois, 1)
        d += dt.timedelta(days=(6 - d.weekday()) % 7)
        return d + dt.timedelta(weeks=rang - 1)
    d = dt.date(annee, mois + 1, 1) - dt.timedelta(days=1)
    return d - dt.timedelta(days=(d.weekday() - 6) % 7)


def paris(serveur):
    """Heure serveur (secondes, horloge du serveur) -> datetime naif heure de Paris."""
    s = dt.datetime(1970, 1, 1) + dt.timedelta(seconds=serveur)
    ete_us = _dimanche(s.year, 3, 2) <= s.date() < _dimanche(s.year, 11, 1)
    utc = s - dt.timedelta(hours=3 if ete_us else 2)
    ete_eu = _dimanche(utc.year, 3, -1) <= utc.date() < _dimanche(utc.year, 10, -1)
    return utc + dt.timedelta(hours=2 if ete_eu else 1)


def ouvre_avant(j, n=2):
    d = j
    while n:
        d -= dt.timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def atr(d1, n=ATR_N):
    tr = [max(d1[i][2] - d1[i][3], abs(d1[i][2] - d1[i - 1][4]), abs(d1[i][3] - d1[i - 1][4]))
          for i in range(len(d1) - n, len(d1))]
    return sum(tr) / n


class Fomc:
    def __init__(self, pont, fichier=FICHIER, dates=DATES):
        self.pont, self.fichier = pont, fichier
        self.dates = [dt.date.fromisoformat(x) for x in dates]
        self.pos, self.fait, self.bps, self.arret = None, [], [], None
        self.info, self.dernier, self.muet = None, 0, False
        try:
            with open(fichier, encoding="utf-8") as f:
                d = json.load(f)
            self.pos, self.fait, self.bps, self.arret = d.get("pos"), d.get("fait", []), d.get("bps", []), d.get("arret")
        except (OSError, ValueError):
            pass

    def sauver(self):
        try:
            with open(self.fichier, "w", encoding="utf-8") as f:
                json.dump({"pos": self.pos, "fait": self.fait, "bps": self.bps, "arret": self.arret}, f)
        except OSError:
            pass

    def tickets(self):
        return [self.pos["ticket"]] if self.pos else []

    def tour(self, ps, maintenant, peut_ouvrir):
        if maintenant - self.dernier < 60:
            return
        self.dernier = maintenant
        try:
            self.un(ps, maintenant, peut_ouvrir)
        except Exception as e:                           # ne doit jamais gener le reste du robot
            if not self.muet:
                self.muet = True
                self.pont.noter(evenement="erreur", hypothese=NOM, symbole=SYMBOLE,
                                texte=("%s: %s" % (type(e).__name__, e)).split("'")[0][:120])

    def compter(self, bp):
        if bp is None:
            return
        self.bps.append(bp)
        if self.arret is None and len(self.bps) >= 16 and sum(self.bps[-16:]) < -300:
            self.arret = "somme des 16 derniers < -300 bp"
        if self.arret is None and len(self.bps) >= 24 and sum(self.bps) < 0:
            self.arret = "moyenne negative apres 24 trades"

    def un(self, ps, maintenant, peut_ouvrir):
        p_ = paris(maintenant)
        minute = p_.hour * 60 + p_.minute
        o = self.pos
        if o and o["ticket"] not in ps:
            self.pont.noter(evenement="sortie", hypothese=NOM, symbole=SYMBOLE, raison="stop ou fermeture hors robot",
                            ticket=o["ticket"], entree=o.get("entree"), dernier_profit=o.get("profit"), essai="non prouve")
            self.pos = o = None
            self.sauver()
        if o:
            p = ps[o["ticket"]]
            o["profit"] = p.get("profit")
            j = dt.date.fromisoformat(o["j"])
            if p_.date() > j or (p_.date() == j and minute >= HEURE_PARIS):
                r = self.pont.fermer(o["ticket"])
                if r.get("ok"):
                    e, x = o.get("entree") or p.get("prix_entree"), r.get("prix_obtenu")
                    bp = round((x / e - 1) * 1e4, 1) if e and x else None
                    self.compter(bp)
                    self.pont.noter(evenement="sortie", hypothese=NOM, symbole=SYMBOLE, raison="cloture du jour de la Fed",
                                    ticket=o["ticket"], entree=e, prix_sortie=x, profit=p.get("profit"), bp=bp,
                                    arret=self.arret, essai="non prouve")
                    self.pos = None
                    self.sauver()
            return
        if self.arret or not peut_ouvrir or not HEURE_PARIS <= minute < HEURE_PARIS + FENETRE:
            return
        j = next((d for d in self.dates if ouvre_avant(d) == p_.date()), None)
        if j is None or j.isoformat() in self.fait:
            return
        px = self.pont.prix(SYMBOLE)
        if not px or px["bid"] <= 0 or not 0 <= (px["ask"] - px["bid"]) / px["bid"] * 1e4 <= SPREAD_MAX_BP:
            return
        if self.info is None:
            self.info = self.pont.symbole(SYMBOLE)
        info = self.info
        b = self.pont.bougies(SYMBOLE, "D1", ATR_N + 3)
        a = atr(b[:-1]) if b and len(b) > ATR_N + 1 else 0.0
        self.fait.append(j.isoformat())
        self.sauver()
        lots = info["lot_min"]
        notionnel = lots * info["taille_contrat"] * px["ask"]
        if notionnel > NOTIONNEL_MAX or a <= 0:
            self.pont.noter(evenement="ouverture sautee", hypothese=NOM, symbole=SYMBOLE,
                            raison="taille minimale trop grosse" if a > 0 else "ATR inconnu", notionnel=round(notionnel))
            return
        ecart = max(STOP_ATR * a, 3 * (px["ask"] - px["bid"]) + info.get("niveau_stops_points", 0) * info["point"])
        stop = round(px["bid"] - ecart, info["chiffres"])
        r = self.pont.ouvrir(SYMBOLE, "achat", lots, stop=stop, id=NOM)
        if r.get("ok") and r.get("ticket"):
            self.pos = {"ticket": r["ticket"], "entree": r.get("prix_obtenu"), "j": j.isoformat()}
            self.sauver()
        self.pont.noter(evenement="ouverture", hypothese=NOM, symbole=SYMBOLE, sens=1, ok=bool(r.get("ok")),
                        refus=r.get("refus"), lots=lots, notionnel=round(notionnel), fomc=j.isoformat(),
                        bid=px["bid"], ask=px["ask"], stop=stop, atr=round(a, 2), prix_obtenu=r.get("prix_obtenu"),
                        essai="non prouve")
