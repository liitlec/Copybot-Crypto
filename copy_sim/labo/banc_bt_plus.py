"""Banc BT+ : bt_or qui AJOUTE PLUS FORT quand ca marche (or XAUUSD, compte demo).
Mecanique bt_or inchangee (banc_bt_regulier.simule) : sens = cloture contre l'EMA 2 jours, entree aux heures fixes,
ajouts dans le sens du prix tous les 0,25 ATR (cloture de bougie, niveau saute au-dela d'un demi-pas), sortie de TOUT
le panier au recul de 0,667 ATR depuis le meilleur prix. Le moment d'ouverture et de sortie des paniers ne depend PAS
des ajouts : tous les paniers sont communs aux variantes, seules les positions ajoutees (nombre, taille) changent.
Grille fixee d'avance, N = 36 = tailles x nombre max x condition :
  tailles de la k-ieme position (k = 0, 1, 2...) : « 1-1-1 » (actuel) ; « 1-2-3 » (1 + k) ; « 1-1,5-2 » (1 + k/2) ;
          temoin decroissant « 1-0,67-0,33 » puis 0,33 (pour verifier que le sens compte) ;
  nombre maximum de positions : 3, 5, 7 (memes pas de 0,25 ATR) ;
  condition d'ajout (evaluee a la cloture de la bougie ou le niveau est franchi ; si elle n'est pas remplie le niveau
          est saute, le suivant est 0,25 ATR plus loin) : « tjrs » (actuel) ; « >1R » = gain latent du panier
          (positions deja ouvertes, tailles comprises, au prix de sortie bid/ask de la cloture) > 1 R ;
          « ATR+ » = ATR jour 20 j courant (celui de la veille, comme partout) > ATR a l'ouverture du panier.
  1-1-1 x 3 x tjrs = bt_or actuel = reference.
Unites : 1 R = perte d'une position de taille 1 au stop initial (0,667 ATR) ; $ = 0,01 lot par unite de taille
(USD = 0,40 $ par bp comme banc_jumeau). Spread reel, meme convention que banc_bt_regulier / banc_jumeau (entree achat
cloture + spread, vente cloture - spread ; sortie au niveau du stop, vente declenchee par haut + spread), sans fuite :
stop avec le meilleur prix d'AVANT la bougie, puis meilleur prix, puis ajouts a la cloture.
Courbe JOURNALIERE marquee a la derniere cloture du jour (gain latent compris, achat au bid, vente a l'ask).
COMPARAISON A RISQUE EGAL : chaque variante est multipliee par un facteur constant (a) fa = pire baisse journaliere de
bt_or / pire baisse de la variante (meme pire baisse) ; (b) fb = ecart-type journalier de bt_or / celui de la variante.
NB : gain/pire baisse, Sharpe, regularite, signes et mois<0 ne dependent pas du facteur ; il fixe les totaux et la
plus grosse perte d'un panier. Mesures : total a risque egal (R, $), mois<0, pire baisse, gain/pire baisse, Sharpe
journalier annualise (x racine 252), regularite = moyenne/ecart-type mensuel, plus grosse perte d'un panier, moities.
Walk-forward (M5 6 -> 1 mois ; H1 12 -> 3 mois) : choix de la variante au meilleur gain/pire baisse d'apprentissage,
facteur fa appris sur l'apprentissage (pire baisse de bt_or / pire baisse de la variante sur l'apprentissage) ;
« du bon cote » = hors echantillon gain/pire baisse > bt_or ET total >= bt_or (memes mois de test).
Essais multiples : bootstrap stationnaire de blocs de PANIERS apparies (blocs moyens 5, 2000 tirages, BR.boot) sur
la difference variante - bt_or de gain/pire baisse par panier clos et de Sharpe par panier ; reality check de White
(max sur les 36) -> p corrige par stat et par jeu ; p retenu par jeu = max(p gain/creux, p Sharpe).
Verdict fixe d'avance : TIENT = une variante a gain/pire baisse ET Sharpe journaliers > bt_or sur M5 ET H1,
walk-forward du bon cote sur les deux, p corrige < 0,05 sur un jeu et < 0,15 sur l'autre ; PRESQUE = descriptif rempli
sur les deux jeux mais p ou walk-forward insuffisant ; sinon NON.
Reutilise banc_bt_regulier (charge, simule, boot) et banc_jumeau (mesure, ratio_mat, sharpe_mat, H_H1).
Controles : la reference redonne banc_bt_regulier.simule panier par panier (295 / ~+114 R M5 ; 956 / ~+153 R H1).
RESULTAT (execution du 18/11/2026, 4 s) : verdict NON. Controles exacts (295 / +114,1 R ; 956 / +153,4 R).
  M5 : ajouter plus fort aide (1-2-3/7/tjrs gain/creux 8,62 contre 6,34, +157 R a risque egal contre +116), mais
  H1 : c'est l'inverse (1-2-3 moyenne 1,80 contre 1-1-1 2,93 ; le temoin decroissant est le meilleur, 4,19 contre 3,66,
  avec Sharpe plus bas). Aucune variante meilleure en gain/creux ET Sharpe sur les deux jeux. Condition « ATR+ » nuit
  partout. Walk-forward : M5 du bon cote (3,77 contre 3,51), H1 non (3,06 contre 7,67). p corrige M5 0,646, H1 0,951.
Ecrit donnees/bt_plus.csv (une ligne par variante et par jeu). Usage : python3 banc_bt_plus.py"""
import os, time, itertools, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_bt_regulier as BR
import banc_jumeau as BJ

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
PAS, STOP = BR.PAS, BR.STOP
USD = 0.40
KMAX = 7
TAILLES = {"1-1-1": [1.0] * KMAX,
           "1-2-3": [1.0 + k for k in range(KMAX)],
           "1-1,5-2": [1.0 + 0.5 * k for k in range(KMAX)],
           "decr": [1.0, 0.67, 0.33] + [0.33] * (KMAX - 3)}
