"""Banc ENTREE 5 : un stop initial plus serre (meme risque en $, donc plus de taille) fait-il monter le gain par R ?
(PRIORITES 22/11 « bt_or doit mieux entrer en position », point 5 ; compte DEMO, aucun ordre.)
Mecanique bt_or (banc_bt_regulier.simule) gardee : memes heures d'entree, meme sens (cloture contre EMA 2 jours), un
panier par cote, ajouts a la cloture dans le sens du prix (niveau saute au-dela d'un demi-pas), 3 positions au plus,
sortie de tout le panier au stop suiveur (recul depuis le meilleur prix), spread reel (memes conventions que BR.simule).
Seuls changent : la distance du stop initial A x ATR jour 20 j, le suiveur et le pas de pyramide.
1 R = perte d'UNE position au stop initial de SON panier (A x ATR) : a risque egal en $, la taille est 0,667/A fois
celle de bt_or ; le spread pese donc (0,667/A) fois plus en R.
Grille FIXEE AVANT execution (15 regles x 2 sens = 30 variantes ; N = 29 contre bt_or, qui est la regle 0,667/i/fixe) :
  A dans {0,25 ; 0,4 ; 0,5 ; 0,667 (actuel) ; 1,0} ATR ;
  suiveur (i) = meme multiple A tout du long ;
  suiveur (ii) = A tant que le meilleur prix n'a pas avance de 1 R (A x ATR) depuis la cloture d'ouverture, puis
       0,667 ATR, a CLIQUET (le niveau ne recule jamais : max(niveau au passage, meilleur - 0,667 ATR)) ; seulement pour
       A < 0,667 (0,25 / 0,4 / 0,5) ;
  pas de pyramide : fixe 0,25 ATR, ou proportionnel au stop (0,25 x A / 0,667) ; un seul pas pour A = 0,667 ;
  -> (i) : 0,25f 0,25p 0,4f 0,4p 0,5f 0,5p 0,667 1,0f 1,0p (9) ; (ii) : 0,25f 0,25p 0,4f 0,4p 0,5f 0,5p (6) ;
  sens : bt_or (EMA) et « toujours acheteur » (reference toujours acheteur + pyramide 0,667 : +243,7 R en H1).
Convention intra-bougie pessimiste (celle de BR.simule) : a chaque bougie le stop est teste AVANT la mise a jour du
meilleur prix (un aller-retour dans la bougie sort au stop) ; ajouts a la cloture apres. Gain compte a la SORTIE ;
panier jamais sorti : non compte. Jeux : or H1 08/2022-11/2026 (span 48, heures banc_jumeau.H_H1, debut 60) et ses deux
moities par date d'ouverture (< / >= 01/10/2024) ; or M5 18 mois (xau_m5_2025a + xau_m5_90k).
Mesures (consignes communes) : paniers, total R brut, R/panier, spread paye en R par panier (entree de chaque position,
plus rachat a l'ask des ventes), MAE = excursion defavorable max depuis la 1re entree (bougie de sortie bornee au
niveau de sortie) en R (mediane, 75e centile) et en ATR, % de paniers « stop initial » (perte >= 1 R sur la 1re
position avant tout gain de 1 R, meme bougie -> perte) ; courbe JOURNALIERE marquee (latent a la cloture du dernier
bougie du jour, achat au bid, vente a l'ask) -> pire baisse ; a risque egal : x fa = pire baisse bt_or / pire baisse.
Contre le hasard : 1000 tirages du sens aux memes heures d'entree (graine 2211, memes tirages pour toutes les regles,
blocage un panier par cote compris) : p = (1 + nb tirages >= total) / 1001, sur H1 complet et chaque moitie, et M5.
Difference avec toujours acheteur (meme regle de stop) et avec la reference toujours acheteur + pyramide 0,667.
Walk-forward : H1 12 mois / 3, M5 6 / 1 ; parmi les 30, choix au meilleur gain / pire baisse d'apprentissage, test x fa
d'apprentissage ; compare hors echantillon a bt_or (fa = 1) et a toujours acheteur 0,667 x son fa d'apprentissage.
White (BR.white, bootstrap stationnaire blocs 5 j, 2000) sur jours x 29 variantes (serie x fa - bt_or), par jeu.
Controle de granularite : M1 3 mois (xau_m1_90k) contre M5 sur les memes entrees (heure, prix, ATR et sens pris en M5 ;
chemin en M1 ou en M5), regles 0,25 et 0,4 (i et ii, pas fixe) et 0,667, sens bt_or.
VERDICT fixe d'avance (consignes) : TIENT = la variante choisie en walk-forward bat bt_or ET toujours acheteur +
pyramide hors echantillon a risque egal sur H1 ET M5, White H1 < 0,10, p contre le hasard < 0,10 sur CHACUNE des deux
moities H1 (variante la plus choisie en H1) et MAE mediane (en ATR, le R changeant d'unite) ou % stop initial meilleur
que bt_or ; PRESQUE = walk-forward du bon cote sur les deux jeux mais un autre critere manque ; sinon NE TIENT PAS.
Controle : la regle 0,667/i/fixe au sens bt_or redonne banc_decompose_bt / BR.simule (H1 956 paniers +153,4 R ;
M5 295 paniers +114,1 R) panier par panier.
Ecrit donnees/entree_stop.csv. Usage : python3 banc_entree_stop.py
"""
import os, time, warnings, multiprocessing as mp
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_bt_regulier as BR
import banc_jumeau as BJ

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
NT, GRAINE = 1000, 2211
COUPE = pd.Timestamp("2024-10-01").timestamp()
S0 = BR.STOP
REGLES = ([("i", a, p) for a, ps in ((0.25, "fp"), (0.4, "fp"), (0.5, "fp"), (S0, "f"), (1.0, "fp")) for p in ps]
          + [("ii", a, p) for a in (0.25, 0.4, 0.5) for p in "fp"])
