"""Banc AF : le panier bt_or comme thermometre de la tendance de l'or (PRIORITES 18/11, 8 h 30).
Idee : quand le panier bt_or gagne (tendance reelle), mettre en pause les regles de RETOUR ; quand il n'y a pas de
panier, ou qu'il perd ou stagne, les garder, voire doubler leur mise.
Etat du panier : mecanique bt_or figee (banc_bt_regulier.simule : pas 0,25 ATR, stop suiveur 0,667 ATR, 3 positions),
rejouee sur les bougies M5 du courtier avec le spread reel ; a la cloture de chaque bougie M5 on note le gain latent
des paniers ouverts en R (sortie a la cloture, achat au bid, vente a l'ask). Pas de fuite : une decision prise a la
cloture d'une bougie n'utilise que l'etat de la bougie M5 cloturee AU MOINS 5 min plus tot (decalage d'une bougie).
Etats : absent / perdant (< 0 R) / stagnant (0 a X R) / gagnant (> X R).
Regles (une position a la fois par regle, B.trades avec spread reel, $ a 0,01 lot = 0,40 $ par bp) :
  RETOUR : fcassure_m5, contre_exces_m5 (banc_famille.py, pause au calme v11) et retour_court_ar (robot v14, M15 :
           cloture a plus de 2,5 ecarts-types de la moyenne des 20 bougies precedentes ou fausse cassure du range du
           jour -> on joue le retour ; stop juste au-dela de l'extreme des 2 dernieres bougies + 0,5 $ (au moins 3 $),
           objectif milieu du range du jour, sortie a 3 h ; stop avant objectif si les deux dans la meme bougie).
  TENDANCE : elan_m15, cassure_m15 (banc_famille.py). R0 = selection actuelle = les 4 regles de banc_famille.
(1) Descriptif 15 mois : resultat de chaque regle selon l'etat a l'entree, X en {0,5 ; 1 ; 2}, par moitie.
(2) Bascule, grille fixee d'avance N = 24 : X en {0 ; 0,5 ; 1 ; 2} x mise des regles de retour (gagnant x0 ; sinon
    x1 / sinon x2 / absent x1, perdant x2, stagnant x1) x {retour seul ; et tendance x2 quand le panier gagne}.
    Walk-forward glissant 6 mois / 1 mois, choix au meilleur t (gain par jour) sur l'apprentissage. Mesure principale :
    difference contre les MEMES regles sans thermometre A EXPOSITION EGALE (mise moyenne realisee dans le mois de
    test, par famille). Reality check de White (bootstrap stationnaire, blocs 5 j, 2000 tirages) sur les 24 series
    de difference a exposition egale. Temoin : etat du panier decale au hasard (rotation circulaire de 20 j au moins,
    meme proportion et memes blocs de pause), 200 tirages. Comparaisons : R0, R0 + retour_court_ar, « suivre ce qui
    marche » 5 jours (banc_famille_wf, L = 5 j, poids 2/0, deux familles), triche (retour coupe les jours ou la
    tendance gagne, connu d'avance).
(3) Or H1 08/2022-11/2026 : bt_or rejoue en H1 (reglages de banc_bt_regulier), regle de retour H1 = contre la sortie
    de la fourchette de 12 h, tenue 3 h ; tendance H1 = la suit. Signe de l'effet « panier gagnant » par annee.
Verdict (fixe d'avance) sur la difference a exposition egale : tient = > 0 ET (t >= 2,6 OU p RC < 0,05) ;
presque = > 0 et (1,5 <= t < 2,6 ou p < 0,15) ; sinon ne tient pas. Usage : python3 banc_thermometre.py"""
import contextlib, io, itertools, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_famille_wf as W
import banc_bt_regulier as BR
F, B = W.F, W.B
USD = F.USD
PAS, STOP, MAXP = BR.PAS, BR.STOP, BR.MAXP


