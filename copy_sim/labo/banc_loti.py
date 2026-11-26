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


def simule2(d, span, heures, debut, mode=None, decal=0.0, maxpos=5, mult=1.0):
    """bt_or_plus (lot H) + renfort au point mort (mode 'be', seuil point mort + decal ATR) ou grille depuis le prix
    moyen (mode 'moyen'). Rend les paniers et, par panier, les renforts 'point mort' (taille, barre)."""
    c, hi, lo, t = (d[x].values for x in ("cloture", "haut", "bas", "heure"))
    sp = d["sp"].values * mult
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    P, X, ouvert = [], [], {}

    def ajoute(p, i, s, be=False):
        p["e"].append(c[i] + (sp[i] if s > 0 else -sp[i])); p["w"].append(float(len(p["w"]) + 1))
        if be:
            p["be"].append((p["w"][-1], i))
        p["perte"] = False

    for i in range(debut, len(c)):
        for s in list(ouvert):
            p = ouvert[s]
            niveau = p["meilleur"] - s * p["recul"]
            if (lo[i] <= niveau) if s > 0 else (hi[i] + sp[i] >= niveau):
                usd = sum(w * s * (niveau - e) for w, e in zip(p["w"], p["e"]))
                P.append((t[p["i"]], t[i], s, usd / p["unite"], usd))
                X.append({"i0": p["i"], "i1": i, "s": s, "sortie": niveau, "unite": p["unite"], "be": p["be"]})
                del ouvert[s]
                continue
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            x = c[i] if s > 0 else c[i] + sp[i]                     # prix de sortie à la clôture
            moyen = sum(w * e for w, e in zip(p["w"], p["e"])) / sum(p["w"])
            latent = s * (x - moyen)
            if mode == "moyen":
                while len(p["e"]) < maxpos and s * (c[i] - (moyen + s * p["pas"])) >= 0:
                    ajoute(p, i, s)
                    moyen = sum(w * e for w, e in zip(p["w"], p["e"])) / sum(p["w"])
            else:
                while len(p["e"]) < maxpos and s * (c[i] - p["prochain"]) >= 0:
                    if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                        ajoute(p, i, s)
                    p["prochain"] += s * p["pas"]
                if mode == "be" and len(p["e"]) >= 2:
                    if latent < 0:
                        p["perte"] = True
                    elif p["perte"] and latent >= decal * p["atr"] and len(p["e"]) < maxpos:
                        ajoute(p, i, s, be=True)
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if s not in ouvert:
                ouvert[s] = {"i": i, "e": [c[i] + (sp[i] if s > 0 else -sp[i])], "w": [1.0], "meilleur": c[i],
                             "recul": 0.6667 * atr[i], "unite": 0.6667 * atr[i], "pas": 0.25 * atr[i], "atr": atr[i],
                             "prochain": c[i] + s * 0.25 * atr[i], "perte": False, "be": []}
    P = pd.DataFrame(P, columns=["t0", "t1", "s", "g", "usd"])
    P["d0"] = pd.to_datetime(P.t0, unit="s"); P["d1"] = pd.to_datetime(P.t1, unit="s"); P["jour"] = P.d1.dt.floor("D")
    return P, X


VARS2 = {"REF": {}}
for mp in (5, 6):
    VARS2["be/%d" % mp] = dict(mode="be", decal=0.0, maxpos=mp)
    VARS2["be+0,10/%d" % mp] = dict(mode="be", decal=0.10, maxpos=mp)
    VARS2["be+0,25/%d" % mp] = dict(mode="be", decal=0.25, maxpos=mp)
    VARS2["moyen/%d" % mp] = dict(mode="moyen", maxpos=mp)


def placebo_be(d, X, mult=1.0, n=2000):
    """Gain supplémentaire réel des renforts 'point mort' et distribution des mêmes renforts à des clôtures au hasard."""
    c, sp = d["cloture"].values, d["sp"].values * mult
    reel, tirages = 0.0, np.zeros(n)
    for x in X:
        if not x["be"]:
            continue
        s, i0, i1, out, u = x["s"], x["i0"], x["i1"], x["sortie"], x["unite"]
        for w, i in x["be"]:
            reel += w * s * (out - (c[i] + (sp[i] if s > 0 else -sp[i]))) / u
            jj = rng.integers(i0 + 1, max(i1, i0 + 2), size=n)
            tirages += w * s * (out - (c[jj] + np.where(s > 0, sp[jj], -sp[jj]))) / u
    return reel, tirages


def point2():
    J = H.jeux()
    R = {}
    for j, (d, k) in J.items():
        for m in (1.0, 2.0):
            R[(j, m)] = {v: simule2(d, mult=m, **k, **prm) for v, prm in VARS2.items()}
    lignes = []
    for j, (d, k) in J.items():
        ref = R[(j, 1.0)]["REF"][0]
        for v in VARS2:
            P, X = R[(j, 1.0)][v]
            row = dict(jeu=j, variante=v, **H.mesures(P))
            if j == "H1":
                for bn, msk in (("B1", P.jour <= H.B1F), ("B2", P.jour >= H.B2_0)):
                    mb = H.mesures(P[msk]); row[bn + "_gc"], row[bn + "_sh"], row[bn + "_tot"] = mb["g_creux"], mb["sharpe"], mb["total"]
            row["total_x2"] = R[(j, 2.0)][v][0].g.sum()
            nbe = [b for x in X for b in x["be"]]
            row["renforts_be"] = len(nbe)
            if v != "REF":
                if VARS2[v].get("mode") == "be":
                    reel, tir = placebo_be(d, X)
                    row["gain_be_R"] = reel; row["gain_be_moyen"] = reel / max(len(nbe), 1)
                    row["placebo_p"] = (tir >= reel).mean(); row["placebo_med"] = np.median(tir)
                else:
                    m = ref.merge(P, on="t0", suffixes=("_r", "_v")); dif = (m.g_v - m.g_r).values
                    row["placebo_p"] = (np.array([(dif * rng.choice((-1, 1), len(dif))).sum() for _ in range(2000)]) >= dif.sum()).mean()
            for b in (0.02, 0.05):
                L = semaines(evenements(P))
                row["arret_%.2f" % b] = mc(L, b, {"bt": 0.0, "c": 0.0}, n=1000).arret.mean()
            lignes.append(row)
    T = pd.DataFrame(lignes)
    h = T[(T.jeu == "H1") & (T.variante != "REF")]
    T.loc[h.index, "p_holm"] = H.holm(h.placebo_p.values)
    r5 = T[(T.jeu == "M5") & (T.variante == "REF")].iloc[0]; rh = T[(T.jeu == "H1") & (T.variante == "REF")].iloc[0]
    def ok(v):
        if v == "REF": return False
        a = T[(T.jeu == "M5") & (T.variante == v)].iloc[0]; b = T[(T.jeu == "H1") & (T.variante == v)].iloc[0]
        return bool(a.g_creux > r5.g_creux and a.sharpe > r5.sharpe and b.B1_gc > rh.B1_gc and b.B1_sh > rh.B1_sh
                    and b.B2_gc > rh.B2_gc and b.B2_sh > rh.B2_sh and b.p_holm < 0.05 and a.placebo_p < 0.05
                    and a.total_x2 > r5.total_x2 and b.total_x2 > rh.total_x2
                    and a["arret_0.02"] <= r5["arret_0.02"] + 0.02 and b["arret_0.02"] <= rh["arret_0.02"] + 0.02)
    T["retenue"] = T.variante.map(ok)
    return T
