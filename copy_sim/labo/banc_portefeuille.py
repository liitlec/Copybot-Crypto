"""Banc AQ : portefeuille de la famille « rebonds d'indices » (PRIORITES 17/11 17 h, point 4).
Plan fixe d'avance :
- Pieces : chaque regle qui TIENT (ou PRESQUE) est transformee en serie journaliere « rendement d'un notionnel de 1 »
  (0 les jours sans position). Pieces de base, recalculees ici sur Yahoo journalier long (cache donnees/indices_jour.csv.gz) :
    repli_<indice> : RSI 2 j < 10 au-dessus de la moyenne 200 j, achat cloture J (approx. de l'ouverture J+1),
                     sortie cloture > moyenne 5 j ou 10 jours ; S&P, Nasdaq 100, Dow, Russell 2000 ;
    rebond_nas     : grande journee du Nasdaq 100 (amplitude > 1,5 x mediane 20 j) -> sens inverse, ouverture -> cloture J+1
                     (jours a ouverture connue seulement) ;
    vix_sp         : VIX > moyenne 20 j + 2 ecarts-types -> achat S&P cloture J, sortie cloture J+5 (« presque »).
  + les trades hors echantillon des bancs des points 1-3 (donnees/rebonds_*.csv, hors fichiers *_tout), repartis
  regulierement sur les jours de tenue.
  Couts : 1,5 bp aller-retour (indices) + financement de nuit (taux 3 mois ^IRX + 2,5 %)/360 par nuit tenue.
- Poids : Kelly multi-pieces f = inverse(Sigma) x mu (jours), estime sur TOUT le passe disponible (fenetre croissante,
  5 ans au moins), applique a l'annee suivante (walk-forward annuel) ; poids negatifs mis a 0 (pas de vente d'une regle) ;
  levier global plafonne a 50 (garde-fou). Mises : 0,1 / 0,15 / 0,25 / 0,5 / 1 Kelly (le Kelly estime est enorme :
  20 a 35 fois le capital, car chaque piece n'est active que ~12 % du temps).
- Rendu : rendement par an compose, pire baisse, annees negatives, sur la periode hors echantillon ; et le meme
  calcul pour chaque piece seule a 0,5 Kelly, et pour le panier acheteur des 4 indices a risque egal (reference).
Usage : python3 banc_portefeuille.py"""
import os, glob, json, time, urllib.request, datetime as dt
import numpy as np, pandas as pd

ICI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ICI, "donnees", "indices_jour.csv.gz")
TK = {"SP": "^GSPC", "NAS": "^NDX", "DJ": "^DJI", "RUT": "^RUT", "VIX": "^VIX", "IRX": "^IRX"}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
COUT = 1.5e-4
LEV_MAX = 50.0     # garde-fou seulement (le Kelly estime demande 20 a 35 fois le capital)


def yahoo_ohlc(tk):
    url = ("https://query2.finance.yahoo.com/v8/finance/chart/%s?interval=1d&period1=0&period2=%d"
           % (urllib.request.quote(tk), int(time.time())))
    for k in range(4):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30))
            r = r["chart"]["result"][0]
            q = r["indicators"]["quote"][0]
            d = pd.DataFrame({c: q[c] for c in ("open", "high", "low", "close")},
                             index=pd.to_datetime(r["timestamp"], unit="s").normalize())
            return d.dropna(subset=["close"])[lambda x: ~x.index.duplicated(keep="last")]
        except Exception as e:
            err = e; time.sleep(2 * (k + 1))
    raise RuntimeError("echec %s : %s" % (tk, err))


def donnees():
    if os.path.exists(CACHE):
        d = pd.read_csv(CACHE, index_col=0, parse_dates=True)
    else:
        d = pd.concat({n: yahoo_ohlc(t) for n, t in TK.items()}, axis=1, sort=True)
        d.columns = ["%s_%s" % c for c in d.columns]
        d = d[(d.index >= "1988-01-01") & (d.index < pd.Timestamp(dt.date.today()))]
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        d.to_csv(CACHE, float_format="%.6g")
    out = {n: d[[c for c in d.columns if c.startswith(n + "_")]].rename(columns=lambda c: c.split("_")[1]).dropna(subset=["close"])
           for n in TK}
    for n in ("SP", "NAS", "DJ", "RUT"):
        o = out[n]
        o.loc[(o["open"] - o["close"].shift(1)).abs() < 1e-9, "open"] = np.nan
        o.loc[(o["high"] - o["low"]).abs() < 1e-9, ["high", "low"]] = np.nan
    return out


