"""Banc GP : regle « renforts gagnants » proposee par GPT Astra (PRIORITES 23/11 ; compte DEMO / labo, aucun ordre).
Regle FIGEE le 23/11 (meme texte que le robot mt5/robot/gpt_pyramide.py), appliquee telle quelle, aucun reglage :
  seance = jour serveur, bougies D1 du courtier (xau_d1_5k) ; R = 0,25 x moyenne (haut - bas) des 14 dernieres seances
  FERMEES ; sens = cloture de la veille contre la moyenne simple de ses 50 dernieres clotures (au-dessus achat, en
  dessous vente) ; filtre = veille tres calme (amplitude < 0,6 x moyenne des 14 amplitudes precedentes) OU inside day ;
  entree = cloture de la bougie M15 de 08:00 serveur (achat cloture + spread, vente cloture), un panier au plus par
  seance et un seul panier ouvert a la fois (comme le robot) ; volume initial V ; stop initial 1 R contre la 1re entree ;
  renforts 0,5 V a +1 R puis +1,5 R (variante « 3R » : 3e a +2 R), un seuil a la fois comme le robot : une cloture M15
  au-dela du seuil (gain = sens x (cloture - 1re entree)) arme le renfort, ajoute a l'ouverture de la bougie suivante si
  elle est encore au-dela (achat ouverture + spread) ; sinon rien et le seuil peut se re-armer plus tard ;
  stop : a la 1re cloture >= +1 R -> prix d'entree moyen des positions ouvertes ; ensuite max(stop, meilleure cloture
  - 1,5 R) (symetrique en vente), jamais en recul.
Sorties : A laisser courir (stop seul ; version demo) ; B fermer 50 % du volume a +2 R (ordre limite au prix e0 + 2 R),
  plus d'ajout ensuite ; C 3e renfort a +2 R puis fermer 25 % a +3 R ; D tout fermer a la cloture de la derniere bougie
  de la seance (23:45). Variantes (N = 6, pas d'optimisation) : A, A+3R, B, C, D, D+3R.
Execution : ordre PESSIMISTE dans une bougie : ouverture (renfort arme) -> stop (avec le stop d'avant la bougie ; achat
  touche si bas <= stop, vente si haut + spread >= stop ; trou d'ouverture au-dela du stop : sortie a l'ouverture) ->
  objectifs partiels B/C -> cloture (meilleure cloture, stop, armement). Spread reel de la bougie. Swaps estimes :
  6 %/an du notionnel (volume ouvert x prix) par nuit calendaire, achat ET vente (debites a chaque changement de jour).
  1 R = perte de V au stop initial (gain d'un panier en R, renforts compris, swaps compris).
Jeux : (1) or M15 du courtier xau_m15_50k (30/09/2024 -> 11/11/2026, jeu principal) ; (2) controle : or M5 18 mois
  (xau_m5_2025a + xau_m5_90k) regroupe en M15 ; (3) or H1 08/2022 -> 11/2026 (approximation : entree a l'OUVERTURE de la
  bougie H1 de 08:00, renforts / stops sur bougies H1, meme ordre pessimiste ; ecart avec M15 donne sur la periode
  commune) et ses moities (paniers ouverts avant / a partir du 01/10/2024).
References sur les memes mois (courbes journalieres marquees, en R propres) : bt_or (BR.simule = banc_bt_plus 1-1-1/3/
  tjrs), bt_or_plus (banc_bt_plus 1-2-3/5/tjrs), « toujours acheteur + pyramide » (mecanique bt_or, toujours achat,
  3 positions, comme banc_decompose_bt e3). H1 : reglage H1 des bancs (EMA 48, heures BJ.H_H1) ; M15 : bt_or sur les
  bougies M15 (EMA 192 = 2 jours, heures arrondies au quart d'heure, 03:05 -> 03:00) ; M5 : bt_or natif M5. Les
  references ne paient pas de swap (comme dans leurs bancs).
A RISQUE EGAL : facteur = pire baisse journaliere de bt_or / pire baisse de la variante, sur la meme fenetre ; on compare
  les totaux ainsi mis a l'echelle (meme chose pour bt_or_plus et achat+pyramide).
Mesures par jeu et moitie : paniers, % gagnants, R moyen, total R, pire baisse (courbe journaliere marquee), mois
  positifs, gain par semaine au risque de 12 % du capital par panier (compose ; et simple), pire baisse en % a 12 %.
Fenetre de GPT refaite EXACTEMENT : simulation neuve du 08/06/2026 au 25/09/2026 (16 semaines), puis 28/09 -> 04/12/2026
  (10 semaines ; donnees jusqu'au 11/11 seulement -> semaines disponibles), et 08/06 -> fin des donnees.
Walk-forward : rien a regler ; resultat par trimestre et nombre de trimestres positifs. Essais multiples : N = 6,
  reality check de White (BR.white, bootstrap stationnaire, 2000 tirages) des 6 courbes journalieres contre zero (H1 et M15).
Monte-Carlo de ruine (version A) : bootstrap stationnaire de la suite des paniers (blocs moyens 10), 10 000 parcours,
  12 et 24 mois (paniers par mois du jeu), compte cent 100 et 500 EUR (1 unite = 0,01 once, unites = max(1, plancher(
  risque x compte / risque d'une unite)), comme banc_pari_tendance), ruine = sous 20 % du depart (on s'arrete) ;
  risque 12 %, 3 %, 2 % par panier ; scenarios mesure / prudent (avantage / 2) / nul ; jeux M15 et H1.
  Mesures : chance de ruine, de finir au moins au double, valeur finale mediane, pire baisse mediane.
VERDICT FIXE D'AVANCE (sur la version A, celle de la demo) : TIENT = R moyen > 0 sur les deux moities H1 ET sur M15,
  bat bt_or a risque egal sur les deux moities H1, et p de White (6 variantes, H1) < 0,10 ; PRESQUE = R moyen positif
  partout mais ne bat pas bt_or ou p >= 0,10 ; sinon NE TIENT PAS. (La regle va sur la demo pour les donnees quel que
  soit le verdict.)
RESULTAT (execution du 23/11/2026, 4 s) : PRESQUE. Version A : R moyen +0,28 (H1 2022-08 -> 2024-09, 122 paniers),
  +0,51 (H1 2024-10 -> 2026-11, 97), +0,50 (M15, 97 paniers, 29 % gagnants, +48,5 R) ; a risque egal, bat bt_or sur la
  1re moitie H1 (+49 R contre +0,6) mais pas sur la 2de (+68 contre +154) ni sur M15 (+72 contre +148) ; White H1
  p = 0,029. Ecart H1/M15 sur la periode commune faible (R/panier +0,51 contre +0,50). Fenetre de GPT refaite
  (08/06-25/09/2026) : 9 paniers, -3,9 R, -3,25 %/semaine a 12 % (GPT : +3,21 %) ; suite 28/09-11/11 : 7 paniers
  perdants, -6,7 R. Au risque de 12 % : pire baisse -83 % (M15) a -99,5 % (H1), ruine en 24 mois 29-44 % (mesure) ;
  a 2-3 % : ruine ~0 % mesure, 0-3 % prudent.
Ecrit donnees/gpt_pyramide.csv. Usage : python3 banc_gpt_pyramide.py
"""
import os, time, contextlib, io, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_bt_regulier as BR
    import banc_jumeau as BJ
    import banc_bt_plus as BP

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
COUPE = pd.Timestamp("2024-10-01")
SWAP = 0.06 / 365
VARIANTES = {"A": ("A", False), "A+3R": ("A", True), "B": ("B", False), "C": ("C", True), "D": ("D", False),
             "D+3R": ("D", True)}
