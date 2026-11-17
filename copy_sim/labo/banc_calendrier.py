"""Banc CALENDRIER : effets de calendrier sur les indices US (PRIORITES 17/11 17 h, point 3). Plan fixe d'avance.
Marches : S&P 500 (^GSPC), Nasdaq 100 (^NDX), Dow (^DJI), Russell 2000 (^RUT) ; DAX (^GDAXI) en temoin.
Donnees : Yahoo journalier 1990-2026 (Dow des 1992), copie legere dans donnees/cal_<marche>.csv.gz ; taux 3 mois US
(FRED DTB3) dans donnees/cal_dtb3.csv ; dates FOMC (reunions PREVUES, sans les conferences telephoniques ni les reunions
« unscheduled », jour de l'annonce = dernier jour de la reunion, 1994-2026) relues sur federalreserve.gov et gardees
dans donnees/fomc.csv ; jours feries NYSE reconstruits par regles (Nouvel an, MLK des 1998, Presidents, Vendredi saint,
Memorial, Juneteenth des 2022, 4 juillet, Labor, Thanksgiving, Noel, report samedi->vendredi / dimanche->lundi, sauf
Nouvel an un samedi) et confrontes aux jours ouvres absents de ^GSPC ; fermetures imprevues (11/09, Sandy, deuils)
exclues car inconnues a l'avance. Controle recent : bougies D1 du courtier (2018/2020-2026) et spread M5 a la cloture.
Ce qui est NEUF par rapport a banc_saisons.py (Fable) : (a) grille complete k x j du tournant du mois (16 reglages,
dont 3 deja vus : k=1/j=3, k=2/j=3, k=4/j=3), Russell 2000, historique des 1990, jours au hasard ; (b) veille de
ferie et (c) FOMC : jamais testes ; (d) nuit/jour AVEC filtre simple (moyenne 200 j, veille en baisse / en hausse) et
Russell ; les versions sans filtre (deja vues) servent de point de comparaison. Achats seulement (effets connus).
Grilles (par marche) :
 (a) tournant du mois : achat a la cloture du jour -k (k-ieme dernier jour de bourse du mois), sortie a la cloture du
     jour +j du mois suivant, k, j dans {1..4} : 16.
 (b) veille de ferie US (V = dernier jour de bourse avant le ferie) : achat cloture V-1 ou V-2, sortie cloture V ou
     cloture du premier jour apres le ferie (V+1) : 4.
 (c) FOMC (J = jour de l'annonce) : achat cloture J-1 ou J-2, sortie cloture J ou J+1 : 4.
 (d) nuit (cloture -> ouverture) ou jour (ouverture -> cloture) x filtre {aucun, cloture > moyenne 200 j, veille en
     baisse, veille en hausse} (filtre connu a la cloture de la veille) : 8 ; annees a ouvertures figees exclues
     (part des jours ouverture = cloture de la veille > 5 %).
N = (16 + 4 + 4 + 8) x 5 marches = 160 reglages. Lignes walk-forward : 4 effets x 5 marches = 20 (Bonferroni sur 20).
Couts : 2 bp aller-retour par trade (haut de la fourchette 1-2 bp ; le spread M5 mesure a la cloture est affiche) +
financement CFD (DTB3 + 2,5 %)/360 par nuit calendaire tenue (DAX : meme formule). Les dates d'un evenement US sont
appliquees au DAX par sa derniere cloture <= la date.
Methode : walk-forward glissant, apprentissage 10 ans civils -> test 2 ans, pas de 2 ans ; reglage choisi au meilleur
t (gain net par trade) sur l'apprentissage, par marche. Hors echantillon (HE) : gain moyen par trade, t, deux moities
du HE, ecart a « acheter et garder a exposition egale » (moyenne journaliere nette du B&H dans la fenetre de test x
jours tenus), jours au hasard (meme nombre, meme duree, meme fenetre de test, 2000 tirages : p = part des tirages >=).
p HE unilateral, Bonferroni x 20 ; reality check de White (bootstrap stationnaire, blocs 10 j, 2000 tirages) sur
toute la periode, par effet (tous marches et reglages), contre 0 et contre la reference.
Verdict : TIENT = HE > 0, p Bonferroni < 0,05 (ou RC < 0,05), deux moities > 0, bat le B&H et le hasard (p < 0,05) ;
PRESQUE = HE > 0 et deux moities > 0 sans la significativite ; sinon NE TIENT PAS.
Sorties : res_calendrier.md (scratchpad, tableau), donnees/rebonds_calendrier.csv (trades HE des regles TIENT /
PRESQUE) et donnees/rebonds_calendrier_tout.csv (toute la periode, reglage choisi sur la derniere fenetre).
Usage : python3 banc_calendrier.py  (telecharge au premier lancement, ~1-2 min ensuite)"""
import os, re, sys, json, time, urllib.request, datetime as dt
from statistics import NormalDist
import numpy as np, pandas as pd

