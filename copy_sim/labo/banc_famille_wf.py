"""Banc AB rigoureux : walk-forward glissant + correction pour essais multiples (suite de banc_famille.py).
Plan fixe d'avance (PRIORITES 17/11) : 4 pistes, grille de reglages enumeree, apprentissage 6 mois / test 1 mois glissant,
choix du reglage au meilleur t (gain par jour) sur l'apprentissage ; Bonferroni (t >= 2,6) et reality check de White
(bootstrap stationnaire, blocs moyens 5 j, 2000 tirages) du meilleur des N reglages contre R0 et contre R1.
R0 = les 4 regles poids 1 ; R1 = R0 sans elan_m15. Gains par jour = trades rattaches au jour de la decision.
Les poids d'un jour J n'utilisent que des trades SORTIS avant le debut de J. Usage : python3 banc_famille_wf.py"""
import contextlib, io
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_famille as F
B, m15, m5, T, tr, REGLES = F.B, F.m15, F.m5, F.T, F.tr, F.REGLES
idx = F.D.index[F.D.index.dayofweek < 5]
BAR = {id(m15): pd.Timedelta("15min"), id(m5): pd.Timedelta("5min")}
FAM = {n: v[3] for n, v in REGLES.items()}


def sortie(n, x):
    """Heure de sortie (cloture de la bougie i+h) de chaque trade de la regle n."""
    d, _, h, _ = REGLES[n]
    i = d.index.get_indexer(x.index)
    return d.index[i + h] + BAR[id(d)]


pj = lambda x: x.g.groupby(x.index.floor("D")).sum().reindex(idx).fillna(0)
J = {n: pj(x) for n, x in T.items()}
JT, JR = J["elan_m15"] + J["cassure_m15"], J["fcassure_m5"] + J["contre_exces_m5"]
R0, R1 = JT + JR, J["cassure_m15"] + JR
# series par jour de SORTIE, pour fabriquer les poids (connues au debut du jour suivant)
X = {n: pd.DataFrame({"g": x.g.values, "fin": sortie(n, x)}) for n, x in T.items()}
def par_sortie(fam):
    z = pd.concat([X[n] for n in X if FAM[n] == fam]).sort_values("fin")
    return z, z.g.groupby(z.fin.dt.floor("D")).sum()
XT, ST = par_sortie("T"); XR, SR = par_sortie("R")
ST = ST.reindex(pd.date_range(idx[0], idx[-1])).fillna(0); SR = SR.reindex(ST.index).fillna(0)
connu = lambda s: s.shift(1).reindex(idx)              # cumul / valeur connue au debut du jour J (calendrier)

CFG = {}                                                # (piste, nom) -> serie $ par jour
# Piste 1 : le marche choisit, delai de jugement k bougies M15
c, sc = m15["cloture"].values, F.s_cass.values
for k, nomk in ((2, "30 min"), (4, "1 h"), (8, "2 h")):
    tm, mv, dern = [], [], -99
    for i in np.flatnonzero(sc != 0):
        if i - dern < k or i + k >= len(c):
            continue
        dern = i
        niv = F.ha.values[i] if sc[i] > 0 else F.ba.values[i]
        tm.append(m15.index[i + k] + BAR[id(m15)]); mv.append(1.0 if (c[i + k] - niv) * sc[i] > 0 else -1.0)
    tm, mv = np.array(tm), np.array(mv)
    tot = 0
    for n, x in T.items():
        dec = x.index + BAR[id(REGLES[n][0])]           # heure ou la decision est prise
        j = np.searchsorted(tm, dec.values, side="right") - 1
        mo = np.where(j >= 0, mv[np.maximum(j, 0)], 0)
        tot = tot + pj(x[mo == (1 if FAM[n] == "T" else -1)])
    CFG[(1, "delai " + nomk)] = tot