def simule_etat(d, span=576, heures=BR.H_M5, debut=600):
    """Copie de banc_bt_regulier.simule qui rend en plus, a la cloture de chaque bougie, le gain latent en R des
    paniers ouverts (NaN = pas de panier). Les paniers rendus doivent etre identiques a BR.simule."""
    c, hi, lo, sp, t = (d[x].values for x in ("cloture", "haut", "bas", "sp", "heure"))
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    P, ouvert, lat = [], {}, np.full(len(c), np.nan)
    for i in range(debut, len(c)):
        for s in list(ouvert):
            p = ouvert[s]
            niveau = p["meilleur"] - s * p["stop"]
            if (lo[i] <= niveau) if s > 0 else (hi[i] + sp[i] >= niveau):
                p = ouvert.pop(s)
                P.append(sum(s * (niveau - e) for e in p["e"]) / p["stop"])
                continue
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            while len(p["e"]) < MAXP and s * (c[i] - p["prochain"]) >= 0:
                if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                    p["e"].append(c[i] + (sp[i] if s > 0 else -sp[i]))
                p["prochain"] += s * p["pas"]
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if s not in ouvert:
                ouvert[s] = {"i": i, "e": [c[i] + (sp[i] if s > 0 else -sp[i])], "meilleur": c[i], "stop": STOP * atr[i],
                             "pas": PAS * atr[i], "prochain": c[i] + s * PAS * atr[i]}
        if ouvert:
            lat[i] = sum(sum(s * ((c[i] if s > 0 else c[i] + sp[i]) - e) for e in p["e"]) / p["stop"] for s, p in ouvert.items())
    return np.array(P), lat


def etat_connu(t_bar, lat, dec):
    """Gain latent connu pour des decisions prises aux instants dec : bougie dont la cloture precede dec d'une bougie."""
    pas = np.median(np.diff(t_bar[:1000]))
    j = np.searchsorted(t_bar, dec - 2 * pas, side="right") - 1
    return np.where(j >= 0, lat[np.maximum(j, 0)], np.nan), j


# ---------------------------------------------------------------- donnees et etat du panier (15 mois, M5)
d5 = BR.charge("xau_m5_90k")
Pg, LAT = simule_etat(d5)
P_ref = BR.simule(d5)
T5 = d5.heure.values
ns = lambda ix: (ix.values.astype("datetime64[s]").astype(np.int64))


def retour_court_ar(m):
    """Regle retour_court_ar du robot (v14) rejouee en M15 : DataFrame (g $, s) indexe par la bougie de decision."""
    o, h, l, c, sp = (m[x].values for x in ("ouverture", "haut", "bas", "cloture", "sp"))
    cs = m["cloture"]
    mo, sd = cs.shift(1).rolling(20).mean().values, cs.shift(1).rolling(20).std().values
    jr = (m.index.values.astype("datetime64[s]").astype(np.int64)) // 86400
    hd = pd.Series(h).groupby(jr).cummax().shift(2).values; ld = pd.Series(l).groupby(jr).cummin().shift(2).values
    nb = pd.Series(1, index=range(len(c))).groupby(jr).cumsum().values           # rang de la bougie dans le jour
    hj = pd.Series(h).groupby(jr).cummax().values; lj = pd.Series(l).groupby(jr).cummin().values
    res, idx, i, n = [], [], 21, len(c)
    while i < n - 13:
        s = 0
        if sd[i] > 0 and abs(c[i] - mo[i]) > 2.5 * sd[i]:
            s = -1 if c[i] > mo[i] else 1
        elif nb[i] >= 6 and jr[i - 1] == jr[i]:                              # >= 4 bougies du jour avant i-1
            if h[i - 1] > hd[i] and c[i] < hd[i]:
                s = -1
            elif l[i - 1] < ld[i] and c[i] > ld[i]:
                s = 1
        if s == 0:
            i += 1; continue
        e = i + 1
        ent = o[e] + (sp[e] if s > 0 else 0.0)
        mini = max(3.0, 3 * sp[e])
        if s < 0:
            stop = max(max(h[i - 1], h[i]) + 0.5, ent + sp[e] + mini)
        else:
            stop = min(min(l[i - 1], l[i]) - 0.5, o[e] - mini)
        mil = (hj[i] + lj[i]) / 2
        obj = mil if (s > 0 and mil > ent + sp[e]) or (s < 0 and mil < o[e] - sp[e]) else None
        sortie = None
        for k in range(e, i + 13):
            if s > 0:
                if l[k] <= stop:
                    sortie = min(o[k], stop) if k > e else stop; break
                if obj is not None and h[k] >= obj:
                    sortie = max(o[k], obj) if k > e else obj; break
            else:
                if h[k] + sp[k] >= stop:
                    sortie = max(o[k] + sp[k], stop) if k > e else stop; break
                if obj is not None and l[k] + sp[k] <= obj:
                    sortie = min(o[k] + sp[k], obj) if k > e else obj; break
        if sortie is None:
            k = i + 12; sortie = c[k] + (sp[k] if s < 0 else 0.0)
        g = (sortie - ent) / o[e] if s > 0 else (ent - sortie) / o[e]
        res.append(g * 1e4 * USD); idx.append(i)
        i = k
    return pd.DataFrame({"g": res, "s": 0}, index=m.index[idx])


