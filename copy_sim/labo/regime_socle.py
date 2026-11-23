"""Socle commun du Lot B (PRIORITES 23/11 « deux lots en parallele ») : determiner le type de marche EN DIRECT.
Toutes les pistes (banc_regime_p1.py ... p7.py) utilisent ce socle, pour etre comparables. Rien n'est regle ici.

Calendrier : jour = jour du SERVEUR du courtier (New York + 7 h ; minuit serveur = 17 h New York), lundi-vendredi,
du 01/08/2022 a la fin des bougies H1 de l'or (11/2026). Les poids d'un jour J (un par famille, 0 a 2) ne peuvent
utiliser que ce qui est connu au DEBUT de J : bougies H1 de l'or fermees avant minuit serveur, bougies D1 des indices
du courtier jusqu'a J-1, P&L des familles connu avant J (trades SORTIS avant J ; positions journalieres jusqu'a J-1),
VIX / taux / dollar FRED avec 2 jours de decalage, COT avec 13 jours apres la date du rapport (prudent).

Familles (fixes, issues du labo ; aucune nouvelle regle) :
  bt_or_h1    : mecanique bt_or rejouee en H1 (banc_bt_regulier.simule, reglages H1 de banc_thermometre (3)) ; gain en R
                du panier, rattache au jour d'OUVERTURE du panier (decision) ; poids = celui de ce jour.
  cassure_h1  : or H1, suit la sortie de la fourchette des 12 H1 precedentes, tenue 3 h (banc_or.trades) ; jour de decision.
  retour_h1   : or H1, contre cette meme sortie, tenue 3 h.
  repli_ind   : S&P, Nasdaq, Dow, Russell (D1 du courtier) : RSI 2 < 10 et cloture > moyenne 200 -> achat a la cloture,
                sortie cloture > moyenne 5 ou 10 jours ; moyenne des 4 ; position JOURNALIERE (poids applique chaque jour).
  rebond_nas  : Nasdaq D1 : apres une journee d'amplitude > 1,5 x mediane 20 j, jouer contre son sens le lendemain
                (ouverture -> cloture) ; position journaliere.
  tendance_sp : S&P D1 : acheteur si moyenne 50 > moyenne 200, vendeur sinon ; position journaliere.
Couts : spread reel du courtier (x cout : 1 = reel, 2 = double) a chaque entree/sortie ; pour les positions
journalieres, un changement de poids paie aussi le spread sur la taille changee ; financement de nuit (IRX + 2,5 %)
sur les positions d'indices tenues la nuit.
Unite : chaque famille est mise a l'echelle pour que son P&L journalier ait un ecart-type de 1 sur la periode de
chauffe 01/08/2022 -> 31/01/2023 (avant tout hors echantillon). Gains exprimes en « u » (1 u = 1 ecart-type
journalier d'une famille pendant la chauffe).

References (obligatoires) : TOUT = toutes les familles poids 1 ; SUIVRE5 = poids 2 si le P&L CONNU de la famille sur
ses 5 derniers jours ouvres est > 0, sinon 0 (banc_famille_wf, L = 5 j, poids 2/0).
Evaluation (evalue) : walk-forward glissant, apprentissage 6 mois, test 1 mois, du 01/02/2023 a la fin ; le reglage
du mois de test = meilleur t (gain par jour) sur l'apprentissage (meme cout que la serie jugee). Chaque mois de test
est mis a EXPOSITION EGALE : x (somme des poids TOUT) / (somme des poids du candidat) sur le mois (exposition
seulement, jamais le P&L). Memes regles pour SUIVRE5. Periodes : P1 = 02/2023-07/2024 (« 2022-2024 »),
P2 = 08/2024-11/2026 (« 2024-2026 »), dont la periode reservee RES = 05/2026-11/2026 (montree a part).
Correction pour essais multiples : reality check de White (bootstrap stationnaire, blocs moyens 5 j, 2000 tirages)
sur les N reglages de la piste ET la serie walk-forward, difference contre TOUT et contre SUIVRE5 sur tout le hors
echantillon ; p corrige = le plus grand des deux. Critere (fixe d'avance, PRIORITES 23/11) : retenu si, au spread
reel, le walk-forward gagne en P1 ET en P2, bat TOUT et SUIVRE5 en P1 ET en P2, p corrige < 0,05, et bat encore
les deux references en P1 et P2 au spread double. Correction finale entre les 7 pistes : Holm (dans AVIS).
"""
import contextlib, io, os, json, time, urllib.request, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_or as B
    import banc_bt_regulier as BR

