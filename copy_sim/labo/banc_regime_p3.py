"""Lot B, piste 3 : MÉTA-ÉTIQUETAGE (López de Prado). Pour chaque signal d'une famille, un classifieur dit s'il faut
le prendre ou non. Socle commun : regime_socle.py (jours serveur, familles, unité u, walk-forward, White, critère).

Signaux et étiquettes :
  - familles par trade (bt_or_h1, cassure_h1, retour_h1) : chaque trade ; étiquette = gain du trade (u, au coût jugé) > 0.
  - familles journalières (repli_ind, rebond_nas, tendance_sp) : chaque jour J où la position est non nulle ;
    étiquette = P&L de la famille (poids 1) du jour J > 0.
Caractéristiques, TOUTES connues au DÉBUT du jour J (minuit serveur) pour la version jugée par evalue :
  or H1 (bougies fermées avant minuit, dernière = celle qui commence à J - 1 h) : log vol 24 H1, log (vol 24 / vol 120),
  efficacité 24 H1 (|déplacement| / somme des |variations|), écart à la moyenne 120 H1 (en vol x racine 24) ;
  jour de la semaine (4 indicatrices) ; P&L CONNU de la famille sur 5 et 20 jours (S.connu : trades sortis avant J,
  positions jusqu'à J-1) ; VIX connu (clôture J-1, log) et sa variation sur 5 jours ; S&P D1 jusqu'à J-1 : vol 20 j,
  rendement 5 j, écart à la moyenne 50 j. Pas de caractéristique « heure » dans la version jugée : l'heure d'un trade
  n'est pas connue au début de J (ni même s'il y aura un trade), et un poids du jour qui moyennerait les probas des
  trades de J utiliserait de l'information intrajour postérieure aux premiers trades -> REFUSÉ (fuite). Choix retenu :
  le classifieur d'une famille par trade apprend sur les trades avec les caractéristiques du DÉBUT de leur jour de
  décision ; sa proba pour J est donc la même pour tous les trades de J (aucune moyenne nécessaire).
  Complément (affiché à part, hors critère) : version « trade par trade » où chaque trade or est jugé avec les
  caractéristiques connues à SA décision (H1 fermées avant dec, heure de dec en sin/cos) ; série calculée ici selon les
  conventions de S.pnl, mise à exposition égale par S.egal (exposition du jour = moyenne des poids des trades du jour,
  1 les jours sans trade), puis S.walk / S.white contre TOUT et SUIVRE5, comme evalue.

Modèle : régression logistique L2 (numpy, Newton ; constante non pénalisée ; caractéristiques centrées-réduites sur
l'apprentissage), un modèle par famille, réentraîné chaque mois (le 1er) et figé pendant le mois.
Validation PURGÉE + EMBARGO : pour le mois commençant m0, apprentissage sur les signaux des L mois précédents dont
l'étiquette est CONNUE au plus tard m0 - 5 jours (trades : jour suivant la sortie <= m0 - 5 j ; journalières :
J + 1 <= m0 - 5 j). Les trades bt_or_h1 encore ouverts (jusqu'à 13 jours) sont donc exclus.
Modèle actif à partir du 01/11/2022 (au moins 3 mois de données) ; avant, et si l'apprentissage a moins de 40
signaux ou moins de 8 d'une des deux classes, poids 1 (= TOUT) pour la famille.
Poids du jour J (0..2) : seuil s -> 2 si proba > s, 0 sinon ; « doux » -> clip(1 + 10 (proba - 0,5), 0, 2).
Familles journalières, jours sans position : poids 1 (sans effet sur le P&L, neutre pour l'exposition comme TOUT).

GRILLE FIXÉE D'AVANCE (16 réglages) : pénalité L2 lambda in {1, 10} x fenêtre L in {6, 12} mois
x prise in {seuil 0,50 ; seuil 0,55 ; seuil 0,60 ; doux}. Nom : l<lambda>_L<mois>_<prise>.
Rien n'est réglé sur la période réservée (>= 05/2026) : la grille ci-dessus est fixée avant tout calcul.
Usage : python3 banc_regime_p3.py
"""
import contextlib, io, time
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import regime_socle as S

JOURS, FAMS, TRADES = S.JOURS, S.FAMS, S.TRADES
EMBARGO = pd.Timedelta(days=5)
ACTIF = pd.Timestamp("2022-11-01")
LAMBDAS, FENETRES, PRISES = (1.0, 10.0), (6, 12), ("s50", "s55", "s60", "doux")
GRILLE_NOMS = ["l%d_L%d_%s" % (l, L, p) for l in LAMBDAS for L in FENETRES for p in PRISES]