m15 = F.m15
TR = dict(F.T); TR["retour_court_ar"] = retour_court_ar(m15)
FAM = {"elan_m15": "T", "cassure_m15": "T", "fcassure_m5": "R", "contre_exces_m5": "R", "retour_court_ar": "R"}
BAR = {"elan_m15": 900, "cassure_m15": 900, "retour_court_ar": 900, "fcassure_m5": 300, "contre_exces_m5": 300}
idx = W.idx; jour_pos = pd.Series(np.arange(len(idx)), idx)
rows = []
for n, x in TR.items():
    x = x[(x.index >= idx[0]) & (x.index < idx[-1] + pd.Timedelta("1D"))]
    dec = ns(x.index) + BAR[n]
    la, jj = etat_connu(T5, LAT, dec)
    dj = jour_pos.reindex(x.index.floor("D")).values
    rows.append(pd.DataFrame({"r": n, "f": FAM[n], "g": x.g.values, "lat": la, "j": jj, "jour": dj, "t": x.index}))
TT = pd.concat(rows, ignore_index=True)
TT = TT[TT.jour == TT.jour].reset_index(drop=True); TT["jour"] = TT.jour.astype(int)
mil = F.mil
ND = len(idx)
pj = lambda g, msk=None: np.bincount(TT.jour.values[msk] if msk is not None else TT.jour.values,
                                     weights=g[msk] if msk is not None else g, minlength=ND)
isR, isT = (TT.f == "R").values, (TT.f == "T").values
JT = pd.Series(pj(TT.g.values * isT), idx); JRet = pd.Series(pj(TT.g.values * isR), idx)
JR2 = pd.Series(pj(TT.g.values * (isR & (TT.r != "retour_court_ar").values)), idx)
R0 = JT + JR2
tst = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else 0.0
creux = lambda x: (np.cumsum(x) - np.maximum.accumulate(np.cumsum(x))).min()
print("Or M5 %s -> %s (%d jours ouvres). Controles : bt_or %d paniers %+.1f R (banc_bt_regulier %+.1f R, identiques : %s) ;"
      % (idx[0].date(), idx[-1].date(), ND, len(Pg), Pg.sum(), P_ref.g.sum(), bool(np.allclose(np.sort(Pg), np.sort(P_ref.g.values)))))
print("  R0 (4 regles) %+.0f $ (banc_famille_wf %+.0f) ; retour_court_ar %d trades %+.0f $ ; spread moyen M5 %.2f bp"
      % (R0.sum(), W.R0.sum(), (TT.r == "retour_court_ar").sum(), TT.g[TT.r == "retour_court_ar"].sum(), W.sp[1]))

# ---------------------------------------------------------------- (1) descriptif
def classe(lat, X):
    return np.where(np.isnan(lat), 0, np.where(lat < 0, 1, np.where(lat <= X, 2, 3)))
ok5 = ~np.isnan(LAT[600:])
print("(1) Part du temps (bougies M5) : absent %.0f %%, perdant %.0f %% ; gagnant > 0,5 / 1 / 2 R : %.0f / %.0f / %.0f %%"
      % (100 * (~ok5).mean(), 100 * (LAT[600:] < 0).mean(), *[100 * (LAT[600:] > X).mean() for X in (0.5, 1, 2)]))
cell = lambda g: "%4d %+5.0f %+5.1f" % (len(g), g.sum(), tst(g)) if len(g) > 2 else "%4d   -       " % len(g)
LIGNES = [("absent", 0, 1), ("perdant <0", 1, 1)] + [(("%s %g" % (nm, X)), k, X) for X in (0.5, 1, 2) for nm, k in (("0..", 2), ("> ", 3))]
ordre = ["fcassure_m5", "contre_exces_m5", "retour_court_ar", "elan_m15", "cassure_m15"]
print("  etat a l'entree | " + " | ".join("%-16s" % n[:16] for n in ordre) + " | (n $ t)")
for lab, k, X in LIGNES:
    cl = classe(TT.lat.values, X)
    print("  %-15s | " % lab + " | ".join(cell(TT.g.values[(TT.r == n).values & (cl == k)]) for n in ordre))