ICI = os.path.dirname(os.path.abspath(__file__))
DONL = os.path.join(ICI, "donnees")
DEBUT, CHAUFFE_FIN, OOS = pd.Timestamp("2022-08-01"), pd.Timestamp("2023-01-31"), pd.Timestamp("2023-02-01")
P1_FIN, RES = pd.Timestamp("2024-07-31"), pd.Timestamp("2026-05-01")
FAMS = ["bt_or_h1", "cassure_h1", "retour_h1", "repli_ind", "rebond_nas", "tendance_sp"]
TRADES = ["bt_or_h1", "cassure_h1", "retour_h1"]          # familles par trade (poids du jour de decision)
H1_HEURES = {(2, 0), (7, 0), (11, 0), (14, 0), (15, 0)}

# ------------------------------------------------------------------------------------------------ donnees
dh, _ = B.charge("xau_h1_50k")
dh = dh[dh.index >= DEBUT - pd.Timedelta(days=40)]
OR_H1 = dh                                                     # index = debut de bougie (heure serveur)
FIN = dh.index[-1].floor("D")
JOURS = pd.DatetimeIndex(sorted(set(dh.index.floor("D"))))
JOURS = JOURS[(JOURS >= DEBUT) & (JOURS <= FIN) & (JOURS.dayofweek < 5)]
IND = {}
for k, f in (("SP", "sp_d1_5k"), ("NAS", "nas_d1_5k"), ("DJ", "dj_d1_5k"), ("RUT", "us2000_d1_5k")):
    d, _ = B.charge(f)
    IND[k] = d[~d.index.duplicated()].sort_index()
_ij = pd.read_csv(os.path.join(DONL, "indices_jour.csv.gz"), index_col=0, parse_dates=True)
VIX = _ij["VIX_close"].dropna()                                 # date New York ; connu a partir du jour serveur J+1
IRX = _ij["IRX_close"].dropna()


def finance(idx):
    """Cout de financement d'une nuit (fraction du notionnel) par jour de idx (week-end : jusqu'a 3 nuits)."""
    irx = IRX.reindex(idx, method="ffill").fillna(3.0)
    nuits = pd.Series(idx, index=idx).diff().dt.days.fillna(1).clip(1, 4)
    return (irx / 100 + 0.025) / 360 * nuits


# ------------------------------------------------------------------------------------------------ familles
def _fam_trades(cout):
    """Trades des familles or H1 : DataFrame (fam, jour de decision, fin = heure de sortie, g brut non mis a l'echelle)."""
    d = dh.copy(); d["sp"] = d["sp"] * cout
    dd = d.reset_index(drop=True)
    P = BR.simule(dd, span=48, heures=H1_HEURES, debut=60)
    out = [pd.DataFrame({"fam": "bt_or_h1", "dec": pd.to_datetime(P.t0, unit="s"),
                         "fin": pd.to_datetime(P.t1, unit="s") + pd.Timedelta("1h"), "g": P.g.values})]
    hh, bb = d["haut"].shift(1).rolling(12).max(), d["bas"].shift(1).rolling(12).min()
    sc = (d["cloture"] > hh).astype(float) - (d["cloture"] < bb).astype(float)
    for nom, s in (("cassure_h1", sc), ("retour_h1", -sc)):
        x, i = B.trades(d, s, 3, mult=1.0)
        out.append(pd.DataFrame({"fam": nom, "dec": d.index[i] + pd.Timedelta("1h"),
                                 "fin": d.index[np.minimum(i + 3, len(d) - 1)] + pd.Timedelta("1h"), "g": x[:, 0]}))
    T = pd.concat(out, ignore_index=True)
    T["jour"] = T.dec.dt.floor("D")
    return T[(T.jour >= DEBUT) & (T.jour <= FIN)].reset_index(drop=True)


