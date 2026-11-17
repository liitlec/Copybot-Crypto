"""Banc AD : coupe-circuit journalier et regle du cout, sur la selection des 4 regles de base de banc_famille.py
(elan_m15, cassure_m15, fcassure_m5, contre_exces_m5 ; or, bougies du courtier sur 15 mois, spread reel, pause au
calme v11, $ a 0,01 lot), pas seulement sur les trades du robot.
Les 4 regles tournent ensemble ; un trade est decide a la cloture de sa bougie, et le coupe-circuit ne voit que
les trades DEJA SORTIS a ce moment (les positions ouvertes vont a leur sortie prevue). Reglages (fixes d'avance) :
  J1, J2, J3   : plus de nouveau trade dans la journee (horloge du serveur) des que la perte realisee du jour
                 atteint 1, 2 ou 3 fois la perte moyenne d'un trade perdant (trades perdants des 120 jours
                 ouvres precedents, connus la veille) ;
  A10, A20, A40: idem avec un seuil fixe de -10, -20, -40 $ ;
  S2, S3       : pause de 24 h apres 2 ou 3 pertes de suite (dans l'ordre des sorties ; compteur remis a zero
                 apres la pause) ;
  C10, C20     : regle du cout : trade refuse si le spread de la bougie de decision depasse 0,1 ou 0,2 fois
                 l'amplitude attendue (ces regles n'ont pas de stop : moyenne sur 500 bougies du mouvement
                 |cloture - ouverture| sur la duree de tenue de la regle, connue a la decision).
N = 10. Methode : gains par jour (jour de la decision), walk-forward glissant apprentissage 6 mois / test 1 mois,
reglage au meilleur t sur l'apprentissage ; difference par jour avec la selection sans coupe-circuit (total,
creux, t) ; reality check de White (bootstrap stationnaire, blocs 5 j, 2000 tirages) des 10 reglages contre la
selection sans coupe-circuit ; temoin a exposition egale : meme nombre de trades retires au hasard (200 tirages).
Verdict fixe d'avance sur la difference : tient = diff > 0 et (t >= 2,6 ou p RC < 0,05) ; presque = diff > 0 et
(1,5 <= t < 2,6 ou p < 0,15). Usage : python3 banc_coupe_circuit.py"""
import contextlib, io, heapq
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_famille as F
REGLES, USD = F.REGLES, F.USD
idx = F.D.index[F.D.index.dayofweek < 5]
BAR = {"elan_m15": "15min", "cassure_m15": "15min", "fcassure_m5": "5min", "contre_exces_m5": "5min"}

# ---------------------------------------------------------------- table des trades de la selection
L = []
for n, x in F.T.items():
    d, s, h, _ = REGLES[n]
    i = d.index.get_indexer(x.index)
    b = pd.Timedelta(BAR[n])
    amp = (d["cloture"] - d["ouverture"].shift(h - 1)).abs().rolling(500, min_periods=100).mean()
    L.append(pd.DataFrame({"regle": n, "dec": x.index + b, "fin": d.index[i + h] + b, "g": x.g.values,
                           "sp": d["sp"].values[i], "amp": amp.values[i], "jour": x.index.floor("D")}))
X = pd.concat(L).sort_values("dec").reset_index(drop=True)
X["ratio"] = X.sp / X.amp
dec, fin, g, jr = X.dec.values, X.fin.values, X.g.values, X.jour.values
# perte moyenne d'un trade perdant, 120 jours ouvres precedents (trades sortis avant le debut du jour)
PJ = pd.Series(np.where(g < 0, g, 0.0)).groupby(X.fin.dt.floor("D")).sum()
NJ = pd.Series((g < 0).astype(float)).groupby(X.fin.dt.floor("D")).sum()
cal = pd.date_range(idx[0], idx[-1] + pd.Timedelta("1D"))
PJ, NJ = PJ.reindex(cal).fillna(0), NJ.reindex(cal).fillna(0)
cal_ouv = cal[cal.dayofweek < 5]
PM = (PJ.rolling(168, min_periods=1).sum() / NJ.rolling(168, min_periods=1).sum()).shift(1)   # 168 j civils ~ 120 ouvres
PM = PM.where(NJ.rolling(168, min_periods=1).sum().shift(1) >= 30)
perte_moy = PM.reindex(X.jour).values                                    # negatif


