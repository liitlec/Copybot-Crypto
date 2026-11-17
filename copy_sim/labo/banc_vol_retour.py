"""Banc : la volatilite qui revient a la moyenne (sans options), or et indices US, journalier long.
Donnees : Yahoo journalier OHLC (or GC=F depuis 2000, S&P 500 ^GSPC, Nasdaq 100 ^NDX et VIX ^VIX depuis 1990),
cache data/vol_jour.csv.gz (les vieilles bougies dont l'ouverture = cloture de la veille ont une ouverture
inconnue : pas d'entree ces jours-la, soit S&P avant ~2008 et Nasdaq avant ~1999) ; bougies du courtier (or D1/H1/M15, Nasdaq et S&P D1) pour la prevision de
l'amplitude et un controle. Couts aller-retour = spread median observe chez le courtier (or H1, S&P M5, Nasdaq M5).
Grille fixee d'avance (N = 36, trois sous-pistes jugees chacune par son walk-forward et son reality check) :
  (a) journee agitee : amplitude du jour J = (haut - bas) / cloture J-1 ; si > m x mediane des 20 jours precedents
      (m = 1,5 / 2 / 3), le lendemain : entree a l'ouverture J+1, sortie a la cloture J+1, CONTRE le mouvement du
      jour J (cloture J - cloture J-1) ou DANS son sens ; 3 marches x 3 m x 2 sens = 18 reglages ; reference : rien.
      Mesure a part : l'amplitude du lendemain est-elle previsible (correlation des log(amplitude / mediane 20)) ?
  (b) mise inversement proportionnelle a la volatilite : position acheteuse = k / ecart-type des rendements des n
      derniers jours (n = 5 ou 20), connu a la cloture J-1, appliquee au rendement de J+1 (plafond 3 fois la mise
      fixe) ; k fixe sur l'apprentissage pour que le risque (ecart-type) egale celui de la mise fixe ; cout a chaque
      reajustement ; 3 marches x 2 n = 6 reglages ; jugee sur l'ECART a la mise fixe (achat-garde, mise 1).
  (c) VIX haut : si la cloture du VIX en J > 25, > 30 ou > moyenne 20 j + 2 ecarts-types, achat de l'indice a
      l'ouverture J+1, sortie a la cloture J+h (h = 5 ou 10), pas de chevauchement ; 2 indices x 3 seuils x 2 h = 12
      reglages ; references : rien et achat-garde de l'indice a exposition egale.
Methode : walk-forward glissant (apprentissage 3 ans, test 1 an), meilleur reglage au t (gain par jour) sur
l'apprentissage ; reality check de White (bootstrap stationnaire, blocs moyens 10 j, 2000 tirages) ; Bonferroni.
Verdict fixe d'avance : tient = hors echantillon > 0 et (t >= 2,6 ou p < 0,05) ; presque = > 0 et (1,5 <= t < 2,6
ou p < 0,15) ; sinon ne tient pas. Usage : python3 banc_vol_retour.py"""
import os, json, time, urllib.request, datetime as dt, warnings
warnings.filterwarnings("ignore")
from statistics import NormalDist
import numpy as np, pandas as pd
import banc_or as B
from banc_or_dollar_taux import lire, tstat, creux, white, walk_forward, verdict

ICI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ICI, "data", "vol_jour.csv.gz")
TK = {"OR": "GC=F", "SP": "^GSPC", "NAS": "^NDX", "VIX": "^VIX"}


def yahoo_ohlc(tk):
    url = ("https://query2.finance.yahoo.com/v8/finance/chart/%s?interval=1d&period1=0&period2=%d"
           % (urllib.request.quote(tk), int(time.time())))
    r = json.loads(lire(url))["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    d = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")},
                     index=pd.to_datetime(r["timestamp"], unit="s").normalize())
    return d.dropna()[lambda x: ~x.index.duplicated(keep="last")]


def donnees():
    if os.path.exists(CACHE):
        d = pd.read_csv(CACHE, index_col=0, parse_dates=True)
    else:
        d = pd.concat({n: yahoo_ohlc(t) for n, t in TK.items()}, axis=1, sort=True)
        d.columns = ["%s_%s" % c for c in d.columns]
        d = d[(d.index >= "1990-01-01") & (d.index < pd.Timestamp(dt.date.today()))]
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        d.to_csv(CACHE, float_format="%.6g")
    out = {n: d[[c for c in d.columns if c.startswith(n + "_")]].rename(columns=lambda c: c.split("_")[1]).dropna()
           for n in TK}
    for n in ("OR", "SP", "NAS"):     # vieilles bougies Yahoo : ouverture = cloture de la veille -> ouverture inconnue
        o = out[n]
        o.loc[(o["open"] - o["close"].shift(1)).abs() < 1e-9, "open"] = np.nan
    return out


