"""Banc : l'or contre le dollar et les taux reels US (journalier, 2003 -> aujourd'hui).
Donnees gratuites sans cle, mises en cache dans data/or_taux_jour.csv.gz :
  - Tresor US (home.treasury.gov) : taux nominal 10 ans et taux reel 10 ans (TIPS, depuis 2003) ;
  - Yahoo : or GC=F (contrat a terme continu) et indice dollar DX-Y.NYB (clotures journalieres).
Heures de publication : le taux du Tresor du jour J est releve vers 15 h 30 New York et publie le soir de J ; la
cloture de l'or (GC=F) tombe avant. Donc un signal calcule avec les donnees de J n'est utilise qu'a partir de la
CLOTURE de J+1 : la position gagne le rendement de l'or de la cloture J+1 a la cloture J+1+h (decalage de 2 jours
sur les rendements quotidiens). Meme decalage pour le dollar (cloture 17 h New York).
Regles (grille fixee d'avance, N = 14) :
  (a) signal avance : X = taux reel 10 ans ou log(dollar), variation sur k = 1, 5, 20 jours ; position sur l'or =
      -signe(variation) (taux ou dollar qui montent -> vendre l'or), decidee tous les h = 1 ou 5 jours, tenue h jours
      (12 reglages) ;
  (b) ecart qui revient : regression glissante 250 j de log(or) sur taux reel + log(dollar) ; z = residu du jour /
      ecart-type des residus de la fenetre ; z > s -> vendre l'or, z < -s -> acheter, sortie quand z repasse 0 ;
      s = 1,5 ou 2 (2 reglages).
Couts : spread median observe sur l'or H1 du courtier (aller-retour), compte a chaque changement de position.
Methode : walk-forward glissant (apprentissage 3 ans, test 1 an), meilleur reglage au t (gain par jour) sur
l'apprentissage ; series hors echantillon concatenees ; reality check de White (bootstrap stationnaire, blocs moyens
10 j, 2000 tirages) sur les N reglages ; Bonferroni rappele. References : ne rien faire (0) et acheter-et-garder
l'or a exposition egale (exposition moyenne |position| de la regle sur la meme periode).
Verdict fixe d'avance : tient = hors echantillon > 0 et (t >= 2,6 ou p < 0,05) ; presque = > 0 et (1,5 <= t < 2,6
ou p < 0,15) ; sinon ne tient pas. Usage : python3 banc_or_dollar_taux.py"""
import os, io, json, time, urllib.request, datetime as dt
import numpy as np, pandas as pd

ICI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ICI, "data", "or_taux_jour.csv.gz")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"


def lire(url):
    for essai in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30).read()
        except Exception as e:
            err = e
            time.sleep(2 * (essai + 1))
    raise RuntimeError("echec %s : %s" % (url, err))


def yahoo_cloture(tk):
    url = ("https://query2.finance.yahoo.com/v8/finance/chart/%s?interval=1d&period1=0&period2=%d"
           % (urllib.request.quote(tk), int(time.time())))
    r = json.loads(lire(url))["chart"]["result"][0]
    s = pd.Series(r["indicators"]["quote"][0]["close"], index=pd.to_datetime(r["timestamp"], unit="s").normalize())
    return s.dropna()[lambda x: ~x.index.duplicated(keep="last")]


def tresor(typ, a0):
    out = []
    for a in range(a0, dt.date.today().year + 1):
        url = ("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/"
               "%d/all?type=%s&field_tdr_date_value=%d&page&_format=csv" % (a, typ, a))
        d = pd.read_csv(io.BytesIO(lire(url)))
        col = [c for c in d.columns if c.strip().upper() == "10 YR"][0]
        out.append(pd.Series(d[col].values, index=pd.to_datetime(d["Date"], format="%m/%d/%Y")))
        time.sleep(0.3)
    return pd.concat(out).sort_index().astype(float)


def donnees():
    if os.path.exists(CACHE):
        return pd.read_csv(CACHE, index_col=0, parse_dates=True)
    d = pd.DataFrame({"or": yahoo_cloture("GC=F"), "dollar": yahoo_cloture("DX-Y.NYB")})
    d["reel10"] = tresor("daily_treasury_real_yield_curve", 2003)
    d["nom10"] = tresor("daily_treasury_yield_curve", 2000)
    d = d[d.index < pd.Timestamp(dt.date.today())]      # pas la bougie du jour, incomplete
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    d.to_csv(CACHE, float_format="%.6g")
    return d


# ---------------------------------------------------------------- outils communs
tstat = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else 0.0
creux = lambda x: (x.cumsum() - x.cumsum().cummax()).min()


def boot_idx(rng, n, b=10.0):
    """Bootstrap stationnaire (Politis-Romano) vectorise : blocs de longueur geometrique moyenne b."""
    neuf = rng.random(n) < 1 / b
    neuf[0] = True
    deb = np.flatnonzero(neuf)
    bloc = np.cumsum(neuf) - 1
    dep = rng.integers(n, size=len(deb))
    return (dep[bloc] + np.arange(n) - deb[bloc]) % n


