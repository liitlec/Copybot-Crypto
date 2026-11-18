"""Banc AI : bt_or (panier de tendance sur l'or) MELANGE aux autres regles « qui tiennent ou presque » : se completent-ils ?
(PRIORITES 18/11 12 h 30, suite de banc_portefeuille.py qui ne contenait PAS bt_or.)
Pieces = series JOURNALIERES de rendement en fraction du capital pour une mise unitaire (0 les jours sans position),
sur jours ouvres (un gain date d'un samedi/dimanche est reporte au lundi). Couts deja inclus dans chaque piece.
- bt_or : rejoue en H1 (xau_h1_50k a partir du 01/08/2022, reglages H1 de banc_bt_regulier / banc_jumeau : EMA 48
  bougies, heures 2,7,11,14,15 h), courbe marquee a la cloture du jour, gain latent compris (banc_jumeau.simule_j,
  colonne bt_or), spread reel. CONVENTION : 1 R = 1 % du capital a mise unitaire (rendement = R / 100).
  Verification : meme courbe en M5 (xau_m5_2025a + xau_m5_90k, 06/2025 -> 11/2026), correlation mensuelle H1/M5.
- Complements (banc_portefeuille : cache donnees/indices_jour.csv.gz, couts 1,5 bp + financement de nuit) :
  repli_ind = moyenne des 4 replis (S&P, Nasdaq 100, Dow, Russell ; notionnel total 1) ; rebond_nas ; vix_sp (presque) ;
  rebond_sp = donnees/rebonds_grande_journee.csv gj_fige:sp ; fomc_dax = donnees/rebonds_calendrier.csv cal_fomc:DAX.
  achat_seul = panier ACHETE SEULEMENT reduit aux caches locaux (4 indices US + or D1 du courtier), risque egal
  (banc_prime : poids = min(10 % / vol 60 j, 1) / 5, decides a J-2, comptant, frais 0,2 %/an, sans dividendes,
  1,5 bp par changement de poids). Ecartes : « suivre ce qui marche » (trades du robot sur 15 mois / quelques jours
  de demo : ne recouvre pas 2022-2026), COT euro (cache data/cot.csv.gz absent : il faudrait tout retelecharger),
  panier achete seulement complet (argent, BTC, ETH, DAX... : cache data/jour.csv.gz absent).
Periode commune : celle de bt_or H1 (08/2022 -> 11/2026).
POINT 1 : correlations bt_or / chaque complement (jour, semaine, mois) ; resultat des complements pendant les mois
  ou bt_or perd contre ceux ou il gagne (somme, moyenne, % de mois gagnants, t de Welch) ; zoom 2023 et 04-10/2026.
POINT 2 : poids >= 0, trois methodes fixees d'avance, sur les rendements journaliers d'apprentissage :
  (a) parite de risque w ~ 1/vol ; (b) moyenne-variance : Sigma retrecie 0,5 vers sa diagonale, moyennes retrecies
  de moitie vers la moyenne commune, w = inv(Sigma) mu, negatifs a 0 ; (c) Kelly f = inv(Sigma) (mu / 2) avec les
  memes retrecissements, negatifs a 0, chaque piece plafonnee a 40 % de vol annuelle seule (a vol egale, (c) ne differe
  de (b) que si le plafond mord). Si tous les poids sont nuls : pas de position (cash).
  Walk-forward a fenetre croissante, test par SEMESTRE (1er test 08/2023 apres 12 mois d'apprentissage).
  Trois portefeuilles par methode : bt_or seul, complements seuls, melange.
POINT 3 : hors echantillon, (i) a volatilite cible egale (10 %/an sur l'apprentissage) ; (ii) a 0,5 et 1 Kelly
  fractionne (Kelly estime sur l'apprentissage avec moyennes / 2 ; pour (a) et (b) Kelly scalaire de la direction,
  pour (c) le vecteur f) ; garde-fou : vol annuelle d'apprentissage <= 100 % ; ruine = capital < 20 %.
  Rendement par an compose, % mois < 0, pire baisse, rendement / pire baisse, Sharpe mensuel.
  Bootstrap stationnaire (blocs moyens 20 jours, 2000 tirages, apparie) de la difference de Sharpe (journalier
  annualise) melange - bt_or seul et melange - complements seuls, a vol egale ; p corrige = max sur les 3 methodes
  (reality check de White). Poids finaux appris sur tout l'historique.
Verdict (fixe d'avance) : tient = a vol egale et hors ech., le melange a un meilleur rendement / pire baisse ET un
  meilleur Sharpe que bt_or seul ET que les complements seuls, pour au moins 2 methodes sur 3, avec p corrige < 0,05
  contre bt_or seul ; presque = memes conditions descriptives mais p >= 0,05 ; sinon non.
Controles : bt_or H1 ~ +154 R / 956 paniers ; pieces d'indices aux ordres de grandeur de banc_portefeuille ;
  melange a un seul actif = cet actif.
RESULTAT (execution du 18/11/2026, 11 s) : verdict PRESQUE. Correlations bt_or / complements ~0 (jour -0,06..0,00 ;
  mois -0,01..+0,11). Hors ech. 08/2023-11/2026 a vol 10 % : parite melange +26,3 %/an, creux -7,6 %, an/creux 3,49,
  Sharpe 1,75 contre bt_or seul 2,41 / 1,67 et complements 2,13 / 1,48 ; Kelly retr. 2,32 / 1,48 contre 2,17 / 1,48
  (Sharpe a peine >) et 2,22 / 1,36 ; MV retr. echoue (1,41). p corrige contre bt_or seul 0,570 (contre complements
  0,027). Poids : fomc_dax (vol 1,7 %) pese 44-75 % ; bt_or ~1/7 du risque en parite.
Ecrit donnees/mix_wf.csv (series mensuelles hors echantillon). Usage : python3 banc_mix.py"""
import os, time, contextlib, io, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_bt_regulier as BR
    import banc_jumeau as BJ
    import banc_portefeuille as BP

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
DEB = pd.Timestamp("2022-08-01")
VOL_CIBLE, VOL_MAX, PLAF_C = 0.10, 1.0, 0.40
rng = np.random.default_rng(20261118)
pd.set_option("display.width", 220)


