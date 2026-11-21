"""Banc AD : moins de mois negatifs avec des pieces decorrelees (PRIORITES 16/11 18 h, point 2 ; suite du banc Z).
Base = melange v11 sur l'or (elan_m15 + cassure_m15 + exces_m5 avec pause au calme, + bt_or), $ a 0,01 lot, 15 mois.
Piece ajoutee = repli d'indices americains (regle du robot, bougies jour du courtier : NAS100+, SP500+, DJ30+,
US2000+), gain de chaque trade compte au mois de son entree, pour un montant de marche M par trade.
Question : combien de mois negatifs en moins, pour quel montant, et la piece est-elle vraiment decorrelee ?
Usage : python3 banc_pieces.py"""
import warnings; warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_or as B, banc_grille as G, banc_blocktrend as BT
from banc_melange import par_jour
from banc_blockrange_ohlc import trades

m15, _ = B.charge("xau_m15_50k"); m5, _ = B.charge("xau_m5_90k")
m15 = m15[m15.index >= m5.index[0]]
J = {}
lr = np.log(m15["cloture"])
J["elan_m15"], _, _ = par_jour(m15, np.sign(lr - lr.shift(12)), 12)
ha, ba = m15["haut"].shift(1).rolling(48).max(), m15["bas"].shift(1).rolling(48).min()
J["cassure_m15"], _, _ = par_jour(m15, (m15["cloture"] > ha).astype(float) - (m15["cloture"] < ba).astype(float), 12)
r = np.log(m5["cloture"]).diff(); z = r / r.rolling(100).std().shift(1)
J["exces_m5"], _, _ = par_jour(m5, (z > 3).astype(float) - (z < -3).astype(float), 3)
g = G.charge("xau_m5_90k"); P = BT.simule(g, 0.25, 0.6667, 3)
jd = m5.index.floor("D")
atr = (m5["haut"].groupby(jd).max() - m5["bas"].groupby(jd).min()).rolling(20).mean().shift(1)
jb = pd.Series([p[3] for p in P], index=m5.index[[p[0] for p in P]].floor("D"))
J["bt_or"] = (jb * (0.6667 * atr).reindex(jb.index).ffill().values).groupby(level=0).sum()
T = pd.DataFrame(J).fillna(0.0); T = T[T.index.dayofweek < 5]
D = m5.groupby(jd).agg(o=("cloture", "first"), h=("haut", "max"), b=("bas", "min")); D = D[D.index.dayofweek < 5]
rg = ((D.h - D.b) / D.o).reindex(T.index)
calme_v = (rg.shift(1) < rg.shift(1).rolling(60, min_periods=20).median()).fillna(False)
petites = T[["elan_m15", "cassure_m15", "exces_m5"]].sum(axis=1).where(~calme_v, 0)
base = petites + T["bt_or"]

taux = pd.Series(4.0, index=pd.date_range("2015-01-01", "2027-01-01"))     # taux court ~4 %, + 2,5 % de marge du courtier dans trades()
R = []
for f in ("nas_d1_5k", "sp_d1_5k", "dj_d1_5k", "us2000_d1_5k"):
    b = pd.read_csv("mt5/donnees/%s.csv.gz" % f)
    d = pd.DataFrame({"open": b.ouverture.values, "high": b.haut.values, "low": b.bas.values, "close": b.cloture.values},
                     index=pd.to_datetime(b.heure, unit="s").dt.normalize())
    d = d[d.index.dayofweek < 5]
    t = trades(d, taux, 10); t["f"] = f; R.append(t)
R = pd.concat(R)
R = R[(R.date >= T.index[0]) & (R.date <= T.index[-1])]
rj = R.groupby("date").net.sum().reindex(T.index).fillna(0.0)          # somme des rendements nets du jour d'entree
print("repli d'indices sur la periode : %d trades, %+.1f bp par trade, %.0f %% gagnants" % (len(R), R.net.mean() * 1e4, 100 * (R.net > 0).mean()))
mb, mr = base.groupby(base.index.to_period("M")).sum(), rj.groupby(rj.index.to_period("M")).sum()
print("correlation par mois base / repli : %+.2f ; par semaine : %+.2f" % (mb.corr(mr), base.groupby(base.index.to_period("W")).sum().corr(rj.groupby(rj.index.to_period("W")).sum())))
print("mois negatifs de la base ou le repli est positif : %d sur %d" % (((mb < 0) & (mr > 0)).sum(), (mb < 0).sum()))


def bilan(nom, x):
    c = x.cumsum(); m = x.groupby(x.index.to_period("M")).sum()
    print("  %-46s total %+7.0f $  mois<0 %2d/%d  pire mois %+6.0f $  pire creux %+6.0f $" % (nom, x.sum(), (m < 0).sum(), len(m), m.min(), (c - c.cummax()).min()))
    return m


M = {"base": bilan("base (melange v11 sur l'or, 0,01 lot)", base)}
for mont in (10000, 20000, 50000, 100000):
    M[mont] = bilan("base + repli, %6d $ de marche par trade" % mont, base + rj * mont)
bilan("repli seul, 50 000 $ par trade", rj * 50000)
for part in (0.5, 0.25):
    bilan("base x %.2f + repli 50 000 $ (moins d'or)" % part, base * part + rj * 50000)
print("\nmois :", " ".join(str(p)[2:] for p in M["base"].index))
for k in ("base", 20000, 50000):
    print("%-8s" % k, " ".join("%+5.0f" % v for v in M[k].values))
print("repli   ", " ".join("%+5.0f" % (v * 50000) for v in mr.values))

print("\nPrudence : ces 15 mois sont tres favorables au repli (+78 bp par trade contre +25 a +40 bp sur 6 a 8 ans chez le courtier).")
R2 = R.copy(); R2["net"] = R2.net - (R2.net.mean() - 0.0030)             # meme dispersion, moyenne ramenee a +30 bp
rj2 = R2.groupby("date").net.sum().reindex(T.index).fillna(0.0)
for mont in (10000, 20000, 50000):
    bilan("base + repli ramene a +30 bp, %6d $ par trade" % mont, base + rj2 * mont)
