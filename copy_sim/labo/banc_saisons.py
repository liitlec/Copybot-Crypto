"""Banc SAISONS : effets de calendrier et d'heure, plan fixe d'avance, walk-forward glissant + reality check de White.
Deja fait ailleurs (pas refait) : fin de mois conditionnelle (banc_finmois.py, banc_finmois_fx.py) et effet d'une heure
isolee (banc G, B.par_heure dans banc_or.py). Ici, regles PURES de calendrier, sans condition de prix.
(a) Jour de la semaine : tenir de la cloture de la veille a la cloture du jour J ; grille 5 jours x {achat, vente} = 10
    par marche ; or, Nasdaq 100, S&P 500, Dow, DAX ; Yahoo journalier 2000-2026 ET bougies jour du courtier.
(b) Tournant du mois (jours de bourse) : 3 derniers, 3 premiers, dernier + 3 premiers, 3 derniers + 3 premiers ;
    x {achat, vente} = 8 par marche ; Yahoo journalier, memes 5 marches. Le dernier mois incomplet est ignore.
(c) Fenetres d'heures (bougies du courtier, spread reel sp de la bougie d'entree / de sortie) : Londres 9 h-10 h et
    9 h-12 h (Paris) ; New York 9 h 30-10 h 30 et 9 h 30-16 h (heure de New York, soit 15 h 30 a Paris hors semaines
    de decalage) ; nuit 22 h-8 h Paris (nuits de semaine seulement). Achat / vente de la fenetre entiere (10) + suivre /
    contrer le sens de la fenetre precedente : Asie (1 h-9 h Paris) -> Londres 9-10 et 9-12, Londres (9 h Paris ->
    9 h 30 NY) -> NY 1re heure et seance (8). N = 18 par fichier : or M5, or M15, Nasdaq M5, S&P M5, Dow M5.
(d) Nuit contre jour sur indices : nuit = achat/vente a la cloture au comptant (16 h NY ; DAX 17 h 30), sortie a
    l'ouverture (9 h 30 NY ; DAX 9 h) ; jour = l'inverse. Grille {nuit, jour} x {achat, vente} x {tous, sauf lundi}
    = 8 par marche. Yahoo (ouverture/cloture du jour, annees a ouvertures figees exclues) et courtier M5.
Fuseau du courtier : horloge serveur = heure de New York + 7 h (verifie : pic de volume a 16 h 30 serveur toute
l'annee) ; conversion vers Paris et New York par les fuseaux officiels (changements d'heure geres).
Couts : spread mediane du courtier a l'heure de l'entree (achat) ou de la sortie (vente) pour Yahoo et les bougies jour ;
spread de la bougie en intrajournalier (prix vendeur : achat a bid + sp). Portage CFD par nuit calendaire (week-end
= 3), hypothese calee sur les swaps reels de mt5/autres/historique.csv.gz (taux 3 mois US r) : indices achat r + 3 %,
vente 2,6 % - r ; DAX achat r + 1,5 %, vente 4,1 % - r (taux euro ~ r - 1,5) ; or achat max(r - 0,4 %, 1 %), vente
0,7 % - r ; par an / 360.
Methode : series de gain par jour ; walk-forward glissant (journalier : apprentissage 3 ans civils, test 1 an ;
intrajournalier : 6 mois / 1 mois), choix au meilleur t sur l'apprentissage ; reality check de White (bootstrap
stationnaire, blocs moyens 5 j, 2000 tirages) contre « ne rien faire », par ligne (N de la ligne) ET sur toute la
sous-partie. Reference : regle de base a exposition egale (achat permanent x part du temps expose ; pour suivre /
contrer : achat de la meme fenetre). Verdict (par ligne, p de la ligne) : tient = HE > 0 et (t >= 2,6 ou p < 0,05) ;
presque = HE > 0 et (t >= 1,5 ou p < 0,15) ; sinon ne tient pas. Usage : python3 banc_saisons.py"""
import contextlib, io
from statistics import NormalDist
import numpy as np, pandas as pd
import banc_or as B
with contextlib.redirect_stdout(io.StringIO()):
    import banc_repli_plus as P
P.TICKERS["TAUX"] = "^IRX"
JOURS = ["lun", "mar", "mer", "jeu", "ven"]
TAUX = (P.ohlc("TAUX").close / 100).sort_index()
rng = np.random.default_rng(17)