# Piste 2 : suivre ce qui marche
for L in (1, 2, 3, 5, 10):
    gT = connu(ST.rolling(L, min_periods=1).sum()) > 0
    gR = connu(SR.rolling(L, min_periods=1).sum()) > 0
    for wg, wp in ((1.5, .5), (2, 0), (1, 0)):
        wT, wR = np.where(gT, wg, wp), np.where(gR, wg, wp)
        CFG[(2, "L=%d j (%g,%g) tend" % (L, wg, wp))] = JT * wT + JR
        CFG[(2, "L=%d j (%g,%g) deux" % (L, wg, wp))] = JT * wT + JR * wR
def dix(z):
    cs = np.r_[0, np.cumsum(z.g.values)]; f = z.fin.values
    k = np.searchsorted(f, idx.values, side="left")    # trades sortis avant minuit du jour J
    return pd.Series(cs[k] - cs[np.maximum(k - 10, 0)], idx) > 0
gT, gR = dix(XT), dix(XR)
for wg, wp in ((1.5, .5), (2, 0), (1, 0)):
    CFG[(2, "10 trades (%g,%g) tend" % (wg, wp))] = JT * np.where(gT, wg, wp) + JR
    CFG[(2, "10 trades (%g,%g) deux" % (wg, wp))] = JT * np.where(gT, wg, wp) + JR * np.where(gR, wg, wp)
# Piste 3 : les deux a la fois (somme des poids = 2 comme R0)
CFG[(3, "1:1")] = JT + JR
CFG[(3, "2:1")] = (4 * JT + 2 * JR) / 3
sT, sR = connu(ST.rolling(60, min_periods=20).std()), connu(SR.rolling(60, min_periods=20).std())
iT, iR = (1 / sT).fillna(1), (1 / sR).fillna(1)
CFG[(3, "risque egal 60 j")] = 2 * (iT * JT + iR * JR) / (iT + iR)
# Piste 4 : filtre de direction sur la famille tendance (retour inchange)
cl = m15["cloture"]
f2j, f20 = np.sign(cl - cl.ewm(span=192).mean()), np.sign(cl - cl.rolling(80).mean())
jh = m15["haut"].groupby(F.jour(m15)).cummax(); jb = m15["bas"].groupby(F.jour(m15)).cummin()
pos = ((cl - jb) / (jh - jb).replace(0, np.nan)).fillna(0.5)
for nf in ("2 j", "20 h", "2 j + 20 h"):
    for bt in (False, True):
        tot = JR
        for n, s in (("elan_m15", F.s_elan), ("cassure_m15", F.s_cass)):
            f = {"2 j": s == f2j, "20 h": s == f20, "2 j + 20 h": (s == f2j) & (s == f20)}[nf]
            if bt:
                f = f & ~(((s > 0) & (pos > 0.8)) | ((s < 0) & (pos < 0.2)))
            tot = tot + pj(tr(m15, s, 12, f.values))
        CFG[(4, "fond %s%s" % (nf, " + pas au bout" if bt else ""))] = tot
N = len(CFG)

# ---------------------------------------------------------------- walk-forward
tstat = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else 0.0
creux = lambda x: (x.cumsum() - x.cumsum().cummax()).min()
mois = idx.to_period("M"); MO = mois.unique()
fen = [(MO[i - 6], MO[i - 1], MO[i]) for i in range(6, len(MO))]
sp = (m15["sp"] / m15["cloture"] * 1e4).mean(), (m5["sp"] / m5["cloture"] * 1e4).mean()
print("Donnees %s -> %s, %d jours ouvres, %d mois ; spread moyen dans B.trades : M15 %.2f bp, M5 %.2f bp (MULT %.1f)" % (idx[0].date(), idx[-1].date(), len(idx), len(MO), sp[0], sp[1], B.MULT))
print("Controle : R0 total %+.0f $ (banc_famille : tendance %+.0f + retour %+.0f) ; R1 %+.0f $" % (R0.sum(), JT.sum(), JR.sum(), R1.sum()))
print("N = %d reglages (piste 1 : %d, 2 : %d, 3 : %d, 4 : %d) ; %d fenetres (test %s -> %s) ; correlation jour tendance/retour %+.2f"
      % (N, *[sum(k[0] == p for k in CFG) for p in (1, 2, 3, 4)], len(fen), fen[0][2], fen[-1][2], JT.corr(JR)))
