"""Banc AR : les autres marches annoncent-ils l'or ? (avance / retard intrajournalier, bougies M5 du courtier).
Donnees : or xau (m5_2025a + m5_90k), nas (m5_2025a + m5_90k), sp, dj, xag, eur (image inverse du dollar), btc (10 mois
seulement : mesure (1) uniquement). Jointure EXACTE des horodatages sur une grille de 5 min : un rendement sur L minutes
n'existe que si TOUTES les bougies de la fenetre existent chez les deux instruments (indices fermes la nuit, week-end,
trous : pas de rendement « perime »). Bougies en prix vendeur, horloge du serveur (UTC+2/+3).
Seances (heure du serveur, a l'instant t) : Asie 0-9 h, Londres 9-15 h, New York 15-24 h.
(1) Mesure : correlation entre le rendement de X sur L (5..120 min) finissant en t et celui de l'or sur H (5..120 min)
    commencant en t (et l'inverse) ; z approche = rho * racine(n * 5 / max(L, H)) (chevauchement). Tout, par moitie, par
    seance. Evenements : |X| > k ecarts-types sur 5 ou 15 min (ecart-type glissant 2000 obs., connu avant) et |or| < 0,5
    ecart-type sur la meme fenetre ; or sur 15/30/60 min ensuite, signe dans le sens du mouvement de X (ev. espaces de 1 h).
(2) Regle : |zX(L)| > k et |zOr(L)| < |zX(L)| / 2 -> or dans le sens de X (ou contre : sens = signe du gain brut moyen
    sur l'APPRENTISSAGE seulement), entree a l'ouverture de la bougie suivante, sortie apres H, spread reel (B.trades).
    Grille fixee : X {nas, sp, dj, xag, eur} x L {5, 15} x k {2, 3} x H {15, 60} = 40 reglages (x 2 sens = 80 series
    pour le reality check). Walk-forward 6 mois -> 1 mois, choix au meilleur t des gains par jour. Reference : rien.
(3) Filtres « les autres marches confirment » sur elan_m15 / cassure_m15 (banc_famille.py, pause au calme incluse).
    Etat a la cloture de la bougie M15 : correlation glissante 2 h (24 rendements M5) or/argent, or/euro, or/Nasdaq ;
    un marche vote si |rho| >= 0,2 et son rendement 3 h existe ; sens implique = signe(rho) x signe(rendement 3 h).
    7 filtres x 2 regles = 14 reglages. Reference : la regle sans filtre a exposition egale (base x part des trades
    gardes, part mesuree sur l'apprentissage) ; walk-forward 6 -> 1 mois sur l'ecart ; reality check sur les 14 ecarts.
Verdict fixe d'avance : tient = hors ech. > 0 et (t >= 2,6 ou p RC < 0,05) ; presque = > 0 et (1,5 <= t < 2,6 ou p < 0,15).
Usage : python3 banc_avance_retard.py"""
import contextlib, io
from statistics import NormalDist
import numpy as np, pandas as pd
import banc_or as B
with contextlib.redirect_stdout(io.StringIO()):
    import banc_famille as F

SRC = {"xau": ("xau_m5_2025a", "xau_m5_90k"), "nas": ("nas_m5_2025a", "nas_m5_90k"), "sp": ("sp_m5_90k",),
       "dj": ("dj_m5_90k",), "xag": ("xag_m5_90k",), "eur": ("eur_m5_90k",), "btc": ("btc_m5_90k",)}


def charge(ids):
    d = pd.concat([B.charge(i)[0] for i in ids])
    return d[~d.index.duplicated(keep="last")].sort_index()


P = {k: charge(v) for k, v in SRC.items()}
OR = P["xau"]
XS = [k for k in P if k != "xau"]
G = pd.date_range(OR.index[0], OR.index[-1], freq="5min")
LP = pd.DataFrame({k: np.log(P[k]["cloture"]).reindex(G) for k in P})
OK = LP.notna().astype(int)
HS = (5, 15, 30, 60, 120)


