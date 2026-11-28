"""Lot B, piste 5 : REGIME COMMUN or / indices / dollar / taux, connu au debut du jour serveur J (socle regime_socle).

Idee : decrire l'etat commun des marches (tendance et volatilite de l'or, des indices, du dollar, du taux reel 10 ans,
de la pente 10 ans - 2 ans, correlations glissantes or/dollar, or/taux reel, or/indices), le ranger en quelques
etats, et donner a chaque etat des poids de familles (0 a 2), soit fixes a la main d'avance, soit appris.

Informations utilisees et DECALAGES (chaque serie est rangee sur sa date « native » D puis rendue connue a D + lag,
derniere valeur connue reportee sur les jours serveur) :
  - or : cloture de la derniere bougie H1 du jour serveur D (bougie 23 h, fermee a minuit) -> connue a J >= D + 1 j ;
    historique complet du fichier xau_h1_50k (lu avec banc_or.charge, comme le socle) pour les fenetres longues ;
  - indices SP, NAS (D1 du courtier, bougie du jour serveur D fermee a minuit) -> connus a J >= D + 1 j ;
  - VIX : S.vix_connu() (cloture New York de J-1, deja decale) ;
  - taux FRED (DGS10, DGS2, DFII10) : date D -> connu a D + 2 j (comme S.fred_connu) ;
  - dollar large DTWEXBGS : la Fed le publie UNE FOIS PAR SEMAINE (H.10, le lundi, pour la semaine d'avant) ; le
    decalage de 2 j du socle ne suffit pas -> ici date D connue a D + 10 j (prudent) ;
  - une grandeur qui melange plusieurs sources prend le decalage le plus long de ses sources (ex. correlation
    or/dollar : 10 j ; or/taux reel : 2 j ; or/SP : 1 j). Les variations sont calculees sur l'axe natif (memes dates
    pour les deux series d'une correlation), jamais entre series decalees differemment.
  - poids appris : pour le mois de test m (debut m0), apprentissage sur [m0 - 6 mois, m0) avec UNIQUEMENT des gains
    connus avant m0 : trades or H1 SORTIS avant m0 (rattaches au jour de decision), positions journalieres jusqu'a
    m0 - 1 j. Rien n'est regle sur la periode reservee (grille et logique ecrites avant tout calcul).

Grandeurs (connues au debut de J) : r20/r60 = log-rendement 20/60 jours ouvres ; v20 = ecart-type des log-rendements
20 j ; d20 = variation sur 20 j.
  or_r20, or_r60, or_v20 (et sa mediane 250 j), sp_r20, sp_r60, nas_r20, sp_v20, vix, usd_d20 (log), usd_d60,
  rr_d20 (taux reel DFII10), pente = DGS10 - DGS2 et pente_d20, c_or_usd / c_or_rr / c_or_sp = correlations 60 j des
  variations journalieres.
Etats (regroupements simples, fixes d'avance) :
  E_risk   : risk-on si sp_r60 > 0 et vix < 20, sinon risk-off (2 etats) ;
  E_or     : signes de or_r20 et or_r60 (4 etats) ;
  E_macro  : signes de usd_d20 et rr_d20 (dollar fort/faible x taux reels en hausse/baisse, 4 etats) ;
  E_volrisk: or_v20 > sa mediane 250 j (vol or haute/basse) x risk-on/off (4 etats) ;
  E_acp    : ACP glissante : au debut de chaque mois m0, les 16 grandeurs ci-dessus (sauf la mediane de vol) des 500 jours ouvres avant m0
             sont centrees-reduites (moyenne/ecart-type de cette fenetre), ACP par SVD, axes orientes (charge de or_r60
             >= 0 sur l'axe 1, de sp_r60 >= 0 sur l'axe 2) ; etat = signes des 2 premieres composantes (4 etats) ; le
             mois de test est projete avec la transformation ajustee avant m0.
Grille FIXEE D'AVANCE (N = 26) :
  (1) neutre : toutes familles a 1 (permet au walk-forward de revenir a TOUT).
  (2) 5 reglages « a la main » (logique economique ecrite avant tout calcul) :
     main_risk  : risk-on -> tendance_sp 2, repli_ind 1,5, rebond_nas 0,5 (indices qui montent dans le calme :
                  suivre et acheter les replis) ; risk-off -> tendance_sp 0,5, repli_ind 0,5, rebond_nas 1,5 (marche
                  nerveux : les exces se corrigent le lendemain, la tendance casse) ; familles or a 1.
     main_or    : or_r20 et or_r60 de meme signe (or en tendance nette) -> bt_or_h1 1,5, cassure_h1 1,5, retour_h1
                  0,5 ; signes opposes (or sans direction) -> bt_or_h1 1, cassure_h1 0,5, retour_h1 1,5 ; indices a 1.
     main_macro : dollar et taux reel varient dans le MEME sens sur 20 j (les deux moteurs de l'or poussent ensemble ->
                  mouvements directionnels) -> familles or de suivi 1,5 et retour 0,5 ; sens opposes -> suivi 0,5,
                  retour 1,5 ; indices a 1.
     main_vol   : vol or haute -> cassure_h1 1,5, bt_or_h1 1,5, retour_h1 1 ; basse -> cassure 0,5, bt 1, retour
                  1,5 ; et regle main_risk pour les indices.
     main_comb  : moyenne des poids de main_risk, main_or et main_macro.
  (3) 20 reglages appris = 5 etats (E_risk, E_or, E_macro, E_volrisk, E_acp) x retrecissement k (20 ou 60 jours) x
      regle (binaire / proportionnelle). Pour chaque etat s et famille f sur la fenetre d'apprentissage : g_sf =
      gain moyen par jour de f quand l'etat vaut s (n_s jours), g_f = moyenne sur toute la fenetre ;
      g^ = (n_s g_sf + k g_f) / (n_s + k). binaire : poids 2 si g^ > 0, sinon 0 ; proportionnelle : poids =
      min(2, max(0, 1 + 4 g^ / e_f)) ou e_f = ecart-type journalier de f sur la fenetre.
Evaluation et critere : ceux du socle (S.evalue : walk-forward 6 mois / 1 mois, exposition egale, White, spread
reel et double). Usage : python3 banc_regime_p5.py
"""
import contextlib, io, time
import numpy as np, pandas as pd
import regime_socle as S
with contextlib.redirect_stdout(io.StringIO()):
    import banc_or as B

