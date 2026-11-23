"""Variante gpt_pyramide_opt (v24, PRIORITES 23/11 « renforts gagnants » proposee par GPT Astra) : POUR LES DONNEES,
HORS totaux, essai NON prouve. Banc : labo/banc_gpt_pyramide.py. Regle figee le 23/11 (meme texte que le banc) :
  R       = 0,25 x moyenne (haut - bas) des 14 dernieres seances D1 fermees ;
  sens    = cloture D1 de la veille au-dessus de sa moyenne 50 seances -> achat, en dessous -> vente ;
  filtre  = veille tres calme (amplitude < 0,6 x moyenne des 14 precedentes) OU inside day (dans l'avant-veille) ;
  entree  = cloture de la bougie M15 de 08:00 serveur, un panier par seance, volume V = LOTS_BASE ;
  stop    = 1 R contre la 1re entree ; des la 1re cloture M15 a >= +1 R : prix d'entree moyen ; ensuite
            max(stop, meilleure cloture M15 - 1,5 R) (symetrique en vente), jamais en recul ;
  renforts= 0,5 x V a +1 R puis +1,5 R : cloture M15 au-dela du seuil ET ouverture de la bougie suivante encore au-dela
            (ajout a cette ouverture) ; version A : on laisse courir (sortie au stop seulement).
Les stops sont poses CHEZ LE COURTIER sur chaque position (et deplaces), marques 37 aux centimes : les positions
survivent a un changement de version meme si la memoire est perdue.
REGLE D'ARRET (ecrite avant le premier panier) : arret si le cumul atteint -15 R (1 R = perte de V au stop initial), ou
si la moyenne est < -0,3 R apres 30 paniers. Taille : V = 0,02 lot (renforts 0,01 lot), donnees seulement."""
import json
import time
import bt_or

NOM = "gpt_pyramide_opt"
SYMBOLE = "XAUUSD"
LOTS_BASE = 0.02
HEURE_ENTREE = (8, 0)              # bougie M15 de 08:00 serveur
CALME, N_ADR, N_TEND = 0.6, 14, 50
SEUILS = (1.0, 1.5)
SUIVI_R = 1.5
ARRET_R, ARRET_N, ARRET_MOY = -15.0, 30, -0.3
MARQUE = 37
FICHIER = "etat_gpt_pyramide.json"
R_REPRISE = 15.0                  # R estime (environ 0,25 x amplitude journaliere de l'or) si la memoire est perdue


def parametres(d1):
    """d1 : bougies D1 FERMEES [t, o, h, l, c, ...]. Rend (sens, R) ou (0, None) si pas de signal."""
    if len(d1) < max(N_TEND, N_ADR + 2):
        return 0, None
    amp = [x[2] - x[3] for x in d1]
    adr = sum(amp[-N_ADR:]) / N_ADR
    veille, avant = d1[-1], d1[-2]
    calme = amp[-1] < CALME * (sum(amp[-N_ADR - 1:-1]) / N_ADR)
    inside = veille[2] <= avant[2] and veille[3] >= avant[3]
    if not (calme or inside) or adr <= 0:
        return 0, None
    mm = sum(x[4] for x in d1[-N_TEND:]) / N_TEND
    s = 1 if veille[4] > mm else (-1 if veille[4] < mm else 0)
    return s, 0.25 * adr


