"""Banc ENTREE-MOMENT : bt_or peut-il mieux choisir le MOMENT d'entree ? (PRIORITES 22/11 « bt_or doit mieux entrer en
position », pistes 1 et 2 ; compte demo, aucun ordre).
Tout le reste de bt_or est garde : sens = cloture contre EMA 2 jours (M5 span 576, H1 span 48), un panier par cote,
ajouts tous les 0,25 ATR jour 20 j (3 positions au plus, regle de saut de banc_bt_regulier.simule), sortie de tout le
panier sur recul de 0,6667 ATR depuis le meilleur prix ; spread reel ; 1 R = perte d'une position au stop initial.
Seul change l'INSTANT d'entree. Chaque variante produit une liste d'instants (bougie q, sens donne par l'EMA) ; un instant
est pris s'il n'y a pas de panier ouvert de ce cote a la cloture de q (meme regle de blocage que bt_or).
Jeux : or M5 17 mois (xau_m5_2025a + xau_m5_90k, heures BR.H_M5) ; or H1 08/2022 -> 11/2026 (heures banc_jumeau.H_H1),
moities par date d'ouverture : 2022-08 -> 2024-09 et 2024-10 -> 2026-11. « h » = heures (12 bougies M5, 1 bougie H1).
GRILLE FIXEE AVANT EXECUTION, N = 20 variantes (+ bt_or de reference) :
  Piste 1, repli apres heure fixe (R1-R8) : a chaque heure fixe de bt_or, sens s de l'EMA ; on attend, pendant au plus
    D h, la premiere cloture q (apres l'heure) qui a recule de x ATR jour, soit depuis la cloture de l'heure fixe
    (ref « heure »), soit depuis le meilleur prix atteint depuis l'heure fixe (ref « haut » : plus haut pour un achat,
    plus bas pour une vente) ; ordre annule si une cloture repasse de l'autre cote de l'EMA ; sinon pas de panier.
    ref {heure, haut} x x {0,25 ; 0,5} x D {4 h ; 12 h} = 8.
  Piste 1, repli sans heure fixe (R9-R12) : n'importe quelle bougie ; sens de l'EMA ; entree a la cloture qui, pour la
    premiere fois, est a x ATR ou plus sous le plus haut des L dernieres heures (achat ; au-dessus du plus bas pour une
    vente). x {0,25 ; 0,5} x L {12 h ; 24 h} = 4.
  Piste 2, cassure sans heure fixe (C1-C4) : cloture au-dessus du plus haut des N heures precedentes avec cloture > EMA
    (achat), au-dessous du plus bas avec cloture < EMA (vente). N {4, 12, 24, 48} = 4.
  Piste 2, cassure apres heure fixe (C5-C8) : a chaque heure fixe, sens de l'EMA, premiere cloture dans [heure, heure +
    12 h] qui casse le plus haut (plus bas) des N heures precedentes dans ce sens ; annule si l'EMA est recoupee.
    N {4, 12, 24, 48} = 4.
Mesures (consignes communes) : total brut R (paniers sortis), R/panier ; a risque egal : x fa = pire baisse journaliere
  (courbe marquee chaque jour a la cloture, gain latent compris) de bt_or / celle de la variante ; MAE = excursion
  defavorable maximale de la 1re position depuis son entree jusqu'a la sortie du panier, en R (mediane, 75e centile) ;
  % stop initial = le prix touche le stop initial (perte >= 1 R sur la 1re position) avant un gain de 1 R (chemin des
  prix suivi au-dela de la sortie ; meme bougie = stop).
  Contre le hasard : 2000 tirages (graine 2211) du sens aux MEMES instants, blocage rejoue -> p = (1 + nb >= reel)/2001,
  sur tout le jeu et sur chaque moitie H1 ; « toujours acheteur + pyramide » aux memes instants.
  Walk-forward : H1 apprentissage 12 mois / test 3 mois, M5 6 / 1 ; choix parmi les 20 au meilleur gain / |pire
  baisse| d'apprentissage ; la variante choisie est mise au risque de bt_or (fa appris) ; comparee hors echantillon a
  bt_or et a toujours acheteur + pyramide aux heures de bt_or (lui aussi mis au risque de bt_or, fa appris).
  White (BR.white) : matrice jours x 20 de (variante x fa - bt_or), p corrige par jeu.
VERDICT FIXE D'AVANCE : TIENT = le walk-forward bat bt_or ET toujours acheteur + pyramide hors echantillon a risque egal
  sur H1 ET M5, p White < 0,10 sur H1, p contre le sens au hasard < 0,10 sur CHAQUE moitie H1 et MAE mediane ou
  % stop initial meilleur que bt_or (ces trois derniers pour la variante la plus choisie du walk-forward H1) ;
  PRESQUE = walk-forward du bon cote sur les deux jeux mais un autre critere manque ; sinon NE TIENT PAS.
RESULTAT (execution du 22/11/2026, 10 s) : NE TIENT PAS.
  Controles : bt_or H1 956 paniers +153,4 R, hasard +108,1, toujours acheteur +243,7, p 0,040 ; M5 295 / +114,1 R
    (= banc_decompose_bt).
  H1 : le repli ameliore le R par panier (+0,23 a +0,69 contre +0,16) et le total a risque egal (R2 repli 0,25 ATR
    depuis l'heure, 12 h : +114,3 brut, +277,4 a risque egal ; R6 repli 0,25 ATR depuis le plus haut, 12 h : +180,4
    brut, +222,9) ; MAE mediane a peine meilleure (0,42-0,50 contre 0,51), % stop initial inchange (47-52 contre 48).
    Mais aucune variante ne bat le sens au hasard sur les DEUX moities (R6 : p 0,36 / 0,001 ; R4 : 0,023 / 0,38 ;
    meilleur couple R9 0,10 / 0,046) ; White p = 0,278. Les cassures ne font pas mieux que bt_or (C1 +147,8 brut).
    Walk-forward 12/3 (14 fenetres, 2023-08 -> 2026-11) : choisi +246,3 R, bt_or +179,0, toujours acheteur + pyramide
    (meme risque) +319,6 : bat bt_or, pas l'achat permanent.
  M5 : cassures nettement au-dessus du hasard (C2-C8 p 0,0005-0,003) mais pas au-dessus de bt_or en brut ; White
    p = 0,683 ; walk-forward 6/1 (12 mois) : choisi +43,3 R contre bt_or +62,5 (et achat +30,2) : perd.
  Lecture : attendre un repli de 0,25 ATR trie les entrees (moins de paniers, meilleur R/panier) sans rendre le sens
    plus juste ; sur 4 ans, rien ne bat « toujours acheteur + pyramide ».
Ecrit donnees/entree_moment.csv. Usage : python3 banc_entree_moment.py
"""
import os, time, warnings
from multiprocessing import Pool
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_bt_regulier as BR
import banc_jumeau as BJ

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
NT, GRAINE = 2000, 2211
COUPE = pd.Timestamp("2024-10-01").timestamp()

