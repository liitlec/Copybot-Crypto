"""Banc AD (PRIORITES 17/11 12 h 15, piste 1) : prevoir EN DIRECT le type de la suite de la journee de l'or a 9 h,
12 h et 15 h 30 (heure de Paris, convertie a chaque date : serveur = New York + 7 h, donc Paris = serveur - 1 h sauf
les semaines ou l'heure d'ete US et europeenne different), puis choisir la famille de regles pour le reste du jour.
Types (meme definition que banc_aller_retour.py, appliquee a la SUITE du jour, de l'instant t a minuit serveur) :
agitee = amplitude de la suite > mediane des 60 jours precedents de l'amplitude de la suite au meme instant ;
aller-retour (AR) = agitee et efficacite |cloture fin - prix a t| / amplitude < 0,35 ; tendance = agitee et >= 0,35 ;
calme = le reste. Regles (banc_famille.py, spread reel, pause au calme v11, $ a 0,01 lot) : famille TENDANCE =
elan_m15 + cassure_m15 ; famille RETOUR = fcassure_m5 + contre_exces_m5. Prevision « tendance » -> famille tendance,
« AR » -> famille retour, « calme » -> rien, pour les trades decides apres t le meme jour serveur.
Indices (bougies M5 fermees avant t, rien du futur) pour or, nas, sp, argent, euro : amplitude et direction depuis
minuit, sur 1 h / 4 h / 24 h (rapportees a leur mediane 20 j au meme instant), ecart a la cloture de la veille,
position dans la fourchette du jour, nombre de fausses cassures de la fourchette d'1 h depuis minuit (sortie en
cloture, retour dedans 3 bougies plus tard) ; type de la veille (jour entier), jour de la semaine, annonce US forte
(liste de banc_pause_annonces.py : jour, deja passee, encore a venir) ; taux du Tresor 10 ans nominal et reel et
dollar (valeurs des dates civiles anterieures au jour serveur : variation 1 j et 5 j). L'heure est fixe par modele.
Modeles en numpy (scikit-learn absent) : regression logistique multinomiale L2 (lambda 0,3 ou 0,03 sur indices
centres reduits), arbre CART profondeur 2 ou 3 (feuille >= 8 jours), foret de controle (25 arbres prof. 3).
Grille fixee d'avance : 3 heures x 5 modeles x 2 jeux d'indices (« or » : or + calendrier + taux ; « tout » : + nas,
sp, argent, euro) = 30 reglages. Walk-forward glissant 6 mois -> 1 mois ; dans chaque apprentissage, choix du
reglage (par heure) au meilleur t du gain par jour sur les 2 derniers mois, modeles appris sur les 4 premiers ; puis
reappris sur les 6 mois et appliques au mois de test. Jugement : (a) bonnes reponses sur 3 classes contre la classe
la plus frequente et « meme type que la veille » ; (b) $ de la famille choisie contre R0 (les 4 regles), tendance
seule, triche (vrai type de la suite) et hasard de meme frequence (predictions melangees dans le mois, 200 tirages).
Reality check de White (bootstrap stationnaire, blocs 5 j, 2000 tirages) des 30 series hors echantillon contre R0.
Deja refute : detecteur d'AR a 1-2 indices (38-50 % de precision hors echantillon, banc_aller_retour2.py).
Usage : python3 banc_modele_moment.py   (ecrit aussi le taux de bonnes reponses par heure si SCORES est defini)"""
import contextlib, io, os, sys, statistics
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_pause_annonces as PA
F = PA.F; B = F.B
ICI = os.path.dirname(os.path.abspath(__file__))
HEURES = {"9 h": (9, 0), "12 h": (12, 0), "15 h 30": (15, 30)}
CL = ["calme", "tend", "AR"]


def m5(nom):
    a, _ = B.charge(nom + "_m5_90k")
    if os.path.exists(os.path.join(B.DON, nom + "_m5_2025a.csv.gz")):
        b, _ = B.charge(nom + "_m5_2025a")
        a = pd.concat([b, a])
        a = a[~a.index.duplicated(keep="last")].sort_index()
    return a