def cout():
    out = {}
    for n, f in (("OR", "xau_h1_50k"), ("SP", "sp_m5_90k"), ("NAS", "nas_m5_90k")):
        d, _ = B.charge(f)
        out[n] = float((d["sp"] / d["cloture"] * 1e4).median())
    return out


def amplitude(d):
    a = (d["high"] - d["low"]) / d["close"].shift(1)
    a = a.where((d["high"] > d["low"]) & (a < 0.25))                 # vieilles bougies sans haut/bas -> ecartees
    med = a.rolling(20, min_periods=15).median().shift(1)               # 20 jours AVANT J
    return a, med


def prev_amp(a, med):
    """Correlation des log(amplitude/mediane) J et J+1, et rapport J+1 apres un jour > 2 x mediane / sinon."""
    x = np.log(a / med); y = np.log(a.shift(-1) / med)
    ok = x.notna() & y.notna()
    gros = (a / med > 2) & ok
    return x[ok].corr(y[ok]), np.exp(y[gros].median()), np.exp(y[~gros & ok].median()), int(gros.sum())


def ligne_wf(nom, cfg, idx, P, ref=None, base=None):
    """Walk-forward ; base = serie a soustraire (piste b) ; ref = reference a exposition egale (piste c)."""
    oos, choix = walk_forward(cfg, list(cfg), idx)
    g = pd.concat([cfg[c][0][t] for c, t in oos]); p = pd.concat([cfg[c][1][t] for c, t in oos])
    ntr = sum(int(cfg[c][2][t].sum()) for c, t in oos)
    ga = g.groupby(g.index.year).sum(); fq = pd.Series([c for c in choix]).value_counts()
    pv = P[0]
    print("%-12s %-18s %5s %+8.0f %+5.1f %6.3f %3d/%-2d %5d %+7.1f %+7.0f  -> %s" % (
        nom, fq.index[0], "%d/%d" % (fq.iloc[0], len(choix)), g.sum(), tstat(g), pv, (ga > 0).sum(), len(ga), ntr,
        g.sum() / max(ntr, 1), creux(g), verdict(g.sum(), tstat(g), pv)))
    print("   choix par annee : " + " ".join("%d:%s" % (y, c.replace(" ", "")) for y, c in zip(np.unique(g.index.year), choix)))
    return g, p, oos


