"""Banc AT : y a-t-il d'AUTRES actifs ou une mecanique de TENDANCE (panier BlockTrend) tient sur longue periode ?
Meme mecanique que banc_blocktrend / bt_or mais a l'echelle JOURNALIERE (plus lente), historique long, univers large.
GRILLE FIXEE D'AVANCE (ecrite avant tout lancement, aucun ajout apres coup) - 24 reglages par actif :
  sens   : cloture contre EMA 50 / 100 / 200 jours ;  cotes : achats+ventes (un panier par cote) | achats seulement ;
  pyramide : 1 ou 3 positions (ajout de meme taille tous les 1 ATR(20 j) franchis a la cloture, niveau saute si la
             cloture est deja a plus d'un demi-pas au-dela) ;  stop : sortie de TOUT le panier au recul de 3 ATR
             (variante 2 ATR) depuis le meilleur prix (stop suiveur, = stop initial au depart).
  3 x 2 x 2 x 2 = 24 (le « ~12 » demande, doubles par la variante 2 ATR : les 24 entrent TOUS dans la correction).
  Reglage de reference (centre de grille, choisi d'avance pour les tableaux) : EMA 100, achats+ventes, pyramide 3, stop 3.
Deroulement journalier : (1) stop teste sur le bas/haut du jour avec le meilleur prix de la veille (prudent), sortie au
  niveau, ou a l'ouverture si le jour ouvre au-dela (trou) ; (2) meilleur prix mis a jour, ajouts a la cloture ;
  (3) entree a la cloture si pas de panier de ce cote (sens = cloture vs EMA). ATR(20) = moyenne des 20 derniers
  vrais ecarts des jours qui ONT un haut/bas (les jours « plats » h=l=c, cloture seule, sont exclus de l'ATR et le stop
  y est teste sur la cloture). Debut commun a tous les reglages : 220e bougie (EMA 200 valide).
Donnees : donnees/gj_*.csv.gz (OHLC journalier Yahoo) pour btc, eth, dax (>= 1994, avant : clotures seules), dj, eur,
  nas, nik (>= 1989, avant : clotures seules), oil, rut, sp, xag, xau (xau/xag : 15-50 % de jours sans haut/bas avant
  2011, ~10-20 % ensuite pour xag) ; fra et eu50 : bougies D1 du courtier (mt5/donnees/*_d1_5k, 2018/2020 -> 2026).
  Indices = prix SANS dividendes (un CFD acheteur recoit l'ajustement de dividende : penalise les achats ~1,5-2 %/an).
Couts (aller-retour, en fraction du prix, a chaque position) : max(spread median du courtier D1 hors zeros, plancher
  prudent). Le spread D1 du courtier est une seule photo par jour (52-74 % de zeros) d'ou le plancher.
  Planchers : indices 2 bp, or 3 bp, argent 5 bp, petrole 5 bp, euro 1 bp, crypto 10 bp. Courtier : xau 0,5, nas 0,3,
  sp 0,5, dj 0,2, ger(dax) 0,2, fra 1,0, eu50 2,2, us2000(rut) 1,1 bp -> seul eu50 depasse le plancher (2,24 bp).
Portage (swap) par nuit calendaire sur le notionnel : achats (taux 3 mois US (gj_irx) + 2,5 %)/365, ventes 2,5 %/365
  paye ; crypto : (taux + 10 %) achats, 10 % ventes (les CFD crypto paient bien plus). Resultats AVEC et SANS portage.
Unites : 1 R = perte d'une position au stop initial (taille = 1 R / distance du stop) ; risque 1 % du capital par R
  => R/an = % du capital par an (non compose). Series journalieres marquees a la cloture (latent compris).
Acheter-et-garder a risque egal : achat permanent a risque constant (1 position de taille 1/(3 ATR), reajustee chaque
  jour, portage acheteur compris), puis MIS A LA MEME VOLATILITE journaliere que la serie comparee (sur sa periode).
Mesures : par actif x reglage : R total, R/panier (t), R/an avec/sans portage, gain/pire baisse, % annees < 0,
  moities 1re/2de de l'historique, fenetre 08/2022-11/2026 (bt_or : ~ +0,16 R/panier, t 2,1).
  Walk-forward annuel : reglage au meilleur R/jour moyen (portage compris) sur tout le passe (>= 3 ans), rejoue l'annee
  suivante. Portefeuille = moyenne a risque egal (1 %/R par actif, divise par le nombre d'actifs actifs ce jour) des
  series walk-forward de chaque actif (principal) ; secondaire : un meme reglage pour tous, choisi sur le passe.
  Reality check de White studentise (bootstrap stationnaire, blocs moyens 20 j, 2000 tirages, graine 20261121) sur
  les 14 x 24 series journalieres portage compris, contre ZERO et contre ACHETER-ET-GARDER a risque egal ; p corrige
  par actif = part des tirages ou le max (sur TOUT l'ensemble) depasse le meilleur t de l'actif (une etape, prudent).
  Portefeuille : RC sur ses 24 reglages communs. But +10 %/mois : portefeuille WF dimensionne pour une pire baisse
  composee de -30 % (facteur choisi apres coup = optimiste), rendement/an, % mois < 0, correlation mensuelle a bt_or
  (bt_or H1 reconstruit par banc_mix.bt_or_jour, 08/2022-11/2026).
VERDICT (fixe d'avance) : « tient » = walk-forward hors echantillon > 0 sur ses DEUX moities, portage compris, ET bat
  acheter-et-garder a risque egal hors echantillon, ET p corrige < 0,10 contre zero ET contre acheter-et-garder ;
  « presque » = hors echantillon > 0 portage compris mais preuve mince ; sinon « ne tient pas ».
Sortie : donnees/tend_actifs.csv.   Usage : python3 banc_tend_actifs.py"""
import os, time, itertools, contextlib, io, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
DON, MT5 = os.path.join(ICI, "donnees"), os.path.join(ICI, "mt5", "donnees")
GRAINE, B, BLOC = 20261121, 2000, 20.0
FEN = (pd.Timestamp("2022-08-01"), pd.Timestamp("2026-11-30"))
GRILLE = list(itertools.product((50, 100, 200), ("AV", "A"), (1, 3), (3.0, 2.0)))
REF = (100, "AV", 3, 3.0)
# actif : (source, plancher de cout en bp, courtier pour le spread, debut OHLC, portage special)
ACTIFS = {"sp": ("gj", 2, "sp", None), "nas": ("gj", 2, "nas", None), "dj": ("gj", 2, "dj", None),
          "rut": ("gj", 2, "us2000", None), "dax": ("gj", 2, "ger", "1994-01-01"), "nik": ("gj", 2, None, "1989-01-01"),
          "fra": ("mt5", 2, "fra", None), "eu50": ("mt5", 2, "eu50", None), "xau": ("gj", 3, "xau", None),
          "xag": ("gj", 5, None, None), "oil": ("gj", 5, None, None), "eur": ("gj", 1, None, None),
          "btc": ("gj", 10, None, None), "eth": ("gj", 10, None, None)}