ICI = os.path.dirname(os.path.abspath(__file__))
DON = os.path.join(ICI, "donnees")
MT5 = os.path.join(ICI, "mt5", "donnees")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
MARCHES = {"SP500": "^GSPC", "NAS100": "^NDX", "DOW": "^DJI", "RUSSELL": "^RUT", "DAX": "^GDAXI"}
US = ["SP500", "NAS100", "DOW", "RUSSELL"]
COURTIER = {"SP500": "sp", "NAS100": "nas", "DOW": "dj", "RUSSELL": "us2000", "DAX": "ger"}
COUT = 2e-4
L_APP, L_TEST = 10, 2
NLIGNES = 20
rng = np.random.default_rng(1711)
ND = NormalDist()


# ------------------------------------------------------------------ donnees
def lit_url(url):
    for e in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=40).read()
        except Exception as err:
            last = err; time.sleep(2 * (e + 1))
    raise RuntimeError("echec %s : %s" % (url, last))


def yahoo(nom):
    f = os.path.join(DON, "cal_%s.csv.gz" % nom.lower())
    if os.path.exists(f):
        return pd.read_csv(f, index_col=0, parse_dates=True)
    url = ("https://query2.finance.yahoo.com/v8/finance/chart/%s?interval=1d&period1=631152000&period2=%d"
           % (urllib.request.quote(MARCHES[nom]), int(time.time())))
    r = json.loads(lit_url(url))["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    idx = pd.to_datetime(r["timestamp"], unit="s", utc=True).tz_convert(r["meta"]["exchangeTimezoneName"])
    d = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")}, index=idx.tz_localize(None).normalize())
    d = d.dropna(subset=["close"]); d = d[d.close > 0]
    d = d[~d.index.duplicated(keep="last")]
    d = d[d.index < pd.Timestamp.today().normalize()]          # pas la seance en cours
    d.round(4).to_csv(f)
    return d


def taux():
    f = os.path.join(DON, "cal_dtb3.csv")
    if not os.path.exists(f):
        t = pd.read_csv(io_bytes(lit_url("https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTB3")))
        t.columns = ["date", "dtb3"]; t = t[t.date >= "1989-01-01"]
        t["dtb3"] = pd.to_numeric(t.dtb3, errors="coerce"); t.dropna().to_csv(f, index=False)
    t = pd.read_csv(f, parse_dates=["date"]).set_index("date").dtb3 / 100
    return t


def io_bytes(b):
    import io
    return io.BytesIO(b)


MOIS = {m: i + 1 for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                         "September", "October", "November", "December"])}