H_M15 = {(3, 0), (8, 0), (8, 30), (12, 0), (15, 45), (16, 0), (16, 30)}
NPAR, BLOC = 10000, 10.0
PLANCHER, EURUSD, PX = 0.20, 1.16, 4000.0
rng = np.random.default_rng(2311)


# ---------------------------------------------------------------- donnees
def charge_m15_depuis_m5():
    a5, b5 = BR.charge("xau_m5_2025a"), BR.charge("xau_m5_90k")
    d5 = pd.concat([a5, b5[b5.heure > a5.heure.iloc[-1]]], ignore_index=True)
    q = d5.heure // 900
    d = d5.groupby(q).agg(ouverture=("ouverture", "first"), haut=("haut", "max"), bas=("bas", "min"),
                          cloture=("cloture", "last"), sp=("sp", "mean")).reset_index()
    d["heure"] = d.pop("heure") * 900
    return d5, d


def params_d1():
    d1 = BR.charge("xau_d1_5k")
    amp = d1.haut - d1.bas
    adr = amp.rolling(14).mean()
    calme = amp < 0.6 * adr.shift(1)
    inside = (d1.haut <= d1.haut.shift(1)) & (d1.bas >= d1.bas.shift(1))
    sma = d1.cloture.rolling(50).mean()
    sens = np.where(d1.cloture > sma, 1, np.where(d1.cloture < sma, -1, 0))
    ok = (calme | inside) & adr.notna() & sma.notna() & adr.shift(1).notna() & (sens != 0)
    return d1.heure.values, np.where(ok, sens, 0), (0.25 * adr).values, d1


