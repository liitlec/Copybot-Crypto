"""Essais hors ligne du robot du labo sur le faux terminal. Doit finir par « ESSAIS OK »."""
import os
import random

import faux_mt5
import acces_robot
import robot
ETEINTES_V7 = set(robot.ETEINTES)
robot.ETEINTES = set()  # les essais historiques supposent toutes les hypotheses actives

for f in ("etat_essai.json",):
    if os.path.exists(f):
        os.remove(f)
pont = acces_robot.AccesRobot.pour_essais(faux_mt5)

# 17/11 : sous Windows, remplacer garde_essai.json echoue parfois (fichier tenu un instant par l'antivirus ou
# l'indexeur : WinError 5) ; la v16 a ete refusee pour cela. On reessaie quelques fois avant d'abandonner.
import time as _time
_ecrire_json = acces_robot.pont.ecrire_json


def _ecrire_json_patient(chemin, objet):
    for essai in range(40):
        try:
            return _ecrire_json(chemin, objet)
        except PermissionError:
            if essai == 39:
                raise
            _time.sleep(0.05)


acces_robot.pont.ecrire_json = _ecrire_json_patient


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
assert len(robot.HYPOTHESES) <= 11 and all(v[0] in robot.PERIODES and v[1] >= 60 for v in robot.HYPOTHESES.values())
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
assert len(ps) == len(r.ouvert) >= 9, (len(ps), sorted(r.ouvert))
assert all(k.endswith("_opt") or k in robot.HYPOTHESES for k in r.ouvert)
assert "retour_court_ar" in r.ouvert and "retour_strict_ar" not in r.ouvert, "v14 : le strict attend son detecteur"
oc = [o for o in faux_mt5.ordres_recus if o.get("comment", "").endswith("retour_court_ar")]
assert oc and oc[0]["sl"] > 0, oc
assert "ecart_midi_m5" not in r.ouvert, "hors de ses heures"
assert {k[:-4] if k.endswith("_opt") else k for k in r.ouvert} <= set(robot.HYPOTHESES)
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
# v13 : memoire perdue (changement de version) -> chaque position reprise par le code de son stop, rien ferme
assert all(robot.NOTE_DU_CODE.get(int(round(p["stop"] * 100)) % 100) for p in pont.positions()), "stops codes"
if os.path.exists("etat_vide.json"):
    os.remove("etat_vide.json")
_cd, robot.CODE_DEPUIS = robot.CODE_DEPUIS, 0
r3b = robot.Robot(pont, fichier="etat_vide.json")
r3b.heure = lambda: t0[0]
assert not r3b.ouvert
r3b.reconcilier()
robot.CODE_DEPUIS = _cd
assert len(pont.positions()) == len(ps), "aucune position fermee comme orpheline"
assert set(r3b.ouvert) == set(r.ouvert), (sorted(r3b.ouvert), sorted(r.ouvert))
for k, o in r.ouvert.items():
    q = r3b.ouvert[k]
    assert q["ticket"] == o["ticket"] and q["note"] == o["note"] and q["sens"] == o["sens"], (k, q, o)
    assert abs(q["sortie"] - o["sortie"]) <= 2, (k, q["sortie"], o["sortie"])
assert set(robot.HYPOTHESES_NOMS) == set(robot.HYPOTHESES), "liste des noms codes a jour"
r3b.tour_crypto({}, t0[0], True)                  # v13 : symboles crypto absents du faux terminal -> note, pas de plantage
assert [c.nom for c in r3b.crypto] == ["bt_crypto_btc", "bt_crypto_eth"]
os.remove("etat_vide.json")
assert robot.coder(2650.13, 1, "hasard_m1") <= 2650.13 and robot.coder(2650.13, -1, "hasard_m1") >= 2650.13
assert all(c % 10 != 7 for c in robot.CODE.values()) and len(set(robot.CODE.values())) == len(robot.CODE)

# 4) sorties au temps : 3 min (fausse cassure), 5 min (hasard, elan, retour), puis le reste
t0[0] += 181
r.sorties(t0[0], r.reconcilier())
assert "fcassure_m1" not in r.ouvert and len(pont.positions()) == len(ps) - 1
t0[0] += 120
r.sorties(t0[0], r.reconcilier())
assert not {"hasard_m1", "elan_m1", "retour_m1"} & set(r.ouvert) and len(pont.positions()) == len(ps) - 4
t0[0] += 10800
r.sorties(t0[0], r.reconcilier())
assert not r.ouvert and not pont.positions()

# 5) stop touche chez le courtier (la position disparait) : note, memoire nettoyee ; orpheline fermee
m15c = [[x[0] + 1800] + x[1:] for x in m15]
t0[0] += 7200                                            # sortir de la fenetre de fermeture nocturne (0 h 25 -> 2 h 25)
r.tour({"M1": m1b, "M5": m5b, "M15": m15c})
assert r.ouvert
faux_mt5.positions.clear()
r.reconcilier()
assert not r.ouvert
x = pont.ouvrir("XAUUSD", "achat", 0.01, stop=2645.0, id="inconnue")   # stop proche : pas un panier bt_or (v12)
assert x["ok"]
r.reconcilier()
assert not pont.positions(), "orpheline fermee"

