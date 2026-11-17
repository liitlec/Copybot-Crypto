"""Variante pari_opt (v16, PRIORITES 17/11 12 h 45 « poche pari ») : HORS totaux du test, compte VIRTUEL de 100 $.
Banc : labo/banc_pari.py (Monte-Carlo sur les vrais trades du courtier, 10 000 parcours). A 100 $, le lot minimum impose
deja un pari enorme sur l'or (42 % du compte par position) et sur le Nasdaq / le Dow (28 a 52 fois le compte) : ruine
72 a 90 % en un an des que l'avantage est divise par 2. Le seul montage qui passe la regle fixee d'avance (chance de x5
maximale avec ruine <= 50 %, avantage / 2, 12 mois) : le repli d'indices (regle de repli_ind, prouvee) sur les deux plus
petits contrats, SP500+ et US2000+, mise 2 Kelly (levier 14 fois le compte virtuel). Chances a 12 mois (avantage / 2) :
ruine 15 %, sous 50 $ 25 %, mediane ~100 $, x2 26 %, x5 6 %, x10 1 %. ~18 trades par an : c'est lent.
Regles : celles de repli_ind (RSI 2 j < 10 au-dessus de la moyenne 200 j, entree debut de journee suivante, stop 2 ATR,
sortie cloture > moyenne 5 j ou 10 jours), avec une taille calculee sur le compte virtuel :
  lots = pas_lot x max(1, plancher(LEVIER x compte / notionnel d'un lot minimum)), plafonnes a 0,50 lot ;
  trade saute si un seul lot minimum depasse NOTIONNEL_MAX_X fois le compte (contrat plus gros que prevu).
  Le compte virtuel avance du gain reel de chaque sortie (en $, la taille jouee est celle qu'il aurait eue).
REGLE D'ARRET (ecrite avant le premier trade) : poche vide = compte virtuel < 20 $ -> plus aucune ouverture ; aussi arret
si la moyenne des trades est negative apres 40 trades.
v18 (PRIORITES 17/11 17 h 20, « triple ou rien », banc labo/banc_pari_triple.py) : OBJECTIF D'ARRET a x3 = 300 $. Des que
le compte virtuel plus les gains latents des positions ouvertes atteint 300 $, on ferme tout, on encaisse et on s'arrete.
Monte-Carlo (avantage / 2, jusqu'a 5 ans) : ce montage a cette mise donne la plus forte chance de x3 avant la ruine a
100 $ : 56 % (ruine 39 %, rien en 5 ans 5 %, duree mediane ~1,4 an) ; objectif x5 : 42 % (ruine 45 %).
La decision de passer en reel reste a Baptiste.
Ses positions sont connues par son fichier d'etat (etat_pari.json) ; le robot les retire de ce que repli_ind peut reprendre."""
import json
import math
import repli_ind as R

NOM = "pari_opt"
SYMBOLES = ("SP500+", "US2000+")
DEPART, LEVIER, NOTIONNEL_MAX_X, LOTS_MAX = 100.0, 14.0, 30.0, 0.5
POCHE_VIDE, ARRET_N = 20.0, 40
OBJECTIF = 3.0                 # x3 : on encaisse et on s'arrete (v18)
FICHIER = "etat_pari.json"


def lots_pour(compte, info, ask):
    """Taille a jouer pour le compte virtuel ; 0 si un lot minimum est deja trop gros pour la poche."""
    pas = info.get("pas_lot") or info["lot_min"]
    unite = info["lot_min"] * info["taille_contrat"] * ask
    if unite <= 0 or unite > NOTIONNEL_MAX_X * compte:
        return 0.0
    n = max(1, int(math.floor(LEVIER * compte / unite)))
    lots = min(LOTS_MAX, info["lot_min"] + (n - 1) * pas if pas else info["lot_min"] * n)
    return round(math.floor(lots / pas + 1e-9) * pas, 2)


