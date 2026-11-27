"""Banc « Ajout au lot M » (PRIORITES 27/11 12 h 50, Baptiste : « si ça redescend, au moins récupérer un peu de gain et
pas être à zéro »). CONTRAT FIGÉ ET POUSSÉ AVANT TOUT RÉSULTAT DE CES VARIANTES.

CADRE ET ÉPREUVES : ceux de banc_lotm_astra.py (contrat 4affbbf), dont on réutilise le moteur, l'argent et le
Monte-Carlo apparié (mêmes 2 000 tirages de blocs de semaines, 20 000 USC, base v3 0,05, règles courtes, garde-fou
-5 %/jour, arrêt -34 % sur equity flottante). Référence V4 = sortie actuelle (point mort = prix moyen + spread dès 4
positions, paliers 0,5 / 0,35 ATR à +2 / +4 R).
VARIANTES (10) — seul change le PLANCHER dès 4 positions (le plus protecteur avec la sortie v4 s'applique) :
  F10, F20, F30 : plancher = prix moyen + spread + 0,10 / 0,20 / 0,30 ATR (au-dessous en vente) au lieu de prix
                  moyen + spread (k = 0,10 avait été vu au lot M « point mort + k », non retenu : refait ici en argent) ;
  G20, G30      : en plus du point mort v4, une fois le gain latent maximal du panier >= 3 R (R = 0,6667 ATR x 1 base,
                  gain calculé à la clôture, jambes réelles), plancher = prix où le gain latent vaut 20 / 30 % de ce
                  maximum (prix moyen réel + gain gardé / taille) ;
  F10R3, F20R3, F30R3, G20R3, G30R3 : la même chose + la règle « rejet » d'Astra à 3 clôtures (R3, celle qu'Astra
                  classe devant R2 ; prix moyen virtuel pour le point mort comme dans banc_lotm_astra, le gain gardé de
                  G se calcule sur les jambes réelles).
MESURES : comme banc_lotm_astra (R à risque égal : gain÷pire baisse et Sharpe principal, total et gain÷pire baisse
  réserve, total au spread doublé ; argent : P(arrêt), médiane, 10e centile, écarts à V4 avec IC 90 %).
  En plus (demandé) : paniers qui RETOMBENT = paniers V4 de >= 4 positions dont le gain latent maximal a atteint >= 2 R
  et qui finissent à <= +0,5 R (principal) : nombre, gain moyen V4 et gain moyen de la variante sur les mêmes paniers ;
  GRANDS PANIERS COUPÉS TROP TÔT = paniers V4 >= +5 R que la variante finit à moins de la moitié ; 5 plus grands.
PLACEBO : signes des différences appariées (paniers de même ouverture) tirés au hasard, 2 000 tirages, principal (comme
  les lots J/K/M de sortie) ; p = part des placebos à somme >= réelle. Holm sur les 10.
ADOPTION : celle de banc_lotm_astra (moins d'arrêts ET médiane >= V4 ; gain÷pire baisse ET Sharpe > V4 principal ;
  total ET gain÷pire baisse > V4 réserve ; > V4 spread doublé ; p Holm < 0,05).
PANIER RÉEL DU 27/11 (descriptif) : 0,02 @ 3 563,54 / 0,04 @ 3 598,58 / 0,06 @ 3 648,08 / 0,08 @ 3 677,30, meilleur
  ≈ 3 685 $, ATR ≈ 110,19 $ (0,6667 ATR = 73,46 $) : pour chaque variante, niveau du plancher et gain en $ gardé si le
  prix redescend jusqu'à lui (et, avec R3, si la 4e jambe sort à 3 671,79 $).
Si une variante est ADOPTÉE : préparer la v5 réelle SANS la publier ; accord écrit de Baptiste avant toute installation.
Usage : python3 banc_lotm_plancher.py
"""
import os, time, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_loth as H, banc_lotg as G, banc_lotl as LL
import banc_lotm_astra as M

ICI = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(M.GRAINE + 50)
VAR = {"V4": (None, None, None)}
for k_ in (0.10, 0.20, 0.30):
    VAR["F%d" % round(k_ * 100)] = (None, None, ("F", k_))
for g_ in (0.20, 0.30):
    VAR["G%d" % round(g_ * 100)] = (None, None, ("G", g_))
for v in list(VAR)[1:]:
    VAR[v + "R3"] = ("rejet", 3, VAR[v][2])


