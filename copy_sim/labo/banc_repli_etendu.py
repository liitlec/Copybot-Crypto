"""Banc X : le repli d'indices en plus gros (plus de marches, portefeuille, sorties, seuils), reglage FIGE d'avance.
Regle de base (celle du labo, bougies jour) : signal a la cloture du jour i si RSI 2 j (Wilder) < 10 et cloture > moyenne
200 j -> achat a l'ouverture de i+1 ; sortie a l'ouverture du lendemain de la premiere cloture au-dessus de la moyenne
5 j, ou apres 10 jours ; pas de stop ; une position par marche, pas de nouvel achat le jour d'une sortie.
Ouvertures Yahoo fausses (= cloture de la veille : S&P et Russell avant 2007, FTSE presque toujours) : on execute alors
a la cloture de ce jour-la (un jour de retard, prudent, jamais d'avance sur le futur).
Couts : aller-retour 2 bp indices (spread courtier observe 0,2-0,6 bp, ouverture plus chere), or 3 bp, argent 5 bp,
BTC 3 bp ; portage CFD 6 %/an du notionnel par nuit calendaire tenue (week-ends compris).
Donnees : Yahoo jour 1998-2026 (ouverture, haut, bas, cloture ; cache data/repli_*.csv.gz), trades 2000-2026.
(a) 12 marches, regle telle quelle, deux moities ; verdict par marche fixe d'avance : tient = deux moities > 0 et
    t >= 2,6 (Bonferroni 12 marches) ; presque = deux moities > 0 et t >= 1,5.
(b) portefeuille des marches « tient » ou « presque » (choix sur tout l'echantillon : optimiste), et version honnete
    a selection glissante (au 1er janvier, marche pris si ses trades passes : >= 20, moyenne > 0, t >= 1,5) ;
    f = {20, 50, 100 %} du compte par trade, plafond d'exposition {100, 200 %} (trade saute si plafond atteint).
(c)+(d) N = 18 reglages sur les 4 indices americains (univers fixe d'avance) : sorties {moyenne 5 j, RSI2 > 50,
    RSI2 > 70, 5 jours, 1re cloture en hausse} x stop {aucun, -3 %, -5 %} (entree RSI2 < 10), et entrees {RSI2 < 5,
    < 10, < 15, 3 baisses de suite} (sortie moyenne 5 j). Walk-forward annuel : apprentissage 3 ans, test 1 an, choix
    au meilleur t du gain par jour ; reality check de White (bootstrap stationnaire, blocs 5 j, 2000 tirages) sur les 18.
(e) H4 : deja refute (banc W, banc_repli_h4.py), non refait. Usage : python3 banc_repli_etendu.py"""
import os, json, time, urllib.request, warnings
import numpy as np, pandas as pd
from donnees import UA
warnings.simplefilter("ignore")

ICI = os.path.dirname(os.path.abspath(__file__))
TK = {"SP500": "^GSPC", "NASDAQ": "^NDX", "DOW": "^DJI", "RUSSELL": "^RUT", "DAX": "^GDAXI", "EU50": "^STOXX50E",
      "CAC": "^FCHI", "FTSE": "^FTSE", "NIKKEI": "^N225", "OR": "GC=F", "ARGENT": "SI=F", "BTC": "BTC-USD"}
COUT = {"OR": 3e-4, "ARGENT": 5e-4, "BTC": 3e-4}          # sinon 2 bp
PORTAGE = 0.06 / 365
US4 = ["SP500", "NASDAQ", "DOW", "RUSSELL"]
DEBUT = pd.Timestamp("2000-01-01")


def ohlc(nom):
    f = os.path.join(ICI, "data", "repli_%s.csv.gz" % nom)
    if not os.path.exists(f):
        url = "https://query2.finance.yahoo.com/v8/finance/chart/%s?interval=1d&period1=883612800&period2=%d" % (
            urllib.request.quote(TK[nom]), int(time.time()))
        for essai in range(4):
            try:
                r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30))
                break
            except Exception:
                time.sleep(3 * (essai + 1))
        r = r["chart"]["result"][0]; q = r["indicators"]["quote"][0]
        d = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")},
                         index=pd.to_datetime(r["timestamp"], unit="s").normalize()).dropna()
        d = d[(d.open > 0) & (d.high >= d.low)]
        d = d[~d.index.duplicated(keep="last")]
        os.makedirs(os.path.dirname(f), exist_ok=True)
        d.to_csv(f, float_format="%.6g")
    return pd.read_csv(f, index_col=0, parse_dates=True)