X5 = {n: m5(n) for n in ("xau", "nas", "sp", "xag", "eur")}
xau = X5["xau"]
jd = xau.index.floor("D")
J = xau.groupby(jd).agg(o=("cloture", "first"), c=("cloture", "last"), hi=("haut", "max"), lo=("bas", "min"), n=("cloture", "size"))
J = J[(J.n > 200) & (J.index.dayofweek < 5)]
J["amp"] = J.hi - J.lo
J["eff"] = (J.c - J.o).abs() / J.amp
J["med"] = J.amp.rolling(60).median().shift(1)
J["type"] = np.where(J.amp > J.med, np.where(J.eff < 0.35, 2, 1), 0).astype(float)
J.loc[J.med.isna(), "type"] = np.nan
JOURS = J.index


def instant(hh, mm):
    loc = pd.DatetimeIndex(JOURS + pd.Timedelta(hours=hh, minutes=mm)).tz_localize("Europe/Paris")
    return pd.Series(loc.tz_convert("America/New_York").tz_localize(None) + pd.Timedelta("7h"), JOURS)


TT = {h: instant(*v) for h, v in HEURES.items()}


def mesures(d, tt, pre):
    t = d.index.values; jj = d.index.floor("D")
    H, L, C, O = d["haut"], d["bas"], d["cloture"], d["ouverture"]
    hi0, lo0 = H.groupby(jj).cummax().values, L.groupby(jj).cummin().values
    op0 = O.groupby(jj).transform("first").values
    prevc = C.groupby(jj).last().shift(1).reindex(jj).values
    W = {}
    for k, nm in ((12, "1h"), (48, "4h"), (288, "24h")):
        W["amp" + nm] = (H.rolling(k).max() - L.rolling(k).min()).values
        W["dir" + nm] = (C - C.shift(k)).values
    c = C.values
    hp, lp = H.shift(1).rolling(12).max().values, L.shift(1).rolling(12).min().values
    c3 = np.r_[c[3:], [np.nan] * 3]
    meme = np.r_[jj.values[3:] == jj.values[:-3], [False] * 3]
    fausse = meme & (((c > hp) & (c3 < hp)) | ((c < lp) & (c3 > lp)))
    fk = np.r_[[False] * 3, fausse[:-3]]                     # connue a la cloture de la 3e bougie suivante
    nfc = pd.Series(fk.astype(float), d.index).groupby(jj).cumsum().values
    k = np.searchsorted(t, tt.values, side="left") - 1     # derniere bougie FERMEE avant t
    ok = (k >= 0) & (jj.values[np.maximum(k, 0)] == tt.index.values)
    k = np.maximum(k, 0)
    v = lambda a: np.where(ok, a[k], np.nan)
    amp0 = v(hi0 - lo0)
    med = lambda a: pd.Series(a, tt.index).rolling(20, min_periods=10).median().shift(1).values
    m0, m1, m4, m24 = med(amp0), med(v(W["amp1h"])), med(v(W["amp4h"])), med(v(W["amp24h"]))
    X = {"amp0": amp0 / m0, "dir0": v(c - op0) / m0, "amp1h": v(W["amp1h"]) / m1, "dir1h": v(W["dir1h"]) / m1,
         "amp4h": v(W["amp4h"]) / m4, "dir4h": v(W["dir4h"]) / m4, "amp24h": v(W["amp24h"]) / m24,
         "dir24h": v(W["dir24h"]) / m24, "ecart_veille": v(c - prevc) / m24,
         "pos": v((c - lo0) / np.where(hi0 > lo0, hi0 - lo0, np.nan)), "fausses_c": v(nfc)}
    return pd.DataFrame({pre + "_" + a: b for a, b in X.items()}, tt.index)


