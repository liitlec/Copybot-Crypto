"""Banc grande_journee : le contre-pied d'une grande journee (regle rebond_nas) etendu a 12 marches.
Piste PRIORITES 17/11 17 h, point 1. Regle de base (rebond_nas, banc_vol_retour.py) : amplitude du jour J =
(haut - bas) / cloture J-1 ; si > m x mediane des 20 jours precedents, position CONTRE le mouvement du jour J
(signe de cloture J - cloture J-1), entree a l'ouverture J+1, sortie a la cloture J+h-1+1 (h = tenue en jours).

Donnees (copies legeres dans donnees/gj_*.csv.gz, dates = jour de la bourse du marche) : Yahoo journalier long
  nas ^NDX (reference deja prouvee), sp ^GSPC, dj ^DJI, rut ^RUT, dax ^GDAXI, nik ^N225, btc BTC-USD, eth ETH-USD,
  oil CL=F, xag SI=F, et deux temoins xau GC=F, eur EURUSD=X ; taux 3 mois ^IRX pour le financement.
  Ouvertures douteuses ECARTEES (pas d'entree ces jours-la) : ouverture = cloture de la veille (sauf crypto et euro,
  marches continus), ouverture hors [bas, haut], bougie sans amplitude, et toute ANNEE ou plus de 3 % des jours ont
  ouverture = cloture de la veille (vieilles bougies Yahoo : S&P avant 2008 et 2013, Nasdaq avant 1999, Russell avant
  2007, Dow plusieurs annees...). NB : l'ouverture Yahoo d'un indice au comptant (9 h 30 New York) est en partie
  perimee (valeurs pas encore cotees) : elle peut gonfler un gain de rebond ; d'ou le controle courtier. Contrats a
  terme (petrole, argent, or) : seuls les jours ouverture = cloture de la veille sont ecartes (egalite fortuite
  frequente, pas -> annee entiere). EURUSD=X : depuis 2011 la bougie Yahoo a cloture = ouverture (meme instant) ; on
  prend donc l'euro depuis 2011 avec cloture J := ouverture J+1 (marche continu). Prix <= 0 (petrole avril 2020) ecartes. Controle sur les bougies D1 du COURTIER (nas, sp, dj, us2000,
  ger, xau ; 2018/2020 -> 2026 ; ouverture = debut de la journee serveur, verifiee contre la 1re bougie M5).
Couts aller-retour (bp du notionnel) = max(spread median du courtier en M5/M1 + 0,5 bp de glissement, plancher
  prudent) ; planchers : indices 1 (Russell 1,5, Nikkei 2 : pas de M5), crypto 5, petrole/argent 3, or/euro 1 ;
  + financement (taux 3 mois + 2,5 %)/360 par nuit calendaire tenue (tenue > 1 jour), dans les deux sens.

Plan fixe d'avance :
 (a) MEME reglage fige partout : m = 1,5, mediane 20 j, contre, tenue 1 jour, deux sens (N = 12 marches, aucun
     reglage par marche). Par marche : trades, bp/trade, t, deux moities, temoin (2000 tirages d'entrees au hasard,
     meme nombre, meme tenue, memes sens, jours d'ouverture valide), Bonferroni sur 12 ; reality check de White sur
     les 12 series ; portefeuille poids egaux des 9 marches nouveaux (hors nas et temoins).
 (b) Par marche, petite grille : seuil m = 1,5 / 2 / 2,5 x tenue 1 / 2 / 3 jours x {deux sens, achats seuls}, sens
     contre (18 reglages par marche, N = 216 en tout). Walk-forward : apprentissage 5 ans glissants (annees civiles),
     test 1 an ; on retient le reglage au meilleur t (gain par jour, gains comptes au jour de sortie) s'il a >= 10
     trades et t > 0, sinon rien cette annee. Pas de chevauchement (nouveau signal ignore tant qu'on est en position).
     Reality check de White sur les 216 series (bootstrap stationnaire, blocs moyens 10 j, 1000 tirages) + Bonferroni.
 Verdict (par marche, sur ses trades hors echantillon) : TIENT = moyenne > 0, t >= seuil de Bonferroni (N = 12 :
 2,87 en (a) ; N = 12 marches en (b) car le walk-forward a deja integre le choix, et RC des 216 < 0,05), les deux
 moities > 0 et p temoin < 0,05 ; PRESQUE = moyenne > 0, t >= 1,5, les deux moities > 0 ; sinon NE TIENT PAS.
Sorties : donnees/rebonds_grande_journee.csv (trades hors echantillon des regles TIENT/PRESQUE : (a) toute la
 periode sauf nas, qui a servi a fixer le reglage ; (b) trades du walk-forward), donnees/rebonds_grande_journee_tout.csv
 (toute la periode au reglage retenu) ; correlations journalieres des marches qui tiennent.
Usage : python3 banc_grande_journee.py   (moins d'une minute ; donnees en cache, sinon telechargees)"""
import os, json, time, urllib.request, warnings
warnings.filterwarnings("ignore")
from statistics import NormalDist
import numpy as np, pandas as pd
import banc_or as B
from banc_or_dollar_taux import lire, tstat, boot_idx

