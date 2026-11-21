"""Banc AF : momentum croise entre actifs (PRIORITES 17/11, B), journalier long (Yahoo, cache data/momentum_jour.csv.gz).
Panier du labo (celui de banc_prime) : S&P 500, Nasdaq 100, DAX, Nikkei, FTSE, or, argent, BTC, ETH (crypto quand
elle existe). Regle : a chaque fin de {semaine, mois}, classer les actifs par rendement sur L mois (21 j par mois),
avec ou sans saut du dernier mois ; acheter les K plus forts SEULEMENT si leur propre rendement est > 0 (sinon la
part reste liquide, rendement 0) ; poids a risque egal : min(10 %/vol 60 j, 1) / K. Au comptant (sans levier ni
financement ; dividendes touches, frais 0,2 %/an, comme banc_prime). Decision a la cloture J, execution J+1 (w.shift(2)).
Couts : moitie du spread median du courtier par unite echangee (bougies M5/M1 du courtier : or, argent, Nasdaq,
S&P, DAX, BTC, ETH), sinon 2 bp aller-retour (Nikkei, FTSE).
Grille fixee d'avance, N = 36 : rythme {semaine, mois} x K {1, 2, 3} x periode {1, 3, 6, 12 mois sans saut ;
6-1, 12-1 mois avec saut du dernier mois} (saut omis pour 1 et 3 mois : il viderait ou amputerait la fenetre).
Reference : le panier achete seulement a risque egal (banc_prime, « comptant toujours achete » : +7,6 %/an
2016-2026, pire baisse -12 %) et ne rien faire. Walk-forward glissant : apprentissage 3 ans, test 1 an ; reglage au
meilleur t (rendement net journalier) ; chaque annee de test mise a la volatilite de la reference sur l'apprentissage.
Reality check de White (bootstrap stationnaire, blocs moyens 5 j, 2000 tirages) des 36 contre la reference, series
mises a la meme volatilite que la reference sur tout l'echantillon. Verdict : tient = difference hors echantillon > 0
et (t >= 2,6 ou p < 0,05) ; presque = > 0 et (1,5 <= t < 2,6 ou p < 0,15) ; sinon ne tient pas.
Usage : python3 banc_momentum_croise.py"""
import os, itertools, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import donnees, banc_tendance as T

ICI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ICI, "data", "momentum_jour.csv.gz")
ACTIFS = ["SP500", "NASDAQ", "DAX", "NIKKEI", "FTSE", "OR", "ARGENT", "BTC", "ETH"]
COURTIER = {"OR": "xau_m5_90k", "ARGENT": "xag_m5_90k", "NASDAQ": "nas_m5_90k", "SP500": "sp_m5_90k",
            "DAX": "ger_m1_90k", "BTC": "btc_m5_90k", "ETH": "eth_m5_90k"}


def prix():
    if not os.path.exists(CACHE):
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        j = {}
        for a in ACTIFS:
            s = donnees.yahoo(donnees.UNIVERS[a][0], "1d", "max")
            s.index = s.index.tz_convert(None).normalize()
            j[a] = s[~s.index.duplicated(keep="last")]
        pd.DataFrame(j).sort_index().to_csv(CACHE, float_format="%.6g")
    p = pd.read_csv(CACHE, index_col=0, parse_dates=True)
    return p[p.index.dayofweek < 5].ffill(limit=5)


def couts_aller_retour():
    rt = {a: 2.0 for a in ACTIFS}
    for a, ident in COURTIER.items():
        d = pd.read_csv(os.path.join(ICI, "mt5", "donnees", ident + ".csv.gz"))
        dec = max(len(("%.5f" % v).rstrip("0").split(".")[1]) for v in d["cloture"].iloc[:2000])
        rt[a] = float((d["spread_points"] * 10.0 ** (-dec) / d["cloture"] * 1e4).median())
    return pd.Series(rt)


def net(r, w, rt):
    tenu = w.shift(2).fillna(0)
    brut = (tenu * r.fillna(0)).sum(axis=1)
    cout = ((w.shift(1) - w.shift(2)).abs().fillna(0) * rt / 2 / 1e4).sum(axis=1)
    fin = sum(tenu[a] * (0.002 - T.DIVIDENDE.get(a, 0.0)) for a in w) / 252
    return brut - cout - fin


def poids_momentum(px, r, vol, rythme, K, L, saut):
    sk = 21 if saut else 0
    mom = px.shift(sk) / px.shift(sk + 21 * L) - 1
    fins = px.index.to_series().groupby(px.index.to_period("W" if rythme == "semaine" else "M")).last()
    m = mom.loc[fins.values]
    rang = m.rank(axis=1, ascending=False, method="first")
    sel = (rang <= K) & (m > 0)
    w = (sel * (T.RISQUE / vol.loc[fins.values]).clip(upper=1.0) / K).fillna(0)
    return w.reindex(px.index).ffill().fillna(0)


tst = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else 0.0
rng = np.random.default_rng(17)


def an_pire(x):
    c = (1 + x).cumprod()
    return 100 * (c.iloc[-1] ** (252 / len(x)) - 1), 100 * (c / c.cummax() - 1).min()


