"""Banc AG : allouer la mise des petites regles de l'or selon le regime connu en direct (PRIORITES 18/11).
Donnees : or M5 du courtier xau_m5_2025a + xau_m5_90k (06/2025 -> 11/2026), M15 xau_m15_50k, H1 xau_h1_50k (drapeau),
M1 xau_m1_90k (3 mois : regles M1 du robot en descriptif seulement). Spread reel, $ a 0,01 lot (1 bp = 0,40 $ comme
banc_famille), une position a la fois par regle (B.trades : decision a la cloture i, entree a l'ouverture i+1).
Regles : elan_m15, cassure_m15, fcassure_m5, contre_exces_m5 (banc_famille, R0), retour_court_ar (banc_thermometre),
bt_or ($ par panier, banc_bt_regulier.simule), exces_m1 / fcassure_m1 (robot : contre une bougie M1 > 3 ecarts-types,
12 min ; contre la sortie de la fourchette de 48 min, 3 min).
Regimes connus en direct (fixes d'avance), aucune fuite :
  drapeau v11 (robot.agite) : mouvement H1 moyen (|log| des 24 dernieres H1 fermees) > sa mediane haute des 1440
    valeurs precedentes -> agite, sinon calme ; on prend la derniere H1 FERMEE avant la decision (heure pleine).
  tranche, heure de Paris a l'entree (serveur = New York + 7 h) : Asie 22-8 h, Europe 8-14 h, US 14-22 h.
  panier bt_or (banc_thermometre.etat_connu, bougie M5 cloturee une bougie avant) : absent / <= 1 R / > 1 R.
Comme le robot (v12), chaque regle de R0 a deux places : la regle elle-meme (agite seulement : R0 = selection
actuelle, en pause au calme) et sa variante _calme (calme seulement) ; chacune une position a la fois.
retour_court_ar et bt_or tournent tout le temps (une place). Gains rattaches au jour (serveur) de la decision.
(1) Descriptif : n, $/trade, bp/trade, $/jour de trading, t, par drapeau et drapeau x tranche, $ par moitie ;
    question « +109 $ des variantes _calme en 3 jours quand R0 perd -78 $ » sur fenetres glissantes de 3 jours.
(2) Allocation walk-forward : poids w(regle, case) >= 0, plafond 2, appris sur 6 mois, appliques au mois suivant.
    Grille fixee d'avance N = 18 : cases {drapeau ; drapeau x tranche ; drapeau x tranche x panier} x retrecissement
    k in {50, 200, 800} trades (m' = m n / (n + k)) x forme {binaire : 1 si m' > 0 et t de la case > 1 ;
    proportionnelle : w = min(2, max(0, m'/s2) / c), c tel que l'exposition moyenne d'apprentissage = 1}.
    5 regles (R0 x 2 places + retour_court_ar). Choix au meilleur t (gain par jour) sur l'apprentissage ; les trades
    d'apprentissage sortis apres le debut du mois de test sont exclus. References : R0 et « tout en marche » (5 regles,
    poids 1, 2 places), aussi a exposition egale (x mise moyenne realisee par trade dans le mois de test, comme
    banc_thermometre.egal). Triche = poids et reglage appris sur le mois de test. Reality check de White (bootstrap
    stationnaire, blocs 5 j, 2000 tirages) sur les 18 series hors echantillon de difference a exposition egale.
    Temoin : etiquettes de case (drapeau, tranche, panier ensemble) prises a un instant decale par rotation circulaire
    de 20 jours au moins, 200 tirages, tout le walk-forward refait.
Verdict (fixe d'avance) sur la difference a exposition egale contre la meilleure des deux references : tient = > 0 ET
(t >= 2,6 OU p RC < 0,05) ; presque = > 0 et (1,5 <= t < 2,6 ou p < 0,15) ; sinon ne tient pas.
Ecrit donnees/alloc_wf.csv (series journalieres hors echantillon). Usage : python3 banc_alloc.py"""
import contextlib, io, itertools, os, time, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
T00 = time.time()
with contextlib.redirect_stdout(io.StringIO()):
    import banc_thermometre as TH                  # rejoue banc_thermometre (~10 s) : on n'en garde que les fonctions
