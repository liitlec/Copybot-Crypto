"""Rejeu du module du robot (mt5/robot/bt_or.py) sur les vraies bougies M5, compare au banc : verifie que le code qui
trade en direct fait bien ce que le banc a mesure. Usage : python3 rejeu_bt.py [nombre de bougies]"""
import os, sys
import numpy as np
ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ICI, "mt5", "robot"))
import bt_or
import banc_grille as G, banc_blocktrend as BT


class FauxPont:
    def __init__(s):
        s.bid, s.pos, s.n, s.notes = 0.0, {}, 0, []

    def prix(s, x):
        return {"bid": s.bid, "ask": s.bid + 0.2}

    def ouvrir(s, x, sens, lots, stop, objectif=None, id="r"):
        s.n += 1
        s.pos[s.n] = {"ticket": s.n, "sens": sens, "e": s.bid + 0.2 if sens == "achat" else s.bid, "profit": 0}
        return {"ok": True, "ticket": s.n, "prix_obtenu": s.pos[s.n]["e"]}

    def fermer(s, t):
        s.pos.pop(t, None)
        return {"ok": True}

    def modifier(s, t, stop, objectif=None):
        return {"ok": True}

    def noter(s, **k):
        s.notes.append(k)

    def ps(s):
        for p in s.pos.values():
            sg = 1 if p["sens"] == "achat" else -1
            p["profit"] = sg * ((s.bid if sg > 0 else s.bid + 0.2) - p["e"])
        return dict(s.pos)


if __name__ == "__main__":
    nb = int(sys.argv[1]) if len(sys.argv) > 1 else 12000
    d = G.charge("xau_m5_90k"); n = len(d)
    bars = [[int(a), float(o), float(h), float(l), float(c), 0, 0] for a, o, h, l, c in zip(d.heure, d.ouverture, d.haut, d.bas, d.cloture)]
    dj = d.groupby(d.heure // 86400).agg(t=("heure", "first"), o=("ouverture", "first"), h=("haut", "max"), l=("bas", "min"), c=("cloture", "last")).reset_index(drop=True)
    D1 = [[int(r.t), r.o, r.h, r.l, r.c, 0, 0] for r in dj.itertuples()]
    f = os.path.join(os.environ.get("TMPDIR", "/tmp"), "rejeu_bt_etat.json")
    if os.path.exists(f):
        os.remove(f)
    fp = FauxPont(); bt = bt_or.PanierBT(fp, fichier=f); bt_or.ARRET_R = -1e9
    deb = n - nb
    for i in range(deb, n):
        b = bars[i]
        for px in ((b[3], b[2], b[4]) if b[4] >= b[1] else (b[2], b[3], b[4])):
            fp.bid = px; bt.surveiller(fp.ps(), fp.prix(""))
        k = np.searchsorted(dj.t.values, b[0], side="right") - 1
        bt.bougie(bars[max(0, i - 2999):i + 1], D1[max(0, k - 29):k], True)
    R = np.array([x["R"] for x in fp.notes if x.get("evenement") == "sortie panier"])
    print("module du robot rejoue sur les %d dernieres bougies M5 : %d paniers, total %+.1f R, gagnants %.0f %%" % (nb, len(R), R.sum(), 100 * (R > 0).mean()))
    P = [p for p in BT.simule(d, 0.25, 0.6667, 3) if p[0] >= deb]
    print("banc sur la meme periode (pyramide de 3 au plus)        : %d paniers, total %+.1f R" % (len(P), sum(p[3] for p in P)))
    os.remove(f) if os.path.exists(f) else None