# 5 bis) l'hypothese de midi ouvre dans ses heures (12-14 h serveur)
faux_mt5.positions.clear()
pont = acces_robot.AccesRobot.pour_essais(faux_mt5)       # pont neuf : plafond de 30 ordres par minute (v15 : 2 ordres _opt)
r3 = robot.Robot(pont, hasard=random.Random(3), fichier="etat_essai.json")
t3 = [1794000000 - 1794000000 % 86400 + 13 * 3600]
r3.heure = lambda: t3[0]
r3.ouvert = {}
r3.tour({"M1": m1, "M5": m5, "M15": m15})
m5d = [[x[0] + 300] + x[1:] for x in m5]
r3.tour({"M1": m1, "M5": m5d, "M15": m15})
assert "ecart_midi_m5" in r3.ouvert and r3.ouvert["ecart_midi_m5"]["sens"] == -1, sorted(r3.ouvert)
assert r3.ouvert["ecart_midi_m5"]["note"] == "midi_calme", "faux terminal : H1 plat = regime calme"
assert any(o.get("comment", "").endswith("midi_calme") for o in faux_mt5.ordres_recus), "etiquette dans l'ordre"
import math
calme_h1 = [[i * 3600, 0, 0, 0, 2650.0 * math.exp(0.0002 * (i % 2)), 1, 19] for i in range(1500)]
assert robot.agite(calme_h1) is False
agite_h1 = [list(x) for x in calme_h1]
for i in range(1470, 1500):
    agite_h1[i][4] = 2650.0 * math.exp(0.004 * (i % 2))
assert robot.agite(agite_h1) is True and robot.agite(calme_h1[:500]) is None
assert r3.etiquette("elan_m1") == "elan_m1"
faux_mt5.positions.clear()
r3.reconcilier()

# 5 ter) pas d'ouverture autour de la fermeture nocturne (23 h 50 - 1 h 10 serveur)
r4 = robot.Robot(pont, hasard=random.Random(4), fichier="etat_essai.json")
t4 = [1794000000 - 1794000000 % 86400 + 30 * 60]
r4.heure = lambda: t4[0]
r4.ouvert = {}
r4.vu = {"M1": 0, "M5": 0, "M15": 0}
r4.tour({"M1": m1, "M5": m5, "M15": m15})
assert not r4.ouvert and not pont.positions(), "rien a 0 h 30 serveur"

# 6) spread trop large : pas d'ouverture ; ouverture sans stop refusee par le pont
faux_mt5._prix["XAUUSD"] = (2650.10, 2651.50)
assert r.ouvrir("elan_m15", 1, plat, t0[0]) is None and not pont.positions()
faux_mt5._prix["XAUUSD"] = (2650.10, 2650.35)
assert not pont.ouvrir("XAUUSD", "achat", 0.01, stop=0)["ok"]
# 7) panier bt_or (mecanique BlockTrend) sur un faux pont a prix pilotes
import bt_or


class FauxPont:
    def __init__(self):
        self.bid, self.pos, self.n, self.notes, self.modifs = 4000.0, {}, 100, [], []

    def prix(self, s):
        return {"bid": self.bid, "ask": self.bid + 0.2, "heure_serveur": 0}

    def ouvrir(self, s, sens, lots, stop, objectif=None, id="robot"):
        assert lots == 0.01 and stop > 0 and id.startswith("bt_or_")
        assert (sens == "achat" and stop < self.bid) or (sens == "vente" and stop > self.bid + 0.2)
        self.n += 1
        e = self.bid + 0.2 if sens == "achat" else self.bid
        self.pos[self.n] = {"ticket": self.n, "sens": sens, "prix_entree": e, "stop": stop, "profit": 0.0, "id": id}
        return {"ok": True, "ticket": self.n, "prix_obtenu": e}

    def fermer(self, t):
        return {"ok": self.pos.pop(t, None) is not None}

    def modifier(self, t, stop, objectif=None):
        self.pos[t]["stop"] = stop
        self.modifs.append((t, stop))
        return {"ok": True}

    def noter(self, **k):
        self.notes.append(k)
        return True

    def positions(self):
        for p in self.pos.values():
            s = 1 if p["sens"] == "achat" else -1
            p["profit"] = round(s * ((self.bid if s > 0 else self.bid + 0.2) - p["prix_entree"]), 2)
        return list(self.pos.values())


def m5_jusqua(h, m, prix, n=2600, base=3900.0):
    """n bougies M5 fermees finissant par celle de h:m (serveur), en hausse de base a prix."""
    fin = 1794009600 - 1794009600 % 86400 + h * 3600 + m * 60
    return [[fin - 300 * (n - 1 - i), 0, base + (prix - base) * i / (n - 1) + 1, base + (prix - base) * i / (n - 1) - 1,
             base + (prix - base) * i / (n - 1), 1, 20] for i in range(n)]


d1 = [[i * 86400, 4000, 4030, 3970, 4000, 1, 20] for i in range(29)]      # amplitude vraie 60 $ -> ATR 60
assert abs(bt_or.atr_jour(d1) - 60.0) < 1e-9 and bt_or.atr_jour(d1[:5]) is None
assert abs(bt_or.ema([5.0] * 50, 10) - 5.0) < 1e-9
if os.path.exists("etat_bt_essai.json"):
    os.remove("etat_bt_essai.json")