JOURS, FAMS = S.JOURS, S.FAMS
OR_FAM = ["bt_or_h1", "cassure_h1", "retour_h1"]


# ------------------------------------------------------------------------------------------------ grandeurs
def _connu(s, lag):
    """Serie datee D (date native) -> valeur connue au debut du jour serveur J (derniere date D <= J - lag jours)."""
    s = s.dropna().copy(); s.index = s.index + pd.Timedelta(days=lag)
    s = s[~s.index.duplicated(keep="last")]
    return s.reindex(s.index.union(JOURS)).ffill().reindex(JOURS)


def _grandeurs():
    d, _ = B.charge("xau_h1_50k")
    d = d[d.index.dayofweek < 5]
    orj = np.log(d["cloture"].groupby(d.index.floor("D")).last())          # cloture du jour serveur D (bougie 23 h)
    sp = np.log(S.IND["SP"]["cloture"]); sp = sp[sp.index.dayofweek < 5]
    nas = np.log(S.IND["NAS"]["cloture"]); nas = nas[nas.index.dayofweek < 5]
    F = S.fred(); F = F[F.index.dayofweek < 5]
    usd = np.log(F["DTWEXBGS"].dropna()); rr = F["DFII10"].dropna(); pente = (F["DGS10"] - F["DGS2"]).dropna()
    G = {}
    # or et indices : decalage 1 j (bougies fermees a minuit serveur du jour D)
    G["or_r20"], G["or_r60"] = _connu(orj.diff(20), 1), _connu(orj.diff(60), 1)
    v = orj.diff().rolling(20).std()
    G["or_v20"], G["or_v20_med"] = _connu(v, 1), _connu(v.rolling(250, min_periods=120).median(), 1)
    G["sp_r20"], G["sp_r60"], G["nas_r20"] = _connu(sp.diff(20), 1), _connu(sp.diff(60), 1), _connu(nas.diff(20), 1)
    G["sp_v20"] = _connu(sp.diff().rolling(20).std(), 1)
    G["vix"] = S.vix_connu()                                                # cloture NY de J-1 (socle)
    # dollar : publication hebdomadaire -> 10 j ; taux : 2 j
    G["usd_d20"], G["usd_d60"] = _connu(usd.diff(20), 10), _connu(usd.diff(60), 10)
    G["rr_d20"] = _connu(rr.diff(20), 2)
    G["pente"], G["pente_d20"] = _connu(pente, 2), _connu(pente.diff(20), 2)
    # correlations 60 j sur l'axe natif commun (memes dates), decalage = le plus long des deux sources
    def corr(a, b, lag):
        x = pd.concat([a.diff(), b.diff()], axis=1, join="inner").dropna()
        return _connu(x.iloc[:, 0].rolling(60, min_periods=40).corr(x.iloc[:, 1]), lag)
    G["c_or_usd"], G["c_or_rr"], G["c_or_sp"] = corr(orj, usd, 10), corr(orj, rr, 2), corr(orj, sp, 1)
    return pd.DataFrame(G)