# ---------------------------------------------------------------- outils
def taux(dates):
    u = TAUX.reindex(TAUX.index.union(pd.DatetimeIndex(dates).normalize())).ffill()
    return u.reindex(pd.DatetimeIndex(dates).normalize()).fillna(0.02).values


def portage(dates, nuits, sens, fam):
    """Cout de portage (fraction) pour tenir `nuits` nuits calendaires dans le sens `sens`."""
    r = taux(dates)
    if fam == "or":
        a = np.maximum(r - 0.004, 0.01) if sens > 0 else 0.007 - r
    elif fam == "dax":
        a = r + 0.015 if sens > 0 else 0.041 - r
    else:
        a = r + 0.03 if sens > 0 else 0.026 - r
    return a * np.asarray(nuits) / 360


def tstat(X):
    X = np.asarray(X, float)
    s = X.std(0, ddof=1)
    return np.where(s > 0, X.mean(0) / np.where(s > 0, s, 1) * np.sqrt(len(X)), 0.0)


def creux(x):
    c = np.cumsum(x)
    return (c - np.maximum.accumulate(np.r_[0, c])[1:]).min()


def comptes(n, nb=2000, b=5.0):
    """Bootstrap stationnaire : nombre de fois ou chaque jour est tire, (nb, n)."""
    neuf = rng.random((nb, n)) < 1 / b; neuf[:, 0] = True
    pos = np.where(neuf, np.arange(n), 0); pos = np.maximum.accumulate(pos, axis=1)
    dep = np.where(neuf, rng.integers(n, size=(nb, n)), 0)
    dep = np.take_along_axis(dep, pos, axis=1)
    ii = (dep + np.arange(n) - pos) % n
    flat = (ii + np.arange(nb)[:, None] * n).ravel()
    return np.bincount(flat, minlength=nb * n).reshape(nb, n).astype(np.float32)


def rc(C):
    """Reality check de White contre zero : p du meilleur reglage, nom du meilleur."""
    M = np.nan_to_num(C.values.astype(np.float32)); n = len(M)
    mu = M.mean(0); V = np.sqrt(n) * mu.max()
    Vb = np.concatenate([np.sqrt(n) * ((comptes(n, 250) @ M) / n - mu).max(1) for _ in range(8)])
    return (Vb >= V).mean(), C.columns[int(mu.argmax())]


def bonf(N):
    return NormalDist().inv_cdf(1 - 0.05 / N)


def wf(C, T, R, per, L):
    """Walk-forward glissant. C gains/jour, T trades/jour, R reference/jour (memes colonnes), per = periode du jour."""
    Pu = np.sort(per.unique()); o, ref, tr, ch, gp = [], [], 0, [], []
    for i in range(L, len(Pu)):
        app, te = per.isin(Pu[i - L:i]).values, (per == Pu[i]).values
        k = C.columns[int(np.argmax(tstat(C.values[app])))]
        o.append(C[k].values[te]); ref.append(R[k].values[te]); tr += T[k].values[te].sum(); ch.append(k)
        gp.append(C[k].values[te].sum() > 0)
    o, ref = np.concatenate(o), np.concatenate(ref)
    fq = pd.Series(ch).value_counts()
    return dict(tot=o.sum(), t=float(tstat(o[:, None])[0]), tr_=float(tstat((o - ref)[:, None])[0]), gp=np.mean(gp), cr=creux(o), tr=tr,
                bp=o.sum() / max(tr, 1) * 1e4, ref=ref.sum(), ch="%s %d/%d" % (fq.index[0], fq.iloc[0], len(ch)),
                p0=Pu[L], p1=Pu[-1])


def verdict(r, p):
    if r["tot"] > 0 and (r["t"] >= 2.6 or p < 0.05):
        return "TIENT"
    if r["tot"] > 0 and (r["t"] >= 1.5 or p < 0.15):
        return "presque"
    return "non"


def ligne(nom, C, T, R, per, L):
    r = wf(C, T, R, per, L); p, _ = rc(C); pr, _ = rc(C - R)
    print("%-8s %-22s %+6.1f %+5.1f %3.0f %+6.1f %5d %+6.1f %+6.1f %+5.1f %5.3f %5.3f %s" % (
        nom, r["ch"][:22], 100 * r["tot"], r["t"], 100 * r["gp"], 100 * r["cr"], r["tr"], r["bp"], 100 * r["ref"], r["tr_"],
        p, pr, verdict(r, p)))
    return r


