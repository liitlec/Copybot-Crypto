"""Banc Astra (PRIORITES 23/11 10 h 20, texte astra_regimes_2311.md) : derniere experience bornee du detecteur de regime.
CONTRAT FIXE AVANT TOUT CALCUL (commit separe, avant le premier lancement) :

Donnees : or du courtier, M5 xau_m5_90k (08/2025 -> 11/2026) et M15 xau_m15_50k sur la meme periode ; spread reel
(colonne sp, prix en $/once) ; heure serveur = New York + 7 h (Paris = serveur - 1 h). Controle 4 ans (oracle et veto
seulement) : or H1 08/2022 -> 11/2026.
Familles (celles du labo, banc_famille, SANS la pause au calme v11 pour ne pas melanger deux filtres) :
  TENDANCE = elan_m15 + cassure_m15 ; RETOUR = fcassure_m5 + contre_exces_m5 ; une position a la fois par regle,
  decision a la cloture d'une bougie, entree a l'ouverture suivante (banc_or.trades), cout = spread reel (x2 = double).
  Controle H1 : TENDANCE = cassure_h1 (12 h, tenue 3 h) ; RETOUR = contre un exces H1 (rendement > 2,5 ecarts-types
  des 100 H1 precedentes, tenue 2 h). (cassure/retour du socle sont des miroirs, inutilisables ici.)
Unite R : budget de risque global a la decision, commun aux variantes. Une entree prise avec tout le budget = poids 1 ;
  1 R = ecart-type du gain d'un trade de la famille sur la chauffe 08-10/2025 (H1 : 08-10/2022). Allocations des
  NOUVELLES entrees decidees dans l'heure [H, H+1) : 50/50 = (0,5 ; 0,5) ; tendance seule = (1 ; 0) ;
  retour seul = (0 ; 1) ; veto = (0 ; 0). Les positions deja ouvertes suivent leurs sorties (le gain d'un trade va a
  l'heure de sa decision).
1. Oracle horaire : a chaque heure, meilleur des trois choix connu apres coup (tendance seule, retour seul, 50/50).
   Gain de l'oracle sur le 50/50 = borne haute. Seuil d'arret fixe : si la borne haute est < 0,05 R par heure qui
   change l'allocation, OU si les 10 meilleures heures font plus de 50 % du gain, la recherche du detecteur est jugee
   sans objet. On liste les 10 heures qui font le plus de gain.
2. Veto de cout : A = mediane, sur les 60 seances anterieures (meme heure serveur), de l'amplitude haut-bas de l'heure
   [H, H+1) ; c = cout aller-retour executable = 1,5 x mediane du spread des bougies M5 de l'heure precedente
   (spread une fois + provision de glissement 50 %). Si A/c < 4 : veto pendant l'heure, sinon 50/50.
   Placebos : (a) autant d'heures suspendues tirees au hasard dans les memes cases (heure serveur x mois), 1 000 tirages ;
   (b) reduction permanente du risque donnant la meme exposition moyenne (50/50 x part des trades gardes).
3. Prolongement apres retournement (changements directionnels) : par seance serveur, c = mediane sur les 20 seances
   anterieures du cout aller-retour journalier (1,5 x mediane du spread M5) ; delta = max(4 c ; 0,15 x ATR journalier
   14 seances terminees) ; clotures M5 ; inversion confirmee au premier recul de delta depuis l'extreme de cloture ;
   prolongement d'une jambe terminee = (extreme - prix de confirmation) / delta. A chaque heure pleine, mediane des 3
   derniers prolongements termines dans la seance : >= 1 -> tendance seule ; <= 0,25 -> retour seul ; sinon (ou moins
   de 3 jambes) 50/50. Placebo : 1 000 permutations des medianes entre seances, a heure egale et meme tiers de
   volatilite (delta), en gardant les heures ou 3 jambes existaient. Heure du 1er signal publiee (Paris).
4. Tenue du prix apres annonce (CPI, emploi US, 8 h 30 New York = 15:30 serveur ; dates de banc_annonces_levier) :
   P0 = cloture de la bougie 15:25 ; J = P5 - P0 (cloture 15:30) ; ignore si |J| < 2 x mediane |variation| de la bougie
   15:30 sur les 60 seances anterieures ; F = (P15 - P0) / J (cloture de la bougie 15:40). F >= 0,75 -> tendance dans le
   sens du choc ; F <= 0,25 et P0 non traverse entre 15:30 et 15:45 -> retour vers P0 ; sinon 50/50 ; expire a +60 min.
   Mesure : (a) poids sur les familles (tendance seulement dans le sens du choc, retour seulement vers P0) dans
   [15:45, 16:30) ; (b) trade direct de l'autorisation : entree a l'ouverture 15:45, sortie a la cloture 16:25
   (bougie de 16:25), spread reel. Placebo : faux evenements a 15:30 les autres jours de meme jour de semaine passant
   le meme seuil |J|, 1 000 tirages de meme taille. Exploratoire (peu d'evenements).
Retard en argent (regles 3 et 4) : a chaque alerte, heure, premier prix executable, gain deja passe (famille favorisee
  moins 50/50, du debut de seance a l'alerte) et gain encore accessible (de l'alerte a la fin de seance).
Verdict (pour chaque regle 2, 3, 4, contre le 50/50 ; fixe d'avance) : TIENT si les 6 conditions :
  (i) gain net moyen >= +0,05 R par heure ou la regle change l'allocation ; (ii) gain net total > 0 avec couts doubles ;
  (iii) pire recul (cumul de R) pas pire que celui du 50/50 ; (iv) borne basse de l'IC a 95 % du gain journalier
  incremental > 0 apres correction pour 3 essais (quantile unilateral 1,67 %, bootstrap stationnaire blocs moyens 5 j,
  2 000 tirages) ; (v) test SPA de Hansen (3 regles contre 50/50) p < 0,05 ; (vi) bat son placebo (p < 0,05).
  INDETERMINE si gain total > 0 et (i) tient mais l'IC contient 0 ; sinon NE TIENT PAS.
  Une regle qui tient part en demo `_opt` hors totaux (6 mois prospectifs) ; si rien ne bat le 50/50 : arreter la
  recherche du detecteur sur cet historique et le dire. Usage : python3 banc_astra.py
"""
import contextlib, io, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_or as B
with contextlib.redirect_stdout(io.StringIO()):
    import banc_annonces_levier as AL

