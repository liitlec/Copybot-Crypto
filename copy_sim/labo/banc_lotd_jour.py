"""Banc Lot D, points 6-8 (ajout de Baptiste 23/11 11 h 25) : « la journee qui commence sera-t-elle une journee de
tendance ou d'aller-retour ? », decide a 9 h Paris puis mis a jour a 11 h et 14 h.
CONTRAT FIGE ET POUSSE AVANT TOUT RESULTAT.

ECART FORCE AU POINT 6 : l'historique intrajour long (Dukascopy, HistData) est BLOQUE par la politique reseau de
l'environnement cloud (connexions refusees le 23/11). On travaille donc sur l'or H1 du courtier (xau_h1_50k,
08/2022 -> 11/2026, ~1 100 jours). Pas de « 15-20 ans » : le resultat sera dit indicatif sur cette duree.

JOUR = jour serveur (New York + 7 h), lundi-vendredi. Heure serveur = heure de Paris + 1 h. Decisions :
  9 h Paris = apres les bougies H1 serveur 00..09 (fermees a 10:00 serveur) ; 11 h = 00..11 ; 14 h = 00..14.
ETIQUETTE (point 6) : efficacite du jour = |cloture - ouverture| / (haut - bas) ; « tendance » = efficacite du RESTE
  du jour (de l'heure de decision a la fin) >= mediane des jours d'apprentissage. Resultat en argent = R des paniers
  bt_or (banc_bt_regulier.simule, reglage H1 du socle, spread reel) OUVERTS ce jour a/apres l'heure de decision
  (9 h : entrees 11, 14, 15 serveur ; 11 h : 14, 15 ; 14 h : 15). Les paniers ouverts avant restent a mise 1.
  Controle du point 6 : etiquettes du jour calculees aussi sur l'or M5 du courtier (xau_m5_90k) sur la periode commune ;
  accord des etiquettes H1 / M5 (part des jours de meme etiquette) donne en clair.
INDICES CONNUS A LA DECISION (point 7) : amplitude / ATR20 et sens / efficacite de la seance depuis minuit serveur
  (Asie + debut d'Europe) ; ecart d'ouverture (ouverture du jour - cloture de la veille) / ATR20 ; efficacite des 1 et
  5 jours precedents ; compression = amplitude d'hier / ATR20 ; jour de la semaine (4 indicatrices) ; jour d'annonce
  (NFP, CPI, FOMC : listes de banc_regime_p6) ; position dans la tendance du mois (prix - ouverture du mois) / ATR20 et
  |idem| ; VIX connu (S.vix_connu) et GVZ connu (decalage du socle, 2 jours). 15 variables.
MODELES : logistique (variables centrees-reduites sur l'apprentissage, L2, C = 1) et arbre de profondeur 2 (feuilles
  >= 50 jours). Walk-forward croissant : apprentissage >= 250 jours, re-estimation chaque mois, prevision du mois
  suivant. Taux de base = toujours la frequence d'apprentissage (AUC 0,5).
MISE : probabilite prevue dans le tiers haut des previsions de l'apprentissage -> 2 ; tiers bas -> 0 ; sinon 1 ;
  appliquee aux paniers bt_or ouverts apres la decision ce jour-la. 6 regles = 2 modeles x 3 heures.
JUGEMENT : reference « toujours 1 » ; risque egal (comparaison des rapports moyenne/ecart-type des P&L JOURNALIERS) ;
  blocs B1 = debut de prevision -> 09/2024, B2 = 10/2024 -> fin. AUC hors echantillon (IC bootstrap 95 %).
  SPA de Hansen sur les 6 regles (bootstrap stationnaire, blocs moyens 5 jours, 2000 tirages). Placebo : previsions
  melangees entre jours d'un meme mois, 1000 tirages. Spread double (simule refait avec sp x 2).
  RETENU si : AUC > 0,5 (borne basse IC > 0,5) ET bat « toujours 1 » a risque egal en B1 ET B2 ET p SPA < 0,05 ET
  placebo p < 0,05 ET bat encore au spread double.
VALEUR D'UNE BONNE PREVISION : prevision synthetique juste avec probabilite q du signe du R apres decision (mise 2 si
  « bon jour » prevu, 0 sinon) ; gain a risque egal contre « toujours 1 » pour q = 0,50 ... 0,70 ; precision minimale
  qui paie (moyenne de 200 tirages par q). Comparee a la precision reelle des modeles.
POINT 8 : bilan jour / mois. Variante demo seulement si une regle est RETENUE.
Usage : python3 banc_lotd_jour.py   (ecrit donnees/lotd_jour.csv)
"""
import ast, contextlib, io, os, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_bt_regulier as BR
    import regime_socle as S
