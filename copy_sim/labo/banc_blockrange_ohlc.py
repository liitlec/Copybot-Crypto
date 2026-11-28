"""Banc R bis : BlockRange avec les vraies bougies jour (ouverture, haut, bas, cloture de Yahoo) : entree a
l'OUVERTURE du lendemain du signal (comme le robot), stop dur a 2 x ATR 20 j touche dans la bougie (au stop, ou a
l'ouverture si elle est deja dessous), sortie a l'ouverture qui suit une cloture au-dessus de la moyenne 5 j, ou
apres 10 jours. Couts : 2 bp + financement (taux 3 mois + 2,5 %) par nuit. 3 essais (seuil 5, 10, 25 ; filtre 200 j).
Usage : python3 banc_blockrange_ohlc.py"""
import os, json, time, urllib.request
import numpy as np, pandas as pd
from donnees import UNIVERS, UA
from banc_blockrange import rsi2, INDICES

ICI = os.path.dirname(os.path.abspath(__file__))


def ohlc(nom):
    f = os.path.join(ICI, "data", "ohlc_%s.csv.gz" % nom)
    if os.path.exists(f):
        return pd.read_csv(f, index_col=0, parse_dates=True)
    url = "https://query2.finance.yahoo.com/v8/finance/chart/%s?interval=1d&period1=946684800&period2=%d" % (
        urllib.request.quote(UNIVERS[nom][0]), int(time.time()))
    r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30))["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    d = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")},
                     index=pd.to_datetime(r["timestamp"], unit="s").normalize()).dropna()
    d = d[(d.open > 0) & (d.high >= d.low)]
    d.to_csv(f)
    return d


def trades(d, taux, seuil):
    c = d.close
    r, m200, m5 = rsi2(c), c.rolling(200).mean(), c.rolling(5).mean()
    tr = pd.concat([d.high - d.low, (d.high - c.shift()).abs(), (d.low - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(20).mean()
    o, h, l, v = d.open.values, d.high.values, d.low.values, c.values
    tx = taux.reindex(d.index).ffill().values
    out, i, n = [], 200, len(d)
    while i < n - 2:
        if r.iloc[i] < seuil and v[i] > m200.iloc[i]:
            e, stop = o[i + 1], o[i + 1] - 2 * atr.iloc[i]
            j, sortie = i + 1, None
            while True:
                if l[j] <= stop:
                    sortie = min(stop, o[j]); break
                if j >= n - 1:
                    sortie = v[j]; break
                if v[j] > m5.iloc[j] or j - i >= 10:
                    j += 1; sortie = o[j]; break
                j += 1
            nuits = (d.index[j] - d.index[i + 1]).days
            fin = np.nanmean(tx[i:j + 1]) / 100 + 0.025
            out.append((d.index[i + 1], sortie / e - 1 - 0.0002 - fin * nuits / 360, nuits, sortie / e - 1,
                        v[i + 1 if False else i] and (o[i + 1] / v[i] - 1)))
            i = j
        i += 1
    return pd.DataFrame(out, columns=["date", "net", "nuits", "brut", "ecart_nuit"])


if __name__ == "__main__":
    taux = pd.read_csv(os.path.join(ICI, "data", "jour.csv.gz"), index_col=0, parse_dates=True)["TAUX_US_3M"]
    D = {s: ohlc(s) for s in INDICES}
    for seuil in (5, 10, 25):
        t = pd.concat([trades(D[s], taux, seuil).assign(indice=s) for s in INDICES]).sort_values("date")
        print("\nRSI2 < %d, filtre 200 j, entree a l'ouverture suivante" % seuil)
        for nom, a, b in (("reglage 2000-2015", "2000", "2016"), ("verdict 2016-2026", "2016", "2027"),
                          ("recent 08/2025-11/2026", "2025-08-06", "2027")):
            x = t[(t.date >= a) & (t.date < b)]
            m, e = x.net.mean(), x.net.std() / np.sqrt(len(x))
            # erreur type par semaine (les 5 indices entrent souvent ensemble : trades non independants)
            sem = x.groupby(x.date.dt.to_period("W")).net.sum()
            ts = sem.mean() / (sem.std() / np.sqrt(len(sem)))
            print("  %-22s %4d tr  brut %+6.1f bp  net %+6.1f bp  t = %+.1f (par semaine : %+.1f)  gagnants %2.0f %%  nuits %.1f  ecart de nuit manque %+5.1f bp  pire %+.1f %%"
                  % (nom, len(x), x.brut.mean() * 1e4, m * 1e4, m / e, ts, 100 * (x.net > 0).mean(), x.nuits.mean(), x.ecart_nuit.mean() * 1e4, x.net.min() * 100))
        if seuil == 10:
            x = t[t.date >= "2016"]
            print("  par indice (verdict) : " + ", ".join("%s %d tr %+.0f bp" % (s, len(g), g.net.mean() * 1e4) for s, g in x.groupby("indice")))
            an = t.groupby(t.date.dt.year).net.agg(["count", "sum"])
            print("  par an (somme, %) : " + ", ".join("%d: %+.0f (%d)" % (y, r["sum"] * 100, r["count"]) for y, r in an.iterrows()))
            # courbe : chaque trade pese 20 % du compte (5 indices = levier 1 au plus)
            cap = (1 + 0.2 * t.set_index("date").net).cumprod()
            ans = (t.date.max() - t.date.min()).days / 365.25
            print("  a 20 %% du compte par trade : %+.1f %% par an, pire baisse %.1f %%" % ((cap.iloc[-1] ** (1 / ans) - 1) * 100, (cap / cap.cummax() - 1).min() * 100))