RNG = np.random.default_rng(2311)
H1T = pd.Timedelta("1h")

# ------------------------------------------------------------------------------------------------ donnees et familles
m15, _ = B.charge("xau_m15_50k"); m5, _ = B.charge("xau_m5_90k")
m15 = m15[m15.index >= m5.index[0]]
BAR = {"m5": pd.Timedelta("5min"), "m15": pd.Timedelta("15min"), "h1": H1T}


def signaux_m():
    lr = np.log(m15["cloture"])
    s_elan = np.sign(lr - lr.shift(12))
    ha, ba = m15["haut"].shift(1).rolling(48).max(), m15["bas"].shift(1).rolling(48).min()
    s_cass = (m15["cloture"] > ha).astype(float) - (m15["cloture"] < ba).astype(float)
    h5, b5 = m5["haut"].shift(1).rolling(12).max(), m5["bas"].shift(1).rolling(12).min()
    s_fc = (m5["cloture"] < b5).astype(float) - (m5["cloture"] > h5).astype(float)
    r = np.log(m5["cloture"]).diff(); z = r / r.rolling(100).std().shift(1)
    s_cx = (z < -3).astype(float) - (z > 3).astype(float)
    return [("elan_m15", m15, s_elan, 12, "m15", "T"), ("cassure_m15", m15, s_cass, 12, "m15", "T"),
            ("fcassure_m5", m5, s_fc, 3, "m5", "R"), ("contre_exces_m5", m5, s_cx, 3, "m5", "R")]


def familles(regles, mult, chauffe):
    """Trades : DataFrame (dec = heure de decision = cloture de la bougie, fam T/R, s sens, g en R)."""
    out = []
    for nom, d, s, h, tf, fam in regles:
        x, i = B.trades(d, s, h, mult=mult)
        out.append(pd.DataFrame({"dec": d.index[i] + BAR[tf], "fam": fam, "regle": nom,
                                 "s": np.sign(s.values[i]), "g": x[:, 0], "px": d["ouverture"].values[np.minimum(i + 1, len(d) - 1)]}))
    T = pd.concat(out, ignore_index=True).sort_values("dec").reset_index(drop=True)
    T["g"] = T.g * T.px / 1e4                                  # bp -> $ par once
    return T


def en_R(T, ech):
    T = T.copy(); T["g"] = T.g / T.fam.map(ech); T["H"] = T.dec.dt.floor("h"); T["jour"] = T.dec.dt.floor("D")
    return T


