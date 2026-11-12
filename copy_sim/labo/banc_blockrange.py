"""Banc R : la mecanique de BlockRange refaite (PRIORITES 12/11 13 h 15).
Regle : achat d'un indice quand le RSI 2 jours < seuil et que la cloture est au-dessus de la moyenne 200 j ;
sortie quand la cloture repasse au-dessus de la moyenne 5 j, ou apres 10 jours ; stop a 2 x ATR 20 j (approche ici
par 2 x 1,4 x moyenne des |variations| de cloture, juge a la cloture : les donnees Yahoo du labo n'ont que les clotures).
Entree et sortie a la cloture du jour du signal (le robot entre a l'ouverture suivante : ecart ignore).
Couts : 2 bp aller-retour (spread indice) + financement CFD (taux 3 mois + 2,5 %) / 360 par nuit tenue.
Temoin : meme nombre de jours tenus, pris au hasard dans les jours au-dessus de la moyenne 200 j (= rendement moyen
d'un jour "en tendance haussiere" x duree), pour separer l'effet "repli" de la simple prime des indices.
8 essais : seuil 5/10/15/25 x avec/sans filtre 200 j. Usage : python3 banc_blockrange.py"""
import os
import numpy as np, pandas as pd

ICI = os.path.dirname(os.path.abspath(__file__))
INDICES = ["SP500", "NASDAQ", "DAX", "NIKKEI", "FTSE"]


def rsi2(c):
    d = c.diff()
    h = d.clip(lower=0).ewm(alpha=0.5, adjust=False).mean()
    b = (-d.clip(upper=0)).ewm(alpha=0.5, adjust=False).mean()
    return 100 * h / (h + b)


def trades(c, taux, seuil, filtre):
    c = c.dropna()
    r, m200, m5 = rsi2(c), c.rolling(200).mean(), c.rolling(5).mean()
    atr = 1.4 * c.diff().abs().rolling(20).mean()
    v, out, i, n = c.values, [], 200, len(c)
    tx = taux.reindex(c.index).ffill().values
    while i < n - 1:
        if r.iloc[i] < seuil and (not filtre or v[i] > m200.iloc[i]):
            e, stop, j = v[i], v[i] - 2 * atr.iloc[i], i
            while j < n - 1:
                j += 1
                if v[j] <= stop or v[j] > m5.iloc[j] or j - i >= 10:
                    break
            nuits = (c.index[j] - c.index[i]).days
            fin = np.nanmean(tx[i:j + 1]) / 100 + 0.025
            out.append((c.index[i], v[j] / e - 1 - 0.0002 - fin * nuits / 360, j - i, v[j] / e - 1))
            i = j + 1          # pas de nouvel achat le jour qui suit une sortie
        i += 1
    return pd.DataFrame(out, columns=["date", "net", "jours", "brut"])


def ligne(nom, t, temoin_bp):
    if len(t) < 5:
        return "%-22s %5d" % (nom, len(t))
    m, e = t.net.mean(), t.net.std() / np.sqrt(len(t))
    return "%-22s %5d  brut %+6.1f bp  net %+6.1f bp  (t = %+.1f)  gagnants %2.0f %%  tenue %.1f j  temoin %+5.1f bp  pire %+.1f %%" % (
        nom, len(t), t.brut.mean() * 1e4, m * 1e4, m / e, 100 * (t.net > 0).mean(), t.jours.mean(), temoin_bp, t.net.min() * 100)


if __name__ == "__main__":
    d = pd.read_csv(os.path.join(ICI, "data", "jour.csv.gz"), index_col=0, parse_dates=True)
    d = d[d.index >= "2000-01-01"]
    for seuil in (5, 10, 15, 25):
        for filtre in (True, False):
            tous, tem = [], []
            for s in INDICES:
                t = trades(d[s], d["TAUX_US_3M"], seuil, filtre)
                c = d[s].dropna()
                haut = c > c.rolling(200).mean() if filtre else pd.Series(True, index=c.index)
                jr = c.pct_change().shift(-1)[haut]                    # rendement du jour suivant un jour "au-dessus"
                t["temoin"] = [jr[:x].tail(2500).mean() for x in t.date] * t.jours  # connu a la date, x duree
                tous.append(t.assign(indice=s))
            t = pd.concat(tous).sort_values("date")
            print("\nRSI2 < %d, filtre 200 j : %s" % (seuil, "oui" if filtre else "non"))
            for nom, a, b in (("reglage 2000-2015", "2000", "2016"), ("verdict 2016-2026", "2016", "2027"),
                              ("recent 08/2025-11/2026", "2025-08-06", "2027")):
                x = t[(t.date >= a) & (t.date < b)]
                print("  " + ligne(nom, x, x.temoin.mean() * 1e4 if len(x) else 0))
            if seuil == 10 and filtre:
                x = t[t.date >= "2016"]
                print("  par indice (verdict) : " + ", ".join("%s %d tr %+.0f bp" % (s, len(g), g.net.mean() * 1e4) for s, g in x.groupby("indice")))
                an = x.groupby(x.date.dt.year).net.agg(["count", "sum"])
                print("  par an (somme des trades, %) : " + ", ".join("%d: %+.1f (%d)" % (y, r["sum"] * 100, r["count"]) for y, r in an.iterrows()))