def rsi2(c):
    d = c.diff()
    h = d.clip(lower=0).ewm(alpha=0.5, adjust=False).mean(); b = (-d).clip(lower=0).ewm(alpha=0.5, adjust=False).mean()
    return (100 * h / (h + b)).fillna(50)


def prepare(nom):
    d = ohlc(nom)
    c = d.close
    x = dict(dt=d.index, o=d.open.values, h=d.high.values, l=d.low.values, c=c.values, r=rsi2(c).values,
             m200=c.rolling(200).mean().values, m5=c.rolling(5).mean().values,
             ok=(d.open != c.shift()).values, cout=COUT.get(nom, 2e-4))
    x["bas3"] = ((c < c.shift()) & (c.shift() < c.shift(2)) & (c.shift(2) < c.shift(3))).values
    return x


def simule(x, entree="rsi10", sortie="m5", stop=0.0, jmax=10):
    """Trades : liste de (date d'entree, rsi, net, chemin [(date, rendement du jour net de portage)])."""
    dt, o, h, l, c, r, m200, m5, ok = (x[k] for k in ("dt", "o", "h", "l", "c", "r", "m200", "m5", "ok"))
    sig = {"rsi5": r < 5, "rsi10": r < 10, "rsi15": r < 15, "bas3": x["bas3"]}[entree] & (c > m200)
    if sortie == "j5":
        jmax = 5
    n, out, i = len(c), [], np.searchsorted(dt, DEBUT)
    i = max(i, 200)
    while i < n - 2:
        if not sig[i]:
            i += 1; continue
        e = i + 1
        pe = o[e] if ok[e] else c[e]
        st = pe * (1 - stop) if stop else -1.0
        chem, prec, j, px, fin = [], pe, e, None, None
        while True:
            debut_j = o[j] if (j > e and ok[j]) else (pe if j == e else c[j - 1])
            if st > 0 and not (j == e and not ok[e]) and l[j] <= st:   # stop touche dans la journee
                px = min(st, debut_j) if j > e else st
                chem.append((dt[j], px / prec - 1)); fin = j; break
            chem.append((dt[j], c[j] / prec - 1)); prec = c[j]
            k = j - e + 1
            fsort = {"m5": c[j] > m5[j], "r50": r[j] > 50, "r70": r[j] > 70, "j5": False,
                     "hausse": c[j] > c[j - 1]}[sortie]
            if fsort or k >= jmax or j + 1 >= n:
                if j + 1 >= n:
                    px = c[j]; fin = j; break
                j += 1
                px = o[j] if ok[j] else c[j]
                chem.append((dt[j], px / prec - 1)); fin = j; break
            j += 1
        # portage par nuit calendaire, cout a l'entree
        dates = [z[0] for z in chem]
        nuits = np.r_[0, np.diff(np.array(dates, dtype="datetime64[D]")).astype(int)]
        chem = [(dd, rr - PORTAGE * nn) for (dd, rr), nn in zip(chem, nuits)]
        chem[0] = (chem[0][0], chem[0][1] - x["cout"])
        net = px / pe - 1 - x["cout"] - PORTAGE * nuits.sum()
        out.append((dt[e], r[i], net, chem))
        i = fin                     # pas de nouvel achat le jour de la sortie : signal au plus tot a sa cloture
    return out


tst = lambda v: v.mean() / v.std(ddof=1) * np.sqrt(len(v)) if len(v) > 2 and v.std() > 0 else 0.0
X = {n: prepare(n) for n in TK}
JOURS = pd.DatetimeIndex(sorted(set().union(*[set(X[n]["dt"][X[n]["dt"] >= DEBUT]) for n in TK]))).normalize()
JOURS = JOURS[JOURS.dayofweek < 5]
print("Yahoo jour, trades %s -> %s ; couts 2 bp indices / 3 or / 5 argent / 3 BTC + portage 6 %%/an par nuit" % (
    DEBUT.date(), JOURS[-1].date()))