GRILLE = []
for ref in ("heure", "haut"):
    for x in (0.25, 0.5):
        for D in (4, 12):
            GRILLE.append(("R%d repli %s %.2f ATR, %d h" % (len(GRILLE) + 1, ref, x, D), ("repli_h", ref, x, D)))
for x in (0.25, 0.5):
    for L in (12, 24):
        GRILLE.append(("R%d repli libre %.2f ATR, haut %d h" % (len(GRILLE) + 1, x, L), ("repli_l", x, L)))
for N in (4, 12, 24, 48):
    GRILLE.append(("C%d cassure libre %d h" % (len(GRILLE) - 11, N), ("cass_l", N)))
for N in (4, 12, 24, 48):
    GRILLE.append(("C%d cassure apres heure %d h" % (len(GRILLE) - 11, N), ("cass_h", N, 12)))
BT = ("bt_or (heures fixes)", ("bt",))

P = {}   # donnees du jeu courant (globales pour Pool / fork)


def prepare(d, span, heures, debut, bph):
    c, hi, lo, sp, t = (d[x].values.astype(float) if x != "heure" else d[x].values for x in ("cloture", "haut", "bas", "sp", "heure"))
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    n = len(c)
    valide = (np.arange(n) >= debut) & (atr == atr) & (ema == ema) & (atr > 0)
    H = np.array([i for i in np.flatnonzero(valide) if (hh[i], mm[i]) in heures])
    jours = np.unique(jour)
    return dict(c=c, hi=hi, lo=lo, sp=sp, t=t, ema=ema, atr=atr, n=n, valide=valide, H=H, bph=bph,
                jidx=np.searchsorted(jours, jour), jours=pd.to_datetime(jours * 86400, unit="s"))


