"""Banc DECOMPOSE : d'ou vient le resultat de bt_or ? (PRIORITES 22/11, contre-expertise externe, point 2 ; compte demo).
Mecanique bt_or inchangee (banc_bt_regulier.simule) : entree aux heures fixes s'il n'y a pas de panier de ce cote,
ajouts dans le sens du prix tous les 0,25 ATR (3 positions au plus), sortie de tout le panier au recul de 0,667 ATR
depuis le meilleur prix. Spread reel, meme convention que BR.simule. 1 R = perte d'une position au stop initial :
identique pour toutes les variantes (risque comparable par construction, une position = 1 R de risque initial).
Jeux : or M5 18 mois (xau_m5_2025a + xau_m5_90k, span 576, heures BR.H_M5, debut 600) ; or H1 depuis 08/2022 (span 48,
heures banc_jumeau.H_H1, debut 60), et ses deux moities : paniers OUVERTS avant le 01/10/2024 / a partir du 01/10/2024
(meme simulation continue, decoupee par date d'ouverture ; 2e moitie = forte hausse de l'or).
Variantes fixees d'avance :
  (a) bt_or tel quel (sens = cloture contre EMA 2 jours, 3 positions) ; controle : redonne BR.simule panier par panier
      (M5 295 paniers +114,1 R ; H1 956 paniers +153,4 R) ;
  (b) meme sens, sans renforcements (1 position, meme stop suiveur, memes sorties) ;
  (c) sens tire au sort (pile ou face a chaque heure d'entree valide, le reste identique, blocage « un panier par cote »
      compris), avec (c3) et sans (c1) renforcements ; 2000 tirages, graine 2211 ; p du signal de sens =
      (1 + nb tirages >= bt_or) / (1 + 2000), (a) contre c3 et (b) contre c1, sur le total R (retenu) et, en
      appoint, sur le R par panier (le hasard ouvre plus de paniers : les deux cotes se debloquent plus souvent) ;
  (e) toujours acheteur, avec (e3) et sans (e1) renforcements.
Methode exacte : le resultat d'un panier ne depend que de sa bougie d'ouverture et de son sens (les deux cotes sont
independants dans BR.simule) ; on precalcule donc chaque panier possible (heure d'entree x sens) puis on rejoue la
regle de blocage pour chaque suite de sens. Gain compte au jour de SORTIE ; panier jamais sorti : non compte.
Mesures fixees d'avance : paniers, total R, R/panier, pire baisse (cumul des paniers dans l'ordre des sorties),
mois negatifs / mois du jeu. Decomposition additive fixee d'avance, par jeu :
  a = c1 moyen (tendance de l'or + frais, entrees au hasard, 1 position)
    + (c3 moyen - c1 moyen) (pyramide sans signal)
    + (a - c3 moyen) (signal de sens, interaction avec la pyramide comprise) ;
  mesures d'appoint : pyramide avec signal = a - b ; tendance = e3 (et e1) ; signal au-dela de l'achat seul = a - e3.
RESULTAT (execution du 22/11/2026, 7 s) : controles exacts (M5 295 / +114,1 R ; H1 956 / +153,4 R, panier par panier).
  M5 17 mois : a +114,1 = tendance+frais +21,0 (18 %) + pyramide sans signal +57,1 (50 %) + signal +35,9 (31 %) ;
    p sens 0,004 (total), 0,0005 (R/panier) ; toujours acheteur 3 pos. +92,7 R (81 % de a, avec 255 paniers).
  H1 52 mois : a +153,4 = +26,5 (17 %) + 81,6 (53 %) + 45,3 (30 %) ; p sens 0,041 ; MAIS toujours acheteur 3 pos.
    +243,7 R (159 % de a, pire baisse -25 contre -40) : le signal fait moins bien que l'achat seul (-90 R).
  H1 2022-08 -> 2024-09 : a -0,9 R (15/26 mois < 0), p sens 0,88 (sous la moyenne du hasard +20,8) ; achat seul +100,7.
  H1 2024-10 -> 2026-11 : a +154,2 R, p sens 0,0005 ; achat seul +142,9 R ; tout le resultat H1 est dans cette moitie.
  Lecture : la pyramide est la plus grosse part (50-53 %) ; le signal de sens bat le hasard sur M5 et H1 complet, mais
  pas l'achat permanent, et il est nul sur 2022-2024 : il agit surtout comme « rester acheteur pendant la hausse ».
Ecrit donnees/decompose_bt.csv. Usage : python3 banc_decompose_bt.py
"""
import os, time, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_bt_regulier as BR
import banc_jumeau as BJ

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
NT, GRAINE = 2000, 2211
COUPE = pd.Timestamp("2024-10-01").timestamp()