def _fam_jour(cout):
    """Familles journalieres : pour chacune (brut du jour J par unite de position, position du jour J, cout unitaire)."""
    R = {}
    # repli_ind : moyenne des 4 indices
    pos_l, ret_l, sp_l = [], [], []
    for k, o in IND.items():
        c = o["cloture"]; dc = c.diff(); up, dn = dc.clip(lower=0), (-dc).clip(lower=0)
        rsi = 100 - 100 / (1 + up.ewm(alpha=.5, adjust=False).mean() / dn.ewm(alpha=.5, adjust=False).mean())
        m200, m5 = c.rolling(200).mean(), c.rolling(5).mean()
        pos = pd.Series(0.0, index=c.index); i, n = 200, len(c)
        while i < n - 1:
            if rsi.iloc[i] < 10 and c.iloc[i] > m200.iloc[i]:
                j = i + 1
                while j < n - 1 and not (c.iloc[j] > m5.iloc[j] or j - i >= 10):
                    j += 1
                pos.iloc[i + 1:j + 1] = 1.0                # tenu de la cloture i a la cloture j
                i = j + 1
            else:
                i += 1
        ret = c.pct_change().fillna(0) - finance(c.index)
        pos_l.append(pos / 4); ret_l.append(ret); sp_l.append((o["sp"] / c).shift(1).bfill())
    R["repli_ind"] = (pos_l, ret_l, sp_l)
    o = IND["NAS"]; c = o["cloture"]
    amp = (o["haut"] - o["bas"]) / c.shift(1); med = amp.shift(1).rolling(20).median()
    s = -np.sign(c - c.shift(1)).where(amp > 1.5 * med, 0).shift(1).fillna(0)
    r = (o["cloture"] - o["ouverture"]) / o["ouverture"]          # intrajour : pas de nuit
    R["rebond_nas"] = ([s], [r], [o["sp"] / o["ouverture"]])
    o = IND["SP"]; c = o["cloture"]
    s = np.sign(c.rolling(50).mean() - c.rolling(200).mean()).shift(1).fillna(0)
    R["tendance_sp"] = ([s], [c.pct_change().fillna(0) - finance(c.index) * s.abs()], [o["sp"] / c.shift(1)])
    out = {}
    for f, (P, Rt, S) in R.items():
        out[f] = [(p.reindex(JOURS).fillna(0), r.reindex(JOURS).fillna(0), sp.reindex(JOURS).ffill().bfill() * cout)
                  for p, r, sp in zip(P, Rt, S)]
    out["_intrajour"] = {"rebond_nas"}
    return out


def _construit(cout):
    T = _fam_trades(cout)
    J = _fam_jour(cout)
    return T, J


_CACHE = {}


def base(cout=1.0):
    """(T, J, echelle) pour ce cout. Echelle fixee au spread reel sur la chauffe (la meme pour tous les couts)."""
    if cout not in _CACHE:
        _CACHE[cout] = _construit(cout)
    if "ech" not in _CACHE:
        T1, J1 = base(1.0)[:2] if cout != 1.0 else _CACHE[1.0]
        W1 = pd.DataFrame(1.0, index=JOURS, columns=FAMS)
        brut = _pnl_fams(T1, J1, W1, {f: 1.0 for f in FAMS})
        ch = brut[(brut.index >= DEBUT) & (brut.index <= CHAUFFE_FIN)]
        _CACHE["ech"] = {f: 1.0 / ch[f].std() for f in FAMS}
    return _CACHE[cout][0], _CACHE[cout][1], _CACHE["ech"]