W, F, B, BR = TH.W, TH.F, TH.B, TH.BR
USD, tst = F.USD, TH.tst
ICI = os.path.dirname(os.path.abspath(__file__))
sec = lambda ix: pd.DatetimeIndex(ix).values.astype("datetime64[s]").astype(np.int64)

# ---------------------------------------------------------------- donnees
a5, b5_ = BR.charge("xau_m5_2025a"), BR.charge("xau_m5_90k")
d5 = pd.concat([a5, b5_[b5_.heure > a5.heure.iloc[-1]]], ignore_index=True)
m5 = d5.copy(); m5.index = pd.to_datetime(m5.heure, unit="s")
m15, _ = B.charge("xau_m15_50k"); m15 = m15[m15.index >= m5.index[0]]
m1, _ = B.charge("xau_m1_90k")
h1, _ = B.charge("xau_h1_50k")
T5 = d5.heure.values
idx = pd.DatetimeIndex(sorted(set(m5.index.floor("D")))); idx = idx[idx.dayofweek < 5]
ND = len(idx); jour_pos = pd.Series(np.arange(ND), idx)
mil = m5.index[len(m5) // 2]

# drapeau v11 : copie vectorisee de robot.agite (mediane haute = passe[len // 2])
lr1 = np.log(h1.cloture.values)
v = pd.Series(np.r_[np.nan, np.abs(np.diff(lr1))]).rolling(24).mean()
med = v.shift(1).rolling(1440, min_periods=700).quantile(0.5, interpolation="higher")
AG = np.where(med.isna(), -1, (v > med).astype(int)).astype(int)        # 1 agite, 0 calme, -1 inconnu
FIN_H1 = h1.heure.values + 3600


def drapeau(dec):
    """Drapeau connu a l'instant dec (s) : derniere bougie H1 dont la cloture est <= dec."""
    k = np.searchsorted(FIN_H1, dec, side="right") - 1
    assert (FIN_H1[k] <= dec).all()
    return np.where(k >= 0, AG[np.maximum(k, 0)], -1)


def tranche(dec):
    t = pd.DatetimeIndex(pd.to_datetime(np.asarray(dec), unit="s"))
    ny = (t - pd.Timedelta(hours=7)).tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT")
    p = ny.tz_convert("Europe/Paris").tz_localize(None)
    h = np.where(p.isna(), (t - pd.Timedelta(hours=1)).hour, p.hour)
    return np.where((h >= 8) & (h < 14), 1, np.where((h >= 14) & (h < 22), 2, 0))


pan_cl = lambda la: np.where(np.isnan(la), 0, np.where(la <= 1, 1, 2))   # absent / <= 1 R / > 1 R

# etat du panier bt_or (gain latent en R a chaque cloture M5)
Pg, LAT = TH.simule_etat(d5)
P = BR.simule(d5)
ok_bt = bool(np.allclose(np.sort(Pg), np.sort(P.g.values)))

# ---------------------------------------------------------------- signaux (formules de banc_famille / robot)
lr = np.log(m15["cloture"])
s_elan = np.sign(lr - lr.shift(12))
ha, ba = m15["haut"].shift(1).rolling(48).max(), m15["bas"].shift(1).rolling(48).min()
s_cass = (m15["cloture"] > ha).astype(float) - (m15["cloture"] < ba).astype(float)
hh5, bb5 = m5["haut"].shift(1).rolling(12).max(), m5["bas"].shift(1).rolling(12).min()
s_fc = (m5["cloture"] < bb5).astype(float) - (m5["cloture"] > hh5).astype(float)
r5 = np.log(m5["cloture"]).diff(); z5 = r5 / r5.rolling(100).std().shift(1)
s_cx = (z5 < -3).astype(float) - (z5 > 3).astype(float)
r1 = np.log(m1["cloture"]).diff(); z1 = r1 / r1.rolling(100).std().shift(1)
s_ex1 = (z1 < -3).astype(float) - (z1 > 3).astype(float)
hh1, bb1 = m1["haut"].shift(1).rolling(48).max(), m1["bas"].shift(1).rolling(48).min()
s_fc1 = (m1["cloture"] < bb1).astype(float) - (m1["cloture"] > hh1).astype(float)
REG = {"elan_m15": (m15, s_elan, 12, 900), "cassure_m15": (m15, s_cass, 12, 900),
       "fcassure_m5": (m5, s_fc, 3, 300), "contre_exces_m5": (m5, s_cx, 3, 300),
       "exces_m1": (m1, s_ex1, 12, 60), "fcassure_m1": (m1, s_fc1, 3, 60)}
R0N = ["elan_m15", "cassure_m15", "fcassure_m5", "contre_exces_m5"]
ALLOC = R0N + ["retour_court_ar"]


def joue(nom, d, s, h, bar, masque):
    x, i = B.trades(d, s * masque, h)
    t0 = sec(d.index)
    return pd.DataFrame({"r": nom, "g": x[:, 0] * USD, "bp": x[:, 0], "dec": t0[i] + bar,
                         "fin": t0[np.minimum(i + h, len(t0) - 1)] + bar, "t": d.index[i]})


rows = []
for nom, (d, s, h, bar) in REG.items():
    fl = drapeau(sec(d.index) + bar)
    for slot, m in (("A", fl != 0), ("C", fl == 0)):              # inconnu -> pas de pause (comme le robot)
        z = joue(nom, d, s, h, bar, m.astype(float)); z["slot"] = slot; rows.append(z)
rc = TH.retour_court_ar(m15)
rows.append(pd.DataFrame({"r": "retour_court_ar", "g": rc.g.values, "bp": rc.g.values / USD, "dec": sec(rc.index) + 900,
                          "fin": sec(rc.index) + 900 * 13, "t": rc.index, "slot": "-"}))
tb = pd.to_datetime(P.t0, unit="s")
rows.append(pd.DataFrame({"r": "bt_or", "g": P.bp.values * USD, "bp": P.bp.values, "dec": P.t0.values + 300,
                          "fin": P.t1.values + 300, "t": tb, "slot": "-"}))
TT = pd.concat(rows, ignore_index=True)
TT["fl"] = drapeau(TT.dec.values); TT["tr"] = tranche(TT.dec.values)
la, jj = TH.etat_connu(T5, LAT, TT.dec.values)
assert (T5[np.maximum(jj, 0)] + 600 <= TT.dec.values).all()           # bougie M5 close au moins 5 min avant
TT["pan"] = pan_cl(la); TT["jj"] = jj
TT["jour"] = jour_pos.reindex(pd.DatetimeIndex(TT.t).floor("D")).values
TT = TT[(TT.jour == TT.jour) & (TT.jj >= 0)].reset_index(drop=True); TT["jour"] = TT.jour.astype(int)
assert (TT.fl >= 0).all(), "drapeau inconnu"
pj = lambda msk, w=1.0: pd.Series(np.bincount(TT.jour.values[msk], weights=(TT.g.values * w)[msk], minlength=ND), idx)
isr = lambda n: (TT.r == n).values
mR0 = np.isin(TT.r, R0N) & (TT.slot == "A").values
mC = np.isin(TT.r, R0N) & (TT.slot == "C").values
R0, JC = pj(mR0), pj(mC)

# controle : R0 de banc_famille (pause au calme JOURNALIERE de la veille) sur ses 15 mois
rows = []
for nom in R0N:
    d, s, h, bar = REG[nom]
    cv = F.calme_v.reindex(d.index.floor("D")).fillna(False).values.astype(bool)
    rows.append(joue(nom, d, s, h, bar, (~cv).astype(float)))
Xf = pd.concat(rows); Rf = Xf.g.groupby(pd.DatetimeIndex(Xf.t).floor("D")).sum().reindex(W.idx).fillna(0)
wft = W.mois >= W.fen[0][2]
print("Or M5 %s -> %s (%d jours ouvres) ; drapeau v11 calme sur %.0f %% des H1 de la periode ; bt_or %d paniers %+.1f R (identiques a BR.simule : %s)"
      % (idx[0].date(), idx[-1].date(), ND, 100 * (AG[(h1.heure.values >= T5[0]) & (AG >= 0)] == 0).mean(), len(P), P.g.sum(), ok_bt))
print("Controle R0 pause JOURNALIERE (banc_famille) recalcule ici : %+.0f $ (banc_famille_wf %+.0f), mois de test 2026-02..11 %+.0f $ (wf %+.0f)"
      % (Rf.sum(), W.R0.sum(), Rf[wft].sum(), W.R0[wft].sum()))
print("  R0 avec le drapeau v11 HORAIRE (celui de ce banc), memes jours : %+.0f $, mois 2026-02..11 %+.0f $ ; spread moyen M5 %.2f bp"
      % (R0.reindex(W.idx).fillna(0).sum(), R0.reindex(W.idx[wft]).fillna(0).sum(), (m5.sp / m5.cloture * 1e4).mean()))

# ---------------------------------------------------------------- (1) descriptif
TRN = ["Asie", "Europe", "US"]
h1m = (pd.DatetimeIndex(TT.t) < mil)
ND1 = int(((idx >= m1.index[0].floor("D")) & (idx <= m1.index[-1])).sum())
print("(1) Descriptif. $/j = total / jours ouvres (%d ; regles M1 : %d jours, %s -> %s). t par trade. moities : $ 1re / 2de (coupure %s)"
      % (ND, ND1, m1.index[0].date(), m1.index[-1].date(), mil.date()))
print("  %-16s %-6s %5s %7s %7s %7s %5s %13s" % ("regle", "drap.", "n", "$/tr", "bp/tr", "$/j", "t", "moities $"))
P1 = ["elan_m15", "cassure_m15", "fcassure_m5", "contre_exces_m5", "retour_court_ar", "bt_or", "exces_m1", "fcassure_m1"]
for n in P1:
    nd = ND1 if n.endswith("m1") else ND
    for fn, fv in (("calme", 0), ("agite", 1), ("tout", None)):
        m = isr(n) & ((TT.fl == fv).values if fv is not None else True)
        g = TT.g.values[m]
        if not len(g):
            continue
        print("  %-16s %-6s %5d %+7.2f %+7.2f %+7.2f %+5.1f %+6.0f/%+6.0f" % (n if fv == 0 else "", fn, len(g), g.mean(), TT.bp.values[m].mean(),
              g.sum() / nd, tst(g), g[h1m[m]].sum(), g[~h1m[m]].sum()))
print("  drapeau x tranche (n  $total  t ; * = |t| >= 2 et meme signe dans les deux moities)")
print("  %-16s %-6s | %-20s | %-20s | %-20s" % ("regle", "drap.", *TRN))
for n in P1:
    for fn, fv in (("calme", 0), ("agite", 1)):
        z = []
        for k in range(3):
            m = isr(n) & (TT.fl == fv).values & (TT.tr == k).values
            g = TT.g.values[m]; a, b = g[h1m[m]].sum(), g[~h1m[m]].sum()
            st = "*" if len(g) > 2 and abs(tst(g)) >= 2 and np.sign(a) == np.sign(b) else " "
            z.append("%5d %+6.0f %+5.1f%s" % (len(g), g.sum(), tst(g), st))
        print("  %-16s %-6s | %s" % (n if fv == 0 else "", fn, " | ".join(z)))

# question +109 $
c3, r3 = JC.rolling(3).sum().dropna(), R0.rolling(3).sum().dropna()
pire = r3 <= -78
print("Question « _calme +109 $ en 3 jours pendant que R0 perd -78 $ » (_calme = les 4 regles de R0, calme seulement) :")
print("  _calme : %d trades, total %+.0f $, %+.2f $/j (t jour %+.1f, moities %+.0f / %+.0f) ; R0 : %+.0f $, %+.2f $/j (t %+.1f) ; correlation jour %+.2f"
      % (mC.sum(), JC.sum(), JC.mean(), tst(JC), JC[idx < mil].sum(), JC[idx >= mil].sum(), R0.sum(), R0.mean(), tst(R0), JC.corr(R0)))
print("  fenetres glissantes de 3 jours ouvres : %d ; _calme >= +109 $ : %.1f %% ; R0 <= -78 $ : %.1f %% ; _calme >= +109 sachant R0 <= -78 : %.1f %% (%d/%d) ; les deux : %.1f %%"
      % (len(c3), 100 * (c3 >= 109).mean(), 100 * pire.mean(), 100 * (c3[pire] >= 109).mean() if pire.any() else np.nan,
         (c3[pire] >= 109).sum(), pire.sum(), 100 * ((c3 >= 109) & pire).mean()))
print("  quantiles _calme 3 j (5/50/95 %%) : %+.0f / %+.0f / %+.0f $ ; correlation 3 j _calme / R0 %+.2f"
      % (*np.percentile(c3, [5, 50, 95]), c3.corr(r3)))

# ---------------------------------------------------------------- (2) allocation walk-forward
mA = np.isin(TT.r, ALLOC)
A = TT[mA].reset_index(drop=True)
rr = A.r.map({n: i for i, n in enumerate(ALLOC)}).values
gA, dA, fA = A.g.values, A.jour.values, A.fin.values
TEM = pd.Series(np.bincount(dA, weights=gA, minlength=ND), idx)
mois = idx.to_period("M"); MO = mois.unique()
moA = mois[dA]
fen = [(MO[i - 6], MO[i - 1], MO[i]) for i in range(6, len(MO))]
WIN = []
for a, b, t in fen:
    deb = sec(pd.DatetimeIndex([t.start_time]))[0]
    WIN.append(((moA >= a) & (moA <= b) & (fA < deb), moA == t, ((mois >= a) & (mois <= b)), mois == t))
NC = (2, 6, 18); NIV = ("drap", "drap x heure", "drap x heure x panier")
GR = list(itertools.product(range(3), (50, 200, 800), ("bin", "prop")))
nomc = lambda c: "%s k%d %s" % (NIV[c[0]], c[1], c[2])
nR0 = np.isin(A.r, R0N) & (A.slot == "A").values   # trades de R0 parmi ceux de l'allocation


def cles(fl, trn, pan):
    c2 = fl * 3 + trn
    return [rr * 2 + fl, rr * 6 + c2, rr * 18 + c2 * 3 + pan]


def fit(key, nk, msk, k, forme):
    kk, g = key[msk], gA[msk]
    n = np.bincount(kk, minlength=nk).astype(float)
    S = np.bincount(kk, g, nk); Q = np.bincount(kk, g * g, nk)
    m = np.divide(S, n, out=np.zeros(nk), where=n > 0)
    var = np.divide(Q - n * m * m, n - 1, out=np.zeros(nk), where=n > 1)
    mp = m * n / (n + k)
    ok = (n > 2) & (var > 0)
    if forme == "bin":
        t = np.divide(m, np.sqrt(np.where(ok, var, 1) / np.maximum(n, 1)), out=np.zeros(nk), where=ok)
        return ((mp > 0) & (t > 1) & ok).astype(float)
    raw = np.where(ok, np.maximum(0, mp) / np.where(ok, var, 1), 0.0)
    N = n.sum()
    if N == 0 or (raw > 0).sum() == 0:
        return np.zeros(nk)
    if 2 * n[raw > 0].sum() / N <= 1:
        return 2.0 * (raw > 0)
    lo, hi = np.log((n * raw).sum() / N) - 30, np.log((n * raw).sum() / N)
    for _ in range(60):                                      # exposition moyenne = 1 avec le plafond 2
        c = np.exp((lo + hi) / 2)
        if (n * np.minimum(2, raw / c)).sum() / N > 1:
            lo = np.log(c)
        else:
            hi = np.log(c)
    return np.minimum(2, raw / np.exp(hi))


def jourw(w, msk):
    return np.bincount(dA[msk], weights=(gA * w)[msk], minlength=ND)


def walk(fl, trn, pan, triche=False, tous=False):
    """Rend la serie WF (jours de test), la mise moyenne par jour, le choix ; et, si tous, les series de chaque reglage."""
    K = cles(fl, trn, pan)
    oos, expo, ch, per = np.zeros(ND), np.zeros(ND), [], {c: (np.zeros(ND), np.zeros(ND)) for c in GR} if tous else None
    for app, te, japp, jte in WIN:
        src, jsrc = (te, jte) if triche else (app, japp)
        best, bt, res = None, -np.inf, {}
        for c in GR:
            w = fit(K[c[0]], 5 * NC[c[0]], src, c[1], c[2])[K[c[0]]]
            t = tst(jourw(w, src)[jsrc]); res[c] = w
            if t > bt:
                best, bt = c, t
            if tous:
                per[c][0][jte] = jourw(w, te)[jte]; per[c][1][jte] = w[te].mean() if te.any() else 0
        w = res[best]
        oos[jte] = jourw(w, te)[jte]; expo[jte] = w[te].mean() if te.any() else 0; ch.append(best)
    return oos, expo, ch, per


LAB = (A.fl.values, A.tr.values, A.pan.values)
o, ex, ch, PER = walk(*LAB, tous=True)
ot, ext, cht, _ = walk(*LAB, triche=True)
TJ = np.zeros(ND, bool)
for *_, jte in WIN:
    TJ |= jte
S = lambda x: pd.Series(np.asarray(x)[TJ], idx[TJ])
o_, R0t, TEMt = S(o), S(R0), S(TEM)
R0e, TEMe = S(R0 * ex), S(TEM * ex)
om = o_.groupby(o_.index.to_period("M")).sum()
fq = pd.Series([nomc(c) for c in ch]).value_counts()
print("(2) Allocation WF : N = %d reglages, %d mois de test (%s -> %s), 5 regles, %d trades d'allocation ; choisi le plus souvent : %s (%d/%d)"
      % (len(GR), len(fen), fen[0][2], fen[-1][2], len(A), fq.index[0], fq.iloc[0], len(fen)))
print("  choix par mois : " + ", ".join("%s:%s" % (t, nomc(c).replace("drap x heure x panier", "dhp").replace("drap x heure", "dh"))
                                          for (_, _, t), c in zip(fen, ch)))
print("  hors echantillon %+.0f $ (%+.2f $/j, t %+.1f), mois gagnants %d/%d, mise moyenne par trade %.2f ; R0 %+.0f $ (t %+.1f) ; tout en marche %+.0f $ (t %+.1f)"
      % (o_.sum(), o_.mean(), tst(o_), (om > 0).sum(), len(om), ex[TJ & (ex > 0)].mean() if (ex[TJ] > 0).any() else 0,
         R0t.sum(), tst(R0t), TEMt.sum(), tst(TEMt)))
nR0m = pd.Series(nR0.astype(float)).groupby(moA).sum(); nAm = pd.Series(1.0, range(len(A))).groupby(moA).sum()
R0tot = S(R0 * ex * (nAm / nR0m).reindex(mois).fillna(0).values)
DIF = {}
for nom, ref in (("R0", R0t), ("R0 expo egale", R0e), ("tout en marche", TEMt), ("tout en marche expo egale", TEMe),
                 ("R0 a exposition TOTALE egale (info)", R0tot)):
    z = o_ - ref; zm = z.groupby(z.index.to_period("M")).sum(); DIF[nom] = z
    print("  - %-36s %+7.0f $ ; allocation - lui %+6.0f $ (%+5.2f $/j, t %+.1f), mois > %d/%d"
          % (nom, ref.sum(), z.sum(), z.mean(), tst(z), (zm > 0).sum(), len(zm)))
# reality check : series hors echantillon de chaque reglage
RCp = {}
for nom, base in (("tout en marche", TEM), ("R0", R0)):
    Dm = np.column_stack([(PER[c][0] - base.values * PER[c][1])[TJ] for c in GR])
    kb, p = BR.white(Dm); RCp[nom] = p
    print("  RC de White, 18 series a expo. egale contre %s : meilleur %s (%+.0f $ hors ech.), p = %.3f" % (nom, nomc(GR[kb]), Dm[:, kb].sum(), p))
ott = S(ot)
print("  triche (poids et reglage appris sur le mois de test) %+.0f $ (t %+.1f) ; - tout en marche expo egale %+.0f $ ; - R0 expo egale %+.0f $ ; >= WF : %s"
      % (ott.sum(), tst(ott), (ott - S(TEM * ext)).sum(), (ott - S(R0 * ext)).sum(), ott.sum() >= o_.sum()))
# temoin : etiquettes decalees
rng = np.random.default_rng(23)
tau = T5 + 600
FLB, TRB, PNB = drapeau(tau), tranche(tau), pan_cl(LAT)
FLB = np.where(FLB < 0, 1, FLB)
nl, jA = len(T5), A.jj.values
a0, e0, _, _ = walk(FLB[jA], TRB[jA], PNB[jA])
a1, e1, _, _ = walk(FLB[(jA + 288) % nl], TRB[(jA + 288) % nl], PNB[(jA + 288) % nl])
print("  controle des etiquettes : decalage 0 (etiquettes lues sur la grille M5) %+.0f $ (vrai %+.0f) ; decalage d'un jour %+.0f $ ; accord etiquettes %.1f %%"
      % (S(a0).sum(), o_.sum(), S(a1).sum(), 100 * ((FLB[jA] == LAB[0]) & (TRB[jA] == LAB[1]) & (PNB[jA] == LAB[2])).mean()))
tem = []
for _ in range(200):
    off = rng.integers(288 * 20, nl - 288 * 20)
    q = (jA + off) % nl
    a, e, _, _ = walk(FLB[q], TRB[q], PNB[q])
    tem.append(((S(a) - S(TEM * e)).sum(), (S(a) - S(R0 * e)).sum(), S(a).sum()))
tem = np.array(tem)
dT, dR = DIF["tout en marche expo egale"].sum(), DIF["R0 expo egale"].sum()
print("  temoin etiquettes decalees (200 rotations >= 20 j) : - tout en marche expo egale %+.0f $ en moyenne (temoin mieux : %.0f %%), - R0 expo egale %+.0f $ (mieux : %.0f %%), total %+.0f $ (mieux : %.0f %%)"
      % (tem[:, 0].mean(), 100 * (tem[:, 0] >= dT).mean(), tem[:, 1].mean(), 100 * (tem[:, 1] >= dR).mean(), tem[:, 2].mean(), 100 * (tem[:, 2] >= o_.sum()).mean()))
# poids appris sur les 6 derniers mois
app = (moA >= MO[-6]) & (moA <= MO[-1]); japp = (mois >= MO[-6])
K = cles(*LAB)
best = max(GR, key=lambda c: tst(jourw(fit(K[c[0]], 5 * NC[c[0]], app, c[1], c[2])[K[c[0]]], app)[japp]))
L = best[0]; Wb = fit(K[L], 5 * NC[L], app, best[1], best[2]).reshape(5, NC[L])
cols = [("cal", "agi")[f] + ("" if L == 0 else "." + "AEU"[t] + ("" if L == 1 else "abg"[p]))
        for f in range(2) for t in (range(3) if L else [0]) for p in (range(3) if L == 2 else [0])]
print("  poids appris %s -> %s, reglage choisi %s (A/E/U = Asie/Europe/US ; a/b/g = panier absent / <= 1 R / gagnant) :"
      % (MO[-6], MO[-1], nomc(best)))
print("    %-16s " % "" + " ".join("%5s" % c for c in cols))
for i, n in enumerate(ALLOC):
    print("    %-16s " % n + " ".join("%5.2f" % x if x else "    ." for x in Wb[i]))
ref = "tout en marche expo egale" if TEMe.sum() >= R0e.sum() else "R0 expo egale"
dd = DIF[ref]; p = RCp["tout en marche" if ref.startswith("tout") else "R0"]
v = "tient" if dd.sum() > 0 and (tst(dd) >= 2.6 or p < 0.05) else (
    "presque" if dd.sum() > 0 and (tst(dd) >= 1.5 or p < 0.15) else "ne tient pas")
print("  Verdict (fixe d'avance, contre la meilleure reference = %s : %+.0f $, t %+.1f, p RC %.3f) : %s"
      % (ref, dd.sum(), tst(dd), p, v))
out = pd.DataFrame({"alloc": o_, "r0": R0t, "tout": TEMt, "r0_eq": R0e, "tout_eq": TEMe, "triche": ott, "mise": S(ex)}).round(2)
out.index.name = "jour"
out.to_csv(os.path.join(ICI, "donnees", "alloc_wf.csv"))
print("Ecrit donnees/alloc_wf.csv (%d jours) ; duree %.0f s" % (len(out), time.time() - T00))
