"""Banc AH : un JUMEAU qui encaisse petit a petit, pose PAR-DESSUS bt_or (or XAUUSD, compte demo).
bt_or garde exactement sa mise et ses regles (banc_bt_regulier.simule : sens = cloture contre l'EMA 2 jours, entrees
aux heures fixes, ajouts tous les 0,25 ATR, 3 positions, sortie de tout au recul de 0,667 ATR depuis le meilleur prix).
Le jumeau prend EXACTEMENT les memes entrees (memes paniers, memes ajouts, meme prix, meme spread), avec une mise
m x celle de bt_or (m dans {0,5 ; 1 ; 2}), mais sort autrement. Ensemble = bt_or + m x jumeau. Temoin = bt_or x (1+m)
(miser plus sur bt_or, meme risque d'entree que l'ensemble).
Donnees : or M5 du courtier xau_m5_2025a + xau_m5_90k (06/2025 -> 11/2026, spread reel) ; or H1 xau_h1_50k a partir du
01/08/2022 (reglages H1 de banc_bt_regulier : EMA 48 bougies, heures 2,7,11,14,15 h, debut 60).
Unites : 1 R = perte d'UNE position au stop initial (0,667 ATR) = risque constant comme le robot ; $ = 0,01 lot par
position (1 bp = 0,40 $, comme banc_bt_regulier.bp / banc_alloc), le jumeau a m x 0,01 lot.
Grille fixee d'avance (N = 10 jumeaux x 3 mises = 30 ensembles). Les paliers « en R » sont mesures PAR POSITION depuis
son propre prix d'entree (comme la prise partielle de banc_sorties_bt, le plus simple) ; la fraction est celle de la
position de depart (un tiers = 1/3 de chaque position) ; « apres +k R » (resserrement) = le meilleur prix du panier
s'est eloigne de k R du cours d'ouverture du panier (comme banc_sorties_bt « serre »).
  J1 1/3 a +1 R, 1/3 a +2 R, reste au suiveur 0,667 ATR      J2 1/2 a +1 R, reste suiveur
  J3 1/3 a +2 R, 1/3 a +4 R, reste suiveur                   J4 1/2 a +2 R, reste suiveur
  J5 suiveur 0,667 ATR, 0,5 ATR apres +2 R, 0,33 ATR apres +4 R    J6 suiveur 0,667 puis 0,4 ATR apres +1 R
  J7 tout le jumeau sort a cours d'ouverture du panier + 3 R (comme banc_sorties_bt objectif), sinon suiveur
  J8 1/3 a +1 ATR, 1/3 a +2 ATR du prix moyen d'entree du panier (moyenne des positions entrees), reste suiveur
  J9 1/3 a +1 R, 1/3 a +3 R ; une fois +1 R atteint par une position, son stop = max(suiveur, son prix d'entree)
  J10 quand le panier est plein (3 positions), 1/3 de chaque position sort a chaque pas (0,25 ATR) de plus franchi
      (niveau = 4e niveau d'ajout puis +1 pas ; 2 fois au plus), reste suiveur
Execution bougie par bougie sans fuite : a chaque bougie, d'abord le stop (calcule avec le meilleur prix AVANT la
bougie ; si stop et objectif dans la meme bougie : le stop), puis les objectifs (ordres limites au niveau exact, achat
sorti au bid, vente rachetee a l'ask = bas + spread), puis mise a jour du meilleur prix, puis ajouts a la cloture.
Un jumeau sorti en entier ne reprend pas les ajouts suivants de bt_or. Le suiveur du jumeau n'est jamais plus large
que celui de bt_or : quand bt_or sort, le jumeau est deja sorti.
Courbe JOURNALIERE marquee a la cloture du dernier bougie du jour (gain latent compris) : pire baisse, mois, regularite.
Mesures : total (R, $), gain en plus, mois<0, pire baisse (R, $, en plus), gain/pire baisse (en R : c'est l'unite du
robot ; la colonne $ est donnee a titre indicatif), regularite = moyenne/ecart-type du gain mensuel, part gardee par le
jumeau sur les 10 % des paniers bt_or les plus gagnants (gain jumeau / gain bt_or), moities (signe de m x jumeau et
de l'ecart au temoin m x (jumeau - bt_or)).
NB : gain / pire baisse ne depend pas de la taille : le temoin bt_or x (1+m) a EXACTEMENT le rapport de bt_or seul,
il ne gagne que du total ; « battre le temoin en gain/pire baisse » = battre bt_or seul en gain/pire baisse.
Critere (fixe d'avance) « on garde » : total ensemble >= bt_or seul ET (gain/pire baisse > bt_or seul OU moins de
mois negatifs), sur M5 ET sur H1. Walk-forward (M5 6 mois -> 1 ; H1 12 mois -> 3) : choix de l'ensemble au meilleur
gain/pire baisse d'apprentissage parmi ceux qui battent bt_or seul (gain/pire baisse plus haut et total >=), sinon pas
de jumeau ; « du bon cote » = hors echantillon total >= bt_or ET gain/pire baisse > bt_or, sur M5 et H1.
Essais multiples : bootstrap stationnaire de blocs de PANIERS apparies (blocs moyens 5 paniers, 2000 tirages,
banc_bt_regulier.boot) sur la difference de gain/pire baisse par panier clos (et de Sharpe par panier),
ensemble - bt_or seul et ensemble - temoin ; reality check de White (max sur les 30) -> p par jeu.
Verdict : tient = critere sur M5 et H1 + walk-forward du bon cote sur les deux + p < 0,05 sur les deux ; presque =
critere descriptif sur les deux mais p >= 0,05 ou walk-forward mitige ; sinon non.
Reutilise banc_bt_regulier (charge, simule, boot), banc_sorties_bt (simule, controle J2 = prise partielle 1/2 a +1 R),
banc_blocktrend (simule, controle de bt_or). banc_thermometre n'est PAS importe (il rejoue tout son banc a l'import) :
son style (latent marque a la cloture, bootstrap, walk-forward glissant) est repris.
Controles : bt_or seul = banc_bt_regulier (295 paniers, +114 R en M5) ; m = 0 redonne bt_or ; jumeau J0 a sortie
identique a bt_or redonne le temoin.
RESULTAT (execution du 18/11/2026, 13 s) : verdict NON, miser plus sur bt_or fait aussi bien.
  M5 : bt_or seul +115,6 R (courbe marquee), creux -18,2 R, gain/creux 6,34, 7/18 mois<0 ; AUCUN des 30 ensembles ne
  depasse 6,34 (meilleurs J5 m0,5 et J7 m0,5 : 6,33) ni n'a moins de mois<0 -> critere rempli par aucun sur M5.
  H1 : bt_or seul gain/creux 3,66 ; 18/30 remplissent le critere (J9 m2 3,79, J9 m1 3,75, J2 m2 3,73), ecarts de 1-4 %.
  Walk-forward : M5 3,30 contre 3,51 (bt_or) ; H1 4,43 contre 7,67 -> mauvais cote sur les deux.
  Reality check gain/creux par panier : p corrige 0,884 (M5) / 0,869 (H1), identique contre le temoin (rapport
  invariant a la taille) ; Sharpe par panier : 0,642 / 0,701. Le jumeau perd sur les deux jeux contre bt_or
  (m x (J - bt) negatif dans presque toutes les cases) : encaisser tot coute plus que la baisse evitee.
Ecrit donnees/jumeau.csv. Usage : python3 banc_jumeau.py"""
import os, time, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_bt_regulier as BR
import banc_sorties_bt as BS
import banc_blocktrend as BT

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
PAS, STOP, MAXP = BR.PAS, BR.STOP, BR.MAXP
USD = 0.40
H_H1 = {(2, 0), (7, 0), (11, 0), (14, 0), (15, 0)}
SPECS = {"J0": {},                                           # controle : sortie identique a bt_or
         "J1": {"tR": [(1, 1 / 3), (2, 1 / 3)]},
         "J2": {"tR": [(1, 0.5)]},
         "J3": {"tR": [(2, 1 / 3), (4, 1 / 3)]},
         "J4": {"tR": [(2, 0.5)]},
         "J5": {"serre": [(2, 0.5 / STOP), (4, 0.33 / STOP)]},
         "J6": {"serre": [(1, 0.4 / STOP)]},
         "J7": {"obj": 3.0},
         "J8": {"tA": [(1, 1 / 3), (2, 1 / 3)]},
         "J9": {"tR": [(1, 1 / 3), (3, 1 / 3)], "be": 1.0},
         "J10": {"plein": 1 / 3}}