MAXS = (3, 5, 7)
CONDS = ("tjrs", ">1R", "ATR+")
VAR = list(itertools.product(TAILLES, MAXS, CONDS))
NV = len(VAR)
NOMV = ["%s/%d/%s" % v for v in VAR]
REF = VAR.index(("1-1-1", 3, "tjrs"))
SZ = np.array([TAILLES[v[0]] for v in VAR])            # NV x KMAX
MX = np.array([v[1] for v in VAR])
CD = np.array([CONDS.index(v[2]) for v in VAR])


def simule_plus(d, span=576, heures=BR.H_M5, debut=600):
    """Les 36 variantes en une passe. Rend paniers (DataFrame), gains par panier GR, GD (n x NV), courbes ER, ED."""
    c, hi, lo, sp, t = (d[x].values for x in ("cloture", "haut", "bas", "sp", "heure"))
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    fin_j = np.r_[jour[1:] != jour[:-1], True]
    accR, accD = np.zeros(NV), np.zeros(NV)
    P, GR, GD, NP, EQR, EQD, JO = [], [], [], [], [], [], []
    ouvert = {}
    for i in range(debut, len(c)):
        for s in list(ouvert):
            p = ouvert[s]
            niveau = p["meilleur"] - s * p["stop"]
            if (lo[i] <= niveau) if s > 0 else (hi[i] + sp[i] >= niveau):
                g = (p["W"] * s * (niveau - p["E"])).sum(1)
                accR += g / p["stop"]; accD += g * p["usd"]
                P.append((t[p["i"]], t[i], s)); GR.append(g / p["stop"]); GD.append(g * p["usd"]); NP.append(p["n"].copy())
                del ouvert[s]
                continue
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            cand = np.flatnonzero((p["n"] < MX) & (s * (c[i] - p["prochain"]) >= 0))
            x = c[i] if s > 0 else c[i] + sp[i]
            ent = c[i] + (sp[i] if s > 0 else -sp[i])
            for v in cand:
                while p["n"][v] < MX[v] and s * (c[i] - p["prochain"][v]) >= 0:
                    if s * (c[i] - p["prochain"][v]) <= 0.5 * p["pas"]:
                        if CD[v] == 0:
                            ok = True
                        elif CD[v] == 1:
                            ok = (p["W"][v] * s * (x - p["E"][v])).sum() > p["stop"]
                        else:
                            ok = atr[i] > p["atr0"]
                        if ok:
                            k = p["n"][v]; p["E"][v, k] = ent; p["W"][v, k] = SZ[v, k]; p["n"][v] += 1
                    p["prochain"][v] += s * p["pas"]
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if s not in ouvert:
                ent = c[i] + (sp[i] if s > 0 else -sp[i])
                E = np.zeros((NV, KMAX)); W = np.zeros((NV, KMAX)); E[:, 0] = ent; W[:, 0] = SZ[:, 0]
                ouvert[s] = {"i": i, "E": E, "W": W, "n": np.ones(NV, int), "meilleur": c[i], "stop": STOP * atr[i],
                             "pas": PAS * atr[i], "prochain": np.full(NV, c[i] + s * PAS * atr[i]), "atr0": atr[i],
                             "usd": USD * 1e4 / c[i]}
        if fin_j[i]:
            lR, lD = np.zeros(NV), np.zeros(NV)
            for s, p in ouvert.items():
                x = c[i] if s > 0 else c[i] + sp[i]
                v = (p["W"] * s * (x - p["E"])).sum(1)
                lR += v / p["stop"]; lD += v * p["usd"]
            EQR.append(accR + lR); EQD.append(accD + lD); JO.append(jour[i])
    P = pd.DataFrame(P, columns=["t0", "t1", "s"])
    dates = pd.to_datetime(np.array(JO) * 86400, unit="s")
    return P, np.array(GR), np.array(GD), np.array(NP), pd.DataFrame(np.array(EQR), dates), pd.DataFrame(np.array(EQD), dates)