# ------------------------------------------------------------------ (a) marche par marche
print("(a) regle figee, par marche | trades/an  bp/trade  t | 1re moitie bp (t) | 2e moitie bp (t) | gagn | verdict")
BASE, VERD = {}, {}
for n in TK:
    T = simule(X[n]); BASE[n] = T
    d0, g = np.array([t[0] for t in T]), np.array([t[2] for t in T])
    deb, fin = max(DEBUT, X[n]["dt"][200]), X[n]["dt"][-1]
    mil = deb + (fin - deb) / 2
    a, b = g[d0 < mil], g[d0 >= mil]
    t = tst(g)
    v = "tient" if a.mean() > 0 and b.mean() > 0 and t >= 2.6 else (
        "presque" if a.mean() > 0 and b.mean() > 0 and t >= 1.5 else "non")
    VERD[n] = v
    print("  %-8s %s-%s %4d %5.1f/an %+6.1f %+5.1f | %+6.1f (%+4.1f) | %+6.1f (%+4.1f) | %3.0f%% | %s" % (
        n, deb.year, fin.year, len(g), len(g) / ((fin - deb).days / 365.25), 1e4 * g.mean(), t, 1e4 * a.mean(),
        tst(a), 1e4 * b.mean(), tst(b), 100 * (g > 0).mean(), v))
GARDE = [n for n in TK if VERD[n] != "non"]


# ------------------------------------------------------------------ (b) portefeuille
def portef(trades, f, cap):
    ev = sorted(trades, key=lambda t: (t[0], t[1]))
    par_jour = {}
    for t in ev:
        par_jour.setdefault(t[0], []).append(t)
    ouvert, eq, pic, dd, pris, ser = [], 1.0, 1.0, 0.0, 0, []
    for D in JOURS:
        for t in par_jour.get(D, []):
            if (len(ouvert) + 1) * f <= cap + 1e-9:
                ouvert.append([dict(t[3]), t[3][-1][0]]); pris += 1
        R = sum(f * p[0].get(D, 0.0) for p in ouvert)
        ouvert = [p for p in ouvert if p[1] > D]
        eq *= 1 + R; pic = max(pic, eq); dd = min(dd, eq / pic - 1); ser.append(R)
    ans = (JOURS[-1] - JOURS[0]).days / 365.25
    return pris / ans, 100 * (eq ** (1 / ans) - 1), 100 * dd


def glissant():
    """Trades des marches retenus au 1er janvier d'apres leur seul passe (>= 20 trades, moyenne > 0, t >= 1,5)."""
    out = []
    for y in range(2003, JOURS[-1].year + 1):
        for n in TK:
            p = np.array([t[2] for t in BASE[n] if t[3][-1][0] < pd.Timestamp(y, 1, 1)])
            if len(p) >= 20 and p.mean() > 0 and tst(p) >= 1.5:
                out += [t for t in BASE[n] if t[0].year == y]
    return out


UNIV = {"retenus (choix a posteriori)": sum((BASE[n] for n in GARDE), []), "selection glissante 2003+": glissant(),
        "4 indices US": sum((BASE[n] for n in US4), [])}
print("(b) retenus : %s. Cellule = trades/an, gain %%/an compose, pire baisse %%" % ", ".join(GARDE))
print("  f/trade plafond | " + " | ".join("%-27s" % k for k in UNIV))
for f in (0.2, 0.5, 1.0):
    for cap in (1.0, 2.0):
        print("  %4.0f%%   %4.0f%%   | " % (100 * f, 100 * cap) + " | ".join(
            "%5.0f tr  %+5.1f%%  %6.1f%%     " % portef(T, f, cap) for T in UNIV.values()))
bh = pd.concat([pd.Series(X[n]["c"], X[n]["dt"]).pct_change() for n in US4], axis=1).loc[DEBUT:].fillna(0).mean(1)
eqb = (1 + bh).cumprod()
print("  reference achat-conserve 4 indices US (sans cout ni portage) : %+.1f %%/an, pire baisse %.0f %% ; ne rien faire : 0" % (
    100 * (eqb.iloc[-1] ** (365.25 / (bh.index[-1] - bh.index[0]).days) - 1), 100 * (eqb / eqb.cummax() - 1).min()))

# ------------------------------------------------------------------ (c)+(d) grille, walk-forward, reality check
CFG = {}
for s_ in ("m5", "r50", "r70", "j5", "hausse"):
    for st in (0.0, 0.03, 0.05):
        CFG[("c", "rsi10", s_, st)] = None
