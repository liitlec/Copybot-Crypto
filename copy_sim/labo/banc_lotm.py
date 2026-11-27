"""Banc Lot M (27/11, demande de Baptiste : « au min de pas retourner à 0 mais un peu plus quand même »).
CONTRAT FIGÉ ET POUSSÉ AVANT LES RÉSULTATS. Cadre du lot J/K (or M5 courtier, principal 08/2025-08/2026, réserve
09-11/2026, bt_or_plus 1-2-3-4-5, paliers +2/+4 R). Seule change la sortie « point mort » dès 4 positions : au lieu du
prix moyen + spread, prix moyen + spread + k x ATR jour, k = 0 (v4 actuelle), 0,05, 0,10, 0,15, 0,25 ATR (4 variantes).
Mesures et jugement du lot K (à risque égal : gain÷pire baisse et Sharpe sur le principal, total et gain÷pire baisse sur
la réserve, placebo = signes des différences appariées, Holm sur 4, spread doublé, P(arrêt -34 %) à 0,05 au plus +2 pts).
En plus : bénéfice garanti sur le panier réel du 27/11 (4 positions, moyen 3 641,4, ATR ≈ 110 $) pour chaque k.
Si une variante est RETENUE : préparer la v5 sans la publier ; Baptiste décide."""
import os, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_loth as H, banc_loti as I, banc_lotj as LJ, banc_lotg as G

ICI = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(2712)
KS = {"v4 (k=0)": 0.0, "k=0,05": 0.05, "k=0,10": 0.10, "k=0,15": 0.15, "k=0,25": 0.25}


def simule(d, span, heures, debut, k, mult=1.0):
    c, hi, lo, t = (d[x].values for x in ("cloture", "haut", "bas", "heure"))
    sp = d["sp"].values * mult
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
            niv = LJ.niveau_sortie({"pal": (2, 4)}, s, p["meilleur"], p["e"], p["w"], p["A"], p["unite"], 0.0, sp[i])
            if len(p["e"]) >= 4:
                moyen = sum(w * e for w, e in zip(p["w"], p["e"])) / sum(p["w"])
                pm = moyen + s * (sp[i] + k * p["A"])
                niv = max(niv, pm) if s > 0 else min(niv, pm)
            if (lo[i] <= niv) if s > 0 else (hi[i] + sp[i] >= niv):
                usd = sum(w * s * (niv - e) for w, e in zip(p["w"], p["e"]))
                P.append((t[p["i"]], t[i], s, usd / p["unite"], usd))
                del ouvert[s]
                continue
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            while len(p["e"]) < 5 and s * (c[i] - p["prochain"]) >= 0:
                if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                    p["e"].append(c[i] + (sp[i] if s > 0 else -sp[i])); p["w"].append(float(len(p["w"]) + 1))
                p["prochain"] += s * p["pas"]
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if s not in ouvert:
                ouvert[s] = {"i": i, "e": [c[i] + (sp[i] if s > 0 else -sp[i])], "w": [1.0], "meilleur": c[i],
                             "A": atr[i], "unite": 0.6667 * atr[i], "pas": 0.25 * atr[i], "prochain": c[i] + s * 0.25 * atr[i]}
    P = pd.DataFrame(P, columns=["t0", "t1", "s", "g", "usd"])
    P["d0"] = pd.to_datetime(P.t0, unit="s"); P["d1"] = pd.to_datetime(P.t1, unit="s"); P["jour"] = P.d1.dt.floor("D")
    return P