def simule(cfg):
    """Masque des trades pris par la selection avec le coupe-circuit cfg = (type, parametre)."""
    typ, p = cfg
    pris = np.zeros(len(X), bool)
    if typ == "C":
        return X.ratio.values <= p
    ouverts, jour_pnl, serie, pause = [], {}, 0, np.datetime64("1970-01-01")
    for k in range(len(X)):
        t = dec[k]
        while ouverts and ouverts[0][0] <= t:                             # sorties connues avant la decision
            tf, j = heapq.heappop(ouverts)
            dj = tf.astype("datetime64[D]")
            jour_pnl[dj] = jour_pnl.get(dj, 0.0) + g[j]
            if typ == "S" and tf > pause:
                serie = serie + 1 if g[j] < 0 else 0
                if serie >= p:
                    pause, serie = tf + np.timedelta64(24, "h"), 0
        if typ == "S" and t < pause:
            continue
        if typ in ("J", "A"):
            seuil = p * perte_moy[k] if typ == "J" else -p
            if seuil == seuil and jour_pnl.get(t.astype("datetime64[D]"), 0.0) <= seuil:
                continue
        pris[k] = True
        heapq.heappush(ouverts, (fin[k], k))
    return pris


GRILLE = [("J", 1), ("J", 2), ("J", 3), ("A", 10), ("A", 20), ("A", 40), ("S", 2), ("S", 3), ("C", 0.1), ("C", 0.2)]
nom = lambda c: "%s%g" % (c[0], c[1] * 100 if c[0] == "C" else c[1])
par_jour = lambda m: (pd.Series(g[m]).groupby(jr[m]).sum().reindex(idx).fillna(0), pd.Series(m[m]).groupby(jr[m]).size().reindex(idx).fillna(0))
BASE, BN = par_jour(np.ones(len(X), bool))
MASQ = {c: simule(c) for c in GRILLE}
CFG = {c: par_jour(MASQ[c]) for c in GRILLE}
N = len(GRILLE)

tstat = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else 0.0
creux = lambda x: (x.cumsum() - x.cumsum().cummax()).min()
print("Or, 4 regles de base ensemble, %s -> %s (%d jours ouvres), %d trades sans coupe-circuit, total %+.0f $, creux %+.0f $ ; N = %d reglages"
      % (idx[0].date(), idx[-1].date(), len(idx), len(X), BASE.sum(), creux(BASE), N))
print("Perte moyenne d'un trade perdant (120 j) : mediane %.2f $ (de %.2f a %.2f) ; ratio spread / amplitude attendue : mediane %.3f, > 0,1 : %.0f %%, > 0,2 : %.0f %%"
      % (np.nanmedian(perte_moy), np.nanmax(perte_moy), np.nanmin(perte_moy), X.ratio.median(), 100 * (X.ratio > .1).mean(), 100 * (X.ratio > .2).mean()))
print("Tout l'echantillon (reference : selection sans coupe-circuit) :")
print("%-6s %7s %6s %7s %6s %7s %5s | %s" % ("regl.", "total", "creux", "trades", "diff", "t diff", "bp/tr", "diff par regle elan / cassure / fcass / cexces"))
for c in GRILLE:
    o, nb = CFG[c]; dd = o - BASE; m = MASQ[c]
    pr = " / ".join("%+5.0f" % -g[(~m) & (X.regle.values == n)].sum() for n in REGLES)
    print("%-6s %+7.0f %+6.0f %7d %+6.0f %+7.1f %+5.1f | %s" % (nom(c), o.sum(), creux(o), nb.sum(), dd.sum(), tstat(dd), o.sum() / USD / nb.sum(), pr))