def instants(v):
    """Liste (q, sens 0 achat / 1 vente) d'une variante, triee par q, un seul instant par bougie."""
    c, hi, lo, ema, atr, n, val, H, b = (P[k] for k in ("c", "hi", "lo", "ema", "atr", "n", "valide", "H", "bph"))
    sg = np.where(c > ema, 1, -1)
    Q = []
    if v[0] == "bt":
        Q = [(i, i, sg[i]) for i in H]
    elif v[0] in ("repli_h", "cass_h"):
        if v[0] == "cass_h":
            NB = v[1] * b
            rh = pd.Series(hi).rolling(NB).max().shift(1).values
            rl = pd.Series(lo).rolling(NB).min().shift(1).values
        for i in H:
            s = sg[i]
            if v[0] == "repli_h":
                _, ref, x, D = v
                q0, q1 = i + 1, min(n, i + 1 + D * b)
            else:
                q0, q1 = i, min(n, i + 1 + v[2] * b)
            seg = np.arange(q0, q1)
            if len(seg) == 0:
                continue
            casse = s * (c[seg] - ema[seg]) <= 0
            if v[0] == "repli_h":
                if ref == "heure":
                    ok = s * (c[i] - c[seg]) >= x * atr[i]
                else:
                    ext = np.maximum.accumulate(hi[i:q1])[1:] if s > 0 else np.minimum.accumulate(lo[i:q1])[1:]
                    ok = s * (ext - c[seg]) >= x * atr[i]
            else:
                ok = (c[seg] > rh[seg]) if s > 0 else (c[seg] < rl[seg])
            ok &= val[seg] & ~casse
            k_ok = np.argmax(ok) if ok.any() else len(seg)
            k_x = np.argmax(casse) if casse.any() else len(seg)
            if k_ok < k_x:
                Q.append((seg[k_ok], i, s))
    elif v[0] == "repli_l":
        _, x, L = v
        LB = L * b
        rh = pd.Series(hi).rolling(LB, min_periods=1).max().values
        rl = pd.Series(lo).rolling(LB, min_periods=1).min().values
        cond = np.where(sg > 0, rh - c >= x * atr, c - rl >= x * atr) & val
        prec = np.r_[False, cond[:-1] & (sg[:-1] == sg[1:])]
        Q = [(q, q, sg[q]) for q in np.flatnonzero(cond & ~prec)]
    elif v[0] == "cass_l":
        NB = v[1] * b
        rh = pd.Series(hi).rolling(NB).max().shift(1).values
        rl = pd.Series(lo).rolling(NB).min().shift(1).values
        ok = val & (((sg > 0) & (c > rh)) | ((sg < 0) & (c < rl)))
        Q = [(q, q, sg[q]) for q in np.flatnonzero(ok)]
    Q.sort()
    q = np.array([a for a, _, _ in Q], int); s = np.array([0 if z > 0 else 1 for _, _, z in Q], int)
    if len(q) == 0:
        return q, s
    garde = np.r_[True, q[1:] != q[:-1]]
    return q[garde], s[garde]


def panier(arg):
    """Panier bt_or ouvert a la cloture de i, sens si (0 achat / 1 vente) : sortie, niveau, entrees, MAE, stop initial."""
    i, si = arg
    c, hi, lo, sp, atr, n = (P[k] for k in ("c", "hi", "lo", "sp", "atr", "n"))
    s = 1 if si == 0 else -1
    st, pas, c0 = BR.STOP * atr[i], BR.PAS * atr[i], c[i]
    e0 = c0 + s * sp[i]
    qx, niv, start, ref, W = n, np.nan, i + 1, c0, 256
    while start < n:
        j1 = min(n, start + W)
        if s > 0:
            pm = np.maximum.accumulate(hi[start:j1]); prev = np.maximum(ref, np.r_[-np.inf, pm[:-1]])
            lvl = prev - st; hit = lo[start:j1] <= lvl
        else:
            pm = np.minimum.accumulate(lo[start:j1]); prev = np.minimum(ref, np.r_[np.inf, pm[:-1]])
            lvl = prev + st; hit = hi[start:j1] + sp[start:j1] >= lvl
        if hit.any():
            k = int(np.argmax(hit)); qx, niv = start + k, lvl[k]
            break
        ref = max(ref, pm[-1]) if s > 0 else min(ref, pm[-1]); start = j1; W *= 4
    ent = [(i, e0)]; pro, pos = c0 + s * pas, i + 1
    while len(ent) < BR.MAXP and pos < qx:
        seg = s * (c[pos:qx] - pro) >= 0
        if not seg.any():
            break
        q = pos + int(np.argmax(seg))
        while len(ent) < BR.MAXP and s * (c[q] - pro) >= 0:
            if s * (c[q] - pro) <= 0.5 * pas:
                ent.append((q, c[q] + s * sp[q]))
            pro += s * pas
        pos = q + 1
    if qx < n:
        g3 = sum(s * (niv - e) for _, e in ent) / st; g1 = s * (niv - e0) / st
        if s > 0:
            adv = min(lo[i + 1:qx].min() if qx > i + 1 else np.inf, niv); mae = (e0 - adv) / st
        else:
            adv = max((hi[i + 1:qx] + sp[i + 1:qx]).max() if qx > i + 1 else -np.inf, niv); mae = (adv - e0) / st
        mae = max(0.0, mae)
    else:
        g3 = g1 = mae = np.nan
    A, F = c0 - s * st, e0 + s * st
    stopi, start, W = np.nan, i + 1, 256
    while start < n:
        j1 = min(n, start + W)
        if s > 0:
            a, f = lo[start:j1] <= A, hi[start:j1] >= F
        else:
            a, f = hi[start:j1] + sp[start:j1] >= A, lo[start:j1] + sp[start:j1] <= F
        if a.any() or f.any():
            ka = np.argmax(a) if a.any() else 10 ** 9; kf = np.argmax(f) if f.any() else 10 ** 9
            stopi = 1.0 if ka <= kf else 0.0
            break
        start = j1; W *= 4
    return qx, g3, g1, mae, stopi, ent, niv, st, s