def etiquette(tt):
    d = xau; t = d.index.values; jj = d.index.floor("D")
    sH = d["haut"][::-1].groupby(jj[::-1]).cummax()[::-1].values
    sL = d["bas"][::-1].groupby(jj[::-1]).cummin()[::-1].values
    fin = d["cloture"].groupby(jj).transform("last").values
    k = np.searchsorted(t, tt.values, side="left") - 1
    k1 = np.minimum(k + 1, len(t) - 1)
    ok = (k >= 0) & (jj.values[np.maximum(k, 0)] == tt.index.values) & (jj.values[k1] == tt.index.values)
    c0 = d["cloture"].values[np.maximum(k, 0)]
    amp = np.maximum(sH[k1], c0) - np.minimum(sL[k1], c0)
    eff = np.abs(fin[k1] - c0) / amp
    amp = pd.Series(np.where(ok, amp, np.nan), tt.index)
    md = amp.rolling(60, min_periods=60).median().shift(1)
    y = np.where(amp > md, np.where(eff < 0.35, 2, 1), 0).astype(float)
    y[md.isna().values | amp.isna().values] = np.nan
    return pd.Series(y, tt.index)


# calendrier et taux (connus avant t)
ev = pd.DatetimeIndex(PA.CAL["US"])
tx = pd.read_csv(os.path.join(ICI, "data", "or_taux_jour.csv.gz"), index_col=0, parse_dates=True)[["nom10", "reel10", "dollar"]].dropna()
k = np.searchsorted(tx.index.values, JOURS.values, side="left") - 1   # derniere date civile < jour serveur
TX = pd.DataFrame(index=JOURS)
for cn in tx:
    a = tx[cn].values
    TX[cn + "_v1"] = a[k] - a[k - 1]
    TX[cn + "_v5"] = a[k] - a[k - 5]
TX["dollar_v1"] = TX["dollar_v1"] / tx["dollar"].values[k]; TX["dollar_v5"] = TX["dollar_v5"] / tx["dollar"].values[k]
COM = pd.DataFrame(index=JOURS)
COM["veille_tend"], COM["veille_AR"] = (J.type.shift(1) == 1).astype(float), (J.type.shift(1) == 2).astype(float)
for i, nm in enumerate(("lun", "mar", "mer", "jeu", "ven")):
    COM[nm] = (JOURS.dayofweek == i).astype(float)
evj = ev.floor("D")
COM["annonce_jour"] = JOURS.isin(evj).astype(float)

# gains des 4 regles par jour, pour les trades decides apres t
FAM = {n: v[3] for n, v in F.REGLES.items()}
DATA = {}
for h, tt in TT.items():
    X = [mesures(X5[n], tt, n) for n in X5]
    an = pd.DataFrame({"annonce_passee": [((ev >= tt[j].floor("D")) & (ev < tt[j])).any() for j in JOURS],
                       "annonce_avenir": [((ev >= tt[j]) & (ev < tt[j].floor("D") + pd.Timedelta("1D"))).any() for j in JOURS]}, JOURS).astype(float)
    OR = pd.concat([X[0], COM, an, TX], axis=1)
    TOUT = pd.concat([OR] + X[1:], axis=1)
    g = {"T": pd.Series(0.0, JOURS), "R": pd.Series(0.0, JOURS)}; n = {"T": pd.Series(0, JOURS), "R": pd.Series(0, JOURS)}
    for nm, x in F.T.items():
        dj = x.index.floor("D")
        apres = x.index.values >= tt.reindex(dj).values
        y = x[apres & dj.isin(JOURS)]
        g[FAM[nm]] = g[FAM[nm]].add(y.g.groupby(y.index.floor("D")).sum(), fill_value=0).reindex(JOURS).fillna(0)
        n[FAM[nm]] = n[FAM[nm]].add(y.g.groupby(y.index.floor("D")).size(), fill_value=0).reindex(JOURS).fillna(0)
    DATA[h] = dict(y=etiquette(tt), OR=OR, TOUT=TOUT, gT=g["T"], gR=g["R"], nT=n["T"], nR=n["R"])