creux = BJ.creux
shj = lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0.0


def jeu(nom, d, kw, L_app, L_test):
    t1 = time.time()
    P, GR, GD, NP, ER, ED = simule_plus(d, **kw)
    ref = BR.simule(d, **kw)
    n = len(P)
    print("\n=== %s : %s -> %s, %d paniers, %d jours (simulation %.0f s)" % (nom, ER.index[0].date(), ER.index[-1].date(), n, len(ER), time.time() - t1))
    print("Controle : reference %+.1f R (%d paniers) ; banc_bt_regulier.simule %d paniers %+.1f R ; identiques panier par panier : %s"
          % (GR[:, REF].sum(), n, len(ref), ref.g.sum(), len(ref) == n and np.allclose(GR[:, REF], ref.g.values)))
    xR, xD = ER.diff().fillna(ER.iloc[0]), ED.diff().fillna(ED.iloc[0])
    mois = xR.index.to_period("M")
    b = BJ.mesure(xR[REF], mois); sd0 = xR[REF].std()
    rows = []
    for v in range(NV):
        a = BJ.mesure(xR[v], mois)
        fa = b["cr"] / a["cr"] if a["cr"] < 0 else 1.0
        fb = sd0 / xR[v].std()
        r = dict(jeu=nom, variante=NOMV[v], tailles=VAR[v][0], max_pos=VAR[v][1], condition=VAR[v][2],
                 pos_moy=NP[:, v].mean(), taille_moy=(SZ[v][None, :] * (np.arange(KMAX)[None, :] < NP[:, v][:, None])).sum(1).mean(),
                 total_R_brut=a["tot"], creux_R_brut=a["cr"], facteur_a=fa, facteur_b=fb,
                 total_R_a=fa * a["tot"], total_usd_a=fa * xD[v].sum(), creux_usd_a=fa * creux(xD[v].values),
                 total_R_b=fb * a["tot"], mois_neg=a["mneg"], mois=a["nm"], gain_creux=a["rap"], sharpe=shj(xR[v]),
                 regularite=a["reg"], pire_panier_R_a=fa * GR[:, v].min(), h1_R_a=fa * a["h1"], h2_R_a=fa * a["h2"])
        rows.append(r)
    T = pd.DataFrame(rows)
    T["d_gc"] = T.gain_creux - T.gain_creux[REF]; T["d_sh"] = T.sharpe - T.sharpe[REF]
    T["bat"] = (T.d_gc > 1e-9) & (T.d_sh > 1e-9)
    # ------------------------------------------------ bootstrap apparie par blocs de paniers, reality check
    I = BR.boot(n)
    pres = {}
    for stat, f in (("gc", BJ.ratio_mat), ("sh", BJ.sharpe_mat)):
        o = f(GR.T); bo = np.stack([f(GR[I, v]) for v in range(NV)])          # NV ; NV x B
        dob = o - o[REF]; dbo = bo - bo[REF]
        V = dob.max(); Vb = (dbo - dob[:, None]).max(0)
        T["p_brut_" + stat] = [(dbo[v] - dob[v] >= dob[v]).mean() if v != REF else np.nan for v in range(NV)]
        kb = int(dob.argmax()); pres[stat] = (NOMV[kb], dob[kb], (Vb >= V).mean())
    print("%-18s %4s %4s %7s %7s %6s %7s %6s %6s %5s %5s %7s %13s %5s %5s" % (
        "variante", "pos", "fa", "totR a", "tot$ a", "totR b", "m<0", "creuxR", "g/cr", "Shrp", "regul", "pirePan", "moities", "pGC", "pSh"))
    for _, r in T.sort_values("gain_creux", ascending=False).iterrows():
        print("%-18s %4.2f %4.2f %+7.1f %+7.0f %+6.1f %3d/%-3d %+6.1f %6.2f %5.2f %5.2f %+7.2f %+6.0f/%+6.0f %5.3f %5.3f%s" % (
            r.variante, r.pos_moy, r.facteur_a, r.total_R_a, r.total_usd_a, r.total_R_b, r.mois_neg, r.mois, r.creux_R_brut * r.facteur_a,
            r.gain_creux, r.sharpe, r.regularite, r.pire_panier_R_a, r.h1_R_a, r.h2_R_a, r.p_brut_gc, r.p_brut_sh,
            "  <- REF" if r.variante == NOMV[REF] else ("  *" if r.bat else "")))
    print("Effet moyen par dimension (moyenne sur les autres ; gain/creux, Sharpe, total R a risque egal a) :")
    for dim in ("tailles", "max_pos", "condition"):
        g = T.groupby(dim)[["gain_creux", "sharpe", "total_R_a"]].mean()
        print("  %-9s " % dim + " | ".join("%s %.2f %.2f %+.1f" % (k, *g.loc[k]) for k in g.index))
    for stat in ("gc", "sh"):
        print("  bootstrap %s : meilleur %s (ecart %+.3f), p corrige (max des 36) %.3f" % (stat, *pres[stat]))
    # ------------------------------------------------ walk-forward
    MO = mois.unique()
    oos, oosb, ch = [], [], []
    for i0 in range(L_app, len(MO), L_test):
        app = (mois >= MO[i0 - L_app]) & (mois <= MO[i0 - 1]); te = (mois >= MO[i0]) & (mois <= MO[min(i0 + L_test, len(MO)) - 1])
        M = [BJ.mesure(xR[v][app], mois[app]) for v in range(NV)]
        v = max(range(NV), key=lambda k: (M[k]["rap"], k == REF))
        fa = M[REF]["cr"] / M[v]["cr"] if M[v]["cr"] < 0 else 1.0
        oos.append(fa * xR[v][te]); oosb.append(xR[REF][te]); ch.append(NOMV[v])
    o, ob = pd.concat(oos), pd.concat(oosb)
    mo = o.index.to_period("M")
    a, bb = BJ.mesure(o, mo), BJ.mesure(ob, mo)
    wf_ok = a["rap"] > bb["rap"] + 1e-9 and a["tot"] >= bb["tot"] - 1e-9
    fq = pd.Series(ch).value_counts()
    print("Walk-forward %d -> %d mois, %d fenetres (%s -> %s) ; choix : %s" % (L_app, L_test, len(ch), o.index[0].date(), o.index[-1].date(),
          ", ".join("%s %d" % (k, v) for k, v in fq.head(6).items())))
    for lab, z, s_ in (("choisi (fa appris)", a, o), ("bt_or actuel", bb, ob)):
        print("  %-19s total %+6.1f R  mois<0 %2d/%d  creux %+5.1f R  gain/creux %5.2f  Sharpe %5.2f  regul %5.2f"
              % (lab, z["tot"], z["mneg"], z["nm"], z["cr"], z["rap"], shj(s_), z["reg"]))
    print("  -> du bon cote : %s  (jeu traite en %.0f s)" % (wf_ok, time.time() - t1))
    return T, dict(wf_ok=wf_ok, wf=(a, bb), p=pres)


