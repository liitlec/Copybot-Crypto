"""Hypothese bt_or : la mecanique de BlockTrend sur l'or, en petit (essai NON prouve, 0,01 lot par position).
Banc : labo/banc_blocktrend.py (or M5, 15 mois : +0,38 R par panier avec 3 positions au plus, 28 % de gagnants,
pire creux -18 R ; rien sur le Nasdaq). Regles :
  sens     : cloture M5 contre son EMA de 576 bougies (2 jours) -> achats au-dessus, ventes en dessous ;
  entree   : a la cloture des bougies M5 de 03:05, 08:00, 08:30, 12:00, 15:45, 16:00, 16:30 (serveur), un panier par cote ;
  ajouts   : dans le sens du gain, une position par « pas » (0,25 ATR jour) franchi a la cloture M5, saute si la cloture
             est deja a plus d'un demi-pas au-dela ; 3 positions au plus ;
  sortie   : tout le panier quand le prix recule de 0,6667 ATR jour depuis son meilleur niveau (stop suiveur tenu par le
             robot) ; stop de secours chez le courtier un quart plus loin, remonte avec le meilleur prix.
REGLE D'ARRET (ecrite avant le premier trade) : arret a -20 R cumules (pire creux du banc : -18 R), ou moyenne
< -0,3 R apres 40 paniers. 1 R = 0,6667 x ATR jour x 1 once (environ 40 a 60 $ a 0,01 lot)."""
import json
import time

SYMBOLE = "XAUUSD"
LOTS = 0.01
MAX_POS = 3
PAS_K, STOP_K, SECOURS_K = 0.25, 0.6667, 1.25
HEURES = ((3, 5), (8, 0), (8, 30), (12, 0), (15, 45), (16, 0), (16, 30))
EMA_N = 576
ARRET_R = -20.0
FICHIER = "etat_bt.json"


def ema(valeurs, n):
    a = 2.0 / (n + 1)
    e = valeurs[0]
    for v in valeurs[1:]:
        e = a * v + (1 - a) * e
    return e


def atr_jour(d1, n=20):
    """Moyenne des n dernieres amplitudes vraies sur des bougies D1 FERMEES. None s'il en manque."""
    if len(d1) < n + 1:
        return None
    tr = []
    for i in range(len(d1) - n, len(d1)):
        h, b, cp = d1[i][2], d1[i][3], d1[i - 1][4]
        tr.append(max(h - b, abs(h - cp), abs(b - cp)))
    return sum(tr) / n