def marque(b):
    """Increments journaliers marques (cloture de chaque jour, latent compris) d'un panier sorti."""
    i, g3, ent, qx, st, s = b["i"], b["g3"], b["ent"], b["qx"], b["st"], b["s"]
    c, sp, jidx = P["c"], P["sp"], P["jidx"]
    barres = np.arange(i, qx + 1)
    m = c[barres] + (sp[barres] if s < 0 else 0)
    val = np.zeros(len(barres))
    for qe, e in ent:
        val += np.where(barres >= qe, s * (m - e) / st, 0.0)
    val[-1] = g3
    jj = jidx[barres]
    dern = np.r_[jj[1:] != jj[:-1], True]
    jd, vd = jj[dern], val[dern]
    return jd, np.diff(np.r_[0.0, vd])


def rejoue(q, EX, G, S, grp, ng):
    """S : N x K sens. Totaux par groupe (N x ng), nb de paniers sortis par groupe, masque des paniers pris (si N = 1)."""
    N, K = S.shape
    bu = np.zeros((N, 2), int); r = np.arange(N)
    tot = np.zeros((N, ng)); cnt = np.zeros((N, ng)); O = np.zeros((N, K), bool) if N == 1 else None
    n = P["n"]
    for k in range(K):
        sd = S[:, k]
        ok = bu[r, sd] <= q[k]
        bu[r[ok], sd[ok]] = EX[k, sd[ok]]
        fini = ok & (EX[k, sd] < n)
        tot[:, grp[k]] += np.where(fini, G[k, sd], 0.0); cnt[:, grp[k]] += fini
        if O is not None:
            O[0, k] = fini[0]
    return tot, cnt, O


def pire_baisse(x):
    cs = np.r_[0.0, np.cumsum(x)]
    return (cs - np.maximum.accumulate(cs)).min()


