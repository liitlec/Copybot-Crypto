"""Banc Lot I (PRIORITES 26/11 22 h 05). Point 1 : risque d'arrêt -34 % par base (0,02 / 0,03 / 0,04 / 0,05), même
Monte-Carlo (blocs de semaines, longueur moyenne 4, 2 000 parcours) et rejeu que le lot H (banc_loth), 20 000 USC,
12 mois, mise v3 (base = b x solde / 20 000, vers le bas au pas 0,01, fixée par panier, jamais au-dessus de b),
règles courtes comprises sur M5 (0,01 lot cent chacune, x solde/20 000, au moins 0,01 ; H1 4 ans : pas de données
M1/M15 avant 08/2025, donc bt_or_plus seul). Prudent = avantage moyen de chaque famille divisé par 2.
Point 2 : voir le contrat plus bas (figé avant ses résultats)."""
import os, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_loth as H
import banc_lotg as G

ICI = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(2611)
DEPART = 20000.0


def evenements(P, courtes=None):
    """Liste triée (heure de sortie, famille, valeur) : bt = USD par lot de base ; c = USC à 0,01 lot."""
    ev = [(t, "bt", u) for t, u in zip(P.t1.values, P.usd.values)]
    if courtes is not None:
        ev += [(t, "c", g) for t, g in zip(courtes.t.values, courtes.g.values)]
    ev.sort(key=lambda x: x[0])
    return ev


def chemin(ev, b, prud):
    solde = haut = DEPART; pire = 0.0
    for _, k, v in ev:
        if k == "bt":
            base = min(np.floor(b * solde / DEPART / 0.01 + 1e-9) * 0.01, b)
            if base < 0.01:
                return dict(final=solde, pire=pire, arret=True)
            solde += base * (v - prud["bt"]) * 100.0
        else:
            lot = max(np.floor(0.01 * solde / DEPART / 0.01 + 1e-9) * 0.01, 0.01)
            solde += (v - prud["c"]) * lot / 0.01
        haut = max(haut, solde); pire = min(pire, solde / haut - 1)
        if solde <= (1 - H.ARRET) * haut:
            return dict(final=solde, pire=pire, arret=True)
    return dict(final=solde, pire=pire, arret=False)


def semaines(ev):
    s = pd.Series([pd.Timestamp(t, unit="s").to_period("W") for t, _, _ in ev])
    toutes = pd.period_range(s.min(), s.max(), freq="W")
    par = {w: [] for w in toutes}
    for w, e in zip(s, ev):
        par[w].append(e)
    return [par[w] for w in toutes]


def mc(liste, b, prud, mois=12, n=2000):
    Hn = int(round(mois * 4.33)); R = []
    for _ in range(n):
        ev, k, i = [], 0, rng.integers(len(liste))
        while k < Hn:
            if rng.random() < 0.25:
                i = rng.integers(len(liste))
            ev += liste[i % len(liste)]; k += 1; i += 1
        R.append(chemin(ev, b, prud))
    return pd.DataFrame(R)