def _pnl_fams(T, J, W, ech):
    """P&L journalier par famille (DataFrame jours x familles) sous les poids W (jours x familles, connus au debut de J)."""
    W = W.reindex(index=JOURS, columns=FAMS).fillna(0.0)
    out = pd.DataFrame(0.0, index=JOURS, columns=FAMS)
    for f in TRADES:
        x = T[T.fam == f]
        w = W[f].reindex(x.jour).values
        out[f] = pd.Series(w * x.g.values, index=x.jour.values).groupby(level=0).sum().reindex(JOURS).fillna(0) * ech[f]
    for f in FAMS:
        if f in TRADES:
            continue
        tot = pd.Series(0.0, index=JOURS); w = W[f]
        for p, r, sp in J[f]:
            q = w * p
            if f in J["_intrajour"]:
                cst = sp * q.abs()                             # aller-retour dans la journee : un spread entier
            else:
                cst = sp * (q - q.shift(1).fillna(0)).abs() * 0.5   # demi-spread par cote a chaque changement de taille
            tot += q * r - cst
        out[f] = tot * ech[f]
    return out


def pnl_fams(W, cout=1.0):
    T, J, ech = base(cout)
    return _pnl_fams(T, J, W, ech)


def pnl(W, cout=1.0):
    """P&L journalier total (serie) sous les poids W (DataFrame jours x FAMS, valeurs 0..2)."""
    return pnl_fams(W, cout).sum(1)


def connu(cout=1.0):
    """P&L par famille (poids 1) CONNU au debut de chaque jour J = realise strictement avant J :
    trades sortis avant minuit du jour J ; positions journalieres jusqu'a J-1. DataFrame jours x familles, par jour
    de connaissance (valeur du jour J = ce qui s'est ajoute pendant J-1 calendaire, a utiliser pour J et apres)."""
    T, J, ech = base(cout)
    W1 = pd.DataFrame(1.0, index=JOURS, columns=FAMS)
    P = _pnl_fams(T, J, W1, ech)
    K = pd.DataFrame(0.0, index=JOURS, columns=FAMS)
    for f in TRADES:
        x = T[T.fam == f]
        jf = x.fin.dt.floor("D") + pd.Timedelta(days=1)         # connu des le jour suivant la sortie
        jf = jf.where(x.fin != x.fin.dt.floor("D"), x.fin.dt.floor("D"))   # sortie pile a minuit : connu ce jour-la
        s = pd.Series(x.g.values * ech[f], index=jf.values).groupby(level=0).sum()
        K[f] = s.reindex(pd.date_range(JOURS[0], JOURS[-1] + pd.Timedelta(days=7))).fillna(0).cumsum() \
                .reindex(JOURS, method="ffill").fillna(0).diff().fillna(0)
    for f in FAMS:
        if f not in TRADES:
            K[f] = P[f].shift(1).fillna(0)
    return K


def trades(cout=1.0):
    """Trades des familles or H1 (colonnes fam, dec, fin, g en u, jour) : pour les pistes qui jugent chaque trade."""
    T, J, ech = base(cout)
    T = T.copy(); T["g"] = T.g * T.fam.map(ech)
    return T


# ------------------------------------------------------------------------------------------------ references
def W_tout():
    return pd.DataFrame(1.0, index=JOURS, columns=FAMS)


def W_suivre5(cout=1.0):
    K = connu(cout)
    return (K.rolling(5, min_periods=1).sum() > 0).astype(float) * 2.0


# ------------------------------------------------------------------------------------------------ statistiques
tst = lambda x: float(x.mean() / x.std() * np.sqrt(len(x))) if len(x) > 2 and x.std() > 0 else 0.0
_rng = np.random.default_rng(23)


def boot(n, Bn=2000, b=5.0, rng=None):
    rng = rng or _rng
    out = np.empty((Bn, n), int)
    for k in range(Bn):
        neuf = rng.random(n) < 1 / b; neuf[0] = True
        bl = np.cumsum(neuf) - 1; deb = np.flatnonzero(neuf)
        out[k] = (rng.integers(n, size=len(deb))[bl] + np.arange(n) - deb[bl]) % n
    return out


