"""Hypothese rebond_nas_opt (v15, variante a part, HORS totaux du test de la semaine) : sur le Nasdaq, on prend le
contre-pied d'une journee de grande amplitude, pour une seule journee.
Banc : labo/banc_vol_retour.py (journalier long, walk-forward 1993-2026 : +10,8 bp par trade, t = 2,3, reality check
p < 0,001 sur 18 reglages) ; controle sur les bougies D1 du courtier 2018-2026 : 385 trades, +28 bp par trade, t = 2,9,
toutes les annees positives ; achats +39 bp (t = 3,0), ventes +15 bp (t = 1,0). Essai en direct, taille minimale.
Regles (bougies D1 du courtier, FERMEES) :
  signal : (haut - bas) / cloture de la veille de la derniere journee > 1,5 x la mediane des 20 journees precedentes ;
           sens = contraire du mouvement de cette journee (cloture - cloture de la veille) ;
  entree : au debut de la journee suivante (dans les 180 premieres minutes, des que le spread est normal) ;
  sortie : le meme jour, 22 h 45 apres le debut de la bougie du jour, ou des qu'une nouvelle journee commence ;
  stop   : de secours seulement, chez le courtier, a 3 x ATR 20 jours (le banc n'a pas de stop).
REGLE D'ARRET (ecrite avant le premier trade, suivie par le labo sur les notes « sortie ») : arret si la somme des
trades passe sous -1 000 bp, ou si la moyenne est negative apres 60 trades.
Sa position est connue par son fichier d'etat ; si ce fichier est perdu, repli_ind la reprend (et la sort a sa facon)."""
import json

SYMBOLE, NOM = "NAS100+", "rebond_nas_opt"
SEUIL, N_MED = 1.5, 20
STOP_ATR, ATR_N = 3.0, 20
SPREAD_MAX_BP = 3.0
ATTENTE_MAX = 180 * 60
TENUE = 22 * 3600 + 45 * 60
NOTIONNEL_MAX = 30000.0
FICHIER = "etat_rebond.json"


def signal(d1):
    """d1 = bougies D1 FERMEES (heure, ouverture, haut, bas, cloture...). Rend +1 (achat), -1 (vente) ou 0."""
    if len(d1) < N_MED + 2:
        return 0
    amp = [(d1[i][2] - d1[i][3]) / d1[i - 1][4] for i in range(len(d1) - N_MED - 1, len(d1))]
    passe = sorted(amp[:-1])
    med = (passe[N_MED // 2 - 1] + passe[N_MED // 2]) / 2.0
    if med <= 0 or amp[-1] <= SEUIL * med:
        return 0
    m = d1[-1][4] - d1[-2][4]
    return -1 if m > 0 else (1 if m < 0 else 0)


def atr(d1, n=ATR_N):
    tr = [max(d1[i][2] - d1[i][3], abs(d1[i][2] - d1[i - 1][4]), abs(d1[i][3] - d1[i - 1][4]))
          for i in range(len(d1) - n, len(d1))]
    return sum(tr) / n


class Rebond:
    def __init__(self, pont, fichier=FICHIER, symbole=SYMBOLE, nom=NOM):
        self.pont, self.fichier = pont, fichier
        self.symbole, self.nom = symbole, nom          # v19 : la meme regle sert aussi a rebond_sp_opt (SP500+)
        self.pos, self.fait, self.info, self.dernier, self.muet = None, None, None, 0, False
        try:
            with open(fichier, encoding="utf-8") as f:
                d = json.load(f)
            self.pos, self.fait = d.get("pos"), d.get("fait")
        except (OSError, ValueError):
            pass

    def sauver(self):
        try:
            with open(self.fichier, "w", encoding="utf-8") as f:
                json.dump({"pos": self.pos, "fait": self.fait}, f)
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
                self.pont.noter(evenement="erreur", hypothese=self.nom, symbole=self.symbole,
                                texte=("%s: %s" % (type(e).__name__, e)).split("'")[0][:120])

    def un(self, ps, maintenant, peut_ouvrir):
        o = self.pos
        if o and o["ticket"] not in ps:                  # stop de secours touche, ou fermee hors robot
            self.pont.noter(evenement="sortie", hypothese=self.nom, symbole=self.symbole, raison="stop ou fermeture hors robot",
                            ticket=o["ticket"], entree=o.get("entree"), dernier_profit=o.get("profit"), essai="non prouve")
            self.pos = o = None
            self.sauver()
        b = self.pont.bougies(self.symbole, "D1", 60)
        if not b or len(b) < N_MED + 3:
            return
        jour, d1 = b[-1][0], b[:-1]                      # la derniere bougie est la journee en cours
        if o:
            p = ps[o["ticket"]]
            o["profit"] = p.get("profit")
            if jour != o["jour"] or maintenant - o["jour"] >= TENUE:
                r = self.pont.fermer(o["ticket"])
                if r.get("ok"):
                    e, x = o.get("entree") or p.get("prix_entree"), r.get("prix_obtenu")
                    self.pont.noter(evenement="sortie", hypothese=self.nom, symbole=self.symbole, sens=o["sens"], ticket=o["ticket"],
                                    raison="fin de journee" if jour == o["jour"] else "nouvelle journee",
                                    entree=e, prix_sortie=x, profit=p.get("profit"),
                                    bp=round(o["sens"] * (x / e - 1) * 1e4, 1) if e and x else None, essai="non prouve")
                    self.pos = None
                    self.sauver()
            return
        if not peut_ouvrir or self.fait == jour or not 0 <= maintenant - jour <= ATTENTE_MAX:
            return
        s = signal(d1)
        if not s:
            self.fait = jour
            self.sauver()
            return
        px = self.pont.prix(self.symbole)
        if not px or px["bid"] <= 0 or not 0 <= (px["ask"] - px["bid"]) / px["bid"] * 1e4 <= SPREAD_MAX_BP:
            return                                       # spread anormal : on reessaie dans une minute
        if self.info is None:
            self.info = self.pont.symbole(self.symbole)
        info = self.info
        lots = info["lot_min"]
        notionnel = lots * info["taille_contrat"] * px["ask"]
        a = atr(d1)
        ecart = max(STOP_ATR * a, 3 * (px["ask"] - px["bid"]) + info["niveau_stops_points"] * info["point"])
        stop = round(px["bid"] - ecart if s > 0 else px["ask"] + ecart, info["chiffres"])
        self.fait = jour
        self.sauver()
        if notionnel > NOTIONNEL_MAX:
            self.pont.noter(evenement="ouverture sautee", hypothese=self.nom, symbole=self.symbole, raison="taille minimale trop grosse",
                            notionnel=round(notionnel))
            return
        r = self.pont.ouvrir(self.symbole, "achat" if s > 0 else "vente", lots, stop=stop, id=self.nom)
        if r.get("ok") and r.get("ticket"):
            self.pos = {"ticket": r["ticket"], "entree": r.get("prix_obtenu"), "jour": jour, "sens": s}
            self.sauver()
        self.pont.noter(evenement="ouverture", hypothese=self.nom, symbole=self.symbole, sens=s, ok=bool(r.get("ok")),
                        refus=r.get("refus"), lots=lots, notionnel=round(notionnel), bid=px["bid"], ask=px["ask"],
                        stop=stop, atr=round(a, 2), prix_obtenu=r.get("prix_obtenu"), essai="non prouve")
