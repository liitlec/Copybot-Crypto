"""Banc AA : le calme qui precede le mouvement (PRIORITES 14/11 19 h 30, points 1 et 2). Or M5 du courtier, 15 mois.
1) Compression : la fourchette (plus haut - plus bas) des N dernieres heures est dans le cinquieme le plus etroit
   de ses 60 derniers jours (connu a la bougie precedente). Entree : premiere cloture M5 hors de cette fourchette
   (cassure), dans son sens, a l'ouverture suivante ; stop = retour de l'autre cote du milieu de la fourchette ;
   sortie au temps. Comparaison : la meme cassure quand la fourchette n'est PAS comprimee (les 4 autres cinquiemes).
   N = 4 h, 8 h, 24 h ; tenue 1 h, 4 h. 12 cases x 2. Gains en $ par once apres spread.
2) Spread reel et amplitude par heure, jours calmes / agites (regime du robot), et combien de temps dure un calme.
Reglage 60 % / verdict 40 %. Usage : python3 banc_compression.py"""
import numpy as np, pandas as pd
import banc_grille as G

d = G.charge("xau_m5_90k")
o, h, l, c, sp = (d[x].values for x in ("ouverture", "haut", "bas", "cloture", "sp"))
hs = d["h"].values
n = len(d); k = int(n * 0.6)


def res(x):
    x = np.array(x)
    if len(x) < 15:
        return "%4d tr       -        " % len(x)
    return "%4d tr %+5.2f $ (t %+.1f)" % (len(x), x.mean(), x.mean() / x.std() * np.sqrt(len(x)))


print("%-40s | reglage : comprime / normal %22s | verdict : comprime / normal" % ("cassure d'une fourchette", ""))
for heures in (4, 8, 24):
    w = heures * 12
    hi = d["haut"].rolling(w).max().shift(1); lo = d["bas"].rolling(w).min().shift(1)
    larg = hi - lo
    seuil = larg.rolling(288 * 60, min_periods=288 * 20).quantile(0.2).shift(1)
    comp = (larg < seuil).values; connu = seuil.notna().values
    hi, lo, larg = hi.values, lo.values, larg.values
    sig = (c > hi).astype(int) - (c < lo).astype(int)
    for tenue in (12, 48):
        R = {(a, b): [] for a in (0, 1) for b in (0, 1)}
        libre = 0
        for i in np.flatnonzero(sig):
            if i < libre or i + tenue + 2 >= n or not connu[i] or hs[i] < 2 or hs[i] >= 22:
                continue
            s, e = sig[i], o[i + 1]
            stop = (hi[i] + lo[i]) / 2
            x = None
            for j in range(i + 1, i + 1 + tenue):
                if (l[j] if s > 0 else h[j]) * s <= stop * s:
                    x = stop if (o[j] - stop) * s > 0 else o[j]; break
            if x is None:
                x = c[j]
            R[(int(i >= k), int(comp[i]))].append(s * (x - e) - sp[i + 1])
            libre = j
        print("  %-38s | %s / %s | %s / %s" % ("fourchette %2d h, tenue %d h" % (heures, tenue // 12), res(R[(0, 1)]), res(R[(0, 0)]), res(R[(1, 1)]), res(R[(1, 0)])))

# 2) spread et amplitude par heure, selon le regime du robot ; duree des calmes
amp = pd.Series(h - l)
court = amp.rolling(288).mean(); med = court.rolling(288 * 60, min_periods=288 * 20).median()
calme = (court < med).shift(1)
ok = med.shift(1).notna()
x = pd.DataFrame({"h": hs, "sp": sp, "amp": amp.values, "calme": calme.values})[ok.values]
x["calme"] = x["calme"].astype(bool)
g = x.groupby(["calme", "h"]).agg(sp=("sp", "median"), amp=("amp", "mean")).unstack(0)
print("\nheure serveur : spread median / amplitude M5 moyenne ($), jours calmes | agites ; rapport spread / amplitude au calme")
for hh in range(1, 24):
    print("  %02d h : %.2f / %5.2f | %.2f / %5.2f | %3.0f %%" % (hh, g["sp"][True][hh], g["amp"][True][hh], g["sp"][False][hh], g["amp"][False][hh], 100 * g["sp"][True][hh] / g["amp"][True][hh]))
v = x["calme"].values
chg = np.flatnonzero(np.diff(v.astype(int))) + 1
segs = np.diff(np.r_[0, chg, len(v)]); etat = v[np.r_[0, chg]]
for nom, b in (("calme", True), ("agite", False)):
    s = segs[etat == b] / 288
    print("periodes de %s : %d ; duree mediane %.1f jour(s) de bourse, moyenne %.1f, la plus longue %.0f" % (nom, len(s), np.median(s), s.mean(), s.max()))