fp = FauxPont()
bt = bt_or.PanierBT(fp, fichier="etat_bt_essai.json")
bt.bougie(m5_jusqua(9, 0, 4000.0), d1, True)
assert not fp.pos, "pas d'entree hors des heures fixes"
bt.bougie(m5_jusqua(8, 0, 4000.0), d1, False)
assert not fp.pos, "pas d'entree si le spread est trop large"
bt.vu = None
bt.bougie(m5_jusqua(8, 0, 4000.0), d1, True)
assert len(fp.pos) == 1 and "1" in bt.paniers, "achat : cours au-dessus de l'EMA"
p = bt.paniers["1"]
assert abs(p["stop"] - 40.002) < 0.01 and abs(p["pas"] - 15.0) < 1e-6 and abs(p["prochain"] - 4015.0) < 1e-6
assert abs(list(fp.pos.values())[0]["stop"] - (4000 - 1.25 * 40.002)) < 0.1, "stop de secours chez le courtier (marque v12 : quelques centimes)"
bt.bougie(m5_jusqua(8, 30, 4005.0), d1, True)
assert len(fp.pos) == 1, "un seul panier par cote, pas d'ajout avant le pas"
fp.bid = 4016.0
bt.surveiller({q["ticket"]: q for q in fp.positions()}, fp.prix("XAUUSD"))
bt.bougie(m5_jusqua(8, 35, 4016.0), d1, True)
assert len(fp.pos) == 2, "ajout dans le sens du gain au premier pas"
fp.bid = 4055.0                                           # saute deux pas d'un coup : niveau saute, puis un seul ajout au plus
bt.surveiller({q["ticket"]: q for q in fp.positions()}, fp.prix("XAUUSD"))
bt.bougie(m5_jusqua(8, 40, 4055.0), d1, True)
assert len(fp.pos) <= 3 and fp.modifs, "3 positions au plus ; stop de secours remonte"
assert all(q["stop"] > 4000 - 1.25 * 40.002 + 1 for q in fp.pos.values()), "le stop n'a fait que monter"
n_avant = len(fp.pos)
fp.bid = 4055.0 - 39.0
bt.surveiller({q["ticket"]: q for q in fp.positions()}, fp.prix("XAUUSD"))
assert len(fp.pos) == n_avant, "pas de sortie avant le recul complet"
fp.bid = 4055.0 - 40.5
bt.surveiller({q["ticket"]: q for q in fp.positions()}, fp.prix("XAUUSD"))
assert not fp.pos and not bt.paniers and bt.n_paniers == 1, "tout le panier sort sur le recul"
assert any(k.get("evenement") == "sortie panier" for k in fp.notes)
# reprise apres redemarrage et stop de secours touche chez le courtier
bt.vu = None
fp.bid = 3900.0
bas = [[x[0], 0, 4101 - i * 0.05, 4099 - i * 0.05, 4100 - i * 0.05, 1, 20] for i, x in enumerate(m5_jusqua(12, 0, 3900.0))]
bt.bougie(bas, d1, True)
assert "-1" in bt.paniers and list(fp.pos.values())[0]["sens"] == "vente", "vente : cours sous l'EMA"
bt2 = bt_or.PanierBT(fp, fichier="etat_bt_essai.json")
assert bt2.tickets() == bt.tickets() and bt2.n_paniers == 1
fp.pos.clear()
bt2.surveiller({}, fp.prix("XAUUSD"))
assert not bt2.paniers and bt2.n_paniers == 2
bt2.cumul_r = -20.5
assert bt2.arrete(), "regle d'arret a -20 R"
bt2.vu = None
bt2.bougie(m5_jusqua(8, 0, 4000.0), d1, True)
assert not fp.pos, "plus d'entree apres la regle d'arret"
# le robot ne ferme pas les positions du panier comme orphelines
x = pont.ouvrir("XAUUSD", "achat", 0.01, stop=2600.07, id="bt_or_1")      # stop marque (v12)
r.bt.paniers["1"] = {"tickets": [x["ticket"]], "profits": {}, "meilleur": 2650.1, "stop": 40.0, "pas": 15.0,
                      "prochain": 2665.0, "debut": 0, "secours": 2600.0}
r.reconcilier()
assert len(pont.positions()) == 1, "position du panier conservee"
r.bt.paniers.clear()                                      # v12 : memoire perdue (changement de version) -> panier repris
r.reconcilier()
assert len(pont.positions()) == 1 and "1" in r.bt.paniers, "panier bt_or repris, pas ferme comme orphelin"
assert any(k.get("evenement") == "reprise" and k.get("hypothese") == "bt_or" for k in faux_mt5.notes_lues()) \
    if hasattr(faux_mt5, "notes_lues") else True