# ---------------------------------------------------------------------------------------- caractéristiques
def _h1_feat():
    """Caractéristiques or H1 calculées sur les bougies jusqu'à t incluse (index = début de bougie t) :
    connues à t + 1 h (clôture de la bougie t)."""
    d = S.OR_H1; c = d["cloture"]; r = np.log(c).diff()
    v24, v120 = r.rolling(24).std(), r.rolling(120).std()
    F = pd.DataFrame({
        "lvol24": np.log(v24),
        "vratio": np.log(v24 / v120),
        "eff24": (c - c.shift(24)).abs() / c.diff().abs().rolling(24).sum(),
        "z120": (np.log(c) - np.log(c.rolling(120).mean())) / (v120 * np.sqrt(24)),
    }, index=d.index)
    return F


H1F = _h1_feat()


def _asof(F, t):
    """Ligne de F (index = début de bougie) pour la dernière bougie FERMÉE à l'instant t : début <= t - 1 h."""
    i = F.index.searchsorted(pd.DatetimeIndex(t) - pd.Timedelta("1h"), side="right") - 1
    return F.iloc[np.maximum(i, 0)].values


def _sp_feat():
    """S&P D1 : la bougie datée d se ferme à minuit serveur d+1 -> connue au jour J >= d + 1 (décalage +1 jour)."""
    c = S.IND["SP"]["cloture"]; ret = c.pct_change()
    F = pd.DataFrame({"sp_lvol20": np.log(ret.rolling(20).std()), "sp_r5": c.pct_change(5),
                      "sp_m50": c / c.rolling(50).mean() - 1})
    F.index = F.index + pd.Timedelta(days=1)
    return F.reindex(F.index.union(JOURS)).ffill().reindex(JOURS)


def _jour_feat(cout):
    """Caractéristiques communes connues au début de J (hors P&L de famille) : DataFrame indexé par JOURS."""
    X = pd.DataFrame(_asof(H1F, JOURS), index=JOURS, columns=H1F.columns)   # dernière H1 = J-1 h -> J
    for k in range(4):                                                     # lundi..jeudi (vendredi = référence)
        X["dow%d" % k] = (JOURS.dayofweek == k).astype(float)
    v = np.log(S.vix_connu())                                              # clôture NY J-1, connue en J
    X["lvix"], X["dvix5"] = v, v - v.shift(5)                              # shift sur JOURS : connu aussi
    X = X.join(_sp_feat())
    return X


def _fam_connu(cout):
    """P&L connu (S.connu : réalisé strictement avant J) sur 5 et 20 jours, par famille."""
    K = S.connu(cout)
    return {f: pd.DataFrame({"k5": K[f].rolling(5, min_periods=1).sum(), "k20": K[f].rolling(20, min_periods=1).sum()})
            for f in FAMS}


# ---------------------------------------------------------------------------------------- logistique L2
def logit_fit(X, y, lam, it=25):
    n, k = X.shape; Xa = np.column_stack([np.ones(n), X]); b = np.zeros(k + 1)
    P = np.eye(k + 1) * lam; P[0, 0] = 0.0
    for _ in range(it):
        p = 1 / (1 + np.exp(-np.clip(Xa @ b, -30, 30)))
        g = Xa.T @ (p - y) + P @ b
        H = (Xa * (p * (1 - p))[:, None]).T @ Xa + P + 1e-8 * np.eye(k + 1)
        db = np.linalg.solve(H, g); b -= db
        if np.abs(db).max() < 1e-7:
            break
    return b


def logit_pred(b, X):
    return 1 / (1 + np.exp(-np.clip(b[0] + X @ b[1:], -30, 30)))


def _ajuste_predit(Xa, ya, Xt, lam):
    """Standardise sur l'apprentissage, ajuste, prédit. None si apprentissage insuffisant."""
    ok = np.isfinite(Xa).all(1)
    Xa, ya = Xa[ok], ya[ok]
    if len(ya) < 40 or ya.sum() < 8 or (1 - ya).sum() < 8:
        return None
    mu, sd = Xa.mean(0), Xa.std(0); sd[sd == 0] = 1.0
    b = logit_fit((Xa - mu) / sd, ya, lam)
    Z = np.nan_to_num((Xt - mu) / sd)
    return logit_pred(b, Z)


MOIS_M = pd.date_range(ACTIF, JOURS[-1] + pd.offsets.MonthBegin(1), freq="MS")


