"""Banc Y bis (16/11, PRIORITES 15 h 30) : précision du détecteur d'aller-retour (objectif >= 75 %) et règle de retour
à stop court. Or M5 15 mois. Pour chaque journée, PREMIER signal (heure h, bougies fermées seulement) d'une règle :
amplitude depuis 0 h / médiane 60 j à la même heure >= k, efficacité du chemin < e, nombre de traversées de
l'ouverture du jour >= x, heure >= h0. Grille choisie sur la 1re moitié des jours, jugée sur la 2de.
Règle de retour au signal : prix dans le tiers haut de l'amplitude -> vente, tiers bas -> achat ; objectif = milieu
de l'amplitude ; stop = extrême du jour + 10 % de l'amplitude ; sinon sortie en fin de journée. Spread réel. En R."""
import itertools
import numpy as np, pandas as pd
import banc_grille as G

d = G.charge("xau_m5_90k")
t = d["heure"].values
d["jour"], d["h"] = t // 86400, (t // 3600) % 24
J = d.groupby("jour").agg(o=("cloture", "first"), c=("cloture", "last"), hi=("haut", "max"), lo=("bas", "min"), n=("cloture", "size"))
J = J[J.n > 200]
J["amp"] = J.hi - J.lo
J["eff"] = (J.c - J.o).abs() / J.amp
J["med"] = J.amp.rolling(60).median().shift(1)
J = J.dropna()
J["ar"] = (J.amp > J.med) & (J.eff < 0.35)
base = J.ar.mean()

rows = []
for j, g in d[d.jour.isin(J.index)].groupby("jour"):
    c, hi, lo, hh, sp = g.cloture.values, g.haut.values, g.bas.values, g.h.values, g.sp.values
    o = c[0]
    cross = np.concatenate([[0], np.cumsum(np.sign(c[1:] - o) * np.sign(c[:-1] - o) < 0)])
    for h in range(6, 22):
        k = np.searchsorted(hh, h) - 1                 # derniere bougie fermee avant l'heure h
        if k < 11:
            continue
        H, L = hi[:k + 1].max(), lo[:k + 1].min()
        a = H - L
        if a <= 0:
            continue
        pos = (c[k] - L) / a
        # issue de la regle de retour a partir de la bougie k+1
        s = -1 if pos > 2 / 3 else (1 if pos < 1 / 3 else 0)
        r = np.nan
        if s:
            e = c[k] + (sp[k] if s > 0 else 0.0)
            stop = (L - 0.1 * a) if s > 0 else (H + 0.1 * a)
            obj = L + a / 2
            risque = abs(e - stop)
            r = s * (c[-1] - e) / risque
            for i in range(k + 1, len(c)):
                if (s > 0 and lo[i] <= stop) or (s < 0 and hi[i] + sp[i] >= stop):
                    r = -1.0; break
                if (s > 0 and hi[i] >= obj) or (s < 0 and lo[i] + sp[i] <= obj):
                    r = s * (obj - e) / risque; break
        rows.append((j, h, a, abs(c[k] - o) / a, cross[k], r))
T = pd.DataFrame(rows, columns=["jour", "h", "amp_h", "eff_h", "cross", "r"])
T["ratio"] = T.amp_h / T.groupby("h").amp_h.transform(lambda s: s.rolling(60).median().shift(1))
T = T.dropna(subset=["ratio"]).join(J[["ar"]], on="jour")
jours = np.sort(T.jour.unique()); mi = jours[len(jours) // 2]


def evalue(df, k, e, x, h0):
    s = df[(df.ratio >= k) & (df.eff_h < e) & (df.cross >= x) & (df.h >= h0)]
    f = s.sort_values("h").groupby("jour").first()
    return f


res = []
for k, e, x, h0 in itertools.product((1.0, 1.3, 1.6, 2.0), (0.1, 0.15, 0.2, 0.25, 0.35), (0, 3, 6, 10), (8, 12, 16, 18)):
    a = evalue(T[T.jour < mi], k, e, x, h0)
    if len(a) >= 5:
        res.append((a.ar.mean(), len(a), (k, e, x, h0)))
print("%d essais de grille ; aller-retour de base %.0f %% des jours" % (len(res), 100 * base))
print("\ncourbe precision / jours signales (meilleur reglage par tranche de jours, choisi en 1re moitie, juge en 2de) :")
print("  jours signales (1re moitie)  precision 1re  | 2de moitie : jours  precision  regle de retour : trades  moy R  gagnants")
for lo_n, hi_n in ((5, 8), (8, 12), (12, 20), (20, 35), (35, 60), (60, 200)):
    c_ = [r for r in res if lo_n <= r[1] < hi_n]
    if not c_:
        continue
    p, n, reg = max(c_)
    b = evalue(T[T.jour >= mi], *reg)
    rr = b.r.dropna()
    print("  %3d-%3d : %3d jours  %4.0f %%  %-22s | %3d  %4.0f %%   %3d  %+5.2f  %3.0f %%" % (
        lo_n, hi_n, n, 100 * p, str(reg), len(b), 100 * b.ar.mean() if len(b) else 0, len(rr),
        rr.mean() if len(rr) else 0, 100 * (rr > 0).mean() if len(rr) else 0))
print("\nregle de retour sans detecteur (tous jours, premiere occasion a partir de 12 h) :")
f = T[T.h >= 12].sort_values("h").groupby("jour").first()
rr = f.r.dropna()
print("  %d trades  moy %+.2f R  gagnants %.0f %%  | jours AR : %+.2f R  autres : %+.2f R" % (
    len(rr), rr.mean(), 100 * (rr > 0).mean(), f[f.ar].r.mean(), f[~f.ar].r.mean()))