pont.fermer(x["ticket"])
r.bt.paniers.clear()
y = pont.ouvrir("XAUUSD", "achat", 0.01, stop=2645.0, id="hasard_m1")       # petite position inconnue : orpheline
r.reconcilier()
assert not pont.positions() and not r.bt.paniers, "une petite position inconnue reste fermee comme orpheline"
# v12 : redemarrage avec un panier bt_or ouvert -> panier repris, rien ferme, meme stop suiveur
fp3 = FauxPont()
bt3 = bt_or.PanierBT(fp3, fichier="etat_bt_essai3.json")
bt3.bougie(m5_jusqua(8, 0, 4000.0), d1, True)
fp3.bid = 4016.0
bt3.surveiller({q["ticket"]: q for q in fp3.positions()}, fp3.prix("XAUUSD"))
bt3.bougie(m5_jusqua(8, 35, 4016.0), d1, True)
assert len(fp3.pos) == 2 and all(bt_or.marque(q["stop"]) for q in fp3.pos.values()), "stops marques"
debut = m5_jusqua(8, 0, 4000.0)[-1][0] + 300
for i, q in enumerate(sorted(fp3.pos.values(), key=lambda q: q["ticket"])):
    q["symbole"], q["heure_serveur"], q["prix_actuel"] = "XAUUSD", debut + 2100 * i, fp3.bid
m5r = m5_jusqua(8, 35, 4016.0)
av = bt3.paniers["1"]
os.remove("etat_bt_essai3.json")
bt4 = bt_or.PanierBT(fp3, fichier="etat_bt_essai3.json")                     # memoire vide
assert not bt4.paniers
bt4.adopter({q["ticket"]: q for q in fp3.positions()}, m5r, d1)
ap = bt4.paniers.get("1")
assert ap and sorted(ap["tickets"]) == sorted(av["tickets"]) and len(fp3.pos) == 2, "panier repris, rien ferme"
assert abs(ap["stop"] - av["stop"]) < 1e-6 and abs(ap["pas"] - av["pas"]) < 1e-6, "meme distance de stop suiveur"
assert abs(ap["meilleur"] - av["meilleur"]) <= 1.0 and abs(ap["prochain"] - av["prochain"]) <= 0.5, (ap, av)   # entree = ask : un spread d ecart
assert ap["secours"] == min(q["stop"] for q in fp3.pos.values())
# v13 : bt_crypto sur un faux pont BTC (taille minimale du courtier, contrat de 1)
class FauxPontC(FauxPont):
    def ouvrir(self, s, sens, lots, stop, objectif=None, id="robot"):
        assert s == "BTCUSD" and lots == 0.01 and id.startswith("bt_crypto_btc_"), (s, lots, id)
        self.n += 1
        e = self.bid + 20 if sens == "achat" else self.bid
        self.pos[self.n] = {"ticket": self.n, "symbole": s, "sens": sens, "prix_entree": e, "stop": stop, "profit": 0.0,
                            "id": id, "heure_serveur": 0, "prix_actuel": self.bid}
        return {"ok": True, "ticket": self.n, "prix_obtenu": e}

    def prix(self, s):
        return {"bid": self.bid, "ask": self.bid + 20, "heure_serveur": 0}

    def symbole(self, s):
        return {"lot_min": 0.01, "taille_contrat": 1.0, "chiffres": 2, "point": 0.01, "pas_lot": 0.01}

fc = FauxPontC()
fc.bid = 90000.0
d1c = [[i * 86400, 90000, 91500, 88500, 90000, 1, 20] for i in range(29)]     # ATR 3 000 $
bc = bt_or.PanierBT(fc, fichier="etat_c_essai.json", symbole="BTCUSD", nom="bt_crypto_btc", lots=None, taille=None)
bc.bougie(m5_jusqua(8, 0, 90000.0, base=88000.0), d1c, True)
assert len(fc.pos) == 1 and "1" in bc.paniers and bc.lots == 0.01 and bc.taille == 1.0
q = list(fc.pos.values())[0]
assert bt_or.marque(q["stop"]) and abs(q["stop"] - (90000 - 1.25 * 0.6667 * 3000)) < 0.1
assert any(k.get("hypothese") == "bt_crypto_btc" for k in fc.notes)
os.remove("etat_c_essai.json")
bc2 = bt_or.PanierBT(fc, fichier="etat_c_essai.json", symbole="BTCUSD", nom="bt_crypto_btc", lots=0.01, taille=1.0)
bc2.adopter({t: x for t, x in fc.pos.items()}, m5_jusqua(8, 0, 90000.0, base=88000.0), d1c)
assert bc2.tickets() == bc.tickets(), "panier crypto repris apres perte de memoire"
assert not bt_or.PanierBT(fc, fichier="x_essai.json").candidat(q, d1c), "bt_or ne prend pas une position BTC"
fc.bid = bc2.paniers["1"]["meilleur"] - bc2.paniers["1"]["stop"] - 1
bc2.surveiller({t: x for t, x in fc.pos.items()}, fc.prix("BTCUSD"))
assert not fc.pos and bc2.n_paniers == 1 and abs(bc2.cumul_r) < 2, bc2.cumul_r
for f in ("etat_c_essai.json", "x_essai.json"):
    if os.path.exists(f):
        os.remove(f)