ICI = os.path.dirname(os.path.abspath(__file__))
DON = os.path.join(ICI, "donnees")
TK = {"nas": "^NDX", "sp": "^GSPC", "dj": "^DJI", "rut": "^RUT", "dax": "^GDAXI", "nik": "^N225",
      "btc": "BTC-USD", "eth": "ETH-USD", "oil": "CL=F", "xag": "SI=F", "xau": "GC=F", "eur": "EURUSD=X"}
TEMOINS, REF = ("xau", "eur"), "nas"
CONTINU = ("btc", "eth", "eur")
COMPTANT = ("nas", "sp", "dj", "rut", "dax", "nik")
# spread courtier (fichier M5/M1) et plancher prudent, bp aller-retour
SPREAD = {"nas": ("nas_m5_90k", 1), "sp": ("sp_m5_90k", 1), "dj": ("dj_m5_90k", 1), "rut": (None, 1.5),
          "dax": ("ger_m1_90k", 1), "nik": (None, 2), "btc": ("btc_m5_90k", 5), "eth": ("eth_m5_90k", 5),
          "oil": (None, 3), "xag": ("xag_m5_90k", 3), "xau": ("xau_m5_90k", 1), "eur": ("eur_m5_90k", 1)}
COURTIER = {"nas": "nas", "sp": "sp", "dj": "dj", "rut": "us2000", "dax": "ger", "xau": "xau"}
SEUILS, TENUES, SENS = (1.5, 2, 2.5), (1, 2, 3), ("deux", "achats")
FIGE = (1.5, 1, "deux")
APP = 5
rng = np.random.default_rng(17)