# ---------------------------------------------------------------- la regle
def simule_regle(d, D1, sortie="A", trois=False, entree_ouverture=False, journal=False):
    """Rend (paniers DataFrame, courbe journaliere marquee en R : Series, marque du panier ouvert par jour : Series)."""
    hd, sensd, Rd, _ = D1
    o, hi, lo, c, sp, t = (d[x].values for x in ("ouverture", "haut", "bas", "cloture", "sp", "heure"))
    n = len(c)
    jour = t // 86400
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    fin_j = np.r_[jour[1:] != jour[:-1], True]
    k1 = np.searchsorted(hd, jour * 86400, "left") - 1
    seuils = [1.0, 1.5] + ([2.0] if trois else [])
    P, EQ, MK, JO = [], [], [], []
    acc = 0.0
    p = None
    fait = -1

    def valeur(i, prix_bid):       # gain latent du panier ouvert en R au prix de sortie
        x = prix_bid if p["s"] > 0 else prix_bid + sp[i]
        return sum(w * p["s"] * (x - e) for e, w in p["pos"]) / p["R"] + p["real"] - p["swap"]

    def ferme(i, px_sortie, raison):
        nonlocal acc, p
        g = sum(w * p["s"] * (px_sortie - e) for e, w in p["pos"]) / p["R"] + p["real"] - p["swap"]
        acc += g
        P.append(dict(t0=t[p["i"]], t1=t[i], s=p["s"], R=p["R"], e0=p["e0"], px1=px_sortie, g=g, swap=p["swap"],
                      renforts=p["nren"], vol_max=p["vmax"], raison=raison, rrel=p["R"] / p["e0"],
                      ev=" | ".join(p["ev"]) if journal else ""))
        p = None

    def entre(i, prix_bid):
        nonlocal p, fait
        fait = jour[i]
        k = k1[i]
        if k < 0 or sensd[k] == 0 or not Rd[k] > 0:
            return
        s, R = int(sensd[k]), Rd[k]
        e = prix_bid + sp[i] if s > 0 else prix_bid
        p = dict(i=i, s=s, R=R, e0=e, pos=[[e, 1.0]], stop=e - s * R, best=e, be=False, nren=0, att=None, real=0.0,
                 swap=0.0, vmax=1.0, partB=False, partC=False, ev=[])
        if journal:
            p["ev"].append("%s entree %s %.2f R=%.2f stop %.2f" % (pd.to_datetime(t[i], unit="s"), "achat" if s > 0
                                                                     else "vente", e, R, e - s * R))

    for i in range(n):
        if p is not None and i > 0 and jour[i] != jour[i - 1]:
            p["swap"] += sum(w for _, w in p["pos"]) * c[i - 1] * SWAP * (jour[i] - jour[i - 1]) / p["R"]
        libre = p is None
        if libre and entree_ouverture and hh[i] == 8 and mm[i] == 0 and fait != jour[i]:
            entre(i, o[i])
        if p is not None:
            s, R = p["s"], p["R"]
            # (a) renfort arme a la cloture precedente
            if p["att"] is not None:
                if s * (o[i] - (p["e0"] + s * p["att"] * R)) >= 0:
                    e = o[i] + sp[i] if s > 0 else o[i]
                    p["pos"].append([e, 0.5])
                    p["nren"] += 1
                    p["vmax"] = max(p["vmax"], sum(w for _, w in p["pos"]))
                    if journal:
                        p["ev"].append("%s renfort %d a %.2f" % (pd.to_datetime(t[i], unit="s"), p["nren"], e))
                p["att"] = None
            # (b) stop (pessimiste : avant tout gain de la bougie)
            if s > 0 and lo[i] <= p["stop"]:
                ferme(i, min(o[i], p["stop"]), "stop")
            elif s < 0 and hi[i] + sp[i] >= p["stop"]:
                ferme(i, max(o[i] + sp[i], p["stop"]), "stop")
            if p is not None:
                # (c) objectifs partiels (ordre limite)
                for nom, k_r, frac in (("B", 2.0, 0.5), ("C", 3.0, 0.25)):
                    drap = "part" + nom
                    if sortie == nom and not p[drap]:
                        niv = p["e0"] + s * k_r * R
                        if (hi[i] >= niv) if s > 0 else (lo[i] + sp[i] <= niv):
                            p["real"] += sum(frac * w * s * (niv - e) for e, w in p["pos"]) / R
                            for q in p["pos"]:
                                q[1] *= 1 - frac
                            p[drap] = True
                            if journal:
                                p["ev"].append("%s ferme %d %% a %.2f" % (pd.to_datetime(t[i], unit="s"), 100 * frac, niv))
                # (d) cloture : meilleure cloture, stop, armement
                p["best"] = max(p["best"], c[i]) if s > 0 else min(p["best"], c[i])
                gr = s * (c[i] - p["e0"]) / R
                avant = p["stop"]
                if gr >= 1.0 and not p["be"]:
                    W = sum(w for _, w in p["pos"])
                    moy = sum(e * w for e, w in p["pos"]) / W
                    p["stop"] = max(p["stop"], moy) if s > 0 else min(p["stop"], moy)
                    p["be"] = True
                if p["be"]:
                    nv = p["best"] - s * 1.5 * R
                    p["stop"] = max(p["stop"], nv) if s > 0 else min(p["stop"], nv)
                if journal and p["stop"] != avant:
                    p["ev"].append("%s stop %.2f" % (pd.to_datetime(t[i] + 900, unit="s"), p["stop"]))
                if not (sortie == "B" and p["partB"]) and p["nren"] < len(seuils) and gr >= seuils[p["nren"]]:
                    p["att"] = seuils[p["nren"]]
                # (e) sortie de fin de seance
                if sortie == "D" and fin_j[i]:
                    ferme(i, c[i] if s > 0 else c[i] + sp[i], "fin de seance")
        if libre and not entree_ouverture and hh[i] == 8 and mm[i] == 0 and fait != jour[i]:
            entre(i, c[i])
        if fin_j[i]:
            mk = valeur(i, c[i]) if p is not None else 0.0
            EQ.append(acc + mk); MK.append(mk); JO.append(jour[i])
    P = pd.DataFrame(P)
    dates = pd.to_datetime(np.array(JO) * 86400, unit="s")
    return P, pd.Series(EQ, dates), pd.Series(MK, dates)


