"""Banc T : la mecanique de BlockFinMois refaite (regles : BLOCK_REGLES.md, section 4). Bougies jour Yahoo 2000-2026.
Piste B (indices) : le dernier jour de bourse du mois, achat a la cloture si le mois est negatif et la cloture
au-dessus de la moyenne 200 j ; stop 3 ATR 20 j (dans la bougie) ; sortie a la cloture 10 jours de bourse apres.
Variantes : sans condition (effet « debut de mois » pur), tenue 3 / 5 / 10 jours, mois negatif seul, tendance seule.
Piste A (devises, clotures seules) : dernier jour du mois, achat si RSI 2 j < 30, sortie des que la cloture depasse
la moyenne 5 j ou apres 10 jours ; stop 2 ATR (approche par 1,4 x |variation| moyenne, juge a la cloture).
Couts : indices 2 bp + financement (taux 3 mois + 2,5 %) par nuit ; devises 2 bp, portage ignore.
Temoin : la meme regle lancee un jour quelconque du mois (tous les jours qui ne sont pas le dernier).
Usage : python3 banc_finmois.py"""
import os
import numpy as np, pandas as pd
from banc_repli_plus import ohlc, B
from banc_blockrange import rsi2

ICI = os.path.dirname(os.path.abspath(__file__))
IND = B + ["FTSE"]
FX = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]


def indices(d, taux, tenue=10, negatif=True, tendance=True, stop_k=3.0, fin_de_mois=True):
    c, o, l = d.close.values, d.open.values, d.low.values
    m200 = d.close.rolling(200).mean().values
    tr = pd.concat([d.high - d.low, (d.high - d.close.shift()).abs(), (d.low - d.close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(20).mean().values
    mois = d.index.to_period("M")
    dernier = np.r_[mois[1:] != mois[:-1], False]
    debut = pd.Series(d.close.values, mois).groupby(level=0).first().reindex(mois).values   # 1re cloture du mois
    tx = (np.nan_to_num(taux.reindex(d.index).ffill().values, nan=2.0) / 100 + 0.025) / 360
    out = []
    for i in range(205, len(d) - tenue - 1):
        if dernier[i] != fin_de_mois:
            continue
        if negatif and not c[i] < debut[i]:
            continue
        if tendance and not c[i] > m200[i]:
            continue
        e, stop, x = c[i], c[i] - stop_k * atr[i], None
        for j in range(i + 1, i + tenue + 1):
            if stop_k and l[j] <= stop:
                x = min(stop, o[j]); break
        if x is None:
            j = i + tenue; x = c[j]
        nuits = (d.index[j] - d.index[i]).days
        out.append((d.index[i], x / e - 1 - 0.0002 - tx[i] * nuits))
    return out


def devises(c, seuil=30, fin_de_mois=True):
    c = c.dropna()
    v, r, m5 = c.values, rsi2(c).values, c.rolling(5).mean().values
    atr = 1.4 * c.diff().abs().rolling(20).mean().values
    mois = c.index.to_period("M")
    dernier = np.r_[mois[1:] != mois[:-1], False]
    out = []
    for i in range(30, len(c) - 11):
        if dernier[i] != fin_de_mois or not r[i] < seuil:
            continue
        for j in range(i + 1, i + 11):
            if v[j] <= v[i] - 2 * atr[i] or v[j] > m5[j]:
                break
        out.append((c.index[i], v[j] / v[i] - 1 - 0.0002))
    return out


def ligne(nom, t):
    t = pd.DataFrame(t, columns=["date", "net"])
    s = "  %-46s" % nom
    for a, b in (("2001", "2016"), ("2016", "2027")):
        x = t[(t.date >= a) & (t.date < b)]
        if len(x) < 5:
            s += " | %4d trades" % len(x); continue
        g = x.groupby(x.date.dt.to_period("M")).net.mean()      # un point par mois : les marches entrent ensemble
        s += " | %4d trades %+6.1f bp (t par mois %+.1f, %2.0f %% gagnants)" % (len(x), x.net.mean() * 1e4, g.mean() / g.std() * np.sqrt(len(g)), 100 * (x.net > 0).mean())
    return s


if __name__ == "__main__":
    taux = pd.read_csv(os.path.join(ICI, "data", "jour.csv.gz"), index_col=0, parse_dates=True)["TAUX_US_3M"]
    D = {s: ohlc(s) for s in IND}
    tous = lambda **k: sum((indices(D[s], taux, **k) for s in IND), [])
    print("%-48s | 2001-2015 %38s | 2016-2026" % ("Piste B, 9 indices", ""))
    print(ligne("regle de Baptiste (mois negatif, > MM200, 10 j)", tous()))
    print(ligne("  temoin : meme regle, un autre jour du mois", tous(fin_de_mois=False)))
    for tenue in (3, 5):
        print(ligne("regle de Baptiste, tenue %d j" % tenue, tous(tenue=tenue)))
    print(ligne("fin de mois sans condition, 3 j", tous(tenue=3, negatif=False, tendance=False)))
    print(ligne("fin de mois sans condition, 5 j", tous(tenue=5, negatif=False, tendance=False)))
    print(ligne("fin de mois sans condition, 10 j", tous(negatif=False, tendance=False)))
    print(ligne("  temoin : un autre jour, sans condition, 5 j", tous(tenue=5, negatif=False, tendance=False, fin_de_mois=False)))
    print(ligne("mois negatif seul, 10 j", tous(tendance=False)))
    print(ligne("au-dessus de MM200 seul, 10 j", tous(negatif=False)))
    j = pd.read_csv(os.path.join(ICI, "data", "jour.csv.gz"), index_col=0, parse_dates=True)
    print("\nPiste A, 7 devises (contre le dollar, dans le sens de la paire)")
    print(ligne("regle de Baptiste (RSI 2 j < 30, fin de mois)", sum((devises(j[s]) for s in FX), [])))
    print(ligne("  temoin : meme regle, un autre jour du mois", sum((devises(j[s], fin_de_mois=False) for s in FX), [])))
    print(ligne("RSI 2 j < 10, fin de mois", sum((devises(j[s], seuil=10) for s in FX), [])))
