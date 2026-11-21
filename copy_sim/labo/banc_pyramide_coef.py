"""Banc PY : grille DANS LE SENS du prix (pyramide a coefficient) sur l'or XAUUSD, compte DEMO, aucun ordre
(PRIORITES 21/11, piste 2, point 2). Base = mecanique bt_or (banc_bt_regulier.simule) :
  sens = cloture contre l'EMA 2 jours ; entree a la cloture des bougies aux heures serveur fixes (M5 03:05, 08:00,
  08:30, 12:00, 15:45, 16:00, 16:30 ; H1 = banc_jumeau.H_H1) s'il n'y a pas de panier de ce cote ; ajouts dans le
  sens du prix a la cloture d'une bougie au-dela du niveau suivant (niveau saute si la cloture est a plus d'un
  demi-pas au-dela) ; sortie de TOUT le panier au recul depuis le meilleur prix (stop suiveur = stop initial).
CE QUI CHANGE : la taille du palier k (k = 0 = entree) vaut w_k x lot de base :
  coefficients : 1,0 (w = 1) ; 1,2 ; 1,3 ; 1,5 ; 2,0 (w = coef^k) ; « cloche » (1 ; 1,4 ; 1,8 ; 2,2 ; 2,6 ; 3,0 au
  niveau 5, puis 3 x 0,98^(k-5) comme BlockFIFO) ; decroissant 0,8 (w = 0,8^k, pyramide classique).
  pas entre paliers 0,125 / 0,25 / 0,5 ATR jour 20 j (veille, fige a l'ouverture) ; paliers max (positions) 3 / 5 / 10.
  sortie : « fixe » = recul 0,667 ATR (bt_or) ; « serre » = recul divise par 2 (une fois pour toutes) des que le gain
  latent a la cloture atteint +2 R (R = recul x lot du palier 0, comme BTS) ; « pm » = point mort apres le palier 3 :
  des que 3 positions sont ouvertes, le stop ne peut plus etre sous le prix moyen d'entree du panier.
SECURITES (toutes les variantes de la grille) :
  stop global du panier = X % du solde au depart du panier. TAILLE : le lot de base est tel que la perte NATURELLE la
  plus forte de la pyramide pleine (prix monte jusqu'au dernier palier rempli puis recule jusqu'a la sortie, entrees
  aux niveaux nominaux ; calcul exact par variante, L_max en ATR x lot de base) vaut X % : lot de base = X % x solde /
  (L_max x ATR). Le stop global (perte latente du panier >= L_max x ATR par lot de base, verifiee au pire prix de la
  bougie) coupe donc tout ce qui depasse la perte prevue (entrees au-dela des niveaux, ecarts d'ouverture, spread,
  portage). « SAUT » = stop global touche (sortie au niveau du stop global, ou a l'ouverture si l'ecart l'a deja
  franchi) ; on compte aussi les « quasi-sauts » (perte >= 75 % de X).
  filtre de tendance : EMA 2 jours (sens) + pas d'ajout si ATR 20 j > 1,2 x ATR 100 j (marche agite ; inactif tant
  que l'ATR 100 j n'existe pas). Pause : aucun nouveau panier (deux cotes) pendant 24 h apres un saut.
GRILLE FIXEE AVANT EXECUTION (rien d'ajoute ensuite), N = 105 variantes, nom « coef/pas/paliers/sortie » :
  sortie fixe : 7 coefficients x 3 pas x 3 paliers = 63 ; sorties serre et pm : 7 x 3 paliers x 2, pas 0,25 = 42.
  X (3 / 5 / 10 %) ne change ni les paniers ni les sauts (tout est en unites de lot de base, le stop global est en $
  par lot de base) : les rendements en % sont proportionnels a X. Les 105 sont donc mesurees a X = 5 % ; X = 3 / 10 %
  seulement pour les tailles de saut et la ruine (compte cent, arrondis).
REFERENCES (hors N, memes couts) : bt_or = 1,0/0,25/3/fixe SANS securites (ni stop global, ni filtre, ni pause) ;
  bt_or_plus_opt = n x lot (w = 1 + k), 5 paliers, 0,25, fixe, sans securites (banc_bt_plus) ; + sa version avec
  securites. Meme mise en % (L_max -> X) pour tous ; comparaison AU MEME RISQUE = facteur fa = pire baisse journaliere
  de bt_or / pire baisse de la variante (colonnes *_a) ; equivalent : gain / pire baisse.
DONNEES : or M5 du courtier xau_m5_2025a + xau_m5_90k (06/2025 -> 11/2026, ~17 mois) ; or H1 xau_h1_50k depuis le
  01/08/2022 (~4 ans) ; M1 xau_m1_90k (3 mois) en controle de l'ordre intrabougie (memes regles, ajouts sur cloture M5).
COUTS : achat a cloture + spread, vente a cloture ; sortie au niveau (vente declenchee par haut + spread) ou a
  l'ouverture en cas d'ecart ; portage 6 %/an du notionnel (0,06/260 par nuit ouvree) des positions ouvertes a 23 h
  serveur, des deux cotes. Ordre dans la bougie PESSIMISTE : stops (suiveur, point mort, global) avec le meilleur prix
  d'AVANT la bougie, puis meilleur prix, puis ajouts a la cloture, puis entrees. Optimiste (meilleur prix d'abord) :
  une ligne sur M5. Controle : 1,0/0,25/3/fixe sans securites, sans portage, sans ecart et avec la convention de
  banc_bt_regulier (vente a cloture - spread) redonne banc_bt_regulier.simule panier par panier.
MESURES (par variante, M5 et H1) : courbe JOURNALIERE marquee (gain latent compris), en % du compte (additif) ; gain
  median par mois, % de mois positifs, pire baisse, paniers/mois ; sauts : nombre, 1 tous les N mois, taille mediane
  et pire (% du compte), mois de gain median effaces par saut ; quasi-sauts.
RUINE (compte cent en euros, EURUSD 1,16 ; 0,01 lot cent = 0,01 once ; chaque position = lot de base ideal x w_k
  arrondi a 0,01 once, au moins 0,01 ; taille au solde du jour de cloture du panier) a 100 et 500 EUR : (a) rejeu H1
  depuis chaque debut de mois, 252 et 504 jours ouvres ; (b) Monte-Carlo bootstrap stationnaire des JOURS H1 (blocs
  moyens 20 j, 5000 tirages, graine 2111) sur 12 et 24 mois. Ruine = solde < 20 % de la mise OU lot de base ideal
  < 0,005 once (le minimum doublerait au moins le risque voulu). Aussi : finir sous la mise.
RIGUEUR : walk-forward M5 6 -> 1 mois, H1 12 -> 3 mois glissants ; choix sur l'apprentissage au meilleur gain / pire
  baisse parmi les variantes sans saut de plus de 25 % du compte ; facteur fa (pire baisse de bt_or / pire baisse du
  choix) appris sur l'apprentissage ; rejoue sur le test ; compare a ne rien faire et a bt_or (memes mois).
  Reality check de White (banc_bt_regulier.white, blocs 5 j, 2000 tirages) sur jours x 105 variantes (rendements en %
  a X = 5 %) contre zero -> p corrige par jeu ; en plus (information) contre bt_or au meme risque.
VERDICT FIXE D'AVANCE : TIENT = walk-forward hors echantillon > 0 ET > bt_or au meme risque sur M5 ET H1, p corrige
  (contre zero) < 0,10 sur les deux jeux, ET ruine 24 mois Monte-Carlo a 500 EUR < 5 % pour la variante la plus
  choisie par le walk-forward H1, a X = 5 % ; PRESQUE = du bon cote hors echantillon sur les deux jeux mais p >= 0,10
  ou ruine >= 5 % ; sinon NE TIENT PAS.
RESULTAT (execution du 21/11/2026 ...) : a remplir.
Ecrit donnees/pyramide_coef.csv. Usage : python3 banc_pyramide_coef.py"""
import os, time, itertools, warnings
from multiprocessing import Pool
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_bt_regulier as BR
import banc_jumeau as BJ

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
RECUL = BR.STOP                        # 0,6667 ATR
KPM = 3                                # point mort apres le palier 3
SWAP = 0.06 / 260                      # par nuit ouvree, du notionnel
EURUSD, ONCE_MIN = 1.16, 0.01
COEFS = ("1.0", "1.2", "1.3", "1.5", "2.0", "cloche", "0.8")
PAS = (0.125, 0.25, 0.5)
PALIERS = (3, 5, 10)
GRILLE = [(c, p, k, "fixe") for c in COEFS for p in PAS for k in PALIERS] + \
         [(c, 0.25, k, s) for s in ("serre", "pm") for c in COEFS for k in PALIERS]