def white(Dm):
    """Reality check de White (studentise) : Dm = matrice jours x strategies de differences ; p du meilleur."""
    Dm = np.asarray(Dm, float); n = len(Dm)
    sd = Dm.std(0); sd[sd == 0] = np.inf
    mu = Dm.mean(0); V = (np.sqrt(n) * mu / sd).max()
    ii = boot(n, rng=np.random.default_rng(23))
    Vb = np.array([(np.sqrt(n) * (Dm[k].mean(0) - mu) / sd).max() for k in ii])
    return float((Vb >= V).mean())


MOIS = pd.date_range(OOS, JOURS[-1] + pd.offsets.MonthBegin(1), freq="MS")


def _expo(W):
    return W.reindex(index=JOURS, columns=FAMS).fillna(0).sum(1)


def egal(S, W):
    """Met la serie S (poids W) a exposition egale a TOUT, mois par mois (exposition seulement)."""
    e = _expo(W); out = S.copy()
    for m0 in pd.date_range(DEBUT, JOURS[-1] + pd.offsets.MonthBegin(1), freq="MS"):
        k = (S.index >= m0) & (S.index < m0 + pd.offsets.MonthBegin(1))
        em = e[k].mean()
        out[k] = S[k] * (len(FAMS) / em if em > 0 else 0.0)
    return out


def walk(series):
    """series : dict cfg -> serie journaliere (deja a exposition egale). Rend (serie hors echantillon, choix par mois)."""
    oos, choix = [], []
    for m0 in MOIS:
        a0 = m0 - pd.DateOffset(months=6)
        ka = lambda s: s[(s.index >= a0) & (s.index < m0)]
        kt = lambda s: s[(s.index >= m0) & (s.index < m0 + pd.offsets.MonthBegin(1))]
        best = max(series, key=lambda c: tst(ka(series[c])))
        oos.append(kt(series[best])); choix.append((m0.strftime("%Y-%m"), best))
    return pd.concat(oos), choix


def _per(s):
    p1 = s[(s.index >= OOS) & (s.index <= P1_FIN)]; p2 = s[s.index > P1_FIN]; r = s[s.index >= RES]
    return p1, p2, r