def traite(nom, d, kw, bph, moities, app, test):
    global P
    t1 = time.time()
    P = prepare(d, bph=bph, **kw)
    n, t, ND = P["n"], P["t"], len(P["jours"])
    VAR = [BT] + GRILLE
    INS = {nm: instants(v) for nm, v in VAR}
    tous = sorted(set((int(i), si) for q, _ in INS.values() for i in q for si in (0, 1)))
    with Pool(4) as po:
        res = po.map(panier, tous, chunksize=256)
    CA = {k: dict(i=k[0], qx=r[0], g3=r[1], g1=r[2], mae=r[3], stopi=r[4], ent=r[5], st=r[7], s=r[8]) for k, r in zip(tous, res)}
    print("\n=== %s : %d bougies, %d paniers possibles precalcules en %.0f s" % (nom, n, len(tous), time.time() - t1))
    rng = np.random.default_rng(GRAINE)
    mois_j = P["jours"].to_period("M")
    lignes, SER = [], {}

    def serie(cles):
        x = np.zeros(ND)
        for k in cles:
            b = CA[k]
            if "jd" not in b:
                b["jd"], b["ji"] = marque(b)
            np.add.at(x, b["jd"], b["ji"])
        return x
    for nm, v in VAR:
        q, s = INS[nm]
        K = len(q)
        EX = np.array([[CA[(int(i), 0)]["qx"], CA[(int(i), 1)]["qx"]] for i in q]).reshape(K, 2)
        G = np.array([[CA[(int(i), 0)]["g3"], CA[(int(i), 1)]["g3"]] for i in q]).reshape(K, 2)
        grp = (t[q] >= COUPE).astype(int) if moities else np.zeros(K, int)
        tr, cr, O = rejoue(q, EX, G, s[None, :], grp, 2)
        ta, ca, Oa = rejoue(q, EX, G, np.zeros((1, K), int), grp, 2)
        th, ch, _ = rejoue(q, EX, G, rng.integers(0, 2, size=(NT, K)), grp, 2)
        pris = [(int(i), int(z)) for i, z, o in zip(q, s, O[0]) if o]
        SER[nm] = serie(pris)
        if nm == BT[0]:
            SER["achat"] = serie([(int(i), 0) for i, o in zip(q, Oa[0]) if o])
        mae = np.array([CA[k]["mae"] for k in pris]); sti = np.array([CA[k]["stopi"] for k in pris])
        T, Ta, Th = tr[0].sum(), ta[0].sum(), th.sum(1)
        L = dict(jeu=nom, variante=nm, instants=K, paniers=int(cr[0].sum()), total_R=T, R_panier=T / max(cr[0].sum(), 1),
                 pire_baisse_jour_R=pire_baisse(SER[nm]), mae_med=np.median(mae), mae_p75=np.percentile(mae, 75),
                 pct_stop_init=100 * np.nanmean(sti), hasard_moy=Th.mean(), p_hasard=(1 + (Th >= T).sum()) / (NT + 1),
                 achat_memes_instants=Ta, ecart_achat=T - Ta)
        if moities:
            for h in (0, 1):
                L["total_m%d" % (h + 1)] = tr[0, h]; L["paniers_m%d" % (h + 1)] = cr[0, h]
                L["R_panier_m%d" % (h + 1)] = tr[0, h] / max(cr[0, h], 1)
                L["p_hasard_m%d" % (h + 1)] = (1 + (th[:, h] >= tr[0, h]).sum()) / (NT + 1)
                L["achat_m%d" % (h + 1)] = ta[0, h]
        lignes.append(L)
    ref = SER[BT[0]]; dref = pire_baisse(ref)
    for L in lignes:
        L["fa"] = dref / L["pire_baisse_jour_R"] if L["pire_baisse_jour_R"] < 0 else 1.0
        L["risque_egal_R"] = L["fa"] * L["total_R"]
    fa_achat = dref / pire_baisse(SER["achat"])
    # ---------------------------------------------------------------- walk-forward
    MO = mois_j.unique()
    nomsg = [nm for nm, _ in GRILLE]
    wf, choix = [], []
    m = app
    while m < len(MO):
        ma = (mois_j >= MO[m - app]) & (mois_j <= MO[m - 1])
        mt = (mois_j >= MO[m]) & (mois_j <= MO[min(m + test, len(MO)) - 1])
        ra = pire_baisse(ref[ma])
        crit = {k: SER[k][ma].sum() / max(-pire_baisse(SER[k][ma]), 1e-9) for k in nomsg}
        best = max(nomsg, key=lambda k: crit[k])
        fa = ra / pire_baisse(SER[best][ma]) if pire_baisse(SER[best][ma]) < 0 else 1.0
        pa = pire_baisse(SER["achat"][ma]); fac = ra / pa if pa < 0 else 1.0
        wf.append((MO[m], fa * SER[best][mt].sum(), ref[mt].sum(), fac * SER["achat"][mt].sum()))
        choix.append(best)
        m += test
    W = pd.DataFrame(wf, columns=["debut_test", "choisi", "bt_or", "achat"])
    fq = pd.Series(choix).value_counts()
    # ---------------------------------------------------------------- White
    Dm = np.column_stack([L["fa"] * SER[L["variante"]] - ref for L in lignes[1:]])
    kb, pw = BR.white(Dm)
    print("%-36s %5s %4s %7s %6s %7s %6s %5s %5s %5s %7s %6s %7s" % ("variante", "inst.", "pan", "brut R", "fa", "egal R", "R/pan",
          "MAE", "MAE75", "%stop", "hasard", "p", "achat=t"))
    for L in lignes:
        print("%-36s %5d %4d %+7.1f %6.2f %+7.1f %+6.3f %5.2f %5.2f %5.1f %+7.1f %6.4f %+7.1f" % (
            L["variante"][:36], L["instants"], L["paniers"], L["total_R"], L["fa"], L["risque_egal_R"], L["R_panier"],
            L["mae_med"], L["mae_p75"], L["pct_stop_init"], L["hasard_moy"], L["p_hasard"], L["achat_memes_instants"])
              + ("   moities %+6.1f (p %.3f) / %+6.1f (p %.3f)" % (L["total_m1"], L["p_hasard_m1"], L["total_m2"], L["p_hasard_m2"]) if moities else ""))
    print("Toujours acheteur + pyramide aux heures de bt_or : %+.1f R brut, fa %.2f -> %+.1f R a risque egal"
          % (lignes[0]["achat_memes_instants"], fa_achat, fa_achat * lignes[0]["achat_memes_instants"]))
    print("White (N = %d, variante x fa - bt_or) : meilleure %s, p corrige = %.3f" % (len(GRILLE), nomsg[kb], pw))
    print("Walk-forward %d/%d mois, %d fenetres de test (%s -> %s) : choisi %+.1f R ; bt_or %+.1f R ; toujours acheteur + pyr. %+.1f R"
          % (app, test, len(W), W.debut_test.iloc[0], MO[-1], W.choisi.sum(), W.bt_or.sum(), W.achat.sum()))
    print("  choix : " + " ; ".join("%s x%d" % (k, v) for k, v in fq.items()))
    print("  fenetres gagnees contre bt_or %d/%d, contre achat %d/%d" % ((W.choisi > W.bt_or).sum(), len(W), (W.choisi > W.achat).sum(), len(W)))
    for k, w in W.iterrows():
        lignes.append(dict(jeu=nom, variante="walk-forward test %s" % w.debut_test, total_R=w.choisi, wf_bt_or=w.bt_or,
                           wf_achat=w.achat, wf_choix=choix[k]))
    lignes.append(dict(jeu=nom, variante="walk-forward total", total_R=W.choisi.sum(), wf_bt_or=W.bt_or.sum(),
                       wf_achat=W.achat.sum(), wf_choix=fq.index[0], p_white=pw, fa=fa_achat))
    print("Duree du jeu %.0f s" % (time.time() - t1))
    return lignes, dict(wf=W.choisi.sum(), wfb=W.bt_or.sum(), wfa=W.achat.sum(), pw=pw, top=fq.index[0])