def vers_ouvres(s, B):
    """Reporte une serie datee (jours calendaires) sur les jours ouvres B (week-end -> lundi suivant), somme."""
    s = s[(s.index >= B[0]) & (s.index <= B[-1])]
    pos = B.searchsorted(s.index.normalize())
    ok = pos < len(B)
    return pd.Series(s.values[ok], index=B[pos[ok]]).groupby(level=0).sum().reindex(B).fillna(0.0)


# ------------------------------------------------------------------ pieces
def bt_or_jour(d, kw):
    (Pi, GR, _), ER, _ = BJ.simule_j(d, **kw)
    x = ER[0].diff().fillna(ER[0].iloc[0])
    return x, Pi, GR[:, 0]


def achat_seul(D, B):
    x = pd.read_csv(os.path.join(ICI, "mt5", "donnees", "xau_d1_5k.csv.gz"))
    xau = pd.Series(x.cloture.values, index=pd.to_datetime(x.heure, unit="s").dt.normalize())
    px = pd.DataFrame({n: D[n]["close"] for n in ("SP", "NAS", "DJ", "RUT")})
    px["OR"] = vers_ouvres(xau, pd.bdate_range(xau.index[0], xau.index[-1])).replace(0, np.nan)
    px = px[px.index >= "2018-10-01"].ffill()
    r = px.pct_change()
    vol = r.ewm(span=60, min_periods=40).std() * np.sqrt(252)
    w = (0.10 / vol).clip(upper=1.0) / 5
    tenu = w.shift(2)
    g = (tenu * r).sum(axis=1) - w.diff().abs().sum(axis=1).shift(1).fillna(0) * 1.5e-4 - tenu.sum(axis=1) * 0.002 / 252
    return vers_ouvres(g.fillna(0), B)