def white(M, rng, tirages=2000):
    """p du reality check de White pour le meilleur des colonnes de M (gains par jour, contre 0)."""
    n = len(M); mu = M.mean(0); V = np.sqrt(n) * mu.max()
    Vb = np.array([np.sqrt(n) * (M[boot_idx(rng, n)].mean(0) - mu).max() for _ in range(tirages)])
    return (Vb >= V).mean(), int(mu.argmax())


def walk_forward(cfg, cles, idx, app=3):
    an = idx.year; ans = np.unique(an)
    oos, choix = [], []
    for k in range(app, len(ans)):
        a = (an >= ans[k - app]) & (an < ans[k]); t = an == ans[k]
        best = max(cles, key=lambda c: tstat(cfg[c][0][a]))
        choix.append(best); oos.append((best, t))
    return oos, choix


def verdict(tot, t, p):
    if tot > 0 and (t >= 2.6 or p < 0.05):
        return "tient"
    if tot > 0 and (t >= 1.5 or p < 0.15):
        return "presque"
    return "ne tient pas"


def main():
    t0 = time.time()
    import banc_or as B
    h1, _ = B.charge("xau_h1_50k")
    COUT = float((h1["sp"] / h1["cloture"] * 1e4).median())        # bp aller-retour
    D = donnees().ffill(limit=5).dropna()
    D = D[D.index.dayofweek < 5]
    r = np.log(D["or"]).diff().fillna(0) * 1e4                      # rendement or en bp, jour t
    idx = D.index
    X = {"reel": D["reel10"], "dollar": np.log(D["dollar"]) * 100}

    def serie(sig, h):
        """sig decide le soir de J (index J) ; decision tous les h jours ; position active du rendement J+2 a J+h+1."""
        s = pd.Series(np.where(np.arange(len(sig)) % h == 0, sig, np.nan), idx).ffill().fillna(0)
        p = s.shift(2).fillna(0)
        g = p * r - COUT / 2 * p.diff().abs().fillna(0)
        ent = ((p != 0) & (p != p.shift(1))).astype(int)
        return g, p, ent

    cfg = {}
    for nx, x in X.items():
        for k in (1, 5, 20):
            sig = -np.sign(x.diff(k)).fillna(0).values
            for h in (1, 5):
                cfg[("a", "%s k%d h%d" % (nx, k, h))] = serie(sig, h)
    # (b) regression glissante 250 j
    y, x1, x2 = np.log(D["or"]), D["reel10"], np.log(D["dollar"])
    W = 250
    m = lambda v: v.rolling(W).mean()
    my, m1, m2 = m(y), m(x1), m(x2)
    c11, c22, c12 = m(x1 * x1) - m1 ** 2, m(x2 * x2) - m2 ** 2, m(x1 * x2) - m1 * m2
    c1y, c2y, cyy = m(x1 * y) - m1 * my, m(x2 * y) - m2 * my, m(y * y) - my ** 2
    det = c11 * c22 - c12 ** 2
    b1, b2 = (c22 * c1y - c12 * c2y) / det, (c11 * c2y - c12 * c1y) / det
    e = (y - my) - b1 * (x1 - m1) - b2 * (x2 - m2)
    ssr = (cyy - b1 * c1y - b2 * c2y) * W / (W - 3)
    z = (e / np.sqrt(ssr)).fillna(0).values
    for s in (1.5, 2.0):
        st, cur = np.zeros(len(z)), 0
        for i, v in enumerate(z):
            if cur == 0 and abs(v) > s:
                cur = -np.sign(v)
            elif cur != 0 and np.sign(v) == cur:      # z repasse 0 (cote oppose a l'entree)
                cur = 0
            st[i] = cur
        cfg[("b", "ecart z>%g" % s)] = serie(st, 1)
    N = len(cfg)

    print("Or (GC=F) / dollar (DX-Y.NYB) / Tresor 10 ans reel et nominal : %s -> %s, %d jours ; cout %.2f bp aller-retour"
          % (idx[0].date(), idx[-1].date(), len(idx), COUT))
    dr, dd, dn = X["reel"].diff(), X["dollar"].diff(), D["nom10"].diff()
    print("Correlation jour (meme jour, non tradable) or/taux reel %+.2f, or/dollar %+.2f, or/nominal %+.2f ; "
          "avancee (or J+2 / variation J) : reel %+.2f, dollar %+.2f"
          % (r.corr(dr), r.corr(dd), r.corr(dn), r.shift(-2).corr(dr), r.shift(-2).corr(dd)))
    rng = np.random.default_rng(23)
    fams = {"a signal avance (12)": [c for c in cfg if c[0] == "a"], "b ecart (2)": [c for c in cfg if c[0] == "b"],
            "tout (14)": list(cfg)}
    P = {}
    for nf, cles in fams.items():
        P[nf] = white(np.column_stack([cfg[c][0].values for c in cles]), rng)
    from statistics import NormalDist
    print("N = %d reglages ; Bonferroni 5 %% bilateral sur %d : t >= %.2f ; walk-forward 3 ans -> 1 an" % (N, N, NormalDist().inv_cdf(1 - 0.025 / N)))
    print("%-21s %-17s %5s %8s %5s %6s %6s %5s %7s %7s %6s | %s" % ("famille", "reglage + choisi", "nb", "hors ech", "t",
          "p RC", "ans>0", "trad", "bp/trad", "creux", "expo", "or achat-garde expo egale : total t creux | diff t"))
    for nf, cles in fams.items():
        oos, choix = walk_forward(cfg, cles, idx)
        g = pd.concat([cfg[c][0][t] for c, t in oos]); p = pd.concat([cfg[c][1][t] for c, t in oos])
        ntr = sum(int(cfg[c][2][t].sum()) for c, t in oos)
        ga = g.groupby(g.index.year).sum()
        expo = p.abs().mean(); ref = expo * r[g.index]
        fq = pd.Series([c[1] for c in choix]).value_counts()
        pv = P[nf][0]
        print("%-21s %-17s %5s %+8.0f %+5.1f %6.3f %3d/%-2d %5d %+7.1f %+7.0f %6.2f | %+6.0f %+4.1f %+6.0f | %+6.0f %+4.1f  -> %s"
              % (nf, fq.index[0], "%d/%d" % (fq.iloc[0], len(choix)), g.sum(), tstat(g), pv, (ga > 0).sum(), len(ga), ntr,
                 g.sum() / max(ntr, 1), creux(g), expo, ref.sum(), tstat(ref), creux(ref), (g - ref).sum(), tstat(g - ref),
                 verdict(g.sum(), tstat(g), pv)))
        if nf.startswith("tout"):
            print("  periode hors echantillon %s -> %s ; choix par annee : %s" % (g.index[0].date(), g.index[-1].date(),
                  " ".join("%d:%s" % (y, c[1].replace(" ", "")) for y, c in zip(np.unique(g.index.year), choix))))
            print("  or achat-garde pleine exposition meme periode : %+.0f bp (t %+.1f, creux %+.0f)"
                  % (r[g.index].sum(), tstat(r[g.index]), creux(r[g.index])))
    print("Reality check : meilleur des 14 sur tout l'echantillon = %s (%+.0f bp, t %+.1f)"
          % (list(cfg)[P["tout (14)"][1]][1], cfg[list(cfg)[P["tout (14)"][1]]][0].sum(), tstat(cfg[list(cfg)[P["tout (14)"][1]]][0])))
    print("Tous les reglages, echantillon entier (bp total / t / trades) :")
    lig = ["%s %+.0f/%+.1f/%d" % (c[1], v[0].sum(), tstat(v[0]), v[2].sum()) for c, v in cfg.items()]
    for i in range(0, len(lig), 4):
        print("  " + " ; ".join(lig[i:i + 4]))
    # controle horaire (hors grille) : la cloture Yahoo de GC=F = reglement 13 h 30 New York, AVANT le releve du
    # Tresor (15 h 30). Un decalage d'un seul jour (non tradable) melange donc 2 h d'avenir. Version tradable : or H1
    # du courtier, entree a la cloture de la bougie serveur 01 h (~19 h New York, serveur = New York + 7 h), tenue 24 h.
    c = h1["cloture"]; c1 = c[c.index.hour == 1]; c1.index = c1.index.normalize(); c1 = c1[~c1.index.duplicated()]
    r1 = np.log(c1).diff().shift(-1) * 1e4                              # du jour serveur D (19 h NY veille) a D+1
    lig = []
    for nx, x in (("reel", X["reel"]), ("dollar", X["dollar"])):
        sg = -np.sign(x.diff())
        dec = pd.Series(sg.values, idx + pd.Timedelta(days=1)).reindex(c1.index, method="ffill")  # derniere valeur < D
        g1 = (dec * r1 - COUT / 2 * dec.diff().abs()).dropna()
        gl1 = (-np.sign(x.diff()).shift(1) * r).loc[g1.index[0]:]
        lig.append("%s k1 h1 : decale 1 j Yahoo (non tradable) %+.0f bp t %+.1f ; courtier 19 h NY %+.0f bp t %+.1f"
                   % (nx, gl1.sum(), tstat(gl1), g1.sum(), tstat(g1)))
    print("Controle horaire %s -> %s : %s" % (c1.index[0].date(), c1.index[-1].date(), " | ".join(lig)))
    print("(%.0f s)" % (time.time() - t0))


if __name__ == "__main__":
    main()