def echelle(T, debut, fin):
    k = (T.dec >= debut) & (T.dec < fin)
    return {f: T.g[k & (T.fam == f)].std() for f in ("T", "R")}


# ------------------------------------------------------------------------------------------------ outils
def par_heure(T):
    """Gains (R) des nouvelles entrees par heure de decision et famille, poids 1 (tout le budget)."""
    P = T.pivot_table(index="H", columns="fam", values="g", aggfunc="sum").fillna(0.0)
    for f in ("T", "R"):
        if f not in P:
            P[f] = 0.0
    return P[["T", "R"]]


def alloue(P, W):
    """W : DataFrame (index heures, colonnes T, R) ; heures absentes = 50/50. Rend le gain par heure."""
    W = W.reindex(P.index).fillna(0.5)
    return P["T"] * W["T"] + P["R"] * W["R"]


def W5050(P):
    return pd.DataFrame(0.5, index=P.index, columns=["T", "R"])


def creux(x):
    c = np.cumsum(np.asarray(x)); return float((c - np.maximum.accumulate(np.r_[0, c])[1:]).min())


def boot(n, Bn=2000, b=5.0, rng=None):
    rng = rng or np.random.default_rng(5)
    out = np.empty((Bn, n), int)
    for k in range(Bn):
        neuf = rng.random(n) < 1 / b; neuf[0] = True
        bl = np.cumsum(neuf) - 1; deb = np.flatnonzero(neuf)
        out[k] = (rng.integers(n, size=len(deb))[bl] + np.arange(n) - deb[bl]) % n
    return out


def ic_bas(d, q=0.05 / 3):
    """Borne basse unilaterale (quantile q) de la moyenne journaliere, bootstrap stationnaire."""
    d = np.asarray(d, float); ii = boot(len(d))
    m = np.array([d[k].mean() for k in ii])
    return float(np.quantile(m, q)), float(d.mean())


def spa(D):
    """Test SPA de Hansen (version consistante, studentise) ; D = jours x modeles (gain - benchmark)."""
    D = np.asarray(D, float); n, k = D.shape
    mu = D.mean(0); ii = boot(n, rng=np.random.default_rng(7))
    Mb = np.array([D[j].mean(0) for j in ii])
    om = np.sqrt(n) * Mb.std(0); om[om == 0] = np.inf
    T = max(0.0, (np.sqrt(n) * mu / om).max())
    seuil = -np.sqrt(2 * np.log(np.log(n))) * om / np.sqrt(n)
    muc = np.where(mu >= seuil, mu, 0.0)
    Tb = np.array([max(0.0, (np.sqrt(n) * (Mb[j] - mu + muc) / om).max()) for j in range(len(Mb))])
    return float((Tb >= T).mean())


def jour_serie(g, jours):
    return g.groupby(g.index.floor("D")).sum().reindex(jours).fillna(0.0)


RES = {}


def juge(nom, P1, P2, W, placebo_p, jours, extra=""):
    """P1, P2 : gains par heure (spread x1, x2) ; W : allocation de la regle."""
    b1, r1 = alloue(P1, W5050(P1)), alloue(P1, W)
    b2, r2 = alloue(P2, W5050(P2)), alloue(P2, W)
    Wr = W.reindex(P1.index).fillna(0.5)
    chg = ((Wr["T"] != 0.5) | (Wr["R"] != 0.5)) & ((P1["T"] != 0) | (P1["R"] != 0))
    d = r1 - b1
    par_dec = d[chg].sum() / max(chg.sum(), 1)
    dj = jour_serie(d, jours)
    lo, mu = ic_bas(dj.values)
    c_r, c_b = creux(jour_serie(r1, jours)), creux(jour_serie(b1, jours))
    cond = {"i +0,05 R/decision": par_dec >= 0.05, "ii couts doubles > 0": (r2 - b2).sum() > 0,
            "iii recul pas pire": c_r >= c_b, "iv IC bas > 0": lo > 0, "vi placebo": placebo_p < 0.05}
    RES[nom] = dict(dj=dj, cond=cond, par_dec=par_dec, n_chg=int(chg.sum()), tot=d.sum(), tot2=(r2 - b2).sum(),
                    lo=lo, creux_r=c_r, creux_b=c_b, p_plac=placebo_p, b_tot=b1.sum(), r_tot=r1.sum(), extra=extra)
    print("  %s : 50/50 %+.1f R, regle %+.1f R (diff %+.1f ; couts x2 %+.1f) ; %d heures changees, %+.3f R par heure changee ;"
          " creux %.1f contre %.1f ; IC bas (3 essais) %+.4f R/j (moy %+.4f) ; placebo p %.3f"
          % (nom, b1.sum(), r1.sum(), d.sum(), (r2 - b2).sum(), chg.sum(), par_dec, c_r, c_b, lo, mu, placebo_p))


