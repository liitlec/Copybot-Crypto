"""Banc RECONCILIE : pourquoi le meme plan -30 % rend +1,6 %/mois (annexe C, banc_dix) ou +0,3 %/mois (annexe D,
banc_plan_cent) en scenario prudent ? (PRIORITES 22/11, contre-expertise externe, point 1 + note de l'expert).
Le labo calcule seulement : AUCUN ordre n'est passe (compte demo / compte cent simule).
FIXE AVANT : rien n'est re-ecrit, tout est importe. Donnees = banc_plan_cent.series() (bt_or H1 + repli_ind + rebond_nas
+ rebond_sp, 08/2022-11/2026, couts du labo inclus) ; poids = parite de risque ; L = calibre du plan -30 % (controle
7,50) ; courbe a mise hebdomadaire (banc_plan_cent.courbe) ; mois = 1/12 de 261 jours ouvres ; scenarios mesure /
prudent (avantage / 2) / nul (banc_plan_cent.ampute). Deux jeux de tirages, rejoues A L'IDENTIQUE :
  A = tirages de banc_plan_cent (1er appel de son generateur, 12 mois, 5000) ;
  B = tirages de banc_dix / banc_retrait (24 mois, 5000), on garde les 12 premiers mois.
Deux regles d'arret : sans arret (banc_plan_cent) ; arret a -34 % depuis le plus haut (banc_dix.arrete, puis especes).
Cinq definitions, sur CHAQUE combinaison : (a) mediane du mois isole (tous mois x tirages) ; (b) moyenne des mois ;
(c) moyenne geometrique mensuelle par trajectoire (V12^(1/12) - 1) puis mediane ; (d) « rythme median 12 mois » =
mediane(V12)^(1/12) - 1 ; (e) % de mois negatifs ; plus (f) exp(moyenne des log(1 + mois)) - 1 (controle de (c)).
NB : (c) et (d) sont egales par construction (x -> x^(1/12) est croissante : la mediane passe a travers).
Rejeu historique (UNE trajectoire, 52 mois calendaires, scenarios appliques a l'histoire par ampute) : (a), (b), (e) sur les mois
calendaires ; (c) = valeur finale^(1/nb mois) - 1 ; (d) = mediane des fenetres glissantes de 12 mois.
Controles attendus : A sans arret prudent (a) = +0,29 % (annexe D) ; B avec arret prudent (a) = +0,22 % et (d) = +1,60 %
(annexe C, donnees/dix.csv, M0 12 mois).
NOTE DE L'EXPERT (« moitie du capital sur bt_or, moitie sur le repli d'indices, sans levier, 0,04 % par aller-retour »
= +20,87 % en 4 ans, +0,40 %/mois, meilleur mois +4,53 %, pire baisse -5,36 %) : sa taille de position bt_or n'est pas
ecrite ; grille FIXEE AVANT d'interpretations : bt_or en notionnel (P&L / notionnel par position, banc_jumeau, 1 = le
capital) a 1 ou 1/3 par position (3 positions max -> jamais plus que le capital), ou en R (1 R = 1 %) ; frais du labo
seuls ou + 0,04 % par aller-retour (bt_or : par position ; repli : 0,04 % au lieu de 0,015 % a l'entree) ; fenetre
entiere ou 48 derniers mois ; compose quotidien, 50/50 du compte. Le nombre de positions par panier est recompte par une
copie de la logique d'entree de banc_bt_regulier.simule (controle : 956 paniers).
Ecrit donnees/reconcilie.csv. Usage : python3 banc_reconcilie.py

RESULTAT (execution du 22/11/2026, 11 s, 5000 tirages, rien de reduit) : verdict RECONCILIE, l'ecart est une affaire de
DEFINITION, pas de reglage. Controles exacts : L 7,4975 ; A sans arret prudent (a) +0,29 % ; B arret -34 % prudent
(a) +0,22 %, (d) +1,60 % ; mesure (d) +4,38 %. Les deux bancs ont les memes series, poids, L, frais et courbe hebdo.
Prudent, 12 mois (A sans arret | B arret -34 %) : (a) med. mois +0,29 | +0,22 ; (b) moy. mois +2,72 | +2,76 ;
(c) = (d) +1,58 | +1,60 ; (e) mois < 0 48 | 48 % ; (f) +2,10 | +2,14 ; compte median x1,21, moyen x1,39-1,40 ;
annee en perte 27 | 26 %. Mesure : (a) +2,77, (b) +5,5, (d) +4,3-4,4, M<0 32 %. Nul : (a) -2,1, (b) 0,0, (d) -1,2/-1,4,
M<0 64 % (58 % avec arret : mois geles a 0).
Changer de tirages (A -> B) bouge (d) de +0,03 pt ; ajouter l'arret le bouge de -0,02 pt et (a) de -0,07/-0,09 pt.
Changer de DEFINITION dans un meme reglage : +1,3 pt. Cause : mois tres asymetriques (asymetrie ~ +4 : bt_or fait
peu de grands mois et beaucoup de petits mois rouges), donc mediane d'un mois (0,3 %) << rythme compose (1,6 %) <<
moyenne (2,7 %, tiree par les rares grands mois ; perte de composition ~ 1,1 pt).
Rejeu historique prudent (UNE trajectoire, 52 mois) : (a) +0,16, (b) +2,67, (c) +2,08, (d) +1,54, M<0 48 % ; pire baisse
40,8 % : l'arret -34 % SE DECLENCHE le 21/09/2023 (nul : 05/06/2023) et fige le compte a x0,74. Mesure : (c) +4,79,
pire baisse 17 %, pas d'arret.
DECIDER avec (d) / (c) (compte median a 12 mois, ici x1,21 prudent = +1,6 %/mois) et TOUJOURS avec P(annee en perte)
27 % et le % de mois negatifs 48 % ; (a) seule sous-estime ce qu'on gagne, (b) seule le surestime.
NOTE DE L'EXPERT : NON retrouvee a l'identique. Interpretation la plus proche (bt_or 1/3 du notionnel par position,
+0,04 %/AR, 48 mois) : +27,4 %, +0,50 %/mois, meilleur mois +7,16 %, pire baisse -7,5 % (cible +20,87 / +0,40 /
+4,53 / -5,36). Sa taille bt_or n'est pas ecrite et ses donnees ne sont pas les notres ; l'ordre de grandeur
(+0,4 a +0,7 %/mois sans levier) est le meme : les +1,6 %/mois du plan viennent du levier L 7,5.
"""
import os, time, contextlib, io, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_plan_cent as PC
    import banc_retrait as BRT
    import banc_dix as DIX
    import banc_bt_regulier as BR
    import banc_jumeau as BJ
    import banc_mix as BM
    import banc_portefeuille as BP

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
J12 = PC.JOURS
FINS = DIX.FINS[:12]
SC = {"mesure": 0.0, "prudent": 0.5, "nul": 1.0}
SEUIL = 0.34
DEFS = ("a_med_mois", "b_moy_mois", "c_geo_med", "d_rythme12", "e_mois_neg", "f_exp_moylog")


