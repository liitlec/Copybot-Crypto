"""Banc COT : positionnement des speculateurs (rapport hebdomadaire de la CFTC) comme signal, en journalier/hebdomadaire.

Donnees
- COT « legacy, futures seulement » de la CFTC (publicreporting.cftc.gov, jeu 6dca-aqww, gratuit, sans cle), tout
  l'historique, cache data/cot.csv.gz. Non commerciaux (speculateurs) et commerciaux, positions longues - courtes.
- Prix : bougies jour du courtier (mt5/donnees, xau/nas/sp/dj d1) quand elles existent, completees avant par Yahoo
  (donnees.yahoo : GC=F, SI=F, ^GSPC, ^NDX, ^DJI, EURUSD=X, JPY=X, BTC-USD), cache data/prix_cot.csv.gz.
  Courtier : entree a l'OUVERTURE du lundi. Yahoo : les ouvertures anciennes sont fausses (open = cloture), on
  prend donc la CLOTURE du lundi (plus tard que permis : prudent). Yen : position longue yen = inverse de USDJPY.
Calendrier (aucun regard vers le futur)
- Le rapport porte sur le mardi et sort le vendredi 15 h 30 heure de New York : il n'est utilise qu'au lundi qui suit
  (date du rapport + 6 j). Semaine avec un jour ferie federal US (lundi a vendredi) : la sortie glisse au lundi
  suivant 15 h 30, on ne s'en sert donc qu'une semaine plus tard (+13 j). Rapports pris pendant les fermetures de
  l'administration (2013, 2018-19, 2025) : ignores (publies en retard). Test de sensibilite : tout a +13 j.
Regle
- Indice COT = (net - min) / (max - min) x 100 sur les W derniers rapports, W dans {52, 104, 156}.
- « contre » : indice des speculateurs > haut -> vendre, < bas -> acheter ; « suivre » : l'inverse ;
  « comm » : indice des commerciaux > haut -> acheter, < bas -> vendre (on suit les commerciaux).
- Seuils (haut, bas) dans {(80, 20), (90, 10)} ; tenue 1, 4 ou 8 semaines (un nouveau signal relance la tenue)
  ou jusqu'au retour de l'indice a 50. Grille : 3 sens x 3 W x 2 seuils x 4 tenues = N = 72 reglages par marche.
- Rendement hebdomadaire d'un lundi au lundi suivant, exposition 1 ; cout = spread median observe dans les bougies
  du courtier (aller-retour), compte a chaque changement de position. Financement de nuit (swap) NON compte.
Methode (fixee d'avance)
- Walk-forward glissant : apprentissage 3 ans, test 1 an (annees civiles), meilleur t sur l'apprentissage parmi les
  72 reglages ; serie hors echantillon concatenee : total (bp), t, annees gagnantes, creux, trades, bp par trade,
  et chaque moitie de la periode de test (stabilite = les deux moitiees > 0).
- References : ne rien faire (0) et acheter-et-garder a exposition egale (rendement du marche x exposition moyenne).
- Reality check de White (bootstrap stationnaire, blocs moyens 8 semaines, 2000 tirages) contre « ne rien faire » :
  par marche (N = 72) et sur l'ensemble marches x reglages (rendements ramenes a la volatilite de chaque marche).
- Verdict : tient = hors ech > 0 et (t >= 2,6 ou p RC < 0,05) ; presque = hors ech > 0 et (t >= 1,5 ou p < 0,15).
Usage : python3 banc_cot.py   (premier lancement : telechargement ; ensuite le cache data/ suffit)"""
import contextlib, io, os, json, time, urllib.request
import numpy as np, pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
import donnees
with contextlib.redirect_stdout(io.StringIO()):
    import banc_or as B