nom_regle = lambda r: "%s %s %s" % ("%.3g" % r[1] if r[1] != S0 else "0.667", r[0], "pas fixe" if r[2] == "f" else "pas prop")
G = {}   # tableaux du jeu en cours (herites par les processus fils)


def prepare(d, span, heures, debut):
    c, hi, lo, sp, t = (d[x].values for x in ("cloture", "haut", "bas", "sp", "heure"))
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    n = len(c)
    ik = np.array([i for i in range(debut, n) if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0])
    jours, dpos = np.unique(jour, return_inverse=True)
    finj = np.r_[jour[1:] != jour[:-1], True]
    return dict(c=c.tolist(), hi=hi.tolist(), lo=lo.tolist(), sp=sp.tolist(), finj=finj.tolist(), dpos=dpos.tolist(), n=n,
                t=t, ik=ik, atr=atr, signal=np.where(c[ik] > ema[ik], 0, 1), jours=jours, dposa=dpos)


def panier(A, i, s, stop, pas, d2, nmax, c0=None, sp0=None):
    """Un panier ouvert a la cloture de la bougie i (sens s). d2 = distance du suiveur apres +1 R (None = suiveur (i)).
    Rend (bougie de sortie, gain 3 pos en R, gain 1 pos, MAE en R, stop initial touche, spread paye en R, positions,
    [(jour, latent R)])."""
    c, hi, lo, sp, finj, dpos = A["c"], A["hi"], A["lo"], A["sp"], A["finj"], A["dpos"]
    ci = c[i] if c0 is None else c0; spi = sp[i] if sp0 is None else sp0
    e0 = ci + spi if s > 0 else ci - spi
    e = [e0]; cout = spi
    meilleur, prochain, dist = ci, ci + s * pas, stop
    cliq = -1e18 if s > 0 else 1e18
    passe = d2 is None
    mae, drap, decide, lat = 0.0, 0, False, []
    for q in range(i + 1, nmax):
        niveau = meilleur - s * dist
        niveau = max(niveau, cliq) if s > 0 else min(niveau, cliq)
        if s > 0:
            touche = lo[q] <= niveau; adv = e0 - (niveau if touche else lo[q]); fav = hi[q] - e0
        else:
            touche = hi[q] + sp[q] >= niveau; adv = (niveau if touche else hi[q] + sp[q]) - e0; fav = e0 - lo[q] - sp[q]
        if adv > mae:
            mae = adv
        if not decide:
            if adv >= stop - 1e-12:
                drap, decide = 1, True
            elif fav >= stop and not touche:
                decide = True
        if touche:
            g3 = sum(s * (niveau - x) for x in e) / stop
            if s < 0:
                cout += len(e) * sp[q]
            return q, g3, s * (niveau - e0) / stop, mae / stop, drap, cout / stop, len(e), lat
        meilleur = max(meilleur, hi[q]) if s > 0 else min(meilleur, lo[q])
        if not passe and s * (meilleur - ci) >= stop:
            passe = True
            cliq = meilleur - s * stop
            dist = d2
        while len(e) < BR.MAXP and s * (c[q] - prochain) >= 0:
            if s * (c[q] - prochain) <= 0.5 * pas:
                e.append(c[q] + (sp[q] if s > 0 else -sp[q])); cout += sp[q]
            prochain += s * pas
        if finj[q]:
            mk = c[q] if s > 0 else c[q] + sp[q]
            lat.append((dpos[q], sum(s * (mk - x) for x in e) / stop))
    return nmax, 0.0, 0.0, mae / stop, drap, cout / stop, len(e), lat