def fomc():
    f = os.path.join(DON, "fomc.csv")
    if os.path.exists(f):
        return pd.to_datetime(pd.read_csv(f).annonce)
    jours = []
    for y in range(1994, 2021):
        t = lit_url("https://www.federalreserve.gov/monetarypolicy/fomchistorical%d.htm" % y).decode("utf8", "ignore")
        for h in re.findall(r"<h5[^>]*>([^<]*)</h5>", t):
            h = h.strip()
            if "Meeting" not in h or "unscheduled" in h or "cancelled" in h:
                continue
            m = re.match(r"(\w+) (\d+)(?:-(?:(\w+) )?(\d+))? Meeting - (\d{4})", h)
            if not m:
                continue
            mo = MOIS[m.group(3) or m.group(1)]; jo = int(m.group(4) or m.group(2))
            jours.append(dt.date(int(m.group(5)), mo, jo))
        time.sleep(0.3)
    t = lit_url("https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm").decode("utf8", "ignore")
    blocs = re.split(r"(\d{4}) FOMC Meetings", t)
    for y, b in zip(blocs[1::2], blocs[2::2]):
        for mo, jo in re.findall(r'fomc-meeting__month[^>]*><strong>([^<]*)</strong></div>\s*<div class="fomc-meeting__date[^>]*>([^<]*)</div>', b):
            if "notation" in jo or "unscheduled" in jo.lower() or "cancel" in jo.lower():
                continue
            mo = mo.split("/")[-1].strip(); n = re.findall(r"\d+", jo)
            if not n:
                continue
            m = [k for k in MOIS if k.startswith(mo[:3])][0]
            jours.append(dt.date(int(y), MOIS[m], int(n[-1])))
    s = pd.Series(sorted(set(jours)), name="annonce")
    s.to_csv(f, index=False)
    return pd.to_datetime(s)


def paques(y):
    a = y % 19; b, c = divmod(y, 100); d, e = divmod(b, 4); f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30; i, k = divmod(c, 4); l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451; mo = (h + l - 7 * m + 114) // 31; jo = (h + l - 7 * m + 114) % 31 + 1
    return dt.date(y, mo, jo)


def nieme_lundi(y, m, n, wd=0):
    d = dt.date(y, m, 1); d += dt.timedelta((wd - d.weekday()) % 7)
    if n > 0:
        return d + dt.timedelta(7 * (n - 1))
    d = dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(1)          # dernier
    return d - dt.timedelta((d.weekday() - wd) % 7)


def observe(d, nouvel_an=False):
    if d.weekday() == 5:
        return None if nouvel_an else d - dt.timedelta(1)
    if d.weekday() == 6:
        return d + dt.timedelta(1)
    return d


def feries(y):
    F = [observe(dt.date(y, 1, 1), True), nieme_lundi(y, 2, 3), paques(y) - dt.timedelta(2), nieme_lundi(y, 5, -1),
         observe(dt.date(y, 7, 4)), nieme_lundi(y, 9, 1), nieme_lundi(y, 11, 4, 3), observe(dt.date(y, 12, 25))]
    if y >= 1998:
        F.append(nieme_lundi(y, 1, 3))
    if y >= 2022:
        F.append(observe(dt.date(y, 6, 19)))
    return sorted(f for f in F if f)


# ------------------------------------------------------------------ trades
class Marche:
    def __init__(self, nom, d, tx):
        self.nom, self.d = nom, d
        self.c = d.close.values; self.idx = d.index
        r = tx.reindex(tx.index.union(d.index)).ffill().reindex(d.index).fillna(0.03).values
        self.fin = (r + 0.025) / 360                                   # par nuit
        self.jn = self.idx.values.astype("datetime64[D]").astype(np.int64)
        ret = np.r_[np.nan, self.c[1:] / self.c[:-1] - 1]
        nuits = np.r_[1, np.diff(self.jn)]
        self.bh = ret - self.fin * nuits                               # B&H net par jour

    def pos(self, dates):
        """Derniere seance <= date."""
        return np.searchsorted(self.idx.values, pd.DatetimeIndex(dates).values, side="right") - 1

    def trades(self, e, s):
        e, s = np.asarray(e), np.asarray(s)
        ok = (e >= 0) & (s > e) & (s < len(self.c))
        e, s = e[ok], s[ok]
        r = self.c[s] / self.c[e] - 1 - COUT - self.fin[e] * (self.jn[s] - self.jn[e])
        return pd.DataFrame({"entree": self.idx[e], "sortie": self.idx[s], "r": r, "h": s - e, "ie": e})