class Pari:
    def __init__(self, pont, fichier=FICHIER):
        self.pont, self.fichier = pont, fichier
        self.compte, self.trades, self.somme, self.arret = DEPART, 0, 0.0, None
        self.pos, self.fait, self.infos, self.dernier, self.muets = {}, {}, {}, 0, set()
        try:
            with open(fichier, encoding="utf-8") as f:
                d = json.load(f)
            self.compte, self.trades = d.get("compte", DEPART), d.get("trades", 0)
            self.somme, self.arret = d.get("somme", 0.0), d.get("arret")
            self.pos = {k: v for k, v in d.get("pos", {}).items() if k in SYMBOLES}
            self.fait = d.get("fait", {})
        except (OSError, ValueError):
            pass

    def sauver(self):
        try:
            with open(self.fichier, "w", encoding="utf-8") as f:
                json.dump({"compte": self.compte, "trades": self.trades, "somme": self.somme, "arret": self.arret,
                           "pos": self.pos, "fait": self.fait}, f)
        except OSError:
            pass

    def tickets(self):
        return [p["ticket"] for p in self.pos.values()]

    def compter(self, gain, s, raison, **x):
        self.compte = round(self.compte + (gain or 0.0), 2)
        self.trades += 1
        self.somme = round(self.somme + (gain or 0.0), 2)
        if self.arret is None and self.compte >= OBJECTIF * DEPART:
            self.arret = "objectif x%g atteint" % OBJECTIF
        if self.arret is None and self.compte < POCHE_VIDE:
            self.arret = "poche vide"
        if self.arret is None and self.trades >= ARRET_N and self.somme < 0:
            self.arret = "moyenne negative apres %d trades" % ARRET_N
        self.pont.noter(evenement="sortie", hypothese=NOM, symbole=s, raison=raison, profit=gain,
                        compte_virtuel=self.compte, arret=self.arret, essai="non prouve", **x)

    def encaisser(self, ps):
        """v18 : compte virtuel + gains latents >= objectif -> on ferme tout et on s'arrete."""
        ouverts = {s: o for s, o in self.pos.items() if o["ticket"] in ps}
        latent = sum(ps[o["ticket"]].get("profit") or 0.0 for o in ouverts.values())
        if self.arret or not ouverts or self.compte + latent < OBJECTIF * DEPART:
            return
        for s, o in ouverts.items():
            p = ps[o["ticket"]]
            r = self.pont.fermer(o["ticket"])
            if r.get("ok"):
                e, x = o.get("entree") or p.get("prix_entree"), r.get("prix_obtenu")
                info = self.infos.get(s) or self.pont.symbole(s)
                gain = (x - e) * o["lots"] * info["taille_contrat"] if e and x else p.get("profit")
                del self.pos[s]
                self.compter(round(gain, 2), s, "objectif x%g" % OBJECTIF, ticket=o["ticket"], entree=e, prix_sortie=x,
                             lots=o["lots"])
        if not self.pos:
            self.arret = self.arret or "objectif x%g atteint" % OBJECTIF
        self.sauver()

    def tour(self, ps, maintenant, peut_ouvrir):
        if maintenant - self.dernier < 60:
            return
        self.dernier = maintenant
        try:
            self.encaisser(ps)
        except Exception as e:
            if "encaisser" not in self.muets:
                self.muets.add("encaisser")
                self.pont.noter(evenement="erreur", hypothese=NOM, texte=("%s: %s" % (type(e).__name__, e)).split("'")[0][:120])
        for s in SYMBOLES:
            try:
                self.un(s, ps, maintenant, peut_ouvrir)
            except Exception as e:                       # ne doit jamais gener le reste du robot
                if s not in self.muets:
                    self.muets.add(s)
                    self.pont.noter(evenement="erreur", hypothese=NOM, symbole=s,
                                    texte=("%s: %s" % (type(e).__name__, e)).split("'")[0][:120])

    def un(self, s, ps, maintenant, peut_ouvrir):
        o = self.pos.get(s)
        if o and o["ticket"] not in ps:                  # stop touche chez le courtier : dernier gain connu
            del self.pos[s]
            self.compter(o.get("profit"), s, "stop ou fermeture hors robot", ticket=o["ticket"], estime=True)
            self.sauver()
            o = None
        b = self.pont.bougies(s, "D1", 260)
        if not b or len(b) < R.MM_LONGUE + 10:
            return
        jour, d1 = b[-1][0], b[:-1]
        if o:
            p = ps[o["ticket"]]
            o["profit"] = p.get("profit")
            if o.get("jour") is None:
                o["jour"] = jour
                self.sauver()
            raison = R.signal_sortie(d1, o["jour"])
            if raison:
                r = self.pont.fermer(o["ticket"])
                if r.get("ok"):
                    e, x = o.get("entree") or p.get("prix_entree"), r.get("prix_obtenu")
                    info = self.infos.get(s) or self.pont.symbole(s)
                    gain = (x - e) * o["lots"] * info["taille_contrat"] if e and x else p.get("profit")
                    del self.pos[s]
                    self.fait[s] = jour
                    self.compter(round(gain, 2), s, raison, ticket=o["ticket"], entree=e, prix_sortie=x, lots=o["lots"],
                                 bp=round((x / e - 1) * 1e4, 1) if e and x else None)
                    self.sauver()
            return
        if self.arret or not peut_ouvrir or self.fait.get(s) == jour or not 0 <= maintenant - jour <= R.ATTENTE_MAX:
            return
        if not R.signal_entree(d1):
            self.fait[s] = jour
            self.sauver()
            return
        px = self.pont.prix(s)
        if not px or px["bid"] <= 0 or not 0 <= (px["ask"] - px["bid"]) / px["bid"] * 1e4 <= R.SPREAD_MAX_BP:
            return
        if s not in self.infos:
            self.infos[s] = self.pont.symbole(s)
        info = self.infos[s]
        lots = lots_pour(self.compte, info, px["ask"])
        a = R.atr(d1)
        ecart = max(R.STOP_ATR * a, 3 * (px["ask"] - px["bid"]) + info.get("niveau_stops_points", 0) * info["point"])
        stop = round(px["bid"] - ecart, info["chiffres"])
        self.fait[s] = jour
        self.sauver()
        if lots <= 0:
            self.pont.noter(evenement="ouverture sautee", hypothese=NOM, symbole=s, raison="lot minimum trop gros pour la poche",
                            compte_virtuel=self.compte)
            return
        r = self.pont.ouvrir(s, "achat", lots, stop=stop, id=NOM)
        if r.get("ok") and r.get("ticket"):
            self.pos[s] = {"ticket": r["ticket"], "entree": r.get("prix_obtenu"), "jour": jour, "lots": lots}
            self.sauver()
        self.pont.noter(evenement="ouverture", hypothese=NOM, symbole=s, sens=1, ok=bool(r.get("ok")), refus=r.get("refus"),
                        lots=lots, notionnel=round(lots * info["taille_contrat"] * px["ask"]), compte_virtuel=self.compte,
                        bid=px["bid"], ask=px["ask"], stop=stop, atr=round(a, 2), prix_obtenu=r.get("prix_obtenu"),
                        essai="non prouve")
