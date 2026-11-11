"""Essais hors ligne du robot du labo sur le faux terminal. Doit finir par « ESSAIS OK »."""
import os
import random

import faux_mt5
import acces_robot
import robot

for f in ("etat_essai.json",):
    if os.path.exists(f):
        os.remove(f)
pont = acces_robot.AccesRobot.pour_essais(faux_mt5)


def barres(n, pas, debut=1794000000, prix=2650.0, pente=0.0, dernier_saut=0.0):
    b = []
    for i in range(n):
        o = prix + pente * i
        c = o + pente + (dernier_saut if i == n - 2 else 0.0)   # n-2 = derniere bougie FERMEE
        b.append([debut + pas * i, o, max(o, c) + 0.5, min(o, c) - 0.5, c, 100, 19])
    return b


# 1) signaux purs
h = random.Random(1)
plat = barres(130, 900)[:-1]
assert robot.signal("elan_m15", plat) == 0 and robot.signal("cassure_m15", plat) == 0
haus = barres(130, 900, pente=0.4)[:-1]
assert robot.signal("elan_m15", haus) == 1
assert robot.signal("elan_m15", barres(130, 900, pente=-0.4)[:-1]) == -1
assert robot.signal("cassure_m15", barres(130, 900, dernier_saut=5.0)[:-1]) == 1
assert robot.signal("cassure_m15", barres(130, 900, dernier_saut=-5.0)[:-1]) == -1
bruit = barres(130, 300)
for i, x in enumerate(bruit):
    x[4] = x[1] + (0.1 if i % 2 else -0.1)
calme = [list(x) for x in bruit]
bruit[-2][4] = bruit[-2][1] + 8.0
assert robot.signal("exces_m5", bruit[:-1]) == 1 and robot.signal("exces_m5", calme[:-1]) == 0
assert robot.signal("exces_m1", bruit[:-1]) == -1 and robot.signal("exces_m1", calme[:-1]) == 0
assert robot.signal("fcassure_m1", barres(130, 60, dernier_saut=5.0)[:-1]) == -1
assert robot.signal("fcassure_m1", plat) == 0
assert robot.signal("elan_m1", haus) == 1 and robot.signal("retour_m1", haus) == -1
assert robot.signal("hasard_m1", plat, h) in (-1, 1)
pic = [list(x) for x in calme[:-1]]
pic[-1][4] = pic[-1][1] + 3.0
assert robot.signal("ecart_midi_m5", pic) == -1 and robot.signal("ecart_midi_m5", calme[:-1]) == 0
creux = [list(x) for x in calme[:-1]]
creux[-1][4] = creux[-1][1] - 3.0
assert robot.signal("ecart_midi_m5", creux) == 1
assert set(robot.HEURES) <= set(robot.HYPOTHESES)
assert len(robot.HYPOTHESES) <= 9 and all(v[0] in robot.PERIODES and v[1] >= 60 for v in robot.HYPOTHESES.values())
assert robot.ecart_stop(plat, 3.0) >= 3.0

# 2) un tour complet : premier tour sans ordre, puis nouvelle bougie -> ouvertures avec stop a 0,01 lot
r = robot.Robot(pont, hasard=random.Random(2), fichier="etat_essai.json")
t0 = [1794000000]
r.heure = lambda: t0[0]
m1 = barres(130, 60, pente=0.1, dernier_saut=9.0)
m5, m15 = barres(130, 300, dernier_saut=9.0), barres(130, 900, pente=0.4, dernier_saut=9.0)
for i, x in enumerate(m5):                              # un peu de bruit, puis un exces sur la derniere fermee
    x[4] = x[1] + (0.1 if i % 2 else -0.1)