print("  familles : bp/trade, $ 1re/2de moitie, t   | RETOUR (3 regles)                | TENDANCE (2 regles)")
h1 = (TT.t < mil).values
for lab, k, X in LIGNES:
    cl = classe(TT.lat.values, X)
    z = []
    for fm in (isR, isT):
        g = TT.g.values[fm & (cl == k)]; a = TT.g.values[fm & (cl == k) & h1]; b = TT.g.values[fm & (cl == k) & ~h1]
        z.append("%5d %+6.2fbp %+6.0f/%+6.0f t%+5.1f" % (len(g), g.mean() / USD if len(g) else 0, a.sum(), b.sum(), tst(g)))
    print("  %-15s | %s | %s" % (lab, z[0], z[1]))

# ---------------------------------------------------------------- (2) bascule
MISES = {"sinon x1": (1, 1, 1), "sinon x2": (2, 2, 2), "abs x1 perd x2": (1, 2, 1)}    # (absent, perdant, stagnant)
GR = list(itertools.product((0, 0.5, 1, 2), MISES, (False, True)))


def poids(lat, cfg):
    X, mise, tend = cfg
    a, p, s = MISES[mise]
    cl = classe(lat, X)
    wR = np.choose(cl, [a, p, s, 0]).astype(float)
    wT = np.where(cl == 3, 2.0, 1.0) if tend else np.ones(len(lat))
    return np.where(isR, wR, wT)


def series(lat, cfg):
    w = poids(lat, cfg)
    return pd.Series(pj(TT.g.values * w), idx), w


def egal(w, msk):
    """Base sans thermometre a exposition egale : mise moyenne realisee par famille sur les trades de msk."""
    kR = w[isR & msk].mean() if (isR & msk).any() else 1.0
    kT = w[isT & msk].mean() if (isT & msk).any() else 1.0
    return kT * JT + kR * JRet


mois = idx.to_period("M"); MO = mois.unique()
fen = [(MO[i - 6], MO[i - 1], MO[i]) for i in range(6, len(MO))]
mtr = TT.t.dt.to_period("M").values
S = {k: series(TT.lat.values, k) for k in GR}


def walk(S, lat=None):
    oos, base, ch = [], [], []
    for a, b, t in fen:
        app, te = (mois >= a) & (mois <= b), mois == t
        best = max(GR, key=lambda k: tst(S[k][0][app]))
        s, w = S[best] if lat is None else series(lat, best)
        oos.append(s[te]); base.append(egal(w, mtr == t)[te]); ch.append(best)
    return pd.concat(oos), pd.concat(base), ch


o, e, ch = walk(S)
dd = o - e
fq = pd.Series(["X%g %s %s" % (k[0], k[1], "+tend" if k[2] else "") for k in ch]).value_counts()
Dm = np.column_stack([(S[k][0] - egal(S[k][1], np.ones(len(TT), bool))).values for k in GR])
rng = np.random.default_rng(17)
I = [W.boot_idx(ND) for _ in range(2000)]
n = ND; mu = Dm.mean(0); V = np.sqrt(n) * mu.max()
p_rc = (np.array([np.sqrt(n) * (Dm[ii].mean(0) - mu).max() for ii in I]) >= V).mean()
kb = GR[int(mu.argmax())]
om = o.groupby(o.index.to_period("M")).sum(); dm = dd.groupby(dd.index.to_period("M")).sum()
print("(2) Bascule : N = %d reglages, %d mois de test (%s -> %s) ; choisi le plus souvent : %s (%d/%d)"
      % (len(GR), len(fen), fen[0][2], fen[-1][2], fq.index[0], fq.iloc[0], len(fen)))
ntr = sum(((mtr == t) & (S[k][1] > 0)).sum() for (_, _, t), k in zip(fen, ch))
wt = np.concatenate([S[k][1][mtr == t] for (_, _, t), k in zip(fen, ch)]); gt = np.concatenate([TT.g.values[mtr == t] for _, _, t in fen])
print("  hors echantillon %+.0f $ (t %+.1f), mois gagnants %d/%d, creux %+.0f $, %d trades actifs, %+.2f bp par trade mise"
      % (o.sum(), tst(o), (om > 0).sum(), len(om), creux(o.values), ntr, (wt * gt).sum() / wt[wt > 0].sum() / USD))