# ------------------------------------------------------------------ statistiques
def stats(r):
    """r : rendements journaliers (compose). Rend an, %mois<0, pire baisse, rapport, Sharpe mensuel, ruine."""
    if len(r) == 0 or (r == 0).all():
        return dict(an=0.0, mneg=np.nan, creux=0.0, rap=np.nan, sh=np.nan, ruine=False)
    eq = (1 + r.clip(lower=-1)).cumprod()
    if (eq <= 0).any():
        eq = eq.where(eq.cummin() > 0, 0.0)
    an = eq.iloc[-1] ** (252 / len(r)) - 1 if eq.iloc[-1] > 0 else -1.0
    cr = (eq / eq.cummax() - 1).min()
    m = (1 + r).groupby(r.index.to_period("M")).prod() - 1
    return dict(an=an, mneg=100 * (m < 0).mean(), creux=cr, rap=an / -cr if cr < 0 else np.nan,
                sh=m.mean() / m.std() * np.sqrt(12) if m.std() > 0 else np.nan, ruine=bool(eq.min() < 0.2))


def direction(X, meth):
    """Poids >= 0 appris sur X (jours x pieces). (a) 1/vol ; (b) MV retrecie ; (c) Kelly retreci plafonne (non normalise)."""
    sd = X.std().values
    if X.shape[1] == 1 and meth == "a":
        return np.array([1.0])
    if meth == "a":
        w = np.where(sd > 0, 1 / np.where(sd > 0, sd, 1), 0.0)
        return w / w.sum()
    S = X.cov().values; S = 0.5 * S + 0.5 * np.diag(np.diag(S))
    mu = X.mean().values; mu = 0.5 * mu + 0.5 * mu.mean()
    if meth == "b":
        w = np.clip(np.linalg.solve(S + 1e-14 * np.eye(len(mu)), mu), 0, None)
        return w / w.sum() if w.sum() > 0 else w
    f = np.clip(np.linalg.solve(S + 1e-14 * np.eye(len(mu)), mu / 2), 0, None)
    return np.minimum(f, PLAF_C / (np.where(sd > 0, sd, np.inf) * np.sqrt(252)))


def mises(X, meth):
    """Rend (direction normalisee, levier vol cible, levier 0,5 K, levier 1 K) appris sur X."""
    w = direction(X, meth)
    if w.sum() <= 0:
        return w, 0.0, 0.0, 0.0
    p = X.values @ w
    sd = p.std() * np.sqrt(252)
    if sd <= 0:
        return w, 0.0, 0.0, 0.0
    vc = VOL_CIBLE / sd
    k = 1.0 if meth == "c" else max(p.mean() / 2, 0) / p.var()   # (c) : w est deja le vecteur de Kelly (mu / 2)
    plaf = VOL_MAX / sd
    return w, vc, min(0.5 * k, plaf), min(k, plaf)


def boot_sharpe(Rm, Rb, I):
    """Rm, Rb : (methodes x jours) ; I : tirages. Rend ecarts observes, p bruts, p corrige (max)."""
    sh = lambda Z: Z.mean(-1) / Z.std(-1) * np.sqrt(252)
    d0 = sh(Rm) - sh(Rb)
    db = sh(Rm[:, I]) - sh(Rb[:, I])                                     # methodes x tirages
    cen = db - d0[:, None]
    p_brut = (cen >= d0[:, None]).mean(1)
    p_cor = (cen.max(0) >= d0.max()).mean()
    return d0, p_brut, p_cor