def precalc(regle):
    mode, a, p = regle
    A = G; ik, atr, n = A["ik"], A["atr"], A["n"]
    K = len(ik)
    EX = np.full((K, 2), n, int); G3, G1, MAE, DR, CO, NP = (np.zeros((K, 2)) for _ in range(6))
    rb, rd, rv = [], [], []
    for k, i in enumerate(ik):
        for si, s in ((0, 1), (1, -1)):
            stop = a * atr[i]
            pas = (BR.PAS if p == "f" else BR.PAS * a / S0) * atr[i]
            d2 = S0 * atr[i] if mode == "ii" else None
            q, g3, g1, mae, dr, co, npos, lat = panier(A, i, s, stop, pas, d2, n)
            EX[k, si], G3[k, si], G1[k, si], MAE[k, si], DR[k, si], CO[k, si], NP[k, si] = q, g3, g1, mae, dr, co, npos
            for dj, v in lat:
                rb.append(2 * k + si); rd.append(dj); rv.append(v)
    return dict(EX=EX, G3=G3, G1=G1, MAE=MAE, DR=DR, CO=CO, NP=NP, MAEatr=MAE * a,
                rb=np.array(rb, int), rd=np.array(rd, int), rv=np.array(rv))


def rejoue(ik, EX, n, S):
    N, K = S.shape
    bu = np.zeros((N, 2), int); r = np.arange(N)
    O = np.zeros((N, K), bool)
    for k in range(K):
        sd = S[:, k]
        ok = bu[r, sd] <= ik[k]
        O[ok, k] = True
        bu[r[ok], sd[ok]] = EX[k, sd[ok]]
    X = EX[np.arange(K)[None, :], S]
    O &= X < n
    return O, X


def courbe(P, O, X, s, B):
    """Serie journaliere marquee (increments) pour une suite de sens s (K,) ; O, X de rejoue (1 ligne)."""
    nj = len(B["jours"]); K = len(s)
    real = np.zeros(nj)
    g = P["G3"][np.arange(K), s]
    np.add.at(real, B["dposa"][np.minimum(X, B["n"] - 1)][O], g[O])
    ouvert = np.zeros(2 * K, bool); ouvert[(2 * np.arange(K) + s)[O]] = True
    m = ouvert[P["rb"]]
    lat = np.zeros(nj); np.add.at(lat, P["rd"][m], P["rv"][m])
    E = np.cumsum(real) + lat
    return pd.Series(np.diff(np.r_[0.0, E]), index=pd.to_datetime(B["jours"] * 86400, unit="s"))