def paniers_possibles(d, span=576, heures=BR.H_M5, debut=600):
    """Pour chaque heure d'entree valide k et chaque sens (0 = achat, 1 = vente) : bougie de sortie, gain 3 pos, gain 1 pos."""
    c, hi, lo, sp, t = (d[x].values for x in ("cloture", "haut", "bas", "sp", "heure"))
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    n = len(c)
    ik = np.array([i for i in range(debut, n) if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0])
    K = len(ik)
    EX = np.full((K, 2), n, int); G3 = np.zeros((K, 2)); G1 = np.zeros((K, 2))
    for k, i in enumerate(ik):
        for si, s in ((0, 1), (1, -1)):
            stop, pas = BR.STOP * atr[i], BR.PAS * atr[i]
            e = [c[i] + (sp[i] if s > 0 else -sp[i])]
            meilleur, prochain = c[i], c[i] + s * pas
            for q in range(i + 1, n):
                niveau = meilleur - s * stop
                if (lo[q] <= niveau) if s > 0 else (hi[q] + sp[q] >= niveau):
                    EX[k, si] = q
                    G3[k, si] = sum(s * (niveau - x) for x in e) / stop
                    G1[k, si] = s * (niveau - e[0]) / stop
                    break
                meilleur = max(meilleur, hi[q]) if s > 0 else min(meilleur, lo[q])
                while len(e) < BR.MAXP and s * (c[q] - prochain) >= 0:
                    if s * (c[q] - prochain) <= 0.5 * pas:
                        e.append(c[q] + (sp[q] if s > 0 else -sp[q]))
                    prochain += s * pas
    signal = np.where(c[ik] > ema[ik], 0, 1)
    return dict(ik=ik, EX=EX, G3=G3, G1=G1, signal=signal, t=t, n=n)


def rejoue(B, S):
    """S : N x K sens (0/1). Rend O (ouvert ET sorti), sens, bougie de sortie, gains G3 et G1 (N x K)."""
    N, K = S.shape
    bu = np.zeros((N, 2), int); r = np.arange(N)
    O = np.zeros((N, K), bool)
    for k in range(K):
        sd = S[:, k]
        ok = bu[r, sd] <= B["ik"][k]
        O[ok, k] = True
        bu[r[ok], sd[ok]] = B["EX"][k, sd[ok]]
    X = B["EX"][np.arange(K)[None, :], S]
    O &= X < B["n"]
    g3 = np.where(O, B["G3"][np.arange(K)[None, :], S], 0.0)
    g1 = np.where(O, B["G1"][np.arange(K)[None, :], S], 0.0)
    return O, X, g3, g1


def mesures(O, X, g, B, masque, mois_sortie, nmois):
    """Par ligne : paniers, total, R/panier, pire baisse (ordre des sorties), mois negatifs."""
    g = np.where(masque[None, :], g, 0.0); Om = O & masque[None, :]
    npan = Om.sum(1); tot = g.sum(1)
    ordre = np.argsort(np.where(Om, X, B["n"] + 1), axis=1, kind="stable")
    cs = np.cumsum(np.take_along_axis(g, ordre, 1), 1)
    cs = np.hstack([np.zeros((len(g), 1)), cs])
    cr = (cs - np.maximum.accumulate(cs, 1)).min(1)
    M = np.zeros((len(g), nmois))
    ms = mois_sortie[np.minimum(X, B["n"] - 1)]
    rr = np.repeat(np.arange(len(g)), g.shape[1])
    np.add.at(M, (rr, ms.ravel()), g.ravel())
    return dict(pan=npan, tot=tot, rp=np.where(npan > 0, tot / np.maximum(npan, 1), 0), cr=cr, mneg=(M < -1e-12).sum(1))


