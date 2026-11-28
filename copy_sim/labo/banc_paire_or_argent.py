"""Banc paire or / argent : l'ecart (log-ratio or/argent) revient-il a sa moyenne ?

Regle : r = log(or) - log(argent) ; z = (r - moyenne glissante W) / ecart-type glissant W, calcule a la cloture.
|z| > seuil -> on joue le retour : z > 0 = vendre l'or, acheter l'argent ; z < 0 = l'inverse.
Sortie quand z repasse par 0 (change de signe) ou, en intrajournalier, apres W bougies (meme duree que la fenetre).
Tout est decale d'une bougie : decision a la cloture i, execution a l'ouverture i+1 (journalier : cloture i+1).
Jambes : valeur egale (1 / 1) ou ponderees par le beta glissant (rend. or sur rend. argent, fenetre W, borne 0,2-2) ;
valeur brute totale = 2 jambes, gains exprimes en bp de la valeur d'UNE jambe.

(a) Intrajournalier : bougies M5 du courtier XAUUSD et XAGUSD (prix vendeur), jointure exacte sur l'horodatage,
    spread reel de chaque jambe (achat a vendeur + spread, vente a vendeur). Grille fixee d'avance :
    W {2 h, 8 h, 24 h, 5 j} x seuil {2 ; 2,5 ; 3} x jambes {egales, beta} = 24 reglages.
    Walk-forward glissant apprentissage 6 mois / test 1 mois, choix au meilleur t des gains par jour.
(b) Journalier : Yahoo GC=F et SI=F (cache data/metaux_jour.csv.gz), jointure exacte sur la date.
    W {20, 60, 120} j x seuil {1,5 ; 2}, sortie a 0, jambes egales = 6 reglages ; cout aller-retour par jambe =
    spread median observe dans les bougies du courtier (or et argent). Walk-forward 3 ans / 1 an.
Gains rattaches au jour de SORTIE du trade (l'apprentissage ne voit que des trades clos). Reference = ne rien faire (0).
Essais multiples : reality check de White (bootstrap stationnaire, blocs moyens 5 j, 2000 tirages) sur les N reglages
contre 0 ; seuil Bonferroni rappele. Correlation des gains par jour hors echantillon avec le rendement de l'or seul.
Usage : python3 banc_paire_or_argent.py"""
import os, contextlib, io
import numpy as np, pandas as pd
from statistics import NormalDist
import banc_or as B
with contextlib.redirect_stdout(io.StringIO()):
    import donnees as DN

ICI = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(17)
tstat = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else 0.0
creux = lambda x: (x.cumsum() - x.cumsum().cummax()).min()


def simule(lr, wg_beta, o_g, o_s, sp_g, sp_s, W, seuil, tmax):
    """Trades non chevauchants. Retourne liste (indice sortie, gain bp sur une jambe, apres couts)."""
    z = ((lr - lr.rolling(W).mean()) / lr.rolling(W).std()).values
    n, out, i = len(z), [], W
    while i < n - 2:
        if not np.isfinite(z[i]) or abs(z[i]) <= seuil:
            i += 1; continue
        sg = -np.sign(z[i])                       # +1 = acheter l'or / vendre l'argent
        e, j = i + 1, i + 1
        while j < n - 1 and np.sign(z[j]) == np.sign(z[i]) and (tmax is None or j - i < tmax):
            j += 1
        x = j + 1                                 # execution a l'ouverture suivante
        if x >= n:
            break
        b = wg_beta[i]; wg, ws = 2 / (1 + b), 2 * b / (1 + b)
        if sg > 0:   # or achete, argent vendu
            lg = (o_g[x] - (o_g[e] + sp_g[e])) / o_g[e]; ls = (o_s[e] - (o_s[x] + sp_s[x])) / o_s[e]
        else:
            lg = (o_g[e] - (o_g[x] + sp_g[x])) / o_g[e]; ls = (o_s[x] - (o_s[e] + sp_s[e])) / o_s[e]
        out.append((x, (wg * lg + ws * ls) * 1e4))
        i = x
    return out


def boot_idx(n, b=5.0):
    i = np.empty(n, int); i[0] = rng.integers(n)
    neuf = rng.random(n) < 1 / b; nv = rng.integers(n, size=n)
    for t in range(1, n):
        i[t] = nv[t] if neuf[t] else (i[t - 1] + 1) % n
    return i