def point1():
    J = H.jeux()
    P5, Ph = H.simule(*[J["M5"][0]], **J["M5"][1]), H.simule(*[J["H1"][0]], **J["H1"][1])
    debut = pd.Timestamp("2025-08-06")
    C = []
    for nom, (fic, regle, ks, hs, ref) in G.REGLES.items():
        d = G.charge_tf(fic, debut)
        T = G.joue(d, G.signal(d, regle, ref[0]), ref[1], None, retour=(regle == "retour"))
        C.append(T.assign(t=(T.t - pd.Timestamp("1970-01-01")).dt.total_seconds().astype(int)))
    C = pd.concat(C)
    jeux = {"H1 4 ans (bt_or_plus)": evenements(Ph), "M5 15 mois (bt_or_plus + courtes)": evenements(P5, C)}
    moy = {"H1 4 ans (bt_or_plus)": {"bt": Ph.usd.mean(), "c": 0.0},
           "M5 15 mois (bt_or_plus + courtes)": {"bt": P5.usd.mean(), "c": C.g.mean()}}
    lignes = []
    for j, ev in jeux.items():
        L = semaines(ev)
        for b in (0.02, 0.03, 0.04, 0.05):
            for scen in ("mesure", "prudent"):
                prud = {k: (max(v, 0) / 2 if scen == "prudent" else 0.0) for k, v in moy[j].items()}
                R = mc(L, b, prud)
                lignes.append(dict(jeu=j, base=b, scenario=scen, p_arret=R.arret.mean(), pire_med=R.pire.median(),
                                   final_med=R.final.median(), final_p10=R.final.quantile(0.1)))
    T = pd.DataFrame(lignes)
    # rejeux réels de 12 mois
    rj = []
    for j, ev, debuts in (("H1", jeux["H1 4 ans (bt_or_plus)"], ("2022-08-01", "2023-08-01", "2024-10-01", "2025-11-01")),
                          ("M5", jeux["M5 15 mois (bt_or_plus + courtes)"], ("2025-08-06",))):
        for d0 in debuts:
            a = pd.Timestamp(d0).timestamp(); z = (pd.Timestamp(d0) + pd.DateOffset(months=12)).timestamp()
            e = [x for x in ev if a <= x[0] < z]
            for b in (0.02, 0.03, 0.04, 0.05):
                r = chemin(e, b, {"bt": 0.0, "c": 0.0})
                rj.append(dict(jeu=j, debut=d0, base=b, final=r["final"], pire=r["pire"], arret=r["arret"]))
    return T, pd.DataFrame(rj)


if __name__ == "__main__":
    T, R = point1()
    T.to_csv(os.path.join(ICI, "donnees", "loti_bases.csv"), index=False)
    pd.set_option("display.width", 250)
    print(T.round(3).to_string(index=False)); print(R.round(3).to_string(index=False))


CONTRAT_POINT2 = """POINT 2 — RENFORT QUAND LE PANIER REVIENT AU POINT MORT. CONTRAT FIGÉ ET POUSSÉ AVANT SES RÉSULTATS.
Mécanique bt_or_plus du lot H (banc_loth.simule, tailles 1-2-3-4-5..., recul 0,6667 ATR, renforts de la grille tous
les 0,25 ATR depuis la 1re entrée). Variantes (8) :
  (a) be      : en plus de la grille, un renfort (taille suivante) à la clôture qui repasse au-dessus du POINT MORT du
                panier (prix moyen pondéré + spread de sortie) quand le panier a >= 2 positions et a été en perte à une
                clôture depuis le dernier renfort ; un seul par passage (il faut repasser en perte pour le suivant) ;
  (b) be+0,10 / be+0,25 : idem, seuil = point mort + 0,10 / 0,25 ATR ;
  (c) moyen   : la grille est comptée depuis le prix moyen du panier : renfort quand la clôture dépasse
                prix moyen + 0,25 ATR (recalculé après chaque renfort), au lieu de la grille fixe ;
  chacune avec 5 positions au plus et avec 6 positions au plus. Même sortie (le stop suiveur ne dépend pas des renforts).
Données : M5 08/2025-11/2026 ; H1 08/2022-11/2026 (B1 = 08/2022-09/2024, B2 = 10/2024-11/2026) ; spread réel puis doublé.
Mesures : total R, gain÷pire baisse et Sharpe journalier (risque égal), sur M5, H1 B1, H1 B2 ; nombre de renforts
« point mort » et leur gain moyen ; en argent : P(arrêt -34 %) en 12 mois, base 0,02 (et 0,05), mise v3, même
Monte-Carlo que le point 1 (bt_or_plus seul), 20 000 USC.
Placebo (a)/(b) : les mêmes renforts supplémentaires (même nombre, mêmes tailles, même panier) placés à une clôture
tirée au hasard dans la vie du panier (2 000 tirages) ; p = part des tirages au gain supplémentaire >= réel.
Placebo (c) : signes des différences appariées par panier tirés au hasard (2 000). Correction : Holm sur les 8.
RETENUE si : gain÷pire baisse ET Sharpe > référence sur M5, H1 B1 ET H1 B2 ; p Holm < 0,05 sur H1 et p < 0,05 sur
M5 ; encore > référence au spread doublé ; P(arrêt -34 %) à base 0,02 pas plus de 2 points au-dessus de la référence.
Si retenue : proposée pour la version réelle suivante, SANS installation (feu vert de Baptiste dans la conversation).
"""
