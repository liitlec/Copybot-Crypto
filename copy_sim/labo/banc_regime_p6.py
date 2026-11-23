"""Banc Lot B, piste 6 : les informations de DEBUT DE JOURNEE fixent-elles les poids des 6 familles du socle ?
(PRIORITES 23/11, deux lots en parallele ; socle commun regime_socle.py, non modifie ; memes familles, memes couts,
meme walk-forward 6 mois / 1 mois, exposition egale, White, critere fixe d'avance.)

Informations utilisees, toutes connues au DEBUT du jour serveur J (minuit serveur = 17 h New York) :
  VIX     : cloture New York de J-1 (S.vix_connu : date NY D -> utilisable au jour serveur D+1 ; la cloture de 16 h NY
            = 23 h serveur, donc avant minuit serveur). Niveau, et variation sur 5 jours ouvres (vix(J)/vix(J-5) - 1).
  GVZ     : volatilite implicite de l'or (CBOE, FRED GVZCLS), DISPONIBLE ; decalage prudent du socle : valeur datee D
            utilisable au jour serveur D+2 (comme S.fred_connu). Etat « haut » = GVZ connu > mediane glissante des
            250 jours precedents de la serie DEJA decalee. Cache : donnees/regime_gvz.csv.gz.
  ECART   : l'ecart d'ouverture du jour J lui-meme (premiere bougie H1 de J contre cloture de la veille) N'EST PAS
            connu au debut de J, et le socle applique le poids du jour a TOUS les trades decides pendant J (des 00:00) :
            on ne peut pas y decaler la decision a 08:00. On prend donc l'ecart de la seance PRECEDENTE :
            |ouverture de la 1re bougie H1 de J-1 - cloture de la derniere bougie H1 avant J-1| / amplitude H1 moyenne
            des 24 bougies avant J-1. Toutes ces bougies sont fermees avant minuit serveur de J. Etat « grand » = > 1.
  ANNONCE : J est un jour d'annonce US programmee : emploi (NFP) et inflation (CPI) a 8 h 30 NY = 15:30 serveur,
            decision FOMC 14 h NY = 21:00 serveur. Les DATES sont publiees des mois a l'avance (calendriers BLS et Fed ;
            reports de 2025 annonces avant la date) ; les RESULTATS ne sont pas utilises. Dates : FOMC = donnees/fomc.csv,
            NFP / CPI = listes reconstruites de banc_annonces_levier.py (NFP_A + NFP_B, CPI_A + CPI_B), recopiees ici.
  COT     : positionnement net des non-commerciaux de l'or / interet ouvert (S.cot_or : connu au rapport + 13 j,
            prudent). Rang centile parmi les 750 jours precedents (connus). Etat « extreme » = rang > 0,9 ou < 0,1.

Grille FIXEE D'AVANCE (21 reglages ; poids 0..2 par famille ; aucun reglage sur la periode reservee >= 05/2026 :
seuils et formes ecrits avant tout calcul, le walk-forward du socle choisit chaque mois sur les 6 mois precedents) :
  neutre             : toutes les familles a 1 (= TOUT, pour que le walk-forward puisse ne rien faire).
  Regles a seuil (a priori economiques, rien d'appris) :
  r_vix20 / r_vix25  : VIX connu > 20 (resp. 25) -> retour a la moyenne des indices (repli_ind, rebond_nas) 2,
                       tendance_sp 0 ; sinon tout a 1.
  r_vixhausse        : VIX + 15 % sur 5 jours -> meme motif.
  r_gvz              : GVZ haut -> cassure_h1 2, retour_h1 0 ; GVZ bas -> cassure_h1 0, retour_h1 2 ; autres a 1.
  r_annonce_pause    : jour d'annonce -> familles or H1 (bt_or_h1, cassure_h1, retour_h1) a 0 ; sinon 1.
  r_annonce_cassure  : jour d'annonce -> cassure_h1 2, retour_h1 0 ; sinon 1.
  r_ecart            : grand ecart de la seance precedente -> cassure_h1 2, retour_h1 0 ; sinon 1.
  r_cot              : COT extreme -> retour_h1 2, cassure_h1 0, bt_or_h1 0,5 ; sinon 1.
  Poids appris par case (6 etats binaires x 2 retrecissements = 12) : etats vix20, vixhausse, gvz, annonce, ecart,
  cot. Pour chaque mois m (des 09/2022), sur les jours de [m - 6 mois, m) : P&L par famille au poids 1 (meme cout
  que la serie jugee) ; pour les familles or H1, SEULS les trades SORTIS avant m (fin < m) ; pour les familles
  journalieres, les jours < m (clotures D1 connues avant minuit serveur). Pour chaque famille f et chaque valeur v de
  l'etat : t = t de Student du P&L de f les jours ou l'etat vaut v ; poids des jours de m ou l'etat vaut v =
  clip(1 + lam x t, 0, 2), lam in {0,25 ; 0,5} (retrecissement : t = 2 donne 1,5 ou 2) ; moins de 15 jours -> 1.
  Noms : a_<etat>_<lam>.
Lecture : S.evalue("p6 debut", grille) puis S.ligne_csv("p6 debut", res). Usage : python3 banc_regime_p6.py
"""
import os, io, time
import numpy as np, pandas as pd
import regime_socle as S

