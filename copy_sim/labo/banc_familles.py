"""Banc F (17/11, PRIORITES 10 h 15) : la bonne famille au bon moment. Etape 1 : sélection contre sélection sans
elan_m15 ; piste 4 (filtre de direction des règles de tendance M15 : n'entrer que si la tendance de fond va dans le
même sens, et pas au bout du range du jour). Or M15/M5, 15 mois, mêmes calculs que banc_mise.py. Réglages choisis sur
la 1re moitié des jours, jugés sur la 2de. Usage : python3 banc_familles.py"""
import contextlib, io, itertools, runpy
import numpy as np, pandas as pd
import banc_or as B
from banc_melange import par_jour
with contextlib.redirect_stdout(io.StringIO()):
    E = runpy.run_path("banc_mise.py")
T, m15, bt = E["T"], E["m15"], E["bt"]
moit = T.index[len(T) // 2]


def bilan(nom, x):
    x = x.reindex(T.index).fillna(0.0)
    m = x.groupby(x.index.to_period("M")).sum(); c = x.cumsum()
    print("  %-52s total %+6.0f  1re %+6.0f  2de %+6.0f  mois<0 %2d/%d  creux %+6.0f" % (
        nom, x.sum(), x[x.index < moit].sum(), x[x.index >= moit].sum(), (m < 0).sum(), len(m), (c - c.cummax()).min()))
    return x


print("etape 1 : selection (elan_m15 + cassure_m15 + exces_m5 + bt_or), mise fixe")
sel = bilan("selection", T[["elan_m15", "cassure_m15", "exces_m5"]].sum(axis=1) + bt)
bilan("sans elan_m15", T[["cassure_m15", "exces_m5"]].sum(axis=1) + bt)
for k in ("elan_m15", "cassure_m15", "exces_m5", "bt_or"):
    bilan("  " + k + " seul", T[k])

# piste 4 : filtre de direction sur elan_m15 et cassure_m15
c = m15["cloture"]; lr = np.log(c)
s_elan = np.sign(lr - lr.shift(12))
ha, ba = m15["haut"].shift(1).rolling(48).max(), m15["bas"].shift(1).rolling(48).min()
s_cas = (c > ha).astype(float) - (c < ba).astype(float)
jour = m15.index.floor("D")
hj = m15["haut"].groupby(jour).cummax(); bj = m15["bas"].groupby(jour).cummin()
pos = ((c - bj) / (hj - bj)).where(hj > bj, 0.5)
print("\npiste 4 : filtre de direction (fond = pente de la moyenne de N bougies M15 ; bout du range = position > p)")
res = []
for n, p in itertools.product((80, 192, 384), (0.8, 0.9, 1.01)):
    fond = np.sign(c - c.rolling(n).mean())
    ok = lambda s: s.where((s == fond) & (((s > 0) & (pos < p)) | ((s < 0) & (pos > 1 - p))), 0.0)
    je, _, _ = par_jour(m15, ok(s_elan), 12); jc, _, _ = par_jour(m15, ok(s_cas), 12)
    x = (je.reindex(T.index).fillna(0) + jc.reindex(T.index).fillna(0))
    res.append((x[x.index < moit].sum(), x[x.index >= moit].sum(), n, p, x))
base = (T["elan_m15"] + T["cassure_m15"])
print("  tendance M15 sans filtre : 1re %+.0f  2de %+.0f" % (base[base.index < moit].sum(), base[base.index >= moit].sum()))
for a, b, n, p, _ in sorted(res, key=lambda r: -r[0]):
    print("  fond %3d bougies, bout %.2f : 1re %+6.0f  2de %+6.0f" % (n, p, a, b))
best = max(res, key=lambda r: r[0])
print("  -> choisi sur la 1re moitie : fond %d, bout %.2f ; 2de moitie %+.0f (sans filtre %+.0f) ; mediane des 9 en 2de : %+.0f" % (
    best[2], best[3], best[1], base[base.index >= moit].sum(), np.median([r[1] for r in res])))
bilan("selection avec tendance filtree (reglage choisi)", best[4] + T["exces_m5"] + bt)
