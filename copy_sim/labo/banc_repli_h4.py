"""Banc W : le repli d'indices en H4 au lieu du jour (PRIORITES 12/11 22 h 40, point 1). NAS100+ H4 du courtier
(2018-2026). Meme logique : RSI 2 bougies < seuil et cloture au-dessus de la moyenne longue ; achat a l'ouverture
suivante ; stop 2 ATR 20 bougies ; sortie quand une cloture repasse au-dessus de la moyenne 5 bougies, ou apres 10
bougies. Moyenne longue : 200 bougies H4 (~33 jours) ou 1200 (~200 jours). Cout : spread de la bougie + 0,4 bp par
bougie tenue (financement). Reglage 2018-2022, verdict 2023-2026. 6 essais. Usage : python3 banc_repli_h4.py"""
import numpy as np, pandas as pd
from banc_blockrange import rsi2

b = pd.read_csv("mt5/donnees/nas_h4_20k.csv.gz")
t = pd.to_datetime(b.heure, unit="s")
o, h, l, c = (b[x].values for x in ("ouverture", "haut", "bas", "cloture"))
sp = b.spread_points.values * 0.01
cs = pd.Series(c)
r = rsi2(cs).values
m5 = cs.rolling(5).mean().values
tr = pd.concat([b.haut - b.bas, (b.haut - cs.shift()).abs(), (b.bas - cs.shift()).abs()], axis=1).max(axis=1)
atr = tr.rolling(20).mean().values
print("NAS100+ H4 : %d bougies, %s -> %s" % (len(b), t.iloc[0].date(), t.iloc[-1].date()))
for longue in (200, 1200):
    ml = cs.rolling(longue).mean().values
    for seuil in (5, 10, 25):
        out, i, n = [], longue, len(b)
        while i < n - 12:
            if r[i] < seuil and c[i] > ml[i]:
                e, stop = o[i + 1], o[i + 1] - 2 * atr[i]
                j = i + 1
                while True:
                    if l[j] <= stop:
                        x = min(stop, o[j]); break
                    if c[j] > m5[j] or j - i >= 10 or j >= n - 2:
                        j += 1; x = o[j]; break
                    j += 1
                out.append((t.iloc[i + 1], (x - e - max(sp[i + 1], 0.8)) / e - 0.00004 * (j - i)))
                i = j
            i += 1
        x = pd.DataFrame(out, columns=["date", "net"])
        s = "  moyenne %4d, RSI2 < %2d :" % (longue, seuil)
        for a, bb in (("2018", "2023"), ("2023", "2027")):
            y = x[(x.date >= a) & (x.date < bb)].net
            s += " | %4d tr %+5.1f bp (t %+.1f, %2.0f %% gagn.)" % (len(y), y.mean() * 1e4, y.mean() / y.std() * np.sqrt(len(y)), 100 * (y > 0).mean())
        print(s)