def global_rc(titre, S):
    C = pd.concat([s[0] for s in S], axis=1).fillna(0.0); R = pd.concat([s[1] for s in S], axis=1).fillna(0.0)
    p, k = rc(C); pr, kr = rc(C - R)
    print("%s | N = %d ; RC global contre 0 : %s p = %.3f ; contre ref : %s p = %.3f ; Bonferroni t >= %.2f (ligne : %.2f)" % (
        titre, C.shape[1], k, p, kr, pr, bonf(C.shape[1]), bonf(S[0][0].shape[1])))


ENTETE = "%-8s %-22s %6s %5s %3s %6s %5s %6s %6s %5s %5s %5s %s" % (
    "marche", "reglage le plus choisi", "HE %", "t", "%p+", "creux%", "trad", "bp/tr", "ref %", "t-ref", "pRC0", "pRCr", "verdict")


# ---------------------------------------------------------------- donnees du courtier
def charge(*ids):
    d = pd.concat([B.charge(i)[0] for i in ids]).sort_index()
    d = d[~d.index.duplicated()]
    ny = (d.index - pd.Timedelta(hours=7)).tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT")
    ok = ~ny.isna(); d = d[ok]; ny = ny[ok]
    d["pa"] = ny.tz_convert("Europe/Paris").tz_localize(None)
    d["ny"] = ny.tz_localize(None)
    return d


def med_sp(d, clk, hh, mm):
    """Spread median (fraction du prix) de la bougie qui commence a hh:mm (horloge clk)."""
    x = d[(d[clk].dt.hour == hh) & (d[clk].dt.minute == mm)]
    return float((x.sp / x.cloture).median())


# ---------------------------------------------------------------- (a) et (b) : journalier
def regle_jour(c, masques, fam, cout_achat, cout_vente):
    """c : clotures ; masques : nom -> booleen (tenu de la cloture J-1 a la cloture J)."""
    c = c.dropna()
    ret = c.pct_change().values; nuits = np.r_[1, np.diff(c.index.values).astype("timedelta64[D]").astype(int)]
    C, T, R = {}, {}, {}
    for nom, (m, s) in masques.items():
        m = np.asarray(m, bool) & ~np.isnan(ret)
        ent = m & ~np.r_[False, m[:-1]]
        g = np.where(m, s * np.nan_to_num(ret) - portage(c.index, nuits, s, fam), 0.0)
        g -= ent * (cout_achat if s > 0 else cout_vente)
        C[nom], T[nom], R[nom] = g, ent.astype(int), s * np.nan_to_num(ret) * m.mean()
    f = lambda z: pd.DataFrame(z, index=c.index)
    return f(C), f(T), f(R)


def masques_semaine(idx):
    return {"%s %s" % ("achat" if s > 0 else "vente", JOURS[j]): (idx.dayofweek == j, s) for j in range(5) for s in (1, -1)}


def masques_mois(idx):
    mo = pd.Series(idx.to_period("M"), index=idx)
    k = mo.groupby(mo).cumcount().values + 1                    # rang depuis le debut du mois
    j = mo.groupby(mo).cumcount(ascending=False).values + 1     # rang depuis la fin du mois
    j = np.where(mo.values == mo.values[-1], 99, j)             # dernier mois incomplet
    W = {"fin3": j <= 3, "deb3": k <= 3, "fin1+deb3": (j == 1) | (k <= 3), "fin3+deb3": (j <= 3) | (k <= 3)}
    return {"%s %s" % (w, "achat" if s > 0 else "vente"): (m, s) for w, m in W.items() for s in (1, -1)}


# ---------------------------------------------------------------- (c) et (d) : fenetres intrajournalieres
def fenetre(d, clk, a, b, bar):
    """Une ligne par jour : ouverture et spread de la 1re bougie dans [a, b), cloture et spread de la derniere."""
    t = d[clk]; mn = t.dt.hour * 60 + t.dt.minute
    if a < b:
        m = (mn >= a) & (mn < b); cle = t.dt.normalize()
    else:                                                       # a cheval sur minuit (nuit)
        m = (mn >= a) | (mn < b); cle = (t + pd.Timedelta(minutes=1440 - a)).dt.normalize()
    x = d[m].assign(cle=cle[m], mn=mn[m])
    g = x.groupby("cle").agg(o=("ouverture", "first"), spo=("sp", "first"), c=("cloture", "last"),
                             spc=("sp", "last"), t0=(clk, "first"), t1=(clk, "last"))
    deb = g.index
    st = deb + pd.Timedelta(minutes=a) - (pd.Timedelta(days=1) if a > b else pd.Timedelta(0))
    fin = deb + pd.Timedelta(minutes=b)
    ok = (g.t0 - st <= bar) & (fin - g.t1 <= 2 * bar)
    if a > b:
        ok &= g.index.dayofweek.isin([1, 2, 3, 4])               # nuits de semaine seulement
    g = g[ok]; g.index.name = None
    return g