# panier d'avant la v12 (stop sans marque, deja suivi) : repris par l'heure d'entree ; l'ajout par le meme stop
anc = {1: {"ticket": 1, "symbole": "XAUUSD", "sens": "vente", "prix_entree": 3851.07, "prix_actuel": 3840.0,
           "stop": 3910.68, "profit": 11.0, "heure_serveur": 1794816000 - 1794816000 % 86400 + 8 * 3600 + 302},
       2: {"ticket": 2, "symbole": "XAUUSD", "sens": "vente", "prix_entree": 3830.0, "prix_actuel": 3840.0,
           "stop": 3910.68, "profit": -10.0, "heure_serveur": 1794816000 - 1794816000 % 86400 + 9 * 3600 + 7},
       3: {"ticket": 3, "symbole": "XAUUSD", "sens": "achat", "prix_entree": 3862.41, "prix_actuel": 3840.0,
           "stop": 3821.71, "profit": -22.0, "heure_serveur": 1794816000 - 1794816000 % 86400 + 10 * 3600 + 905},
       4: {"ticket": 4, "symbole": "XAUUSD", "sens": "achat", "prix_entree": 3864.01, "prix_actuel": 3840.0,
           "stop": 3857.15, "profit": -24.0, "heure_serveur": 1794816000 - 1794816000 % 86400 + 8 * 3600 + 301}}
d1o = [[i * 86400, 3850, 3893, 3807, 3850, 1, 20] for i in range(29)]       # ATR 86 $
bt5 = bt_or.PanierBT(FauxPont(), fichier="etat_bt_essai5.json")
bt5.adopter(anc, [], d1o)
assert set(bt5.paniers) == {"-1"} and sorted(bt5.paniers["-1"]["tickets"]) == [1, 2], bt5.paniers
assert abs(bt5.paniers["-1"]["stop"] - 0.6667 * 86) < 0.01
os.remove("etat_bt_essai5.json")
fp3.bid = av["meilleur"] - av["stop"] - 1.5
bt4.surveiller({q["ticket"]: q for q in fp3.positions()}, fp3.prix("XAUUSD"))
assert not fp3.pos and bt4.n_paniers == 1, "le panier repris sort sur le meme recul"
os.remove("etat_bt_essai3.json")
for f in ("etat_essai.json", "etat_bt_essai.json", "etat_bt.json"):
    if os.path.exists(f):
        os.remove(f)
# 7) v7 : une hypothese eteinte n'ouvre plus rien
assert "retour_m1" in ETEINTES_V7
# 8) v8 : elan_m1 eteinte aussi
assert "elan_m1" in ETEINTES_V7
# 9) v9 : repli_ind (achat d'un indice apres un repli court, en tendance haussiere)
import repli_ind


class PontIndice:
    def __init__(self):
        self.pos, self.n, self.notes, self.b, self.bid, self.ecart = {}, 500, [], [], 20000.0, 1.0

    def bougies(self, s, periode="M1", nombre=100):
        if s != "NAS100+":
            raise ValueError("symbole absent")
        return self.b[-nombre:]

    def prix(self, s):
        return {"bid": self.bid, "ask": self.bid + self.ecart, "heure_serveur": 0}

    def symbole(self, s):
        return {"point": 0.01, "chiffres": 2, "lot_min": 0.1, "pas_lot": 0.1, "taille_contrat": 1.0, "niveau_stops_points": 0}

    def ouvrir(self, s, sens, lots, stop, objectif=None, id="robot"):
        assert s == "NAS100+" and sens == "achat" and lots == 0.1 and 0 < stop < self.bid and id == "repli_ind"
        self.n += 1
        self.pos[self.n] = {"ticket": self.n, "symbole": s, "sens": sens, "prix_entree": self.bid + self.ecart, "stop": stop, "profit": 0.0}
        return {"ok": True, "ticket": self.n, "prix_obtenu": self.bid + self.ecart}

    def fermer(self, t):
        return {"ok": self.pos.pop(t, None) is not None, "prix_obtenu": self.bid}

    def noter(self, **k):
        self.notes.append(k)

    def ps(self):
        return dict(self.pos)


def jours(clotures):
    return [[i * 86400, c, c + 100, c - 100, c, 1, 80] for i, c in enumerate(clotures)]


hausse = [10000 + 40 * i for i in range(250)]
assert repli_ind.rsi2(hausse) > 99 and repli_ind.rsi2(hausse + [hausse[-1] - 300, hausse[-1] - 600]) < 10
assert not repli_ind.signal_entree(jours(hausse)), "pas de repli : pas d'achat"
repli = hausse + [hausse[-1] - 300, hausse[-1] - 600]
assert repli_ind.signal_entree(jours(repli)), "repli court au-dessus de la moyenne 200 j : achat"
assert not repli_ind.signal_entree(jours([20000 - 40 * i for i in range(252)])), "sous la moyenne 200 j : pas d'achat"
if os.path.exists("etat_repli_essai.json"):
    os.remove("etat_repli_essai.json")