NOM = lambda v: "%s/%g/%d/%s" % v[:4]
REFS = {"bt_or": ("1.0", 0.25, 3, "fixe", False), "bt_or_plus_opt": ("lin", 0.25, 5, "fixe", False),
        "bt_or_plus_opt+secu": ("lin", 0.25, 5, "fixe", True)}
H_M1 = {(h, m + 4) for h, m in BR.H_M5}


def poids(coef, K):
    if coef == "cloche":
        return np.array([1 + 0.4 * k if k <= 5 else 3 * 0.98 ** (k - 5) for k in range(K)])
    if coef == "lin":
        return 1.0 + np.arange(K)
    return float(coef) ** np.arange(K)


def lmax(W, pas, sortie):
    """Perte naturelle la plus forte (ATR x lot de base) : m paliers remplis aux niveaux nominaux, meilleur prix au
    dernier, sortie au recul (ou point mort)."""
    pire = 0.0
    for m in range(1, len(W) + 1):
        e = np.arange(m) * pas; w = W[:m]; best = (m - 1) * pas; r = RECUL
        if sortie == "serre" and (w * (best - e)).sum() >= 2 * RECUL * W[0]:
            r = RECUL / 2
        x = best - r
        if sortie == "pm" and m >= KPM:
            x = max(x, (w * e).sum() / w.sum())
        pire = max(pire, -(w * (x - e)).sum())
    return pire