NOMS = list(SPECS)                    # indice k+1 dans les tableaux (0 = bt_or)
SP = [SPECS[n] for n in NOMS]
NS = 1 + len(NOMS)
MISES = (0.5, 1.0, 2.0)


def simule_j(d, span=576, heures=BR.H_M5, debut=600):
    """bt_or + les jumeaux en une passe. Rend : paniers (t0, t1, s, gR[NS], gD[NS]) et courbe journaliere marquee."""
    c, hi, lo, sp, t = (d[x].values for x in ("cloture", "haut", "bas", "sp", "heure"))
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    fin_j = np.r_[jour[1:] != jour[:-1], True]
    accR, accD = np.zeros(NS), np.zeros(NS)
    P, EQR, EQD, JO = [], [], [], []
    ouvert = {}

    def real(p, k, e, w, x):
        mv = p["s"] * (x - e) * w
        p["g"][k] += mv; accR[k] += mv / p["stop"]; accD[k] += mv * p["usd"]

    for i in range(debut, len(c)):
        for s in list(ouvert):
            p = ouvert[s]
            ext = hi[i] if s > 0 else lo[i] + sp[i]           # prix de sortie favorable atteint dans la bougie
            adv = lo[i] if s > 0 else hi[i] + sp[i]           # prix de sortie defavorable
            st = p["stop"]
            prog = s * (p["meilleur"] - p["c0"]) / st
            for k, tw in enumerate(p["tw"]):
                if not tw["viv"]:
                    continue
                sp_ = SP[k]; K = k + 1; e, w = tw["e"], tw["w"]
                dist = 1.0
                for kk, f in sp_.get("serre", ()):
                    if prog >= kk:
                        dist = f
                trail = p["meilleur"] - s * dist * st
                for q in range(len(e)):                       # 1) stops d'abord
                    if w[q] <= 1e-12:
                        continue
                    lv = trail
                    if tw["be"][q]:
                        lv = max(trail, e[q]) if s > 0 else min(trail, e[q])
                    if s * (adv - lv) <= 0:
                        real(p, K, e[q], w[q], lv); w[q] = 0.0
                if max(w) <= 1e-12:
                    tw["viv"] = False; continue
                if "obj" in sp_ and s * (ext - p["c0"]) >= sp_["obj"] * st:     # 2) objectif total
                    x = p["c0"] + s * sp_["obj"] * st
                    for q in range(len(e)):
                        if w[q] > 1e-12:
                            real(p, K, e[q], w[q], x); w[q] = 0.0
                    tw["viv"] = False; continue
                moy = np.mean(e)
                for q in range(len(e)):                       # 3) paliers
                    if w[q] <= 1e-12:
                        continue
                    for ti, (kk, f) in enumerate(sp_.get("tR", ())):
                        if ti not in tw["fl"][q] and s * (ext - e[q]) >= kk * st:
                            f = min(f, w[q]); real(p, K, e[q], f, e[q] + s * kk * st); w[q] -= f; tw["fl"][q].add(ti)
                            if "be" in sp_ and kk >= sp_["be"]:
                                tw["be"][q] = True
                    for ti, (kk, f) in enumerate(sp_.get("tA", ())):
                        lv = moy + s * kk * st / STOP
                        if ("A", ti) not in tw["fl"][q] and s * (ext - lv) >= 0:
                            f = min(f, w[q]); real(p, K, e[q], f, lv); w[q] -= f; tw["fl"][q].add(("A", ti))
                if "plein" in sp_ and tw["pl"] is not None:
                    while tw["pn"] < 2 and s * (ext - tw["pl"]) >= 0:
                        for q in range(len(e)):
                            f = min(sp_["plein"], w[q])
                            if f > 1e-12:
                                real(p, K, e[q], f, tw["pl"]); w[q] -= f
                        tw["pn"] += 1; tw["pl"] += s * p["pas"]
                if max(w) <= 1e-12:
                    tw["viv"] = False
            niveau = p["meilleur"] - s * st                   # bt_or
            if s * (adv - niveau) <= 0:
                for e in p["e"]:
                    real(p, 0, e, 1.0, niveau)
                assert not any(tw["viv"] for tw in p["tw"])
                del ouvert[s]
                P.append((t[p["i"]], t[i], s, p["g"] / st, p["g"] * p["usd"]))
                continue
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            while len(p["e"]) < MAXP and s * (c[i] - p["prochain"]) >= 0:
                if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                    ent = c[i] + (sp[i] if s > 0 else -sp[i])
                    p["e"].append(ent)
                    for tw in p["tw"]:
                        if tw["viv"]:
                            tw["e"].append(ent); tw["w"].append(1.0); tw["fl"].append(set()); tw["be"].append(False)
                p["prochain"] += s * p["pas"]
            if len(p["e"]) == MAXP:
                for tw in p["tw"]:
                    if tw["viv"] and tw["pl"] is None:
                        tw["pl"] = p["prochain"]
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if s not in ouvert:
                ent = c[i] + (sp[i] if s > 0 else -sp[i])
                ouvert[s] = {"i": i, "s": s, "e": [ent], "meilleur": c[i], "c0": c[i], "stop": STOP * atr[i],
                             "pas": PAS * atr[i], "prochain": c[i] + s * PAS * atr[i], "usd": USD * 1e4 / c[i],
                             "g": np.zeros(NS),
                             "tw": [{"viv": True, "e": [ent], "w": [1.0], "fl": [set()], "be": [False], "pl": None, "pn": 0}
                                    for _ in NOMS]}
        if fin_j[i]:
            lR, lD = np.zeros(NS), np.zeros(NS)
            for s, p in ouvert.items():
                x = c[i] if s > 0 else c[i] + sp[i]
                v = np.zeros(NS)
                v[0] = sum(s * (x - e) for e in p["e"])
                for k, tw in enumerate(p["tw"]):
                    if tw["viv"]:
                        v[k + 1] = sum(s * (x - e) * w for e, w in zip(tw["e"], tw["w"]))
                lR += v / p["stop"]; lD += v * p["usd"]
            EQR.append(accR + lR); EQD.append(accD + lD); JO.append(jour[i])
    P = pd.DataFrame({"t0": [x[0] for x in P], "t1": [x[1] for x in P], "s": [x[2] for x in P]}), \
        np.array([x[3] for x in P]), np.array([x[4] for x in P])
    dates = pd.to_datetime(np.array(JO) * 86400, unit="s")
    return P, pd.DataFrame(np.array(EQR), dates), pd.DataFrame(np.array(EQD), dates)