G = _grandeurs()
ACP_COLS = ["or_r20", "or_r60", "or_v20", "sp_r20", "sp_r60", "nas_r20", "sp_v20", "vix", "usd_d20", "usd_d60",
            "rr_d20", "pente", "pente_d20", "c_or_usd", "c_or_rr", "c_or_sp"]      # 16 grandeurs


def _sg(x):
    return (x > 0).astype(int)


RISK_ON = ((G.sp_r60 > 0) & (G.vix < 20)).astype(int)
ETATS = {
    "risk": RISK_ON,
    "or": _sg(G.or_r20) * 2 + _sg(G.or_r60),
    "macro": _sg(G.usd_d20) * 2 + _sg(G.rr_d20),
    "volrisk": (G.or_v20 > G.or_v20_med).astype(int) * 2 + RISK_ON,
}


def _etat_acp():
    """Etat ACP : ajustement au debut de chaque mois sur les 500 jours ouvres d'avant (passe seulement)."""
    out = pd.Series(np.nan, index=JOURS)
    X = G[ACP_COLS]
    mois = pd.date_range(JOURS[0], JOURS[-1] + pd.offsets.MonthBegin(1), freq="MS")
    for m0 in mois:
        k = (JOURS >= m0) & (JOURS < m0 + pd.offsets.MonthBegin(1))
        if not k.any():
            continue
        hist = X[X.index < m0].dropna().iloc[-500:]
        if len(hist) < 250:
            continue
        mu, sd = hist.mean(), hist.std().replace(0, 1)
        Z = ((hist - mu) / sd).values
        _, _, Vt = np.linalg.svd(Z, full_matrices=False)
        v1, v2 = Vt[0], Vt[1]
        if v1[ACP_COLS.index("or_r60")] < 0: v1 = -v1
        if v2[ACP_COLS.index("sp_r60")] < 0: v2 = -v2
        Zm = ((X[k] - mu) / sd).ffill().fillna(0).values      # jours du mois, transformation ajustee avant m0
        out[k] = (Zm @ v1 > 0).astype(int) * 2 + (Zm @ v2 > 0).astype(int)
    return out


# l'ACP d'un mois m0 n'utilise que des grandeurs connues avant m0 ; l'etat du mois m0 sert aux jours de m0 (test) et,
# pour les mois suivants, de jours d'apprentissage (passes) : aucune information future.
ETATS["acp"] = _etat_acp()


# ------------------------------------------------------------------------------------------------ poids a la main
def _W(d):
    return pd.DataFrame({f: d.get(f, pd.Series(1.0, index=JOURS)) for f in FAMS}, index=JOURS).fillna(1.0)


def _main_risk():
    on = RISK_ON == 1
    return _W({"tendance_sp": pd.Series(np.where(on, 2.0, 0.5), index=JOURS),
               "repli_ind": pd.Series(np.where(on, 1.5, 0.5), index=JOURS),
               "rebond_nas": pd.Series(np.where(on, 0.5, 1.5), index=JOURS)})


def _or_suivi(cond):
    """cond vrai -> familles or de suivi favorisees ; faux -> retour favorise."""
    return {"bt_or_h1": pd.Series(np.where(cond, 1.5, 1.0), index=JOURS),
            "cassure_h1": pd.Series(np.where(cond, 1.5, 0.5), index=JOURS),
            "retour_h1": pd.Series(np.where(cond, 0.5, 1.5), index=JOURS)}


def _main_or():
    return _W(_or_suivi((np.sign(G.or_r20) == np.sign(G.or_r60)).values))