# ------------------------------------------------------------------------------------------------ calcul principal
REG = signaux_m()
T1, T2 = familles(REG, 1.0, None), familles(REG, 2.0, None)
ECH = echelle(T1, pd.Timestamp("2025-08-01"), pd.Timestamp("2025-11-01"))
T1, T2 = en_R(T1, ECH), en_R(T2, ECH)
P1, P2 = par_heure(T1), par_heure(T2)
JOURS = pd.DatetimeIndex(sorted(set(m5.index.floor("D")))); JOURS = JOURS[JOURS.dayofweek < 5]
print("Or M5/M15 %s -> %s ; %d jours ; trades tendance %d, retour %d ; 1 R = %s $/once par trade"
      % (m5.index[0].date(), m5.index[-1].date(), len(JOURS), (T1.fam == "T").sum(), (T1.fam == "R").sum(),
         {k: round(v, 2) for k, v in ECH.items()}))
for nom, P in (("spread reel", P1), ("spread double", P2)):
    print("  Temoins (%s) : 50/50 %+.1f R ; tendance seule %+.1f ; retour seul %+.1f"
          % (nom, alloue(P, W5050(P)).sum(), P["T"].sum(), P["R"].sum()))


# ---- 1. oracle horaire
def oracle(P, titre):
    b = 0.5 * (P["T"] + P["R"])
    best = pd.concat([b, P["T"], P["R"]], axis=1).max(axis=1)
    g = best - b
    chg = g > 1e-12
    top = g.sort_values(ascending=False)
    part10 = top.head(10).sum() / g.sum() if g.sum() > 0 else np.nan
    print("\n1. ORACLE HORAIRE (%s) : 50/50 %+.1f R ; oracle %+.1f R ; borne haute %+.1f R sur %d heures changees "
          "(%+.3f R par heure changee ; %.2f R par jour) ; les 10 meilleures heures = %.0f %% du gain"
          % (titre, b.sum(), best.sum(), g.sum(), chg.sum(), g.sum() / max(chg.sum(), 1), g.sum() / len(set(P.index.floor("D"))), 100 * part10))
    return g, part10


g_or, part10 = oracle(P1, "or M5/M15, spread reel")
oracle(P2, "spread double")
top = g_or.sort_values(ascending=False).head(10)
print("  10 heures qui font le plus de gain (heure de Paris, gain R, choix) :")
for h, v in top.items():
    ch = "tendance" if P1.loc[h, "T"] > P1.loc[h, "R"] else "retour"
    print("    %s  %+.2f R  %s (T %+.2f, R %+.2f)" % ((h - H1T).strftime("%Y-%m-%d %H:%M"), v, ch, P1.loc[h, "T"], P1.loc[h, "R"]))
# controle AJOUTE APRES le premier lancement (hors contrat) : meme oracle quand les gains « retour » sont melanges entre
# heures (tendance et retour sans lien) : si la borne haute est la meme, elle ne mesure que le bruit.
_g = []
for _ in range(200):
    Q = P1.copy(); Q["R"] = RNG.permutation(P1["R"].values); b_ = 0.5 * (Q["T"] + Q["R"])
    _g.append((pd.concat([b_, Q["T"], Q["R"]], axis=1).max(axis=1) - b_).sum())
print("  Controle (ajoute apres coup) : borne haute avec heures melangees au hasard %+.1f R (q5-q95 %+.1f / %+.1f) "
      "contre %+.1f R reel" % (np.median(_g), np.quantile(_g, .05), np.quantile(_g, .95), g_or.sum()))
seuil_ok = (g_or.sum() / max((g_or > 0).sum(), 1) >= 0.05) and part10 <= 0.5
print("  Seuil d'arret (contrat) : %s" % ("depasse, on continue" if seuil_ok else "NON atteint : detecteur sans objet"))