from banc_lotd import spa, sr, tranche

ICI = os.path.dirname(os.path.abspath(__file__))
DECS = {"9 h": 10, "11 h": 12, "14 h": 15}               # heure de Paris -> premiere heure serveur NON connue
B2_0 = pd.Timestamp("2024-10-01")
rng = np.random.default_rng(29)


def calendrier():
    src = open(os.path.join(ICI, "banc_regime_p6.py")).read()
    L = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(src).body
         if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in ("NFP", "CPI")}
    F = list(pd.read_csv(os.path.join(S.DONL, "fomc.csv")).annonce)
    return pd.DatetimeIndex(pd.to_datetime(L["NFP"] + L["CPI"] + F)).unique()


def barres(ident, debut="2022-08-01"):
    d = BR.charge(ident)
    d = d[d.heure >= pd.Timestamp(debut).timestamp()].reset_index(drop=True)
    t = pd.to_datetime(d.heure, unit="s")
    d["jour"], d["h"] = t.dt.floor("D"), t.dt.hour
    return d[t.dt.dayofweek < 5].reset_index(drop=True)


def etiquettes(d):
    """Efficacite du reste du jour pour chaque heure de decision."""
    out = {}
    for nom, hd in DECS.items():
        av, ap = d[d.h < hd], d[d.h >= hd]
        cd = av.groupby("jour").cloture.last()
        g = ap.groupby("jour").agg(hi=("haut", "max"), lo=("bas", "min"), c=("cloture", "last"))
        g = g.join(cd.rename("cd"), how="inner")
        hi, lo = np.maximum(g.hi, g.cd), np.minimum(g.lo, g.cd)
        out[nom] = ((g.c - g.cd).abs() / (hi - lo)).where(hi > lo)
    return pd.DataFrame(out)


def variables(d, ann, vix, gvz):
    j = d.groupby("jour").agg(o=("ouverture", "first"), hi=("haut", "max"), lo=("bas", "min"), c=("cloture", "last"))
    tr = np.maximum(j.hi - j.lo, np.maximum((j.hi - j.c.shift()).abs(), (j.lo - j.c.shift()).abs()))
    atr = tr.rolling(20).mean().shift(1)
    eff = (j.c - j.o).abs() / (j.hi - j.lo)
    mo = j.o.groupby(j.index.to_period("M")).transform("first")
    X = {}
    for nom, hd in DECS.items():
        s = d[d.h < hd].groupby("jour").agg(o=("ouverture", "first"), hi=("haut", "max"), lo=("bas", "min"), c=("cloture", "last"))
        s = s.reindex(j.index)
        v = pd.DataFrame(index=j.index)
        v["amp"] = (s.hi - s.lo) / atr; v["sens"] = (s.c - s.o) / atr; v["eff_s"] = (s.c - s.o).abs() / (s.hi - s.lo)
        v["ecart"] = (j.o - j.c.shift()) / atr; v["eff1"] = eff.shift(); v["eff5"] = eff.shift().rolling(5).mean()
        v["compr"] = (j.hi - j.lo).shift() / atr
        for k in (1, 2, 3, 4): v["dow%d" % k] = (j.index.dayofweek == k).astype(float)
        v["annonce"] = j.index.isin(ann).astype(float)
        v["mois"] = (s.c - mo) / atr; v["|mois|"] = v["mois"].abs()
        v["vix"] = vix.reindex(j.index).ffill().values; v["gvz"] = gvz.reindex(j.index).ffill().values
        X[nom] = v
    return X


def logit_fit(X, y, lam=1.0):
    A = np.c_[np.ones(len(X)), X]; w = np.zeros(A.shape[1]); P = np.eye(A.shape[1]) * lam; P[0, 0] = 0
    for _ in range(30):
        p = 1 / (1 + np.exp(-A @ w)); g = A.T @ (p - y) + P @ w
        H = A.T @ (A * (p * (1 - p))[:, None]) + P
        w -= np.linalg.solve(H, g)
    return lambda Z: 1 / (1 + np.exp(-np.c_[np.ones(len(Z)), Z] @ w))