debut_regles = min(x.index[0] for x in F.T.values()).floor("D")
ok = (JOURS >= debut_regles) & np.logical_and.reduce([DATA[h]["y"].notna().values & DATA[h]["OR"]["xau_amp0"].notna().values for h in TT])
JR = JOURS[ok]
mois = JR.to_period("M"); MO = mois.unique()
fen = [(MO[i - 6], MO[i - 3], MO[i - 1], MO[i]) for i in range(6, len(MO))]


# ---------------------------------------------------------------- modeles numpy
def prep(Xa, Xb):
    med = np.nanmedian(Xa, 0); med = np.where(np.isnan(med), 0, med)
    Xa = np.where(np.isnan(Xa), med, Xa); Xb = np.where(np.isnan(Xb), med, Xb)
    mu, sd = Xa.mean(0), Xa.std(0); sd[sd == 0] = 1
    return (Xa - mu) / sd, (Xb - mu) / sd


def logit(Xa, y, Xb, lam):
    n, p = Xa.shape; A = np.c_[np.ones(n), Xa]; Y = np.eye(3)[y]
    Lp = np.linalg.eigvalsh(A.T @ A / n).max() * 0.5 + lam
    W = np.zeros((p + 1, 3)); V = W.copy(); tk = 1.0
    for _ in range(300):
        Z = A @ V; Z -= Z.max(1, keepdims=True); P = np.exp(Z); P /= P.sum(1, keepdims=True)
        G = A.T @ (P - Y) / n; G[1:] += lam * V[1:]
        W1 = V - G / Lp; t1 = (1 + np.sqrt(1 + 4 * tk * tk)) / 2
        V = W1 + (tk - 1) / t1 * (W1 - W); W, tk = W1, t1
    imp = np.sqrt((W[1:] ** 2).sum(1))
    return (np.c_[np.ones(len(Xb)), Xb] @ W).argmax(1), imp


def arbre(X, y, prof, rng=None, mf=None, mini=8):
    imp = np.zeros(X.shape[1])
    def noeud(idx, pr):
        cnt = np.bincount(y[idx], minlength=3)
        if pr == 0 or len(idx) < 2 * mini or cnt.max() == len(idx):
            return cnt / cnt.sum()
        n = len(idx); g0 = 1 - ((cnt / n) ** 2).sum(); best = (0, None, None)
        feats = range(X.shape[1]) if mf is None else rng.choice(X.shape[1], mf, replace=False)
        for j in feats:
            xs = X[idx, j]; o = np.argsort(xs, kind="mergesort"); xs = xs[o]
            Yc = np.cumsum(np.eye(3)[y[idx][o]], 0); nl = np.arange(1, n + 1.0); Yr = cnt - Yc; nr = n - nl
            gi = (nl * (1 - ((Yc / nl[:, None]) ** 2).sum(1)) + nr * (1 - ((Yr / np.maximum(nr, 1)[:, None]) ** 2).sum(1))) / n
            val = np.zeros(n, bool); val[mini - 1:n - mini] = True; val[:-1] &= xs[:-1] < xs[1:]; val[-1] = False
            if not val.any():
                continue
            i = np.flatnonzero(val)[gi[val].argmin()]
            if g0 - gi[i] > best[0]:
                best = (g0 - gi[i], j, (xs[i] + xs[i + 1]) / 2)
        if best[1] is None:
            return cnt / cnt.sum()
        _, j, s = best; imp[j] += best[0] * n
        g = X[idx, j] <= s
        return (j, s, noeud(idx[g], pr - 1), noeud(idx[~g], pr - 1))
    return noeud(np.arange(len(y)), prof), imp


def predit(tree, X):
    if not isinstance(tree, tuple):
        return np.tile(tree, (len(X), 1))
    j, s, a, b = tree; out = np.empty((len(X), 3)); g = X[:, j] <= s
    out[g] = predit(a, X[g]); out[~g] = predit(b, X[~g])
    return out