# ---------------------------------------------------------------- reference « toujours acheteur + pyramide »
def simule_achat(d, span=576, heures=BR.H_M5, debut=600):
    """Copie de BR.simule, sens toujours achat, 3 positions ; rend paniers et courbe journaliere marquee (R)."""
    c, hi, lo, sp, t = (d[x].values for x in ("cloture", "haut", "bas", "sp", "heure"))
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    fin_j = np.r_[jour[1:] != jour[:-1], True]
    p, acc, G, EQ, JO = None, 0.0, [], [], []
    for i in range(debut, len(c)):
        if p is not None:
            niveau = p["meilleur"] - p["stop"]
            if lo[i] <= niveau:
                g = sum(niveau - e for e in p["e"]) / p["stop"]
                acc += g; G.append(g); p = None
            else:
                p["meilleur"] = max(p["meilleur"], hi[i])
                while len(p["e"]) < BR.MAXP and c[i] - p["prochain"] >= 0:
                    if c[i] - p["prochain"] <= 0.5 * p["pas"]:
                        p["e"].append(c[i] + sp[i])
                    p["prochain"] += p["pas"]
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0 and p is None:
            p = {"e": [c[i] + sp[i]], "meilleur": c[i], "stop": BR.STOP * atr[i], "pas": BR.PAS * atr[i],
                 "prochain": c[i] + BR.PAS * atr[i]}
        if fin_j[i]:
            mk = sum(c[i] - e for e in p["e"]) / p["stop"] if p is not None else 0.0
            EQ.append(acc + mk); JO.append(jour[i])
    return np.array(G), pd.Series(EQ, pd.to_datetime(np.array(JO) * 86400, unit="s"))


def references(d, kw):
    P, GR, GD, NP, ER, ED = BP.simule_plus(d, **kw)
    ga, ea = simule_achat(d, **kw)
    return {"bt_or": ER[BP.REF], "bt_or_plus": ER[BP.NOMV.index("1-2-3/5/tjrs")], "achat+pyr": ea}, len(P), GR[:, BP.REF].sum(), len(ga), ga.sum()


