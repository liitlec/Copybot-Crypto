"""Hypothese repli_ind : la regle de BlockRange refaite (achat d'un indice apres un repli court, en tendance haussiere).
Banc : labo/banc_blockrange_ohlc.py (5 indices, 2000-2026, couts compris) : +20 bp par trade au reglage (519 trades)
ET au verdict 2016-2026 (454 trades, t = 2,3), 66 % de gagnants, ~4 nuits ; bougies du courtier : NAS100+ +25 bp
(62 trades), SP500+ +40 bp (54 trades). Petit : ~10 trades par an et par indice. Essai en direct, taille minimale.
Regles (bougies D1 du courtier, FERMEES) :
  entree : RSI 2 jours < 10 et cloture au-dessus de la moyenne 200 jours -> achat au debut de la journee suivante
           (dans les 180 premieres minutes, des que le spread est normal), une position au plus par indice,
           pas de nouvel achat le jour d'une sortie ;
  stop   : chez le courtier, a 2 x ATR 20 jours sous le prix ;
  sortie : des qu'une cloture du jour passe au-dessus de la moyenne 5 jours, ou apres 10 jours.
Une position sur un indice est toujours la sienne : apres un changement de version il la reprend au lieu de la fermer.
REGLE D'ARRET (ecrite avant le premier trade, suivie a chaque passage du labo sur les notes « sortie ») : arret si
la somme des trades passe sous -1 500 bp, ou si la moyenne est sous -20 bp apres 60 trades."""
import json

SYMBOLES = ("NAS100+", "SP500+", "DJ30+", "GER40+", "US2000+")   # US2000+ ajoute en v10 (courtier : +25 bp, 61 trades)
RSI_SEUIL, MM_LONGUE, MM_SORTIE, JOURS_MAX = 10.0, 200, 5, 10
STOP_ATR, ATR_N = 2.0, 20
SPREAD_MAX_BP = 3.0            # pas d'achat si le spread depasse 3 dix-milliemes du prix (normal : 0,3 a 0,5)
ATTENTE_MAX = 180 * 60         # secondes apres le debut de la bougie du jour
NOTIONNEL_MAX = 30000.0        # taille minimale du courtier, refusee si elle depasse ce montant de marche
FICHIER = "etat_repli.json"


def rsi2(c):
    """RSI de Wilder sur 2 jours (lissage 1/2), calcule sur toute la serie de clotures c."""
    h = b = 0.0
    for i in range(1, len(c)):
        d = c[i] - c[i - 1]
        h = 0.5 * max(d, 0.0) + 0.5 * h
        b = 0.5 * max(-d, 0.0) + 0.5 * b
    return 100.0 * h / (h + b) if h + b > 0 else 50.0


def atr(d1, n=ATR_N):
    tr = [max(d1[i][2] - d1[i][3], abs(d1[i][2] - d1[i - 1][4]), abs(d1[i][3] - d1[i - 1][4]))
          for i in range(len(d1) - n, len(d1))]
    return sum(tr) / n


def signal_entree(d1):
    """d1 = bougies D1 FERMEES. Vrai si la derniere cloture est un repli court dans une tendance haussiere."""
    c = [x[4] for x in d1]
    if len(c) < MM_LONGUE + 5:
        return False
    return rsi2(c) < RSI_SEUIL and c[-1] > sum(c[-MM_LONGUE:]) / MM_LONGUE


def signal_sortie(d1, jour_entree):
    """Vrai si, depuis le jour d'entree, une journee s'est fermee au-dessus de sa moyenne 5 jours, ou 10 jours passes."""
    c = [x[4] for x in d1]
    n = sum(1 for x in d1 if x[0] >= jour_entree)
    if n < 1 or len(c) < MM_SORTIE:
        return None
    if n >= JOURS_MAX:
        return "10 jours"
    if c[-1] > sum(c[-MM_SORTIE:]) / MM_SORTIE:
        return "au-dessus de la moyenne 5 j"
    return None