def foret(Xa, y, Xb, rng):
    P = np.zeros((len(Xb), 3)); imp = np.zeros(Xa.shape[1]); mf = max(1, int(np.sqrt(Xa.shape[1])))
    for _ in range(25):
        b = rng.integers(len(y), size=len(y))
        t, im = arbre(Xa[b], y[b], 3, rng, mf)
        P += predit(t, Xb); imp += im
    return P.argmax(1), imp


MODELES = ["logit l0.3", "logit l0.03", "arbre p2", "arbre p3", "foret"]
def ajuste(mod, Xa, y, Xb, rng):
    Xa, Xb = prep(Xa, Xb)
    if mod.startswith("logit"):
        return logit(Xa, y, Xb, float(mod.split("l")[-1]))
    if mod.startswith("arbre"):
        t, imp = arbre(Xa, y, int(mod[-1]))
        return predit(t, Xb).argmax(1), (imp, t)
    return foret(Xa, y, Xb, rng)


tstat = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else 0.0
creux = lambda x: (x.cumsum() - x.cumsum().cummax()).min()
gain = lambda D, p, j: np.where(p == 1, D["gT"][j].values, np.where(p == 2, D["gR"][j].values, 0.0))
ntr = lambda D, p, j: np.where(p == 1, D["nT"][j].values, np.where(p == 2, D["nR"][j].values, 0))

rng = np.random.default_rng(11)
CFGS = [(h, m, s) for h in HEURES for m in MODELES for s in ("or", "tout")]
OOS = {c: [] for c in CFGS}; SEL = {h: [] for h in HEURES}; IMP = {h: {"logit": [], "foret": [], "racine": []} for h in HEURES}
for a, v, b, t in fen:
    app, val, apf, te = JR[(mois >= a) & (mois < v)], JR[(mois >= v) & (mois <= b)], JR[(mois >= a) & (mois <= b)], JR[mois == t]
    for h in HEURES:
        D = DATA[h]; sc = {}
        for c in [c for c in CFGS if c[0] == h]:
            Xs = D["OR" if c[2] == "or" else "TOUT"]
            pv, _ = ajuste(c[1], Xs.loc[app].values, D["y"][app].values.astype(int), Xs.loc[val].values, rng)
            sc[c] = tstat(gain(D, pv, val))
            pt, imp = ajuste(c[1], Xs.loc[apf].values, D["y"][apf].values.astype(int), Xs.loc[te].values, rng)
            OOS[c].append(pd.Series(pt, te))
            if c[2] == "tout":
                cols = np.array(Xs.columns)
                if c[1] == "logit l0.3": IMP[h]["logit"].append(cols[np.argsort(-imp)[:5]])
                if c[1] == "foret": IMP[h]["foret"].append(cols[np.argsort(-imp)[:5]])
                if c[1] == "arbre p3" and isinstance(imp[1], tuple): IMP[h]["racine"].append(cols[imp[1][0]])
        best = max(sc, key=sc.get); SEL[h].append((best, OOS[best][-1]))
OOS = {c: pd.concat(v) for c, v in OOS.items()}
TE = OOS[CFGS[0]].index

# ---------------------------------------------------------------- sorties
print("Or M5 courtier (+ nas, sp, argent, euro M5), jours avec etiquette et regles : %s -> %s (%d j) ; walk-forward %d fenetres, tests %s -> %s (%d j)"
      % (JR[0].date(), JR[-1].date(), len(JR), len(fen), fen[0][3], fen[-1][3], len(TE)))
print("N = %d reglages (3 heures x %d modeles x 2 jeux : or %d indices, tout %d) ; Bonferroni : t >= %.2f"
      % (len(CFGS), len(MODELES), DATA["9 h"]["OR"].shape[1], DATA["9 h"]["TOUT"].shape[1], statistics.NormalDist().inv_cdf(1 - 0.05 / len(CFGS))))