def reality_check(CFG, n_tir=2000):
    M = np.column_stack([v.values for v in CFG.values()]); n = len(M)
    mu = M.mean(0); V = np.sqrt(n) * mu.max()
    Vb = np.array([np.sqrt(n) * (M[boot_idx(n)].mean(0) - mu).max() for _ in range(n_tir)])
    return list(CFG)[int(mu.argmax())], mu.max() * n, (Vb >= V).mean()


def walk_forward(CFG, TR, per, app, ref_or):
    """per : periode de chaque jour ; app : nb de periodes d'apprentissage. Rend la ligne de resultats."""
    P = per.unique(); oos, choix, ntr, gtr = [], [], 0, []
    for k in range(app, len(P)):
        a = (per >= P[k - app]) & (per <= P[k - 1]); te = per == P[k]
        best = max(CFG, key=lambda c: tstat(CFG[c][a]))
        choix.append(best); oos.append(CFG[best][te])
        t = TR[best]; g = t[t.index.isin(CFG[best].index[te])]
        ntr += len(g); gtr.extend(g.values)
    o = pd.concat(oos)
    gp = o.groupby(per[per >= P[app]]).sum()
    fq = pd.Series(choix).value_counts()
    corr = o.corr(ref_or.reindex(o.index).fillna(0))
    return dict(choix=fq.index[0], nchoix="%d/%d" % (fq.iloc[0], len(choix)), tot=o.sum(), t=tstat(o),
                gagn="%d/%d" % ((gp > 0).sum(), len(gp)), creux=creux(o), ntr=ntr, bp=np.mean(gtr) if gtr else np.nan,
                corr=corr, deb=o.index[0].date(), fin=o.index[-1].date())


def verdict(tot, t, p):
    if tot > 0 and (t >= 2.6 or p < 0.05): return "TIENT"
    if tot > 0 and (1.5 <= t < 2.6 or p < 0.15): return "PRESQUE"
    return "NE TIENT PAS"


def affiche(nom, CFG, TR, r):
    kb, tot_b, p = reality_check(CFG)
    N = len(CFG); bonf = NormalDist().inv_cdf(1 - 0.05 / N)
    print("%-26s %5s %9s %5s %6s %6s %7s %8s %6s" % ("reglage le plus choisi", "nb", "hors ech", "t", "per.+", "trades", "bp/tr", "creux", "corr or"))
    print("%-26s %5s %+9.0f %+5.1f %6s %6d %+7.2f %+8.0f %+6.2f" % (r["choix"], r["nchoix"], r["tot"], r["t"], r["gagn"], r["ntr"], r["bp"], r["creux"], r["corr"]))
    print("Test hors echantillon %s -> %s (unite : bp d'une jambe, somme) ; reference ne rien faire = 0" % (r["deb"], r["fin"]))
    print("Reality check (N=%d, contre 0) : meilleur = %s (%+.0f bp sur tout), p = %.3f ; Bonferroni t >= %.2f" % (N, kb, tot_b, p, bonf))
    print("Verdict %s : %s" % (nom, verdict(r["tot"], r["t"], p)))