class PanierBT:
    def __init__(self, pont, fichier=FICHIER):
        self.pont, self.fichier = pont, fichier
        self.paniers = {}        # "1" / "-1" -> panier
        self.cumul_r, self.n_paniers, self.vu = 0.0, 0, None
        try:
            with open(fichier, encoding="utf-8") as f:
                d = json.load(f)
            self.paniers, self.cumul_r, self.n_paniers = d.get("paniers", {}), d.get("cumul_r", 0.0), d.get("n", 0)
        except (OSError, ValueError):
            pass

    def sauver(self):
        try:
            with open(self.fichier, "w", encoding="utf-8") as f:
                json.dump({"paniers": self.paniers, "cumul_r": self.cumul_r, "n": self.n_paniers}, f)
        except OSError:
            pass

    def tickets(self):
        return {t for p in self.paniers.values() for t in p["tickets"]}

    def arrete(self):
        return self.cumul_r <= ARRET_R or (self.n_paniers >= 40 and self.cumul_r / self.n_paniers < -0.3)

    # ------------------------------------------------------------------ sorties
    def _cloture(self, cle, raison, ps):
        p = self.paniers[cle]
        total = 0.0
        for t in p["tickets"]:
            if t in ps:
                total += ps[t].get("profit") or 0.0
                self.pont.fermer(t)
            else:
                total += p["profits"].get(str(t), 0.0)
        r = total / (p["stop"] * 100 * LOTS) if p["stop"] > 0 else 0.0
        self.cumul_r += r
        self.n_paniers += 1
        self.pont.noter(evenement="sortie panier", hypothese="bt_or", raison=raison, sens=int(cle),
                        positions=len(p["tickets"]), profit=round(total, 2), R=round(r, 2), cumul_R=round(self.cumul_r, 2),
                        paniers=self.n_paniers, essai="non prouve")
        del self.paniers[cle]
        self.sauver()

    def surveiller(self, ps, px):
        """A chaque tour : stop suiveur sur le prix courant, paniers fermes chez le courtier."""
        for cle in list(self.paniers):
            p, s = self.paniers[cle], int(cle)
            vivants = [t for t in p["tickets"] if t in ps]
            for t in vivants:
                p["profits"][str(t)] = ps[t].get("profit") or 0.0
            if len(vivants) < len(p["tickets"]):
                self._cloture(cle, "stop de secours du courtier" if not vivants else "position manquante", ps)
                continue
            if s > 0:
                p["meilleur"] = max(p["meilleur"], px["bid"])
                touche = px["bid"] <= p["meilleur"] - p["stop"]
            else:
                p["meilleur"] = min(p["meilleur"], px["bid"])
                touche = px["ask"] >= p["meilleur"] + p["stop"]
            if touche:
                self._cloture(cle, "recul depuis le meilleur prix", ps)

    # ------------------------------------------------------------------ entrees et ajouts (a chaque bougie M5 fermee)
    def _ouvre(self, p, s, niveau, chiffres):
        px = self.pont.prix(SYMBOLE)
        secours = p["meilleur"] - s * SECOURS_K * p["stop"]
        if (s > 0 and secours >= px["bid"]) or (s < 0 and secours <= px["ask"]):
            return False
        r = self.pont.ouvrir(SYMBOLE, "achat" if s > 0 else "vente", LOTS, stop=round(secours, chiffres),
                             id="bt_or_%d" % niveau)
        self.pont.noter(evenement="ouverture", hypothese="bt_or", niveau=niveau, sens=s, ok=bool(r.get("ok")),
                        refus=r.get("refus"), prix_obtenu=r.get("prix_obtenu"), stop_secours=round(secours, chiffres),
                        distance_stop=round(p["stop"], 2), essai="non prouve")
        if r.get("ok") and r.get("ticket"):
            p["tickets"].append(r["ticket"])
            p["profits"][str(r["ticket"])] = 0.0
            return True
        return False

    def bougie(self, m5, d1, spread_ok, chiffres=2):
        """m5, d1 : bougies FERMEES. Appele une fois par nouvelle bougie M5."""
        if not m5 or m5[-1][0] == self.vu:
            return
        self.vu = m5[-1][0]
        c = m5[-1][4]
        for cle, p in self.paniers.items():                      # stop de secours remonte, puis ajouts
            s = int(cle)
            secours = round(p["meilleur"] - s * SECOURS_K * p["stop"], chiffres)
            if abs(secours - p.get("secours", 0)) > 0.1 * p["stop"] and s * (secours - p.get("secours", secours - s)) > 0:
                for t in p["tickets"]:
                    self.pont.modifier(t, secours)
                p["secours"] = secours
            while spread_ok and len(p["tickets"]) < MAX_POS and s * (c - p["prochain"]) >= 0:
                if s * (c - p["prochain"]) <= 0.5 * p["pas"]:
                    self._ouvre(p, s, len(p["tickets"]) + 1, chiffres)
                p["prochain"] += s * p["pas"]
        t = time.gmtime(m5[-1][0])
        if (t.tm_hour, t.tm_min) in HEURES and spread_ok and not self.arrete() and len(m5) >= 2500:
            a = atr_jour(d1)
            if a and a > 0:
                s = 1 if c > ema([x[4] for x in m5[-2880:]], EMA_N) else -1
                if str(s) not in self.paniers:
                    p = {"tickets": [], "profits": {}, "meilleur": c, "stop": STOP_K * a, "pas": PAS_K * a,
                         "prochain": c + s * PAS_K * a, "debut": m5[-1][0]}
                    p["secours"] = round(c - s * SECOURS_K * p["stop"], chiffres)
                    if self._ouvre(p, s, 1, chiffres):
                        self.paniers[str(s)] = p
        self.sauver()