def tournant(M):
    mo = M.idx.to_period("M"); u = mo.unique()
    prem = np.searchsorted(mo, u, side="left"); dern = np.searchsorted(mo, u, side="right") - 1
    C = {}
    for k in range(1, 5):
        for j in range(1, 5):
            e = dern[:-1] - (k - 1); s = prem[1:] + (j - 1)
            s = np.where(s <= dern[1:], s, -1)
            C["k%d j%d" % (k, j)] = M.trades(e, np.where(s < 0, len(M.c), s))
    return C


def veille_ferie(M, FER):
    C = {}
    fer = pd.DatetimeIndex([f for f in FER if M.idx[0] < f < M.idx[-1]])
    v = M.pos(fer - pd.Timedelta(days=1))                               # derniere cloture avant le ferie
    apres = np.searchsorted(M.idx.values, fer.values, side="right")     # premiere seance apres le ferie
    for a in (1, 2):
        for nom, s in (("V", v), ("V+1", apres)):
            C["achat V-%d sortie %s" % (a, nom)] = M.trades(v - a, s)
    return C


def jours_fed(M, FED):
    C = {}
    fed = pd.DatetimeIndex([f for f in FED if M.idx[0] < f < M.idx[-1]])
    J = M.pos(fed)
    if M.nom != "DAX":
        J = J[M.idx[J] == fed]
    for a in (1, 2):
        for b in (0, 1):
            C["achat J-%d sortie J%s" % (a, "+1" if b else "")] = M.trades(J - a, J + b)
    return C


def nuit_jour(M):
    d = M.d
    o, c = d.open.values, d.close.values
    cp = np.r_[np.nan, c[:-1]]
    fige = pd.Series(np.isclose(o, cp), index=d.index).groupby(d.index.year).transform("mean").values > 0.05
    ok = ~fige & ~np.isnan(o) & (o > 0) & ~np.isnan(cp)
    nuits = np.r_[1, np.diff(M.jn)]
    ok &= nuits <= 4
    ma = pd.Series(c).rolling(200).mean().values
    ma_p = np.r_[np.nan, ma[:-1]]; cpp = np.r_[np.nan, np.nan, c[:-2]]
    F = {"aucun": np.ones(len(c), bool), "MM200": cp > ma_p, "veille baisse": cp < cpp, "veille hausse": cp > cpp}
    rn = o / cp - 1 - COUT - M.fin * nuits
    rj = c / o - 1 - COUT
    C = {}
    i = np.arange(len(c))
    for seg, r in (("nuit", rn), ("jour", rj)):
        for f, m in F.items():
            mm = ok & m
            C["%s %s" % (seg, f)] = pd.DataFrame({"entree": M.idx[np.maximum(i - (seg == "nuit"), 0)][mm], "sortie": M.idx[mm],
                                                 "r": r[mm], "h": 1, "ie": i[mm] - (seg == "nuit")})
    return C, ok


# ------------------------------------------------------------------ statistiques
def tst(x):
    x = np.asarray(x, float)
    return 0.0 if len(x) < 3 or x.std(ddof=1) == 0 else x.mean() / x.std(ddof=1) * np.sqrt(len(x))