pi = PontIndice()
rp = repli_ind.Repli(pi, fichier="etat_repli_essai.json")
pi.b = jours(repli + [repli[-1]])                        # la derniere bougie = journee en cours
jour = pi.b[-1][0]
pi.bid = float(repli[-1])
rp.tour(pi.ps(), jour + 4 * 3600, True)
assert not pi.pos, "plus de 180 minutes apres le debut de la journee : pas d'achat"
rp.dernier = 0
pi.ecart = 50.0
rp.tour(pi.ps(), jour + 3600, True)
assert not pi.pos, "spread anormal : on attend"
pi.ecart = 1.0
rp.tour(pi.ps(), jour + 3620, True)
assert not pi.pos, "une verification par minute au plus"
rp.tour(pi.ps(), jour + 3700, False)
assert not pi.pos, "ouvertures bloquees : pas d'achat"
rp.tour(pi.ps(), jour + 3800, True)
assert len(pi.pos) == 1 and "NAS100+" in rp.pos, "achat a la taille minimale, avec stop"
p0 = list(pi.pos.values())[0]
assert abs(p0["stop"] - (pi.bid - 2 * repli_ind.atr(pi.b[:-1]))) < 0.02, "stop a 2 ATR"
assert any(n.get("evenement") == "erreur" and n.get("symbole") == "SP500+" for n in pi.notes), "indice absent : note, sans plantage"
rp.tour(pi.ps(), jour + 3900, True)
assert len(pi.pos) == 1, "une position au plus par indice"
rp2 = repli_ind.Repli(pi, fichier="etat_repli_essai.json")
assert rp2.tickets() == rp.tickets(), "reprise apres redemarrage"
pi.b = jours(repli + [repli[-1] - 50, repli[-1] - 50])   # une journee de plus, fermee sous la moyenne 5 j
rp.tour(pi.ps(), jour + 86400 + 3600, True)
assert len(pi.pos) == 1, "pas de sortie sous la moyenne 5 j"
pi.b = jours(repli + [repli[-1] - 50, repli[-1] + 900, repli[-1] + 900])
pi.bid = repli[-1] + 900.0
rp.tour(pi.ps(), jour + 2 * 86400 + 3600, True)
assert not pi.pos and not rp.pos, "sortie quand la cloture repasse au-dessus de la moyenne 5 j"
assert [n for n in pi.notes if n.get("evenement") == "sortie"][-1]["bp"] > 0
rp.tour(pi.ps(), jour + 2 * 86400 + 3700, True)
assert not pi.pos, "pas de nouvel achat le jour d'une sortie"
# sortie apres 10 jours, stop touche, reprise d'une position inconnue (changement de version)
assert repli_ind.signal_sortie(jours([100.0 - i for i in range(30)]), 21 * 86400) is None
assert repli_ind.signal_sortie(jours([100.0 - i for i in range(30)]), 20 * 86400) == "10 jours"
pi.pos[900] = {"ticket": 900, "symbole": "NAS100+", "sens": "achat", "prix_entree": 20000.0, "stop": 19000.0, "profit": 0.0}
os.remove("etat_repli_essai.json")
rp3 = repli_ind.Repli(pi, fichier="etat_repli_essai.json")
rp3.adopter(pi.ps())
assert rp3.tickets() == [900], "position sur un indice reprise, pas fermee"
pi.pos.clear()
rp3.tour(pi.ps(), jour + 9 * 86400, True)
assert not rp3.pos and any(n.get("raison", "").startswith("stop") for n in pi.notes), "stop touche chez le courtier : note"
os.remove("etat_repli_essai.json")
# le robot complet ne ferme pas une position d'indice comme orpheline
pont = acces_robot.AccesRobot.pour_essais(faux_mt5)       # pont neuf : plafond de 30 ordres par minute (v14 : un ordre de plus)
pont.ouvrir("EURUSD", "achat", 0.01, stop=1.0, id="autre")
r9 = robot.Robot(pont, hasard=random.Random(1), fichier="etat_essai.json")
r9.repli.fichier = "etat_repli_essai.json"
import repli_ind as _ri
_ri_sym = _ri.SYMBOLES
_ri.SYMBOLES = ("EURUSD",)
r9.reconcilier()
assert len(pont.positions()) == 1 and r9.repli.tickets(), "position d'indice gardee par le robot"
_ri.SYMBOLES = _ri_sym
r9.repli.pos.clear()
r9.reconcilier()
assert not pont.positions(), "hors indices : orpheline fermee comme avant"
for f in ("etat_essai.json", "etat_repli_essai.json", "etat_repli.json"):
    if os.path.exists(f):
        os.remove(f)
