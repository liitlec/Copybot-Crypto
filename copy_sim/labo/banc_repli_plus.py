"""Banc S : comment tirer plus du repli d'indices (PRIORITES 12/11 22 h 40), sans le casser.
Bougies jour Yahoo 2000-2026 (ouverture, haut, bas, cloture). Portefeuille simule JOUR PAR JOUR (positions qui se
chevauchent comprises), couts : 2 bp par trade + financement CFD (taux 3 mois + 2,5 %) par nuit tenue.
Grille (54 reglages) : seuil RSI 2 j (5, 10, 15) x sortie au-dessus de la moyenne (3, 5, 7 j) x duree max (5, 10 j)
x stop (2 ATR, 3 ATR, aucun). Univers : A = 4 indices du robot (S&P, Nasdaq, DAX, Dow) ; B = 8 indices (A + Nikkei,
CAC, EuroStoxx 50, Russell 2000, FTSE exclu) ; or et argent juges a part.
Avance glissante : tous les 3 ans, on prend le reglage au meilleur Sharpe sur TOUT le passe, et on le juge sur les
3 ans suivants. Taille : part fixe du compte par position, ou risque fixe (perte au stop de 2 ATR = x % du compte).
Usage : python3 banc_repli_plus.py"""
import os, json, time, itertools, urllib.request
import warnings
import numpy as np, pandas as pd
warnings.simplefilter("ignore")
from donnees import UA
from banc_blockrange import rsi2

ICI = os.path.dirname(os.path.abspath(__file__))
TICKERS = {"SP500": "^GSPC", "NASDAQ": "^NDX", "DAX": "^GDAXI", "DOW": "^DJI", "NIKKEI": "^N225", "CAC": "^FCHI",
           "EU50": "^STOXX50E", "RUSSELL": "^RUT", "FTSE": "^FTSE", "OR": "GC=F", "ARGENT": "SI=F"}
A = ["SP500", "NASDAQ", "DAX", "DOW"]
B = A + ["NIKKEI", "CAC", "EU50", "RUSSELL"]


def ohlc(nom):
    f = os.path.join(ICI, "data", "ohlc_%s.csv.gz" % nom)
    if os.path.exists(f):
        return pd.read_csv(f, index_col=0, parse_dates=True)
    url = "https://query2.finance.yahoo.com/v8/finance/chart/%s?interval=1d&period1=946684800&period2=%d" % (
        urllib.request.quote(TICKERS[nom]), int(time.time()))
    for essai in range(4):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30))["chart"]["result"][0]
            break
        except Exception:
            time.sleep(3 * (essai + 1))
    q = r["indicators"]["quote"][0]
    d = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")},
                     index=pd.to_datetime(r["timestamp"], unit="s").normalize()).dropna()
    d = d[(d.open > 0) & (d.high >= d.low)]
    d = d[~d.index.duplicated()]
    os.makedirs(os.path.dirname(f), exist_ok=True)
    d.to_csv(f)
    return d