print("Types de la suite sur les jours de test (calme/tend/AR) : " + " ; ".join(
    "%s %s" % (h, "/".join("%.0f" % (100 * (DATA[h]["y"][TE] == k).mean()) for k in range(3))) for h in HEURES) + " %")
print("(a) Bonnes reponses hors echantillon (3 classes)      modele choisi | classe la + frequente | meme que la veille | reglage le plus choisi")
SCORES = {}
for h in HEURES:
    D = DATA[h]; y = D["y"]
    ps = pd.concat([s for _, s in SEL[h]])
    maj = pd.concat([pd.Series(int(D["y"][JR[(mois >= a) & (mois <= b)]].mode()[0]), JR[mois == t]) for a, _, b, t in fen])
    vei = y.shift(1)[TE]
    acc = (ps == y[TE]).mean(); SCORES[h] = acc
    fq = pd.Series([" ".join(c[1:]) for c, _ in SEL[h]]).value_counts()
    meil = max([c for c in CFGS if c[0] == h], key=lambda c: (OOS[c] == y[TE]).mean())
    print("  %-8s %47.0f %% | %20.0f %% | %17.0f %% | %s (%d/%d) ; meilleur fixe : %s %.0f %%" % (
        h, 100 * acc, 100 * (maj == y[TE]).mean(), 100 * (vei == y[TE]).mean(), fq.index[0], fq.iloc[0], len(fen),
        " ".join(meil[1:]), 100 * (OOS[meil] == y[TE]).mean()))
print("(b) $ hors echantillon, trades decides apres l'heure (0,01 lot)")
print("  %-8s %8s %5s %5s %6s %6s %7s | %7s %7s %7s %7s %13s | %8s %5s" % ("heure", "modele", "t", "trades", "bp/tr", "creux", "mois>0",
      "R0", "tend", "triche", "veille", "hasard moy/95", "mod-R0", "t"))
DIFF = {}
for h in HEURES:
    D = DATA[h]; ps = pd.concat([s for _, s in SEL[h]]); p = ps.values
    g = pd.Series(gain(D, p, TE), TE); nt = ntr(D, p, TE).sum()
    r0 = D["gT"][TE] + D["gR"][TE]; te_ = D["gT"][TE]
    tri = gain(D, D["y"][TE].values.astype(int), TE).sum()
    vv = D["y"].shift(1)[TE].fillna(0).values.astype(int); vei = gain(D, vv, TE).sum()
    mt = TE.to_period("M"); hz = []
    for _ in range(200):
        q = p.copy()
        for m in mt.unique():
            w = np.flatnonzero(mt == m); q[w] = rng.permutation(q[w])
        hz.append(gain(D, q, TE).sum())
    d = g - r0; DIFF[h] = (g, d)
    print("  %-8s %+8.0f %+5.1f %6d %+6.1f %+6.0f %3d/%-3d | %+7.0f %+7.0f %+7.0f %+7.0f %+6.0f/%+6.0f | %+8.0f %+5.1f" % (
        h, g.sum(), tstat(g), nt, g.sum() / 0.40 / max(nt, 1), creux(g), (g.groupby(mt).sum() > 0).sum(), len(mt.unique()),
        r0.sum(), te_.sum(), tri, vei, np.mean(hz), np.percentile(hz, 95), d.sum(), tstat(d)))
# relais : 9 h -> 12 h -> 15 h 30
hs = list(HEURES); rel = 0; r0r = 0; trr = 0
for i, h in enumerate(hs):
    D = DATA[h]; p = pd.concat([s for _, s in SEL[h]]).values; y = D["y"][TE].values.astype(int)
    nx = DATA[hs[i + 1]] if i + 1 < len(hs) else None
    seg = lambda key: D[key][TE].values - (nx[key][TE].values if nx is not None else 0)
    rel = rel + np.where(p == 1, seg("gT"), np.where(p == 2, seg("gR"), 0)); r0r = r0r + seg("gT") + seg("gR")
    trr = trr + np.where(y == 1, seg("gT"), np.where(y == 2, seg("gR"), 0))