# ---------------------------------------------------------------------------------------- signaux
def _signaux(cout, au_trade=False):
    """Par famille : (X signaux, y, jour de connaissance de l'étiquette, jour du signal, X de prédiction, index préd.)."""
    XJ, KF = _jour_feat(cout), _fam_connu(cout)
    T = S.trades(cout)
    _, Jd, _ = S.base(cout)
    P1 = S.pnl_fams(S.W_tout(), cout)
    out = {}
    for f in FAMS:
        XF = XJ.join(KF[f])
        if f in TRADES:
            x = T[T.fam == f].reset_index(drop=True)
            jf = x.fin.dt.floor("D") + pd.Timedelta(days=1)                       # étiquette connue le jour suivant la sortie
            jf = jf.where(x.fin != x.fin.dt.floor("D"), x.fin.dt.floor("D"))       # sortie pile à minuit : connue ce jour-là
            Xs = XF.reindex(x.jour).values                                         # début du jour de décision
            if au_trade:                                                           # version trade par trade
                Xs = Xs.copy(); Xs[:, :4] = _asof(H1F, x.dec)                      # H1 fermées avant dec
                h = x.dec.dt.hour.values * 2 * np.pi / 24
                Xs = np.column_stack([Xs, np.sin(h), np.cos(h)])
            out[f] = dict(X=Xs, y=(x.g.values > 0).astype(float), connu=jf.values, jour=x.jour.values,
                          Xp=Xs if au_trade else XF.values, ip=x.index if au_trade else JOURS, dec=x.dec.values)
        else:
            pos = sum(p.abs() for p, _, _ in Jd[f]) > 0                           # position du jour J (connue au début de J)
            jj = JOURS[pos.values]
            out[f] = dict(X=XF.loc[jj].values, y=(P1[f].loc[jj].values > 0).astype(float),
                          connu=(jj + pd.Timedelta(days=1)).values, jour=jj.values,   # P&L de J connu en J+1
                          Xp=XF.values, ip=JOURS, pos=pos)
    return out


def _probas(cout, lam, L, au_trade=False):
    """Probas walk-forward purgées/embargo : par famille, Series sur l'index de prédiction (NaN = pas de modèle)."""
    sig = _signaux(cout, au_trade)
    res = {}
    for f, s in sig.items():
        jp = pd.DatetimeIndex(s["jour"]) if (au_trade and f in TRADES) else pd.DatetimeIndex(s["ip"])
        pr = np.full(len(jp), np.nan)
        conn, jour = pd.DatetimeIndex(s["connu"]), pd.DatetimeIndex(s["jour"])
        for m0 in MOIS_M:
            a0 = max(S.DEBUT, m0 - pd.DateOffset(months=L))
            ka = (jour >= a0) & (conn <= m0 - EMBARGO)                             # PURGE + EMBARGO
            kt = (jp >= m0) & (jp < m0 + pd.offsets.MonthBegin(1))
            if not kt.any():
                continue
            p = _ajuste_predit(s["X"][ka], s["y"][ka], s["Xp"][kt], lam)
            if p is not None:
                pr[kt] = p
        res[f] = pd.Series(pr, index=s["ip"]) if not (au_trade and f in TRADES) else pd.Series(pr)
        if f not in TRADES:
            res[f + "_pos"] = s["pos"]
    return res


def _poids(p, prise, neutre=1.0):
    """neutre = 1 : convention préenregistrée ; neutre = 2 : contrôle (prendre tout = 2 partout = TOUT après egal)."""
    if prise == "doux":
        w = np.clip(1 + 10 * (p - 0.5), 0, 2) if neutre == 1.0 else 2 * np.clip(10 * (p - 0.45), 0, 1)
    else:
        w = np.where(p > {"s50": .50, "s55": .55, "s60": .60}[prise], 2.0, 0.0)
    return np.where(np.isnan(p), neutre, w)                                         # pas de modèle -> neutre


_CP = {}


def probas(cout, lam, L, au_trade=False):
    k = (cout, lam, L, au_trade)
    if k not in _CP:
        _CP[k] = _probas(cout, lam, L, au_trade)
    return _CP[k]


def W_meta(cout, lam, L, prise, neutre=1.0):
    pr = probas(cout, lam, L)
    W = pd.DataFrame(neutre, index=JOURS, columns=FAMS)
    for f in FAMS:
        w = _poids(pr[f].values, prise, neutre)
        if f not in TRADES:
            w = np.where(pr[f + "_pos"].values, w, neutre)                          # jour sans position : neutre
        W[f] = w
    return W


def grille(neutre=1.0):
    g = {}
    for l in LAMBDAS:
        for L in FENETRES:
            for p in PRISES:
                g["l%d_L%d_%s" % (l, L, p)] = (lambda c, l=l, L=L, p=p: W_meta(c, l, L, p, neutre))
    return g