for e_ in ("rsi5", "rsi15", "bas3"):
    CFG[("d", e_, "m5", 0.0)] = None
NT, SER = {}, {}
for k in CFG:
    T = sum((simule(X[n], k[1], k[2], k[3]) for n in US4), [])
    z = pd.Series(0.0, JOURS)
    for t in T:
        for dd, rr in t[3]:
            if dd in z.index:
                z[dd] += rr
    SER[k], NT[k] = z, pd.Series([t[2] for t in T], [t[0] for t in T]).sort_index()
N = len(CFG)
nom = lambda k: "%s %s stop %s" % (k[1], k[2], "%g%%" % (100 * k[3]) if k[3] else "aucun")
B0 = ("c", "rsi10", "m5", 0.0)
an = JOURS.year
print("(c)+(d) N = %d reglages, 4 indices US, %d jours. bp/trade sur 2000-2026 :" % (N, len(JOURS)))
print("  " + " ".join("%s:%+.0f" % (nom(k).replace(" stop ", "/").replace("aucun", "0"), 1e4 * NT[k].mean()) for k in list(CFG)[:8]))
print("  " + " ".join("%s:%+.0f" % (nom(k).replace(" stop ", "/").replace("aucun", "0"), 1e4 * NT[k].mean()) for k in list(CFG)[8:]))
print("  WF annuel (3 ans -> 1 an, %d-%d) | choix le plus frequent | hors ech %% t | ans>0 | creux | trades bp/tr | moins base (t)" % (2003, an.max()))
for p in ("c", "d"):
    cles = [k for k in CFG if k[0] == p] + ([B0] if p == "d" else [])
    o, ntr, choix = [], [], []
    for y in range(2003, an.max() + 1):
        app, te = (an >= y - 3) & (an < y), an == y
        b = max(cles, key=lambda k: tst(SER[k][app].values))
        choix.append(nom(b)); o.append(SER[b][te]); ntr.append(NT[b][NT[b].index.year == y])
    o, ntr = pd.concat(o), pd.concat(ntr)
    base = SER[B0][o.index]; dif = o - base
    ya = o.groupby(o.index.year).sum()
    fq = pd.Series(choix).value_counts()
    print("  (%s) %-30s %2d/%d | %+6.1f %+4.1f | %2d/%2d | %5.1f | %4d %+5.1f | %+5.1f (%+.1f)" % (
        p, fq.index[0][:30], fq.iloc[0], len(choix), 100 * o.sum(), tst(o.values), (ya > 0).sum(), len(ya),
        100 * (o.cumsum() - o.cumsum().cummax()).min(), len(ntr), 1e4 * ntr.mean(), 100 * dif.sum(), tst(dif.values)))
bb = SER[B0][an >= 2003]; nb = NT[B0][NT[B0].index.year >= 2003]
print("  base meme periode : %+6.1f %% (t %+.1f), %d trades, %+.1f bp/trade, creux %.1f %%" % (
    100 * bb.sum(), tst(bb.values), len(nb), 1e4 * nb.mean(), 100 * (bb.cumsum() - bb.cumsum().cummax()).min()))

rng = np.random.default_rng(17)
M = np.column_stack([SER[k].values for k in CFG]); n = len(M)
def boot(n, b=5.0):
    neuf = rng.random(n) < 1 / b; neuf[0] = True
    dep = rng.integers(n, size=n)
    g = np.cumsum(neuf) - 1; st = dep[neuf][g]
    pos = np.arange(n) - np.flatnonzero(neuf)[g]
    return (st + pos) % n
for lab, R in (("ne rien faire", np.zeros(n)), ("regle de base", SER[B0].values)):
    D = M - R[:, None]; mu = D.mean(0); V = np.sqrt(n) * mu.max()
    Vb = np.array([np.sqrt(n) * (D[boot(n)].mean(0) - mu).max() for _ in range(2000)])
    kb = list(CFG)[int(mu.argmax())]
    print("  reality check contre %s : meilleur = %s (t %+.1f), p = %.3f ; Bonferroni %d reglages : t >= %.1f" % (
        lab, nom(kb), tst(D[:, int(mu.argmax())]), (Vb >= V).mean(), N, 2.8))
print("(e) H4 nas_h4_20k : deja refute au banc W (-5 a +10 bp, t <= 1,3), non refait.")
