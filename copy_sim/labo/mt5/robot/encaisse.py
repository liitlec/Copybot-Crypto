"""Variante encaisse_calme_opt (v26, PRIORITES 23/11 11 h « Lot C : encaisser plus qu'on ne depose ») : POCHE VIRTUELLE,
HORS totaux, AUCUN ordre. Banc : labo/banc_lotc.py (combinaison qui passe le critere prudent sur les deux blocs, et la
plus sure en P(net > 0) parmi celles a mise augmentee ; rejeu reel positif sur les deux blocs).
v29 : elle rejoue chaque panier FERME de bt_or_plus_opt (avant v29 : de gpt_pyramide_opt) (regle « cassure apres seance tres calme », memes prix, R du panier
renforts compris) sur un compte virtuel :
  depot 500 EUR ; mise d'un panier = 6 % du capital x 1,5^k (k = pertes d'affilee, plafond 3 paliers, remis a 0 apres
  un panier >= 0 ; plafond 100 % du capital) ; gain = mise x R du panier ;
  retrait chaque fin de semaine (passage au lundi, heure serveur) de tout ce qui depasse 1,5 x le depot (750 EUR) ;
  ruine = capital < 20 % du depot (100 EUR) : le reste est retire, puis recharge de 500 EUR, 2 fois au plus ;
  ensuite arret. Arret aussi 24 mois apres le premier panier.
Mesure suivie : ARGENT NET ENCAISSE = retraits - depots. Ce n'est PAS de l'argent reel (compte demo, poche virtuelle) ;
aucun reel sans accord de Baptiste sur son PC."""
import json

NOM = "encaisse_calme_opt"
FICHIER = "etat_encaisse.json"
DEPOT, F, M, KMAX, PLANCHER, PLAFOND, RECHARGES = 500.0, 0.06, 1.5, 3, 0.2, 1.5, 2
DUREE = 730 * 86400
SEMAINE = 7 * 86400
LUNDI0 = 4 * 86400                    # le 01/01/1970 etait un jeudi : lundi = (t - 4 j) // 7 j


def semaine(t):
    return (t - LUNDI0) // SEMAINE


class Poche:
    def __init__(self, pont, fichier=FICHIER):
        self.pont, self.fichier = pont, fichier
        self.e = {"capital": DEPOT, "depots": DEPOT, "retraits": 0.0, "recharges": 0, "k": 0, "n": 0, "ruines": 0,
                  "semaine": None, "debut": None, "fini": False}
        try:
            with open(fichier, encoding="utf-8") as f:
                self.e.update(json.load(f))
        except (OSError, ValueError):
            pass

    def sauver(self):
        try:
            with open(self.fichier, "w", encoding="utf-8") as f:
                json.dump(self.e, f)
        except OSError:
            pass

    def net(self):
        return self.e["retraits"] - self.e["depots"]

    def panier(self, r, t):
        """r : R du panier ferme de gpt_pyramide_opt ; t : heure (s)."""
        e = self.e
        if e["fini"]:
            return
        if e["debut"] is None:
            e["debut"] = t
        mise = min(F * M ** e["k"], 1.0) * e["capital"]
        e["capital"] = max(e["capital"] + mise * r, 0.0)
        e["k"] = min(e["k"] + 1, KMAX) if r < 0 else 0
        e["n"] += 1
        evt = dict(evenement="sortie panier", hypothese=NOM, R=round(r, 2), mise=round(mise, 2),
                   capital=round(e["capital"], 2), palier=e["k"], essai="poche virtuelle, non prouve")
        if e["capital"] < PLANCHER * DEPOT:
            e["ruines"] += 1
            e["retraits"] += e["capital"]
            if e["recharges"] < RECHARGES:
                e["recharges"] += 1; e["depots"] += DEPOT; e["capital"] = DEPOT; e["k"] = 0
                evt.update(ruine=True, recharge=e["recharges"])
            else:
                e["capital"] = 0.0; e["fini"] = True
                evt.update(ruine=True, arret="plus de recharge")
        evt.update(net_encaisse=round(self.net(), 2))
        self.pont.noter(**evt)
        self.sauver()

    def horloge(self, t):
        """Appele a chaque nouvelle bougie : retrait de fin de semaine, arret a 24 mois."""
        e = self.e
        s = semaine(t)
        if e["semaine"] is None:
            e["semaine"] = s; self.sauver(); return
        if s == e["semaine"] or e["fini"]:
            return
        e["semaine"] = s
        if e["capital"] > PLAFOND * DEPOT:
            x = e["capital"] - PLAFOND * DEPOT
            e["capital"] -= x; e["retraits"] += x
            self.pont.noter(evenement="retrait", hypothese=NOM, montant=round(x, 2), capital=round(e["capital"], 2),
                            net_encaisse=round(self.net(), 2), essai="poche virtuelle, non prouve")
        if e["debut"] is not None and t - e["debut"] >= DUREE:
            e["fini"] = True
            self.pont.noter(evenement="arret", hypothese=NOM, raison="24 mois", net_encaisse=round(self.net(), 2),
                            capital=round(e["capital"], 2))
        self.sauver()