creux = lambda x: (np.r_[0, np.cumsum(x)] - np.maximum.accumulate(np.r_[0, np.cumsum(x)])).min()


def mesure(x, mois):
    """x : gain par jour (courbe marquee). Rend total, mois<0, nb mois, creux, gain/creux, regularite, moities."""
    mm = x.groupby(mois).sum(); cr = creux(x.values); n = len(x) // 2
    return dict(tot=x.sum(), mneg=int((mm < 0).sum()), nm=len(mm), cr=cr, rap=x.sum() / -cr if cr < 0 else np.inf,
                reg=mm.mean() / mm.std() if mm.std() > 0 else 0.0, h1=x.iloc[:n].sum(), h2=x.iloc[n:].sum())


def ratio_mat(X):
    """gain / pire baisse ligne par ligne (X : tirages x paniers)."""
    cs = np.cumsum(X, 1); cs = np.concatenate([np.zeros((len(X), 1)), cs], 1)
    cr = (cs - np.maximum.accumulate(cs, 1)).min(1)
    return cs[:, -1] / np.maximum(-cr, 1e-9)


sharpe_mat = lambda X: X.mean(1) / X.std(1)


def jeu(nom, d, kw, L_app, L_test):
    t1 = time.time()
    (Pi, GR, GD), ER, ED = simule_j(d, **kw)
    ref = BR.simule(d, **kw)
    bt = BT.simule(d, PAS, STOP, MAXP)  if not kw else None
    n = len(Pi)
    print("\n=== %s : %s -> %s, %d paniers, %d jours (simulation %.0f s)" % (nom, ER.index[0].date(), ER.index[-1].date(), n, len(ER), time.time() - t1))
    ok_ref = len(ref) == n and np.allclose(GR[:, 0], ref.g.values)
    print("Controles : bt_or %+.1f R / %+.0f $ (banc_bt_regulier %d paniers %+.1f R, identiques : %s)%s"
          % (GR[:, 0].sum(), GD[:, 0].sum(), len(ref), ref.g.sum(), ok_ref,
             "" if bt is None else " ; banc_blocktrend (pyramide 3) %d paniers %+.1f R" % (len(bt), sum(x[3] for x in bt))))
    k0 = NOMS.index("J0") + 1
    print("  J0 (sortie = bt_or) identique a bt_or par panier : %s ; courbe : %s -> bt_or + m x J0 = temoin ; m = 0 -> bt_or (trivial)"
          % (np.allclose(GR[:, k0], GR[:, 0]), np.allclose(ER[k0], ER[0])))
    if not kw:
        bs = BS.simule(d, partiel=1.0)
        print("  J2 contre banc_sorties_bt.simule(partiel=1) sur les memes bougies : %+.1f R contre %+.1f R (%d paniers)"
              % (GR[:, NOMS.index("J2") + 1].sum(), sum(g for _, g in bs), len(bs)))
    xR, xD = ER.diff().fillna(ER.iloc[0]), ED.diff().fillna(ED.iloc[0])
    mois = xR.index.to_period("M")
    top = np.argsort(GR[:, 0])[::-1][:max(1, n // 10)]
    base = mesure(xR[0], mois); baseD = mesure(xD[0], mois)
    rows = []

    def ligne(lab, sR, sD, part, m, jn):
        a, b = mesure(sR, mois), mesure(sD, mois)
        crit = a["tot"] >= base["tot"] - 1e-9 and (a["rap"] > base["rap"] + 1e-9 or a["mneg"] < base["mneg"])
        r = dict(jeu=nom, ensemble=lab, jumeau=jn, m=m, total_R=a["tot"], total_usd=b["tot"], en_plus_R=a["tot"] - base["tot"],
                 mois_neg=a["mneg"], mois=a["nm"], creux_R=a["cr"], creux_usd=b["cr"], creux_en_plus_usd=b["cr"] - baseD["cr"],
                 gain_creux_R=a["rap"], gain_creux_usd=b["rap"], regularite=a["reg"], part_gros=part,
                 h1_R=a["h1"], h2_R=a["h2"], critere=crit)
        rows.append(r); return r
    ligne("bt_or seul", xR[0], xD[0], 1.0, 0.0, "-")
    for m in MISES:
        ligne("temoin x%.1f" % (1 + m), (1 + m) * xR[0], (1 + m) * xD[0], 1.0, m, "-")
    for k, jn in enumerate(NOMS):
        if jn == "J0":
            continue
        part = GR[top, k + 1].sum() / GR[top, 0].sum()
        for m in MISES:
            r = ligne("%s m%.1f" % (jn, m), xR[0] + m * xR[k + 1], xD[0] + m * xD[k + 1], part, m, jn)
            r["moit_J"] = "%+.0f/%+.0f" % (m * (xR[k + 1].iloc[:len(xR) // 2].sum()), m * xR[k + 1].iloc[len(xR) // 2:].sum())
            dif = m * (xR[k + 1] - xR[0])
            r["moit_J_moins_bt"] = "%+.0f/%+.0f" % (dif.iloc[:len(dif) // 2].sum(), dif.iloc[len(dif) // 2:].sum())
    T = pd.DataFrame(rows)
    T["rang"] = T.gain_creux_R.rank(ascending=False).astype(int)
    print("%-11s %7s %7s %6s %6s %6s %7s %6s %6s %6s %5s %5s %13s %13s %s" % (
        "ensemble", "tot R", "tot $", "+R", "m<0", "creuxR", "creux$", "+cr$", "g/crR", "g/cr$", "regul", "part", "moit m*J", "moit m*(J-bt)", "crit"))
    for _, r in T.sort_values("gain_creux_R", ascending=False).iterrows():
        print("%-11s %+7.1f %+7.0f %+6.1f %2d/%-3d %+6.1f %+7.0f %+6.0f %6.2f %6.2f %5.2f %5.2f %13s %13s %s" % (
            r.ensemble, r.total_R, r.total_usd, r.en_plus_R, r.mois_neg, r.mois, r.creux_R, r.creux_usd, r.creux_en_plus_usd,
            r.gain_creux_R, r.gain_creux_usd, r.regularite, r.part_gros, r.get("moit_J", "") if isinstance(r.get("moit_J", ""), str) else "",
            r.get("moit_J_moins_bt", "") if isinstance(r.get("moit_J_moins_bt", ""), str) else "", "OUI" if r.critere and r.jumeau != "-" else ""))
    # ------------------------------------------------ walk-forward
    ENS = [(jn, m) for jn in NOMS if jn != "J0" for m in MISES]
    serie = {(jn, m): xR[0] + m * xR[NOMS.index(jn) + 1] for jn, m in ENS}
    MO = mois.unique()
    oos, oosb, oost, ch = [], [], [], []
    for i0 in range(L_app, len(MO), L_test):
        app = (mois >= MO[i0 - L_app]) & (mois <= MO[i0 - 1]); te = (mois >= MO[i0]) & (mois <= MO[min(i0 + L_test, len(MO)) - 1])
        b = mesure(xR[0][app], mois[app])
        cand = [(mesure(serie[e][app], mois[app]), e) for e in ENS]
        cand = [(a["rap"], e) for a, e in cand if a["rap"] > b["rap"] and a["tot"] >= b["tot"]]
        if cand:
            e = max(cand)[1]; oos.append(serie[e][te]); oost.append((1 + e[1]) * xR[0][te]); ch.append("%s m%.1f" % e)
        else:
            oos.append(xR[0][te]); oost.append(xR[0][te]); ch.append("aucun")
        oosb.append(xR[0][te])
    o, ob, ot = pd.concat(oos), pd.concat(oosb), pd.concat(oost)
    mo = o.index.to_period("M")
    a, b, c_ = mesure(o, mo), mesure(ob, mo), mesure(ot, mo)
    fq = pd.Series(ch).value_counts()
    wf_ok = a["tot"] >= b["tot"] - 1e-9 and a["rap"] > b["rap"] + 1e-9
    print("Walk-forward %d -> %d mois, %d fenetres (%s -> %s) ; choix : %s" % (L_app, L_test, len(ch), o.index[0].date(), o.index[-1].date(),
          ", ".join("%s %d" % (k, v) for k, v in fq.items())))
    for lab, z in (("choisi", a), ("bt_or seul", b), ("temoin (1+m choisi)", c_)):
        print("  %-20s total %+6.1f R  mois<0 %2d/%d  creux %+5.1f R  gain/creux %5.2f  regul %5.2f" % (lab, z["tot"], z["mneg"], z["nm"], z["cr"], z["rap"], z["reg"]))
    print("  -> du bon cote (total >= bt_or et gain/creux > bt_or) : %s" % wf_ok)
    # ------------------------------------------------ bootstrap par blocs de paniers apparies, reality check
    I = BR.boot(n)                           # 2000 x n, blocs moyens 5 paniers
    b0 = GR[:, 0]
    res = {}
    for stat, f in (("gain/creux", ratio_mat), ("Sharpe", sharpe_mat)):
        for contre in ("bt_or seul", "temoin"):
            dob, dbo = [], []
            rb_o, rb_b = f(b0[None, :])[0], f(b0[I])
            for jn, m in ENS:
                e = b0 + m * GR[:, NOMS.index(jn) + 1]
                r0 = (1 + m) * b0 if contre == "temoin" else b0
                dob.append(f(e[None, :])[0] - f(r0[None, :])[0]); dbo.append(f(e[I]) - f(r0[I]))
            dob, dbo = np.array(dob), np.array(dbo)
            V = dob.max(); Vb = (dbo - dob[:, None]).max(0)
            kb = int(dob.argmax())
            res[(stat, contre)] = (ENS[kb], dob[kb], (Vb >= V).mean(), (dbo[kb] - dob[kb] >= dob[kb]).mean())
            print("  bootstrap %-10s ensemble - %-10s : meilleur %s m%.1f (ecart %+.3f), p brut %.3f, p corrige (max des 30) %.3f"
                  % (stat, contre, *ENS[kb], dob[kb], res[(stat, contre)][3], res[(stat, contre)][2]))
    print("  (jeu traite en %.0f s)" % (time.time() - t1))
    return T, dict(wf_ok=wf_ok, wf=(a, b, c_), choix=fq, p=res)


if __name__ == "__main__":
    a5, b5 = BR.charge("xau_m5_2025a"), BR.charge("xau_m5_90k")
    d5 = pd.concat([a5, b5[b5.heure > a5.heure.iloc[-1]]], ignore_index=True)
    dh = BR.charge("xau_h1_50k")
    dh = dh[dh.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
    print("Grille : %d jumeaux x %d mises = %d ensembles (+ J0 de controle). Unites : R (risque constant) et $ a 0,01 lot par position."
          % (len(NOMS) - 1, len(MISES), (len(NOMS) - 1) * len(MISES)))
    T5, W5 = jeu("or M5", d5, {}, 6, 1)
    TH, WH = jeu("or H1", dh, dict(span=48, heures=H_H1, debut=60), 12, 3)
    T = pd.concat([T5, TH], ignore_index=True)
    T.drop(columns=["rang"]).round(4).to_csv(os.path.join(ICI, "donnees", "jumeau.csv"), index=False)
    # ------------------------------------------------ synthese
    E5 = T5[T5.jumeau != "-"].set_index("ensemble"); EH = TH[TH.jumeau != "-"].set_index("ensemble")
    deux = E5.critere & EH.critere
    b5r, bhr = T5.gain_creux_R.iloc[0], TH.gain_creux_R.iloc[0]
    print("\n=== Synthese")
    print("Critere « on garde » rempli sur M5 ET H1 : %s" % (", ".join(deux[deux].index) or "aucun"))
    bat = (E5.gain_creux_R > b5r) & (EH.gain_creux_R > bhr)
    print("Gain/creux meilleur que bt_or seul (= que le temoin) sur M5 ET H1 : %s" % (", ".join(bat[bat].index) or "aucun : miser plus sur bt_or fait aussi bien"))
    sc = (E5.gain_creux_R / b5r + EH.gain_creux_R / bhr) / 2
    print("5 meilleurs (moyenne des gain/creux relatifs M5 et H1) : " + " ; ".join("%s %.2f" % (k, v) for k, v in sc.sort_values(ascending=False).head(5).items()))
    pm = {k: max(W5["p"][k][2], WH["p"][k][2]) for k in W5["p"]}
    crit_ok = bool(deux.any()); wf_ok = W5["wf_ok"] and WH["wf_ok"]; p_ok = pm[("gain/creux", "bt_or seul")] < 0.05
    v = "TIENT" if crit_ok and wf_ok and p_ok else ("PRESQUE" if crit_ok else "NON")
    print("Walk-forward du bon cote : M5 %s, H1 %s ; p corrige gain/creux (max M5, H1) contre bt_or %.3f, contre temoin %.3f"
          % (W5["wf_ok"], WH["wf_ok"], pm[("gain/creux", "bt_or seul")], pm[("gain/creux", "temoin")]))
    print("Verdict (fixe d'avance) : %s.  Duree totale %.0f s. Ecrit donnees/jumeau.csv (%d lignes)." % (v, time.time() - T00, len(T)))