def gain(g, s, fam, nuits=0):
    if s > 0:
        r = (g.c - g.o - g.spo) / g.o
    else:
        r = (g.o - g.c - g.spc) / g.o
    return r - (portage(g.index, np.full(len(g), nuits), s, fam) if nuits else 0)


def jour_cl(d):
    c = d.groupby(d.pa.dt.normalize()).cloture.last()
    return c.pct_change().fillna(0)


def heures(d, fam, bar):
    W = {"L1": ("pa", 540, 600, 1), "Lm": ("pa", 540, 720, 3), "N1": ("ny", 570, 630, 1), "NS": ("ny", 570, 960, 6.5),
         "nuit": ("pa", 1320, 480, 10)}
    G = {w: fenetre(d, k, a, b, bar) for w, (k, a, b, _) in W.items()}
    asie = fenetre(d, "pa", 60, 540, bar)
    # Londres : 9 h Paris -> 9 h 30 New York (meme date)
    t = d.pa; mn = t.dt.hour * 60 + t.dt.minute; mny = d.ny.dt.hour * 60 + d.ny.dt.minute
    x = d[(mn >= 540) & (mny < 570) & (mny >= 120)]
    lon = x.groupby(x.pa.dt.normalize()).agg(o=("ouverture", "first"), c=("cloture", "last"))
    bh = jour_cl(d)
    C, T, R = {}, {}, {}
    for w, (_, _, _, h) in W.items():
        for s in (1, -1):
            k = "%s %s" % (w, "achat" if s > 0 else "vente")
            C[k] = gain(G[w], s, fam, 1 if w == "nuit" else 0); R[k] = s * bh * h / 24
    for w, prec, nm in (("L1", asie, "Asie"), ("Lm", asie, "Asie"), ("N1", lon, "Lond"), ("NS", lon, "Lond")):
        sg = np.sign(prec.c - prec.o).reindex(G[w].index).fillna(0)
        base = gain(G[w], 1, fam)
        for q, nq in ((1, "suivre"), (-1, "contrer")):
            sens = q * sg
            k = "%s %s %s" % (w, nq, nm)
            C[k] = np.where(sens > 0, base, np.where(sens < 0, gain(G[w], -1, fam), 0.0))
            C[k] = pd.Series(C[k], index=G[w].index); R[k] = base
    idx = bh.index
    C = pd.DataFrame(C).reindex(idx).fillna(0.0)
    T = (pd.DataFrame({k: v != 0 for k, v in C.items()})).astype(int)
    R = pd.DataFrame(R).reindex(idx).fillna(0.0)
    return C, T, R


def nuit_jour_mt5(d, fam):
    jour = fenetre(d, "ny", 570, 960, pd.Timedelta("5min"))
    mny = d.ny.dt.hour * 60 + d.ny.dt.minute
    cl = d[(mny >= 950) & (mny < 960)].groupby(d.ny.dt.normalize()).agg(c=("cloture", "last"), spc=("sp", "last"))
    op = d[(mny >= 570) & (mny < 575)].groupby(d.ny.dt.normalize()).agg(o=("ouverture", "first"), spo=("sp", "first"))
    cl.index.name = op.index.name = None
    z = op.join(cl.shift(1).rename(columns={"c": "cp", "spc": "spp"}), how="inner")
    prev = pd.Series(cl.index, index=cl.index).shift(1).reindex(z.index)
    z["n"] = (z.index - prev).dt.days
    z = z[(z.n >= 1) & (z.n <= 4)].dropna()
    nl = (z.o - z.cp - z.spp) / z.cp - portage(z.index, z.n, 1, fam)
    nv = (z.cp - z.o - z.spo) / z.cp - portage(z.index, z.n, -1, fam)
    return {"nuit": (nl, nv, z.n), "jour": (gain(jour, 1, fam), gain(jour, -1, fam), None)}