t0 = time.time()
J = S.JOURS
FAMS = S.FAMS
OR3 = ["bt_or_h1", "cassure_h1", "retour_h1"]

# ------------------------------------------------------------------------------------------------ calendrier
NFP = ["2022-08-05", "2022-09-02", "2022-10-07", "2022-11-04", "2022-12-02", "2023-01-06", "2023-02-03", "2023-03-10",
       "2023-04-07", "2023-05-05", "2023-06-02", "2023-07-07", "2023-08-04", "2023-09-01", "2023-10-06", "2023-11-03",
       "2023-12-08", "2024-01-05", "2024-02-02", "2024-03-08", "2024-04-05", "2024-05-03", "2024-06-07", "2024-07-05",
       "2024-08-02", "2024-09-06",
       "2024-10-04", "2024-11-01", "2024-12-06", "2025-01-10", "2025-02-07", "2025-03-07", "2025-04-04", "2025-05-02",
       "2025-06-06", "2025-07-03", "2025-08-01", "2025-09-05", "2025-11-20", "2025-12-16", "2026-01-09", "2026-02-11",
       "2026-03-06", "2026-04-03", "2026-05-08", "2026-06-05", "2026-07-02", "2026-08-07", "2026-09-04", "2026-10-02",
       "2026-11-06"]
CPI = ["2022-08-10", "2022-09-13", "2022-10-13", "2022-11-10", "2022-12-13", "2023-01-12", "2023-02-14", "2023-03-14",
       "2023-04-12", "2023-05-10", "2023-06-13", "2023-07-12", "2023-08-10", "2023-09-13", "2023-10-12", "2023-11-14",
       "2023-12-12", "2024-01-11", "2024-02-13", "2024-03-12", "2024-04-10", "2024-05-15", "2024-06-12", "2024-07-11",
       "2024-08-14", "2024-09-11",
       "2024-10-10", "2024-11-13", "2024-12-11", "2025-01-15", "2025-02-12", "2025-03-12", "2025-04-10", "2025-05-13",
       "2025-06-11", "2025-07-15", "2025-08-12", "2025-09-11", "2025-10-24", "2025-12-18", "2026-01-13", "2026-02-13",
       "2026-03-11", "2026-04-10", "2026-05-12", "2026-06-10", "2026-07-14", "2026-08-12", "2026-09-11", "2026-10-14",
       "2026-11-10"]
FOMC = list(pd.read_csv(os.path.join(S.DONL, "fomc.csv")).annonce)
ANN = pd.DatetimeIndex(pd.to_datetime(NFP + CPI + FOMC)).unique()
annonce = pd.Series(J.isin(ANN), index=J)              # date programmee connue d'avance ; jour serveur = date NY

# ------------------------------------------------------------------------------------------------ etats
vix = S.vix_connu()                                      # cloture NY de J-1
vixhausse = vix / vix.shift(5) - 1                       # les deux termes connus au debut de J


def gvz_connu():
    ch = os.path.join(S.DONL, "regime_gvz.csv.gz")
    if not os.path.exists(ch):
        txt = S._get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=GVZCLS&cosd=2017-01-01")
        s = pd.to_numeric(pd.read_csv(io.StringIO(txt), index_col=0, parse_dates=True).iloc[:, 0], errors="coerce")
        s.dropna().to_frame("GVZCLS").to_csv(ch, float_format="%.4f")
    s = pd.read_csv(ch, index_col=0, parse_dates=True)["GVZCLS"].dropna()
    s.index = s.index + pd.Timedelta(days=2)             # decalage prudent du socle (FRED : D -> J = D+2)
    return s.reindex(s.index.union(J)).ffill().reindex(J)


gvz = gvz_connu()
gvz_haut = gvz > gvz.rolling(250, min_periods=120).median().shift(1)   # mediane des jours precedents, deja decales

# ecart d'ouverture de la seance precedente (J-1), calcule sur les bougies H1 fermees avant minuit de J
h = S.OR_H1
jr = h.index.floor("D")
prem = ~pd.Series(jr, index=h.index).duplicated()               # 1re bougie de chaque jour serveur
amp24 = (h["haut"] - h["bas"]).rolling(24).mean().shift(1)       # 24 bougies AVANT la 1re bougie du jour
ec = ((h["ouverture"] - h["cloture"].shift(1)).abs() / amp24)[prem.values]
ec.index = ec.index.floor("D")
ecart_j = ec.reindex(J)                                          # ecart du jour J (NON connu au debut de J)
ecart_prec = ec.shift(1).reindex(J)                              # ecart de la seance d'avant : connu au debut de J
# (shift sur la serie des jours de cotation de l'or : la seance precedente reelle, week-end compris)
ecart_grand = ecart_prec > 1.0