# ---- 2. veto de cout
hm = m5.copy(); hm["H"] = hm.index.floor("h")
Hh = hm.groupby("H").agg(haut=("haut", "max"), bas=("bas", "min"), sp=("sp", "median"))
Hh["amp"] = Hh.haut - Hh.bas
Hh["slot"] = Hh.index.hour
A = Hh.groupby("slot")["amp"].transform(lambda s: s.shift(1).rolling(60, min_periods=30).median())
c = 1.5 * Hh["sp"].shift(1)                                      # spread median de l'heure precedente (connu)
ratio = (A / c).reindex(P1.index)
veto = ratio < 4
Wv = W5050(P1); Wv.loc[veto.fillna(False).values, ["T", "R"]] = 0.0
print("\n2. VETO DE COUT (A/c < 4) : %d heures avec trades sur %d en veto (%.1f %%) ; A/c median %.1f (q10 %.1f)"
      % (veto.sum(), len(P1), 100 * veto.mean(), ratio.median(), ratio.quantile(0.1)))
# placebo (a) : memes cases heure x mois
case = pd.Series(P1.index.hour.astype(str) + "_" + P1.index.strftime("%Y-%m"), index=P1.index)
nv = veto.fillna(False).groupby(case).sum()
b1 = alloue(P1, W5050(P1)); rv = alloue(P1, Wv)
pl = []
grp = {k: np.flatnonzero((case == k).values) for k in nv.index[nv > 0]}
for _ in range(1000):
    m = np.zeros(len(P1), bool)
    for k, ix in grp.items():
        m[RNG.choice(ix, int(nv[k]), replace=False)] = True
    pl.append(b1[~m].sum())
pl = np.array(pl)
p_v = float((pl >= rv.sum()).mean()) if veto.sum() else 1.0
garde = 1 - (veto.fillna(False) & ((P1["T"] != 0) | (P1["R"] != 0))).sum() / max(((P1["T"] != 0) | (P1["R"] != 0)).sum(), 1)
print("  Placebo (a) memes cases : mediane %+.1f R (regle %+.1f) p %.3f ; placebo (b) risque x %.3f partout : %+.1f R"
      % (np.median(pl) if len(pl) else np.nan, rv.sum(), p_v, garde, garde * b1.sum()))
juge("veto de cout", P1, P2, Wv, p_v, JOURS)

# ---- 3. prolongement apres retournement
jr = m5.index.floor("D")
D = m5.groupby(jr).agg(h=("haut", "max"), l=("bas", "min"), c=("cloture", "last"), sp=("sp", "median"))
tr_ = np.maximum(D.h - D.l, np.maximum((D.h - D.c.shift(1)).abs(), (D.l - D.c.shift(1)).abs()))
ATR = tr_.rolling(14).mean().shift(1)
cj = (1.5 * D.sp).rolling(20).median().shift(1)
DELTA = np.maximum(4 * cj, 0.15 * ATR)


def prolongements(delta_s):
    """Pour chaque seance : liste (heure de fin, prolongement) des jambes terminees (clotures M5)."""
    out = {}
    for j, g in m5.groupby(jr):
        dl = delta_s.get(j, np.nan)
        if not dl > 0:
            continue
        cl, tt = g["cloture"].values, g.index + BAR["m5"]
        hi = lo = cl[0]; sens, conf, ext = 0, None, None; L = []
        for k in range(len(cl)):
            x = cl[k]
            if sens == 0:
                hi, lo = max(hi, x), min(lo, x)
                if x >= lo + dl:
                    sens, conf, ext = 1, x, x
                elif x <= hi - dl:
                    sens, conf, ext = -1, x, x
            elif sens == 1:
                ext = max(ext, x)
                if x <= ext - dl:
                    L.append((tt[k], (ext - conf) / dl)); sens, conf, ext = -1, x, x
            else:
                ext = min(ext, x)
                if x >= ext + dl:
                    L.append((tt[k], (conf - ext) / dl)); sens, conf, ext = 1, x, x
        out[j] = L
    return out


LEG = prolongements(DELTA)
rows = []
for j, L in LEG.items():
    if len(L) < 3:
        continue
    fins = np.array([t for t, _ in L], dtype="datetime64[ns]"); v = np.array([p for _, p in L])
    for H in pd.date_range(j + H1T, j + pd.Timedelta("23h"), freq="h"):
        n = np.searchsorted(fins, np.datetime64(H), side="right")
        if n >= 3:
            rows.append((H, j, float(np.median(v[n - 3:n]))))
M = pd.DataFrame(rows, columns=["H", "jour", "med"]).set_index("H")
M["slot"] = M.index.hour
M["vol"] = pd.qcut(DELTA.reindex(M.jour).values, 3, labels=False, duplicates="drop")