if __name__ == "__main__":
    # ---------------- bt_or H1 et M5
    dh = BR.charge("xau_h1_50k"); dh = dh[dh.heure >= DEB.timestamp()].reset_index(drop=True)
    kwh = dict(span=48, heures=BJ.H_H1, debut=60)
    xh, Ph, gh = bt_or_jour(dh, kwh)
    ref = BR.simule(dh, **kwh)
    a5, b5 = BR.charge("xau_m5_2025a"), BR.charge("xau_m5_90k")
    d5 = pd.concat([a5, b5[b5.heure > a5.heure.iloc[-1]]], ignore_index=True)
    x5, P5, g5 = bt_or_jour(d5, {})
    print("Controle bt_or H1 : %d paniers, %+.1f R (banc_bt_regulier : %d paniers, %+.1f R) ; courbe marquee %+.1f R, %s -> %s"
          % (len(Ph), gh.sum(), len(ref), ref.g.sum(), xh.sum(), xh.index[0].date(), xh.index[-1].date()))
    mh, m5 = xh.groupby(xh.index.to_period("M")).sum(), x5.groupby(x5.index.to_period("M")).sum()
    cm = mh.index.intersection(m5.index)[1:]                    # 1er mois M5 incomplet (EMA)
    print("Controle M5 (%d paniers, %+.1f R) : correlation mensuelle H1/M5 sur %d mois communs = %.2f (somme H1 %+.1f R, M5 %+.1f R) ;"
          " journaliere %.2f" % (len(P5), g5.sum(), len(cm), np.corrcoef(mh[cm], m5[cm])[0, 1], mh[cm].sum(), m5[cm].sum(),
                                 pd.concat([xh, x5], axis=1).dropna().corr().iloc[0, 1]))
    print("CONVENTION : 1 R = 1 %% du capital a mise unitaire -> bt_or H1 = %+.0f %% simple sur la periode." % xh.sum())

    # ---------------- indices
    with contextlib.redirect_stdout(io.StringIO()):
        D = BP.donnees()
    idx = D["SP"].index[D["SP"].index >= "1990-01-01"]
    P, TR = {}, {}
    for n in ("SP", "NAS", "DJ", "RUT"):
        x, t = BP.piece_repli(D, n); P["repli_" + n] = x.reindex(idx).fillna(0); TR["repli_" + n] = t
    x, t = BP.piece_rebond(D); P["rebond_nas"] = x.reindex(idx).fillna(0); TR["rebond_nas"] = t
    x, t = BP.piece_vix(D); P["vix_sp"] = x.reindex(idx).fillna(0); TR["vix_sp"] = t
    E = BP.pieces_externes(idx)
    P["rebond_sp"] = E["grande_journee:gj_fige:sp"]; P["fomc_dax"] = E["calendrier:cal_fomc:DAX"]
    print("\nControle pieces d'indices (historique complet, notionnel 1, comme banc_portefeuille) :")
    tst = lambda v: np.mean(v) / np.std(v) * np.sqrt(len(v)) if len(v) > 2 else 0
    for k in P:
        a = P[k][P[k] != 0]
        print("  %-11s %4d trades/jours actifs depuis %s, %+6.1f bp/jour actif, t %.1f ; 08/2022-11/2026 : %+6.1f %% simple"
              % (k, len(TR.get(k, [])) or len(a), a.index[0].date(), 1e4 * a.mean(), tst(a.values),
                 100 * P[k][P[k].index >= DEB].sum()))

    fin = min(xh.index[-1], idx[-1])
    B = pd.bdate_range(DEB, fin)
    X = pd.DataFrame({"bt_or": vers_ouvres(xh / 100, B),
                      "repli_ind": sum(vers_ouvres(P["repli_" + n], B) for n in ("SP", "NAS", "DJ", "RUT")) / 4,
                      "rebond_nas": vers_ouvres(P["rebond_nas"], B), "rebond_sp": vers_ouvres(P["rebond_sp"], B),
                      "fomc_dax": vers_ouvres(P["fomc_dax"], B), "vix_sp": vers_ouvres(P["vix_sp"], B),
                      "achat_seul": achat_seul(D, B)})
    X = X[X.index >= X.bt_or.ne(0).idxmax()]
    COMP = [c for c in X if c != "bt_or"]
    print("\nPeriode commune %s -> %s, %d jours ouvres. Pieces (somme simple %%, vol annuelle %%, Sharpe journalier annualise, %% jours actifs) :"
          % (X.index[0].date(), X.index[-1].date(), len(X)))
    for c in X:
        print("  %-11s %+7.1f %%  vol %5.1f %%  Sharpe %+5.2f  actif %3.0f %%" % (
            c, 100 * X[c].sum(), 100 * X[c].std() * np.sqrt(252), X[c].mean() / X[c].std() * np.sqrt(252), 100 * (X[c] != 0).mean()))

    # ================= POINT 1
    print("\n=== POINT 1. Correlations avec bt_or (tous jours, 0 compris) :")
    Wk = X.resample("W-FRI").sum(); Mo = X.groupby(X.index.to_period("M")).sum()
    print("  %-11s %6s %6s %6s" % ("piece", "jour", "sem.", "mois"))
    for c in COMP:
        print("  %-11s %+6.2f %+6.2f %+6.2f" % (c, X.bt_or.corr(X[c]), Wk.bt_or.corr(Wk[c]), Mo.bt_or.corr(Mo[c])))
    bo = Mo.bt_or
    print("Complements selon le mois de bt_or (%d mois perdants, somme bt_or %+.1f %% ; %d gagnants, %+.1f %%) ; en %% du capital, notionnel 1 :"
          % ((bo < 0).sum(), 100 * bo[bo < 0].sum(), (bo > 0).sum(), 100 * bo[bo > 0].sum()))
    print("  %-11s | %8s %7s %5s | %8s %7s %5s | %6s || 2023: bt %+.1f | 04-10/2026: bt %+.1f" % (
        "piece", "somme-", "moy-", "%g-", "somme+", "moy+", "%g+", "t", 100 * bo["2023"].sum(), 100 * bo["2026-04":"2026-10"].sum()))
    for c in COMP:
        a, b = Mo[c][bo < 0], Mo[c][bo > 0]
        t = (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b))
        z1, z2 = Mo[c]["2023"], Mo[c]["2026-04":"2026-10"]
        l1, l2 = bo["2023"] < 0, bo["2026-04":"2026-10"] < 0
        print("  %-11s | %+7.2f%% %+6.2f%% %4.0f%% | %+7.2f%% %+6.2f%% %4.0f%% | %+6.2f || %+5.2f%% (mois bt<0 : %+5.2f%%) | %+5.2f%% (mois bt<0 : %+5.2f%%)" % (
            c, 100 * a.sum(), 100 * a.mean(), 100 * (a > 0).mean(), 100 * b.sum(), 100 * b.mean(), 100 * (b > 0).mean(), t,
            100 * z1.sum(), 100 * z1[l1].sum(), 100 * z2.sum(), 100 * z2[l2].sum()))
    print("  (2023 : %d mois bt<0 sur %d ; 04-10/2026 : %d sur %d)" % (
        (bo["2023"] < 0).sum(), len(bo["2023"]), (bo["2026-04":"2026-10"] < 0).sum(), len(bo["2026-04":"2026-10"])))

    # ================= POINT 2 et 3
    tests, t0 = [], pd.Timestamp("2023-08-01")
    while t0 <= X.index[-1]:
        t1 = pd.Timestamp("%d-01-01" % (t0.year + 1)) if t0.month >= 7 else pd.Timestamp("%d-07-01" % t0.year)
        tests.append((t0, t1)); t0 = t1
    JEUX = {"bt_or seul": ["bt_or"], "complements": COMP, "melange": ["bt_or"] + COMP}
    METH = {"a": "parite", "b": "MV retr.", "c": "Kelly retr."}
    OOS, WS = {}, {}
    for m in METH:
        for j, cols in JEUX.items():
            R = {k: [] for k in ("vc", "k05", "k1")}; ws = []
            for t0, t1 in tests:
                A, T = X.loc[X.index < t0, cols], X.loc[(X.index >= t0) & (X.index < t1), cols]
                w, vc, k05, k1 = mises(A, m)
                p = T.values @ w
                for k, L in (("vc", vc), ("k05", k05), ("k1", k1)):
                    R[k].append(pd.Series(L * p, index=T.index))
                ws.append((t0.date(), np.round(w / w.sum() if w.sum() > 0 else w, 2), round(vc, 2), round(k05, 2)))
            for k in R:
                OOS[(m, j, k)] = pd.concat(R[k])
            WS[(m, j)] = ws
    # controle : melange a un seul actif = cet actif
    for m in METH:
        for c in ("bt_or", "repli_ind"):
            Z = X[[c]]
            print("Controle melange a un seul actif (%s, %s) : poids %s" % (METH[m], c, direction(Z, m)), end=" ; ")
    print()
    print("\n=== POINT 2. Poids par semestre (normalises ; ordre %s ; levier vol cible / 0,5 K) :" % (["bt_or"] + COMP))
    for m in METH:
        for t0, w, vc, k05 in WS[(m, "melange")]:
            print("  %-11s %s  %s  vc %6.2f  0,5K %6.2f" % (METH[m], t0, " ".join("%4.2f" % v for v in w), vc, k05))
    print("\n=== POINT 3. Hors echantillon %s -> %s (%d semestres), %% par an compose :" % (tests[0][0].date(), X.index[-1].date(), len(tests)))
    lignes = []
    for k, lab in (("vc", "vol cible 10 %"), ("k05", "0,5 Kelly"), ("k1", "1 Kelly")):
        print(" -- %s" % lab)
        print("   %-11s %-11s %8s %7s %8s %7s %7s %s" % ("methode", "portef.", "an %", "m<0 %", "creux %", "an/cr", "Sh mens", "ruine"))
        for m in METH:
            for j in JEUX:
                s = stats(OOS[(m, j, k)])
                lignes.append(dict(mode=k, methode=METH[m], portefeuille=j, **s))
                print("   %-11s %-11s %+8.1f %7.0f %+8.1f %7.2f %7.2f %s" % (METH[m], j, 100 * s["an"], s["mneg"], 100 * s["creux"],
                                                                         s["rap"], s["sh"], "RUINE" if s["ruine"] else ""))
    L = pd.DataFrame(lignes)
    # bootstrap a vol egale
    n = len(OOS[("a", "melange", "vc")])
    I = BR.boot(n, B=2000, b=20.0)
    Rm = np.stack([OOS[(m, "melange", "vc")].values for m in METH])
    res = {}
    for j in ("bt_or seul", "complements"):
        Rb = np.stack([OOS[(m, j, "vc")].values for m in METH])
        res[j] = boot_sharpe(Rm, Rb, I)
        d0, pb, pc = res[j]
        print("Bootstrap (blocs 20 j, 2000) Sharpe journalier annualise melange - %-11s : %s ; p corrige (max des 3) %.3f"
              % (j, " ; ".join("%s %+.2f (p %.3f)" % (METH[m], d, p) for m, d, p in zip(METH, d0, pb)), pc))
    # verdict
    V = L[L["mode"] == "vc"].set_index(["methode", "portefeuille"])
    ok = []
    for m in METH.values():
        mx, bt, cp = V.loc[(m, "melange")], V.loc[(m, "bt_or seul")], V.loc[(m, "complements")]
        f = lambda a, b: (a == a) and (b != b or a > b)
        ok.append(f(mx.rap, bt.rap) and f(mx.rap, cp.rap) and f(mx.sh, bt.sh) and f(mx.sh, cp.sh))
    pcb = res["bt_or seul"][2]
    verdict = ("TIENT" if pcb < 0.05 else "PRESQUE") if sum(ok) >= 2 else "NON"
    print("Conditions descriptives remplies (melange > bt_or seul et > complements, an/creux et Sharpe) : %s"
          % dict(zip(METH.values(), ok)))
    # poids finaux
    print("\nPoids finaux (appris sur tout l'historique) : normalises | mise par rapport a bt_or = 1 (bt_or : 1 R = 1 % ; autres : notionnel 1) ; (c) Kelly : direction normalisee du vecteur f")
    for m in METH:
        w = direction(X[["bt_or"] + COMP], m)
        wn = w / w.sum() if w.sum() > 0 else w
        rel = w / w[0] if w[0] > 0 else np.full_like(w, np.nan)
        print("  %-11s %s" % (METH[m], "  ".join("%s %.2f|%s" % (c, a, "%.1f" % b if b == b else "-") for c, a, b in zip(["bt_or"] + COMP, wn, rel))))
    # fichier mensuel
    M = pd.DataFrame({"%s|%s|%s" % (METH[m], j, k): (1 + OOS[(m, j, k)]).groupby(OOS[(m, j, k)].index.to_period("M")).prod() - 1
                      for m in METH for j in JEUX for k in ("vc", "k05")})
    M.index.name = "mois"
    M.round(5).to_csv(os.path.join(ICI, "donnees", "mix_wf.csv"))
    print("\nVerdict (fixe d'avance) : %s.  p corrige contre bt_or seul %.3f, contre complements %.3f. Duree %.0f s. Ecrit donnees/mix_wf.csv (%d mois x %d series)."
          % (verdict, pcb, res["complements"][2], time.time() - T00, len(M), M.shape[1]))