# ---------------------------------------------------------------- mesures
def incr(eq):
    return eq.diff().fillna(eq.iloc[0])


def creux(x):
    cs = np.r_[0, np.cumsum(x)]
    return (cs - np.maximum.accumulate(cs)).min()


def equite_pct(P, MK, f, deb=None, fin=None):
    """Capital compose (depart 1) au risque f par panier ; courbe journaliere marquee. P, MK : meme simulation."""
    jours = MK.index
    m = np.ones(len(jours), bool)
    if deb is not None:
        m &= (jours >= deb) & (jours <= fin)
    if len(P):
        sorti = pd.to_datetime(P.t1, unit="s").dt.floor("D").values
        o = np.argsort(sorti, kind="stable")
        gs, js = P.g.values[o], sorti[o]
    else:
        gs, js = np.array([]), np.array([], "datetime64[ns]")
    C, E, k = 1.0, [], 0
    for jj, mk, ok in zip(jours.values, MK.values, m):
        while k < len(js) and js[k] <= jj:
            if deb is None or (js[k] >= np.datetime64(deb) and js[k] <= np.datetime64(fin)):
                C *= 1 + f * gs[k]
            k += 1
        if ok:
            E.append(C * (1 + f * mk))
    E = np.array(E)
    dd = (E / np.maximum.accumulate(np.r_[1.0, E])[1:] - 1).min() if len(E) else 0.0
    return E, dd


def stats(nom, jeu, P, EQ, MK, deb, fin, refs=None):
    """deb/fin : Timestamps (jours). Paniers OUVERTS dans [deb, fin] ; courbe sur les jours de [deb, fin]."""
    t0 = pd.to_datetime(P.t0, unit="s")
    Q = P[(t0 >= deb) & (t0 < fin + pd.Timedelta(days=1))]
    x = incr(EQ); x = x[(x.index >= deb) & (x.index <= fin)]
    mo = x.groupby(x.index.to_period("M")).sum()
    sem = max((fin - deb).days / 7, 1e-9)
    E, dd = equite_pct(Q, MK, 0.12, deb, fin) if len(Q) else (np.array([1.0]), 0.0)
    cr = creux(x.values)
    r = dict(jeu=jeu, variante=nom, debut=deb.date(), fin=fin.date(), paniers=len(Q), pct_gagnants=100 * (Q.g > 0).mean() if len(Q) else np.nan,
             R_panier=Q.g.mean() if len(Q) else np.nan, swap_panier=Q.swap.mean() if len(Q) else np.nan, total_R=Q.g.sum(),
             courbe_R=x.sum(), pire_baisse_R=cr, mois_pos=int((mo > 0).sum()), mois=len(mo),
             sem12_compose=100 * (E[-1] ** (1 / sem) - 1) if E[-1] > 0 else -100.0,
             sem12_simple=100 * 0.12 * Q.g.sum() / sem, pire_baisse12_pct=100 * dd, renforts_moy=Q.renforts.mean() if len(Q) else np.nan)
    if refs is not None:
        X = pd.DataFrame({k: incr(v) for k, v in refs.items()})
        X = X[(X.index >= deb) & (X.index <= fin)]
        X = X.reindex(X.index.union(x.index)).fillna(0)
        xv = x.reindex(X.index).fillna(0)
        cb = creux(X["bt_or"].values)
        fv = cb / cr if cr < 0 else np.nan
        r.update(bt_or_R=X["bt_or"].sum(), bt_or_creux=cb, facteur=fv, variante_risque_egal=fv * xv.sum())
        for k in ("bt_or_plus", "achat+pyr"):
            ck = creux(X[k].values)
            r[k + "_risque_egal"] = (cb / ck) * X[k].sum() if ck < 0 else np.nan
        r["bat_bt_or"] = bool(r["variante_risque_egal"] > r["bt_or_R"])
    return r


# ---------------------------------------------------------------- Monte-Carlo
def tirages(n, m):
    out = np.empty((NPAR, m), int)
    for k in range(NPAR):
        neuf = rng.random(m) < 1 / BLOC; neuf[0] = True
        bl = np.cumsum(neuf) - 1; deb = np.flatnonzero(neuf)
        out[k] = (rng.integers(n, size=len(deb))[bl] + np.arange(m) - deb[bl]) % n
    return out