def table_jour(d):
    jour = d.heure.values // 86400
    return pd.DataFrame({"jour": jour, "h": d.haut.values, "l": d.bas.values, "c": d.cloture.values}).groupby("jour").agg(
        h=("h", "max"), l=("l", "min"), c=("c", "last"))


def simule_p(d, v, span=576, heures=BR.H_M5, debut=600, m1=False, opt=False, exact=False, dj=None):
    """Une variante v = (coef, pas, paliers, sortie, securites). Rend (paniers, jours, courbe u cumulee) ;
    u = gain en unites de L_max x ATR (x X % = % du compte)."""
    coef, pas_a, K, sortie, secu = v
    W = poids(coef, K); Lm = lmax(W, pas_a, sortie)
    c, hi, lo, sp, t, o = (d[x].values for x in ("cloture", "haut", "bas", "sp", "heure", "ouverture"))
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    jour = t // 86400
    j = table_jour(d) if dj is None else dj
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    a100 = tr.rolling(100).mean().shift(1).reindex(jour).values
    agite = np.nan_to_num(atr > 1.2 * a100, nan=0).astype(bool) if secu else np.zeros(len(c), bool)
    fin_j = np.r_[jour[1:] != jour[:-1], True]
    s23 = (hh == 23) & np.r_[True, hh[:-1] != 23]
    if exact:
        s23[:] = False
    fin_m5 = (mm % 5 == 4) if m1 else np.ones(len(c), bool)
    P, U, JO = [], [], []
    acc = 0.0; ouvert = {}; pause = -1
    for i in range(debut, len(c)):
        if s23[i]:
            for p in ouvert.values():
                for k in range(p["n"]):
                    p["sw"][k] += SWAP * c[i]; p["sww"] += W[k] * SWAP * c[i]
        for s in list(ouvert):
            p = ouvert[s]
            if opt:
                p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            sw_, swe = p["sw_"], p["swe"]
            T = p["meilleur"] - s * p["recul"]
            S = (swe - s * (p["G"] - p["sww"])) / sw_ if secu else None
            L, saut = T, False
            if secu and s * (S - L) > 0:
                L, saut = S, True
            if sortie == "pm" and p["n"] >= KPM:
                be = swe / sw_
                if s * (be - L) > 0:
                    L, saut = be, False
            if (lo[i] <= L) if s > 0 else (hi[i] + sp[i] >= L):
                x = L
                if not exact:
                    oo = o[i] if s > 0 else o[i] + sp[i]
                    if s * (oo - L) < 0:
                        x = oo
                n = p["n"]
                pp = np.zeros(10); ww = np.zeros(10)
                pp[:n] = s * (x - np.array(p["e"])) - np.array(p["sw"][:n]); ww[:n] = W[:n]
                g = (ww * pp).sum()
                gu = g / (Lm * p["atr"])
                acc += gu
                P.append((t[p["i"]], t[i], s, n, g / (RECUL * p["atr"]), gu, saut, p["atr"], c[p["i"]], Lm * p["atr"], pp, ww))
                del ouvert[s]
                if saut and secu:
                    pause = t[i] + 86400
                continue
            if not opt:
                p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            if fin_m5[i]:
                while p["n"] < K and s * (c[i] - p["prochain"]) >= 0:
                    if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"] and not agite[i]:
                        e = c[i] + sp[i] if s > 0 else (c[i] - sp[i] if exact else c[i])
                        k = p["n"]; p["e"].append(e); p["n"] += 1
                        p["sw_"] += W[k]; p["swe"] += W[k] * e
                    p["prochain"] += s * p["pas"]
                if sortie == "serre" and not p["serre"]:
                    x = c[i] if s > 0 else c[i] + sp[i]
                    if sum(W[k] * s * (x - p["e"][k]) for k in range(p["n"])) - sum(W[k] * p["sw"][k] for k in range(p["n"])) >= 2 * RECUL * p["atr"] * W[0]:
                        p["serre"] = True; p["recul"] = RECUL * p["atr"] / 2
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0 and t[i] >= pause:
            s = 1 if c[i] > ema[i] else -1
            if s not in ouvert:
                e = c[i] + sp[i] if s > 0 else (c[i] - sp[i] if exact else c[i])
                ouvert[s] = {"i": i, "e": [e], "n": 1, "sw": [0.0] * K, "sww": 0.0, "sw_": W[0], "swe": W[0] * e, "meilleur": c[i],
                             "recul": RECUL * atr[i], "pas": pas_a * atr[i], "prochain": c[i] + s * pas_a * atr[i],
                             "atr": atr[i], "G": Lm * atr[i], "serre": False}
        if fin_j[i]:
            lat = 0.0
            for s, p in ouvert.items():
                x = c[i] if s > 0 else c[i] + sp[i]
                lat += sum(W[k] * (s * (x - p["e"][k]) - p["sw"][k]) for k in range(p["n"])) / (Lm * p["atr"])
            U.append(acc + lat); JO.append(jour[i])
    P = pd.DataFrame(P, columns=["t0", "t1", "s", "n", "gR", "gu", "saut", "atr", "px", "LA", "pp", "ww"])
    P["jour"] = pd.to_datetime(P.t1 // 86400 * 86400, unit="s")
    return P, pd.Series(U, pd.to_datetime(np.array(JO) * 86400, unit="s")), Lm


# ---------------------------------------------------------------- mesures
def mesures(u, P, X=5.0):
    x = X * u.diff().fillna(u.iloc[0])
    mo = x.index.to_period("M"); mm = x.groupby(mo).sum(); nm = len(mm)
    cr = BJ.creux(x.values)
    sa = P[P.saut]; qs = P[(P.gu * X <= -0.75 * X)]
    gmed = mm.median()
    taille = -X * sa.gu
    return dict(gain_med_mois=gmed, mois_pos=100 * (mm > 0).mean(), nb_mois=nm, total=x.sum(), pire_baisse=cr,
                gain_creux=x.sum() / -cr if cr < 0 else np.inf, paniers_mois=len(P) / nm, pos_moy=P.n.mean(),
                sauts=len(sa), saut_1_tous_mois=nm / len(sa) if len(sa) else np.inf,
                saut_med=taille.median() if len(sa) else 0.0, saut_pire=taille.max() if len(sa) else 0.0,
                mois_effaces=(taille.median() / gmed if gmed > 0 else np.inf) if len(sa) else 0.0,
                quasi_sauts=len(qs), pire_panier=-X * P.gu.min(), pire_jour=-x.min(),
                sharpe=x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0.0)


# ---------------------------------------------------------------- ruine (compte cent)
def tableaux_jours(P, jours):
    """Par jour de cloture : pnl $/once par position (S x 10), poids, L_max x ATR, prix."""
    pos = pd.Index(jours).get_indexer(P.jour)
    S = max(1, np.bincount(pos[pos >= 0]).max()) if (pos >= 0).any() else 1
    nj = len(jours)
    PP = np.zeros((nj, S, 10)); WW = np.zeros((nj, S, 10)); LA = np.zeros((nj, S)); PX = np.zeros((nj, S))
    cpt = np.zeros(nj, int)
    for q, r in zip(pos, P.itertuples()):
        if q < 0:
            continue
        k = cpt[q]; PP[q, k] = r.pp; WW[q, k] = r.ww; LA[q, k] = r.LA; PX[q, k] = r.px; cpt[q] += 1
    return PP, WW, LA, PX


def ruine(TAB, idx, mise, X):
    """idx : tirages x jours (indices de jours). Rend dict ruine / sous la mise a 12 (252 j) et 24 mois (504 j)."""
    PP, WW, LA, PX = TAB
    n, T = idx.shape
    bal = np.full(n, float(mise)); mort = np.zeros(n, bool); marge = 0.0; out = {}
    for t in range(T):
        j = idx[:, t]
        la = LA[j]; ww = WW[j]; pp = PP[j]
        act = la > 0
        base = np.where(act, X / 100 * bal[:, None] * EURUSD / np.where(act, la, 1), 0)        # once
        impos = (act & (base < 0.5 * ONCE_MIN)).any(1)
        lots = np.round(base[:, :, None] * ww / ONCE_MIN) * ONCE_MIN
        lots = np.where(ww > 0, np.maximum(lots, ONCE_MIN), 0)
        marge = max(marge, ((lots.sum(2) * PX[j]).sum(1) / 500 / np.maximum(bal * EURUSD, 1e-9))[~mort].max(initial=0))
        pnl = (lots * pp).sum((1, 2)) / EURUSD
        bal = np.where(mort, bal, bal + pnl)
        mort |= impos | (bal < 0.2 * mise)
        if t + 1 in (252, 504):
            out[t + 1] = (100 * mort.mean(), 100 * (bal < mise).mean(), np.median(bal))
    out["marge"] = marge
    return out


def boot_jours(nj, T, B=5000, b=20.0, graine=2111):
    r = np.random.default_rng(graine)
    out = np.empty((B, T), int)
    for k in range(B):
        neuf = r.random(T) < 1 / b; neuf[0] = True
        bl = np.cumsum(neuf) - 1; deb = np.flatnonzero(neuf)
        out[k] = (r.integers(nj, size=len(deb))[bl] + np.arange(T) - deb[bl]) % nj
    return out


# ---------------------------------------------------------------- execution parallele
D = {}
KW = {"M5": {}, "H1": dict(span=48, heures=BJ.H_H1, debut=60),
      "M1": dict(span=2880, heures=H_M1, debut=3000, m1=True)}


def tache(arg):
    jeu, nom, v, opts = arg
    if jeu == "M1":
        opts = dict(opts, dj=table_jour(D["M5"]))
    P, u, Lm = simule_p(D[jeu], v, **KW[jeu], **opts)
    return jeu, nom, opts.get("opt", False), P, u, Lm


def charge_tout():
    a5, b5 = BR.charge("xau_m5_2025a"), BR.charge("xau_m5_90k")
    D["M5"] = pd.concat([a5, b5[b5.heure > a5.heure.iloc[-1]]], ignore_index=True)
    dh = BR.charge("xau_h1_50k")
    D["H1"] = dh[dh.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
    D["M1"] = BR.charge("xau_m1_90k")


def walk_forward(XS, ref, L_app, L_test, saut_max):
    """XS : DataFrame jours x variantes (% a X = 5) ; saut_max : dict nom -> serie des pertes de sauts datees."""
    mois = XS.index.to_period("M"); MO = mois.unique()
    oo, oref, ch = [], [], []
    for i0 in range(L_app, len(MO), L_test):
        app = (mois >= MO[i0 - L_app]) & (mois <= MO[i0 - 1])
        te = (mois >= MO[i0]) & (mois <= MO[min(i0 + L_test, len(MO)) - 1])
        crr = BJ.creux(XS[ref][app].values)
        best, bv = None, -np.inf
        for nom in XS.columns:
            if nom in REFS:
                continue
            sm = saut_max[nom]
            z = sm[(sm.index >= XS.index[app][0]) & (sm.index <= XS.index[app][-1])]
            if len(z) and z.max() > 25:
                continue
            x = XS[nom][app]; cr = BJ.creux(x.values)
            r = x.sum() / -cr if cr < 0 else (np.inf if x.sum() > 0 else 0)
            if r > bv:
                best, bv = nom, r
        cr = BJ.creux(XS[best][app].values)
        fa = crr / cr if cr < 0 else 1.0
        oo.append(fa * XS[best][te]); oref.append(XS[ref][te]); ch.append(best)
    return pd.concat(oo), pd.concat(oref), ch


if __name__ == "__main__":
    charge_tout()
    print("Grille fixee : %d variantes (+ %d references). Donnees M5 %d bougies, H1 %d, M1 %d." % (
        len(GRILLE), len(REFS), len(D["M5"]), len(D["H1"]), len(D["M1"])))
    # controle : reproduit banc_bt_regulier.simule
    for jeu in ("M5", "H1"):
        Pc, _, _ = simule_p(D[jeu], ("1.0", 0.25, 3, "fixe", False), exact=True, **KW[jeu])
        kw = {k: w for k, w in KW[jeu].items() if k != "m1"}
        Rb = BR.simule(D[jeu], **kw)
        print("Controle %s : %d paniers %+.1f R ; banc_bt_regulier.simule %d paniers %+.1f R ; identiques panier par panier : %s"
              % (jeu, len(Pc), Pc.gR.sum(), len(Rb), Rb.g.sum(), len(Rb) == len(Pc) and np.allclose(Pc.gR.values, Rb.g.values)))
    VAR = {NOM(v): v + (True,) for v in GRILLE}
    VAR.update(REFS)
    taches = [(j, n, v, {}) for j in ("M5", "H1") for n, v in VAR.items()]
    with Pool(4) as pool:
        RES = pool.map(tache, taches, chunksize=4)
    S = {(j, n): (P, u, Lm) for j, n, _, P, u, Lm in RES}
    print("Simulation des %d x 2 jeux : %.0f s" % (len(VAR), time.time() - T00))
    # ------------------------------------------------ mesures, walk-forward, White
    rows, WF, PW = [], {}, {}
    for jeu, (L_app, L_test) in (("M5", (6, 1)), ("H1", (12, 3))):
        XS = pd.DataFrame({n: 5.0 * S[jeu, n][1].diff().fillna(S[jeu, n][1].iloc[0]) for n in VAR})
        mref = mesures(S[jeu, "bt_or"][1], S[jeu, "bt_or"][0])
        for n, v in VAR.items():
            P, u, Lm = S[jeu, n]
            m = mesures(u, P)
            fa = mref["pire_baisse"] / m["pire_baisse"] if m["pire_baisse"] < 0 else 1.0
            rows.append(dict(jeu=jeu, variante=n, coef=v[0], pas=v[1], paliers=v[2], sortie=v[3], securites=v[4],
                             L_max_ATR=Lm, **m, facteur_a=fa, gain_med_mois_a=fa * m["gain_med_mois"], total_a=fa * m["total"],
                             saut_med_a=fa * m["saut_med"]))
        smax = {n: pd.Series(-5.0 * S[jeu, n][0].gu[S[jeu, n][0].saut].values, S[jeu, n][0].jour[S[jeu, n][0].saut].values) for n in VAR}
        o, orf, ch = walk_forward(XS, "bt_or", L_app, L_test, smax)
        noms = [NOM(v) for v in GRILLE]
        ib, pz = BR.white(XS[noms].values)
        Dm = np.column_stack([XS[n] * (BJ.creux(XS["bt_or"].values) / BJ.creux(XS[n].values)) - XS["bt_or"] for n in noms])
        ib2, pr = BR.white(Dm)
        fq = pd.Series(ch).value_counts()
        mo, mr = o.groupby(o.index.to_period("M")).sum(), orf.groupby(orf.index.to_period("M")).sum()
        WF[jeu] = dict(oos=o.sum(), ref=orf.sum(), cr=BJ.creux(o.values), crr=BJ.creux(orf.values), mpos=100 * (mo > 0).mean(),
                       mposr=100 * (mr > 0).mean(), nf=len(ch), choix=fq, p0=pz, pref=pr, best0=noms[ib], best1=noms[ib2],
                       debut=o.index[0].date(), fin=o.index[-1].date())
        print("\n=== %s : walk-forward %d -> %d mois, %d fenetres (%s -> %s) ; choix : %s" % (
            jeu, L_app, L_test, len(ch), o.index[0].date(), o.index[-1].date(), ", ".join("%s %d" % kv for kv in fq.head(5).items())))
        print("  hors echantillon (a la pire baisse d'apprentissage de bt_or) %+.1f %% (creux %.1f, mois>0 %.0f %%) ; bt_or memes mois %+.1f %% (creux %.1f, mois>0 %.0f %%)"
              % (o.sum(), BJ.creux(o.values), WF[jeu]["mpos"], orf.sum(), BJ.creux(orf.values), WF[jeu]["mposr"]))
        print("  White contre zero : meilleur %s, p corrige %.3f (N = %d) ; contre bt_or au meme risque : meilleur %s, p %.3f"
              % (noms[ib], pz, len(noms), noms[ib2], pr))
    T = pd.DataFrame(rows)
    # ------------------------------------------------ ruine (H1), MC et rejeu historique
    jH = S["H1", "bt_or"][1].index
    I24 = boot_jours(len(jH), 504)
    mois_deb = np.flatnonzero(np.r_[True, jH.month[1:] != jH.month[:-1]])
    HIS = {T_: np.array([np.arange(q, q + T_) for q in mois_deb if q + T_ <= len(jH)]) for T_ in (252, 504)}
    chH = WF["H1"]["choix"].index[0]; ch5 = WF["M5"]["choix"].index[0]
    A, B = T[T.jeu == "M5"].set_index("variante"), T[T.jeu == "H1"].set_index("variante")
    sc = (A.gain_creux / A.gain_creux["bt_or"] + B.gain_creux / B.gain_creux["bt_or"]) / 2
    meil = sc.drop(list(REFS)).idxmax()
    TABLE = list(dict.fromkeys(["bt_or", "1.0/0.25/3/fixe", "bt_or_plus_opt", "bt_or_plus_opt+secu", chH, ch5, meil,
                                "1.5/0.25/5/fixe", "2.0/0.125/10/fixe", "cloche/0.25/10/fixe", "0.8/0.25/5/fixe"]))
    print("\n=== Ruine compte cent (jours H1 08/2022 -> 11/2026), X = 5 %% pour les 105 ; X = 3/10 %% pour le tableau")
    RU = []
    for n in VAR:
        TAB = tableaux_jours(S["H1", n][0], jH)
        for X in ((3.0, 5.0, 10.0) if n in TABLE else (5.0,)):
            for mise in (100, 500):
                mc = ruine(TAB, I24, mise, X)
                h12, h24 = ruine(TAB, HIS[252], mise, X), ruine(TAB, HIS[504], mise, X)
                RU.append(dict(variante=n, X=X, mise=mise, mc12_ruine=mc[252][0], mc12_sous=mc[252][1], mc24_ruine=mc[504][0],
                               mc24_sous=mc[504][1], mc24_median=mc[504][2], hist12_ruine=h12[252][0], hist12_sous=h12[252][1],
                               hist24_ruine=h24[504][0], hist24_sous=h24[504][1], n_hist12=len(HIS[252]), n_hist24=len(HIS[504]),
                               marge_max=mc["marge"]))
    RU = pd.DataFrame(RU)
    print("Ruine calculee (%.0f s depuis le debut). Fenetres historiques : %d (12 mois), %d (24 mois)." % (
        time.time() - T00, len(HIS[252]), len(HIS[504])))
    # ------------------------------------------------ controles M1 / optimiste sur le tableau
    tch = [("M5", n, VAR[n], {"opt": True}) for n in TABLE] + [("M1", n, VAR[n], {}) for n in TABLE]
    with Pool(4) as pool:
        R2 = pool.map(tache, tch)
    O = {(j, n, op): (P, u) for j, n, op, P, u, _ in R2}
    t1m = O["M1", "bt_or", False][1].index[0] + pd.Timedelta(days=30)
    t2m = O["M1", "bt_or", False][1].index[-1] - pd.Timedelta(days=1)
    print("\n=== Controles (tableau) : convention optimiste M5 ; M1 contre M5 sur les memes paniers ouverts %s -> %s (gain %% a X = 5)"
          % (t1m.date(), t2m.date()))
    for n in TABLE:
        P5 = S["M5", n][0]; Po = O["M5", n, True][0]; P1 = O["M1", n, False][0]
        f = lambda P: P[(pd.to_datetime(P.t0, unit="s") >= t1m) & (pd.to_datetime(P.t1, unit="s") <= t2m)]
        print("  %-22s M5 pessimiste %+7.1f %% (sauts %3d) ; optimiste %+7.1f %% (sauts %3d) | 3 mois : M5 %+6.1f %% (%d pan.) M1 %+6.1f %% (%d pan.)"
              % (n, 5 * P5.gu.sum(), P5.saut.sum(), 5 * Po.gu.sum(), Po.saut.sum(), 5 * f(P5).gu.sum(), len(f(P5)),
                 5 * f(P1).gu.sum(), len(f(P1))))
    # ------------------------------------------------ tableau
    print("\n=== Tableau (X = 5 %% ; *_a = au meme risque que bt_or = meme pire baisse journaliere)")
    print("%-22s %-3s %6s %5s %7s %6s %6s %6s %4s %6s %5s %5s %7s %7s | ruine MC 12/24 m : 100E   500E | hist 24 m 100/500" % (
        "variante", "jeu", "Lmax", "pan/m", "gmed/m", "m>0%", "creux", "g/cr", "saut", "1/Nm", "med", "pire", "effaces", "gmed_a"))
    for n in TABLE:
        for jeu, Z in (("M5", A), ("H1", B)):
            r = Z.loc[n]
            ru = RU[(RU.variante == n) & (RU.X == 5.0)].set_index("mise")
            print("%-22s %-3s %6.2f %5.1f %+7.2f %6.0f %6.1f %6.2f %4d %6.1f %5.1f %5.1f %7.1f %+7.2f |  %4.1f/%4.1f  %4.1f/%4.1f | %4.1f/%4.1f" % (
                n, jeu, r.L_max_ATR, r.paniers_mois, r.gain_med_mois, r.mois_pos, r.pire_baisse, r.gain_creux, r.sauts,
                min(r.saut_1_tous_mois, 999), r.saut_med, r.saut_pire, min(r.mois_effaces, 999), r.gain_med_mois_a,
                ru.loc[100, "mc12_ruine"], ru.loc[100, "mc24_ruine"], ru.loc[500, "mc12_ruine"], ru.loc[500, "mc24_ruine"],
                ru.loc[100, "hist24_ruine"], ru.loc[500, "hist24_ruine"]))
    print("Ruine selon X (MC 24 mois, ruine %% / sous la mise %%, 100 E | 500 E) :")
    for n in TABLE:
        z = RU[RU.variante == n].set_index(["X", "mise"])
        print("  %-22s " % n + " ; ".join("X=%g : %4.1f/%4.1f | %4.1f/%4.1f" % (X, z.loc[(X, 100), "mc24_ruine"], z.loc[(X, 100), "mc24_sous"],
                                                                             z.loc[(X, 500), "mc24_ruine"], z.loc[(X, 500), "mc24_sous"]) for X in (3.0, 5.0, 10.0))
              + " ; marge max %.2f x solde" % z.marge_max.max())
    print("Effet moyen par dimension (gain/creux M5 | H1, grille avec securites) :")
    G = T[T.securites & ~T.variante.isin(list(REFS))]
    for dim in ("coef", "pas", "paliers", "sortie"):
        g = G.groupby(["jeu", dim]).gain_creux.median().unstack(0)
        print("  %-8s " % dim + " | ".join("%s %.2f/%.2f" % (k, g.loc[k, "M5"], g.loc[k, "H1"]) for k in g.index))
    nb5 = (A.drop(list(REFS)).gain_creux > A.gain_creux["bt_or"]).sum(); nbh = (B.drop(list(REFS)).gain_creux > B.gain_creux["bt_or"]).sum()
    deux = ((A.gain_creux > A.gain_creux["bt_or"]) & (B.gain_creux > B.gain_creux["bt_or"])).drop(list(REFS))
    print("Variantes > bt_or en gain/pire baisse (= au meme risque) : M5 %d/105, H1 %d/105, les deux : %s" % (
        nb5, nbh, ", ".join(deux[deux].index) or "aucune"))
    # ------------------------------------------------ BlockFIFO reel
    h = pd.read_csv(os.path.join(ICI, "mt5", "autres", "historique.csv.gz")); f = h[h.magique == 701100]
    rf = f.resultat + f.swap + f.commission; jf = rf.groupby(pd.to_datetime(f.fermeture_heure_serveur, unit="s").dt.date).sum()
    print("BlockFIFO reel (magique 701100) : %d positions, %+.0f $ (resultat+swap), %.0f %% gagnantes, %d jours ; pire jour %s %+.0f $ "
          "(les autres jours %+.0f $)" % (len(f), rf.sum(), 100 * (f.resultat > 0).mean(), len(jf), jf.idxmin(), jf.min(), jf.sum() - jf.min()))
    # ------------------------------------------------ verdict
    ruH = RU[(RU.variante == chH) & (RU.X == 5.0) & (RU.mise == 500)].mc24_ruine.iloc[0]
    bon = {j: WF[j]["oos"] > 0 and WF[j]["oos"] > WF[j]["ref"] for j in WF}
    pok = all(WF[j]["p0"] < 0.10 for j in WF)
    v = "TIENT" if all(bon.values()) and pok and ruH < 5 else ("PRESQUE" if all(bon.values()) else "NE TIENT PAS")
    print("\nVerdict (fixe d'avance) : %s. WF M5 %+.1f %% contre bt_or %+.1f %% ; WF H1 %+.1f %% contre bt_or %+.1f %% ; "
          "p corrige M5 %.3f, H1 %.3f (N = %d) ; ruine MC 24 mois 500 EUR de %s (X = 5 %%) : %.1f %%" % (
              v, WF["M5"]["oos"], WF["M5"]["ref"], WF["H1"]["oos"], WF["H1"]["ref"], WF["M5"]["p0"], WF["H1"]["p0"], len(GRILLE), chH, ruH))
    T = T.merge(RU[RU.X == 5.0].pivot_table(index="variante", columns="mise", values=["mc12_ruine", "mc24_ruine", "hist12_ruine", "hist24_ruine", "mc24_sous"]).pipe(
        lambda z: z.set_axis(["%s_%dE" % c for c in z.columns], axis=1)).reset_index(), on="variante", how="left")
    T = pd.concat([T, RU.assign(jeu="ruine_H1")], ignore_index=True)
    T.round(4).to_csv(os.path.join(ICI, "donnees", "pyramide_coef.csv"), index=False)
    print("Ecrit donnees/pyramide_coef.csv (%d lignes). Duree totale %.0f s." % (len(T), time.time() - T00))
    # quelques paniers pour controle
    P = S["H1", chH][0]
    for r in [P.loc[P.gu.idxmin()], P.loc[P.gu.idxmax()]]:
        print("  panier H1 %s : %s -> %s, sens %+d, %d positions, ATR %.2f, prix %.2f, gain %+.3f x L_max (%+.2f %% a X = 5), saut %s"
              % (chH, pd.to_datetime(r.t0, unit="s"), pd.to_datetime(r.t1, unit="s"), r.s, r.n, r.atr, r.px, r.gu, 5 * r.gu, r.saut))