def nuit_jour_cfg(seg, idx, bh):
    C, R = {}, {}
    for sg, (gl, gv, _) in seg.items():
        h = 17.5 if sg == "nuit" else 6.5
        for s, g in ((1, gl), (-1, gv)):
            for lun in (False, True):
                k = "%s %s%s" % (sg, "achat" if s > 0 else "vente", " sauf lun" if lun else "")
                g2 = g[g.index.dayofweek != 0] if lun else g
                C[k] = g2; R[k] = s * bh * h / 24
    C = pd.DataFrame(C).reindex(idx).fillna(0.0)
    return C, (C != 0).astype(int), pd.DataFrame(R).reindex(idx).fillna(0.0)


# ---------------------------------------------------------------- programme
if __name__ == "__main__":
    MT = {"or": charge("xau_m5_2025a", "xau_m5_90k"), "nas": charge("nas_m5_2025a", "nas_m5_90k"),
          "sp": charge("sp_m5_90k"), "dj": charge("dj_m5_90k")}
    ger = charge("ger_m1_90k")
    # fuseau : bougie de plus gros volume entre 13 h et 20 h serveur, en heure de New York
    x = MT["nas"][(MT["nas"].index.hour >= 13) & (MT["nas"].index.hour < 20)]
    v = x.groupby(x.index.normalize()).volume_ticks.idxmax()
    nyv = x.loc[v.values, "ny"]; pav = x.loc[v.values, "pa"]
    dec = (pd.DatetimeIndex(v.values) - pd.DatetimeIndex(pav.values)).total_seconds() / 3600
    print("Fuseau : serveur = New York + 7 h. Pic de volume Nasdaq a 9 h 30 NY sur %.0f %% des jours ; serveur - Paris = 1 h"
          " (%d j) ou 2 h (%d j, semaines de decalage US/Europe) : gere." % (
              100 * ((nyv.dt.hour == 9) & (nyv.dt.minute == 30)).mean(), (dec == 1).sum(), (dec == 2).sum()))
    # spreads medians (fraction) : cloture et ouverture au comptant, dernier bougie du jour serveur
    SPC = {"SP500": med_sp(MT["sp"], "ny", 15, 55), "NASDAQ": med_sp(MT["nas"], "ny", 15, 55),
           "DOW": med_sp(MT["dj"], "ny", 15, 55), "DAX": med_sp(ger, "pa", 17, 29), "OR": float((MT["or"].sp / MT["or"].cloture).median())}
    SPO = {"SP500": med_sp(MT["sp"], "ny", 9, 30), "NASDAQ": med_sp(MT["nas"], "ny", 9, 30),
           "DOW": med_sp(MT["dj"], "ny", 9, 30), "DAX": med_sp(ger, "pa", 9, 0), "OR": SPC["OR"]}
    dern = lambda d: float((d.groupby(d.index.normalize()).last().pipe(lambda z: z.sp / z.cloture)).median())
    SPD = {"xau_d1_5k": dern(MT["or"]), "nas_d1_5k": dern(MT["nas"]), "sp_d1_5k": dern(MT["sp"]),
           "dj_d1_5k": dern(MT["dj"]), "ger_d1_5k": dern(ger)}
    print("Spread median bp, cloture/ouverture au comptant : " + ", ".join("%s %.1f/%.1f" % (k, 1e4 * SPC[k], 1e4 * SPO[k]) for k in SPC)
          + " ; fin de jour serveur : " + ", ".join("%s %.1f" % (k[:3], 1e4 * v) for k, v in SPD.items()))
    FAM = {"OR": "or", "DAX": "dax", "SP500": "ind", "NASDAQ": "ind", "DOW": "ind"}
    Y = {k: P.ohlc(k) for k in ("OR", "NASDAQ", "SP500", "DOW", "DAX")}
    yr = lambda C: pd.Series(C.index.year, index=C.index)
    print(ENTETE)

    # (a) jour de la semaine, Yahoo
    S = []
    for k, d in Y.items():
        C, T, R = regle_jour(d.close, masques_semaine(d.index), FAM[k], SPC[k], SPC[k])
        r = ligne(k[:8], C, T, R, yr(C), 3); S.append((C.add_prefix(k[:3] + " "), R.add_prefix(k[:3] + " ")))
    global_rc("(a) jour de semaine Yahoo %d-%d, tests %d-%d" % (Y["OR"].index[0].year, 2026, r["p0"], r["p1"]), S)
    # (a) jour de la semaine, bougies jour du courtier
    S = []
    for f, fam in (("xau_d1_5k", "or"), ("nas_d1_5k", "ind"), ("sp_d1_5k", "ind"), ("dj_d1_5k", "ind"), ("ger_d1_5k", "dax")):
        d = B.charge(f)[0]; d = d[d.index.dayofweek < 5]
        C, T, R = regle_jour(d.cloture, masques_semaine(d.index), fam, SPD[f], SPD[f])
        r = ligne(f[:3] + " d1", C, T, R, yr(C), 3); S.append((C.add_prefix(f[:3] + " "), R.add_prefix(f[:3] + " ")))
    global_rc("(a) jour de semaine courtier D1 2018/2020-2026 (tests des %d)" % r["p0"], S)
    # (b) tournant du mois, Yahoo
    S = []
    for k, d in Y.items():
        C, T, R = regle_jour(d.close, masques_mois(d.index), FAM[k], SPC[k], SPC[k])
        r = ligne(k[:8], C, T, R, yr(C), 3); S.append((C.add_prefix(k[:3] + " "), R.add_prefix(k[:3] + " ")))
    global_rc("(b) tournant du mois Yahoo, tests %d-%d" % (r["p0"], r["p1"]), S)
    # (c) fenetres d'heures, courtier
    S = []
    mo = lambda C: pd.Series(C.index.to_period("M"), index=C.index)
    for nom, d, fam, bar in (("or M5", MT["or"], "or", "5min"), ("or M15", charge("xau_m15_50k"), "or", "15min"),
                             ("nas M5", MT["nas"], "ind", "5min"), ("sp M5", MT["sp"], "ind", "5min"),
                             ("dj M5", MT["dj"], "ind", "5min")):
        C, T, R = heures(d, fam, pd.Timedelta(bar))
        r = ligne(nom, C, T, R, mo(C), 6); S.append((C.add_prefix(nom + " "), R.add_prefix(nom + " ")))
        if nom == "or M5":
            p5 = "%s->%s" % (C.index[0].date(), C.index[-1].date())
    global_rc("(c) heures courtier (or/nas M5 %s, sp/dj M5 des 2025-08, or M15 des 2024-10 ; tests : 6 mois apres le debut -> %s)" % (p5, r["p1"]), S)
    # (d) nuit contre jour, Yahoo
    S = []
    for k in ("NASDAQ", "SP500", "DOW", "DAX"):
        d = Y[k]; fig = (d.open == d.close.shift()).groupby(d.index.year).transform("mean") > 0.05
        cp = d.close.shift(); n = pd.Series(d.index, index=d.index).diff().dt.days
        ok = ~fig & n.between(1, 4)
        nl = ((d.open - cp) / cp - SPC[k] - portage(d.index, n.fillna(1), 1, FAM[k]))[ok]
        nv = ((cp - d.open) / cp - SPO[k] - portage(d.index, n.fillna(1), -1, FAM[k]))[ok]
        jl = ((d.close - d.open) / d.open - SPO[k])[~fig]; jv = ((d.open - d.close) / d.open - SPC[k])[~fig]
        C, T, R = nuit_jour_cfg({"nuit": (nl, nv, None), "jour": (jl, jv, None)}, d.index, d.close.pct_change().fillna(0))
        r = ligne(k[:8] + " j", C, T, R, yr(C), 3); S.append((C.add_prefix(k[:3] + " "), R.add_prefix(k[:3] + " ")))
    global_rc("(d) nuit/jour Yahoo (annees a ouvertures figees exclues : S&P 2000-07, 2011-13 ; Dow 2005-07, 2013, 2015)", S)
    # (d) nuit contre jour, courtier M5
    S = []
    for nom in ("nas", "sp", "dj"):
        d = MT[nom]; bh = jour_cl(d)
        C, T, R = nuit_jour_cfg(nuit_jour_mt5(d, "ind"), bh.index, bh)
        r = ligne(nom + " M5", C, T, R, mo(C), 6); S.append((C.add_prefix(nom + " "), R.add_prefix(nom + " ")))
    global_rc("(d) nuit/jour courtier M5 (tests nas 2025-12, sp/dj %s -> %s)" % (r["p0"], r["p1"]), S)