def yahoo(tk):
    url = ("https://query2.finance.yahoo.com/v8/finance/chart/%s?interval=1d&period1=0&period2=%d"
           % (urllib.request.quote(tk), int(time.time())))
    r = json.loads(lire(url))["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    ix = pd.to_datetime(r["timestamp"], unit="s", utc=True).tz_convert(r["meta"]["exchangeTimezoneName"])
    d = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")}, index=ix.tz_localize(None).normalize())
    return d.dropna()[lambda x: ~x.index.duplicated(keep="last")]


def charge(n, tk):
    f = os.path.join(DON, "gj_%s.csv.gz" % n)
    if not os.path.exists(f):
        d = yahoo(tk)
        d = d[d.index < pd.Timestamp.today().normalize()]
        d.to_csv(f, float_format="%.6g", index_label="date")
        time.sleep(0.5)
    return pd.read_csv(f, index_col=0, parse_dates=True)


def prepare(d, n):
    """Ajoute amplitude, mediane, mouvement et validite de l'ouverture."""
    d = d.copy()
    if n == "eur":            # bougies Yahoo EURUSD=X : cloture = ouverture (meme instant) depuis 2011 -> prix = ouvertures
        d = d[d.index >= "2011-01-01"]
        d["close"] = d["open"].shift(-1)
        d = d.dropna()
    pos = (d[["open", "high", "low", "close"]] > 0).all(1)
    d = d[pos]
    pc = d["close"].shift(1)
    a = (d["high"] - d["low"]) / pc
    a = a.where((d["high"] > d["low"]) & (a < 0.5))
    d["amp"], d["med"] = a, a.rolling(20, min_periods=15).median().shift(1)
    d["mv"] = np.sign(d["close"] - pc)
    eq = (d["open"] - pc).abs() <= 1e-9 * d["close"]
    ok = (d["open"] <= d["high"] * 1.0001) & (d["open"] >= d["low"] * 0.9999) & (d["high"] > d["low"])
    if n in COMPTANT:
        mauvais = eq.groupby(d.index.year).transform("mean") > 0.03       # annee entiere douteuse
        ok &= ~eq & ~mauvais
    elif n not in CONTINU:
        ok &= ~eq                                                         # contrats a terme : jour par jour
    trou = (d.index.to_series().diff().dt.days > 6).values                 # trou de donnees : pas d'entree
    d["okopen"] = ok & ~trou
    return d


def cout_bp(n):
    f, plancher = SPREAD[n]
    if f is None:
        return float(plancher)
    x, _ = B.charge(f)
    return max(float((x["sp"] / x["cloture"] * 1e4).median()) + 0.5, plancher)


def financement(irx, dates):
    r = irx["close"].reindex(dates, method="ffill").bfill().fillna(3.0).values
    return (r / 100 + 0.025) / 360                                          # par nuit, fraction


def simule(d, m, h, sens, cout, fin):
    """Trades sans chevauchement. Rend DataFrame entree, sortie, sens, r (fraction apres couts), brut."""
    o, c = d["open"].values, d["close"].values
    sig = (d["amp"] > m * d["med"]).values
    mv, ok, ix = d["mv"].values, d["okopen"].values, d.index
    T, libre = [], 0
    for j in np.flatnonzero(sig):
        e, x = j + 1, j + h
        if e < libre or x >= len(d) or not ok[e]:
            continue
        s = -mv[j]
        if s == 0 or (sens == "achats" and s < 0):
            continue
        nuits = (ix[x] - ix[e]).days
        brut = s * (c[x] / o[e] - 1)
        T.append((ix[e], ix[x], int(s), brut - cout / 1e4 - nuits * fin[e], brut))
        libre = x + 1
    return pd.DataFrame(T, columns=["entree", "sortie", "sens", "r", "brut"])


def journalier(T, ix):
    return (T.groupby("sortie")["r"].sum() * 1e4).reindex(ix, fill_value=0.0) if len(T) else pd.Series(0.0, ix)


def temoin(d, T, h_de, cout, fin, tirages=2000):
    """Entrees au hasard : meme nombre, memes tenues et sens, jours d'ouverture valide des memes annees."""
    if len(T) == 0:
        return np.nan, np.nan
    o, c, ix = d["open"].values, d["close"].values, d.index
    ans = set(pd.DatetimeIndex(T["entree"]).year)
    tot = np.zeros(tirages)
    for h, grp in T.groupby(h_de):
        cand = np.flatnonzero(d["okopen"].values & np.isin(ix.year, list(ans)))
        cand = cand[cand + h - 1 < len(d)]
        g = c[cand + h - 1] / o[cand] - 1
        nuits = (ix[cand + h - 1] - ix[cand]).days.values
        tir = rng.integers(len(cand), size=(tirages, len(grp)))
        tot += (grp["sens"].values * g[tir] - cout / 1e4 - nuits[tir] * fin[cand][tir]).sum(1)
    return tot.mean() / len(T) * 1e4, (tot >= T["r"].sum()).mean()


def stats(T):
    if len(T) < 3:
        return dict(n=len(T), bp=np.nan, t=0.0, m1=np.nan, m2=np.nan, brut=np.nan)
    r = T["r"].values * 1e4
    k = len(r) // 2
    return dict(n=len(r), bp=r.mean(), t=tstat(pd.Series(r)), m1=r[:k].mean(), m2=r[k:].mean(),
                brut=T["brut"].mean() * 1e4)


def verdict(s, pt, tb, rc_ok=True):
    if s["n"] >= 10 and s["bp"] > 0 and s["t"] >= tb and s["m1"] > 0 and s["m2"] > 0 and pt < 0.05 and rc_ok:
        return "TIENT"
    if s["n"] >= 10 and s["bp"] > 0 and s["t"] >= 1.5 and s["m1"] > 0 and s["m2"] > 0:
        return "PRESQUE"
    return "NE TIENT PAS"


def white(M, tirages=1000):
    """Reality check studentise (chaque serie divisee par son ecart-type, facon SPA de Hansen) : p du meilleur t."""
    n = len(M); mu = M.mean(0); sd = M.std(0) + 1e-12; V = (np.sqrt(n) * mu / sd).max()
    Vb = np.array([(np.sqrt(n) * (M[boot_idx(rng, n)].mean(0) - mu) / sd).max() for _ in range(tirages)])
    return (Vb >= V).mean(), int((mu / sd).argmax())


def courtier(n, m, h, sens, cout, irx):
    """Meme regle sur les bougies D1 du courtier (ouverture = debut de la journee serveur)."""
    x, _ = B.charge("%s_d1_5k" % COURTIER[n])
    d = pd.DataFrame({"open": x["ouverture"].values, "high": x["haut"].values, "low": x["bas"].values,
                      "close": x["cloture"].values}, index=x.index.normalize())
    d = prepare(d, "btc")                                    # ouvertures du courtier = cotations reelles
    d["okopen"] &= ~((d["open"] - d["close"].shift(1)).abs() < 1e-9)
    return simule(d, m, h, sens, cout, financement(irx, d.index)), d


def verif_ouvertures():
    """Ouverture D1 du courtier = ouverture de la 1re bougie M5 du jour serveur ? (fraction des jours communs)."""
    out = []
    for n, f in (("nas", "nas"), ("sp", "sp"), ("dj", "dj"), ("xau", "xau")):
        x, _ = B.charge("%s_d1_5k" % f); m5, _ = B.charge("%s_m5_90k" % f)
        p = m5.groupby(m5.index.normalize())["ouverture"].first()
        o = x.set_index(x.index.normalize())["ouverture"]
        c = o.index.intersection(p.index)[1:]
        ecart = ((o[c] - p[c]).abs() / o[c] * 1e4)
        out.append("%s %.0f %% egales, ecart median %.2f bp (%d j)" % (n, 100 * (ecart < 0.01).mean(), ecart.median(), len(c)))
    return " ; ".join(out)


def main():
    t0 = time.time()
    irx = charge("irx", "^IRX")
    D, C, FIN = {}, {}, {}
    for n, tk in TK.items():
        D[n] = prepare(charge(n, tk), n)
        C[n] = cout_bp(n)
        FIN[n] = financement(irx, D[n].index)
    print("== Donnees (Yahoo journalier ; entrees permises = ouverture valide) et couts aller-retour ==")
    for n in TK:
        d = D[n]; v = d.index[d["okopen"].values]
        print("  %-4s %s -> %s, %5d j, ouvertures valides %5d (des %s), cout %.2f bp%s" % (
            n, d.index[0].date(), d.index[-1].date(), len(d), len(v), v[0].date(), C[n],
            " (temoin)" if n in TEMOINS else (" (reference deja prouvee)" if n == REF else "")))
    print("  verification des ouvertures D1 du courtier : " + verif_ouvertures())

    # ---------------------------------------------------------------- simulations de toute la grille
    G = {}
    for n in TK:
        for m in SEUILS:
            for h in TENUES:
                for s in SENS:
                    G[(n, m, h, s)] = simule(D[n], m, h, s, C[n], FIN[n])
    cal = pd.DatetimeIndex(sorted(set().union(*[set(D[n].index) for n in TK])))
    cal = cal[cal >= "1990-01-01"]
    tb12 = NormalDist().inv_cdf(1 - 0.025 / 12)

    # ---------------------------------------------------------------- (a) reglage fige
    print("\n== (a) MEME reglage fige partout : m = 1,5, contre, tenue 1 jour, deux sens (N = 12, Bonferroni t >= %.2f) ==" % tb12)
    Ma = np.column_stack([journalier(G[(n,) + FIGE], cal).values for n in TK])
    pa, _ = white(Ma)
    print("  reality check de White sur les 12 marches : p = %.3f" % pa)
    print("  %-4s %-23s %5s %7s %6s %5s %15s %7s %16s %s" % ("", "periode des trades", "trad", "bp/tr", "brut", "t",
          "moities bp", "achats", "temoin bp (p)", "verdict"))
    VA, res_a = {}, {}
    for n in TK:
        T = G[(n,) + FIGE]; s = stats(T)
        tm, pt = temoin(D[n], T, lambda i: 1, C[n], FIN[n])
        ach = T[T.sens > 0]["r"].mean() * 1e4
        VA[n] = verdict(s, pt, tb12)
        res_a[n] = (s, tm, pt)
        print("  %-4s %s -> %s %5d %+7.1f %+6.1f %+5.1f %+7.1f/%+6.1f %+7.1f %+7.1f (%.3f) %s" % (
            n, T.entree.iloc[0].date(), T.entree.iloc[-1].date(), s["n"], s["bp"], s["brut"], s["t"], s["m1"], s["m2"],
            ach, tm, pt, VA[n]))
    nouveaux = [n for n in TK if n not in TEMOINS and n != REF]
    pf = pd.DataFrame({n: journalier(G[(n,) + FIGE], cal) for n in nouveaux})
    act = (pf != 0).sum(1)
    pfj = pf.sum(1) / len(nouveaux)
    tt = pd.concat([G[(n,) + FIGE].assign(m=n) for n in nouveaux])
    k = len(pfj) // 2
    print("  portefeuille poids egaux des %d nouveaux marches (%s) : %d trades, %+.1f bp/trade, t journalier %+.2f, "
          "moities %+.0f / %+.0f bp cumules, jours avec >= 3 marches en position simultanee : %.0f %%"
          % (len(nouveaux), " ".join(nouveaux), len(tt), tt.r.mean() * 1e4, tstat(pfj[pfj.index >= "2000"]),
             pfj.iloc[:k].sum(), pfj.iloc[k:].sum(), 100 * (act >= 3).sum() / max((act >= 1).sum(), 1)))

    # ---------------------------------------------------------------- (b) grille par marche en walk-forward
    cles = list(G)
    print("\n== (b) Grille par marche (18 reglages x 12 marches = 216), walk-forward %d ans / 1 an ==" % APP)
    M = np.column_stack([journalier(G[c], cal).values for c in cles]).astype(np.float32)
    pb, ib = white(M)
    tb216 = NormalDist().inv_cdf(1 - 0.025 / 216)
    print("  reality check de White sur les 216 reglages : p = %.3f (meilleur sur tout l'echantillon : %s %s %s %s, "
          "%+.1f bp/trade, t %+.1f) ; Bonferroni N = 216 : t >= %.2f" % (
              pb, *cles[ib], stats(G[cles[ib]])["bp"], stats(G[cles[ib]])["t"], tb216))
    print("  %-4s %-11s %5s %7s %5s %15s %16s %-22s %-24s %s" % ("", "test", "trad", "bp/tr", "t", "moities bp",
          "temoin bp (p)", "choix (frequence)", "retenu pour demain", "verdict"))
    OOS, VB, RET = {}, {}, {}
    for n in TK:
        d = D[n]; jix = d.index
        ser = {c: journalier(G[c], jix) for c in cles if c[0] == n}
        ntr = {c: G[c] for c in ser}
        valides = jix[d["okopen"].values]
        an0 = valides[0].year + (1 if valides[0].month > 1 else 0)
        rows, choix = [], []
        for y in range(an0 + APP, jix[-1].year + 2):
            a = (jix.year >= y - APP) & (jix.year < y)
            best, bt = None, 0.0
            for c in ser:
                T = ntr[c]; na = ((T.sortie.dt.year >= y - APP) & (T.sortie.dt.year < y)).sum()
                tv = tstat(ser[c][a])
                if na >= 10 and tv > bt:
                    best, bt = c, tv
            if y == jix[-1].year + 1:
                RET[n] = best
                break
            choix.append(best)
            if best is not None:
                T = ntr[best]; rows.append(T[T.entree.dt.year == y].assign(h=best[2], cfg="%g/%d/%s" % best[1:]))
        T = pd.concat(rows) if rows else pd.DataFrame(columns=["entree", "sortie", "sens", "r", "brut", "h", "cfg"])
        OOS[n] = T
        s = stats(T)
        tm, pt = temoin(d, T, "h", C[n], FIN[n]) if len(T) else (np.nan, np.nan)
        VB[n] = verdict(s, pt, tb12, rc_ok=pb < 0.05)
        fq = pd.Series(["%g/%d/%s" % c[1:] if c else "rien" for c in choix]).value_counts()
        ret = "%g/%d/%s" % RET[n][1:] if RET.get(n) else "rien"
        print("  %-4s %d->%d %5d %+7.1f %+5.1f %+7.1f/%+6.1f %+7.1f (%.3f) %-22s %-24s %s" % (
            n, an0 + APP, jix[-1].year, s["n"], s["bp"], s["t"], s["m1"], s["m2"], tm, pt,
            "%s (%d/%d)" % (fq.index[0], fq.iloc[0], len(choix)), ret, VB[n]))
    tout = pd.concat([OOS[n].assign(m=n) for n in TK if len(OOS[n])])
    tn = tout[tout.m.isin(nouveaux)]
    print("  tous marches nouveaux, hors echantillon : %d trades, %+.1f bp/trade, t %+.2f" % (
        len(tn), tn.r.mean() * 1e4, tstat(tn.r)))

    # ---------------------------------------------------------------- controle sur le courtier
    print("\n== Controle sur les bougies D1 du courtier (spread = cout ci-dessus) ==")
    for n in COURTIER:
        for lab, cfg in (("fige", FIGE), ("retenu", RET.get(n))):
            if cfg is None:
                continue
            T, d = courtier(n, *cfg[-3:], C[n], irx); s = stats(T)
            ga = T.groupby(T.entree.dt.year)["r"].sum()
            Y = G[(n,) + tuple(cfg[-3:])]; Y = Y[(Y.entree >= d.index[0]) & (Y.entree <= d.index[-1])]
            print("  %-4s %-6s %-14s %s -> %s : %4d trades, %+6.1f bp/trade, t %+5.2f, moities %+6.1f / %+6.1f, annees > 0 : %d/%d"
                  " | Yahoo meme periode %4d trades %+6.1f bp" % (
                n, lab, "%g/%d/%s" % cfg[1:] if lab == "retenu" else "1.5/1/deux", d.index[0].date(), d.index[-1].date(),
                s["n"], s["bp"], s["t"], s["m1"], s["m2"], (ga > 0).sum(), len(ga), len(Y), Y.r.mean() * 1e4))

    # ---------------------------------------------------------------- sorties
    lig, lig_tout = [], []
    for n in TK:
        if VA[n] in ("TIENT", "PRESQUE"):
            T = G[(n,) + FIGE]
            lig_tout.append(T.assign(regle="gj_fige", marche=n))
            if n != REF:
                lig.append(T.assign(regle="gj_fige", marche=n))
        if VB[n] in ("TIENT", "PRESQUE"):
            lig.append(OOS[n].assign(regle="gj_wf", marche=n))
            if RET.get(n) and not (RET[n][1:] == FIGE and VA[n] in ("TIENT", "PRESQUE")):
                lig_tout.append(G[RET[n]].assign(regle="gj_wf_%g_%d_%s" % RET[n][1:], marche=n))
    col = ["regle", "marche", "entree", "sortie", "sens", "r"]
    for L, f in ((lig, "rebonds_grande_journee.csv"), (lig_tout, "rebonds_grande_journee_tout.csv")):
        X = pd.concat(L)[col] if L else pd.DataFrame(columns=col)
        if len(X):
            X["entree"] = pd.to_datetime(X["entree"]).dt.strftime("%Y-%m-%d")
            X["sortie"] = pd.to_datetime(X["sortie"]).dt.strftime("%Y-%m-%d")
        X.sort_values(["regle", "marche", "entree"]).to_csv(os.path.join(DON, f), index=False, float_format="%.6f")
        print("  ecrit donnees/%s : %d trades" % (f, len(X)))

    # ---------------------------------------------------------------- correlations
    tiennent = [n for n in TK if VA[n] in ("TIENT", "PRESQUE") or VB[n] in ("TIENT", "PRESQUE")]
    print("\n== Correlations journalieres (regle figee, toute la periode, gain au jour d'entree) : %s ==" % " ".join(tiennent))
    if len(tiennent) >= 2:
        P = pd.DataFrame({n: (G[(n,) + FIGE].groupby("entree")["r"].sum() * 1e4) for n in tiennent}).fillna(0)
        P = P[P.index >= "2007-01-01"]
        R = pd.DataFrame({n: D[n]["close"].pct_change() for n in tiennent})
        R = R[R.index >= "2007-01-01"]
        print("  %-5s " % "" + " ".join("%6s" % n for n in tiennent) + "   | correlation des rendements du marche (meme periode)")
        for a in tiennent:
            print("  %-5s " % a + " ".join("%+6.2f" % P[a].corr(P[b]) for b in tiennent) + "   | " +
                  " ".join("%+6.2f" % R[a].corr(R[b]) for b in tiennent))
        for grp in (tiennent, [x for x in tiennent if x != REF]):
            Q = P[grp].mean(1); Q = Q[(P[grp] != 0).any(axis=1).cumsum() > 0]
            ans = Q.groupby(Q.index.year).sum()
            print("  portefeuille poids egaux %s depuis 2007 : t journalier %+.2f, %+.0f bp/an, annees > 0 : %d/%d, creux %+.0f bp"
                  % ("+".join(grp), tstat(Q[Q != 0]), ans.mean(), (ans > 0).sum(), len(ans), (Q.cumsum() - Q.cumsum().cummax()).min()))
        print("  part des jours de trade de la ligne ou la colonne trade aussi (meme sens) :")
        for a in tiennent:
            ta = G[(a,) + FIGE].set_index("entree")["sens"]
            out = []
            for b in tiennent:
                tb_ = G[(b,) + FIGE].set_index("entree")["sens"]
                c = ta.index.intersection(tb_.index)
                c = c[c >= "2007-01-01"]
                out.append("%3.0f%%" % (100 * (ta[c] == tb_[c]).sum() / max((ta.index >= "2007-01-01").sum(), 1)))
            print("  %-5s " % a + " ".join("%6s" % x for x in out))
    print("\n(%.0f s)" % (time.time() - t0))


if __name__ == "__main__":
    main()