def rsi2(c):
    dc = c.diff(); up, dn = dc.clip(lower=0), (-dc).clip(lower=0)
    rs = up.ewm(alpha=0.5, adjust=False).mean() / dn.ewm(alpha=0.5, adjust=False).mean()
    return 100 - 100 / (1 + rs)


def nuit(D, idx):
    irx = D["IRX"]["close"].reindex(idx).ffill().fillna(3.0)
    return (irx / 100 + 0.025) / 360 * pd.Series(idx, index=idx).diff().dt.days.fillna(1).clip(1, 4)


def piece_repli(D, n):
    o = D[n]; c = o["close"]; idx = c.index
    r, ma200, ma5 = rsi2(c), c.rolling(200).mean(), c.rolling(5).mean()
    ret = c.pct_change().fillna(0)
    fin = nuit(D, idx)
    x = pd.Series(0.0, index=idx); trades = []
    i, N = 200, len(idx)
    while i < N - 1:
        if r.iloc[i] < 10 and c.iloc[i] > ma200.iloc[i]:
            j = i + 1
            while j < N and not (c.iloc[j] > ma5.iloc[j] or j - i >= 10):
                j += 1
            j = min(j, N - 1)
            x.iloc[i + 1:j + 1] = ret.iloc[i + 1:j + 1] - fin.iloc[i + 1:j + 1]
            x.iloc[i + 1] -= COUT
            trades.append((idx[i], idx[j], float(np.prod(1 + x.iloc[i + 1:j + 1]) - 1)))
            i = j + 1
        else:
            i += 1
    return x, trades


def piece_rebond(D):
    o = D["NAS"]; c = o["close"]
    amp = (o["high"] - o["low"]) / c.shift(1)
    med = amp.shift(1).rolling(20).median()
    s = -np.sign(c - c.shift(1)).where(amp > 1.5 * med, 0).shift(1)        # position du jour J+1
    r = (o["close"] - o["open"]) / o["open"]
    x = (s * r - COUT * s.abs()).where(o["open"].notna(), 0).fillna(0)
    return x, [(d, d, v) for d, v in x[x != 0].items()]


def piece_vix(D):
    v = D["VIX"]["close"]; c = D["SP"]["close"]; idx = c.index
    v = v.reindex(idx).ffill()
    sig = v > v.rolling(20).mean() + 2 * v.rolling(20).std()
    ret = c.pct_change().fillna(0); fin = nuit(D, idx)
    x = pd.Series(0.0, index=idx); trades = []
    i, N = 25, len(idx)
    while i < N - 6:
        if sig.iloc[i]:
            x.iloc[i + 1:i + 6] = ret.iloc[i + 1:i + 6] - fin.iloc[i + 1:i + 6]
            x.iloc[i + 1] -= COUT
            trades.append((idx[i], idx[i + 5], float(np.prod(1 + x.iloc[i + 1:i + 6]) - 1)))
            i += 6
        else:
            i += 1
    return x, trades


def pieces_externes(idx):
    out = {}
    for f in sorted(glob.glob(os.path.join(ICI, "donnees", "rebonds_*.csv"))):
        if f.endswith("_tout.csv"):
            continue
        T = pd.read_csv(f, parse_dates=["entree", "sortie"])
        for (regle, marche), g in T.groupby(["regle", "marche"]):
            x = pd.Series(0.0, index=idx)
            for _, t in g.iterrows():
                jours = idx[(idx > t.entree) & (idx <= t.sortie)]
                if len(jours) == 0:
                    jours = idx[idx >= t.sortie][:1]
                if len(jours):
                    x.loc[jours] += (1 + t.r) ** (1 / len(jours)) - 1
            out["%s:%s:%s" % (os.path.basename(f)[8:-4], regle, marche)] = x
    return out