def walk_forward(M, C, ref_jour=None):
    """Rend les trades HE (avec reglage), la liste des choix."""
    an0 = max(M.idx[0].year + (M.idx[0].month > 1), min(v.entree.min().year for v in C.values() if len(v)))
    ans = list(range(an0 + L_APP, 2027, L_TEST))
    he, choix = [], []
    for y in ans:
        a0, a1 = pd.Timestamp(y - L_APP, 1, 1), pd.Timestamp(y, 1, 1)
        b1 = pd.Timestamp(y + L_TEST, 1, 1)
        best, bt = None, -1e9
        for k, v in C.items():
            x = v.r[(v.entree >= a0) & (v.sortie < a1)]
            t = tst(x)
            if len(x) >= 10 and t > bt:
                best, bt = k, t
        if best is None:
            continue
        v = C[best]; te = v[(v.entree >= a1) & (v.entree < b1)].copy()
        # reference : B&H net moyen par jour dans la fenetre de test x jours tenus
        w = (M.idx >= a1) & (M.idx < b1)
        mbh = np.nanmean(M.bh[w]) if ref_jour is None else np.nanmean(ref_jour[w])
        te["ref"] = mbh * te.h; te["regle"] = best; te["fen"] = y
        he.append(te); choix.append(best)
    return pd.concat(he), choix


def hasard(M, te, C_all, nuit=False, nb=2000):
    """p : part des tirages au hasard (meme nombre, meme duree, meme fenetre) dont la moyenne >= celle de la regle."""
    if not len(te):
        return np.nan
    moy = np.zeros(nb)
    for (y, h), g in te.groupby(["fen", "h"]):
        a1, b1 = pd.Timestamp(y, 1, 1), pd.Timestamp(y + L_TEST, 1, 1)
        if nuit:
            pool = C_all[(C_all.entree >= a1 - pd.Timedelta(days=5)) & (C_all.sortie >= a1) & (C_all.sortie < b1)].r.values
            if not len(pool):
                continue
            moy += pool[rng.integers(len(pool), size=(nb, len(g)))].sum(1)
        else:
            lo = np.searchsorted(M.idx.values, np.datetime64(a1)); hi = np.searchsorted(M.idx.values, np.datetime64(b1)) - 1
            hi = min(hi, len(M.c) - 1 - h)
            e = rng.integers(lo, max(hi, lo + 1), size=(nb, len(g)))
            r = M.c[e + h] / M.c[e] - 1 - COUT - M.fin[e] * (M.jn[e + h] - M.jn[e])
            moy += r.sum(1)
    moy /= len(te)
    return float((moy >= te.r.mean()).mean())


def comptes(n, nb, b=10.0):
    neuf = rng.random((nb, n)) < 1 / b; neuf[:, 0] = True
    pos = np.where(neuf, np.arange(n), 0); pos = np.maximum.accumulate(pos, axis=1)
    dep = np.where(neuf, rng.integers(n, size=(nb, n)), 0)
    dep = np.take_along_axis(dep, pos, axis=1)
    ii = (dep + np.arange(n) - pos) % n
    flat = (ii + np.arange(nb)[:, None] * n).ravel()
    return np.bincount(flat, minlength=nb * n).reshape(nb, n).astype(np.float32)


def white(S):
    """S : DataFrame jours x reglages (gain au jour de sortie). p du meilleur reglage contre 0."""
    X = np.nan_to_num(S.values.astype(np.float32)); n = len(X)
    mu = X.mean(0); V = np.sqrt(n) * mu.max()
    Vb = np.concatenate([np.sqrt(n) * ((comptes(n, 200) @ X) / n - mu).max(1) for _ in range(10)])
    return float((Vb >= V).mean()), S.columns[int(mu.argmax())]


def serie(v, idx, col="r"):
    return v.groupby("sortie")[col].sum().reindex(idx).fillna(0.0)