def pire(x):
    e = np.r_[0.0, np.cumsum(np.asarray(x))]
    return float((e - np.maximum.accumulate(e)).min())


def traite(nom, d, kw, L_app, L_test, decoupe):
    t1 = time.time()
    B = prepare(d, **kw)
    G.clear(); G.update(B)
    with mp.get_context("fork").Pool(4) as pool:
        PR = pool.map(precalc, REGLES)
    ik, n, K = B["ik"], B["n"], len(B["ik"])
    t_ouv = B["t"][ik]
    print("\n=== %s : %d heures d'entree valides, %d regles precalculees en %.0f s" % (nom, K, len(REGLES), time.time() - t1))
    rng = np.random.default_rng(GRAINE)
    SH = rng.integers(0, 2, size=(NT, K))
    sens = {"bt_or": B["signal"], "achat": np.zeros(K, int)}
    masques = [("complet", np.ones(K, bool))]
    if decoupe:
        masques += [("2022-08->2024-09", t_ouv < COUPE), ("2024-10->2026-11", t_ouv >= COUPE)]
    V, SER = [], {}
    hasard = {}
    for r, P in zip(REGLES, PR):
        Oh, Xh = rejoue(ik, P["EX"], n, SH)
        gh = np.where(Oh, P["G3"][np.arange(K)[None, :], SH], 0.0)
        hasard[r] = (Oh, gh)
        for sn, s in sens.items():
            O, X = rejoue(ik, P["EX"], n, s[None, :])
            O, X = O[0], X[0]
            idx = np.arange(K)
            g = P["G3"][idx, s]
            lab = "%s | %s" % ("bt_or" if sn == "bt_or" else "toujours acheteur", nom_regle(r))
            SER[lab] = courbe(P, O, X, s, B)
            row = dict(jeu=nom, variante=lab, sens=sn, regle=nom_regle(r))
            for mn, m in masques:
                om = O & m
                tot = g[om].sum()
                th = (gh * m[None, :]).sum(1)
                row["pan_" + mn] = int(om.sum()); row["tot_" + mn] = tot
                row["Rpan_" + mn] = tot / max(om.sum(), 1)
                row["p_hasard_" + mn] = (1 + (th >= tot - 1e-9).sum()) / (NT + 1)
                row["hasard_moy_" + mn] = th.mean()
            row.update(spread_R_pan=P["CO"][idx, s][O].mean(), npos_moy=P["NP"][idx, s][O].mean(),
                       mae_med_R=np.median(P["MAE"][idx, s][O]), mae_p75_R=np.percentile(P["MAE"][idx, s][O], 75),
                       mae_med_atr=np.median(P["MAEatr"][idx, s][O]), pct_stop_init=100 * P["DR"][idx, s][O].mean(),
                       R_pan_1pos=P["G1"][idx, s][O].mean(), pct_perdants=100 * (g[O] < 0).mean())
            V.append(row)
            if sn == "bt_or" and r == ("i", S0, "f"):
                ref = BR.simule(d, **kw)
                mine = sorted(zip(B["t"][ik[O]], np.round(g[O], 9))); leur = sorted(zip(ref.t0.values, np.round(ref.g.values, 9)))
                print("Controle 0,667/i/fixe sens bt_or : %d paniers %+.1f R ; BR.simule %d paniers %+.1f R ; identiques panier par panier : %s"
                      % (O.sum(), g[O].sum(), len(ref), ref.g.sum(), mine == leur))
    T = pd.DataFrame(V)
    labs = list(T.variante)
    BT, AB = "bt_or | 0.667 i pas fixe", "toujours acheteur | 0.667 i pas fixe"
    X = pd.DataFrame(SER)
    dd = {k: pire(X[k].values) for k in labs}
    T["pire_baisse"] = T.variante.map(dd)
    T["fa"] = dd[BT] / T.pire_baisse
    T["tot_risque_egal"] = T.tot_complet * T.fa
    T["tot_marque"] = T.variante.map(X.sum())
    T["gain_baisse"] = -T.tot_marque / T.pire_baisse
    tab = T.set_index("variante")
    T["moins_achat_meme_regle"] = [tab.tot_complet[v] - tab.tot_complet["toujours acheteur | " + v.split(" | ")[1]] for v in labs]
    T["moins_achat_ref_risque_egal"] = T.tot_risque_egal - tab.tot_risque_egal[AB]
    # ---------------------------------------------- White
    autres = [v for v in labs if v != BT]
    Dm = np.column_stack([X[v].values * tab.fa[v] - X[BT].values for v in autres])
    kb, pw = BR.white(Dm)
    print("White (N = %d contre bt_or, series a risque egal) : meilleur %s, p corrige = %.3f" % (len(autres), autres[kb], pw))
    # ---------------------------------------------- walk-forward
    mois = X.index.to_period("M"); MO = mois.unique()
    oos, ob, oa, ch = [], [], [], []
    for i0 in range(L_app, len(MO), L_test):
        app = (mois >= MO[i0 - L_app]) & (mois <= MO[i0 - 1]); te = (mois >= MO[i0]) & (mois <= MO[min(i0 + L_test, len(MO)) - 1])
        db = pire(X[BT][app].values)
        sc = {v: X[v][app].sum() / max(-pire(X[v][app].values), 1e-9) for v in labs}
        v = max(sc, key=sc.get)
        fa = db / min(pire(X[v][app].values), -1e-9)
        oos.append(X[v][te] * fa); ob.append(X[BT][te]); oa.append(X[AB][te] * db / min(pire(X[AB][app].values), -1e-9)); ch.append(v)
    o, b_, a_ = pd.concat(oos), pd.concat(ob), pd.concat(oa)
    fq = pd.Series(ch).value_counts()
    wf = dict(choisi=o.sum(), bt=b_.sum(), ab=a_.sum(), pb_choisi=pire(o.values), pb_bt=pire(b_.values), pb_ab=pire(a_.values),
              fen=len(ch), choix=fq, debut=o.index[0].date(), fin=o.index[-1].date())
    print("Walk-forward %d/%d, %d fenetres (%s -> %s) : choisi %+.1f R (pire baisse %+.1f) ; bt_or %+.1f (%+.1f) ; "
          "toujours acheteur 0,667 a risque egal %+.1f (%+.1f)" % (L_app, L_test, len(ch), wf["debut"], wf["fin"], o.sum(),
                                                                   wf["pb_choisi"], b_.sum(), wf["pb_bt"], a_.sum(), wf["pb_ab"]))
    print("  choix : " + " ; ".join("%s %d" % (k, v) for k, v in fq.items()))
    # ---------------------------------------------- affichage
    hh = [m for m, _ in masques]
    print("%-46s %5s %7s %7s %6s %6s %5s %5s %5s %5s %6s %5s" % ("variante", "pan", "brut R", "R eg.", "R/pan", "sprd", "MAEm", "MAEp75",
                                                              "MAEat", "%stop", "p has", "fa") + "".join(" %16s" % m[:16] for m in hh[1:]))
    for _, r in T.iterrows():
        print("%-46s %5d %+7.1f %+7.1f %+6.3f %6.3f %5.2f %5.2f %5.2f %5.1f %6.4f %5.2f" % (
            r.variante, r.pan_complet, r.tot_complet, r.tot_risque_egal, r.Rpan_complet, r.spread_R_pan, r.mae_med_R, r.mae_p75_R,
            r.mae_med_atr, r.pct_stop_init, r.p_hasard_complet, r.fa) + "".join(
            " %+7.1f p%.4f" % (r["tot_" + m], r["p_hasard_" + m]) for m in hh[1:]))
    print("hasard 0,667 (moyenne des %d tirages) : %s" % (NT, " ; ".join(
        "%s %+.1f R / %.0f paniers" % (mn, (hasard[("i", S0, "f")][1] * m[None, :]).sum(1).mean(),
                                       (hasard[("i", S0, "f")][0] & m[None, :]).sum(1).mean()) for mn, m in masques)))
    Oh, gh = hasard[("i", S0, "f")]
    hz = dict(jeu=nom, variante="hasard | 0.667 i pas fixe (moyenne des tirages)")
    for mn, m in masques:
        hz["tot_" + mn] = (gh * m[None, :]).sum(1).mean(); hz["pan_" + mn] = (Oh & m[None, :]).sum(1).mean()
        hz["Rpan_" + mn] = hz["tot_" + mn] / hz["pan_" + mn]
    T = pd.concat([T, pd.DataFrame([hz])], ignore_index=True)
    T["white_p_jeu"] = pw; T["white_meilleur"] = autres[kb]
    T["wf_choisi"] = wf["choisi"]; T["wf_bt_or"] = wf["bt"]; T["wf_achat_ref"] = wf["ab"]
    T["wf_plus_choisi"] = fq.index[0]
    print("  (jeu traite en %.0f s)" % (time.time() - t1))
    return T, wf, pw, fq.index[0]