def parcours(R, rrel, II, f, dep_eur):
    dep = dep_eur * EURUSD
    E = np.full(NPAR, dep); pic = E.copy(); dd = np.zeros(NPAR); vivant = np.ones(NPAR, bool)
    for t in range(II.shape[1]):
        a = vivant
        if not a.any():
            break
        i = II[a, t]
        ru = rrel[i] * PX * 0.01
        u = np.maximum(1, np.floor(f * E[a] / ru))
        E[a] = np.maximum(E[a] + u * ru * R[i], 0.0)
        pic = np.maximum(pic, E); dd = np.minimum(dd, E / pic - 1)
        vivant = vivant & (E >= PLANCHER * dep)
    return E / dep, ~vivant, dd


# ---------------------------------------------------------------- programme
if __name__ == "__main__":
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200)
    D1 = params_d1()
    m15 = BR.charge("xau_m15_50k")
    d5, m15b = charge_m15_depuis_m5()
    dh = BR.charge("xau_h1_50k")
    dh = dh[dh.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
    # controle D1 : amplitudes du fichier D1 contre les jours reconstruits depuis M15
    j = m15.groupby(m15.heure // 86400).agg(h=("haut", "max"), l=("bas", "min"))
    d1 = D1[3].set_index(D1[3].heure // 86400)
    cm = j.index.intersection(d1.index)
    print("Controle D1 : %d seances communes M15/D1 ; ecart median |amplitude| %.2f $ (amplitude mediane %.1f $), "
          "seances a plus de 1 $ d'ecart : %d ; samedis D1 depuis 2022 : %d" % (
              len(cm), np.median(np.abs((j.h - j.l)[cm] - (d1.haut - d1.bas)[cm])), np.median((d1.haut - d1.bas)[cm]),
              int((np.abs((j.h - j.l)[cm] - (d1.haut - d1.bas)[cm]) > 1).sum()),
              int(((pd.to_datetime(D1[3].heure, unit="s").dt.dayofweek == 5) & (D1[3].heure >= 1659312000)).sum())))
    JEUX = {"M15": (m15, False, (m15, dict(span=192, heures=H_M15, debut=200))),
            "M5->M15": (m15b, False, (d5, {})),
            "H1": (dh, True, (dh, dict(span=48, heures=BJ.H_H1, debut=60)))}
    SIM, REFS, rows = {}, {}, []
    for jeu, (d, eo, (dref, kw)) in JEUX.items():
        t1 = time.time()
        for v, (so, tr) in VARIANTES.items():
            SIM[jeu, v] = simule_regle(d, D1, so, tr, entree_ouverture=eo, journal=(v == "A"))
        REFS[jeu], nb, gb, na, ga = references(dref, kw)
        print("%s : %s -> %s, simulation %.0f s ; bt_or %d paniers %+.1f R ; achat+pyramide %d paniers %+.1f R" % (
            jeu, pd.to_datetime(d.heure.iloc[0], unit="s").date(), pd.to_datetime(d.heure.iloc[-1], unit="s").date(),
            time.time() - t1, nb, gb, na, ga))
    # ---- tableau des variantes
    F = {}
    for jeu in JEUX:
        P0, E0, _ = SIM[jeu, "A"]
        deb = max(E0.index[0], REFS[jeu]["bt_or"].index[0]); fin = E0.index[-1]
        fen = [(jeu, deb, fin)]
        if jeu == "H1":
            fen += [("H1 2022-08->2024-09", deb, COUPE - pd.Timedelta(days=1)), ("H1 2024-10->2026-11", COUPE, fin)]
        for nomf, a, b in fen:
            for v in VARIANTES:
                P, EQ, MK = SIM[jeu, v]
                r = stats(v, nomf, P, EQ, MK, a, b, REFS[jeu])
                r["section"] = "variantes"; rows.append(r)
    T = pd.DataFrame([r for r in rows if r["section"] == "variantes"])
    cols = ["jeu", "variante", "paniers", "pct_gagnants", "R_panier", "swap_panier", "total_R", "pire_baisse_R", "mois_pos", "mois",
            "sem12_compose", "pire_baisse12_pct", "facteur", "variante_risque_egal", "bt_or_R", "bt_or_plus_risque_egal",
            "achat+pyr_risque_egal", "renforts_moy"]
    print("\n=== Variantes (R ; 1 R = perte de V au stop initial ; risque egal = mis a la pire baisse journaliere de bt_or)")
    print(T[cols].round(2).to_string(index=False))
    # ---- H1 contre M15 sur la periode commune
    print("\n=== Ecart H1 / M15 sur la periode commune (paniers ouverts du 01/10/2024 au 11/11/2026)")
    fin_c = SIM["M15", "A"][1].index[-1]
    for v in VARIANTES:
        a = stats(v, "M15", *SIM["M15", v], COUPE, fin_c); b = stats(v, "H1", *SIM["H1", v], COUPE, fin_c)
        print("  %-5s M15 %3d paniers R/pan %+.3f total %+6.1f | H1 %3d paniers R/pan %+.3f total %+6.1f" % (
            v, a["paniers"], a["R_panier"], a["total_R"], b["paniers"], b["R_panier"], b["total_R"]))
        rows.append(dict(section="ecart H1-M15", variante=v, jeu="M15", paniers=a["paniers"], R_panier=a["R_panier"], total_R=a["total_R"]))
        rows.append(dict(section="ecart H1-M15", variante=v, jeu="H1", paniers=b["paniers"], R_panier=b["R_panier"], total_R=b["total_R"]))
    # ---- fenetre de GPT refaite (simulation neuve dans la fenetre)
    print("\n=== Fenetre de GPT refaite (simulation neuve, risque 12 % par panier, compose ; GPT : +3,21 %/sem, 7 paniers ; "
          "puis -0,99 %/sem ; pire baisse -27,8 %)")
    FEN = [("08/06-25/09/2026 (16 sem.)", "2026-06-08", "2026-09-25"), ("28/09-04/12/2026 (10 sem.)", "2026-09-28", "2026-12-04"),
           ("08/06-04/12/2026 (26 sem.)", "2026-06-08", "2026-12-04")]
    for jeu in ("M15", "M5->M15"):
        d = JEUX[jeu][0]
        for nomf, a, b in FEN:
            a, b = pd.Timestamp(a), pd.Timestamp(b)
            dd_ = d[(d.heure >= a.timestamp()) & (d.heure < (b + pd.Timedelta(days=1)).timestamp())].reset_index(drop=True)
            for v in VARIANTES:
                P, EQ, MK = simule_regle(dd_, D1, *VARIANTES[v], journal=(v == "A"))
                fin_dispo = min(b, pd.to_datetime(dd_.heure.iloc[-1], unit="s").floor("D"))
                r = stats(v, jeu + " " + nomf, P, EQ, MK, a, fin_dispo)
                if fin_dispo < b:   # semaines disponibles seulement
                    sem = ((fin_dispo - a).days + 3) / 7
                    E, _ = equite_pct(P, MK, 0.12, a, fin_dispo)
                    r["sem12_compose"] = 100 * (E[-1] ** (1 / sem) - 1); r["sem12_simple"] = 100 * 0.12 * P.g.sum() / sem
                else:
                    sem = ((b - a).days + 3) / 7
                    E, _ = equite_pct(P, MK, 0.12, a, b)
                    r["sem12_compose"] = 100 * (E[-1] ** (1 / sem) - 1); r["sem12_simple"] = 100 * 0.12 * P.g.sum() / sem
                r["semaines"] = sem; r["capital_fin_x"] = E[-1]; r["section"] = "fenetre GPT"; rows.append(r)
                if v in ("A", "A+3R", "B", "C"):
                    print("  %-8s %-28s %-5s %4.1f sem. %2d paniers (%d gagnants) total %+5.2f R  %+6.2f %%/sem (simple %+6.2f)  "
                          "capital x%.3f  pire baisse %+5.1f %%" % (jeu, nomf, v, sem, r["paniers"], round(r["paniers"] * (r["pct_gagnants"] or 0) / 100),
                                                                 r["total_R"], r["sem12_compose"], r["sem12_simple"], E[-1], r["pire_baisse12_pct"]))
                if jeu == "M15" and v == "A" and nomf.startswith("08/06-25"):
                    print("    paniers A :")
                    for _, q in P.iterrows():
                        print("     %s -> %s %s R=%.2f$ e0 %.2f sortie %.2f renforts %d  %+.2f R" % (
                            pd.to_datetime(q.t0, unit="s"), pd.to_datetime(q.t1, unit="s"), "achat" if q.s > 0 else "vente",
                            q.R, q.e0, q.px1, q.renforts, q.g))
    # ---- walk-forward : par trimestre
    print("\n=== Par trimestre (courbe journaliere marquee, R) : trimestres positifs")
    for jeu in ("H1", "M15"):
        Q = pd.DataFrame({v: incr(SIM[jeu, v][1]) for v in VARIANTES})
        Q["bt_or"] = incr(REFS[jeu]["bt_or"]).reindex(Q.index).fillna(0)
        q = Q.groupby(Q.index.to_period("Q")).sum()
        print("  %s : " % jeu + " ; ".join("%s %d/%d" % (k, (q[k] > 0).sum(), len(q)) for k in q.columns))
        print(q.round(1).T.to_string())
        for per, ligne in q.iterrows():
            for k, x in ligne.items():
                rows.append(dict(section="trimestre", jeu=jeu, variante=k, debut=str(per), total_R=x))
    # ---- White
    pw = {}
    for jeu in ("H1", "M15"):
        Dm = np.column_stack([incr(SIM[jeu, v][1]).values for v in VARIANTES])
        kb, pw[jeu] = BR.white(Dm)
        print("White (N = 6, contre zero, jours) %s : meilleure %s, p = %.3f" % (jeu, list(VARIANTES)[kb], pw[jeu]))
        rows.append(dict(section="white", jeu=jeu, variante=list(VARIANTES)[kb], p_white=pw[jeu]))
    # ---- Monte-Carlo de ruine, version A
    print("\n=== Monte-Carlo de ruine, version A (10 000 parcours, blocs de paniers ; ruine = sous 20 % du depart)")
    MC = []
    for jeu in ("M15", "H1"):
        P = SIM[jeu, "A"][0].sort_values("t1")
        R0, rrel = P.g.values, P.rrel.values
        pm = len(P) / ((P.t1.max() - P.t0.min()) / 86400 / 30.44)
        mu = R0.mean()
        for mois in (12, 24):
            II = tirages(len(R0), int(round(pm * mois)))
            for sc, R in (("mesure", R0), ("prudent", R0 - mu / 2), ("nul", R0 - mu)):
                for f in (0.12, 0.03, 0.02):
                    for dep in (100.0, 500.0):
                        V, ru, dd = parcours(R, rrel, II, f, dep)
                        MC.append(dict(section="ruine", jeu=jeu, mois=mois, scenario=sc, risque=f, depart=dep,
                                       paniers_mois=pm, p_ruine=ru.mean(), p_double=(V >= 2).mean(), mediane_x=np.median(V),
                                       pire_baisse_med_pct=100 * np.median(dd)))
    M = pd.DataFrame(MC); rows += MC
    print(M.pivot_table(index=["jeu", "mois", "risque", "depart"], columns="scenario",
                        values=["p_ruine", "p_double", "mediane_x", "pire_baisse_med_pct"]).round(2).to_string())
    # ---- controles : deux paniers precis (M15, A)
    P = SIM["M15", "A"][0]
    print("\n=== Controles (M15, version A, en heure serveur)")
    for _, q in pd.concat([P[P.renforts == 2].nlargest(1, "g"), P[(P.renforts == 0) & (P.raison == "stop")].head(1)]).iterrows():
        print("  %+.2f R (swap %.3f R) : %s ; sortie %s a %.2f" % (q.g, q.swap, q.ev, pd.to_datetime(q.t1, unit="s"), q.px1))
    # ---- verdict
    V = T[T.variante == "A"].set_index("jeu")
    h1a, h1b = V.loc["H1 2022-08->2024-09"], V.loc["H1 2024-10->2026-11"]
    pos = h1a.R_panier > 0 and h1b.R_panier > 0 and V.loc["M15"].R_panier > 0
    bat = bool(h1a.bat_bt_or) and bool(h1b.bat_bt_or)
    verdict = "TIENT" if pos and bat and pw["H1"] < 0.10 else ("PRESQUE" if pos else "NE TIENT PAS")
    print("\nVERDICT (fixe d'avance, version A) : %s  [R/panier H1 1re moitie %+.3f, 2de %+.3f, M15 %+.3f ; a risque egal "
          "contre bt_or : %+.1f vs %+.1f et %+.1f vs %+.1f ; White H1 p = %.3f]" % (
              verdict, h1a.R_panier, h1b.R_panier, V.loc["M15"].R_panier, h1a.variante_risque_egal, h1a.bt_or_R,
              h1b.variante_risque_egal, h1b.bt_or_R, pw["H1"]))
    rows.append(dict(section="verdict", variante="A", jeu=verdict, p_white=pw["H1"]))
    pd.DataFrame(rows).round(4).to_csv(os.path.join(ICI, "donnees", "gpt_pyramide.csv"), index=False)
    print("Duree %.0f s ; ecrit donnees/gpt_pyramide.csv" % (time.time() - T00))