rel = pd.Series(rel, TE)
print("  relais 9 h -> 12 h -> 15 h 30 : %+.0f $ (t %+.1f) contre R0 des 9 h %+.0f $ ; ecart %+.0f $ (t %+.1f) ; triche relais %+.0f $" % (
    rel.sum(), tstat(rel), r0r.sum(), (rel - r0r).sum(), tstat(rel - r0r), trr.sum()))

# reality check de White sur les 30 series hors echantillon (reglage fixe) contre R0 de la meme heure
def boot_idx(n, b=5.0):
    i = np.empty(n, int); i[0] = rng.integers(n); neuf = rng.random(n) < 1 / b; nv = rng.integers(n, size=n)
    for t in range(1, n):
        i[t] = nv[t] if neuf[t] else (i[t - 1] + 1) % n
    return i
M = np.column_stack([gain(DATA[c[0]], OOS[c].values, TE) - (DATA[c[0]]["gT"][TE] + DATA[c[0]]["gR"][TE]).values for c in CFGS])
n = len(TE); mu = M.mean(0); V = np.sqrt(n) * mu.max()
Vb = np.array([np.sqrt(n) * (M[ii].mean(0) - mu).max() for ii in (boot_idx(n) for _ in range(2000))])
kb = CFGS[int(mu.argmax())]; prc = (Vb >= V).mean()
tb = tstat(pd.Series(M[:, int(mu.argmax())]))
print("Reality check (30 reglages fixes, hors echantillon, contre R0) : meilleur %s %s %s : %+.0f $ contre R0 (t %+.1f), p = %.3f"
      % (*kb, mu.max() * n, tb, prc))
print("Reglages fixes battant R0 : %d/30 ; battant zero : %d/30" % ((mu > 0).sum(), sum(gain(DATA[c[0]], OOS[c].values, TE).sum() > 0 for c in CFGS)))
print("Indices qui pesent (jeu « tout », top 5 par fenetre, nombre de fenetres sur %d) :" % len(fen))
for h in HEURES:
    f = lambda L: ", ".join("%s %d" % (k, v) for k, v in pd.Series(np.concatenate(L)).value_counts().head(4).items())
    r = pd.Series(IMP[h]["racine"]).value_counts()
    print("  %-7s logit : %s | foret : %s | racine arbre : %s" % (h, f(IMP[h]["logit"]), f(IMP[h]["foret"]),
          ", ".join("%s %d" % kv for kv in r.head(2).items())))
print("Verdict (fixe d'avance, sur l'ecart au R0 : tient = ecart > 0 et (t >= 2,6 ou p RC < 0,05) ; presque = ecart > 0 et (t 1,5-2,6 ou p < 0,15)) :")
for h in HEURES:
    g, d = DIFF[h]; t = tstat(d); pp = prc if kb[0] == h else np.nan
    v = "tient" if d.sum() > 0 and (t >= 2.6 or pp < 0.05) else ("presque" if d.sum() > 0 and (1.5 <= t or pp < 0.15) else "ne tient pas")
    print("  %-8s %s (modele %+.0f $, ecart au R0 %+.0f $, t %+.1f%s)" % (h, v, g.sum(), d.sum(), t, ", p RC %.3f" % pp if pp == pp else ""))
out = os.environ.get("SCORES")
if out:
    with open(out, "w") as fo:
        fo.write("Taux de bonnes reponses hors echantillon (3 classes calme/tendance/aller-retour de la suite du jour), modele choisi en walk-forward 6 -> 1 mois, %d jours de test %s -> %s\n" % (len(TE), TE[0].date(), TE[-1].date()))
        for h in HEURES:
            fo.write("%s Paris : %.1f %%\n" % (h, 100 * SCORES[h]))