def _main_macro():
    c = (np.sign(G.usd_d20) == np.sign(G.rr_d20)).values
    d = _or_suivi(c); d["bt_or_h1"] = pd.Series(np.where(c, 1.5, 0.5), index=JOURS)
    return _W(d)


def _main_vol():
    h = (G.or_v20 > G.or_v20_med).values
    W = _main_risk()
    W["cassure_h1"], W["bt_or_h1"], W["retour_h1"] = np.where(h, 1.5, 0.5), np.where(h, 1.5, 1.0), np.where(h, 1.0, 1.5)
    return W


def _main_comb():
    return (_main_risk() + _main_or() + _main_macro()) / 3.0


# ------------------------------------------------------------------------------------------------ poids appris
_GAINS = {}


def _gains(cout):
    """(P journalier par famille, poids 1, par jour de decision ; trades or avec jour de decision et heure de sortie)."""
    if cout not in _GAINS:
        P = S.pnl_fams(S.W_tout(), cout)
        T = S.trades(cout)
        _GAINS[cout] = (P, T)
    return _GAINS[cout]


def _appris(etat, k, regle):
    def f(cout):
        P, T = _gains(cout)
        st = ETATS[etat]
        W = pd.DataFrame(1.0, index=JOURS, columns=FAMS)
        for m0 in pd.date_range(JOURS[0], JOURS[-1] + pd.offsets.MonthBegin(1), freq="MS"):
            km = (JOURS >= m0) & (JOURS < m0 + pd.offsets.MonthBegin(1))
            if not km.any():
                continue
            a0 = m0 - pd.DateOffset(months=6)
            jA = JOURS[(JOURS >= a0) & (JOURS < m0)]
            if len(jA) < 60:
                continue
            # gains connus avant m0 : trades sortis avant m0 ; positions journalieres jusqu'a m0 - 1 j
            Ga = pd.DataFrame(0.0, index=jA, columns=FAMS)
            for fam in FAMS:
                if fam in OR_FAM:
                    x = T[(T.fam == fam) & (T.jour >= a0) & (T.fin <= m0)]
                    Ga[fam] = x.groupby("jour").g.sum().reindex(jA).fillna(0.0)
                else:
                    Ga[fam] = P[fam].reindex(jA).fillna(0.0)
            sA = st.reindex(jA)
            ok = sA.notna()
            if ok.sum() < 60:
                continue
            Ga, sA = Ga[ok], sA[ok]
            gf, ef = Ga.mean(), Ga.std().replace(0, 1.0)
            st_m = st[km]
            Wm = pd.DataFrame(1.0, index=JOURS[km], columns=FAMS)
            for s in sA.unique():
                gs = Ga[sA == s]; n = len(gs)
                gh = (n * gs.mean() + k * gf) / (n + k)
                w = (gh > 0).astype(float) * 2.0 if regle == "bin" else (1 + 4 * gh / ef).clip(0, 2)
                Wm.loc[(st_m == s).values, :] = w.values
            # etat jamais vu sur l'apprentissage (ou inconnu) : poids 1
            W.loc[km] = Wm.values
        return W
    return f


GRILLE = {"neutre": lambda c: S.W_tout(),
          "main_risk": lambda c: _main_risk(), "main_or": lambda c: _main_or(), "main_macro": lambda c: _main_macro(),
          "main_vol": lambda c: _main_vol(), "main_comb": lambda c: _main_comb()}
for e in ("risk", "or", "macro", "volrisk", "acp"):
    for k in (20, 60):
        for regle in ("bin", "prop"):
            GRILLE["app_%s_k%d_%s" % (e, k, regle)] = _appris(e, k, regle)


if __name__ == "__main__":
    t0 = time.time()
    print("Grandeurs connues au debut de J (moyennes 2023-02 -> fin, NaN restants) :")
    g = G[G.index >= S.OOS]
    print(pd.DataFrame({"moy": g.mean(), "nan": g.isna().sum()}).round(4).T.to_string())
    for e, s in ETATS.items():
        print("  etat %-8s frequences : %s" % (e, s[s.index >= S.OOS].value_counts(normalize=True).round(2).sort_index().to_dict()))
    res = S.evalue("p5 commun", GRILLE)
    S.ligne_csv("p5 commun", res)
    print("  Choix par mois (spread reel) : " + " ".join("%s:%s" % (m, c) for m, c in res[1.0]["choix"]))
    print("%.0f s" % (time.time() - t0))
