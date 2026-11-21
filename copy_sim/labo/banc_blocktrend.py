"""Banc M : la MECANIQUE de BlockTrend refaite sur les bougies M5 du courtier (regles : labo/BLOCK_REGLES.md).
Sens : cloture contre l'EMA de 2 jours (576 bougies M5). Entree aux heures serveur 03:05, 08:00, 08:30, 12:00, 15:45,
16:00, 16:30 s'il n'y a pas de panier de ce cote. Ajouts dans le sens du prix (pyramide) : +1 position de meme
taille a chaque « pas » franchi a la cloture M5 (niveau saute si la cloture est deja a plus d'un demi-pas au-dela),
10 positions au plus. Sortie de tout le panier quand le prix recule de la distance « stop » depuis son meilleur
niveau (stop suiveur ; au depart = stop initial). Distances en multiples de l'ATR journalier 20 jours de la veille.
Couts : spread reel a l'entree de chaque position (le swap de quelques jours n'est pas compte).
Resultat en « R » : 1 R = perte d'UNE position au stop initial (donc taille au risque constant, comme le robot).
Usage : python3 banc_blocktrend.py [ident]"""
import sys
import numpy as np, pandas as pd
import banc_grille as G

HEURES = {(3, 5), (8, 0), (8, 30), (12, 0), (15, 45), (16, 0), (16, 30)}


def simule(d, pas_k, stop_k, max_pos=10, cotes=(1, -1)):
    c, hi, lo, sp, t = (d[x].values for x in ("cloture", "haut", "bas", "sp", "heure"))
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=576, min_periods=576).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr_j = tr.rolling(20).mean().shift(1)
    atr = atr_j.reindex(jour).values
    paniers = []                      # (indice entree, sens, n positions, gain total en R, duree en bougies)
    ouvert = {}
    for i in range(600, len(c)):
        for s in list(ouvert):
            p = ouvert[s]
            # stop suiveur : touche dans la bougie ? (prudent : on regarde le stop avant le nouveau meilleur)
            niveau = p["meilleur"] - s * p["stop"]
            touche = (lo[i] <= niveau) if s > 0 else (hi[i] + sp[i] >= niveau)
            if touche:
                gain = sum(s * (niveau - e) for e in p["entrees"]) / p["stop"]
                paniers.append((p["i"], s, len(p["entrees"]), gain, i - p["i"]))
                del ouvert[s]
                continue
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            if len(p["entrees"]) < max_pos:
                while s * (c[i] - p["prochain"]) >= 0 and len(p["entrees"]) < max_pos:
                    if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                        p["entrees"].append(c[i] + (sp[i] if s > 0 else 0.0))
                    p["prochain"] += s * p["pas"]
        if (hh[i], mm[i]) in HEURES and atr[i] == atr[i] and ema[i] == ema[i]:
            s = 1 if c[i] > ema[i] else -1
            if s in cotes and s not in ouvert:
                e = c[i] + (sp[i] if s > 0 else 0.0)
                ouvert[s] = {"i": i, "entrees": [e], "meilleur": c[i], "stop": stop_k * atr[i], "pas": pas_k * atr[i],
                             "prochain": c[i] + s * pas_k * atr[i]}
                # le vendeur rachete a l'ask : on compte son spread a l'entree (meme cout)
                if s < 0:
                    ouvert[s]["entrees"][0] = c[i] - sp[i]
    return paniers


def resume(nom, P, n):
    if not P:
        print("  %-44s aucun panier" % nom); return
    i = np.array([p[0] for p in P]); g = np.array([p[3] for p in P]); k = np.array([p[2] for p in P]); s = np.array([p[1] for p in P])
    b = [int(n * q / 5) for q in range(6)]
    par = " ".join("%+6.1f" % g[(i >= b[q]) & (i < b[q + 1])].sum() for q in range(5))
    cum = np.cumsum(g)
    print("  %-44s %4d paniers  total %+7.1f R  moyenne %+5.2f R (t=%+.1f)  gagnants %2.0f %%  positions/panier %.1f  pire creux %+6.1f R | par tranche : %s | achats %+.1f ventes %+.1f" % (
        nom, len(g), g.sum(), g.mean(), g.mean() / g.std() * np.sqrt(len(g)), 100 * (g > 0).mean(), k.mean(),
        (cum - np.maximum.accumulate(cum)).min(), par, g[s > 0].sum(), g[s < 0].sum()))


if __name__ == "__main__":
    for ident in (sys.argv[1:] or ["xau_m5_90k", "nas_m5_90k"]):
        d = G.charge(ident)
        t0, t1 = pd.to_datetime(d["heure"].iloc[[0, -1]], unit="s")
        print("\n%s : %d bougies M5, %s -> %s" % (ident, len(d), t0.date(), t1.date()))
        for nom, a in (("reglage serre (pas 0,25 ; stop 0,667 ATR)", (0.25, 0.6667)),
                       ("reglage tres large (pas 0,5 ; stop 1,5 ATR)", (0.5, 1.5)),
                       ("serre, SANS pyramide (1 position)", (0.25, 0.6667, 1)),
                       ("tres large, SANS pyramide", (0.5, 1.5, 1)),
                       ("serre, pyramide de 3 au plus", (0.25, 0.6667, 3))):
            resume(nom, simule(d, *a), len(d))