def controle_grain(nomc, nomf, Bc, df, off, gros, regles):
    """Memes entrees que le jeu grossier Bc (heure, prix, spread, ATR, sens pris dans Bc) ; chemin du panier rejoue en
    bougies grossieres ou en bougies fines df (bougie fine d'entree = derniere de la bougie grossiere : heure + off)."""
    tf = df.heure.values
    Af = dict(c=df.cloture.tolist(), hi=df.haut.tolist(), lo=df.bas.tolist(), sp=df.sp.tolist(),
              finj=[False] * len(df), dpos=[0] * len(df))
    fin = tf[-1]
    nc = int(np.searchsorted(Bc["t"], fin - gros, side="right"))
    posf = {t: j for j, t in enumerate(tf)}
    sel = [(k, i) for k, i in enumerate(Bc["ik"]) if tf[0] + 86400 <= Bc["t"][i] and i < nc and (Bc["t"][i] + off) in posf]
    egal = np.mean([abs(Bc["c"][i] - Af["c"][posf[Bc["t"][i] + off]]) < 0.051 for _, i in sel])
    print("\n=== Controle %s contre %s (%s -> %s) : %d heures d'entree ; cloture %s = cloture %s a 5 cents pres dans %.0f %% des cas"
          % (nomf, nomc, pd.to_datetime(tf[0], unit="s").date(), pd.to_datetime(fin, unit="s").date(), len(sel), nomf, nomc, 100 * egal))
    rows = []
    for sn in ("bt_or", "achat"):
        for regle in regles:
            mode, a, _ = regle
            res = {}
            for jeu in (nomc, nomf):
                bu = {1: -1, -1: -1}; out = []
                for k, i in sel:
                    s = 1 if (sn == "achat" or Bc["signal"][k] == 0) else -1
                    if Bc["t"][i] < bu[s]:
                        continue
                    stop, pas = a * Bc["atr"][i], BR.PAS * Bc["atr"][i]
                    d2 = S0 * Bc["atr"][i] if mode == "ii" else None
                    if jeu == nomc:
                        q, g3, g1, mae, dr, co, npos, _ = panier(Bc, i, s, stop, pas, d2, nc)
                        tq = Bc["t"][q] if q < nc else None
                    else:
                        j = posf[Bc["t"][i] + off]
                        q, g3, g1, mae, dr, co, npos, _ = panier(Af, j, s, stop, pas, d2, len(tf), c0=Bc["c"][i], sp0=Bc["sp"][i])
                        tq = tf[q] // gros * gros if q < len(tf) else None
                    if tq is None:
                        bu[s] = 1e18
                        continue
                    bu[s] = tq
                    out.append((g3, mae, dr, co))
                o = np.array(out)
                res[jeu] = o
                rows.append(dict(jeu="controle %s/%s" % (nomf, nomc), variante="%s | %s" % ("bt_or" if sn == "bt_or" else "toujours acheteur", nom_regle(regle)),
                                 chemin=jeu, pan_complet=len(o), tot_complet=o[:, 0].sum(), Rpan_complet=o[:, 0].mean(),
                                 mae_med_R=np.median(o[:, 1]), pct_stop_init=100 * o[:, 2].mean(), spread_R_pan=o[:, 3].mean()))
            print("  %-6s %-18s %s : %4d paniers %+7.1f R (%+.3f R/pan, %%stop %4.1f) | %s : %4d paniers %+7.1f R (%+.3f R/pan, %%stop %4.1f)"
                  % (sn, nom_regle(regle), nomc, len(res[nomc]), res[nomc][:, 0].sum(), res[nomc][:, 0].mean(), 100 * res[nomc][:, 2].mean(),
                     nomf, len(res[nomf]), res[nomf][:, 0].sum(), res[nomf][:, 0].mean(), 100 * res[nomf][:, 2].mean()))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    print("Grille fixee d'avance : %d regles x 2 sens = %d variantes (N = %d contre bt_or)." % (len(REGLES), 2 * len(REGLES), 2 * len(REGLES) - 1))
    a5, b5 = BR.charge("xau_m5_2025a"), BR.charge("xau_m5_90k")
    d5 = pd.concat([a5, b5[b5.heure > a5.heure.iloc[-1]]], ignore_index=True)
    dh = BR.charge("xau_h1_50k")
    dh = dh[dh.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
    TH, WH, PWH, VH = traite("or H1", dh, dict(span=48, heures=BJ.H_H1, debut=60), 12, 3, True)
    T5, W5, PW5, V5 = traite("or M5", d5, dict(span=576, heures=BR.H_M5, debut=600), 6, 1, False)
    RC = [("i", 0.25, "f"), ("ii", 0.25, "f"), ("i", 0.4, "f"), ("ii", 0.4, "f"), ("i", 0.5, "f"), ("ii", 0.5, "f"), ("i", S0, "f")]
    TC = controle_grain("M5", "M1", prepare(d5, 576, BR.H_M5, 600), BR.charge("xau_m1_90k"), 240, 300, RC)
    TC2 = controle_grain("H1", "M5", prepare(dh, 48, BJ.H_H1, 60), d5, 3300, 3600, RC)
    T = pd.concat([TH, T5, TC, TC2], ignore_index=True)
    T.round(4).to_csv(os.path.join(ICI, "donnees", "entree_stop.csv"), index=False)
    # ---------------------------------------------- verdict
    h = TH.set_index("variante")
    bt = h.loc["bt_or | 0.667 i pas fixe"]
    wf_ok = all(w["choisi"] > w["bt"] and w["choisi"] > w["ab"] for w in (WH, W5))
    v = h.loc[VH]
    p_moit = (v["p_hasard_2022-08->2024-09"] < 0.10) and (v["p_hasard_2024-10->2026-11"] < 0.10)
    mae_ok = v.mae_med_atr < bt.mae_med_atr or v.pct_stop_init < bt.pct_stop_init
    print("\n=== Verdict : walk-forward du bon cote H1 (%+.1f contre bt_or %+.1f / achat %+.1f) et M5 (%+.1f contre %+.1f / %+.1f) : %s ;"
          % (WH["choisi"], WH["bt"], WH["ab"], W5["choisi"], W5["bt"], W5["ab"], wf_ok))
    print("  White H1 p = %.3f (M5 %.3f) ; variante la plus choisie H1 : %s, p hasard moities %.4f / %.4f ; MAE ATR %.2f (bt_or %.2f), "
          "%%stop %.1f (bt_or %.1f)" % (PWH, PW5, VH, v["p_hasard_2022-08->2024-09"], v["p_hasard_2024-10->2026-11"], v.mae_med_atr,
                                         bt.mae_med_atr, v.pct_stop_init, bt.pct_stop_init))
    verdict = "TIENT" if (wf_ok and PWH < 0.10 and p_moit and mae_ok) else ("PRESQUE" if wf_ok else "NE TIENT PAS")
    print("  VERDICT : %s" % verdict)
    print("Duree totale %.0f s. Ecrit donnees/entree_stop.csv (%d lignes)." % (time.time() - T00, len(T)))