def evalue(nom, grille, cout_double=True, verbose=True):
    """grille : dict nom_reglage -> fonction(cout) rendant W (DataFrame jours x FAMS, poids 0..2 connus au debut de J)
    OU DataFrame W (meme pour les deux couts). Rend un dict de resultats et imprime un tableau."""
    res = {}
    for cout in ((1.0, 2.0) if cout_double else (1.0,)):
        Ws = {c: (g(cout) if callable(g) else g) for c, g in grille.items()}
        S = {c: egal(pnl(W, cout), W) for c, W in Ws.items()}
        Wt, Ws5 = W_tout(), W_suivre5(cout)
        tout = egal(pnl(Wt, cout), Wt); s5 = egal(pnl(Ws5, cout), Ws5)
        wf, choix = walk(S)
        tout_o, s5_o = tout.reindex(wf.index), s5.reindex(wf.index)
        Dm_t = np.column_stack([wf - tout_o] + [S[c].reindex(wf.index) - tout_o for c in S])
        Dm_5 = np.column_stack([wf - s5_o] + [S[c].reindex(wf.index) - s5_o for c in S])
        p_t, p_5 = white(Dm_t), white(Dm_5)
        r = {"wf": wf, "tout": tout_o, "suivre5": s5_o, "choix": choix, "p_tout": p_t, "p_s5": p_5,
             "p_corr": max(p_t, p_5), "S": S}
        for lab, s in (("wf", wf), ("tout", tout_o), ("suivre5", s5_o)):
            p1, p2, rr = _per(s)
            r[lab + "_P1"], r[lab + "_P2"], r[lab + "_RES"] = p1.sum(), p2.sum(), rr.sum()
        p1w, p2w, _ = _per(wf - tout_o); p15, p25, _ = _per(wf - s5_o)
        r["t_tout"], r["t_s5"] = tst(wf - tout_o), tst(wf - s5_o)
        r["bat"] = (r["wf_P1"] > 0 and r["wf_P2"] > 0 and p1w.sum() > 0 and p2w.sum() > 0
                    and p15.sum() > 0 and p25.sum() > 0)
        res[cout] = r
    r1 = res[1.0]
    ok = r1["bat"] and r1["p_corr"] < 0.05 and (2.0 not in res or res[2.0]["bat"])
    res["retenu"] = bool(ok)
    res["N"] = len(grille)
    if verbose:
        print("\n=== %s : %d reglages, walk-forward 6 mois / 1 mois, exposition egale a TOUT, unite u ===" % (nom, len(grille)))
        print("%-8s %-10s %9s %9s %9s %8s %8s" % ("spread", "serie", "P1 22-24", "P2 24-26", "dont RES", "t/TOUT", "t/SUIV5"))
        for cout in res:
            if not isinstance(cout, float):
                continue
            r = res[cout]
            for lab in ("wf", "tout", "suivre5"):
                print("%-8s %-10s %+9.1f %+9.1f %+9.1f %8s %8s" % ("x%.0f" % cout, lab, r[lab + "_P1"], r[lab + "_P2"],
                      r[lab + "_RES"], "%+.2f" % r["t_tout"] if lab == "wf" else "", "%+.2f" % r["t_s5"] if lab == "wf" else ""))
            print("         p corrige (White, %d reglages + wf) : contre TOUT %.3f, contre SUIVRE5 %.3f" % (len(grille), r["p_tout"], r["p_s5"]))
        cs = pd.Series([c for _, c in r1["choix"]]).value_counts()
        print("  Reglages choisis (spread reel) : " + ", ".join("%s x%d" % (k, v) for k, v in cs.head(6).items()))
        print("  VERDICT %s : %s" % (nom, "RETENU" if ok else "ne tient pas"))
    return res


def ligne_csv(nom, res, chemin=None):
    """Ajoute une ligne de synthese a donnees/regime_lotb.csv."""
    chemin = chemin or os.path.join(DONL, "regime_lotb.csv")
    r1, r2 = res[1.0], res.get(2.0, {})
    row = {"piste": nom, "N": res["N"], "wf_P1": r1["wf_P1"], "wf_P2": r1["wf_P2"], "wf_RES": r1["wf_RES"],
           "tout_P1": r1["tout_P1"], "tout_P2": r1["tout_P2"], "s5_P1": r1["suivre5_P1"], "s5_P2": r1["suivre5_P2"],
           "p_tout": r1["p_tout"], "p_s5": r1["p_s5"], "p_corr": r1["p_corr"],
           "x2_wf_P1": r2.get("wf_P1"), "x2_wf_P2": r2.get("wf_P2"), "x2_tout_P1": r2.get("tout_P1"),
           "x2_tout_P2": r2.get("tout_P2"), "x2_s5_P1": r2.get("suivre5_P1"), "x2_s5_P2": r2.get("suivre5_P2"),
           "retenu": res["retenu"]}
    df = pd.read_csv(chemin) if os.path.exists(chemin) else pd.DataFrame()
    df = df[df.get("piste", pd.Series(dtype=str)) != nom] if len(df) else df
    pd.concat([df, pd.DataFrame([row])], ignore_index=True).to_csv(chemin, index=False, float_format="%.4f")


# ------------------------------------------------------------------------------------------------ donnees externes
def _get(url, essais=4):
    for k in range(essais):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 labo"})
            return urllib.request.urlopen(req, timeout=60).read().decode()
        except Exception:
            time.sleep(2 * (k + 1))
    raise RuntimeError("telechargement impossible : " + url)