# ------------------------------------------------------------------ mesures
def metriques_mc(V):
    """V : indice de performance (tirages x 261 jours, depart 1)."""
    Vb = V[:, FINS]
    M = Vb / np.concatenate([np.ones((len(V), 1)), Vb[:, :-1]], 1) - 1
    V12 = Vb[:, -1]
    geo = np.maximum(V12, 0) ** (1 / 12) - 1
    return dict(a_med_mois=np.median(M), b_moy_mois=M.mean(), c_geo_med=np.median(geo),
                d_rythme12=np.median(V12) ** (1 / 12) - 1, e_mois_neg=(M < 0).mean(),
                f_exp_moylog=np.exp(np.log1p(np.maximum(M, -0.999)).mean()) - 1,
                moy_geo=geo.mean(), med_V12=np.median(V12), moy_V12=V12.mean(), p_annee_perte=(V12 < 1).mean(),
                asym=((M - M.mean()) ** 3).mean() / M.std() ** 3, part_mois_sup_moy=(M > M.mean()).mean())


def gele(E, seuil):
    """Historique : gele la courbe au 1er jour ou la baisse depuis le plus haut (depart 1) atteint le seuil."""
    dd = E / np.maximum(E.cummax(), 1.0) - 1
    t = dd.index[dd <= -seuil]
    if len(t):
        E = E.copy(); E[E.index > t[0]] = E.loc[t[0]]
    return E, (str(t[0].date()) if len(t) else "non")


def metriques_hist(E):
    fm = E.groupby(E.index.to_period("M")).last()
    v = np.r_[1.0, fm.values]
    m = pd.Series(v[1:] / v[:-1] - 1, index=fm.index)
    fen = v[12:] / v[:-12]
    return dict(a_med_mois=m.median(), b_moy_mois=m.mean(), c_geo_med=v[-1] ** (1 / len(m)) - 1,
                d_rythme12=np.median(fen) ** (1 / 12) - 1, e_mois_neg=(m < 0).mean(),
                f_exp_moylog=np.exp(np.log1p(m).mean()) - 1, med_V12=np.median(fen), n_fen12=len(fen),
                p_annee_perte=(fen < 1).mean(), asym=m.skew(), n_mois=len(m), fin=v[-1],
                pire_baisse=-(E / np.maximum(E.cummax(), 1.0) - 1).min(), meilleur_mois=m.max(), pire_mois=m.min())


