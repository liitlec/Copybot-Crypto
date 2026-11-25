"""Essais hors ligne du robot RÉEL sur le faux terminal en compte réel cent (USC). Doit finir par « ESSAIS OK ».
Le mode réel du pont (pont_reel.py) est activé dans CE processus ; l'autorisation d'essai est écrite dans le dossier
du robot (jamais ailleurs), avec le numéro factice du faux terminal."""
import os

import faux_mt5
import acces_robot
import pont_reel

pmod = pont_reel.activer_essais(".", faux_mt5)
for f in ("etat_robot.json", "etat_bt_plus.json", "sommet_reel.json", "garde_essai.json"):
    if os.path.exists(f):
        os.remove(f)
pont = acces_robot.AccesRobot.pour_essais(faux_mt5)
import robot
import bt_or

# 0) le pont est en mode réel : compte autorisé, cent, symbole or lu chez le courtier
c = pont.compte()
assert c["ordres_autorises"] and c["devise"] == "USC" and c["symbole_or"] == "XAUUSD" and c["mode"] == "reel", c
assert pmod.MAGIQUE_ROBOT == pont_reel.MAGIQUE_ROBOT_REEL and pmod.MAX_LOTS == 0.10 and pmod.MAX_POSITIONS == 10
assert set(robot.HYPOTHESES) == {"elan_m15", "cassure_m15", "exces_m1", "exces_m5", "retour_court_ar"}, "rien d'autre"
assert len(set(robot.CODE.values())) == 5 and all(v % 10 != 7 for v in robot.CODE.values())


def barres(n, pas, debut=1794000000, prix=2650.0, pente=0.0, dernier_saut=0.0):
    b = []
    for i in range(n):
        o = prix + pente * i
        cl = o + pente + (dernier_saut if i == n - 2 else 0.0)
        b.append([debut + pas * i, o, max(o, cl) + 0.5, min(o, cl) - 0.5, cl, 100, 19])
    return b


# 1) signaux (mêmes règles que la démo)
plat = barres(130, 900)[:-1]
assert robot.signal("elan_m15", plat) == 0 and robot.signal("cassure_m15", plat) == 0
assert robot.signal("elan_m15", barres(130, 900, pente=0.4)[:-1]) == 1
assert robot.signal("cassure_m15", barres(130, 900, dernier_saut=-5.0)[:-1]) == -1
bruit = barres(130, 300)
for i, x in enumerate(bruit):
    x[4] = x[1] + (0.1 if i % 2 else -0.1)
calme = [list(x) for x in bruit]
bruit[-2][4] = bruit[-2][1] + 8.0
assert robot.signal("exces_m5", bruit[:-1]) == 1 and robot.signal("exces_m1", bruit[:-1]) == -1
assert robot.signal("exces_m5", calme[:-1]) == 0
assert robot.sur_grille(0.02, 0.01, 0.01) == 0.02 and robot.sur_grille(0.005, 0.01, 0.01) is None
assert robot.sur_grille(0.025, 0.01, 0.01) == 0.02

# 2) tailles lues chez le courtier ; premier tour sans ordre, puis ouvertures avec stop, 0,01 lot, numéro réel
r = robot.Robot(pont, fichier="etat_robot.json")
t0 = [1794000000]
m1 = barres(130, 60, pente=0.1, dernier_saut=9.0)
m5, m15 = barres(130, 300, dernier_saut=9.0), barres(130, 900, pente=0.4, dernier_saut=9.0)
for i, x in enumerate(m5):
    x[4] = x[1] + (0.1 if i % 2 else -0.1)
m5[-2][4] = m5[-2][1] + 9.0
r.heure = lambda: t0[0]
r.tour({"M1": m1, "M5": m5, "M15": m15})
assert r.sym == "XAUUSD" and r.lots_c == 0.01 and r.btp is not None and r.btp.lots == 0.02 and r.btp.max_pos == 5
assert not faux_mt5.ordres_recus and not pont.positions(), "aucun ordre au premier tour"
dec = lambda b, s: [[x[0] + s] + x[1:] for x in b]
r.tour({"M1": dec(m1, 60), "M5": dec(m5, 300), "M15": dec(m15, 900)})
ps = pont.positions()
assert ps and set(r.ouvert) <= set(robot.HYPOTHESES), sorted(r.ouvert)
for o in faux_mt5.ordres_recus:
    assert o["magic"] == pont_reel.MAGIQUE_ROBOT_REEL and o["volume"] == 0.01 and o["sl"] > 0, o
assert all(robot.NOTE_DU_CODE.get(int(round(p["stop"] * 100)) % 100) for p in ps), "nom code dans le stop"

# 3) reprise après redémarrage (mémoire perdue) : retrouvées par le code du stop, rien fermé
os.remove("etat_robot.json")
r2 = robot.Robot(pont, fichier="etat_robot.json")
r2.heure = lambda: t0[0]
r2.preparer()
r2.reconcilier()
assert set(r2.ouvert) == set(r.ouvert) and len(pont.positions()) == len(ps)

