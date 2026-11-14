"""Banc X : l'or autour des annonces americaines de 8 h 30 (heure de New York) - PRIORITES 12/11 12 h 30, famille 3.
Or M5 du courtier (15 mois). Le serveur est a New York + 7 h toute l'annee (verifie : le pic d'amplitude est a
15 h 30 serveur), donc l'annonce tombe dans la bougie de 15:30. Sans calendrier : on prend TOUS les jours ouvres
et on trie par la taille de la bougie de 15:30 (en multiples de l'amplitude M5 moyenne des 2 h precedentes) : une
grosse bougie = une annonce qui a surpris. Entree a l'ouverture de 15:35, dans le sens de la bougie (suite) ;
le resultat « contre » est l'oppose moins deux spreads. Spread reel de la bougie d'entree.
Aussi : premiers vendredis du mois (emploi americain). Reglage 60 % / verdict 40 %. 12 essais.
Usage : python3 banc_annonces.py"""
import numpy as np, pandas as pd
import banc_grille as G

d = G.charge("xau_m5_90k")
t = d["heure"].values
hm = (t // 60) % 1440
amp = (d["haut"] - d["bas"])
prof = amp.groupby(hm).mean().sort_values(ascending=False).head(4)
print("bougies M5 les plus amples (heure serveur) :", ", ".join("%02d:%02d %.2f $" % (m // 60, m % 60, v) for m, v in prof.items()))
ref = amp.rolling(24).mean().shift(1).values
idx = np.flatnonzero(hm == 15 * 60 + 30)
o, c, sp = d["ouverture"].values, d["cloture"].values, d["sp"].values
rows = []
for i in idx:
    if i + 14 >= len(d) or not ref[i] > 0 or t[i + 12] - t[i] != 3600:
        continue
    s = np.sign(c[i] - o[i])
    jour = pd.Timestamp(t[i], unit="s")
    rows.append(dict(i=i, k=abs(c[i] - o[i]) / ref[i], s=s, sp=sp[i + 1], spa=sp[i], nfp=(jour.dayofweek == 4 and jour.day <= 7),
                     **{"r%d" % n: s * (c[i + n] - o[i + 1]) for n in (3, 6, 12)}))
R = pd.DataFrame(rows)
print("%d jours ; taille de la bougie de 15:30 : mediane %.1f x l'amplitude habituelle, 10 %% des jours > %.1f x ; spread median a 15:35 : %.2f $ (habituel %.2f $), les jours > 3x : %.2f $"
      % (len(R), R.k.median(), R.k.quantile(0.9), R.sp.median(), d.sp.median(), R[R.k > 3].sp.median()))
coupe = R.i.quantile(0.6)


def res(x, col):
    g = x[col] - x.sp
    if len(g) < 8:
        return "%3d j        -        " % len(g)
    return "%3d j %+5.2f $ (t %+.1f)" % (len(g), g.mean(), g.mean() / g.std() * np.sqrt(len(g)))


print("%-44s | reglage              | verdict" % "suite de la bougie d'annonce (apres spread)")
for nom, f in (("tous les jours", R.k > 0), ("bougie > 1x", R.k > 1), ("bougie > 2x", R.k > 2), ("bougie > 3x", R.k > 3)):
    for n in (3, 6, 12):
        x = R[f]
        print("  %-42s | %s | %s" % ("%s, tenue %d min" % (nom, n * 5), res(x[x.i < coupe], "r%d" % n), res(x[x.i >= coupe], "r%d" % n)))
x = R[R.nfp]
print("premiers vendredis du mois (emploi) : %d jours ; suite 15 / 30 / 60 min : %s | %s | %s ; taille mediane %.1fx, spread median %.2f $"
      % (len(x), res(x, "r3"), res(x, "r6"), res(x, "r12"), x.k.median(), x.sp.median()))
