"""Banc Y (16/11, PRIORITES 14 h, étape a) : détecteur d'aller-retour EN TEMPS RÉEL sur l'or M5 (15 mois, courtier).
Vérité (après coup, par journée serveur) : agitée = amplitude du jour > médiane des 60 jours précédents ;
aller-retour (AR) = agitée et efficacité |clôture - ouverture| / amplitude < 0,35 ; tendance = agitée et >= 0,35 ;
calme = le reste. Détecteur à l'heure h (seulement les bougies déjà fermées) : amplitude depuis 0 h >= médiane
(60 j) de l'amplitude atteinte à la même heure, ET efficacité du chemin depuis 0 h < seuil. Mesures par heure :
part des jours signalés, précision (signalé -> vraiment AR), rappel (AR -> signalé à cette heure), et retard
(première heure où le détecteur s'allume, sur les vrais AR)."""
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
J["agite"] = J.amp > J.med
J["ar"] = J.agite & (J.eff < 0.35)
J["tend"] = J.agite & ~J.ar
print("%d jours : AR %.0f %%, tendance %.0f %%, calme %.0f %%" % (len(J), 100 * J.ar.mean(), 100 * J.tend.mean(), 100 * (~J.agite).mean()))

# trajectoire intrajournaliere : amplitude et efficacite a la fin de chaque heure
rows = []
for j, g in d[d.jour.isin(J.index)].groupby("jour"):
    o = g.cloture.iloc[0]
    for h in range(4, 23):
        x = g[g.h < h]
        if len(x) < 12:
            continue
        a = x.haut.max() - x.bas.min()
        rows.append((j, h, a, abs(x.cloture.iloc[-1] - o) / a if a > 0 else 1.0))
T = pd.DataFrame(rows, columns=["jour", "h", "amp_h", "eff_h"])
T["med_h"] = T.groupby("h").amp_h.transform(lambda s: s.rolling(60).median().shift(1))
T = T.dropna().join(J[["ar", "tend", "agite"]], on="jour")

for seuil in (0.25, 0.35):
    T["sig"] = (T.amp_h >= T.med_h) & (T.eff_h < seuil)
    print("\nseuil d'efficacite %.2f" % seuil)
    print("  heure  signales  precision  rappel   (AR de base %.0f %%)" % (100 * J.ar.mean()))
    for h in (6, 8, 10, 12, 14, 16, 18, 20):
        x = T[T.h == h]
        if not len(x):
            continue
        s = x[x.sig]
        print("  %2d h    %4.0f %%     %4.0f %%    %4.0f %%" % (h, 100 * x.sig.mean(), 100 * s.ar.mean() if len(s) else 0, 100 * x[x.ar].sig.mean()))
    prem = T[T.sig & T.ar].groupby("jour").h.min()
    n_ar = J.ar.sum()
    print("  vrais AR reperes un jour ou l'autre : %.0f %% ; heure mediane du premier signal : %.0f h ; faux signaux (jour de tendance) : %.0f %% des signaux" % (
        100 * len(prem) / n_ar, prem.median() if len(prem) else float("nan"), 100 * T[T.sig].tend.mean()))