# ---------------------------------------------------------------------------------------- complément trade par trade
def serie_trade(cout, lam, L, prise, neutre=1.0):
    """Série journalière (conventions S.pnl) avec poids trade par trade (or) et poids journaliers (indices)."""
    Wd = W_meta(cout, lam, L, prise, neutre)
    prt = probas(cout, lam, L, au_trade=True)
    T = S.trades(cout)
    Pf = S.pnl_fams(Wd, cout)                                                       # indices : mêmes poids que la version jugée
    We = Wd.copy()
    for f in TRADES:
        x = T[T.fam == f].reset_index(drop=True)
        w = _poids(prt[f].values, prise, neutre)
        Pf[f] = pd.Series(w * x.g.values, index=x.jour.values).groupby(level=0).sum().reindex(JOURS).fillna(0)
        We[f] = pd.Series(w, index=x.jour.values).groupby(level=0).mean().reindex(JOURS).fillna(neutre)
    return S.egal(Pf.sum(1), We)


def evalue_trade(nom, neutre=1.0):
    print("\n--- Complément (hors critère) : %s, trades or jugés à leur décision ---" % nom)
    for cout in (1.0, 2.0):
        Ser = {n: serie_trade(cout, l, L, p, neutre) for n, (l, L, p) in
               zip(GRILLE_NOMS, [(l, L, p) for l in LAMBDAS for L in FENETRES for p in PRISES])}
        Wt, W5 = S.W_tout(), S.W_suivre5(cout)
        tout, s5 = S.egal(S.pnl(Wt, cout), Wt), S.egal(S.pnl(W5, cout), W5)
        wf, choix = S.walk(Ser)
        to, so = tout.reindex(wf.index), s5.reindex(wf.index)
        pt = S.white(np.column_stack([wf - to] + [Ser[c].reindex(wf.index) - to for c in Ser]))
        p5 = S.white(np.column_stack([wf - so] + [Ser[c].reindex(wf.index) - so for c in Ser]))
        for lab, s in (("wf", wf), ("tout", to), ("suivre5", so)):
            a, b, r = S._per(s)
            print("%-8s %-10s %+9.1f %+9.1f %+9.1f" % ("x%.0f" % cout, lab, a.sum(), b.sum(), r.sum()))
        print("         t/TOUT %+.2f  t/SUIV5 %+.2f ; White : contre TOUT %.3f, contre SUIVRE5 %.3f"
              % (S.tst(wf - to), S.tst(wf - so), pt, p5))
        if cout == 1.0:
            cs = pd.Series([c for _, c in choix]).value_counts()
            print("  Choisis : " + ", ".join("%s x%d" % (k, v) for k, v in cs.head(6).items()))


if __name__ == "__main__":
    t0 = time.time()
    res = S.evalue("p3 meta", grille())
    S.ligne_csv("p3 meta", res)
    # diagnostic : taux de prise et justesse hors échantillon des classifieurs (lambda 10, L 6, spread réel)
    pr = probas(1.0, 10.0, 6); T = S.trades(1.0); P1 = S.pnl_fams(S.W_tout(), 1.0)
    print("\nDiagnostic (l10_L6, spread réel, 02/2023 ->) : par famille, part des signaux pris (p > 0,5), "
          "taux de gain pris / non pris")
    for f in FAMS:
        if f in TRADES:
            x = T[T.fam == f]; p = pr[f].reindex(x.jour).values; y = x.g.values > 0; j = x.jour.values
        else:
            k = pr[f + "_pos"].values; p = pr[f].values[k]; y = P1[f].values[k] > 0; j = JOURS[k]
        m = (pd.DatetimeIndex(j) >= S.OOS) & ~np.isnan(p)
        pp, yy = p[m] > 0.5, y[m]
        print("  %-12s n %4d  pris %4.0f %%  gain pris %4.0f %%  non pris %4.0f %%" % (
            f, m.sum(), 100 * pp.mean(), 100 * yy[pp].mean() if pp.any() else np.nan,
            100 * yy[~pp].mean() if (~pp).any() else np.nan))
    evalue_trade("p3 meta (trade par trade)")
    # CONTRÔLE AJOUTÉ APRÈS le premier lancement (non préenregistré, hors CSV) : avec neutre = 1, une famille
    # journalière « toujours prise » reçoit 2 les jours de position et 1 les jours sans position -> levier gratuit
    # que l'exposition égale ne voit presque pas (repli_ind n'est en position que ~25 % des jours) ; idem le repli
    # « pas de modèle -> 1 » face à « pris -> 2 ». Contrôle : neutre = 2 (jours sans position, sans trade dans le
    # complément, sans modèle) et doux = 2 x clip(10 (p - 0,45), 0, 1) ; « tout prendre » redevient alors TOUT.
    S.evalue("p3 meta controle neutre2 (hors CSV)", grille(2.0))
    evalue_trade("p3 meta controle neutre2 (trade par trade)", 2.0)
    print("%.0f s" % (time.time() - t0))