ICI = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ICI, "data")
F_COT, F_PRIX = os.path.join(DATA, "cot.csv.gz"), os.path.join(DATA, "prix_cot.csv.gz")
# nom -> (codes CFTC, ticker Yahoo, bougies jour du courtier, bougies pour le spread, inverse)
MARCHES = {
    "or":      (["088691"], "GC=F", "xau_d1_5k", "xau_m5_90k", False),
    "argent":  (["084691"], "SI=F", None, "xag_m5_90k", False),
    "sp500":   (["13874A"], "^GSPC", "sp_d1_5k", "sp_m5_90k", False),
    "nasdaq":  (["209742"], "^NDX", "nas_d1_5k", "nas_m5_90k", False),
    "dow":     (["124603"], "^DJI", "dj_d1_5k", "dj_m5_90k", False),
    "euro":    (["099741"], "EURUSD=X", None, "eur_m5_90k", False),
    "yen":     (["097741"], "JPY=X", None, "jpy_m1_90k", True),
    "bitcoin": (["133741"], "BTC-USD", None, "btc_m5_90k", False),
}
FERMETURES = [("2013-09-24", "2013-10-29"), ("2018-12-18", "2019-03-05"), ("2025-09-23", "2026-01-27")]
SENS, WS, SEUILS, TENUES = ("contre", "suivre", "comm"), (52, 104, 156), ((80, 20), (90, 10)), (1, 4, 8, 50)
GRILLE = [(s, w, hl, h) for s in SENS for w in WS for hl in SEUILS for h in TENUES]
nomr = lambda k: "%s W%d %d/%d %s" % (k[0], k[1], k[2][0], k[2][1], "->50" if k[3] == 50 else "%dsem" % k[3])


# ------------------------------------------------------------------ donnees
def telecharge_cot():
    lignes = []
    cols = ("report_date_as_yyyy_mm_dd,cftc_contract_market_code,open_interest_all,noncomm_positions_long_all,"
            "noncomm_positions_short_all,comm_positions_long_all,comm_positions_short_all")
    for nom, (codes, *_r) in MARCHES.items():
        for c in codes:
            url = ("https://publicreporting.cftc.gov/resource/6dca-aqww.json?$select=%s&$where=cftc_contract_market_code='%s'"
                   "&$limit=50000&$order=report_date_as_yyyy_mm_dd" % (cols, c))
            for essai in range(5):  # reseau capricieux : on reessaie
                try:
                    d = json.load(urllib.request.urlopen(urllib.request.Request(url.replace("'", "%27"), headers={"User-Agent": donnees.UA}), timeout=60))
                    break
                except OSError:
                    if essai == 4:
                        raise
                    time.sleep(3 * (essai + 1))
            for r in d:
                lignes.append((nom, r["report_date_as_yyyy_mm_dd"][:10], *[float(r.get(k, "nan")) for k in cols.split(",")[2:]]))
            time.sleep(0.5)
    z = pd.DataFrame(lignes, columns=["marche", "date", "oi", "nc_l", "nc_s", "c_l", "c_s"])
    z = z.groupby(["marche", "date"], as_index=False).sum()      # meme contrat sous deux libelles : une ligne par date
    os.makedirs(DATA, exist_ok=True)
    z.to_csv(F_COT, index=False, float_format="%.0f")


def telecharge_prix():
    p = {}
    for nom, (_, tk, *_r) in MARCHES.items():
        s = donnees.yahoo(tk, "1d", "max")
        s.index = s.index.tz_convert(None).normalize()
        p[nom] = s[~s.index.duplicated(keep="last")]
        time.sleep(0.5)
    os.makedirs(DATA, exist_ok=True)
    pd.DataFrame(p).sort_index().loc["1995":].to_csv(F_PRIX, float_format="%.6g")


def semaines(nom, lundis):
    """Rendement de chaque semaine (lundi -> lundi suivant), en bp ; courtier (ouverture) sinon Yahoo (cloture)."""
    y = PRIX[nom].dropna()
    def premier(s):  # prix du premier jour de bourse de chaque semaine civile commencant un lundi
        s = s[s.index.dayofweek < 5]
        g = s.groupby(s.index - pd.to_timedelta(s.index.dayofweek, unit="D")).first()
        return g.reindex(lundis)
    py = premier(y)
    r = py.shift(-1) / py - 1
    ident = MARCHES[nom][2]
    if ident:
        d, _ = B.charge(ident)
        pb = premier(d["ouverture"])
        rb = pb.shift(-1) / pb - 1
        r = rb.where(rb.notna(), r)
    if MARCHES[nom][4]:
        r = 1 / (1 + r) - 1
    return r * 1e4


