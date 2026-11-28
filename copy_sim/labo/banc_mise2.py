"""Banc Z (16/11, PRIORITES 18 h) : suite de banc_mise.py. (1) walk-forward de la mise selon la volatilite :
fenetre et multiplicateurs choisis sur la 1re moitie, juges sur la 2de, a exposition moyenne egale DANS chaque moitie ;
mise continue (volatilite 5 j / mediane 60 j, bornee). (2) mois negatifs : d'ou viennent les pertes, et freins
(mise /2 apres une perte sur 10 ou 20 jours, arret de la semaine apres une perte de X $). Usage : python3 banc_mise2.py"""
import contextlib, io, itertools, runpy
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    E = runpy.run_path("banc_mise.py")
T, rg, p11, bt, calme_v = E["T"], E["rg"], E["p11"], E["bt"], E["calme_v"]
x0 = p11 + bt
moit = T.index[len(T) // 2]
A, B = T.index < moit, T.index >= moit


def jug(k, x=x0):
    k = pd.Series(k, T.index).fillna(1.0)
    return [(k[m] * x[m]).sum() / k[m].mean() for m in (A, B)]


def vol(w):
    v = rg.shift(1).rolling(w).mean()
    return v, v.rolling(60, min_periods=20).median()


print("reference v11 (mise fixe) : 1re %+.0f  2de %+.0f" % tuple(jug(np.ones(len(T)))))
res = []
for w, hi, lo in itertools.product((3, 5, 10, 20), (1.5, 2.0, 3.0), (0.25, 0.5, 1.0)):
    v, med = vol(w)
    a, b = jug(np.where(v > med, hi, lo))
    res.append((a, b, w, hi, lo))
res.sort(reverse=True)
print("%d reglages ; 5 meilleurs sur la 1re moitie -> 2de moitie :" % len(res))
for a, b, w, hi, lo in res[:5]:
    print("  fenetre %2d j, x%.1f / x%.2f : 1re %+6.0f  2de %+6.0f" % (w, hi, lo, a, b))
print("  rang du reglage de Baptiste (5 j, x2/x0,5) : 2de moitie %+.0f" % [r[1] for r in res if r[2:] == (5, 2.0, 0.5)][0])
print("  mediane des 2de moitie sur les 36 reglages : %+.0f" % np.median([r[1] for r in res]))
for w in (5, 10):
    v, med = vol(w)
    a, b = jug((v / med).clip(0.25, 4))
    print("mise continue (vol %d j / mediane 60 j, bornee 0,25-4) : 1re %+.0f  2de %+.0f" % (w, a, b))

# (2) mois negatifs
v, med = vol(5)
k = pd.Series(np.where(v > med, 2.0, 0.5), T.index)
k = k / k.mean()
xv = k * x0
pm = (k * p11).groupby(T.index.to_period("M")).sum(); bm = (k * bt).groupby(T.index.to_period("M")).sum()
tm = pm + bm
print("\nmois negatifs (mise vol) : d'ou viennent les pertes")
for m in tm[tm < 0].index:
    print("  %s : total %+5.0f = petites regles %+5.0f + bt_or %+5.0f" % (m, tm[m], pm[m], bm[m]))


def frein(x, jours=None, cap=None):
    out, sem, perte_sem, hist = [], None, 0.0, []
    for d, val in x.items():
        f = 1.0
        if jours and len(hist) >= jours and sum(hist[-jours:]) < 0:
            f = 0.5
        s = d.isocalendar()[:2]
        if s != sem:
            sem, perte_sem = s, 0.0
        if cap is not None and perte_sem <= -cap:
            f = 0.0
        r = f * val
        out.append(r); hist.append(val); perte_sem += r
    return pd.Series(out, x.index)


def resume(nom, x):
    m = x.groupby(x.index.to_period("M")).sum(); c = x.cumsum()
    print("  %-40s total %+7.0f  mois<0 %2d/%d  creux %+6.0f  2de moitie %+6.0f" % (
        nom, x.sum(), (m < 0).sum(), len(m), (c - c.cummax()).min(), x[B].sum()))
    return m


print("\nfreins (sur la mise vol) ; objectif : moins de mois < 0 sans perdre plus de 20 % du total")
M = {"v11 fixe": resume("v11, mise fixe", x0), "vol": resume("mise vol (5 j, x2/x0,5)", xv)}
for j in (10, 20):
    M["vol+frein%d" % j] = resume("vol + mise /2 apres perte sur %d j" % j, frein(xv, jours=j))
for cap in (300, 500, 800):
    M["vol+cap%d" % cap] = resume("vol + arret semaine apres -%d $" % cap, frein(xv, cap=cap))
M["vol+frein20+cap500"] = resume("vol + frein 20 j + arret -500 $/sem", frein(xv, jours=20, cap=500))
print("\nmois : " + " ".join(str(p)[2:] for p in M["vol"].index))
for n, m in M.items():
    print("%-20s " % n + " ".join("%+5.0f" % v for v in m.values))