CRYPTO = {"btc", "eth"}
pd.set_option("display.width", 250)


def lit_mt5(ident):
    d = pd.read_csv(os.path.join(MT5, ident + "_d1_5k.csv.gz"))
    dec = max(len(("%.5f" % v).rstrip("0").split(".")[1]) for v in d["cloture"].iloc[:2000])
    d["date"] = pd.to_datetime(d.heure, unit="s").dt.normalize()
    d["sp_bp"] = d.spread_points * 10.0 ** (-dec) / d.cloture * 1e4
    return d.rename(columns={"ouverture": "open", "haut": "high", "bas": "low", "cloture": "close"})


def charge(nom):
    src, plancher, cour, deb, = ACTIFS[nom]
    if src == "gj":
        d = pd.read_csv(os.path.join(DON, "gj_%s.csv.gz" % nom), parse_dates=["date"])
    else:
        d = lit_mt5(cour)
    if deb:
        d = d[d.date >= deb]
    d = d.drop_duplicates("date").sort_values("date").reset_index(drop=True)
    sp_c = 0.0
    if cour:
        s = lit_mt5(cour).sp_bp
        sp_c = float(s[s > 0].median())
    return d[["date", "open", "high", "low", "close"]], max(plancher, sp_c), sp_c


IRX = pd.read_csv(os.path.join(DON, "gj_irx.csv.gz"), parse_dates=["date"]).set_index("date").close / 100