def traite(nom, d, kw, decoupe=False):
    t1 = time.time()
    B = paniers_possibles(d, **kw)
    K = len(B["ik"])
    per = pd.to_datetime(B["t"], unit="s").to_period("M")
    cal = per.unique(); mois_sortie = cal.get_indexer(per)
    rng = np.random.default_rng(GRAINE)
    S = {"a": B["signal"][None, :], "e": np.zeros((1, K), int), "c": rng.integers(0, 2, size=(NT, K))}
    R = {k: rejoue(B, v) for k, v in S.items()}
    ref = BR.simule(d, **kw)
    O, X, g3, _ = R["a"]
    mine = sorted(zip(B["t"][B["ik"][O[0]]], np.round(g3[0][O[0]], 9)))
    leur = sorted(zip(ref.t0.values, np.round(ref.g.values, 9)))
    print("\n=== %s : %d heures d'entree valides (precalcul + %d tirages en %.0f s)" % (nom, K, NT, time.time() - t1))
    print("Controle (a) contre BR.simule : %d paniers %+.1f R (BR : %d paniers %+.1f R) ; identiques panier par panier : %s"
          % (O[0].sum(), g3[0].sum(), len(ref), ref.g.sum(), mine == leur))
    t_ouv = B["t"][B["ik"]]
    sous = [(nom, np.ones(K, bool))]
    if decoupe:
        sous += [(nom + " 2022-08->2024-09", t_ouv < COUPE), (nom + " 2024-10->2026-11", t_ouv >= COUPE)]
    lignes = []
    for jn, m in sous:
        cm = per[(B["t"] >= t_ouv[m][0])].unique() if m.any() else cal
        nm = len(cm) if jn == nom else len(pd.period_range(pd.to_datetime(t_ouv[m][0], unit="s").to_period("M"),
                                                            pd.to_datetime(t_ouv[m][-1], unit="s").to_period("M")))
        V = {}
        for cle, (Ok, Xk, a3, a1) in R.items():
            for np_, g in ((3, a3), (1, a1)):
                V[cle + str(np_)] = mesures(Ok, Xk, g, B, m, mois_sortie, len(cal))
        a, b, c3, c1, e3, e1 = (V[k] for k in ("a3", "a1", "c3", "c1", "e3", "e1"))
        A = a["tot"][0]
        p3 = (1 + (c3["tot"] >= A).sum()) / (NT + 1); p1 = (1 + (c1["tot"] >= b["tot"][0]).sum()) / (NT + 1)
        q3 = (1 + (c3["rp"] >= a["rp"][0]).sum()) / (NT + 1); q1 = (1 + (c1["rp"] >= b["rp"][0]).sum()) / (NT + 1)
        print("--- %s (%d mois)" % (jn, nm))
        print("%-32s %6s %8s %7s %7s %7s %13s %6s %7s" % ("variante", "pan.", "total R", "R/pan", "creux", "m<0", "tirages 5-95%", "p sens", "p R/pan"))
        noms = {"a3": "(a) bt_or tel quel", "a1": "(b) sans renforcements", "c3": "(c) hasard, 3 positions (moy.)",
                "c1": "(c) hasard, 1 position (moy.)", "e3": "(e) toujours acheteur, 3 pos.", "e1": "(e) toujours acheteur, 1 pos."}
        for k in ("a3", "a1", "c3", "c1", "e3", "e1"):
            v = V[k]; hasard = k[0] == "c"
            p = p3 if k == "a3" else (p1 if k == "a1" else np.nan)
            q = q3 if k == "a3" else (q1 if k == "a1" else np.nan)
            print("%-32s %6.0f %+8.1f %+7.3f %+7.1f %3.0f/%-3d %13s %6s %7s" % (
                noms[k], v["pan"].mean(), v["tot"].mean(), v["tot"].mean() / max(v["pan"].mean(), 1), np.median(v["cr"]),
                np.median(v["mneg"]), nm, "%+.0f/%+.0f" % tuple(np.percentile(v["tot"], [5, 95])) if hasard else "",
                "%.4f" % p if p == p else "", "%.4f" % q if q == q else ""))
            lignes.append(dict(jeu=jn, variante=noms[k], paniers=v["pan"].mean(), total_R=v["tot"].mean(),
                               R_panier=v["tot"].mean() / max(v["pan"].mean(), 1), pire_baisse_R=np.median(v["cr"]),
                               mois_neg=np.median(v["mneg"]), mois=nm, tirages_et=v["tot"].std() if hasard else np.nan,
                               tirages_q05=np.percentile(v["tot"], 5) if hasard else np.nan,
                               tirages_q50=np.percentile(v["tot"], 50) if hasard else np.nan,
                               tirages_q95=np.percentile(v["tot"], 95) if hasard else np.nan,
                               part_tirages_pos=(v["tot"] > 0).mean() if hasard else np.nan, p_sens=p,
                               p_sens_R_panier=q))
        mc3, mc1 = c3["tot"].mean(), c1["tot"].mean()
        dec = [("tendance+frais (hasard 1 pos.)", mc1), ("pyramide sans signal (c3-c1)", mc3 - mc1), ("signal de sens (a-c3)", A - mc3)]
        app = [("pyramide avec signal (a-b)", A - b["tot"][0]), ("toujours acheteur 3 pos. (e3)", e3["tot"][0]),
               ("toujours acheteur 1 pos. (e1)", e1["tot"][0]), ("signal au-dela de l'achat seul (a-e3)", A - e3["tot"][0])]
        print("Decomposition de a = %+.1f R : " % A + " ; ".join("%s %+.1f R (%+.0f %%)" % (k, x, 100 * x / A) for k, x in dec))
        print("  appoint : " + " ; ".join("%s %+.1f R (%+.0f %%)" % (k, x, 100 * x / A) for k, x in app))
        for k, x in dec + app:
            lignes.append(dict(jeu=jn, variante="decomposition : " + k, total_R=x, part_pct=100 * x / A))
    return lignes


if __name__ == "__main__":
    a5, b5 = BR.charge("xau_m5_2025a"), BR.charge("xau_m5_90k")
    d5 = pd.concat([a5, b5[b5.heure > a5.heure.iloc[-1]]], ignore_index=True)
    dh = BR.charge("xau_h1_50k")
    dh = dh[dh.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
    L = traite("or M5", d5, {})
    L += traite("or H1", dh, dict(span=48, heures=BJ.H_H1, debut=60), decoupe=True)
    T = pd.DataFrame(L)
    T.round(4).to_csv(os.path.join(ICI, "donnees", "decompose_bt.csv"), index=False)
    print("\nDuree totale %.0f s. Ecrit donnees/decompose_bt.csv (%d lignes)." % (time.time() - T00, len(T)))