if __name__ == "__main__":
    a5, b5 = BR.charge("xau_m5_2025a"), BR.charge("xau_m5_90k")
    d5 = pd.concat([a5, b5[b5.heure > a5.heure.iloc[-1]]], ignore_index=True)
    dh = BR.charge("xau_h1_50k")
    dh = dh[dh.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
    print("Grille : %d tailles x %d max x %d conditions = %d variantes ; reference %s. Totaux mis a la pire baisse de bt_or (a)."
          % (len(TAILLES), len(MAXS), len(CONDS), NV, NOMV[REF]))
    T5, W5 = jeu("or M5", d5, {}, 6, 1)
    TH, WH = jeu("or H1", dh, dict(span=48, heures=BJ.H_H1, debut=60), 12, 3)
    T = pd.concat([T5, TH], ignore_index=True)
    T.round(4).to_csv(os.path.join(ICI, "donnees", "bt_plus.csv"), index=False)
    # ------------------------------------------------ synthese
    A, B = T5.set_index("variante"), TH.set_index("variante")
    deux = A.bat & B.bat
    sc = (A.gain_creux / A.gain_creux[NOMV[REF]] + B.gain_creux / B.gain_creux[NOMV[REF]]) / 2
    print("\n=== Synthese")
    print("Gain/creux ET Sharpe > bt_or sur M5 ET H1 : %s" % (", ".join(deux[deux].index) or "aucune"))
    print("5 meilleures (moyenne des gain/creux relatifs M5, H1) : " + " ; ".join(
        "%s %.3f (Sh %.2f/%.2f)" % (k, v, A.sharpe[k], B.sharpe[k]) for k, v in sc.sort_values(ascending=False).head(5).items()))
    p5 = max(W5["p"]["gc"][2], W5["p"]["sh"][2]); ph = max(WH["p"]["gc"][2], WH["p"]["sh"][2])
    p_ok = min(p5, ph) < 0.05 and max(p5, ph) < 0.15
    desc = bool(deux.any()); wf_ok = W5["wf_ok"] and WH["wf_ok"]
    v = "TIENT" if desc and wf_ok and p_ok else ("PRESQUE" if desc else "NON")
    print("Walk-forward du bon cote : M5 %s, H1 %s ; p corrige retenu (max gc, Sharpe) : M5 %.3f, H1 %.3f"
          % (W5["wf_ok"], WH["wf_ok"], p5, ph))
    print("Verdict (fixe d'avance) : %s.  Duree totale %.0f s. Ecrit donnees/bt_plus.csv (%d lignes)." % (v, time.time() - T00, len(T)))