print("  contre la meme exposition sans thermometre : %+.0f $ (t %+.1f), mois > %d/%d, creux %+.0f ; RC des 24 : meilleur X%g %s%s, p = %.3f ; Bonferroni t >= %.1f"
      % (dd.sum(), tst(dd), (dm > 0).sum(), len(dm), creux(dd.values), kb[0], kb[1], " +tend" if kb[2] else "", p_rc, 2.6))
# temoin : etat du panier tourne au hasard (memes proportions, memes blocs)
nl = len(LAT); jT = TT.j.values
tem = []
for _ in range(200):
    off = rng.integers(288 * 20, nl - 288 * 20)
    la = np.where(jT >= 0, LAT[(jT + off) % nl], np.nan)
    So = {k: series(la, k) for k in GR}
    a, b, _ = walk(So)
    tem.append(((a - b).sum(), a.sum()))
tem = np.array(tem)
print("  temoin etat au hasard (200 rotations) : difference a expo. egale %+.0f $ en moyenne, rang du vrai %.0f %% ; total %+.0f $, rang %.0f %%"
      % (tem[:, 0].mean(), 100 * (tem[:, 0] < dd.sum()).mean(), tem[:, 1].mean(), 100 * (tem[:, 1] < o.sum()).mean()))
ix = o.index
SUIV = W.CFG[(2, "L=5 j (2,0) deux")]
TRI = JT + JRet * (JT <= 0)
for nom, r in (("ne rien faire", 0 * o), ("R0 (4 regles x1)", R0[ix]), ("R0 + retour_court_ar x1", (JT + JRet)[ix]),
               ("retour seul x1 (sans tendance)", JRet[ix]), ("suivre ce qui marche 5 j", SUIV[ix]), ("triche (tendance du jour connue)", TRI[ix])):
    z = o - r
    print("  %-34s %+7.0f $ ; thermometre - lui : %+6.0f $ (%+5.1f $/j, t %+.1f)" % (nom, r.sum(), z.sum(), z.mean(), tst(z)))
v = "tient" if dd.sum() > 0 and (tst(dd) >= 2.6 or p_rc < 0.05) else (
    "presque" if dd.sum() > 0 and (tst(dd) >= 1.5 or p_rc < 0.15) else "ne tient pas")
print("  Verdict (fixe d'avance, difference a exposition egale) : %s" % v)

# ---------------------------------------------------------------- (3) or H1, 4 ans
dh = BR.charge("xau_h1_50k")
dh = dh[dh.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
Ph, LH = simule_etat(dh, span=48, heures={(2, 0), (7, 0), (11, 0), (14, 0), (15, 0)}, debut=60)
dh.index = pd.to_datetime(dh.heure, unit="s")
hh, bb = dh["haut"].shift(1).rolling(12).max(), dh["bas"].shift(1).rolling(12).min()
sc = (dh["cloture"] > hh).astype(float) - (dh["cloture"] < bb).astype(float)
print("(3) Or H1 %s -> %s : bt_or %d paniers %+.0f R ; effet = $/trade panier gagnant (> 1 R) - autres etats (t)"
      % (dh.index[0].date(), dh.index[-1].date(), len(Ph), Ph.sum()))
for nom, s in (("retour H1 (contre sortie 12 h, 3 h)", -sc), ("tendance H1 (suit sortie 12 h, 3 h)", sc)):
    x, i = B.trades(dh, s, 3)
    g = x[:, 0] * USD
    la = LH[np.maximum(i - 1, 0)]; la[i < 1] = np.nan
    gag = la > 1
    yr = dh.index[i].year
    z = []
    for y in sorted(set(yr)):
        a, b = g[gag & (yr == y)], g[~gag & (yr == y)]
        z.append("%d %+.2f" % (y, a.mean() - b.mean() if len(a) and len(b) else np.nan))
    a, b = g[gag], g[~gag]
    ef = a.mean() - b.mean(); se = np.sqrt(a.var() / len(a) + b.var() / len(b))
    print("  %-36s %4d tr %+5.0f $ ; gagnant %3d tr %+.2f $/tr, autres %+.2f ; effet %+.2f (t %+.1f) ; par an : %s"
          % (nom, len(g), g.sum(), len(a), a.mean(), b.mean(), ef, ef / se, ", ".join(z)))