def W_prol(med):
    W = pd.DataFrame(0.5, index=med.index, columns=["T", "R"])
    W.loc[med >= 1, ["T", "R"]] = [1.0, 0.0]; W.loc[med <= 0.25, ["T", "R"]] = [0.0, 1.0]
    return W[~W.index.duplicated()]


Wp = W_prol(M["med"])
rp = alloue(P1, Wp).sum()
pl = []
cle = M["slot"].astype(str) + "_" + M["vol"].astype(str)
for _ in range(1000):
    med2 = M["med"].copy()
    for k, ix in cle.groupby(cle).indices.items():
        med2.iloc[ix] = M["med"].values[RNG.permutation(ix)]
    pl.append(alloue(P1, W_prol(med2)).sum())
pl = np.array(pl); p_p = float((pl >= rp).mean())
sig = M[(M.med >= 1) | (M.med <= 0.25)]
prem = sig.groupby("jour").apply(lambda g: g.index.min())
hp = (pd.DatetimeIndex(prem.values) - H1T).hour                   # heure de Paris
print("\n3. PROLONGEMENT : delta median %.2f $ ; jambes par seance mediane %.0f ; heures avec 3 jambes %d ; tendance %d h, retour %d h"
      % (DELTA.median(), np.median([len(L) for L in LEG.values()]), len(M), (M.med >= 1).sum(), (M.med <= 0.25).sum()))
print("  1er signal de la seance (heure de Paris) : mediane %s h, quartiles %s-%s h ; %.0f %% des seances avec signal apres 18 h"
      % (np.median(hp), np.quantile(hp, .25), np.quantile(hp, .75), 100 * np.mean(hp >= 18)))
print("  Placebo (permutations a heure et volatilite egales) : mediane %+.1f R, regle %+.1f R, p %.3f" % (np.median(pl), rp, p_p))
juge("prolongement", P1, P2, Wp, p_p, JOURS)


def retard(W, titre):
    """Pour chaque alerte (passage a tendance ou retour dans une seance) : deja passe / encore accessible (R)."""
    W = W.reindex(P1.index).dropna(); etat = np.where(W["T"] > 0.5, "T", np.where(W["R"] > 0.5, "R", "-"))
    E = pd.Series(etat, index=W.index)
    rows = []
    for j, e in E.groupby(E.index.floor("D")):
        prev = "-"
        for H, v in e.items():
            if v != "-" and v != prev:
                Pj = P1[P1.index.floor("D") == j]
                diff = Pj[v] - 0.5 * (Pj["T"] + Pj["R"])
                px = m5["ouverture"].asof(H) if H >= m5.index[0] else np.nan
                rows.append((H, v, px, diff[diff.index < H].sum(), diff[diff.index >= H].sum()))
            prev = v
    R_ = pd.DataFrame(rows, columns=["H", "etat", "px", "passe", "accessible"])
    if len(R_):
        print("  Retard en argent (%s) : %d alertes ; deja passe : somme %+.1f R (mediane %+.2f) ; encore accessible : "
              "somme %+.1f R (mediane %+.2f)" % (titre, len(R_), R_.passe.sum(), R_.passe.median(), R_.accessible.sum(), R_.accessible.median()))
    return R_


RET = {"prolongement": retard(Wp, "prolongement")}

# ---- 4. annonces
EV = [(t, ty) for t, ty in AL.EV if ty in ("NFP", "CPI") and t >= m5.index[0] + pd.Timedelta(days=90) and t <= m5.index[-1]]
cl = m5["cloture"]
dcl = cl.diff()
slot = pd.Series(m5.index.strftime("%H:%M"), index=m5.index)
med_abs = dcl.abs().groupby(slot).transform(lambda s: s.shift(1).rolling(60, min_periods=20).median())


