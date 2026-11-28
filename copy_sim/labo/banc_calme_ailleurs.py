"""Banc Z : quand l'or est calme, d'autres marches bougent-ils, et y gagne-t-on ? (PRIORITES 14/11 13 h, point 3).
Bougies M5 du courtier, spread reel. Regime de chaque marche = le meme que pour l'or (amplitude M5 moyenne sur 24 h
contre sa mediane de 60 jours). Regime de l'OR reporte sur chaque marche par l'heure.
1) Part du temps ou chaque marche est agite pendant que l'or est calme.
2) Mecanique de tendance (celle de bt_or : pyramide de 3, pas 0,25, stop 0,667 ATR jour) sur chaque marche, paniers
   tries par le regime de l'OR a l'entree, puis par le regime du marche lui-meme.
3) Retour a la moyenne (bandes M15 : 2 ecarts-types sur 5 h, objectif la moyenne, stop 2 ecarts-types, 2 h) sur
   chaque marche quand l'or est calme, en points de base apres spread.
Usage : python3 banc_calme_ailleurs.py"""
import numpy as np, pandas as pd
import banc_grille as G
import banc_blocktrend as BT


def regime(d):
    amp = d["haut"] - d["bas"]
    court = amp.rolling(288).mean()
    med = court.rolling(288 * 60, min_periods=288 * 20).median()
    r = pd.Series(np.where(med.shift(1).isna(), np.nan, (court < med).shift(1).astype(float)), index=d["heure"].values)
    return r                                             # 1 = calme, 0 = agite, nan = inconnu


def f(z):
    if len(z) < 10:
        return "%3d paniers        -        " % len(z)
    return "%3d paniers %+5.2f R (t %+.1f), total %+6.1f R" % (len(z), z.mean(), z.mean() / z.std() * np.sqrt(len(z)), z.sum())


def bandes(d, masque):
    o, h, l, c, sp = (d[x].values for x in ("ouverture", "haut", "bas", "cloture", "sp"))
    cs = pd.Series(c); m = cs.rolling(60).mean().values; e = cs.rolling(60).std().values
    z = (c - m) / e
    sig = np.where(masque, (z < -2).astype(int) - (z > 2).astype(int), 0)
    out, libre, n = [], 0, len(d)
    for i in np.flatnonzero(sig):
        if i < libre or i + 27 >= n:
            continue
        s, en = sig[i], o[i + 1]; stop = en - s * 2 * e[i]; x = None
        for j in range(i + 1, i + 25):
            if (l[j] if s > 0 else h[j]) * s <= stop * s:
                x = stop if (o[j] - stop) * s > 0 else o[j]; break
            if (c[j] - m[j]) * s >= 0:
                x = c[j]; break
        if x is None:
            x = c[j]
        out.append((i, (s * (x - en) - sp[i + 1]) / en * 1e4)); libre = j
    return np.array(out)


or_ = G.charge("xau_m5_90k")
r_or = regime(or_)
print("%-10s | %-40s | mecanique de tendance : or calme / or agite | marche calme / marche agite | bandes M15 quand l'or est calme (reglage / verdict)" % ("marche", "agite pendant que l'or est calme"))
for ident, nom in (("nas_m5_90k", "Nasdaq"), ("xag_m5_90k", "argent"), ("eur_m5_90k", "EURUSD"), ("btc_m5_90k", "BTC"), ("eth_m5_90k", "ETH")):
    d = G.charge(ident)
    r = regime(d)
    ro = r_or.reindex(d["heure"].values).ffill(limit=12)
    ens = pd.DataFrame({"m": r.values, "o": ro.values}).dropna()
    part = (ens.m[ens.o == 1] == 0).mean()
    P = BT.simule(d, 0.25, 0.6667, 3)
    x = pd.DataFrame([(p[0], p[3]) for p in P], columns=["i", "g"])
    x["o"] = ro.values[x.i.values]; x["m"] = r.values[x.i.values]
    b = bandes(d, (ro.values == 1))
    k = len(d) * 0.6
    rb = lambda y: "%4d tr %+5.2f bp (t %+.1f)" % (len(y), y.mean(), y.mean() / y.std() * np.sqrt(len(y))) if len(y) > 20 else "%4d tr" % len(y)
    print("%-10s | agite %2.0f %% du temps ou l'or est calme (%s) | %s / %s | %s / %s | %s / %s" % (
        nom, 100 * part, pd.Timestamp(d["heure"].iloc[0], unit="s").strftime("%m/%Y"),
        f(x.g[x.o == 1]), f(x.g[x.o == 0]), f(x.g[x.m == 1]), f(x.g[x.m == 0]),
        rb(b[b[:, 0] < k, 1]) if len(b) else "-", rb(b[b[:, 0] >= k, 1]) if len(b) else "-"))