if __name__ == "__main__":
    a5, b5 = BR.charge("xau_m5_2025a"), BR.charge("xau_m5_90k")
    d5 = pd.concat([a5, b5[b5.heure > a5.heure.iloc[-1]]], ignore_index=True)
    dh = BR.charge("xau_h1_50k")
    dh = dh[dh.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
    Lh, Vh = traite("or H1", dh, dict(span=48, heures=BJ.H_H1, debut=60), 1, True, 12, 3)
    L5, V5 = traite("or M5", d5, dict(span=576, heures=BR.H_M5, debut=600), 12, False, 6, 1)
    T = pd.DataFrame(Lh + L5)
    top = T[(T.jeu == "or H1") & (T.variante == Vh["top"])].iloc[0]; bt = T[(T.jeu == "or H1") & (T.variante == BT[0])].iloc[0]
    wf_ok = Vh["wf"] > max(Vh["wfb"], Vh["wfa"]) and V5["wf"] > max(V5["wfb"], V5["wfa"])
    autres = (Vh["pw"] < 0.10, top.p_hasard_m1 < 0.10 and top.p_hasard_m2 < 0.10,
              top.mae_med < bt.mae_med or top.pct_stop_init < bt.pct_stop_init)
    v = "TIENT" if wf_ok and all(autres) else ("PRESQUE" if wf_ok else "NE TIENT PAS")
    print("\nVERDICT : %s (walk-forward bat bt_or et achat sur H1 et M5 : %s ; White H1 < 0,10 : %s ; p hasard 2 moities "
          "(%s) : %s ; MAE ou %% stop meilleur : %s)" % (v, wf_ok, autres[0], Vh["top"], autres[1], autres[2]))
    T.round(4).to_csv(os.path.join(ICI, "donnees", "entree_moment.csv"), index=False)
    print("Duree totale %.0f s. Ecrit donnees/entree_moment.csv (%d lignes)." % (time.time() - T00, len(T)))