def arbre_fit(X, y, prof=2, mini=50):
    def best(idx):
        bestg, bs = None, None
        base = y[idx].mean(); gini0 = base * (1 - base) * len(idx)
        for k in range(X.shape[1]):
            for s in np.unique(np.quantile(X[idx, k], np.linspace(0.05, 0.95, 19))):
                g, dr = idx[X[idx, k] <= s], idx[X[idx, k] > s]
                if len(g) < mini or len(dr) < mini: continue
                gi = sum(len(z) * y[z].mean() * (1 - y[z].mean()) for z in (g, dr))
                if bestg is None or gi < bestg: bestg, bs = gi, (k, s, g, dr)
        return bs if bs is not None and bestg < gini0 - 1e-9 else None
    def grow(idx, p):
        sp = best(idx) if p < prof else None
        if sp is None: return ("f", y[idx].mean())
        k, s, g, dr = sp; return ("n", k, s, grow(g, p + 1), grow(dr, p + 1))
    T = grow(np.arange(len(y)), 0)
    def pred1(z, n=T):
        while n[0] == "n": n = n[3] if z[n[1]] <= n[2] else n[4]
        return n[1]
    return lambda Z: np.array([pred1(z) for z in Z])


def auc(p, y):
    r = pd.Series(p).rank().values; n1 = y.sum(); n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0) if n1 and n0 else np.nan


def walk_forward(X, E, fit):
    """Rend mises (0/1/2), probabilites, etiquettes binaires, par jour (hors echantillon)."""
    ok = X.notna().all(1) & E.notna()
    Xv, Ev = X[ok], E[ok]
    mois = Xv.index.to_period("M"); W, Pr, Y = {}, {}, {}
    for m in mois.unique():
        tr, te = mois < m, mois == m
        if tr.sum() < 250: continue
        mu, sd = Xv[tr].mean(), Xv[tr].std().replace(0, 1)
        A, Z = ((Xv[tr] - mu) / sd).values, ((Xv[te] - mu) / sd).values
        med = Ev[tr].median(); y = (Ev[tr] >= med).values.astype(float)
        f = fit(A, y); pin = f(A); q1, q2 = np.quantile(pin, [1 / 3, 2 / 3]); pt = f(Z)
        for dj, p, e in zip(Xv.index[te], pt, Ev[te]):
            W[dj] = 0.0 if p < q1 else (2.0 if p > q2 else 1.0); Pr[dj] = p; Y[dj] = float(e >= med)
    return pd.Series(W), pd.Series(Pr), pd.Series(Y)


def r_jour(P, hd, jours):
    t = pd.to_datetime(P.t0, unit="s"); j, h = t.dt.floor("D"), t.dt.hour
    av = P.g[h < hd].groupby(j[h < hd]).sum().reindex(jours, fill_value=0.0)
    ap = P.g[h >= hd].groupby(j[h >= hd]).sum().reindex(jours, fill_value=0.0)
    return av, ap