cot = S.cot_or()                                                 # connu au rapport + 13 j
cr = (cot["spec_net"] / cot["oi"]).rolling(750, min_periods=250).rank(pct=True)
cot_ext = (cr > 0.9) | (cr < 0.1)

ETATS = {"vix20": vix > 20, "vixhausse": vixhausse > 0.15, "gvz": gvz_haut, "annonce": annonce,
         "ecart": ecart_grand, "cot": cot_ext}
ETATS = {k: v.fillna(False).astype(bool) for k, v in ETATS.items()}


# ------------------------------------------------------------------------------------------------ regles
def W1():
    return pd.DataFrame(1.0, index=J, columns=FAMS)


def regle(etat, si, sinon=None):
    """si / sinon : dict famille -> poids quand l'etat est vrai / faux (autres familles a 1)."""
    def f(cout):
        W = W1()
        for fam, w in si.items():
            W.loc[etat.values, fam] = w
        for fam, w in (sinon or {}).items():
            W.loc[~etat.values, fam] = w
        return W
    return f


IND_MR = {"repli_ind": 2.0, "rebond_nas": 2.0, "tendance_sp": 0.0}
grille = {"neutre": lambda c: W1(),
          "r_vix20": regle(vix.fillna(0) > 20, IND_MR),
          "r_vix25": regle(vix.fillna(0) > 25, IND_MR),
          "r_vixhausse": regle(ETATS["vixhausse"], IND_MR),
          "r_gvz": regle(ETATS["gvz"], {"cassure_h1": 2.0, "retour_h1": 0.0}, {"cassure_h1": 0.0, "retour_h1": 2.0}),
          "r_annonce_pause": regle(ETATS["annonce"], {f: 0.0 for f in OR3}),
          "r_annonce_cassure": regle(ETATS["annonce"], {"cassure_h1": 2.0, "retour_h1": 0.0}),
          "r_ecart": regle(ETATS["ecart"], {"cassure_h1": 2.0, "retour_h1": 0.0}),
          "r_cot": regle(ETATS["cot"], {"retour_h1": 2.0, "cassure_h1": 0.0, "bt_or_h1": 0.5})}

# ------------------------------------------------------------------------------------------------ poids appris
_PJ = {}


def _apprentissage(cout):
    """Pour chaque famille : (jour de decision, P&L en u, instant ou il devient connu)."""
    if cout not in _PJ:
        P = S.pnl_fams(W1(), cout)
        T = S.trades(cout)
        out = {}
        for f in FAMS:
            if f in OR3:
                x = T[T.fam == f]
                out[f] = pd.DataFrame({"jour": x.jour.values, "g": x.g.values, "connu": x.fin.values})
            else:   # position journaliere du jour d : connue a la fin de d (cloture D1 avant minuit serveur)
                out[f] = pd.DataFrame({"jour": J, "g": P[f].values, "connu": J + pd.Timedelta(days=1)})
        _PJ[cout] = out
    return _PJ[cout]


def appris(etat, lam, nmin=15):
    def f(cout):
        A = _apprentissage(cout)
        W = W1()
        mois = pd.date_range(S.DEBUT + pd.offsets.MonthBegin(1), J[-1] + pd.offsets.MonthBegin(1), freq="MS")
        for m0 in mois:
            a0 = m0 - pd.DateOffset(months=6)
            kt = (J >= m0) & (J < m0 + pd.offsets.MonthBegin(1))
            if not kt.any():
                continue
            for fam in FAMS:
                x = A[fam]
                x = x[(x.jour >= a0) & (x.jour < m0) & (x.connu <= m0)]          # seulement ce qui est connu en m0
                g = x.groupby("jour").g.sum().reindex(J[(J >= a0) & (J < m0)]).fillna(0.0)
                if fam not in OR3:
                    g = g[g.index < m0]
                e = etat.reindex(g.index).values
                for v in (True, False):
                    gv = g[e == v]
                    w = 1.0 if len(gv) < nmin else float(np.clip(1 + lam * S.tst(gv), 0, 2))
                    W.loc[kt & (etat.values == v), fam] = w
        return W
    return f


for k, e in ETATS.items():
    for lam in (0.25, 0.5):
        grille["a_%s_%s" % (k, lam)] = appris(e, lam)

if __name__ == "__main__":
    print("Etats (part des jours vrais 02/2023 -> fin) : " + ", ".join(
        "%s %.0f %%" % (k, 100 * v[J >= S.OOS].mean()) for k, v in ETATS.items()))
    print("GVZ connu : %s -> %s ; jours d'annonce : %d ; ecart precedent median %.2f ; COT rang dispo des %s"
          % (gvz.first_valid_index().date(), gvz.last_valid_index().date(), int(annonce.sum()),
             float(ecart_prec.median()), cr.first_valid_index().date()))
    res = S.evalue("p6 debut", grille)
    S.ligne_csv("p6 debut", res)
    print("Choix mois par mois (spread reel) : " + " ".join("%s:%s" % c for c in res[1.0]["choix"]))
    print("%.0f s" % (time.time() - t0))