def cout_bp(nom):
    d, _ = B.charge(MARCHES[nom][3])
    return float((d["sp"] / d["cloture"] * 1e4).median())


def calendrier_cot(z, decal_fixe=None):
    """Date (lundi) a partir de laquelle chaque rapport est utilisable."""
    dt = pd.to_datetime(z["date"])
    if decal_fixe:
        return dt + pd.Timedelta(days=decal_fixe)
    fer = USFederalHolidayCalendar().holidays("1985-01-01", "2027-12-31")
    sem = dt - pd.Timedelta(days=1)
    ferie = np.array([((fer >= a) & (fer <= a + pd.Timedelta(days=4))).any() for a in sem])
    av = dt + pd.to_timedelta(np.where(ferie, 13, 6), unit="D")
    for a, b in FERMETURES:
        av[(dt >= a) & (dt <= b)] = pd.NaT
    return av


# ------------------------------------------------------------------ regle
def positions(x, neuf, k):
    """x : indice (0-100) de la semaine, neuf : rapport nouveau cette semaine ; renvoie la position par semaine."""
    s, _, (hi, lo), h = k
    pos, cnt, cote, out = 0.0, 0, 0, np.zeros(len(x))
    sgn = {"contre": -1.0, "suivre": 1.0, "comm": 1.0}[s]
    for i in range(len(x)):
        v = x[i]
        if neuf[i] and v == v:
            sig = sgn if v > hi else (-sgn if v < lo else 0.0)
            ext = 1 if v > hi else (-1 if v < lo else 0)
            if h == 50:
                if pos != 0 and ((cote > 0 and v <= 50) or (cote < 0 and v >= 50)):
                    pos, cote = 0.0, 0
                if sig != 0:
                    pos, cote = sig, ext
            elif sig != 0:
                pos, cnt = sig, h
        out[i] = pos
        if h != 50 and pos != 0:
            cnt -= 1
            if cnt <= 0:
                pos = 0.0
    return out


def series(nom, decal_fixe=None):
    z = COT[COT.marche == nom].sort_values("date").reset_index(drop=True)
    z["dispo"] = calendrier_cot(z, decal_fixe)
    z = z.dropna(subset=["dispo"])
    r = R[nom]
    net_s, net_c = (z.nc_l - z.nc_s).values, (z.c_l - z.c_s).values
    # rapport en vigueur chaque lundi = le plus recent deja publie
    j = np.searchsorted(z.dispo.values, r.index.values, side="right") - 1
    neuf = np.r_[True, j[1:] != j[:-1]] & (j >= 0)
    c = COUT[nom] / 2
    out = {}
    for w in WS:
        ind = {}
        for nm, net in (("s", net_s), ("c", net_c)):
            sr = pd.Series(net)
            mn, mx = sr.rolling(w, min_periods=w).min(), sr.rolling(w, min_periods=w).max()
            v = ((sr - mn) / (mx - mn).replace(0, np.nan) * 100).values
            ind[nm] = np.where(j >= 0, v[np.maximum(j, 0)], np.nan)
        for k in GRILLE:
            if k[1] != w:
                continue
            p = positions(ind["c" if k[0] == "comm" else "s"], neuf, k)
            p = np.where(np.isfinite(r.values), p, 0.0)
            g = p * np.nan_to_num(r.values) - np.abs(np.diff(np.r_[0, p])) * c
            out[k] = (pd.Series(g, r.index), pd.Series(p, r.index))
    return out


# ------------------------------------------------------------------ statistiques
tstat = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else 0.0
creux = lambda x: (x.cumsum() - x.cumsum().cummax()).min()
ntrades = lambda p: int(((p != 0) & (p != p.shift(1).fillna(0))).sum())