if __name__ == "__main__":
    d = barres("xau_h1_50k")
    P1 = BR.simule(d, span=48, heures=S.H1_HEURES, debut=60)
    d2 = d.copy(); d2["sp"] *= 2; P2 = BR.simule(d2, span=48, heures=S.H1_HEURES, debut=60)
    E = etiquettes(d)
    with contextlib.redirect_stdout(io.StringIO()):
        import banc_regime_p6 as P6
        gvz = P6.gvz_connu()
    X = variables(d, calendrier(), S.vix_connu(), gvz)
    jours = E.index
    # ---------------------------------------------- controle des etiquettes H1 / M5 (point 6)
    m5 = barres("xau_m5_90k", "2025-01-01")
    E5 = etiquettes(m5); com = E5.dropna().index.intersection(E.dropna().index)
    print("POINT 6 (or H1 du courtier, %s -> %s, %d jours)" % (jours[0].date(), jours[-1].date(), len(jours)))
    for c in E:
        a, b = E.loc[com, c] >= E.loc[com, c].median(), E5.loc[com, c] >= E5.loc[com, c].median()
        print("  %-5s efficacite du reste du jour mediane %.2f ; accord etiquettes H1 / M5 %.0f %% sur %d jours ; corr %.2f" % (
            c, E[c].median(), 100 * (a == b).mean(), len(com), np.corrcoef(E.loc[com, c], E5.loc[com, c])[0, 1]))
    effj = d.groupby("jour").apply(lambda x: abs(x.cloture.iloc[-1] - x.ouverture.iloc[0]) / (x.haut.max() - x.bas.min()))
    for dj in ("2026-11-05", "2026-11-06", "2026-11-10", "2026-11-11"):
        if pd.Timestamp(dj) in effj.index: print("  exemple %s : efficacite du jour %.2f" % (dj, effj[pd.Timestamp(dj)]))
    print("  persistance : correlation efficacite jour J / J-1 = %.2f ; J / moyenne 5 j = %.2f" % (
        effj.autocorr(1), np.corrcoef(effj.iloc[5:], effj.shift().rolling(5).mean().iloc[5:])[0, 1]))
    # ---------------------------------------------- point 7
    lignes, Dm, regles = [], [], {}
    for nom, hd in DECS.items():
        av, ap = r_jour(P1, hd, jours); av2, ap2 = r_jour(P2, hd, jours)
        for mod, fit in (("logistique", logit_fit), ("arbre", arbre_fit)):
            W, Pr, Y = walk_forward(X[nom], E[nom], fit)
            idx = W.index; ref = av[idx] + ap[idx]; x = av[idx] + W * ap[idx]
            ref2 = av2[idx] + ap2[idx]; x2 = av2[idx] + W * ap2[idx]
            eg = x * ref.std() / x.std()
            a = auc(Pr.values, Y.values.astype(int))
            bt = [auc(Pr.values[ii], Y.values[ii].astype(int)) for ii in rng.integers(len(Pr), size=(500, len(Pr)))]
            lo_, hi_ = np.nanquantile(bt, [0.025, 0.975])
            per = idx.to_period("M"); pl = []
            for _ in range(1000):
                ws = W.groupby(per).transform(lambda s: pd.Series(rng.permutation(s.values), index=s.index))
                pl.append(sr(av[idx] + ws * ap[idx]))
            pp = (np.array(pl) >= sr(x)).mean()
            b1, b2 = idx < B2_0, idx >= B2_0
            g1 = eg[b1].sum() - ref[b1].sum(); g2 = eg[b2].sum() - ref[b2].sum()
            dc = sr(x2) - sr(ref2)
            Dm.append((eg - ref).values); regles[(nom, mod)] = (W, ap[idx], av[idx], ref)
            lignes.append(dict(decision=nom, modele=mod, jours=len(idx), debut=str(idx[0].date()), auc=a, auc_bas=lo_, auc_haut=hi_,
                               part0=(W == 0).mean(), part2=(W == 2).mean(), ref_R=ref.sum(), sr_ref=sr(ref) * np.sqrt(252),
                               sr=sr(x) * np.sqrt(252), gain_B1=g1, gain_B2=g2, placebo_p=pp, d_sr_x2=dc * np.sqrt(252)))
    L = min(len(x) for x in Dm); Dm = np.column_stack([x[-L:] for x in Dm])
    pspa, pw = spa(Dm)
    T = pd.DataFrame(lignes)
    T["retenu"] = (T.auc_bas > 0.5) & (T.gain_B1 > 0) & (T.gain_B2 > 0) & (pspa < 0.05) & (T.placebo_p < 0.05) & (T.d_sr_x2 > 0)
    T.to_csv(os.path.join(S.DONL, "lotd_jour.csv"), index=False)
    pd.set_option("display.width", 250)
    print("\nPOINT 7 (walk-forward ; R des paniers bt_or ; rapports gain/risque annuels) ; SPA p = %.3f, White p = %.3f" % (pspa, pw))
    print(T.round(3).to_string(index=False))
    # ---------------------------------------------- valeur d'une bonne prevision
    print("\nVALEUR D'UNE PREVISION (decision 9 h, mise 2 si « bon jour » prevu, 0 sinon ; gain a risque egal sur la periode)")
    W, ap, av, ref = regles[("9 h", "logistique")]
    vrai = (ap > 0).values; actif = ap.values != 0
    for q in (0.50, 0.52, 0.55, 0.60, 0.65, 0.70):
        gs = []
        for _ in range(200):
            juste = rng.random(len(ap)) < q
            w = np.where(juste == vrai, 2.0, 0.0) * 1.0
            w = np.where(vrai, np.where(juste, 2.0, 0.0), np.where(juste, 0.0, 2.0))
            x = av + w * ap; gs.append((x * ref.std() / x.std()).sum() - ref.sum())
        print("  precision %.2f (sur %d jours avec panier apres 9 h) : %+.0f R a risque egal (toujours 1 : %+.0f R)" % (q, actif.sum(), np.mean(gs), ref.sum()))
    for (nom, mod), (W, ap, av, ref) in regles.items():
        m = ap != 0; ok = ((W[m] == 2) & (ap[m] > 0)) | ((W[m] == 0) & (ap[m] < 0)); pris = W[m] != 1
        print("  precision reelle %s %-10s : %.2f sur les jours a mise 0 ou 2 (%d jours)" % (nom, mod, ok[pris].mean(), pris.sum()))