def lit(t0):
    """Etat de la regle pour un evenement a t0 (heure serveur de publication). None si donnees manquantes."""
    try:
        P0 = cl.loc[t0 - pd.Timedelta("5min")]; P5 = cl.loc[t0]; P15 = cl.loc[t0 + pd.Timedelta("10min")]
        seuil = 2 * med_abs.loc[t0]
        fen = cl.loc[t0:t0 + pd.Timedelta("10min")]
        o = m5["ouverture"].loc[t0 + pd.Timedelta("15min")]; x = cl.loc[t0 + pd.Timedelta("55min")]
        sp = m5["sp"].loc[t0 + pd.Timedelta("15min")]
    except KeyError:
        return None
    J = P5 - P0
    if not (abs(J) >= seuil > 0):
        return ("petit", 0, 0.0)
    F = (P15 - P0) / J
    if F >= 0.75:
        s = np.sign(J); etat = "tendance"
    elif F <= 0.25 and not ((fen - P0) * np.sign(J) < 0).any():
        s = -np.sign(J); etat = "retour"
    else:
        return ("50/50", 0, 0.0)
    g = (s * (x - o) - sp) / ATR.get(t0.floor("D"), np.nan)            # trade direct, en ATR journalier
    return (etat, s, g)


ev_rows = []
for t0, ty in EV:
    r = lit(t0)
    if r is not None:
        ev_rows.append((t0, ty) + r)
EVd = pd.DataFrame(ev_rows, columns=["t0", "type", "etat", "s", "g"])
act = EVd[EVd.etat.isin(["tendance", "retour"])]
# poids sur les familles dans [15:45, 16:30)
Wa = pd.DataFrame(columns=["T", "R"], dtype=float)
gain_fam = 0.0
for _, e in act.iterrows():
    k = (T1.dec >= e.t0 + pd.Timedelta("15min")) & (T1.dec < e.t0 + pd.Timedelta("60min"))
    x = T1[k]
    fav = (x.fam == "T") & (x.s == e.s) if e.etat == "tendance" else (x.fam == "R") & (x.s == e.s)
    gain_fam += (np.where(fav, 1.0, 0.0) * x.g).sum() - (0.5 * x.g).sum()
# placebo : faux evenements, memes jour de semaine, a 15:30
vrais = {t.floor("D") for t, _ in AL.EV}
faux = []
for t0 in pd.date_range((m5.index[0] + pd.Timedelta(days=90)).normalize(), m5.index[-1].normalize(), freq="D") + pd.Timedelta("15:30:00"):
    if t0.floor("D") in vrais or t0.dayofweek >= 5:
        continue
    r = lit(t0)
    if r is not None and r[0] in ("tendance", "retour"):
        faux.append((t0.dayofweek, r[2]))
faux = pd.DataFrame(faux, columns=["dow", "g"])
pl = []
if len(act) and len(faux):
    dows = act.t0.dt.dayofweek.values
    for _ in range(1000):
        pl.append(np.mean([faux.g[faux.dow == d].sample(1, random_state=int(RNG.integers(1e9))).iloc[0]
                           if (faux.dow == d).any() else np.nan for d in dows]))
pl = np.array(pl); gm = act.g.mean() if len(act) else np.nan
p_a = float(np.nanmean(pl >= gm)) if len(pl) else 1.0
print("\n4. ANNONCES (CPI + emploi, %d evenements avec donnees) : %d petits, %d en 50/50, %d tendance, %d retour"
      % (len(EVd), (EVd.etat == "petit").sum(), (EVd.etat == "50/50").sum(), (EVd.etat == "tendance").sum(), (EVd.etat == "retour").sum()))
print("  Trade direct 15:45 -> 16:30 : moyenne %+.3f ATR par evenement (n %d ; gagnants %d) ; faux evenements : %d, "
      "moyenne %+.3f ATR ; placebo p %.3f" % (gm, len(act), (act.g > 0).sum(), len(faux), faux.g.mean() if len(faux) else np.nan, p_a))
print("  Poids sur les familles (15:45-16:30) : %+.2f R contre le 50/50 sur %d evenements" % (gain_fam, len(act)))
for _, e in act.iterrows():
    print("    %s %s %-8s trade direct %+.3f ATR" % ((e.t0 - H1T).strftime("%Y-%m-%d %H:%M"), e.type, e.etat, e.g))
Wa_rows = {}
for _, e in act.iterrows():
    Wa_rows[e.t0.floor("h") + H1T] = None                       # (familles : effet compte ci-dessus, a la minute)

# ---- SPA (3 regles contre 50/50) et verdicts
dj_ann = pd.Series(0.0, index=JOURS)
for _, e in act.iterrows():
    k = (T1.dec >= e.t0 + pd.Timedelta("15min")) & (T1.dec < e.t0 + pd.Timedelta("60min"))
    x = T1[k]
    fav = (x.fam == "T") & (x.s == e.s) if e.etat == "tendance" else (x.fam == "R") & (x.s == e.s)
    if e.t0.floor("D") in dj_ann.index:
        dj_ann[e.t0.floor("D")] += (np.where(fav, 1.0, 0.0) * x.g).sum() - (0.5 * x.g).sum()