def walk_forward(S, cles):
    an = S[cles[0]][0].index.year
    debut = min(S[k][1].ne(0).idxmax().year for k in cles) if any(S[k][1].ne(0).any() for k in cles) else an[0]
    o, po, choix, gan = [], [], [], []
    for y in range(max(debut, an[0]) + 3, an[-1] + 1):
        app, te = (an >= y - 3) & (an <= y - 1), an == y
        best = max(cles, key=lambda k: tstat(S[k][0][app]))
        o.append(S[best][0][te]); po.append(S[best][1][te]); choix.append(best); gan.append(S[best][0][te].sum() > 0)
    return pd.concat(o), pd.concat(po), choix, gan


def boot_idx(n, b=8.0):
    neuf = rng.random(n) < 1 / b; neuf[0] = True
    bloc = np.cumsum(neuf) - 1; dep = np.flatnonzero(neuf)
    return (rng.integers(n, size=len(dep))[bloc] + np.arange(n) - dep[bloc]) % n


def reality_check(M, tirages=2000):
    global rng
    rng = np.random.default_rng(17)                                  # memes tirages pour chaque appel
    n = len(M); mu = M.mean(0); V = np.sqrt(n) * mu.max()
    Vb = np.array([np.sqrt(n) * (M[boot_idx(n)].mean(0) - mu).max() for _ in range(tirages)])
    return int(mu.argmax()), (Vb >= V).mean()


def verdict(o, t, p):
    if o > 0 and (t >= 2.6 or p < 0.05):
        return "TIENT"
    return "presque" if o > 0 and (t >= 1.5 or p < 0.15) else "ne tient pas"


# ------------------------------------------------------------------ programme
if not os.path.exists(F_COT):
    telecharge_cot()
if not os.path.exists(F_PRIX):
    telecharge_prix()
COT = pd.read_csv(F_COT, dtype={"marche": str, "date": str})
COT = COT[~((COT.marche == "euro") & (COT.date < "1999"))]      # 1986 : ancien ECU, 12 ans avant l'euro
PRIX = pd.read_csv(F_PRIX, index_col=0, parse_dates=True)
LUNDIS = pd.date_range("1997-01-06", PRIX.index[-1], freq="W-MON")
R = {nom: semaines(nom, LUNDIS) for nom in MARCHES}
COUT = {nom: cout_bp(nom) for nom in MARCHES}
S = {nom: series(nom) for nom in MARCHES}
N = len(GRILLE)


def ligne(nom, cles, S_=None, etiquette=None):
    S_ = S_ or S[nom]
    o, po, choix, gan = walk_forward(S_, cles)
    M = np.column_stack([S_[k][0].values for k in cles])
    _, p = reality_check(M[(M != 0).any(1).cumsum() > 0])          # echantillon complet, des le premier trade
    rb = R[nom].reindex(o.index).fillna(0); expo = po.abs().mean(); bh = (rb * expo).sum()
    nt = ntrades(po); m = len(o) // 2; h1, h2 = o.iloc[:m].sum(), o.iloc[m:].sum()
    fq = pd.Series([nomr(k) for k in choix]).value_counts()
    print("%-8s %-25s %2d/%-2d %+7.0f %+5.1f %5.3f %3d/%-2d %4d %+6.0f %+7.0f %+7.0f %+6.0f/%+6.0f %s"
          % (etiquette or nom, fq.index[0][:25], fq.iloc[0], len(choix), o.sum(), tstat(o), p, sum(gan), len(gan),
             nt, o.sum() / max(nt, 1), creux(o), bh, h1, h2, verdict(o.sum(), tstat(o), p)))
    return o, p


ent = "%-8s %-25s %5s %7s %5s %5s %6s %4s %6s %7s %7s %13s %s" % ("marche", "reglage le plus choisi", "nb", "HE bp", "t", "p RC", "ans>0", "trad", "bp/tr", "creux", "B&H=exp", "moitie1/2", "verdict")
o0 = R["or"].dropna()
print("Banc COT (CFTC legacy, non commerciaux / commerciaux) ; N = %d reglages par marche ; Bonferroni 5 %% : t >= %.2f (N=72), %.2f (N=%d)"
      % (N, 3.19, 3.82, N * len(MARCHES)))