# 10) v11 : au calme, les regles de PAUSE_AU_CALME n'ouvrent plus ; elles reprennent quand l'or redevient agite
faux_mt5.positions.clear()
pont10 = acces_robot.AccesRobot.pour_essais(faux_mt5)       # pont neuf : le plafond de 30 ordres par minute repart de zero
r10 = robot.Robot(pont10, hasard=random.Random(2), fichier="etat_essai.json")
r10.ouvert = {}
t10 = [1794000000]
r10.heure = lambda: t10[0]
r10.tour({"M1": m1, "M5": m5, "M15": m15, "H1": calme_h1 + [calme_h1[-1]]})
assert r10.calme is True
r10.tour({"M1": m1b, "M5": m5b, "M15": m15b, "H1": calme_h1 + [calme_h1[-1]]})
assert r10.ouvert and not (set(r10.ouvert) & robot.PAUSE_AU_CALME), sorted(r10.ouvert)
assert "hasard_m1" in r10.ouvert, "le temoin continue au calme"
# v12 : les variantes <nom>_calme tradent au calme, sous leur propre nom, avec stop
vc = {k for k in r10.ouvert if k.endswith(robot.SUFFIXE_CALME)}
assert vc and all(k[:-len(robot.SUFFIXE_CALME)] in robot.PAUSE_AU_CALME for k in vc), sorted(r10.ouvert)
assert all(r10.ouvert[k]["note"] == k for k in vc)
assert any(o.get("comment", "").endswith("_calme") for o in faux_mt5.ordres_recus), "nom calme dans l'ordre"
faux_mt5.positions.clear()
r10.ouvert = {}
r10.calme_vu = 0
m1c = [[x[0] + 120] + x[1:] for x in m1]
m5c = [[x[0] + 600] + x[1:] for x in m5]
m15c = [[x[0] + 1800] + x[1:] for x in m15]
r10.tour({"M1": m1c, "M5": m5c, "M15": m15c, "H1": agite_h1 + [agite_h1[-1]]})
assert r10.calme is False and (set(r10.ouvert) & robot.PAUSE_AU_CALME), "reprise quand l'or bouge"
assert not any(k.endswith(robot.SUFFIXE_CALME) for k in r10.ouvert), "pas de variante calme quand l'or bouge"
faux_mt5.positions.clear()
r10.ouvert = {}
r10.reconcilier()
for f in ("etat_essai.json", "etat_bt.json", "etat_repli.json"):
    if os.path.exists(f):
        os.remove(f)
print("ESSAIS OK")


# v15 : rebond_nas_opt (contre-pied d'une journee de grande amplitude sur le Nasdaq, une journee)
import rebond_nas


class PontRebond(PontIndice):
    def ouvrir(self, s, sens, lots, stop, objectif=None, id="robot"):
        assert s == "NAS100+" and lots == 0.1 and id == "rebond_nas_opt"
        assert (stop < self.bid) if sens == "achat" else (stop > self.bid + self.ecart)
        self.n += 1
        self.pos[self.n] = {"ticket": self.n, "symbole": s, "sens": sens, "prix_entree": self.bid, "stop": stop, "profit": 0.0}
        return {"ok": True, "ticket": self.n, "prix_obtenu": self.bid}


def d1(clo, amp):
    return [(i * 86400, c, c + a / 2.0, c - a / 2.0, c, 1000, 10, 100) for i, (c, a) in enumerate(zip(clo, amp))]


calme = [20000.0 + i for i in range(30)]
assert rebond_nas.signal(d1(calme, [100.0] * 30)) == 0, "journee ordinaire : rien"
assert rebond_nas.signal(d1(calme + [19700.0], [100.0] * 30 + [400.0])) == 1, "grande journee de baisse : achat"
assert rebond_nas.signal(d1(calme + [20400.0], [100.0] * 30 + [400.0])) == -1, "grande journee de hausse : vente"
assert rebond_nas.signal(d1(calme + [19700.0], [100.0] * 30 + [140.0])) == 0, "amplitude sous 1,5 mediane : rien"
if os.path.exists("etat_rebond_essai.json"):
    os.remove("etat_rebond_essai.json")
pr = PontRebond()
rb = rebond_nas.Rebond(pr, fichier="etat_rebond_essai.json")
pr.b = d1(calme + [20400.0, 20400.0], [100.0] * 30 + [400.0, 50.0])     # derniere bougie = journee en cours
jr = pr.b[-1][0]
pr.bid = 20400.0
rb.tour(pr.ps(), jr + 4 * 3600, True)
assert not pr.pos, "trop tard dans la journee : pas d'entree"
rb.dernier = 0
rb.tour(pr.ps(), jr + 600, False)
assert not pr.pos, "ouvertures bloquees : pas d'entree"
rb.dernier = 0
rb.tour(pr.ps(), jr + 700, True)
assert len(pr.pos) == 1 and list(pr.pos.values())[0]["sens"] == "vente", "vente apres une grande journee de hausse"
assert rebond_nas.Rebond(pr, fichier="etat_rebond_essai.json").tickets() == rb.tickets(), "reprise apres redemarrage"
rp3 = repli_ind.Repli(pr, fichier="etat_repli_essai3.json")
rp3.adopter({t: p for t, p in pr.ps().items() if t not in set(rb.tickets())})
assert not rp3.pos, "repli_ind ne prend pas la position de rebond_nas_opt"
rb.dernier = 0
rb.tour(pr.ps(), jr + 3600 * 10, True)
assert len(pr.pos) == 1, "tenue pendant la journee"
rb.dernier = 0
pr.bid = 20300.0
rb.tour(pr.ps(), jr + 22 * 3600 + 46 * 60, True)
assert not pr.pos and not rb.tickets(), "sortie en fin de journee"
nt = [n for n in pr.notes if n.get("evenement") == "sortie" and n.get("hypothese") == "rebond_nas_opt"]
assert nt and nt[-1]["bp"] > 0, "vente gagnante : bp positif"
rb.dernier = 0
rb.tour(pr.ps(), jr + 22 * 3600 + 50 * 60, True)
assert not pr.pos, "pas de nouvelle entree le meme jour"
for f in ("etat_rebond_essai.json", "etat_repli_essai3.json"):
    if os.path.exists(f):
        os.remove(f)