def etude(n_mc=2000, n_plac=2000):
    t0 = time.time()
    d, k = G.jeu_m5(); k.pop("bars_h")
    E1 = {v: M.simule(d, mode=m, prm=x, plancher=pl, **k)[0] for v, (m, x, pl) in VAR.items()}
    E2 = {v: M.simule(d, mode=m, prm=x, plancher=pl, mult=2.0, **k)[0] for v, (m, x, pl) in VAR.items()}
    C1, C2 = LL.courtes([]), LL.courtes([], mult=2.0)
    princ = lambda P: P[P.d1 <= M.FIN]
    sd = lambda P: princ(P).groupby("jour").g.sum().reindex(pd.date_range("2025-08-06", "2026-08-31"), fill_value=0).std()
    ref = E1["V4"]; s_ref = sd(ref); pr0 = princ(ref)
    retombe = pr0[(pr0.npos >= 4) & (pr0.mfe >= 2) & (pr0.g <= 0.5)]
    grands = pr0[pr0.g >= 5]; top5 = pr0.nlargest(5, "g")
    S1 = {v: M.par_semaine(E1[v], C1) for v in E1}; S2 = {v: M.par_semaine(E2[v], C2) for v in E2}
    B = M.tirages(len(S1["V4"][0]), n_mc)
    L, MC = [], {}
    for v in VAR:
        P = E1[v]; f = s_ref / sd(P); Q = P.assign(g=P.g * f)
        mp_, mr = H.mesures(princ(Q)), H.mesures(Q[Q.d1 >= M.R0])
        g = princ(P).set_index("t0").g
        row = dict(variante=v, total_brut=princ(P).g.sum(), facteur=f, g_creux=mp_["g_creux"], sharpe=mp_["sharpe"],
                   res_total=mr["total"], res_g_creux=mr["g_creux"], total_x2=princ(E2[v]).g.sum() * f,
                   retombent_n=len(retombe), retombent_v4=retombe.g.mean(), retombent_var=g.reindex(retombe.t0).mean(),
                   grands_coupes="%d/%d" % ((g.reindex(grands.t0).fillna(0) < 0.5 * grands.g.values).sum(), len(grands)),
                   top5_v4=top5.g.sum(), top5_var=g.reindex(top5.t0).fillna(0).sum())
        if v != "V4":
            m = pr0.merge(princ(P), on="t0", suffixes=("_r", "_v")); dif = (m.g_v - m.g_r).values
            row["placebo_p"] = float((np.array([(dif * rng.choice((-1, 1), len(dif))).sum() for _ in range(n_plac)]) >= dif.sum()).mean())
        sem, w0 = S1[v]
        MC[v] = M.mc_par(sem, P, B)
        x1 = M.rejeu(sem, P, w0); x2 = M.rejeu(S2[v][0], E2[v], S2[v][1])
        row.update(his_total=M.mes_eq(x1[:M.FIN])["total"], his_res=M.mes_eq(x1[M.R0 - pd.Timedelta(days=1):])["total"],
                   his_x2=M.mes_eq(x2[:M.FIN])["total"])
        L.append(row); print(v, "%.0f s" % (time.time() - t0), flush=True)
    T = pd.DataFrame(L).set_index("variante")
    a0 = MC["V4"].arret.values.astype(float); f0 = MC["V4"].final.values
    for v in VAR:
        a = MC[v].arret.values.astype(float); fv = MC[v].final.values
        da, dm = M.ic(a0, a, np.mean), M.ic(f0, fv, np.median)
        T.loc[v, "p_arret"] = a.mean(); T.loc[v, "d_arret_ic"] = "%+.3f [%.3f ; %.3f]" % da
        T.loc[v, "final_med"] = np.median(fv); T.loc[v, "d_med_ic"] = "%+.0f [%.0f ; %.0f]" % dm
        T.loc[v, "final_p10"] = np.quantile(fv, 0.1)
    idx = [v for v in VAR if v != "V4"]
    T.loc[idx, "p_holm"] = H.holm(T.loc[idx, "placebo_p"].values)
    r0 = T.loc["V4"]
    T["adoptee"] = [bool(v != "V4" and r.p_arret < r0.p_arret and r.final_med >= r0.final_med and r.g_creux > r0.g_creux
                         and r.sharpe > r0.sharpe and r.res_total > r0.res_total and r.res_g_creux > r0.res_g_creux
                         and r.total_x2 > r0.total_x2 and r.p_holm < 0.05) for v, r in T.iterrows()]
    return T


def panier_27():
    lots = np.array([0.02, 0.04, 0.06, 0.08]); px = np.array([3563.54, 3598.58, 3648.08, 3677.30])
    A, best, sp = 110.19, 3685.0, 0.2
    unite = 0.6667 * A * 0.02
    def gain(niv, l=lots, p=px):
        return float((l * (niv - p)).sum())
    out = []
    for v, (m, x, pl) in VAR.items():
        for avec in ((False, True) if m == "rejet" else (False,)):
            l, p = (lots[:3], px[:3]) if avec else (lots, px)
            hors = 0.08 * (3671.79 - 3677.30) if avec else 0.0
            moyen_v = (lots * px).sum() / lots.sum()            # prix moyen virtuel (pyramide complète)
            niv = moyen_v + sp + (pl[1] * A if pl and pl[0] == "F" else 0.0)
            gmax = gain(best - sp)                              # maximum atteint avec les 4 jambes
            if pl and pl[0] == "G" and gmax >= 3 * unite:
                niv = max(niv, (l * p).sum() / l.sum() + pl[1] * gmax / l.sum())
            out.append(dict(variante=v + (" (4e jambe sortie)" if avec else ""), plancher=niv,
                             gain_si_retour_plancher=gain(niv, l, p) + hors, gmax_R=gmax / unite))
    return pd.DataFrame(out)


if __name__ == "__main__":
    pd.set_option("display.width", 320); pd.set_option("display.max_columns", 50)
    T = etude(); T.to_csv(os.path.join(ICI, "donnees", "lotm_plancher.csv"))
    print(T.round(3).to_string())
    print(panier_27().round(2).to_string(index=False))