# 4) sortie au temps
t0[0] += 4 * 3600
r.tour({"M1": dec(m1, 60), "M5": dec(m5, 300), "M15": dec(m15, 900)})
assert not r.ouvert and not pont.positions(), "toutes sorties au temps"

# 5) sans autorisation, ou après l'arrêt -34 % : plus aucune ouverture
os.remove(pont_reel.FICHIER_AUTORISATION)
assert not pont.compte()["ordres_autorises"]
avant = len(faux_mt5.ordres_recus)
r.tour({"M1": dec(m1, 120), "M5": dec(m5, 600), "M15": dec(m15, 1800)})
assert len(faux_mt5.ordres_recus) == avant, "sans autorisation : aucun ordre"
assert pont.ouvrir("XAUUSD", "achat", 0.01, stop=2600.0)["ok"] is False
pont_reel.activer_essais(".", faux_mt5)
faux_mt5.valeur = 20000.0
assert pont.compte()["ordres_autorises"]
faux_mt5.valeur = 20000.0 * 0.6
assert not pont.compte()["ordres_autorises"] and "ARRET AUTOMATIQUE" in pont.compte()["arret"]
assert not pont.ouvrir("XAUUSD", "achat", 0.01, stop=2600.0)["ok"]
os.remove(pont_reel.FICHIER_SOMMET)
faux_mt5.valeur = 10000.0
assert pont.compte()["ordres_autorises"], "levee seulement en supprimant sommet_reel.json"

# 6) plafonds du pont réel : 0,11 lot refusé, stop obligatoire
assert "plafond" in pont.ouvrir("XAUUSD", "achat", 0.11, stop=2600.0)["refus"]
assert not pont.ouvrir("XAUUSD", "achat", 0.01, stop=0)["ok"]

# 7) panier bt_or_plus : 0,02 lot de base, renfort à 0,04, stop de secours marqué 97
class FauxPont:
    def __init__(self):
        self.bid, self.pos, self.n, self.notes = 4000.0, {}, 100, []

    def prix(self, s):
        return {"bid": self.bid, "ask": self.bid + 0.2, "heure_serveur": 0}

    def symbole(self, s):
        return {"lot_min": 0.01, "pas_lot": 0.01, "taille_contrat": 100.0, "chiffres": 2, "point": 0.01}

    def ouvrir(self, s, sens, lots, stop, objectif=None, id="robot"):
        assert s == "XAUUSD.c" and stop > 0 and id.startswith("bt_or_plus_") and lots <= 0.10 + 1e-9
        self.n += 1
        e = self.bid + 0.2 if sens == "achat" else self.bid
        self.pos[self.n] = {"ticket": self.n, "sens": sens, "prix_entree": e, "stop": stop, "profit": 0.0, "id": id,
                            "lots": lots, "symbole": s}
        return {"ok": True, "ticket": self.n, "prix_obtenu": e}

    def fermer(self, t):
        return {"ok": self.pos.pop(t, None) is not None}

    def modifier(self, t, stop, objectif=None):
        self.pos[t]["stop"] = stop
        return {"ok": True}

    def noter(self, **k):
        self.notes.append(k)
        return True


def m5_jusqua(h, m, prix, n=2600, base=3900.0):
    fin = 1794009600 - 1794009600 % 86400 + h * 3600 + m * 60
    return [[fin - 300 * (n - 1 - i), 0, base + (prix - base) * i / (n - 1) + 1, base + (prix - base) * i / (n - 1) - 1,
             base + (prix - base) * i / (n - 1), 1, 20] for i in range(n)]


d1 = [[i * 86400, 4000, 4030, 3970, 4000, 1, 20] for i in range(29)]
fp = FauxPont()
bp = bt_or.PanierBT(fp, fichier="etat_bt_plus.json", symbole="XAUUSD.c", nom="bt_or_plus", lots=0.02, taille=100.0,
                    max_pos=5, croissant=True)
bp.bougie(m5_jusqua(8, 0, 4000.0), d1, True)
q = list(fp.pos.values())
assert len(q) == 1 and q[0]["lots"] == 0.02 and bt_or.code_marque(q[0]["stop"]) == bt_or.MARQUE_PLUS
fp.bid = 4016.0
bp.surveiller({x["ticket"]: x for x in fp.pos.values()}, fp.prix("XAUUSD.c"))
bp.bougie(m5_jusqua(8, 35, 4016.0), d1, True)
assert sorted(x["lots"] for x in fp.pos.values()) == [0.02, 0.04], "renfort a 2 x la base"

# 8) symbole avec suffixe chez le courtier : lu, pas supposé
ancien = faux_mt5._prix.pop("XAUUSD")
faux_mt5._prix["XAUUSD.c"] = ancien
assert pont_reel.symbole_or(faux_mt5) == "XAUUSD.c" and pont.compte()["symbole_or"] == "XAUUSD.c"
faux_mt5._prix["XAUUSD"] = faux_mt5._prix.pop("XAUUSD.c")

for f in ("etat_robot.json", "etat_bt_plus.json", "sommet_reel.json", "garde_essai.json", "journal_essai.jsonl",
          pont_reel.FICHIER_AUTORISATION):
    if os.path.exists(f):
        os.remove(f)
print("ESSAIS OK")