class Repli:
    def __init__(self, pont, fichier=FICHIER):
        self.pont, self.fichier = pont, fichier
        self.pos = {}          # symbole -> {"ticket", "entree", "jour"}
        self.fait = {}         # symbole -> debut de la journee deja traitee (achat fait, abandonne, ou sortie)
        self.infos, self.dernier, self.muets = {}, 0, set()
        try:
            with open(fichier, encoding="utf-8") as f:
                d = json.load(f)
            self.pos = {k: v for k, v in d.get("pos", {}).items() if k in SYMBOLES}
            self.fait = d.get("fait", {})
        except (OSError, ValueError):
            pass

    def sauver(self):
        try:
            with open(self.fichier, "w", encoding="utf-8") as f:
                json.dump({"pos": self.pos, "fait": self.fait}, f)
        except OSError:
            pass

    def tickets(self):
        return [p["ticket"] for p in self.pos.values()]

    def adopter(self, ps):
        """Reprend les positions du robot sur un indice qu'il ne connait pas (changement de version)."""
        connus = set(self.tickets())
        for t, p in ps.items():
            s = p.get("symbole")
            if s in SYMBOLES and t not in connus and s not in self.pos:
                self.pos[s] = {"ticket": t, "entree": p.get("prix_entree"), "jour": None}
                self.pont.noter(evenement="reprise", hypothese="repli_ind", symbole=s, ticket=t)
                self.sauver()

    def tour(self, ps, maintenant, peut_ouvrir):
        if maintenant - self.dernier < 60:
            return
        self.dernier = maintenant
        for s in SYMBOLES:
            try:
                self.un(s, ps, maintenant, peut_ouvrir)
            except Exception as e:                       # un indice absent ou ferme ne doit jamais gener le reste
                if s not in self.muets:
                    self.muets.add(s)
                    self.pont.noter(evenement="erreur", hypothese="repli_ind", symbole=s,
                                    texte=("%s: %s" % (type(e).__name__, e)).split("'")[0][:120])

    def un(self, s, ps, maintenant, peut_ouvrir):
        o = self.pos.get(s)
        if o and o["ticket"] not in ps:                  # stop touche chez le courtier
            self.pont.noter(evenement="sortie", hypothese="repli_ind", symbole=s, raison="stop ou fermeture hors robot",
                            ticket=o["ticket"], entree=o.get("entree"), dernier_profit=o.get("profit"), essai="non prouve")
            del self.pos[s]
            self.sauver()
            o = None
        b = self.pont.bougies(s, "D1", 260)
        if not b or len(b) < MM_LONGUE + 10:
            return
        jour, d1 = b[-1][0], b[:-1]                      # la derniere bougie est la journee en cours
        if o:
            p = ps[o["ticket"]]
            o["profit"] = p.get("profit")
            if o.get("jour") is None:
                o["jour"] = jour
                self.sauver()
            raison = signal_sortie(d1, o["jour"])
            if raison:
                r = self.pont.fermer(o["ticket"])
                if r.get("ok"):
                    e, x = o.get("entree") or p.get("prix_entree"), r.get("prix_obtenu")
                    self.pont.noter(evenement="sortie", hypothese="repli_ind", symbole=s, raison=raison, ticket=o["ticket"],
                                    entree=e, prix_sortie=x, profit=p.get("profit"),
                                    bp=round((x / e - 1) * 1e4, 1) if e and x else None, essai="non prouve")
                    del self.pos[s]
                    self.fait[s] = jour
                    self.sauver()
            return
        if not peut_ouvrir or self.fait.get(s) == jour or not 0 <= maintenant - jour <= ATTENTE_MAX:
            return
        if not signal_entree(d1):
            self.fait[s] = jour
            self.sauver()
            return
        px = self.pont.prix(s)
        if not px or px["bid"] <= 0 or not 0 <= (px["ask"] - px["bid"]) / px["bid"] * 1e4 <= SPREAD_MAX_BP:
            return                                       # spread anormal (ouverture de seance) : on reessaie dans une minute
        if s not in self.infos:
            self.infos[s] = self.pont.symbole(s)
        info = self.infos[s]
        lots = info["lot_min"]
        notionnel = lots * info["taille_contrat"] * px["ask"]
        c = [x[4] for x in d1]
        a = atr(d1)
        ecart = max(STOP_ATR * a, 3 * (px["ask"] - px["bid"]) + info["niveau_stops_points"] * info["point"])
        stop = round(px["bid"] - ecart, info["chiffres"])
        self.fait[s] = jour
        self.sauver()
        if notionnel > NOTIONNEL_MAX:
            self.pont.noter(evenement="ouverture sautee", hypothese="repli_ind", symbole=s, raison="taille minimale trop grosse",
                            notionnel=round(notionnel))
            return
        r = self.pont.ouvrir(s, "achat", lots, stop=stop, id="repli_ind")
        if r.get("ok") and r.get("ticket"):
            self.pos[s] = {"ticket": r["ticket"], "entree": r.get("prix_obtenu"), "jour": jour}
            self.sauver()
        self.pont.noter(evenement="ouverture", hypothese="repli_ind", symbole=s, sens=1, ok=bool(r.get("ok")),
                        refus=r.get("refus"), lots=lots, notionnel=round(notionnel), rsi2=round(rsi2(c), 1),
                        bid=px["bid"], ask=px["ask"], stop=stop, atr=round(a, 2), prix_obtenu=r.get("prix_obtenu"),
                        essai="non prouve")