# ---------------------------------------------------------------- walk-forward
mois = idx.to_period("M"); MO = mois.unique()
fen = [(MO[i - 6], MO[i - 1], MO[i]) for i in range(6, len(MO))]
oos, nbs, choix = [], [], []
for a_, b_, t_ in fen:
    app, te = (mois >= a_) & (mois <= b_), mois == t_
    best = max(GRILLE, key=lambda c: tstat(CFG[c][0][app]))
    choix.append(nom(best)); oos.append(CFG[best][0][te]); nbs.append(CFG[best][1][te])
o, nb = pd.concat(oos), pd.concat(nbs)
b0, bn0 = BASE[o.index], BN[o.index]
dd = o - b0
pm = o.groupby(o.index.to_period("M")).sum()

# ---------------------------------------------------------------- reality check de White
rng = np.random.default_rng(17)
def boot_idx(n, b=5.0):
    i = np.empty(n, int); i[0] = rng.integers(n)
    neuf = rng.random(n) < 1 / b; nv = rng.integers(n, size=n)
    for t in range(1, n):
        i[t] = nv[t] if neuf[t] else (i[t - 1] + 1) % n
    return i
M = np.column_stack([CFG[c][0].values for c in GRILLE]) - BASE.values[:, None]
mu = M.mean(0); n = len(idx); V = np.sqrt(n) * mu.max()
p = (np.array([np.sqrt(n) * (M[ii].mean(0) - mu).max() for ii in (boot_idx(n) for _ in range(2000))]) >= V).mean()
t = tstat(dd)
v = "tient" if dd.sum() > 0 and (t >= 2.6 or p < 0.05) else ("presque" if dd.sum() > 0 and (1.5 <= t < 2.6 or p < 0.15) else "ne tient pas")
fq = pd.Series(choix).value_counts()
print("\nWalk-forward 6 mois / 1 mois, %d fenetres de test %s -> %s ; choix : %s" % (len(fen), fen[0][2], fen[-1][2], ", ".join("%s %d" % kv for kv in fq.items())))
print("  avec coupe-circuit : total %+.0f $ (t %+.1f), mois gagnants %d/%d, creux %+.0f $, %d trades, %+.2f bp/trade"
      % (o.sum(), tstat(o), (pm > 0).sum(), len(pm), creux(o), nb.sum(), o.sum() / USD / max(nb.sum(), 1)))
print("  sans coupe-circuit memes jours : total %+.0f $ (t %+.1f), creux %+.0f $, %d trades, %+.2f bp/trade"
      % (b0.sum(), tstat(b0), creux(b0), bn0.sum(), b0.sum() / USD / bn0.sum()))
print("  difference : %+.0f $ (t %+.1f), creux de la difference %+.0f $, mois ou la difference > 0 : %d/%d"
      % (dd.sum(), t, creux(dd), (dd.groupby(dd.index.to_period("M")).sum() > 0).sum(), len(pm)))
print("Reality check (10 reglages contre la selection sans coupe-circuit) : meilleur %s (%+.0f $ sur tout l'echantillon), p = %.3f ; Bonferroni : t >= 2,6"
      % (nom(GRILLE[int(mu.argmax())]), mu.max() * n, p))

# ---------------------------------------------------------------- temoin a exposition egale
r2 = np.random.default_rng(3)
print("Temoin : meme nombre de trades retires au hasard (200 tirages), part des tirages qui font au moins aussi bien :")
lig = []
for c in GRILLE:
    k = (~MASQ[c]).sum(); reel = -g[~MASQ[c]].sum()
    pl = np.array([-g[r2.choice(len(X), k, replace=False)].sum() for _ in range(200)])
    lig.append("%s %+.0f (%.2f)" % (nom(c), reel, (pl >= reel).mean()))
print("  " + " ; ".join(lig[:5])); print("  " + " ; ".join(lig[5:]))
print("Verdict (diff > 0 et (t >= 2,6 ou p < 0,05) = tient ; diff > 0 et (1,5 <= t < 2,6 ou p < 0,15) = presque) : %s" % v)
