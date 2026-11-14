"""Banc V : sorties fines (PRIORITES 12/11 12 h 30, famille 6) sur l'or M1 du courtier (3 mois), spread reel.
Question : une sortie plus fine (stop suiveur, retour au point d'entree, sortie partielle, objectif en multiples du
spread) transforme-t-elle une entree sans avantage en gain ? Entrees : hasard (temoin), elan 3 min, repli (contre un
exces de 2 ecarts-types sur 20 min). Une position a la fois, 60 min au plus. Dans une bougie ou stop et objectif
sont tous deux touches, on compte le STOP (prudent). A = amplitude moyenne des 30 dernieres bougies M1.
Sorties : temps 15 min (reference) ; stop 3A + objectif 3A ; stop 3A + objectif 6A ; stop 2A + objectif 5 spreads ;
stop suiveur 3A ; stop 3A ramene au point d'entree apres +2A ; moitie sortie a +2A puis suiveur 3A sur le reste.
Reglage = 60 % du debut, verdict = 40 % de la fin. 21 essais. Usage : python3 banc_sorties_fines.py"""
import numpy as np, pandas as pd
import banc_grille as G

MAXB = 60


def jouer(d, sig, mode):
    o, h, l, c, sp = (d[x].values for x in ("ouverture", "haut", "bas", "cloture", "sp"))
    A = (d["haut"] - d["bas"]).rolling(30).mean().values
    out, libre, n = [], 0, len(d) - MAXB - 2
    for i in np.flatnonzero(sig):
        if i < libre or i >= n or not A[i] > 0:
            continue
        s, a, e = sig[i], A[i], o[i + 1]
        cout = sp[i + 1]
        stop = obj = None
        suiv = be = part = False
        if mode == "temps15":
            j = i + 15; out.append((i, s * (c[j] - e) - cout)); libre = j; continue
        if mode == "3-3": stop, obj = 3 * a, 3 * a
        elif mode == "3-6": stop, obj = 3 * a, 6 * a
        elif mode == "2-5sp": stop, obj = 2 * a, 5 * max(cout, 0.05)
        elif mode == "suiveur": stop, suiv = 3 * a, True
        elif mode == "zero": stop, be = 3 * a, True
        elif mode == "partiel": stop, suiv, part = 3 * a, True, True
        niveau = e - s * stop                      # prix du stop
        meilleur, gain, reste = e, 0.0, 1.0
        for j in range(i + 1, i + 1 + MAXB):
            bas_fav, haut_fav = (l[j], h[j]) if s > 0 else (h[j], l[j])      # extreme contre nous, extreme pour nous
            if (bas_fav - niveau) * s <= 0:                                   # stop touche (compte en premier)
                x = niveau if (o[j] - niveau) * s > 0 else o[j]
                gain += reste * s * (x - e); reste = 0; break
            if obj is not None and (haut_fav - (e + s * obj)) * s >= 0:
                gain += reste * obj; reste = 0; break
            if (haut_fav - meilleur) * s > 0:
                meilleur = haut_fav
            if part and reste == 1.0 and (meilleur - e) * s >= 2 * a:
                gain += 0.5 * 2 * a; reste = 0.5
            if suiv:
                niveau = max(niveau * s, (meilleur - s * stop) * s) * s
            if be and (meilleur - e) * s >= 2 * a:
                niveau = max(niveau * s, e * s) * s
        if reste:
            gain += reste * s * (c[j] - e)
        out.append((i, gain - cout))
        libre = j
    return np.array(out)


def res(t, a, b):
    x = t[(t[:, 0] >= a) & (t[:, 0] < b), 1]
    return "%5d tr %+6.3f $ (t %+.1f, %2.0f %% gagn.)" % (len(x), x.mean(), x.mean() / x.std() * np.sqrt(len(x)), 100 * (x > 0).mean())


if __name__ == "__main__":
    d = G.charge("xau_m1_90k")
    d = d[(d.h >= 3) & (d.h < 23)].reset_index(drop=True)
    c = d["cloture"]; n = len(d); k = int(n * 0.6)
    rng = np.random.default_rng(3)
    hasard = np.where(rng.random(n) < 0.2, rng.choice((-1, 1), n), 0)
    elan = np.sign(c - c.shift(3)).fillna(0).values.astype(int)
    z = (c - c.rolling(20).mean()) / c.rolling(20).std()
    repli = ((z < -2).astype(int) - (z > 2).astype(int)).values
    print("or M1 : %d bougies, spread moyen %.3f $ ; gains en $ par once (= par trade a 0,01 lot)" % (n, d.sp.mean()))
    print("%-48s | reglage (60 %%)                        | verdict (40 %%)" % "")
    for nom, s in (("hasard", hasard), ("elan 3 min", elan), ("repli 2 ecarts-types", repli)):
        for mode, lib in (("temps15", "sortie au temps 15 min"), ("3-3", "stop 3A, objectif 3A"), ("3-6", "stop 3A, objectif 6A"),
                          ("2-5sp", "stop 2A, objectif 5 spreads"), ("suiveur", "stop suiveur 3A"),
                          ("zero", "stop 3A ramene a l'entree apres +2A"), ("partiel", "moitie a +2A, suiveur sur le reste")):
            t = jouer(d, s, mode)
            print("  %-46s | %s | %s" % (nom + " : " + lib, res(t, 0, k), res(t, k, n)))