def kelly_wf(X, mult, debut_ans=5):
    """Poids Kelly estimes sur le passe (fenetre croissante), refaits chaque annee. Rend la serie du portefeuille."""
    ans = sorted(set(X.index.year))
    an0 = X.index[0].year + debut_ans
    R, W = [], {}
    for a in ans:
        if a < an0:
            continue
        P = X[X.index.year < a]
        vieux = [c for c in P.columns if (P[c] != 0).any() and P.index[(P[c] != 0).values.argmax()].year <= a - 4]
        P = P[vieux]                                  # une piece n'entre qu'avec 3 ans d'historique au moins
        if P.shape[1] == 0:
            continue
        mu, S = P.mean().values, P.cov().values
        w = np.linalg.solve(S + 1e-10 * np.eye(len(mu)), mu) * mult
        w = np.clip(w, 0, None)
        if w.sum() > LEV_MAX:
            w *= LEV_MAX / w.sum()
        W[a] = dict(zip(P.columns, np.round(w, 2)))
        R.append((X.loc[X.index.year == a, P.columns] * w).sum(axis=1))
    return (pd.concat(R) if R else pd.Series(dtype=float)), W


def bilan(r):
    if len(r) == 0:
        return dict(an=np.nan, creux=np.nan, ans_neg=np.nan, n_ans=0)
    eq = (1 + r.clip(lower=-1.0)).cumprod()
    if (eq <= 0).any():
        eq = eq.where(eq.cummin() > 0, 0.0)
    ans = len(r) / 252
    an = eq.iloc[-1] ** (1 / ans) - 1 if eq.iloc[-1] > 0 else -1.0
    creux = (eq / eq.cummax() - 1).min()
    pa = eq.groupby(eq.index.year).last().pct_change().fillna(-1.0)
    pa.iloc[0] = eq.groupby(eq.index.year).last().iloc[0] - 1
    return dict(an=an, creux=creux, ans_neg=int((pa < 0).sum()), n_ans=len(pa), debut=r.index[0].year)