# ------------------------------------------------------------------ programme
def main():
    tx = taux(); FED = fomc()
    D = {k: yahoo(k) for k in MARCHES}
    out = []
    P = lambda *a: (print(*a), out.append(" ".join(str(x) for x in a)))
    # feries : controle contre les jours ouvres absents du S&P
    sp = D["SP500"].index
    FER = [pd.Timestamp(f) for y in range(1990, 2027) for f in feries(y)]
    ouvres = pd.bdate_range(sp[0], sp[-1])
    absents = set(ouvres.difference(sp)); regle = set(f for f in FER if sp[0] <= f <= sp[-1])
    P("Feries NYSE par regles : %d dans la periode ; jours ouvres absents de ^GSPC : %d ; regle mais cote : %s ; "
      "absents hors regle (fermetures imprevues, exclues) : %s" % (
          len(regle), len(absents), sorted(str(x.date()) for x in regle - absents)[:8],
          sorted(str(x.date()) for x in absents - regle)))
    P("FOMC : %d annonces prevues %s -> %s (donnees/fomc.csv)" % (len(FED), FED.min().date(), FED.max().date()))
    for k, d in D.items():
        P("%-8s Yahoo %s -> %s, %d seances" % (k, d.index[0].date(), d.index[-1].date(), len(d)))
    # spread du courtier a la cloture au comptant (controle du cout suppose)
    sps = []
    for k, f, hh in (("SP500", "sp_m5_90k", 22), ("NAS100", "nas_m5_90k", 22), ("DOW", "dj_m5_90k", 22), ("DAX", "ger_m1_90k", None)):
        m = pd.read_csv(os.path.join(MT5, f + ".csv.gz")); t = pd.to_datetime(m.heure, unit="s")
        x = m[(t.dt.hour == hh) & (t.dt.minute == 55)] if hh else m[(t.dt.hour == 18) & (t.dt.minute == 29)]
        sps.append("%s %.2f bp" % (k, 1e4 * (x.spread_points * 0.01 / x.cloture).median()))
    P("Spread courtier median a la cloture au comptant (M5, 22 h 55 serveur ; DAX M1 18 h 29) : " + ", ".join(sps)
      + " -> cout suppose 2 bp aller-retour (prudent) ; Russell : pas de M5, meme hypothese.")

    MK = {k: Marche(k, d, tx) for k, d in D.items()}
    EFFETS = {"tournant": lambda M: tournant(M), "ferie": lambda M: veille_ferie(M, FER),
              "fomc": lambda M: jours_fed(M, FED), "nuitjour": None}
    lignes, toutHE, toutFULL, RCS = [], [], [], []
    Ntot = 0
    for eff in EFFETS:
        S, R = {}, {}
        for k, M in MK.items():
            if eff == "nuitjour":
                C, ok = nuit_jour(M)
                refj = np.where(ok, M.bh, np.nan)
            else:
                C = EFFETS[eff](M); refj = None
            Ntot += len(C)
            he, ch = walk_forward(M, C, refj)
            # reality check : series a la sortie
            for c, v in C.items():
                if not len(v):
                    continue
                mbh = np.nanmean(M.bh if refj is None else refj)
                S["%s %s" % (k, c)] = serie(v, M.idx); R["%s %s" % (k, c)] = serie(v.assign(x=v.r - mbh * v.h), M.idx, "x")
            # hasard
            ph = hasard_nj(M, he, C) if eff == "nuitjour" else hasard(M, he, None)
            t = tst(he.r); ex = he.r - he.ref
            mid = he.entree.min() + (he.entree.max() - he.entree.min()) / 2
            h1, h2 = he[he.entree < mid], he[he.entree >= mid]
            final = ch[-1]
            fq = pd.Series(ch).value_counts()
            lignes.append(dict(effet=eff, marche=k, N=len(C), reglage=final, frequent="%s %d/%d" % (fq.index[0], fq.iloc[0], len(ch)),
                               trades=len(he), bp=1e4 * he.r.mean(), t=t, somme=100 * he.r.sum(),
                               h1=1e4 * h1.r.mean(), t1=tst(h1.r), h2=1e4 * h2.r.mean(), t2=tst(h2.r),
                               ex=1e4 * ex.mean(), tex=tst(ex), ph=ph, p=1 - ND.cdf(t),
                               debut=he.entree.min().date(), fin=he.sortie.max().date()))
            toutHE.append(he.assign(marche=k, effet=eff))
            toutFULL.append(C[final].assign(marche=k, effet=eff, regle=final))
        Sd = pd.DataFrame(S).fillna(0.0); Rd = pd.DataFrame(R).fillna(0.0)
        p0, b0 = white(Sd); pr, br = white(Rd)
        RCS.append((eff, Sd.shape[1], p0, b0, pr, br))
    L = pd.DataFrame(lignes)
    L["pb"] = np.minimum(1, L.p * NLIGNES)
    rcd = {e: (p0, pr) for e, _, p0, _, pr, _ in RCS}

    def verdict(r):
        sig = r.pb < 0.05 or rcd[r.effet][0] < 0.05
        bat = r.ex > 0 and r.tex > 0 and (r.ph < 0.05 if not np.isnan(r.ph) else True)
        if r.bp > 0 and r.h1 > 0 and r.h2 > 0 and sig and bat:
            return "TIENT"
        if r.bp > 0 and r.h1 > 0 and r.h2 > 0:
            return "PRESQUE"
        return "NE TIENT PAS"
    L["verdict"] = L.apply(verdict, axis=1)
    P("\nN total de reglages essayes : %d ; lignes walk-forward : %d (Bonferroni x %d)." % (Ntot, len(L), NLIGNES))
    P("Reality check de White par effet (toute la periode, tous marches et reglages) :")
    for eff, n, p0, b0, pr, br in RCS:
        P("  %-9s N = %3d : contre 0 p = %.3f (meilleur %s) ; contre B&H a exposition egale p = %.3f (meilleur %s)" % (eff, n, p0, b0, pr, br))
    P("\n%-9s %-8s %-24s %-28s %5s %6s %5s %13s %13s %6s %5s %5s %6s %s" % (
        "effet", "marche", "reglage (derniere fen.)", "le plus choisi", "trad", "HE bp", "t", "moitie1 bp(t)", "moitie2 bp(t)",
        "vsB&H", "t", "pHas", "pBonf", "verdict"))
    for _, r in L.iterrows():
        P("%-9s %-8s %-24s %-28s %5d %+6.1f %+5.2f %+6.1f(%+4.1f) %+6.1f(%+4.1f) %+6.1f %+5.2f %5.3f %6.3f %s" % (
            r.effet, r.marche, r.reglage[:24], r.frequent[:28], r.trades, r.bp, r.t, r.h1, r.t1, r.h2, r.t2, r.ex, r.tex, r.ph, r.pb, r.verdict))
    # lignes groupees US (une moyenne par date d'entree : evite de compter 4 fois le meme evenement)
    HE = pd.concat(toutHE)
    P("\nGroupe US (4 indices, moyenne par date d'entree, HE) :")
    for eff in EFFETS:
        g = HE[(HE.effet == eff) & HE.marche.isin(US)]
        a = g.groupby(g.entree.dt.normalize()).r.mean(); x = g.groupby(g.entree.dt.normalize()).apply(lambda z: (z.r - z.ref).mean())
        mid = a.index.min() + (a.index.max() - a.index.min()) / 2
        P("  %-9s evenements %5d : %+6.1f bp (t %+5.2f) ; moities %+6.1f / %+6.1f bp ; vs B&H %+6.1f bp (t %+5.2f) ; p Bonf %.3f" % (
            eff, len(a), 1e4 * a.mean(), tst(a), 1e4 * a[a.index < mid].mean(), 1e4 * a[a.index >= mid].mean(),
            1e4 * x.mean(), tst(x), min(1, (1 - ND.cdf(tst(a))) * NLIGNES)))
    # controle courtier D1 sur les reglages retenus
    P("\nControle bougies D1 du courtier (cloture serveur ~17 h New York), memes dates, reglage retenu, memes couts :")
    FULL = pd.concat(toutFULL)
    for k in MARCHES:
        b = pd.read_csv(os.path.join(MT5, COURTIER[k] + "_d1_5k.csv.gz"))
        b.index = pd.to_datetime(b.heure, unit="s").normalize(); b = b[b.index.dayofweek < 5]
        Mb = Marche(k, b.rename(columns={"cloture": "close", "ouverture": "open"}), tx)
        for eff in ("tournant", "ferie", "fomc"):
            v = FULL[(FULL.marche == k) & (FULL.effet == eff) & (FULL.entree >= b.index[0])]
            if not len(v):
                continue
            tb = Mb.trades(Mb.pos(v.entree), Mb.pos(v.sortie))
            ry = v.r.values[:len(tb)] if len(tb) == len(v) else v.r.values[np.isin(v.entree.values, v.entree.values)][:len(tb)]
            P("  %-8s %-9s %-22s %3d trades %s-> : Yahoo %+6.1f bp, courtier %+6.1f bp (corr %.2f)" % (
                k, eff, v.regle.iloc[0][:22], len(tb), b.index[0].date(), 1e4 * v.r.mean(), 1e4 * tb.r.mean(),
                np.corrcoef(ry, tb.r.values)[0, 1] if len(tb) == len(v) and len(tb) > 2 else np.nan))
    # sorties
    garde = L[L.verdict.isin(["TIENT", "PRESQUE"])]
    rows_he, rows_all = [], []
    for _, r in garde.iterrows():
        g = HE[(HE.effet == r.effet) & (HE.marche == r.marche)]
        rows_he.append(pd.DataFrame({"regle": ("cal_%s " % r.effet) + g.regle.values,
                                     "marche": r.marche, "entree": g.entree.dt.strftime("%Y-%m-%d"),
                                     "sortie": g.sortie.dt.strftime("%Y-%m-%d"), "sens": 1, "r": g.r.round(6)}))
        f = FULL[(FULL.effet == r.effet) & (FULL.marche == r.marche)]
        rows_all.append(pd.DataFrame({"regle": "cal_%s %s" % (r.effet, f.regle.values[0]), "marche": r.marche,
                                      "entree": f.entree.dt.strftime("%Y-%m-%d"), "sortie": f.sortie.dt.strftime("%Y-%m-%d"),
                                      "sens": 1, "r": f.r.round(6)}))
    cols = ["regle", "marche", "entree", "sortie", "sens", "r"]
    (pd.concat(rows_he) if rows_he else pd.DataFrame(columns=cols)).to_csv(os.path.join(DON, "rebonds_calendrier.csv"), index=False)
    (pd.concat(rows_all) if rows_all else pd.DataFrame(columns=cols)).to_csv(os.path.join(DON, "rebonds_calendrier_tout.csv"), index=False)
    P("\nEcrit : donnees/rebonds_calendrier.csv (%d trades HE, %d regles) et rebonds_calendrier_tout.csv." % (
        sum(len(x) for x in rows_he), len(rows_he)))
    return L, out


def hasard_nj(M, he, C, nb=2000):
    """Nuit/jour : tirages parmi TOUTES les nuits (ou tous les jours) valides de la meme fenetre, meme nombre."""
    moy = np.zeros(nb)
    for (y, reg), g in he.groupby(["fen", "regle"]):
        base = C[reg.split()[0] + " aucun"]
        a1, b1 = pd.Timestamp(y, 1, 1), pd.Timestamp(y + L_TEST, 1, 1)
        pool = base.r[(base.sortie >= a1) & (base.sortie < b1)].values
        moy += pool[rng.integers(len(pool), size=(nb, len(g)))].sum(1)
    return float((moy / len(he) >= he.r.mean()).mean())


if __name__ == "__main__":
    main()
