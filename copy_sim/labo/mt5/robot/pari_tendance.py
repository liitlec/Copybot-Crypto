"""Variante pari_tendance_opt (v23, PRIORITES 21/11 15 h 20 « poche pari tendance ») : HORS totaux du test, compte
VIRTUEL separe. Banc : labo/banc_pari_tendance.py (Monte-Carlo sur les vrais paniers bt_or / bt_or_plus, M5 18 mois et
H1 4 ans, 10 000 parcours, 24 mois). Montage choisi par la regle fixee d'avance (meilleure esperance prudente H1 avec
ruine <= 40 %) : la mecanique bt_or (1-1-1, 3 positions), mise 3 % du compte virtuel par R, OBJECTIF x5.
Chances a 24 mois depuis 100 EUR (H1 4 ans) : mesure x5 49 %, ruine 2 % ; prudent (avantage / 2) x5 23 %, ruine 11 %,
rien atteint 66 % ; sans avantage x5 8 %, ruine 36 %. bt_or_plus (1-2-3) fait moins bien a toutes les mises (pire panier
-6,6 R). Reference pari_opt (repli S&P + Russell) : x3 56 % en 5 ans, ruine 39 %.
Compte cent : 100 EUR = 116 $ ; ici sur la demo (compte standard), tout est multiplie par 100 : compte virtuel de depart
11 600 $, 0,01 lot standard = 1 lot cent. Lots = 0,01 x max(1, plancher(MISE x compte / (distance du stop x 1 once))),
plafonnes a 1,00 lot ; calcules a l'ouverture du panier et gardes pour ses ajouts.
REGLE D'ARRET (ecrite avant le premier panier) : objectif x5 = compte virtuel + gains latents >= 58 000 $ -> on ferme tout,
on encaisse et on s'arrete ; poche vide = compte virtuel < 20 % du depart (2 320 $) -> plus aucun panier ; aussi arret si
le cumul est negatif apres 40 paniers. Stop de secours marque 57 (centimes), distinct de bt_or (x7), 97 et 77."""
import json
import math
import bt_or

NOM = "pari_tendance_opt"
DEPART, MISE, OBJECTIF, PLANCHER = 11600.0, 0.03, 5.0, 0.20
LOTS_MAX, ARRET_N = 1.0, 40
FICHIER = "etat_pari_tendance.json"


def lots_pour(compte, stop):
    """Lot de base (standard) pour une mise de MISE x compte au stop initial (1 once par 0,01 lot)."""
    if not stop or stop <= 0 or compte <= 0:
        return 0.0
    n = max(1, int(math.floor(MISE * compte / stop + 1e-9)))
    return round(min(LOTS_MAX, 0.01 * n), 2)


class PanierPari(bt_or.PanierBT):
    def __init__(self, pont, fichier=FICHIER, nom=NOM):
        super().__init__(pont, fichier=fichier, nom=nom)
        self.plus = bt_or.MARQUE_PARI
        self.compte, self.arret, self.somme = DEPART, None, 0.0
        try:
            with open(fichier, encoding="utf-8") as f:
                d = json.load(f)
            self.compte, self.arret, self.somme = d.get("compte", DEPART), d.get("arret"), d.get("somme", 0.0)
        except (OSError, ValueError):
            pass

    def sauver(self):
        try:
            with open(self.fichier, "w", encoding="utf-8") as f:
                json.dump({"paniers": self.paniers, "cumul_r": self.cumul_r, "n": self.n_paniers,
                           "compte": self.compte, "arret": self.arret, "somme": self.somme}, f)
        except OSError:
            pass

    def arrete(self):
        return self.arret is not None or getattr(self, "retire", False)   # v27 : retire du robot

    def _ouvre(self, p, s, niveau, chiffres):
        if "lots0" not in p:                       # nouveau panier : taille sur le compte virtuel
            p["lots0"] = lots_pour(self.compte, p["stop"])
        if p.get("lots0", 0) <= 0:
            return False
        self.lots = p["lots0"]
        return super()._ouvre(p, s, niveau, chiffres)

    def _cloture(self, cle, raison, ps):
        p = self.paniers[cle]
        total = sum((ps[t].get("profit") or 0.0) if t in ps else p["profits"].get(str(t), 0.0) for t in p["tickets"])
        self.lots = p.get("lots0") or bt_or.LOTS
        super()._cloture(cle, raison, ps)
        self.compte = round(self.compte + total, 2)
        self.somme = round(self.somme + total, 2)
        if self.arret is None and self.compte >= OBJECTIF * DEPART:
            self.arret = "objectif x%g atteint" % OBJECTIF
        if self.arret is None and self.compte < PLANCHER * DEPART:
            self.arret = "poche vide"
        if self.arret is None and self.n_paniers >= ARRET_N and self.somme < 0:
            self.arret = "cumul negatif apres %d paniers" % ARRET_N
        self.pont.noter(evenement="compte virtuel", hypothese=self.nom, compte_virtuel=self.compte, arret=self.arret,
                        essai="non prouve")
        self.sauver()

    def surveiller(self, ps, px):
        """Objectif : compte virtuel + gains latents >= x5 -> tout fermer et s'arreter. Puis le suivi normal."""
        latent = sum(ps[t].get("profit") or 0.0 for p in self.paniers.values() for t in p["tickets"] if t in ps)
        if self.paniers and self.compte + latent >= OBJECTIF * DEPART:
            for cle in list(self.paniers):
                self._cloture(cle, "objectif x%g" % OBJECTIF, ps)
            self.arret = self.arret or "objectif x%g atteint" % OBJECTIF
            self.sauver()
            return
        super().surveiller(ps, px)