if __name__ == "__main__":
    D = donnees()
    idx = D["SP"].index[D["SP"].index >= "1990-01-01"]
    P, TR = {}, {}
    for n in ("SP", "NAS", "DJ", "RUT"):
        x, t = piece_repli(D, n); P["repli_" + n] = x.reindex(idx).fillna(0); TR["repli_" + n] = t
    x, t = piece_rebond(D); P["rebond_nas"] = x.reindex(idx).fillna(0); TR["rebond_nas"] = t
    x, t = piece_vix(D); P["vix_sp"] = x.reindex(idx).fillna(0); TR["vix_sp"] = t
    P.update(pieces_externes(idx))
    X = pd.DataFrame(P).fillna(0)
    tst = lambda v: np.mean(v) / np.std(v) * np.sqrt(len(v)) if len(v) > 2 else 0
    print("Pieces (rendement d'un notionnel de 1 ; trades = jours actifs pour les pieces externes) :")
    for k in X.columns:
        a = X[k][X[k] != 0]
        nb = len(TR.get(k, [])) or len(a)
        print("  %-48s %5d trades/jours  depuis %s  moyenne/jour actif %+6.1f bp  t %.1f  part du temps %4.1f %%" % (
            k, nb, a.index[0].date() if len(a) else "-", 1e4 * a.mean() if len(a) else 0, tst(a.values), 100 * len(a) / len(X)))
    C = X.loc[:, X.abs().sum() > 0]
    cor = C[(C != 0).any(axis=1)].corr()
    print("\nCorrelations journalieres (jours ou au moins une piece est active) :")
    print(cor.round(2).to_string())
    pd.set_option("display.width", 250)
    lignes = []
    ref = D["SP"]["close"].pct_change().reindex(idx).fillna(0)
    TIENT = ["repli_SP", "repli_NAS", "repli_DJ", "repli_RUT", "rebond_nas", "grande_journee:gj_fige:sp",
             "calendrier:cal_fomc:DAX"]
    PRESQUE = ["vix_sp", "grande_journee:gj_fige:rut", "calendrier:cal_ferie:RUSSELL", "calendrier:cal_ferie:DAX",
               "calendrier:cal_fomc:SP500", "calendrier:cal_fomc:NAS100", "calendrier:cal_fomc:RUSSELL"]
    TIENT = [c for c in TIENT if c in X.columns]; PRESQUE = [c for c in PRESQUE if c in X.columns]
    jeux = {"A. ce qui tient (repli 4 indices, contre-pied Nasdaq et S&P, FOMC DAX)": TIENT,
            "B. A + les « presque » (VIX, Russell, veilles de ferie, FOMC US)": TIENT + PRESQUE,
            "base ancienne (repli 4 indices + contre-pied Nasdaq)": [c for c in X.columns if c.startswith("repli_") or c == "rebond_nas"]}
    for k in TIENT + PRESQUE:
        jeux["seule : " + k] = [k]
    SERIES = {}
    for nom, cols in jeux.items():
        for mult in ((0.1, 0.15, 0.25, 0.5, 1.0) if not nom.startswith("seule") else (0.15,)):
            r, W = kelly_wf(X[cols], mult)
            SERIES[(nom, mult)] = r
            levier = np.mean([sum(w.values()) for w in W.values()]) if W else np.nan
            b = bilan(r); b8 = bilan(r[r.index.year >= 2008])
            lignes.append(dict(portefeuille=nom, kelly=mult, levier_moyen=round(levier, 1), **b,
                               an_2008=b8["an"], creux_2008=b8["creux"]))
    b = bilan(ref[ref.index.year >= 1995]); b8 = bilan(ref[ref.index.year >= 2008])
    lignes.append(dict(portefeuille="reference : S&P 500 achete et garde (sans levier)", kelly=np.nan, levier_moyen=1.0, **b,
                       an_2008=b8["an"], creux_2008=b8["creux"]))
    T = pd.DataFrame(lignes)
    for c in ("an", "creux", "an_2008", "creux_2008"):
        T[c] = (100 * T[c]).round(1)
    print("\nWalk-forward (poids estimes sur le passe, refaits chaque annee ; % par an composes, pire baisse en % ;"
          " colonnes _2008 = depuis 2008, toutes les pieces disponibles) :")
    print(T.to_string(index=False))
    T.to_csv(os.path.join(ICI, "donnees", "portefeuille_bilan.csv"), index=False)

    # Objectif de Baptiste : +10 % PAR MOIS (= +214 % par an compose). Quel levier faudrait-il au portefeuille A ?
    # On prend la serie A a 0,1 Kelly (poids walk-forward) et on la multiplie par m ; Monte-Carlo 12 mois par blocs de
    # 20 jours tires dans 2008-2026 ; ruine = perte de 80 %.
    rA = SERIES[(list(jeux)[0], 0.1)]
    rA = rA[rA.index.year >= 2008]
    levA = T.levier_moyen.iloc[0]
    rng = np.random.default_rng(10)
    n = len(rA); v = rA.values
    print("\nViser +10 %% par mois avec le portefeuille A (levier moyen a 0,1 Kelly = %.1f) :" % levA)
    print("  multiple  levier  an_histo  creux_histo  mediane_12m  P(>= +214 % en 12 m)  P(ruine -80 % en 12 m)")
    rows = []
    for m in (1, 2, 3, 5, 8, 12, 20):
        b = bilan(rA * m)
        fins, ruine = [], 0
        for _ in range(4000):
            idx_ = np.concatenate([np.arange(s0, s0 + 20) % n for s0 in rng.integers(n, size=13)])[:252]
            eq = np.cumprod(1 + np.clip(v[idx_] * m, -1, None))
            ruine += eq.min() <= 0.2
            fins.append(eq[-1])
        fins = np.array(fins)
        rows.append((m, m * levA, b["an"], b["creux"], np.median(fins) - 1, (fins >= 3.14).mean(), ruine / 4000))
        print("  %5.0f x  %6.1f  %+7.1f %%  %+8.1f %%  %+9.1f %%  %14.0f %%  %18.0f %%" % (
            m, m * levA, 100 * b["an"], 100 * b["creux"], 100 * (np.median(fins) - 1), 100 * (fins >= 3.14).mean(), 100 * ruine / 4000))
    pd.DataFrame(rows, columns=["multiple", "levier", "an", "creux", "mediane_12m", "p_10pc_mois", "p_ruine"]).to_csv(
        os.path.join(ICI, "donnees", "portefeuille_10pc_mois.csv"), index=False)
    r, W = kelly_wf(X[TIENT], 0.1)
    print("\nPoids 0,1 Kelly de la derniere annee (A) :", {k: float(v) for k, v in W[max(W)].items()} if W else {})