print("Couts aller-retour (spread median courtier, bp) : " + ", ".join("%s %.2f" % (k, v) for k, v in COUT.items()))
print("== Piste 1 : or. Prix %s -> %s (courtier d1 depuis 2018-09, GC=F avant) ; COT or %s -> %s"
      % (o0.index[0].date(), o0.index[-1].date(), COT[COT.marche == "or"].date.min(), COT[COT.marche == "or"].date.max()))
print("Walk-forward 3 ans / 1 an, test %d -> %d ; HE = hors echantillon (somme des bp hebdo, exposition 1)" % (walk_forward(S["or"], GRILLE)[0].index[0].year, o0.index[-1].year))
print(ent)
o_or, p_or = ligne("or", GRILLE, etiquette="or 72")
for s in SENS:
    ligne("or", [k for k in GRILLE if k[0] == s], etiquette="or " + s)
S13 = series("or", decal_fixe=13)
ligne("or", GRILLE, S_=S13, etiquette="or +13j")
print("Acheter-et-garder l'or sur les memes semaines (exposition 1) : %+.0f bp ; t %+.1f"
      % (R["or"].reindex(o_or.index).fillna(0).sum(), tstat(R["or"].reindex(o_or.index).fillna(0))))
print("== Piste 2 : tous marches (WF sur les 72 reglages de chaque marche ; p RC par marche, N = 72)")
print(ent)
RES = {}
for nom in MARCHES:
    z = COT[COT.marche == nom].date
    o, p = ligne(nom, GRILLE)
    RES[nom] = (o, p, z.min(), R[nom].dropna().index[0].date())
for nom in MARCHES:  # sensibilite au calendrier de publication pour les marches qui ne sont pas « ne tient pas »
    o, p = RES[nom][:2]
    if verdict(o.sum(), tstat(o), p) != "ne tient pas":
        ligne(nom, GRILLE, S_=series(nom, decal_fixe=13), etiquette=nom[:4] + " +13j")
print("Periodes COT / prix : " + " ; ".join("%s %s/%s" % (k, v[2][:4], str(v[3])[:4]) for k, v in RES.items()))
# reality check d'ensemble, rendements ramenes a la volatilite hebdomadaire de chaque marche
cols, noms = [], []
for nom in MARCHES:
    vol = R[nom].std()
    for k in GRILLE:
        cols.append(S[nom][k][0].values / vol); noms.append((nom, k))
M = np.column_stack(cols)
M = M[(M != 0).any(1).cumsum() > 0]
ib, pg = reality_check(M)
print("Reality check d'ensemble (%d marches x %d = %d reglages, %d semaines) : meilleur = %s %s (t plein ech %+.1f), p = %.3f"
      % (len(MARCHES), N, M.shape[1], len(M), noms[ib][0], nomr(noms[ib][1]), tstat(pd.Series(M[:, ib])), pg))
# part des reglages « contre » gagnants sur chaque moitie de l'echantillon complet de chaque marche
txt = []
for nom in MARCHES:
    g = [S[nom][k][0] for k in GRILLE if k[0] == "contre"]
    act = g[0].index[(pd.concat([x != 0 for x in g], axis=1).any(axis=1)).values]
    a, b = act[0], act[-1]; mil = a + (b - a) / 2
    txt.append("%s %d/%d" % (nom, sum(x[a:mil].sum() > 0 for x in g), sum(x[mil:].sum() > 0 for x in g)))
print("Reglages « contre » (24) gagnants moitie 1 / moitie 2 de l'echantillon : " + ", ".join(txt))
st = [n for n, v in RES.items() if v[0].iloc[:len(v[0]) // 2].sum() > 0 and v[0].iloc[len(v[0]) // 2:].sum() > 0]
print("Stables (hors echantillon > 0 sur les deux moities) : " + (", ".join(st) if st else "aucun"))