def simule(d, taux, seuil=10, mm=5, jmax=10, stop_k=2.0, filtre=200):
    """Rend (rendement journalier d'une position de 1, exposition 0/1, liste des trades (date, net, risque au stop))."""
    c = d.close
    r = rsi2(c).values
    mf = c.rolling(filtre).mean().values
    ms = c.rolling(mm).mean().values
    tr = pd.concat([d.high - d.low, (d.high - c.shift()).abs(), (d.low - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(20).mean().values
    o, l, v = d.open.values, d.low.values, c.values
    n = len(d)
    jour, expo, trades = np.zeros(n), np.zeros(n), []
    fin = (np.nan_to_num(taux.reindex(d.index).ffill().values, nan=2.0) / 100 + 0.025) / 360
    nuits = np.r_[1, np.diff(d.index.values).astype("timedelta64[D]").astype(int)]
    i = max(filtre, 25)
    while i < n - 2:
        if r[i] < seuil and v[i] > mf[i]:
            e = o[i + 1]
            stop = e - stop_k * atr[i] if stop_k else -1.0
            j, prec, tot = i + 1, e, 0.0
            while True:
                expo[j] = 1
                if l[j] <= stop:
                    x = min(stop, o[j]); jour[j] += x / prec - 1; tot = x / e - 1; break
                if j >= n - 1:
                    jour[j] += v[j] / prec - 1; tot = v[j] / e - 1; break
                jour[j] += v[j] / prec - 1
                prec = v[j]
                if v[j] > ms[j] or j - i >= jmax:
                    j += 1
                    jour[j] += o[j] / prec - 1 - fin[j] * nuits[j]; tot = o[j] / e - 1; break
                j += 1
                jour[j] -= fin[j] * nuits[j]
            jour[i + 1] -= 0.0002
            cout = 0.0002 + fin[i + 2:j + 1].dot(nuits[i + 2:j + 1]) if j > i + 1 else 0.0002
            trades.append((d.index[i + 1], tot - cout, 2 * atr[i] / e))
            i = j
        i += 1
    return pd.Series(jour, d.index), pd.Series(expo, d.index), trades


def portefeuille(D, taux, noms, taille="fixe", **k):
    """Rendement journalier du compte pour 1 unite de taille par position. 'fixe' : 100 % du compte par position ;
    'risque' : taille telle que le stop de 2 ATR coute 2 % du compte (donc ~100 % du compte pour un ATR de 1 %)."""
    js, ts = [], []
    for s in noms:
        j, e, t = simule(D[s], taux, **k)
        if taille == "risque" and t:
            w = pd.Series({a: 0.02 / max(c, 1e-4) for a, _, c in t}).reindex(j.index).ffill().fillna(1.0).clip(upper=3)
            j = j * w
        js.append(j); ts += [(a, b) for a, b, _ in t]
    p = pd.concat(js, axis=1).fillna(0.0).sum(axis=1)
    return p[p.index >= "2001"], pd.DataFrame(ts, columns=["date", "net"]).sort_values("date")


def stats(p, f=1.0):
    q = p * f
    cap = (1 + q).cumprod()
    ans = len(q) / 252
    return ((cap.iloc[-1] ** (1 / ans) - 1) * 100, (cap / cap.cummax() - 1).min() * 100,
            q.mean() / q.std() * np.sqrt(252) if q.std() > 0 else 0.0)


def ligne(nom, p, t, f):
    g, dd, sh = stats(p, f)
    ans = len(p) / 252
    m, e = t.net.mean(), t.net.std() / np.sqrt(max(len(t), 1))
    return "  %-34s %5.0f tr/an  %+5.1f bp/trade (t=%+.1f)  a %3.0f %% par position : %+5.1f %%/an, pire baisse %5.1f %%, Sharpe %.2f" % (
        nom, len(t) / ans, m * 1e4, m / e, f * 100, g, dd, sh)


if __name__ == "__main__":
    taux = pd.read_csv(os.path.join(ICI, "data", "jour.csv.gz"), index_col=0, parse_dates=True)["TAUX_US_3M"]
    D = {s: ohlc(s) for s in TICKERS}
    print("Donnees :", ", ".join("%s %s" % (s, D[s].index[0].year) for s in D))
    coupe = lambda p, t, a, b: (p[(p.index >= a) & (p.index < b)], t[(t.date >= a) & (t.date < b)])

    print("\n1) Regle de base (RSI<10, sortie MM5, 10 j, stop 2 ATR) par marche, 2016-2026")
    for s in list(TICKERS):
        p, t = portefeuille(D, taux, [s]); p, t = coupe(p, t, "2016", "2027")
        print(ligne(s, p, t, 1.0))

    print("\n2) Base, par univers")
    for nom, U in (("A : 4 indices du robot", A), ("B : 8 indices", B), ("or + argent", ["OR", "ARGENT"])):
        p, t = portefeuille(D, taux, U)
        for per, a, b in (("2001-2015", "2001", "2016"), ("2016-2026", "2016", "2027")):
            print(ligne(nom + " " + per, *coupe(p, t, a, b), 0.5))

    print("\n3) Grille de 54 reglages sur l'univers B, avance glissante (choix au meilleur Sharpe sur tout le passe)")
    grille = list(itertools.product((5, 10, 15), (3, 5, 7), (5, 10), (2.0, 3.0, 0)))
    R = {}
    for g in grille:
        R[g] = portefeuille(D, taux, B, seuil=g[0], mm=g[1], jmax=g[2], stop_k=g[3])
    base = (10, 5, 10, 2.0)
    sh = lambda g, a, b: stats(coupe(*R[g], a, b)[0])[2]
    morceaux, choix = [], []
    for an in range(2010, 2027, 3):
        a, b = str(an), str(an + 3)
        m = max(grille, key=lambda g: sh(g, "2001", a))
        choix.append((an, m))
        morceaux.append(coupe(*R[m], a, b))
    pg = pd.concat([x[0] for x in morceaux]); tg = pd.concat([x[1] for x in morceaux])
    print("  choix successifs (seuil, MM sortie, jours, stop) :", "; ".join("%d: %s" % c for c in choix))
    print(ligne("avance glissante 2010-2026", pg, tg, 0.5))
    print(ligne("base, meme periode", *coupe(*R[base], "2010", "2027"), 0.5))
    tous = sorted(sh(g, "2016", "2027") for g in grille)
    print("  Sharpe 2016-2026 des 54 reglages : min %.2f, mediane %.2f, max %.2f ; base %.2f ; reglages positifs : %d/54"
          % (tous[0], tous[27], tous[-1], sh(base, "2016", "2027"), sum(x > 0 for x in tous)))
    print("  effet de chaque choix (Sharpe moyen 2001-2015 -> 2016-2026) :")
    for k, nomk in enumerate(("seuil RSI", "MM de sortie", "jours max", "stop ATR")):
        vals = sorted(set(g[k] for g in grille))
        print("    %-13s " % nomk + " | ".join("%s : %.2f -> %.2f" % (x, np.mean([sh(g, "2001", "2016") for g in grille if g[k] == x]),
                                                                    np.mean([sh(g, "2016", "2027") for g in grille if g[k] == x])) for x in vals))

    print("\n4) Filtres et taille (univers B, 2016-2026 ; regles decidees d'apres 2001-2015)")
    for nom, kw in (("base B", {}), ("filtre 100 j", {"filtre": 100}),
                    ("taille au risque (2 %% au stop)", {"taille": "risque"})):
        kw2 = dict(kw); taille = kw2.pop("taille", "fixe")
        if kw2.get("filtre") == 1:
            kw2["filtre"] = 2
        p, t = portefeuille(D, taux, B, taille=taille, **kw2)
        print(ligne(nom + " 2001-2015", *coupe(p, t, "2001", "2016"), 0.5))
        print(ligne(nom + " 2016-2026", *coupe(p, t, "2016", "2027"), 0.5))

    print("\n5) Tableau base / amelioree et ce qu'il faudrait pour 1 %% par jour (2016-2026, tirage de blocs de 20 jours, 2 000 annees)")
    rng = np.random.default_rng(7)
    for nom, (p, t) in (("BASE : 4 indices, regle du robot", coupe(*portefeuille(D, taux, A), "2016", "2027")),
                        ("PLUS LARGE : 8 indices, meme regle", coupe(*R[base], "2016", "2027"))):
        print(" ", nom, "- %.0f trades par an, expose %.0f %% des jours" % (len(t) / (len(p) / 252), 100 * (p != 0).mean()))
        x = p.values
        for f in (0.2, 0.5, 1.0, 2.0, 5.0, 0.01 / x.mean()):
            g, dd, _ = stats(p, f)
            ruine, med = 0, []
            for _ in range(2000):
                deb = rng.integers(0, len(x) - 20, 13)
                y = np.concatenate([x[a:a + 20] for a in deb])[:252] * f
                cap = np.cumprod(1 + np.maximum(y, -0.99))
                ruine += cap.min() < 0.5; med.append(cap[-1] - 1)
            print("    %5.0f %% du compte par position : %+7.1f %%/an (%.3f %%/jour), pire baisse %6.1f %%, annee mediane %+7.0f %%, chances de perdre 50 %% dans l'annee : %4.1f %%"
                  % (f * 100, g, x.mean() * f * 100, dd, np.median(med) * 100, ruine / 20))