print("%-7s %-30s %3s %8s %7s %7s %8s %5s %8s %5s %6s %7s" % ("piste", "reglage le plus choisi", "nb", "hors ech", "R0", "R1", "-R0", "t", "-R1", "t", "mois>R0", "creux"))
test_jours = mois >= fen[0][2]
RES = {}
for p in (1, 2, 3, 4):
    cles = [k for k in CFG if k[0] == p]
    oos, choix = [], []
    for a, b, t in fen:
        app, te = (mois >= a) & (mois <= b), mois == t
        best = max(cles, key=lambda k: tstat(CFG[k][app]))
        choix.append(best[1]); oos.append(CFG[best][te])
    o = pd.concat(oos); r0, r1 = R0[o.index], R1[o.index]
    d0, d1 = o - r0, o - r1
    gm = (o.groupby(o.index.to_period("M")).sum() > r0.groupby(r0.index.to_period("M")).sum()).sum()
    fq = pd.Series(choix).value_counts()
    RES[p] = (d0.sum(), tstat(d0))
    print("%-7d %-30s %3s %+8.0f %+7.0f %+7.0f %+8.0f %+5.1f %+8.0f %+5.1f %3d/%-2d %+7.0f" % (p, fq.index[0][:30], "%d/%d" % (fq.iloc[0], len(fen)), o.sum(), r0.sum(), r1.sum(), d0.sum(), tstat(d0), d1.sum(), tstat(d1), gm, len(fen), creux(o)))

# ---------------------------------------------------------------- reality check de White
rng = np.random.default_rng(17)
def boot_idx(n, b=5.0):
    i = np.empty(n, int); i[0] = rng.integers(n)
    neuf = rng.random(n) < 1 / b; nv = rng.integers(n, size=n)
    for t in range(1, n):
        i[t] = nv[t] if neuf[t] else (i[t - 1] + 1) % n
    return i
M = np.column_stack([CFG[k].values for k in CFG]); n = len(idx)
I = [boot_idx(n) for _ in range(2000)]
for nom, R in (("R0", R0), ("R1", R1)):
    Dm = M - R.values[:, None]; mu = Dm.mean(0); V = np.sqrt(n) * mu.max()
    Vb = np.array([np.sqrt(n) * (Dm[ii].mean(0) - mu).max() for ii in I])
    kb = list(CFG)[int(mu.argmax())]
    print("Reality check contre %s : meilleur reglage = piste %d %s (%+.0f $ sur tout l'echantillon), p = %.3f" % (nom, kb[0], kb[1], mu.max() * n, (Vb >= V).mean()))
    RES[nom] = (Vb >= V).mean(); RES["best_" + nom] = kb[0]

# ---------------------------------------------------------------- R1 contre R0
d = (R1 - R0)
pm = d.groupby(mois).sum()
print("R1 - R0 par mois : " + " ".join("%+.0f" % v for v in pm.values))
print("R1 - R0 tout l'echantillon %+.0f $ (t %+.1f, creux %+.0f) ; sur les jours du walk-forward %+.0f $ (t %+.1f, creux %+.0f), mois R1>R0 %d/%d"
      % (d.sum(), tstat(d), creux(d), d[test_jours].sum(), tstat(d[test_jours]), creux(d[test_jours]), (pm[pm.index >= fen[0][2]] > 0).sum(), len(fen)))
print("Verdict (fixe d'avance : tient = diff > 0 et (t >= 2,6 ou p RC < 0,10) ; a observer = diff > 0 et 1 <= t < 2,6 ;")
print("  le p RC, qui porte sur le meilleur des N, ne compte que pour la piste qui contient ce meilleur reglage) :")
for p in (1, 2, 3, 4):
    dd, t = RES[p]
    prc = RES["R0"] if RES["best_R0"] == p else np.nan
    v = "tient" if dd > 0 and (t >= 2.6 or prc < 0.10) else ("a observer" if dd > 0 and t >= 1 else "ne tient pas")
    print("  piste %d : %s (diff %+.0f $, t %+.1f, p RC contre R0 %s)" % (p, v, dd, t, "%.3f" % prc if prc == prc else "sans objet"))