def fred(ids=("VIXCLS", "DGS10", "DFII10", "DTWEXBGS", "T10YIE", "DGS2")):
    """Series FRED journalieres (cache donnees/regime_fred.csv.gz). Valeur datee D : utilisable au jour serveur D+2."""
    ch = os.path.join(DONL, "regime_fred.csv.gz")
    if os.path.exists(ch):
        F = pd.read_csv(ch, index_col=0, parse_dates=True)
        if all(i in F for i in ids):
            return F[list(ids)]
    cols = {}
    for i in ids:
        txt = _get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=%s&cosd=2017-01-01" % i)
        s = pd.read_csv(io.StringIO(txt), index_col=0, parse_dates=True).iloc[:, 0]
        cols[i] = pd.to_numeric(s, errors="coerce")
    F = pd.DataFrame(cols).sort_index()
    F.to_csv(ch, float_format="%.4f")
    return F


def fred_connu(ids=("VIXCLS", "DGS10", "DFII10", "DTWEXBGS", "T10YIE", "DGS2")):
    """FRED aligne sur JOURS : valeur connue au debut du jour serveur J (derniere observation datee <= J-2)."""
    F = fred(ids)
    F.index = F.index + pd.Timedelta(days=2)
    return F.reindex(F.index.union(JOURS)).ffill().reindex(JOURS)


def cot_or():
    """COT legacy futures de l'or (CFTC 088691), cache donnees/regime_cot_or.csv.gz. Connu au jour = rapport + 13 j."""
    ch = os.path.join(DONL, "regime_cot_or.csv.gz")
    if not os.path.exists(ch):
        url = ("https://publicreporting.cftc.gov/resource/6dca-aqww.json?$limit=5000&$order=report_date_as_yyyy_mm_dd"
               "&cftc_contract_market_code=088691")
        d = pd.DataFrame(json.loads(_get(url)))
        d = pd.DataFrame({"date": pd.to_datetime(d.report_date_as_yyyy_mm_dd),
                          "spec_net": pd.to_numeric(d.noncomm_positions_long_all) - pd.to_numeric(d.noncomm_positions_short_all),
                          "comm_net": pd.to_numeric(d.comm_positions_long_all) - pd.to_numeric(d.comm_positions_short_all),
                          "oi": pd.to_numeric(d.open_interest_all)})
        d.to_csv(ch, index=False)
    d = pd.read_csv(ch, parse_dates=["date"])
    d.index = d.date + pd.Timedelta(days=13)
    return d.drop(columns="date").reindex(d.index.union(JOURS)).ffill().reindex(JOURS)


def vix_connu():
    """VIX (cloture New York de J-1) connu au debut du jour serveur J."""
    v = VIX.copy(); v.index = v.index + pd.Timedelta(days=1)
    return v.reindex(v.index.union(JOURS)).ffill().reindex(JOURS)


def h1_connu():
    """Bougies H1 de l'or fermees avant le debut de chaque jour (utiliser .loc[: J - 1 h] pour la derniere bougie)."""
    return OR_H1


if __name__ == "__main__":
    t0 = time.time()
    T, J, ech = base(1.0)
    print("Jours %s -> %s (%d) ; trades or H1 : %s" % (JOURS[0].date(), JOURS[-1].date(), len(JOURS),
          T.fam.value_counts().to_dict()))
    print("Echelles (1 u) :", {k: round(v, 3) for k, v in ech.items()})
    for cout in (1.0, 2.0):
        P = pnl_fams(W_tout(), cout)
        p1, p2, rr = P[(P.index >= OOS) & (P.index <= P1_FIN)].sum(), P[P.index > P1_FIN].sum(), P[P.index >= RES].sum()
        print("Spread x%.0f, P&L par famille (u) P1 / P2 / RES :" % cout)
        for f in FAMS:
            print("  %-12s %+8.1f %+8.1f %+8.1f   t tout %+.2f" % (f, p1[f], p2[f], rr[f], tst(P[f][P.index >= OOS])))
    res = evalue("references (controle : TOUT seul)", {"tout": lambda c: W_tout()})
    print("%.0f s" % (time.time() - t0))