# =================================================================== (a) intrajournalier M5
def partie_a():
    g, _ = B.charge("xau_m5_90k"); s, _ = B.charge("xag_m5_90k")
    g = g[~g.index.duplicated()]; s = s[~s.index.duplicated()]
    com = g.index.intersection(s.index)
    print("== (a) M5 courtier : or %d bougies %s -> %s, argent %d %s -> %s" % (len(g), g.index[0], g.index[-1], len(s), s.index[0], s.index[-1]))
    deb, fin = max(g.index[0], s.index[0]), min(g.index[-1], s.index[-1])
    hg = ((g.index >= deb) & (g.index <= fin)).sum(); hs = ((s.index >= deb) & (s.index <= fin)).sum()
    print("Alignement : %d horodatages communs ; sur la periode commune, or seul %d, argent seul %d (ecartes)" % (len(com), hg - len(com), hs - len(com)))
    g, s = g.loc[com], s.loc[com]
    assert (g.index == s.index).all()
    print("Spread median : or %.2f bp, argent %.2f bp" % ((g.sp / g.cloture).median() * 1e4, (s.sp / s.cloture).median() * 1e4))
    lr = np.log(g.cloture) - np.log(s.cloture)
    rg, rs = np.log(g.cloture).diff(), np.log(s.cloture).diff()
    og, os_, spg, sps = g.ouverture.values, s.ouverture.values, g.sp.values, s.sp.values
    jour = g.index.floor("D"); jours = pd.DatetimeIndex(jour.unique()); jours = jours[jours.dayofweek < 5]
    CFG, TR = {}, {}
    for nw, W in (("2h", 24), ("8h", 96), ("24h", 288), ("5j", 1440)):
        beta = (rg.rolling(W).cov(rs) / rs.rolling(W).var()).clip(0.2, 2).fillna(1).values
        for sv in (2.0, 2.5, 3.0):
            for nj, wb in (("egal", np.ones(len(g))), ("beta", beta)):
                tr = simule(lr, wb, og, os_, spg, sps, W, sv, W)
                k = "W%s z%.1f %s" % (nw, sv, nj)
                t = pd.Series([v for _, v in tr], index=jour[[x for x, _ in tr]])
                TR[k] = t
                CFG[k] = t.groupby(level=0).sum().reindex(jours).fillna(0)
    print("N = %d reglages ; donnees %s -> %s (%d jours ouvres)" % (len(CFG), jours[0].date(), jours[-1].date(), len(jours)))
    print("Plein echantillon (info) : " + " ; ".join("%s %+.0f/%d" % (k.replace(" ", ""), CFG[k].sum(), len(TR[k])) for k in list(CFG)[::2][:12]))
    ref = np.log(g.cloture).groupby(jour).last().diff().reindex(jours) * 1e4
    r = walk_forward(CFG, TR, jours.to_period("M"), 6, ref)
    affiche("(a)", CFG, TR, r)


# =================================================================== (b) journalier Yahoo
def partie_b():
    f = os.path.join(ICI, "data", "metaux_jour.csv.gz")
    if not os.path.exists(f):
        os.makedirs(os.path.dirname(f), exist_ok=True)
        d = {}
        for nom, tk in (("OR", "GC=F"), ("ARGENT", "SI=F")):
            x = DN.yahoo(tk, "1d", "max"); x.index = x.index.tz_convert(None).normalize()
            d[nom] = x[~x.index.duplicated(keep="last")]
        pd.DataFrame(d).to_csv(f, float_format="%.6g")
    d = pd.read_csv(f, index_col=0, parse_dates=True)
    a, b = d.OR.dropna(), d.ARGENT.dropna()
    com = a.index.intersection(b.index)
    print("\n== (b) Journalier Yahoo GC=F / SI=F : or %d jours, argent %d, communs %d (or seul %d, argent seul %d ecartes)"
          % (len(a), len(b), len(com), len(a) - len(com), len(b) - len(com)))
    a, b = a[com], b[com]
    sauts = ((np.log(a / b).diff().abs()) > 0.08).sum()
    gm, _ = B.charge("xau_m5_90k"); sm, _ = B.charge("xag_m5_90k")
    cg, cs = (gm.sp / gm.cloture).median() * 1e4, (sm.sp / sm.cloture).median() * 1e4
    print("Cout aller-retour par jambe (spread median courtier M5) : or %.2f bp, argent %.2f bp ; sauts |d log ratio| > 8 %% : %d" % (cg, cs, sauts))
    lr = np.log(a) - np.log(b)
    # journalier : decision cloture i, execution cloture i+1 (simule execute au prix d'indice i+1)
    pg, ps = a.values, b.values
    spg, sps = pg * cg / 1e4, ps * cs / 1e4
    jours = a.index; CFG, TR = {}, {}
    for W in (20, 60, 120):
        for sv in (1.5, 2.0):
            tr = simule(lr, np.ones(len(a)), pg, ps, spg, sps, W, sv, None)
            tr = [(x, v) for x, v in tr if np.isfinite(v)]
            k = "W%dj z%.1f" % (W, sv)
            t = pd.Series([v for _, v in tr], index=jours[[x for x, _ in tr]])
            TR[k] = t; CFG[k] = t.groupby(level=0).sum().reindex(jours).fillna(0)
    print("N = %d reglages ; donnees %s -> %s ; plein echantillon : %s" % (len(CFG), jours[0].date(), jours[-1].date(),
          " ; ".join("%s %+.0f/%d" % (k.replace(" ", ""), CFG[k].sum(), len(TR[k])) for k in CFG)))
    ref = np.log(a).diff() * 1e4
    r = walk_forward(CFG, TR, jours.to_period("Y"), 3, ref)
    affiche("(b)", CFG, TR, r)


if __name__ == "__main__":
    partie_a()
    partie_b()
