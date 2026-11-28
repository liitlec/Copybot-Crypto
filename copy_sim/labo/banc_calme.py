"""Banc Y : comment profiter des moments calmes de l'or ? (PRIORITES 14/11 13 h). Or M5 du courtier, 15 mois,
spread reel, entree a l'ouverture de la bougie suivante, gains en $ par once (= par trade a 0,01 lot).
REGIME fixe d'avance (le meme que `agite` du robot, en M5) : calme si l'amplitude M5 moyenne des 24 dernieres
heures est sous sa mediane des 60 derniers jours ; connu a la bougie precedente.
Regles de retour a la moyenne (on vend l'exces haut, on achete l'exces bas) :
  bandes_m15 : cloture a plus de 2 ecarts-types de sa moyenne de 5 h (60 bougies M5) ; objectif = la moyenne ;
               stop = 2 ecarts-types plus loin ; 2 h au plus.
  bandes_h1  : idem sur 20 h (240 bougies) ; 8 h au plus.
  asie       : apres 8 h serveur, cloture hors de la fourchette 1 h - 8 h -> pari sur le retour au milieu ;
               stop = une demi-fourchette plus loin ; sortie a 22 h au plus ; une fois par cote et par jour.
Variante « coupe » : sortie immediate si le regime repasse agite pendant le trade.
Puis : ce que coutent les jours calmes a la mecanique de tendance bt_or (paniers tries par regime a l'entree).
Reglage 60 % / verdict 40 %. Usage : python3 banc_calme.py"""
import numpy as np, pandas as pd
import banc_grille as G
import banc_blocktrend as BT

d = G.charge("xau_m5_90k")
o, h, l, c, sp, t = (d[x].values for x in ("ouverture", "haut", "bas", "cloture", "sp", "heure"))
hs = d["h"].values
n = len(d)
amp = pd.Series(h - l)
court = amp.rolling(288).mean()
med = court.rolling(288 * 60, min_periods=288 * 20).median()
calme = (court < med).shift(1).fillna(False).values.astype(bool)
connu = med.shift(1).notna().values
print("or M5 : %d bougies ; regime connu sur %.0f %% ; calme %.0f %% du temps connu" % (n, 100 * connu.mean(), 100 * calme[connu].mean()))


def jouer(sig, cible, stopd, maxb, coupe=False, fin_h=None):
    out, libre = [], 0
    for i in np.flatnonzero(sig):
        if i < libre or i + maxb + 2 >= n or not connu[i] or not stopd[i] > 0 or hs[i] >= 22 or hs[i] < 2:
            continue
        s, e = sig[i], o[i + 1]
        stop = e - s * stopd[i]
        reg = calme[i]
        x = None
        for j in range(i + 1, i + 1 + maxb):
            if (l[j] if s > 0 else h[j]) * s <= stop * s:
                x = stop if (o[j] - stop) * s > 0 else o[j]; break
            cb = cible[j] if cible.ndim else cible
            if (c[j] - cb) * s >= 0:
                x = c[j]; break
            if (coupe and reg and not calme[j]) or (fin_h is not None and hs[j] >= fin_h) or hs[j] >= 23:
                x = c[j]; break
        if x is None:
            x = c[j]
        out.append((i, reg, s * (x - e) - sp[i + 1]))
        libre = j
    return pd.DataFrame(out, columns=["i", "calme", "g"])


def res(x):
    if len(x) < 15:
        return "%4d tr       -        " % len(x)
    return "%4d tr %+5.2f $ (t %+.1f)" % (len(x), x.g.mean(), x.g.mean() / x.g.std() * np.sqrt(len(x)))


k = int(n * 0.6)
cs = pd.Series(c)
regles = {}
for nom, w, maxb in (("bandes_m15", 60, 24), ("bandes_h1", 240, 96)):
    m, e = cs.rolling(w).mean(), cs.rolling(w).std()
    z = (cs - m) / e
    sig = ((z < -2).astype(int) - (z > 2).astype(int)).values
    regles[nom] = (sig, m.values, (2 * e).values, maxb, None)
jour = t // 86400
asie = d[(d.h >= 1) & (d.h < 8)].groupby(jour[(hs >= 1) & (hs < 8)]).agg(hi=("haut", "max"), lo=("bas", "min"))
hi, lo = asie.hi.reindex(jour).values, asie.lo.reindex(jour).values
ok = (hs >= 8) & (hs < 20)
dessus, dessous = ok & (c > hi), ok & (c < lo)
prem = lambda m: m & (pd.Series(m).groupby(jour).cumsum().values == 1)
sig = prem(dessous).astype(int) - prem(dessus).astype(int)
regles["asie"] = (sig, (hi + lo) / 2, (hi - lo) / 2, 168, 22)

print("%-34s | %-52s | %s" % ("retour a la moyenne", "reglage : calme / agite", "verdict : calme / agite"))
for nom, (sig, cible, stopd, maxb, fin_h) in regles.items():
    for coupe in (False, True):
        x = jouer(sig, cible, stopd, maxb, coupe, fin_h)
        a, b = x[x.i < k], x[x.i >= k]
        print("  %-32s | %s / %s | %s / %s" % (nom + (" + coupe si agite" if coupe else ""), res(a[a.calme]), res(a[~a.calme]), res(b[b.calme]), res(b[~b.calme])))

print("\nCe que coutent les jours calmes a la tendance (bt_or : pyramide de 3, pas 0,25, stop 0,667 ATR), en R par panier")
P = BT.simule(d, 0.25, 0.6667, 3)
x = pd.DataFrame([(p[0], p[3]) for p in P], columns=["i", "g"])
x = x[connu[x.i.values]]
x["calme"] = calme[x.i.values].astype(bool)
for nom, y in (("reglage", x[x.i < k]), ("verdict", x[x.i >= k]), ("tout", x)):
    a, b = y[y.calme], y[~y.calme]
    f = lambda z: "%3d paniers, %+5.2f R en moyenne, total %+6.1f R, %2.0f %% gagnants" % (len(z), z.g.mean(), z.g.sum(), 100 * (z.g > 0).mean())
    print("  %-8s calme : %s | agite : %s" % (nom, f(a), f(b)))