# ------------------------------------------------------------------ note de l'expert
def positions_par_jour(d, span=48, heures=BJ.H_H1, debut=60):
    """Copie de la logique d'entree / sortie de banc_bt_regulier.simule : rend (nb paniers, positions fermees par jour)."""
    c, hi, lo, sp, t = (d[x].values for x in ("cloture", "haut", "bas", "sp", "heure"))
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    P, ouvert = [], {}
    for i in range(debut, len(c)):
        for s in list(ouvert):
            p = ouvert[s]
            niveau = p["meilleur"] - s * p["stop"]
            if (lo[i] <= niveau) if s > 0 else (hi[i] + sp[i] >= niveau):
                P.append((t[i], len(ouvert.pop(s)["e"])))
                continue
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            while len(p["e"]) < BR.MAXP and s * (c[i] - p["prochain"]) >= 0:
                if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                    p["e"].append(c[i])
                p["prochain"] += s * p["pas"]
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if s not in ouvert:
                ouvert[s] = {"e": [c[i]], "meilleur": c[i], "stop": BR.STOP * atr[i], "pas": BR.PAS * atr[i],
                             "prochain": c[i] + s * BR.PAS * atr[i]}
    P = pd.DataFrame(P, columns=["t", "n"])
    return len(P), P.n.sum(), pd.Series(P.n.values.astype(float), index=pd.to_datetime(P.t, unit="s").dt.normalize()).groupby(level=0).sum()


def stats_simples(r):
    E = (1 + r).cumprod()
    fm = E.groupby(E.index.to_period("M")).last(); v = np.r_[1.0, fm.values]; m = v[1:] / v[:-1] - 1
    return dict(total=v[-1] - 1, geo_mois=v[-1] ** (1 / len(m)) - 1, meilleur_mois=m.max(), pire_mois=m.min(),
                pire_baisse=-(E / np.maximum(E.cummax(), 1.0) - 1).min(), n_mois=len(m), mois_neg=(m < 0).mean())