def main():
    t0 = time.time()
    Y, C = donnees(), cout()
    idx = Y["SP"].index.union(Y["OR"].index)
    idx = idx[idx.dayofweek < 5]
    print("Yahoo jour : or %s -> %s, S&P/Nasdaq/VIX %s -> %s ; couts aller-retour (spread median courtier) : %s"
          % (Y["OR"].index[0].date(), Y["OR"].index[-1].date(), Y["SP"].index[0].date(), Y["SP"].index[-1].date(),
             ", ".join("%s %.2f bp" % kv for kv in C.items())))
    rng = np.random.default_rng(31)
    Nt = 36

    # ------------------------------------------------ (a) journee agitee
    print("(a) Amplitude du lendemain previsible ? corr log(ampl/med20) J -> J+1 ; mediane J+1/med20 apres jour > 2x / sinon :")
    lig = []
    for n in ("OR", "SP", "NAS"):
        a, med = amplitude(Y[n]); c, r1, r2, k = prev_amp(a, med)
        lig.append("%s %+.2f, %.2f/%.2f (%d j)" % (n, c, r1, r2, k))
    for f, per in (("xau_d1_5k", "D"), ("xau_h1_50k", "H"), ("xau_m15_50k", "Q")):
        d, _ = B.charge(f)
        a = ((d["haut"] - d["bas"]) / d["cloture"].shift(1)).where(d["haut"] > d["bas"])
        if per == "D":
            med = a.rolling(20).median().shift(1)
        else:                                                           # meme heure (quart d'heure), 20 jours avant
            cle = d.index.hour * 4 + d.index.minute // 15
            med = a.groupby(cle).transform(lambda s: s.rolling(20).median().shift(1))
        c, r1, r2, k = prev_amp(a, med)
        lig.append("courtier or %s %+.2f, %.2f/%.2f" % (f.split("_")[1], c, r1, r2))
    print("   " + " ; ".join(lig[:3])); print("   " + " ; ".join(lig[3:]))
    cfg = {}
    for n in ("OR", "SP", "NAS"):
        d = Y[n].reindex(idx); a, med = amplitude(Y[n]); a, med = a.reindex(idx), med.reindex(idx)
        sens = np.sign(d["close"] - d["close"].shift(1))
        jour = (d["close"] - d["open"]) / d["open"] * 1e4                # ouverture -> cloture de J+1
        for m in (1.5, 2, 3):
            ev = (a > m * med).shift(1).fillna(False).astype(bool) & jour.notna()
            for nom, sg in (("contre", -1), ("sens", 1)):
                pos = (sg * sens.shift(1)).where(ev, 0).fillna(0)
                g = (pos * jour.fillna(0) - C[n] * pos.abs())
                cfg["%s %g %s" % (n, m, nom)] = (g, pos, (pos != 0).astype(int))
    Pa = white(np.column_stack([v[0].values for v in cfg.values()]), rng)
    print("%-12s %-18s %5s %8s %5s %6s %6s %5s %7s %7s" % ("sous-piste", "reglage + choisi", "nb", "hors ech", "t", "p RC",
          "ans>0", "trad", "bp/trad", "creux"))
    ga, _, oa = ligne_wf("(a) N=18", cfg, idx, Pa)
    best = list(cfg)[Pa[1]]
    tous = sorted(((v[0].sum(), k, tstat(v[0]), int(v[2].sum())) for k, v in cfg.items()), reverse=True)
    print("   echantillon entier, 3 meilleurs : " + " ; ".join("%s %+.0f bp t %+.1f %d tr" % (k, s, t, n) for s, k, t, n in tous[:3])
          + " ; 3 pires : " + " ; ".join("%s %+.0f t %+.1f" % (k, s, t) for s, k, t, n in tous[-3:]))
    # controle sur les bougies D1 du courtier (spread reel = cout fixe ci-dessus), meilleur reglage de tout l'echantillon
    n, m, nom = best.split(); m = float(m)
    d, _ = B.charge({"OR": "xau_d1_5k", "SP": "sp_d1_5k", "NAS": "nas_d1_5k"}[n])
    a = (d["haut"] - d["bas"]) / d["cloture"].shift(1); med = a.rolling(20).median().shift(1)
    ev = (a > m * med).shift(1).fillna(False).astype(bool)
    pos = ((-1 if nom == "contre" else 1) * np.sign(d["cloture"].diff()).shift(1)).where(ev, 0)
    g = (pos * (d["cloture"] - d["ouverture"]) / d["ouverture"] * 1e4 - C[n] * pos.abs()).dropna()
    print("   controle courtier D1 (%s, %s -> %s) : %+.0f bp, t %+.1f, %d trades"
          % (best, d.index[0].date(), d.index[-1].date(), g.sum(), tstat(g), int(pos.abs().sum())))

    # ------------------------------------------------ (b) mise inverse a la volatilite (ecart a la mise fixe)
    cfgb, base = {}, {}
    an = idx.year
    for n in ("OR", "SP", "NAS"):
        c = Y[n]["close"].reindex(idx)
        r = (np.log(c).diff() * 1e4).fillna(0).where(c.notna() & c.shift(1).notna(), 0)
        base[n] = r
        for k in (5, 20):
            sd = r.where(r != 0).rolling(k, min_periods=k).std()
            w = (1 / sd).shift(2)                                       # connu a la cloture J-1, rendement de J+1
            cfgb["%s n%d" % (n, k)] = (r, w)
    # facteur k : fixe par annee de test sur les 3 annees precedentes (risque egal a la mise fixe)
    for key, (r, w) in list(cfgb.items()):
        f = pd.Series(np.nan, idx)
        for y in np.unique(an):
            a3 = (an >= y - 3) & (an < y) & (r != 0)
            if (w[a3] * r[a3]).std() > 0:
                f[an == y] = r[a3].std() / (w[a3] * r[a3]).std()
        pos = (f * w).clip(upper=3).fillna(0).where(r != 0, np.nan).ffill().fillna(0)
        g = pos * r - C[key.split()[0]] / 2 * pos.diff().abs().fillna(0)
        cfgb[key] = ((g - r).where(f.notna(), 0), pos, (pos.diff().abs() > 0.05).astype(int), g)
    Pb = white(np.column_stack([v[0].values for v in cfgb.values()]), rng)
    gb, pb, ob = ligne_wf("(b) N=6 ecart", {k: v[:3] for k, v in cfgb.items()}, idx, Pb)
    gs = pd.concat([cfgb[c][3][t] for c, t in ob]); bs = pd.concat([base[c.split()[0]][t] for c, t in ob])
    print("   hors ech. : mise variable %+.0f bp (t %+.1f, creux %+.0f, rendement/creux %.2f, ecart-type jour %.0f) ; "
          "mise fixe %+.0f bp (t %+.1f, creux %+.0f, rendement/creux %.2f, ecart-type %.0f)"
          % (gs.sum(), tstat(gs), creux(gs), -gs.sum() / creux(gs), gs.std(), bs.sum(), tstat(bs), creux(bs),
             -bs.sum() / creux(bs), bs.std()))
    print("   echantillon entier (depuis 1993) par reglage, rendement/creux variable contre fixe : " + " ; ".join(
        "%s %.2f/%.2f" % (k, -v[3][an >= 1993].sum() / creux(v[3][an >= 1993]),
                          -base[k.split()[0]][an >= 1993].sum() / creux(base[k.split()[0]][an >= 1993])) for k, v in cfgb.items()))

    # ------------------------------------------------ (c) VIX haut -> acheter l'indice
    vix = Y["VIX"]["close"].reindex(idx)
    mu, sdv = vix.rolling(20).mean().shift(1), vix.rolling(20).std().shift(1)
    cond = {"vix>25": vix > 25, "vix>30": vix > 30, "vix>m20+2s": vix > mu + 2 * sdv}
    cfgc, refc = {}, {}
    for n in ("SP", "NAS"):
        d = Y[n].reindex(idx); o, c = d["open"].values, d["close"].values
        rcc = (np.log(d["close"]).diff() * 1e4).fillna(0).values
        for cn, cv in cond.items():
            s = cv.fillna(False).values
            for h in (5, 10):
                g, pos, ent = np.zeros(len(idx)), np.zeros(len(idx)), np.zeros(len(idx))
                i = 0
                while i < len(idx) - h:
                    if s[i] and not np.isnan(o[i + 1]):
                        e, x = i + 1, i + h
                        g[e] = np.log(c[e] / o[e]) * 1e4 - C[n]; pos[e] = 1; ent[e] = 1
                        for j in range(e + 1, x + 1):
                            g[j] = rcc[j]; pos[j] = 1
                        i = x + 1
                    else:
                        i += 1
                cfgc["%s %s h%d" % (n, cn, h)] = (pd.Series(g, idx), pd.Series(pos, idx), pd.Series(ent, idx))
        refc[n] = pd.Series(rcc, idx)
    Pc = white(np.column_stack([v[0].values for v in cfgc.values()]), rng)
    gc, pc, oc = ligne_wf("(c) N=12", cfgc, idx, Pc)
    ref = pd.concat([refc[c.split()[0]][t] * cfgc[c][1][t].mean() for c, t in oc])
    Pc2 = white(np.column_stack([v[0].values - refc[k.split()[0]].values * v[1].mean() for k, v in cfgc.items()]), rng)
    print("   achat-garde indice a exposition egale (%.0f %% du temps) : %+.0f bp (t %+.1f, creux %+.0f) ; ecart regle - ref %+.0f bp, t %+.1f, p RC contre ref %.3f"
          % (100 * pc.mean(), ref.sum(), tstat(ref), creux(ref), (gc - ref).sum(), tstat(gc - ref), Pc2[0]))
    tous = sorted(((v[0].sum(), k, tstat(v[0]), int(v[2].sum())) for k, v in cfgc.items()), reverse=True)
    print("   echantillon entier, 4 meilleurs : " + " ; ".join("%s %+.0f bp t %+.1f %d tr" % (k, s, t, n) for s, k, t, n in tous[:4]))
    print("Bonferroni 5 %% bilateral : N=18 t >= %.2f ; N=6 t >= %.2f ; N=12 t >= %.2f ; tout le banc N=%d t >= %.2f ; "
          "periode hors echantillon %s -> %s (%.0f s)" % tuple([NormalDist().inv_cdf(1 - .025 / k) for k in (18, 6, 12)] +
          [Nt, NormalDist().inv_cdf(1 - .025 / Nt), ga.index[0].date(), ga.index[-1].date(), time.time() - t0]))


if __name__ == "__main__":
    main()