m5[-2][4] = m5[-2][1] + 9.0
r.tour({"M1": m1, "M5": m5, "M15": m15})
assert not faux_mt5.ordres_recus and not pont.positions(), "aucun ordre au premier tour"
m5b = [[x[0] + 300] + x[1:] for x in m5]
m15b = [[x[0] + 900] + x[1:] for x in m15]
m1b = [[x[0] + 60] + x[1:] for x in m1]
r.tour({"M1": m1b, "M5": m5b, "M15": m15b})
ps = pont.positions()
assert len(ps) == len(r.ouvert) == 8, (len(ps), sorted(r.ouvert))
assert "ecart_midi_m5" not in r.ouvert, "hors de ses heures"
assert set(r.ouvert) <= set(robot.HYPOTHESES)
for o in faux_mt5.ordres_recus:
    assert o["volume"] == 0.01 and o["sl"] > 0 and o["symbol"] == "XAUUSD", o
for p in ps:
    assert p["stop"] and ((p["sens"] == "achat" and p["stop"] < p["prix_entree"] - 2.9) or
                          (p["sens"] == "vente" and p["stop"] > p["prix_entree"] + 2.9)), p
n = len(faux_mt5.ordres_recus)
r.tour({"M1": m1b, "M5": m5b, "M15": m15b})
assert len(faux_mt5.ordres_recus) == n, "pas de double ouverture sur la meme bougie"

# 3) reprise apres redemarrage : la memoire revient du fichier, rien n'est ferme a tort
r2 = robot.Robot(pont, fichier="etat_essai.json")
assert set(r2.ouvert) == set(r.ouvert)
r2.heure = lambda: t0[0]
r2.reconcilier()
assert len(pont.positions()) == len(ps)

# 4) sorties au temps : 3 min (fausse cassure), 5 min (hasard, elan, retour), puis le reste
t0[0] += 181
r.sorties(t0[0], r.reconcilier())
assert "fcassure_m1" not in r.ouvert and len(pont.positions()) == 7
t0[0] += 120
r.sorties(t0[0], r.reconcilier())
assert not {"hasard_m1", "elan_m1", "retour_m1"} & set(r.ouvert) and len(pont.positions()) == 4
t0[0] += 10800
r.sorties(t0[0], r.reconcilier())
assert not r.ouvert and not pont.positions()

# 5) stop touche chez le courtier (la position disparait) : note, memoire nettoyee ; orpheline fermee
m15c = [[x[0] + 1800] + x[1:] for x in m15]
r.tour({"M1": m1b, "M5": m5b, "M15": m15c})
assert r.ouvert
faux_mt5.positions.clear()
r.reconcilier()
assert not r.ouvert
x = pont.ouvrir("XAUUSD", "achat", 0.01, stop=2600.0, id="inconnue")
assert x["ok"]
r.reconcilier()
assert not pont.positions(), "orpheline fermee"

# 5 bis) l'hypothese de midi ouvre dans ses heures (12-14 h serveur)
faux_mt5.positions.clear()
r3 = robot.Robot(pont, hasard=random.Random(3), fichier="etat_essai.json")
t3 = [1794000000 - 1794000000 % 86400 + 13 * 3600]
r3.heure = lambda: t3[0]
r3.ouvert = {}
r3.tour({"M1": m1, "M5": m5, "M15": m15})
m5d = [[x[0] + 300] + x[1:] for x in m5]
r3.tour({"M1": m1, "M5": m5d, "M15": m15})
assert "ecart_midi_m5" in r3.ouvert and r3.ouvert["ecart_midi_m5"]["sens"] == -1, sorted(r3.ouvert)
faux_mt5.positions.clear()
r3.reconcilier()

# 6) spread trop large : pas d'ouverture ; ouverture sans stop refusee par le pont
faux_mt5._prix["XAUUSD"] = (2650.10, 2651.50)
assert r.ouvrir("elan_m15", 1, plat, t0[0]) is None and not pont.positions()
faux_mt5._prix["XAUUSD"] = (2650.10, 2650.35)
assert not pont.ouvrir("XAUUSD", "achat", 0.01, stop=0)["ok"]
for f in ("etat_essai.json",):
    if os.path.exists(f):
        os.remove(f)
print("ESSAIS OK")