def prepare(nom):
    d, cout_bp, sp_c = charge(nom)
    c, h, l, o = (d[x].values.astype(float) for x in ("close", "high", "low", "open"))
    plat = h <= l
    pc = np.r_[np.nan, c[:-1]]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    trs = pd.Series(np.where(plat, np.nan, tr))
    atr = trs.dropna().rolling(20).mean().reindex(trs.index).ffill().values
    taux = IRX.reindex(pd.DatetimeIndex(d.date)).ffill().bfill().values  # taux connu au jour (Yahoo, meme date)
    taux = pd.Series(taux).ffill().fillna(0.0).values
    marge = 0.10 if nom in CRYPTO else 0.025
    nuits = np.r_[0, np.diff(d.date.values).astype("timedelta64[D]").astype(float)]
    return dict(d=d, c=c, h=h, l=l, o=o, atr=atr, nuits=nuits, rl=taux + marge, rs=np.full(len(c), marge),
                cout=cout_bp * 1e-4, cout_bp=cout_bp, sp_c=sp_c)


def simule(X, span, cotes, maxp, stopk, debut=220):
    c, h, l, o, atr, nuits = X["c"], X["h"], X["l"], X["o"], X["atr"], X["nuits"]
    ema = pd.Series(c).ewm(span=span, min_periods=span).mean().values
    n = len(c); ac = np.abs(c)
    gro, cos, car = np.zeros(n), np.zeros(n), np.zeros(n)
    sides = (1, -1) if cotes == "AV" else (1,)
    rate = {1: X["rl"], -1: X["rs"]}
    P, ouv = [], {}
    for i in range(debut, n):
        for s in list(ouv):
            p = ouv[s]; k = len(p["e"])
            cr = nuits[i] * rate[s][i - 1] / 365 * ac[i - 1] * k / p["stop"]
            car[i] += cr; p["car"] += cr
            niv = p["best"] - s * p["stop"]
            if (l[i] <= niv) if s > 0 else (h[i] >= niv):
                px = min(niv, o[i]) if s > 0 else max(niv, o[i])
                gro[i] += s * (px - c[i - 1]) * k / p["stop"]
                g = sum(s * (px - e) for e in p["e"]) / p["stop"]
                P.append((X["d"].date.iat[p["i"]], X["d"].date.iat[i], s, k, g, p["cos"], p["car"]))
                del ouv[s]
                continue
            gro[i] += s * (c[i] - c[i - 1]) * k / p["stop"]
            p["best"] = max(p["best"], h[i]) if s > 0 else min(p["best"], l[i])
            while len(p["e"]) < maxp and s * (c[i] - p["next"]) >= 0:
                if s * (c[i] - p["next"]) <= 0.5 * p["pas"]:
                    p["e"].append(c[i]); cc = X["cout"] * ac[i] / p["stop"]; cos[i] += cc; p["cos"] += cc
                p["next"] += s * p["pas"]
        if ema[i] == ema[i] and atr[i] == atr[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if s in sides and s not in ouv:
                st = stopk * atr[i]; cc = X["cout"] * ac[i] / st
                cos[i] += cc
                ouv[s] = {"i": i, "e": [c[i]], "best": c[i], "stop": st, "pas": atr[i], "next": c[i] + s * atr[i],
                          "cos": cc, "car": 0.0}
    idx = pd.DatetimeIndex(X["d"].date)
    net = pd.Series(gro - cos - car, idx).iloc[debut:]
    sans = pd.Series(gro - cos, idx).iloc[debut:]
    P = pd.DataFrame(P, columns=["d0", "d1", "s", "k", "g", "cos", "car"])
    P["net"] = P.g - P.cos - P.car; P["sans"] = P.g - P.cos
    return net, sans, P


def achat_garde(X, debut=220):
    c, atr = X["c"], X["atr"]
    u = 1 / (3 * atr[:-1])
    g = np.r_[0, (c[1:] - c[:-1]) * u - X["nuits"][1:] * X["rl"][:-1] / 365 * np.abs(c[:-1]) * u]
    return pd.Series(np.nan_to_num(g), pd.DatetimeIndex(X["d"].date)).iloc[debut:]


tst = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else 0.0


def creux(x):
    e = np.cumsum(np.asarray(x)); return (e - np.maximum.accumulate(np.r_[0, e])[1:]).min()


def ans(x):
    return max((x.index[-1] - x.index[0]).days / 365.25, 1e-9)


def a_vol(ref, x):
    """x mis a la volatilite journaliere de ref (sur les dates communes)."""
    x = x.reindex(ref.index).fillna(0.0)
    return x * (ref.std() / x.std() if x.std() > 0 else 0.0)


def wf(series, debut_min=3):
    """series : dict reglage -> serie journaliere nette. Rend serie hors echantillon + choix par annee."""
    df = pd.DataFrame(series)
    yrs = sorted(set(df.index.year))
    y0 = df.index[0] + pd.DateOffset(years=debut_min)
    out, choix = [], {}
    for y in yrs:
        if pd.Timestamp(y, 1, 1) < y0:
            continue
        app = df[df.index < pd.Timestamp(y, 1, 1)]
        k = app.mean().idxmax(); choix[y] = k
        out.append(df.loc[df.index.year == y, k])
    return (pd.concat(out) if out else pd.Series(dtype=float)), choix


rng = np.random.default_rng(GRAINE)


def boot_comptes(n, B=B, b=BLOC):
    for k in range(B):
        neuf = rng.random(n) < 1 / b; neuf[0] = True
        bl = np.cumsum(neuf) - 1; deb = np.flatnonzero(neuf)
        ii = (rng.integers(n, size=len(deb))[bl] + np.arange(n) - deb[bl]) % n
        yield np.bincount(ii, minlength=n)


def white_t(D):
    """D : (n, K) rendements (0 hors periode). Studentise. Rend t de chaque colonne et distribution du max bootstrap."""
    D = np.nan_to_num(D); n = len(D)
    mu, sd = D.mean(0), D.std(0); sd[sd == 0] = np.inf
    t = np.sqrt(n) * mu / sd
    Z = (D - mu) / sd  # recentre
    mx = np.empty(B); cpt = np.empty((100, n)); j = 0
    for k, cnt in enumerate(boot_comptes(n)):
        cpt[k % 100] = cnt
        if k % 100 == 99:
            mx[j:j + 100] = (cpt @ Z / n * np.sqrt(n)).max(1); j += 100
    return t, mx


def lig(x):
    return "%+7.1f" % x


if __name__ == "__main__":
    X, RES, BH, NET, SANS = {}, [], {}, {}, {}
    for nom in ACTIFS:
        X[nom] = prepare(nom)
        BH[nom] = achat_garde(X[nom])
        for g in GRILLE:
            net, sans, P = simule(X[nom], *g)
            NET[(nom, g)], SANS[(nom, g)] = net, sans
            RES.append((nom, g, P))
    print("Simulations : %.0f s" % (time.time() - T00))

    # ---------------- mesures par actif x reglage
    rows = []
    for nom, g, P in RES:
        net, sans = NET[(nom, g)], SANS[(nom, g)]
        a = ans(net); mid = net.index[0] + (net.index[-1] - net.index[0]) / 2
        bh = a_vol(net, BH[nom])
        yr = net.groupby(net.index.year).sum()
        Pf = P[(P.d1 >= FEN[0]) & (P.d1 <= FEN[1])]
        rows.append(dict(actif=nom, ema=g[0], cotes=g[1], pyr=g[2], stop=g[3], debut=net.index[0].date(),
                         fin=net.index[-1].date(), ans=round(a, 1), paniers=len(P), R_total=net.sum(),
                         R_sans_portage=sans.sum(), R_panier=P.net.mean(), t_panier=tst(P.net),
                         R_an=net.sum() / a, R_an_sans=sans.sum() / a, R_an_bh=bh.sum() / a, R_an_bh_brut=BH[nom].sum() / a,
                         gain_sur_creux=net.sum() / -creux(net) if creux(net) < 0 else np.nan,
                         pct_annees_neg=(yr < 0).mean() * 100, moitie1=net[net.index < mid].sum(),
                         moitie2=net[net.index >= mid].sum(), fen_R_panier=Pf.net.mean(), fen_t=tst(Pf.net),
                         fen_paniers=len(Pf), fen_R=net[(net.index >= FEN[0])].sum(),
                         fen_bh=bh[(bh.index >= FEN[0])].sum()))
    T = pd.DataFrame(rows)

    # ---------------- walk-forward par actif
    WF, CH = {}, {}
    for nom in ACTIFS:
        WF[nom], CH[nom] = wf({g: NET[(nom, g)] for g in GRILLE})

    # ---------------- reality check (actifs x reglages)
    U = sorted(set().union(*[s.index for s in NET.values()]))
    U = pd.DatetimeIndex(U)
    cols = [(nom, g) for nom in ACTIFS for g in GRILLE]
    D0 = np.column_stack([NET[k].reindex(U).fillna(0).values for k in cols])
    D1 = np.column_stack([(NET[k] - a_vol(NET[k], BH[k[0]])).reindex(U).fillna(0).values for k in cols])
    t0, mx0 = white_t(D0)
    t1, mx1 = white_t(D1)
    print("Reality check : %.0f s" % (time.time() - T00))
    T["t_jour_vs0"] = t0; T["t_jour_vsBH"] = t1
    pc0, pc1 = {}, {}
    for j, nom in enumerate(ACTIFS):
        sl = slice(j * len(GRILLE), (j + 1) * len(GRILLE))
        pc0[nom] = (mx0 >= t0[sl].max()).mean(); pc1[nom] = (mx1 >= t1[sl].max()).mean()
    p_glob0, p_glob1 = (mx0 >= t0.max()).mean(), (mx1 >= t1.max()).mean()

    # ---------------- tableau par actif
    print("\nReglage de reference EMA100 / achats+ventes / pyr 3 / stop 3 ATR (R ; 1 R = 1 % du capital) et walk-forward (WF)")
    print("%-5s %-9s %5s %6s %5s %7s %7s %7s %6s %6s %6s %5s | %7s %7s %7s %7s %5s %5s  %s" % (
        "actif", "periode", "pan", "R/pan", "t", "R/an", "sansP", "BH/an", "g/crx", "m1", "m2", "%a<0",
        "WF R/an", "WF BH", "WF m1", "WF m2", "p0", "pBH", "verdict"))
    VER, wfrows = {}, []
    for nom in ACTIFS:
        r = T[(T.actif == nom) & (T.ema == REF[0]) & (T.cotes == REF[1]) & (T.pyr == REF[2]) & (T.stop == REF[3])].iloc[0]
        w = WF[nom]
        if len(w) < 250:
            v, wa, wb, m1, m2 = "trop court", np.nan, np.nan, np.nan, np.nan
        else:
            aw = ans(w); midw = w.index[0] + (w.index[-1] - w.index[0]) / 2
            bw = a_vol(w, BH[nom])
            wa, wb = w.sum() / aw, bw.sum() / aw
            m1, m2 = w[w.index < midw].sum(), w[w.index >= midw].sum()
            if m1 > 0 and m2 > 0 and wa > wb and pc0[nom] < 0.10 and pc1[nom] < 0.10:
                v = "tient"
            elif w.sum() > 0:
                v = "presque"
            else:
                v = "ne tient pas"
        VER[nom] = v
        wfrows.append(dict(actif=nom, ema="WF", cotes="", pyr=np.nan, stop=np.nan, debut=w.index[0].date() if len(w) else None,
                           fin=w.index[-1].date() if len(w) else None, R_an=wa, R_an_bh=wb, moitie1=m1, moitie2=m2,
                           p_corr_vs0=pc0[nom], p_corr_vsBH=pc1[nom], verdict=v,
                           choix=";".join("%d:%s" % (y, "/".join(map(str, k))) for y, k in CH[nom].items())))
        print("%-5s %4d-%2s %5d %+6.2f %5.1f %+7.1f %+7.1f %+7.1f %6.2f %+6.0f %+6.0f %5.0f | %+7.1f %+7.1f %+7.0f %+7.0f %5.2f %5.2f  %s" % (
            nom, r.debut.year, str(r.fin.year)[2:], r.paniers, r.R_panier, r.t_panier, r.R_an, r.R_an_sans, r.R_an_bh,
            r.gain_sur_creux, r.moitie1, r.moitie2, r.pct_annees_neg, wa, wb, m1, m2, pc0[nom], pc1[nom], v))
    print("RC global (24 x %d series) : meilleur t contre zero %.2f (%s) p = %.3f ; contre acheter-et-garder %.2f (%s) p = %.3f" % (
        len(ACTIFS), t0.max(), cols[int(t0.argmax())], p_glob0, t1.max(), cols[int(t1.argmax())], p_glob1))

    print("\nMeilleur reglage EN ECHANTILLON par actif (indicatif, biaise) et fenetre 08/2022-11/2026 du reglage de reference :")
    for nom in ACTIFS:
        s = T[T.actif == nom].sort_values("R_an", ascending=False).iloc[0]
        r = T[(T.actif == nom) & (T.ema == REF[0]) & (T.cotes == REF[1]) & (T.pyr == REF[2]) & (T.stop == REF[3])].iloc[0]
        print("  %-5s meilleur %3d/%-2s/p%d/s%.0f : %+6.1f R/an (sans portage %+6.1f, BH meme vol %+6.1f) t_jour %.1f | fenetre ref : %3d paniers %+5.2f R/pan t %4.1f, %+5.0f R vs BH %+5.0f" % (
            nom, s.ema, s.cotes, s.pyr, s.stop, s.R_an, s.R_an_sans, s.R_an_bh, s.t_jour_vs0,
            r.fen_paniers, r.fen_R_panier, r.fen_t, r.fen_R, r.fen_bh))

    # ---------------- portefeuille
    def porte(dct):
        df = pd.DataFrame(dct).reindex(U)
        act = df.notna().sum(1).replace(0, np.nan)
        return (df.fillna(0).sum(1) / act).fillna(0.0)
    BHP = porte(BH)
    PW = porte({n: WF[n] for n in ACTIFS if len(WF[n])})
    PW = PW[PW.index >= min(WF[n].index[0] for n in ACTIFS if len(WF[n]))]
    PG = {g: porte({n: NET[(n, g)] for n in ACTIFS}) for g in GRILLE}
    PGs = {g: porte({n: SANS[(n, g)] for n in ACTIFS}) for g in GRILLE}
    PW2, CH2 = wf(PG)
    tp0, mxp0 = white_t(np.column_stack([PG[g].values for g in GRILLE]))
    tp1, mxp1 = white_t(np.column_stack([(PG[g] - a_vol(PG[g], BHP)).values for g in GRILLE]))
    pp0, pp1 = (mxp0 >= tp0.max()).mean(), (mxp1 >= tp1.max()).mean()

    def bilan(nom, w):
        aw = ans(w); midw = w.index[0] + (w.index[-1] - w.index[0]) / 2
        bw = a_vol(w, BHP)
        m = w.resample("ME").sum(); m = m[m != 0]
        print("  %-30s %s-%s : %+6.2f R/an (BH meme vol %+6.2f) | moities %+5.0f / %+5.0f | creux %5.0f R | mois<0 %3.0f %% | t %4.1f" % (
            nom, w.index[0].year, w.index[-1].year, w.sum() / aw, bw.sum() / aw, w[w.index < midw].sum(),
            w[w.index >= midw].sum(), creux(w), (m < 0).mean() * 100, tst(w)))
        return w.sum() / aw, bw.sum() / aw, w[w.index < midw].sum(), w[w.index >= midw].sum()
    print("\nPortefeuille a risque egal (moyenne des actifs actifs, 1 %/R par actif / N) :")
    ref = PG[REF]; bilan("reglage de reference", ref); bilan("ref sans portage", PGs[REF])
    bilan("acheter-et-garder (risque egal)", BHP[BHP.index >= ref.index[0]])
    wa, wb, m1, m2 = bilan("WF par actif (principal)", PW)
    bilan("WF reglage commun", PW2)
    dif = PW - a_vol(PW, BHP)
    print("  WF par actif moins acheter-et-garder meme vol : %+.2f R/an, t %.1f" % (dif.sum() / ans(dif), tst(dif)))
    bilan("WF par actif 2016-2026", PW[PW.index >= "2016-01-01"])
    bilan("WF par actif 08/2022-11/2026", PW[PW.index >= FEN[0]])
    bilan("(indicatif) WF sans crypto", porte({n: WF[n] for n in ACTIFS if len(WF[n]) and n not in CRYPTO}).loc[PW.index[0]:])
    print("  RC portefeuille (24 reglages communs) : t max %.2f p = %.3f contre zero ; %.2f p = %.3f contre acheter-et-garder" % (
        tp0.max(), pp0, tp1.max(), pp1))
    if m1 > 0 and m2 > 0 and wa > wb and pp0 < 0.10 and pp1 < 0.10:
        VP = "tient"
    elif PW.sum() > 0:
        VP = "presque"
    else:
        VP = "ne tient pas"
    print("  VERDICT portefeuille : %s" % VP)

    # dimensionnement -30 % (compose) sur WF
    r = PW / 100.0
    def dd(k):
        e = np.cumprod(1 + k * r.values); return (e / np.maximum.accumulate(e) - 1).min()
    lo, hi = 0.0, 50.0
    for _ in range(60):
        mi = (lo + hi) / 2
        if dd(mi) > -0.30: lo = mi
        else: hi = mi
    k = lo; e = np.cumprod(1 + k * r.values)
    an = e[-1] ** (1 / ans(PW)) - 1
    rm = pd.Series(k * r.values, PW.index).resample("ME").apply(lambda x: (1 + x).prod() - 1)
    print("  WF par actif dimensionne pour pire baisse -30 %% : levier x%.1f (1 R = %.1f %%), %+.1f %%/an compose (%.2f %%/mois), mois<0 %.0f %%" % (
        k, k, an * 100, ((1 + an) ** (1 / 12) - 1) * 100, (rm < 0).mean() * 100))
    corr = np.nan
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            import banc_bt_regulier as BR, banc_jumeau as BJ, banc_mix as BM
        dh = BR.charge("xau_h1_50k"); dh = dh[dh.heure >= BM.DEB.timestamp()].reset_index(drop=True)
        xb, _, _ = BM.bt_or_jour(dh, dict(span=48, heures=BJ.H_H1, debut=60))
        mb = xb.resample("ME").sum(); mp = PW.resample("ME").sum().reindex(mb.index)
        corr = mb.corr(mp)
        mpr = PG[REF].resample("ME").sum().reindex(mb.index)
        print("  Correlation mensuelle avec bt_or H1 (%s-%s, %d mois) : WF %.2f ; reglage ref %.2f" % (
            mb.index[0].date(), mb.index[-1].date(), len(mb), corr, mb.corr(mpr)))
        for nom in ACTIFS:
            if len(WF[nom]):
                print("     %s %.2f" % (nom, mb.corr(WF[nom].resample("ME").sum().reindex(mb.index).fillna(0))), end="")
        print()
    except Exception as ex:
        print("  bt_or non reconstruit :", ex)

    wfrows.append(dict(actif="PORTEFEUILLE", ema="WF", R_an=wa, R_an_bh=wb, moitie1=m1, moitie2=m2, p_corr_vs0=pp0,
                       p_corr_vsBH=pp1, verdict=VP, levier_dd30=k, rend_an_dd30=an, corr_bt_or=corr))
    T["verdict_actif"] = T.actif.map(VER)
    out = pd.concat([T, pd.DataFrame(wfrows)], ignore_index=True)
    out.round(4).to_csv(os.path.join(DON, "tend_actifs.csv"), index=False)
    print("\nEcrit donnees/tend_actifs.csv (%d lignes). Duree %.0f s" % (len(out), time.time() - T00))