# ------------------------------------------------------------------ principal
if __name__ == "__main__":
    X, gh = PC.series()
    cols = list(X.columns); w = PC.parite(X[cols])
    Xa = {s: PC.ampute(X[cols], a) for s, a in SC.items()}
    IA = PC.tirages(len(X))                                   # 1er appel du generateur de banc_plan_cent = ses tirages
    L30 = PC.calibre((Xa["prudent"].values @ w)[IA], 0.30)
    IB = BRT.tirages(len(X), 2 * J12)[:, :J12]                # tirages de banc_dix (24 mois), 12 premiers mois
    print("Donnees %s -> %s (%d jours), bt_or %+.0f R ; poids %s ; L plan -30 %% = %.4f (controle 7,4975)" % (
        X.index[0].date(), X.index[-1].date(), len(X), gh.sum(), np.round(w, 3), L30))
    print("Reglages : les deux bancs importent les memes series, poids, L, courbe hebdo et ampute ; differences = "
          "jeu de tirages (A / B) et arret (aucun / -34 %).")

    rows = []
    print("\n=== Monte-Carlo 12 mois, %d tirages, plan -30 %% (L %.3f)" % (PC.NPAR, L30))
    print("%-4s %-10s %-8s | %8s %8s %8s %8s %6s | %8s | %6s %6s %7s %6s" % (
        "tir.", "arret", "scen.", "(a)medM", "(b)moyM", "(c)geo", "(d)ryt12", "(e)M<0", "(f)explog",
        "medV12", "moyV12", "P(an<0)", "asym"))
    for tn, I in (("A", IA), ("B", IB)):
        for arr in ("sans", "-34%"):
            for s in SC:
                V = PC.courbe((Xa[s].values @ w)[I], L30)
                tau = np.full(len(V), J12)
                if arr != "sans":
                    V, _, _, tau = DIX.arrete(V, V, np.zeros_like(V), SEUIL)
                r = metriques_mc(V); r["p_arret"] = (tau < J12).mean()
                print("%-4s %-10s %-8s | %+7.2f%% %+7.2f%% %+7.2f%% %+7.2f%% %5.0f%% | %+7.2f%% | %6.3f %6.3f %6.1f%% %6.2f" % (
                    tn, arr, s, 100 * r["a_med_mois"], 100 * r["b_moy_mois"], 100 * r["c_geo_med"], 100 * r["d_rythme12"],
                    100 * r["e_mois_neg"], 100 * r["f_exp_moylog"], r["med_V12"], r["moy_V12"], 100 * r["p_annee_perte"], r["asym"]))
                rows.append(dict(partie="monte-carlo", tirages=tn, arret=arr, scenario=s, L=L30, **r))

    print("\n=== Rejeu historique reel (UNE trajectoire, mise hebdo, L %.3f ; scenarios appliques a l'histoire)" % L30)
    print("%-10s %-8s | %8s %8s %8s %8s %6s | %8s | %5s %6s %7s %6s %-10s" % (
        "arret", "scen.", "(a)medM", "(b)moyM", "(c)geo", "(d)ryt12", "(e)M<0", "(f)explog", "nmois", "fin x", "pire bs", "asym", "arret le"))
    for arr in ("sans", "-34%"):
        for s in SC:
            E, _ = PC.rejeu(pd.Series(Xa[s].values @ w, index=X.index), L30)
            quand = "-"
            if arr != "sans":
                E, quand = gele(E, SEUIL)
            r = metriques_hist(E)
            print("%-10s %-8s | %+7.2f%% %+7.2f%% %+7.2f%% %+7.2f%% %5.0f%% | %+7.2f%% | %5d %6.2f %6.1f%% %6.2f %-10s" % (
                arr, s, 100 * r["a_med_mois"], 100 * r["b_moy_mois"], 100 * r["c_geo_med"], 100 * r["d_rythme12"],
                100 * r["e_mois_neg"], 100 * r["f_exp_moylog"], r["n_mois"], r["fin"], 100 * r["pire_baisse"], r["asym"], quand))
            rows.append(dict(partie="historique", tirages="-", arret=arr, scenario=s, L=L30, arret_le=quand, **r))

    # ---------------------------------------------------------- note de l'expert
    print("\n=== Note de l'expert : 50 % bt_or + 50 % repli d'indices, sans levier (cible : +20,87 %% en 4 ans, "
          "+0,40 %%/mois, meilleur mois +4,53 %%, pire baisse -5,36 %%)")
    dh = BR.charge("xau_h1_50k"); dh = dh[dh.heure >= BM.DEB.timestamp()].reset_index(drop=True)
    (Pi, _, _), _, ED = BJ.simule_j(dh, span=48, heures=BJ.H_H1, debut=60)
    npan, npos, posj = positions_par_jour(dh)
    B = pd.bdate_range(X.index[0], X.index[-1])
    notion = BM.vers_ouvres(ED[0].diff().fillna(ED[0].iloc[0]) / (BJ.USD * 1e4), B).reindex(X.index).fillna(0)
    posj = BM.vers_ouvres(posj, B).reindex(X.index).fillna(0)
    with contextlib.redirect_stdout(io.StringIO()):
        D = BP.donnees()
    idx = D["SP"].index
    BP.COUT, cout0 = 4e-4, BP.COUT
    rep4 = sum(BM.vers_ouvres(BP.piece_repli(D, n)[0].reindex(idx).fillna(0), B) for n in ("SP", "NAS", "DJ", "RUT")) / 4
    BP.COUT = cout0
    rep4 = rep4.reindex(X.index).fillna(0)
    print("  paniers bt_or %d (controle 956, simule_j %d), positions %d ; bt_or %+.1f %% du notionnel par position cumule "
          "(%.1f R) ; repli_ind %+.1f %% (frais labo) / %+.1f %% (0,04 %%)" % (
              npan, len(Pi), npos, 100 * notion.sum(), 100 * X.bt_or.sum(), 100 * X.repli_ind.sum(), 100 * rep4.sum()))
    print("  %-48s %-9s | %8s %7s %8s %8s %8s %5s" % ("interpretation", "fenetre", "total", "geo/m", "meill.M", "pire M", "pire bs", "nmois"))
    VAR = {"bt_or notionnel 1/pos, frais labo": (notion, X.repli_ind),
           "bt_or notionnel 1/pos, +0,04 %/AR": (notion - 4e-4 * posj, rep4),
           "bt_or notionnel 1/3 par pos, frais labo": (notion / 3, X.repli_ind),
           "bt_or notionnel 1/3 par pos, +0,04 %/AR": ((notion - 4e-4 * posj) / 3, rep4),
           "bt_or en R (1 R = 1 %), frais labo": (X.bt_or, X.repli_ind)}
    deb48 = X.index[-1] - pd.DateOffset(months=48)
    for nom, (b, r) in VAR.items():
        for fen, deb in (("entiere", X.index[0]), ("48 mois", deb48)):
            p = (0.5 * b + 0.5 * r)[X.index > deb]
            z = stats_simples(p)
            print("  %-48s %-9s | %+7.2f%% %+6.2f%% %+7.2f%% %+7.2f%% %7.2f%% %5d" % (
                nom, fen, 100 * z["total"], 100 * z["geo_mois"], 100 * z["meilleur_mois"], 100 * z["pire_mois"],
                100 * z["pire_baisse"], z["n_mois"]))
            rows.append(dict(partie="note expert", scenario=nom, arret=fen, **z))

    pd.DataFrame(rows).to_csv(os.path.join(ICI, "donnees", "reconcilie.csv"), index=False, float_format="%.5g")
    print("\nEcrit donnees/reconcilie.csv (%d lignes). Duree %.0f s." % (len(rows), time.time() - T00))