lo_a, mu_a = ic_bas(dj_ann.values)
RES["annonces"] = dict(dj=dj_ann, cond={"i +0,05 R/decision": (gain_fam / max(len(act), 1)) >= 0.05,
                                        "ii couts doubles > 0": None, "iii recul pas pire": None,
                                        "iv IC bas > 0": lo_a > 0, "vi placebo": p_a < 0.05},
                       par_dec=gain_fam / max(len(act), 1), n_chg=len(act), tot=gain_fam, lo=lo_a, p_plac=p_a)
Dm = np.column_stack([RES[k]["dj"].reindex(JOURS).fillna(0).values for k in ("veto de cout", "prolongement", "annonces")])
p_spa = spa(Dm)
print("\nSPA de Hansen (3 regles contre 50/50, gain journalier) : p = %.3f" % p_spa)
print("\nVERDICTS (contrat fixe d'avance) :")
for k, r in RES.items():
    c = dict(r["cond"]); c["v SPA < 0,05"] = p_spa < 0.05
    tous = all(v for v in c.values() if v is not None) and all(v is not None for v in c.values())
    ind = (r["tot"] > 0) and bool(c["i +0,05 R/decision"]) and not tous
    v = "TIENT" if tous else ("INDETERMINE" if ind else "NE TIENT PAS")
    print("  %-14s %-13s %+.1f R sur %d decisions (%+.3f R par decision) ; %s"
          % (k, v, r["tot"], r["n_chg"], r["par_dec"],
             " ; ".join("%s %s" % (kk, "oui" if vv else ("—" if vv is None else "non")) for kk, vv in c.items())))

# ------------------------------------------------------------------------------------------------ controle 4 ans (H1)
h1, _ = B.charge("xau_h1_50k"); h1 = h1[h1.index >= pd.Timestamp("2022-07-01")]
hh, bb = h1["haut"].shift(1).rolling(12).max(), h1["bas"].shift(1).rolling(12).min()
sc = (h1["cloture"] > hh).astype(float) - (h1["cloture"] < bb).astype(float)
rr = np.log(h1["cloture"]).diff(); zz = rr / rr.rolling(100).std().shift(1)
sx = (zz < -2.5).astype(float) - (zz > 2.5).astype(float)
REG_H = [("cassure_h1", h1, sc, 3, "h1", "T"), ("exces_h1", h1, sx, 2, "h1", "R")]
for mult in (1.0, 2.0):
    TH = familles(REG_H, mult, None)
    if mult == 1.0:
        EH = echelle(TH, pd.Timestamp("2022-08-01"), pd.Timestamp("2022-11-01"))
    TH = en_R(TH, EH); TH = TH[TH.dec >= pd.Timestamp("2022-11-01")]
    PH = par_heure(TH)
    print("\nCONTROLE 4 ANS or H1 (spread x%.0f), 11/2022 -> 11/2026 : 50/50 %+.1f R ; tendance seule %+.1f ; retour seul %+.1f"
          % (mult, alloue(PH, W5050(PH)).sum(), PH["T"].sum(), PH["R"].sum()))
    gH, p10 = oracle(PH, "H1 4 ans, spread x%.0f" % mult)
    for a, b_ in (("2022-11-01", "2024-08-01"), ("2024-08-01", "2027-01-01")):
        k = (gH.index >= a) & (gH.index < b_)
        print("    %s -> %s : borne haute %+.1f R sur %d heures" % (a[:7], b_[:7], gH[k].sum(), (gH[k] > 0).sum()))
    hx = h1.copy(); hx["amp"] = hx.haut - hx.bas; hx["slot"] = hx.index.hour
    AH = hx.groupby("slot")["amp"].transform(lambda s: s.shift(1).rolling(60, min_periods=30).median())
    cH = 1.5 * hx["sp"].shift(1)
    vH = (AH / cH).reindex(PH.index) < 4
    WH = W5050(PH); WH.loc[vH.fillna(False).values, ["T", "R"]] = 0.0
    print("    Veto de cout H1 : %d heures sur %d (%.1f %%) ; 50/50 %+.1f R, avec veto %+.1f R"
          % (vH.sum(), len(PH), 100 * vH.mean(), alloue(PH, W5050(PH)).sum(), alloue(PH, WH).sum()))
