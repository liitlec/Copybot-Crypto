"""Banc T bis : la piste A de BlockFinMois (devises en fin de mois) avec de vraies bougies jour Yahoo (ouverture,
haut, bas, cloture), 14 paires, achats ET ventes. Le dernier jour de bourse du mois, a la cloture : achat si
RSI 2 j < 30 (vente si RSI 2 j > 70) ; stop 2 x ATR 20 j touche dans la bougie ; sortie a la cloture qui repasse
la moyenne 5 j, ou apres 10 jours. Cout : 3 bp aller-retour (majeures) ou 5 bp (croisees), portage ignore.
Temoin : meme regle un autre jour du mois. t avec un point par mois. Usage : python3 banc_finmois_fx.py"""
import os
import numpy as np, pandas as pd
import banc_repli_plus as P
from banc_blockrange import rsi2

MAJ = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]
CRO = ["EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "EURCHF", "EURAUD", "AUDNZD"]
for s in MAJ + CRO:
    P.TICKERS[s] = s + "=X"


def trades(d, sens, cout, fin_de_mois=True, seuil=30):
    d = d[(d.high / d.low < 1.15)]                       # bougies Yahoo aberrantes
    c, o, h, l = d.close.values, d.open.values, d.high.values, d.low.values
    r = rsi2(d.close).values
    m5 = d.close.rolling(5).mean().values
    tr = pd.concat([d.high - d.low, (d.high - d.close.shift()).abs(), (d.low - d.close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(20).mean().values
    mois = d.index.to_period("M")
    dernier = np.r_[mois[1:] != mois[:-1], False]
    out = []
    for i in range(30, len(d) - 11):
        if dernier[i] != fin_de_mois:
            continue
        if (sens > 0 and not r[i] < seuil) or (sens < 0 and not r[i] > 100 - seuil):
            continue
        e, stop, x = c[i], c[i] - sens * 2 * atr[i], None
        for j in range(i + 1, i + 11):
            if (sens > 0 and l[j] <= stop) or (sens < 0 and h[j] >= stop):
                x = stop if (o[j] - stop) * sens > 0 else o[j]; break
            if (c[j] - m5[j]) * sens > 0:
                x = c[j]; break
        if x is None:
            x = c[j]
        out.append((d.index[i], sens * (x / e - 1) - cout))
    return out


def ligne(nom, t):
    t = pd.DataFrame(t, columns=["date", "net"])
    s = "  %-44s" % nom
    for a, b in (("2004", "2016"), ("2016", "2027"), ("2025-08", "2027")):
        x = t[(t.date >= a) & (t.date < b)]
        if len(x) < 5:
            s += " | %4d trades" % len(x); continue
        g = x.groupby(x.date.dt.to_period("M")).net.mean()
        s += " | %5d tr %+5.1f bp (t %+.1f, %2.0f %% gagn., pire %+.1f %%)" % (len(x), x.net.mean() * 1e4, g.mean() / g.std() * np.sqrt(len(g)), 100 * (x.net > 0).mean(), x.net.min() * 100)
    return s


if __name__ == "__main__":
    D = {s: P.ohlc(s) for s in MAJ + CRO}
    print("Donnees :", ", ".join("%s %d" % (s, D[s].index[0].year) for s in D))
    print("%-46s | 2004-2015 %40s | 2016-2026 %40s | 08/2025 ->" % ("", "", ""))
    tous = lambda U, cout, **k: sum((trades(D[s], cout=cout, **k) for s in U), [])
    for nom, U, cout in (("7 majeures", MAJ, 0.0003), ("7 croisees", CRO, 0.0005)):
        print(ligne(nom + " : achats (RSI<30), fin de mois", tous(U, cout, sens=1)))
        print(ligne(nom + " : ventes (RSI>70), fin de mois", tous(U, cout, sens=-1)))
        print(ligne("  temoin achats, autre jour", tous(U, cout, sens=1, fin_de_mois=False)))
        print(ligne("  temoin ventes, autre jour", tous(U, cout, sens=-1, fin_de_mois=False)))
    print(ligne("14 paires, achats + ventes, fin de mois", tous(MAJ, 0.0003, sens=1) + tous(MAJ, 0.0003, sens=-1) + tous(CRO, 0.0005, sens=1) + tous(CRO, 0.0005, sens=-1)))
    print(ligne("14 paires, achats + ventes, autre jour", tous(MAJ, 0.0003, sens=1, fin_de_mois=False) + tous(MAJ, 0.0003, sens=-1, fin_de_mois=False) + tous(CRO, 0.0005, sens=1, fin_de_mois=False) + tous(CRO, 0.0005, sens=-1, fin_de_mois=False)))
