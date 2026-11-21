"""Banc H : le candidat de midi (or M5, 12-15 h serveur, ecart > 2 ecarts-types a la moyenne de 20 bougies, on parie
sur le retour) avec une tendance de fond et des sorties par objectif / stop simulees dans la bougie.
Bougies en prix vendeur. Si objectif et stop sont touches dans la meme bougie, on compte le stop (prudent).
Usage : python3 banc_sorties.py"""
import numpy as np, pandas as pd
import banc_grille as G, banc_plateau as P


def simule(d, obj_moy, stop_k, tenue_max, heures=(12, 13, 14)):
    c, o, hi, lo, sp = (d[k].values for k in ("cloture", "ouverture", "haut", "bas", "sp"))
    ma = d["cloture"].rolling(20).mean().values
    sd = d["cloture"].rolling(20).std().values
    z = (c - ma) / sd
    N = len(c)
    idx, gains = [], []
    for i in np.where((np.abs(z) > 2) & np.isin(d["h"].values, heures) & (np.arange(N) < N - tenue_max - 2))[0]:
        s = -np.sign(z[i])
        e = o[i + 1] + (sp[i + 1] if s > 0 else 0.0)            # achat a l'ask ; vente au bid
        cible = ma[i] if obj_moy else None
        stop = (e - s * stop_k * sd[i]) if stop_k else None
        sortie = None
        for j in range(i + 1, i + 1 + tenue_max):
            a = sp[j] if s < 0 else 0.0                          # un vendeur rachete a l'ask = bid + spread
            if stop is not None and ((s > 0 and lo[j] <= stop) or (s < 0 and hi[j] + a >= stop)):
                sortie = stop; break
            if cible is not None and ((s > 0 and hi[j] >= cible) or (s < 0 and lo[j] + a <= cible)):
                sortie = cible; break
        if sortie is None:
            j = i + tenue_max
            sortie = c[j] + (sp[j] if s < 0 else 0.0)
        idx.append(i); gains.append(s * (sortie - e) / e * 1e4)
    return np.array(idx), np.array(gains)


if __name__ == "__main__":
    d = G.charge("xau_m5_90k")
    N = len(d); b = [int(N * q / 5) for q in range(6)]
    fond = np.sign(d["cloture"] - d["cloture"].rolling(240).mean()).values      # tendance de fond : 20 h
    print("Sorties (objectif = retour a la moyenne ; stop en ecarts-types ; tenue max en bougies M5)")
    print("%-34s %6s %8s %6s %6s | par tranche" % ("variante", "trades", "net bp", "t", "gagn."))
    n = 0
    for obj in (False, True):
        for sk in (0, 2, 3):
            for tm in (3, 6, 12):
                if not obj and sk == 0 and tm != 3:
                    pass
                i, g = simule(d, obj, sk, tm)
                n += 1
                par = " ".join("%+5.2f" % g[(i >= b[q]) & (i < b[q + 1])].mean() for q in range(5))
                print("%-34s %6d %+8.2f %+6.2f %5.0f%% | %s" % (
                    "objectif=%s stop=%s tenue=%d" % ("moy." if obj else "non", sk or "non", tm), len(g), g.mean(),
                    g.mean() / g.std() * np.sqrt(len(g)), 100 * (g > 0).mean(), par))
    i, g = simule(d, False, 0, 3)
    s = -np.sign(((d["cloture"] - d["cloture"].rolling(20).mean()) / d["cloture"].rolling(20).std()).values[i])
    print("\nTendance de fond (cours contre moyenne de 20 h), sortie au temps 3 bougies :")
    for nom, m in (("dans le sens du fond (acheter un creux en hausse)", s == fond[i]), ("contre le fond", s == -fond[i])):
        par = " ".join("%+5.2f" % g[m & (i >= b[q]) & (i < b[q + 1])].mean() for q in range(5))
        print("  %-50s %5d trades %+6.2f bp t=%+5.2f | %s" % (nom, m.sum(), g[m].mean(), g[m].mean() / g[m].std() * np.sqrt(m.sum()), par))
    print("\nEssais de ce banc :", n + 2)