class GptPyramide:
    def __init__(self, pont, fichier=FICHIER):
        self.pont, self.fichier = pont, fichier
        self.panier, self.cumul_r, self.n, self.fait, self.vu, self.muet = None, 0.0, 0, None, None, False
        self.poche = None                 # v26 : poche virtuelle encaisse_calme_opt (encaisse.py), aucun ordre
        try:
            with open(fichier, encoding="utf-8") as f:
                d = json.load(f)
            self.panier, self.cumul_r, self.n, self.fait = d.get("panier"), d.get("cumul_r", 0.0), d.get("n", 0), d.get("fait")
        except (OSError, ValueError):
            pass

    def sauver(self):
        try:
            with open(self.fichier, "w", encoding="utf-8") as f:
                json.dump({"panier": self.panier, "cumul_r": self.cumul_r, "n": self.n, "fait": self.fait}, f)
        except OSError:
            pass

    def tickets(self):
        return list(self.panier["tickets"]) if self.panier else []

    def arrete(self):
        return self.cumul_r <= ARRET_R or (self.n >= ARRET_N and self.cumul_r / self.n < ARRET_MOY)

    @staticmethod
    def candidat(p):
        return p.get("symbole") == SYMBOLE and p.get("stop") and bt_or.code_marque(p["stop"]) == MARQUE

    def adopter(self, ps):
        """Memoire perdue : reprend les positions marquees 37 (stop chez le courtier conserve, suivi repris)."""
        lst = sorted((p for p in ps.values() if self.candidat(p)), key=lambda q: q.get("heure_serveur") or 0)
        if not lst or self.panier:
            return
        s = 1 if lst[0]["sens"] == "achat" else -1
        e0, st = lst[0]["prix_entree"], lst[0]["stop"]
        r = abs(e0 - st)
        if s * (e0 - st) <= 1.0:                          # stop deja au point mort ou au-dela : R inconnu, estime
            r = R_REPRISE
        self.panier = {"s": s, "tickets": [q["ticket"] for q in lst], "e0": e0, "R": r, "stop": st,
                       "meilleur": e0, "renforts": max(0, len(lst) - 1), "be": False, "profits": {}, "attente": None}
        self.pont.noter(evenement="reprise", hypothese=NOM, sens=s, positions=len(lst), stop=st)
        self.sauver()

    def _ouvrir(self, s, lots, stop):
        r = self.pont.ouvrir(SYMBOLE, "achat" if s > 0 else "vente", lots,
                             stop=bt_or.marquer(stop, 2, MARQUE), id=NOM)
        return r

    def _poser_stop(self, nouveau):
        p = self.panier
        m = bt_or.marquer(nouveau, 2, MARQUE)
        if p["s"] * (m - p["stop"]) <= 0.05:              # jamais en recul (petit ecart : on laisse)
            return
        for t in p["tickets"]:
            self.pont.modifier(t, m)
        p["stop"] = m

    def _fin(self, ps, raison):
        p = self.panier
        total = sum((ps[t].get("profit") or 0.0) if t in ps else p["profits"].get(str(t), 0.0) for t in p["tickets"])
        for t in p["tickets"]:
            if t in ps:
                self.pont.fermer(t)
        r = total / (p["R"] * LOTS_BASE * 100.0) if p["R"] > 0 else 0.0
        self.cumul_r += r
        self.n += 1
        self.pont.noter(evenement="sortie panier", hypothese=NOM, raison=raison, sens=p["s"], positions=len(p["tickets"]),
                        profit=round(total, 2), R=round(r, 2), cumul_R=round(self.cumul_r, 2), paniers=self.n,
                        essai="non prouve")
        self.panier = None
        self.sauver()
        if self.poche is not None:
            try:
                self.poche.panier(r, time.time())
            except Exception:
                pass

    def tour(self, ps, m15, d1, permis):
        """ps : positions ; m15, d1 : bougies FERMEES. Appele a chaque tour du robot (travail a chaque nouvelle M15)."""
        p = self.panier
        if p:
            vivants = [t for t in p["tickets"] if t in ps]
            for t in vivants:
                p["profits"][str(t)] = ps[t].get("profit") or 0.0
            if len(vivants) < len(p["tickets"]):           # stop touche chez le courtier
                self._fin(ps, "stop du panier")
                return
        if not m15 or m15[-1][0] == self.vu:
            return
        self.vu = m15[-1][0]
        b = m15[-1]
        if self.poche is not None:
            try:
                self.poche.horloge(b[0])
            except Exception:
                pass
        p = self.panier
        if p:
            s, R = p["s"], p["R"]
            if p.get("attente") is not None:                # renfort confirme si l'ouverture reste au-dela du seuil
                seuil = p["e0"] + s * p["attente"] * R
                if s * (b[1] - seuil) >= 0 and permis:
                    st = p["stop"]
                    r = self._ouvrir(s, round(0.5 * LOTS_BASE, 2), st)
                    if r.get("ok") and r.get("ticket"):
                        p["tickets"].append(r["ticket"])
                        p["profits"][str(r["ticket"])] = 0.0
                        p["renforts"] += 1
                        self.pont.noter(evenement="ouverture", hypothese=NOM, niveau=p["renforts"] + 1, sens=s,
                                        prix_obtenu=r.get("prix_obtenu"), essai="non prouve")
                p["attente"] = None
            c = b[4]
            p["meilleur"] = max(p["meilleur"], c) if s > 0 else min(p["meilleur"], c)
            gain_r = s * (c - p["e0"]) / R
            if gain_r >= 1.0 and not p["be"]:
                pos = [ps[t] for t in p["tickets"] if t in ps]
                if pos:
                    moyen = sum(q["prix_entree"] * (q.get("lots") or 1) for q in pos) / sum(q.get("lots") or 1 for q in pos)
                    self._poser_stop(moyen)
                p["be"] = True
            if p["be"]:
                self._poser_stop(p["meilleur"] - s * SUIVI_R * R)
            if p["renforts"] < len(SEUILS) and gain_r >= SEUILS[p["renforts"]]:
                p["attente"] = SEUILS[p["renforts"]]
            self.sauver()
            return
        t = time.gmtime(b[0])
        jour = b[0] - b[0] % 86400
        if (t.tm_hour, t.tm_min) != HEURE_ENTREE or self.fait == jour or not permis or self.arrete():
            return
        self.fait = jour
        d1f = [x for x in d1 if x[0] < jour]
        s, R = parametres(d1f)
        if not s or not R:
            self.sauver()
            return
        px = self.pont.prix(SYMBOLE)
        e = px["ask"] if s > 0 else px["bid"]
        r = self._ouvrir(s, LOTS_BASE, e - s * R)
        if r.get("ok") and r.get("ticket"):
            e0 = r.get("prix_obtenu") or e
            self.panier = {"s": s, "tickets": [r["ticket"]], "e0": e0, "R": R,
                           "stop": bt_or.marquer(e - s * R, 2, MARQUE), "meilleur": e0, "renforts": 0, "be": False,
                           "profits": {str(r["ticket"]): 0.0}, "attente": None}
        self.pont.noter(evenement="ouverture", hypothese=NOM, niveau=1, sens=s, ok=bool(r.get("ok")), refus=r.get("refus"),
                        prix_obtenu=r.get("prix_obtenu"), R=round(R, 2), essai="non prouve")
        self.sauver()