print("ESSAIS OK")


# v16 : pari_opt (poche pari, compte virtuel 100 $, repli sur SP500+ et US2000+, levier 14 fois le compte virtuel)
import pari_opt


class PontPari(PontIndice):
    def __init__(self):
        super().__init__()
        self.contrat = {"SP500+": 1.0, "US2000+": 1.0}

    def bougies(self, s, periode="M1", nombre=100):
        if s not in pari_opt.SYMBOLES:
            raise ValueError("symbole absent")
        return self.b[-nombre:]

    def symbole(self, s):
        return {"point": 0.01, "chiffres": 2, "lot_min": 0.1, "pas_lot": 0.1, "taille_contrat": self.contrat[s], "niveau_stops_points": 0}

    def ouvrir(self, s, sens, lots, stop, objectif=None, id="robot"):
        assert s in pari_opt.SYMBOLES and sens == "achat" and id == "pari_opt" and 0 < stop < self.bid and 0 < lots <= 0.5
        self.n += 1
        self.pos[self.n] = {"ticket": self.n, "symbole": s, "sens": sens, "prix_entree": self.bid + self.ecart, "stop": stop,
                            "profit": 0.0, "lots": lots}
        return {"ok": True, "ticket": self.n, "prix_obtenu": self.bid + self.ecart}


info = {"lot_min": 0.1, "pas_lot": 0.1, "taille_contrat": 1.0}
assert pari_opt.lots_pour(100.0, info, 2800.0) == 0.5, "petit contrat (280 $) : 5 lots mini = 1 400 $ = 14 fois 100 $"
assert pari_opt.lots_pour(100.0, info, 7600.0) == 0.1, "S&P (760 $) : 1 lot mini"
assert pari_opt.lots_pour(100.0, dict(info, taille_contrat=10.0), 7600.0) == 0.0, "contrat 10 fois plus gros : trade saute"
assert pari_opt.lots_pour(1000.0, info, 2800.0) == 0.5, "plafond 0,50 lot"
for f in ("etat_pari_essai.json", "etat_repli_essai4.json"):
    if os.path.exists(f):
        os.remove(f)
pp = PontPari()
pp.ecart = 0.5                                                  # 2 bp, sous le plafond de 3 bp
pa = pari_opt.Pari(pp, fichier="etat_pari_essai.json")
pp.b = jours([x / 7.0 for x in repli] + [repli[-1] / 7.0])      # prix ~ 2 680 : petit contrat
jour = pp.b[-1][0]
pp.bid = repli[-1] / 7.0
pa.tour(pp.ps(), jour + 3600, True)
assert len(pp.pos) == 2 and set(pa.pos) == set(pari_opt.SYMBOLES), "achat sur les deux indices"
assert all(p["lots"] == 0.5 for p in pp.pos.values()), "taille du compte virtuel (14 x 100 $ / 2 680 $ -> 0,5 lot)"
rp4 = repli_ind.Repli(pp, fichier="etat_repli_essai4.json")
rp4.adopter({t: p for t, p in pp.ps().items() if t not in set(pa.tickets())})
assert not rp4.pos, "repli_ind ne prend pas les positions de pari_opt"
assert pari_opt.Pari(pp, fichier="etat_pari_essai.json").tickets() == pa.tickets(), "reprise apres redemarrage"
pp.b = jours([x / 7.0 for x in repli] + [repli[-1] / 7.0 - 10, repli[-1] / 7.0 + 225, repli[-1] / 7.0 + 225])
pp.bid = repli[-1] / 7.0 + 225.0
pa.dernier = 0
pa.tour(pp.ps(), jour + 2 * 86400 + 3600, True)
assert not pp.pos and not pa.pos, "sortie au-dessus de la moyenne 5 j"
gain = 2 * (225.0 - 0.5) * 0.5
assert abs(pa.compte - (100.0 + gain)) < 0.01 and pa.trades == 2, "compte virtuel = 100 $ + gains reels"
# poche vide : plus d'ouverture
pa.compte, pa.dernier = 30.0, 0
pp.pos[950] = {"ticket": 950, "symbole": "SP500+", "sens": "achat", "prix_entree": 1.0, "stop": 0.5, "profit": -15.0}
pa.pos["SP500+"] = {"ticket": 950, "entree": 1.0, "jour": jour, "lots": 0.1, "profit": -15.0}
del pp.pos[950]
pa.tour(pp.ps(), jour + 3 * 86400 + 3600, True)
assert pa.arret == "poche vide" and pa.compte == 15.0, "stop touche : compte virtuel sous 20 $ -> arret"
pp.b = jours([x / 7.0 for x in repli] + [repli[-1] / 7.0])
pa.fait, pa.dernier = {}, 0
pa.tour(pp.ps(), pp.b[-1][0] + 3600, True)
assert not pp.pos, "poche vide : plus aucune ouverture"
assert pari_opt.Pari(pp, fichier="etat_pari_essai.json").arret == "poche vide", "arret garde apres redemarrage"
for f in ("etat_pari_essai.json", "etat_repli_essai4.json", "etat_pari.json"):
    if os.path.exists(f):
        os.remove(f)
print("ESSAIS OK")