if __name__ == "__main__":
    p = prix()
    r = p.pct_change(fill_method=None)
    r = r.mask(r.abs() > 0.5, 0.0)["2000":]
    px = (1 + r.fillna(0)).cumprod().where(r.notna())
    vol = r.ewm(span=60, min_periods=40).std() * np.sqrt(252)
    rt = couts_aller_retour()
    # reference : banc_prime « comptant toujours achete » (risque egal sur les actifs disponibles)
    w0 = (T.RISQUE / vol).clip(upper=1.0)
    w0 = w0.div(w0.notna().sum(axis=1).clip(lower=1), axis=0).fillna(0)
    ref = net(r, w0, rt)["2001":]
    GR = [(ry, K, L, s) for ry in ("semaine", "mois") for K in (1, 2, 3) for L, s in ((1, 0), (3, 0), (6, 0), (12, 0), (6, 1), (12, 1))]
    S, W = {}, {}
    for g in GR:
        W[g] = poids_momentum(px, r, vol, *g)
        S[g] = net(r, W[g], rt)["2001":]
    idx = ref.index; an = idx.year
    print("Donnees %s -> %s (%d jours ouvres) ; debut par actif : %s" % (idx[0].date(), idx[-1].date(), len(idx),
          ", ".join("%s %d" % (a, p[a].first_valid_index().year) for a in ACTIFS)))
    print("Couts aller-retour (bp, spread median du courtier, sinon 2) : " + ", ".join("%s %.1f" % (a, v) for a, v in rt.items()))
    print("N = %d reglages ; walk-forward apprentissage 3 ans / test 1 an ; Bonferroni : t >= 2,6" % len(GR))
    for (a, b) in (("2001", "2015"), ("2016", "2026")):
        print("Reference %s-%s : %+.1f %%/an, pire baisse %+.0f %% (Sharpe %.2f)" % (a, b, *an_pire(ref[a:b]), tst(ref[a:b]) / np.sqrt(len(ref[a:b]) / 252)))
    # ---------------------------------------------------------------- walk-forward
    oos, choix, nent = [], [], 0
    for y in range(2004, an.max() + 1):
        app, te = (an >= y - 3) & (an < y), an == y
        best = max(GR, key=lambda g: tst(S[g][app]))
        k = ref[app].std() / S[best][app].std()
        oos.append(S[best][te] * k); choix.append(best)
        ww = W[best].loc[idx[te]]
        nent += int(((ww > 0) & (ww.shift(1).fillna(W[best].loc[idx[app]].iloc[-1]) == 0)).values.sum())
    o = pd.concat(oos); r0 = ref[o.index]; dd = o - r0
    oy, ry = o.groupby(o.index.year).sum(), r0.groupby(r0.index.year).sum()
    fq = pd.Series(["%s K%d %dm%s" % (g[0], g[1], g[2], "-1" if g[3] else "") for g in choix]).value_counts()
    print("Reglages choisis (%d annees de test %d-%d) : %s" % (len(choix), o.index[0].year, o.index[-1].year,
          ", ".join("%s x%d" % (n, c) for n, c in fq.items())))
    print("%-30s %8s %7s %7s %6s %9s %7s" % ("", "%/an", "pire", "t", "an>0", "trades", "bp/tr"))
    for nom, x in (("hors echantillon (vol. egale)", o), ("reference, memes jours", r0)):
        a_, pi = an_pire(x)
        print("%-30s %+8.1f %+7.0f %+7.1f %3d/%-2d %9s %7s" % (nom, a_, pi, tst(x), (x.groupby(x.index.year).sum() > 0).sum(), len(oy),
              nent if x is o else "-", "%+.0f" % (1e4 * o.sum() / nent) if x is o else "-"))
    for (a, b) in (("2004", "2015"), ("2016", "2026")):
        print("  %s-%s : momentum %+.1f %%/an (pire %+.0f %%) ; reference %+.1f %%/an (pire %+.0f %%) ; difference t %+.1f" % (
            a, b, *an_pire(o[a:b]), *an_pire(r0[a:b]), tst(dd[a:b])))
    print("Difference hors echantillon : %+.2f %%/an (t %+.1f) ; annees ou le momentum bat la reference : %d/%d" % (
        100 * dd.mean() * 252, tst(dd), (oy > ry).sum(), len(oy)))
    # ---------------------------------------------------------------- reality check
    M = np.column_stack([S[g] * ref.std() / S[g].std() for g in GR]); Dm = M - ref.values[:, None]
    n = len(Dm); mu = Dm.mean(0); V = np.sqrt(n) * mu.max(); Vb = []
    for _ in range(2000):
        neuf = rng.random(n) < 0.2; neuf[0] = True
        bl = np.cumsum(neuf) - 1; deb = np.flatnonzero(neuf)
        ii = (rng.integers(n, size=len(deb))[bl] + np.arange(n) - deb[bl]) % n
        Vb.append(np.sqrt(n) * (Dm[ii].mean(0) - mu).max())
    prc = (np.array(Vb) >= V).mean(); gb = GR[int(mu.argmax())]
    xb = pd.Series(M[:, int(mu.argmax())], idx)
    print("Reality check des %d contre la reference : meilleur = %s K%d %dm%s (%+.1f %%/an, pire %+.0f %% ; ref %+.1f %%/an), p = %.3f" % (
        len(GR), gb[0], gb[1], gb[2], "-1" if gb[3] else "", *an_pire(xb), an_pire(ref)[0], prc))
    print("Reglages qui battent la reference sur tout l'echantillon (vol. egale) : %d/%d ; mediane %+.2f %%/an" % (
        (mu > 0).sum(), len(GR), 100 * 252 * np.median(mu)))
    v = "tient" if dd.sum() > 0 and (tst(dd) >= 2.6 or prc < 0.05) else (
        "presque" if dd.sum() > 0 and (tst(dd) >= 1.5 or prc < 0.15) else "ne tient pas")
    print("Verdict (fixe d'avance) : %s ; contre ne rien faire : hors echantillon %+.1f %%/an (t %+.1f)" % (v, an_pire(o)[0], tst(o)))