def past(k, L):
    m = L // 5
    return (LP[k] - LP[k].shift(m)).where(OK[k].rolling(m + 1).sum() == m + 1)


PA = {k: {L: past(k, L) for L in HS} for k in P}
FU = {k: {H: PA[k][H].shift(-(H // 5)) for H in HS} for k in P}


def sig(r):
    v = r.dropna()
    return v.rolling(2000, min_periods=500).std().shift(1).reindex(G)


SG = {(k, L): sig(PA[k][L]) for k in P for L in (5, 15)}
Z = {(k, L): PA[k][L] / SG[(k, L)] for k in P for L in (5, 15)}
hr = G.hour
SES = np.where(hr < 9, 0, np.where(hr < 15, 1, 2))
tstat = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else 0.0
creux = lambda x: (x.cumsum() - x.cumsum().cummax()).min()
zb = lambda n: NormalDist().inv_cdf(1 - 0.05 / n)

com = {x: len(P[x].index.intersection(OR.index)) for x in XS}
tous = OR.index
for x in XS:
    tous = tous.intersection(P[x].index)
print("Or M5 %s -> %s (%d bougies). Bougies communes (jointure exacte) avec l'or : %s ; communes aux 7 : %d (%s -> %s)"
      % (OR.index[0].date(), OR.index[-1].date(), len(OR), ", ".join("%s %d (des %s)" % (x, com[x], P[x].index[0].date()) for x in XS),
         len(tous), tous[0].date(), tous[-1].date()))

# ------------------------------------------------------------------ (1) mesure
def cell(a, b, extra=None):
    m = a.notna().values & b.notna().values
    if extra is not None:
        m &= extra
    return (np.corrcoef(a.values[m], b.values[m])[0, 1] if m.sum() > 100 else np.nan), m.sum()


print("(1) rho(rendement X sur L finissant en t, or sur H commencant en t) ; z approche ; seuil Bonferroni |z| >= %.1f "
      "(25 cases x 6 X x 2 sens)" % zb(600))
inv = []
for x in XS:
    for sens in ("X", "O"):
        A, Bf = (PA[x], FU["xau"]) if sens == "X" else (PA["xau"], FU[x])
        res = {}
        for L in HS:
            for H in HS:
                r, n = cell(A[L], Bf[H]); res[(L, H)] = (r, n, r * np.sqrt(n * 5 / max(L, H)))
        (L, H), (r, n, z) = max(res.items(), key=lambda kv: abs(kv[1][2]) if kv[1][2] == kv[1][2] else -1)
        m0 = A[L].notna().values & Bf[H].notna().values
        tm = G[m0][m0.sum() // 2]
        hm = [cell(A[L], Bf[H], (G < tm) if i == 0 else (G >= tm))[0] for i in (0, 1)]
        se = [cell(A[L], Bf[H], SES == s)[0] for s in (0, 1, 2)]
        if sens == "O":
            inv.append("%s L%d/H%d %+.3f z%+.1f (%+.2f/%+.2f)" % (x, L, H, r, z, *hm)); continue
        r0 = cell(PA[x][5], PA["xau"][5])[0]
        print("  %-3s->or rho meme bougie %+.2f | (5,5) %+.3f z%+.1f (15,15) %+.3f z%+.1f (60,60) %+.3f z%+.1f | max L%d/H%d %+.3f z%+.1f moities %+.3f/%+.3f A/L/NY %+.3f/%+.3f/%+.3f"
              % (x, r0, res[(5, 5)][0], res[(5, 5)][2], res[(15, 15)][0], res[(15, 15)][2], res[(60, 60)][0], res[(60, 60)][2], L, H, r, z, *hm, *se))
print("  or->X, case max (moities) : " + " ; ".join(inv[:3]))
print("                              " + " ; ".join(inv[3:]))

print("  Evenements X > k sigma en 5 ou 15 min, or < 0,5 sigma ; or ensuite dans le sens de X, bp (t) a 15 / 30 / 60 min :")
for x in XS:
    out = []
    for k in (2, 3):
        e5 = (Z[(x, 5)].abs() > k) & (Z[("xau", 5)].abs() < 0.5)
        e15 = (Z[(x, 15)].abs() > k) & (Z[("xau", 15)].abs() < 0.5)
        dr = np.where(e5, np.sign(PA[x][5]), np.sign(PA[x][15]))
        ti = np.flatnonzero((e5 | e15).values)
        kept, last = [], -99
        for i in ti:
            if i - last >= 12:
                kept.append(i); last = i
        kept = np.array(kept, int)
        s = "k%d n=%4d" % (k, len(kept))
        for H in (15, 30, 60):
            v = (FU["xau"][H].values[kept] * dr[kept] * 1e4)
            v = v[~np.isnan(v)]
            s += " %+5.1f(%+.1f)" % (v.mean() if len(v) else np.nan, tstat(v))
        out.append(s)
    print("  %-3s %s | %s" % (x, out[0], out[1]))

# ------------------------------------------------------------------ (2) regle tradable
DJ = pd.DatetimeIndex(sorted(set(OR.index.floor("D"))))
DJ = DJ[DJ.dayofweek < 5]
MOIS = DJ.to_period("M"); MO = MOIS.unique()
FEN = [(MO[i - 6], MO[i - 1], MO[i]) for i in range(6, len(MO))]
CFG = [(x, L, k, H) for x in ("nas", "sp", "dj", "xag", "eur") for L in (5, 15) for k in (2, 3) for H in (15, 60)]
TR = {}
for c in CFG:
    x, L, k, H = c
    zx, zo = Z[(x, L)], Z[("xau", L)]
    cond = (zx.abs() > k) & (zo.abs() < zx.abs() / 2) & FU["xau"][H].notna()
    s = (np.sign(PA[x][L]) * cond).fillna(0).reindex(OR.index).fillna(0)
    for d in (1, -1):
        a, i = B.trades(OR, s * d, H // 5)
        TR[(c, d)] = pd.DataFrame({"net": a[:, 0], "brut": a[:, 1]}, index=OR.index[i].floor("D"))
DAY = {kd: t.net.groupby(level=0).sum().reindex(DJ).fillna(0) for kd, t in TR.items()}


def walk(scores, tests, trades_fn):
    oos, choix, ntr = [], [], []
    for a, b, t in FEN:
        app, te = (MOIS >= a) & (MOIS <= b), MOIS == t
        best = max(scores(app), key=lambda kv: kv[1])[0]
        choix.append(best); oos.append(tests(best, app)[te]); ntr.append(trades_fn(best, a, b, t))
    return pd.concat(oos), choix, ntr


rng = np.random.default_rng(17)
def boot_idx(n, b=5.0):
    i = np.empty(n, int); i[0] = rng.integers(n)
    neuf = rng.random(n) < 1 / b; nv = rng.integers(n, size=n)
    for t in range(1, n):
        i[t] = nv[t] if neuf[t] else (i[t - 1] + 1) % n
    return i


def rc(M):
    n = len(M); mu = M.mean(0); V = np.sqrt(n) * mu.max()
    Vb = np.array([np.sqrt(n) * (M[boot_idx(n)].mean(0) - mu).max() for _ in range(2000)])
    return int(mu.argmax()), (Vb >= V).mean()


def verdict(tot, t, p):
    return "TIENT" if tot > 0 and (t >= 2.6 or p < 0.05) else ("PRESQUE" if tot > 0 and (1.5 <= t or p < 0.15) else "NE TIENT PAS")


def sens(c, app):
    t = TR[(c, 1)]; b = t.brut[t.index.isin(DJ[app])]
    return 1 if len(b) == 0 or b.mean() > 0 else -1


def tr_test(kd, a, b, t):
    x = TR[kd]; return x.net[x.index.to_period("M") == t]


o, ch, nt = walk(lambda app: [((c, sens(c, app)), tstat(DAY[(c, sens(c, app))][app])) for c in CFG],
                 lambda kd, app: DAY[kd], tr_test)
nt = pd.concat(nt)
fq = pd.Series(["%s L%d k%d H%d %s" % (*c, "suivre" if d > 0 else "contre") for c, d in ch]).value_counts()
KD = list(TR); ib, p2 = rc(np.column_stack([DAY[kd].values for kd in KD]))
om = o.groupby(o.index.to_period("M")).sum()
print("(2) Regle or apres mouvement de X : %d jours ouvres %s -> %s, N = %d reglages (x 2 sens = %d pour le RC), %d fenetres de test %s -> %s"
      % (len(DJ), DJ[0].date(), DJ[-1].date(), len(CFG), len(KD), len(FEN), FEN[0][2], FEN[-1][2]))
print("  hors ech. : total %+.0f bp, t %+.1f, mois > 0 %d/%d, pire creux %+.0f bp, %d trades, %+.2f bp/trade net ; reference rien = 0"
      % (o.sum(), tstat(o), (om > 0).sum(), len(om), creux(o), len(nt), nt.mean() if len(nt) else np.nan))
print("  reglage le plus choisi : %s (%d/%d) ; autres : %s" % (fq.index[0], fq.iloc[0], len(FEN), ", ".join("%s (%d)" % (a, b) for a, b in fq.iloc[1:4].items())))
cb, db = KD[ib]; tb = TR[(cb, db)]
print("  reality check (80 series contre rien) : meilleur %s %s, %+.0f bp sur tout l'echantillon, %d trades, %+.2f bp/trade, p = %.3f ; Bonferroni t >= %.2f"
      % ("%s L%d k%d H%d" % cb, "suivre" if db > 0 else "contre", tb.net.sum(), len(tb), tb.net.mean(), p2, zb(len(KD))))
print("  VERDICT (2) : %s" % verdict(o.sum(), tstat(o), p2))

# ------------------------------------------------------------------ (3) filtres « les autres confirment »
m15 = F.m15
tq = m15.index + pd.Timedelta("10min")                   # bougie M5 qui se ferme en meme temps que la M15
VOTE = {}
for x in ("xag", "eur", "nas"):
    a, b = PA["xau"][5].copy(), PA[x][5].copy()
    m = a.isna() | b.isna(); a[m] = np.nan; b[m] = np.nan
    rho = a.rolling(24, min_periods=20).corr(b).reindex(tq).values
    r3 = past(x, 180).reindex(tq).values
    ok = (np.abs(rho) >= 0.2) & ~np.isnan(r3)
    VOTE[x] = (ok, np.sign(rho) * np.sign(r3), np.nan_to_num(np.abs(rho)))
idx3 = F.D.index[F.D.index.dayofweek < 5]
M3 = idx3.to_period("M"); MO3 = M3.unique()
FEN3 = [(MO3[i - 6], MO3[i - 1], MO3[i]) for i in range(6, len(MO3))]
NOMS = ["majorite confirme", "tous confirment", "argent confirme", "euro confirme", "nasdaq confirme",
        "divergence (majorite contre)", "correlation forte (moy |rho| > 0,3)"]
T3, BASE = {}, {}
for n, s in (("elan_m15", F.s_elan), ("cassure_m15", F.s_cass)):
    sv = s.values
    cf = {x: VOTE[x][0] & (VOTE[x][1] == sv) for x in VOTE}
    co = {x: VOTE[x][0] & (VOTE[x][1] == -sv) for x in VOTE}
    c, d = sum(cf.values()), sum(co.values())
    moy = sum(VOTE[x][2] for x in VOTE) / 3
    fl = [c >= 2, c == 3, cf["xag"], cf["eur"], cf["nas"], d >= 2, moy > 0.3]
    b = F.T[n]; BASE[n] = pd.DataFrame({"g": b.g.values / F.USD}, index=b.index)
    for nm, f in zip(NOMS, fl):
        x = F.tr(m15, s, 12, np.asarray(f, bool))
        T3[(n, nm)] = pd.DataFrame({"g": x.g.values / F.USD}, index=x.index)
pj3 = lambda x: x.g.groupby(x.index.floor("D")).sum().reindex(idx3).fillna(0)
D3 = {k: pj3(v) for k, v in T3.items()}; DB = {n: pj3(v) for n, v in BASE.items()}
cnt = lambda x, per: (x.index.floor("D").isin(idx3[per])).sum()
def q(k, per):
    nb = cnt(BASE[k[0]], per); return cnt(T3[k], per) / nb if nb else 0
print("(3) Filtres sur la tendance de l'or, %s -> %s, N = %d ; bp/trade net filtre (n, t de l'ecart au base) :"
      % (idx3[0].date(), idx3[-1].date(), len(T3)))
print("  base sans filtre : elan_m15 %d tr %+.2f bp/tr ; cassure_m15 %d tr %+.2f bp/tr"
      % (len(BASE["elan_m15"]), BASE["elan_m15"].g.mean(), len(BASE["cassure_m15"]), BASE["cassure_m15"].g.mean()))
for nm in NOMS:
    s = "  %-38s" % nm
    for n in ("elan_m15", "cassure_m15"):
        g, b = T3[(n, nm)].g, BASE[n].g
        e = (g.mean() - b.mean()) / np.sqrt(g.var() / len(g)) if len(g) > 2 else np.nan
        s += " | %-11s %4d tr %+6.2f (t %+.1f)" % (n, len(g), g.mean(), e)
    print(s)
K3 = list(T3)
EC = lambda k, app: D3[k] - q(k, app) * DB[k[0]]
oos, ch3, filt, refe = [], [], [], []
for a, b, t in FEN3:
    app, te = (M3 >= a) & (M3 <= b), M3 == t
    best = max(K3, key=lambda k: tstat(EC(k, app)[app]))
    ch3.append(best); oos.append(EC(best, app)[te]); filt.append(D3[best][te]); refe.append((q(best, app) * DB[best[0]])[te])
o3, f3, r3 = pd.concat(oos), pd.concat(filt), pd.concat(refe)
ntr3 = sum(((T3[k].index.to_period("M") == t)).sum() for k, (_, _, t) in zip(ch3, FEN3))
i3, p3 = rc(np.column_stack([(D3[k] - q(k, np.ones(len(idx3), bool)) * DB[k[0]]).values for k in K3]))
fq3 = pd.Series(["%s / %s" % k for k in ch3]).value_counts()
om3 = o3.groupby(o3.index.to_period("M")).sum()
print("  walk-forward %d fenetres (%s -> %s) : filtre choisi %+.0f bp (t %+.1f, %d trades, %+.2f bp/tr) contre base a exposition egale %+.0f bp"
      % (len(FEN3), FEN3[0][2], FEN3[-1][2], f3.sum(), tstat(f3), ntr3, f3.sum() / max(ntr3, 1), r3.sum()))
print("  ecart hors ech. %+.0f bp, t %+.1f, mois > 0 %d/%d, pire creux %+.0f bp ; le plus choisi : %s (%d/%d)"
      % (o3.sum(), tstat(o3), (om3 > 0).sum(), len(om3), creux(o3), fq3.index[0], fq3.iloc[0], len(FEN3)))
print("  reality check (14 ecarts a exposition egale) : meilleur %s / %s, p = %.3f ; Bonferroni t >= %.2f"
      % (*K3[i3], p3, zb(len(K3))))
print("  VERDICT (3) (ecart au base a exposition egale) : %s ; filtre seul contre rien : %s"
      % (verdict(o3.sum(), tstat(o3), p3), verdict(f3.sum(), tstat(f3), 1.0)))
