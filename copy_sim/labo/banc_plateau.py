"""Banc F : affinage autour du seul plateau du banc E (or M5, milieu de journee, retour apres un ecart a la moyenne).
Regle : z = (cloture - moyenne n) / ecart-type n ; si |z| > s, on parie sur le retour ; entree a l'ouverture suivante,
sortie h bougies plus tard, spread reel paye. Grille : n (15, 20, 30) x s (1,5 / 2 / 2,5) x h (2, 3, 4, 6)
x 5 fenetres d'heures serveur = 180 combinaisons.
Epreuve glissante sur 5 tranches de temps egales : on choisit la meilleure combinaison sur les tranches passees,
on la juge sur la tranche suivante (4 verdicts enchaines, jamais vus au reglage).
Usage : python3 banc_plateau.py [ident]"""
import sys
import numpy as np, pandas as pd
import banc_grille as G

FENETRES = {"11-14h": (11, 12, 13), "12-15h": (12, 13, 14), "13-16h": (13, 14, 15), "12-14h": (12, 13), "toutes": tuple(range(24))}


def gains(d, n, s, h, heures):
    """Gain net (bp) par trade, indice de la bougie de decision."""
    c, o, sp = d["cloture"], d["ouverture"].values, d["sp"].values
    z = ((c - c.rolling(n).mean()) / c.rolling(n).std()).values
    sig = -((z > s).astype(float) - (z < -s).astype(float))
    N = len(c)
    i = np.where((sig != 0) & np.isin(d["h"].values, heures) & (np.arange(N) < N - h - 1))[0]
    ent = o[i + 1]
    g = (sig[i] * (c.values[i + h] - ent) - sp[i + 1]) / ent * 1e4
    return i, g


def t_stat(g, h):
    return g.mean() / g.std() * np.sqrt(len(g) / h) if len(g) > 30 and g.std() > 0 else np.nan


if __name__ == "__main__":
    ident = sys.argv[1] if len(sys.argv) > 1 else "xau_m5_90k"
    d = G.charge(ident)
    N = len(d)
    bornes = [int(N * k / 5) for k in range(6)]
    jours = pd.to_datetime(d["heure"], unit="s")
    print("%s : %d bougies, tranches : %s" % (ident, N, " | ".join(str(jours[b].date()) for b in bornes[:-1])))
    R = {}
    for n in (15, 20, 30):
        for s in (1.5, 2.0, 2.5):
            for h in (2, 3, 4, 6):
                for nf, hs in FENETRES.items():
                    i, g = gains(d, n, s, h, hs)
                    R[(n, s, h, nf)] = [(g[(i >= bornes[k]) & (i < bornes[k + 1])]) for k in range(5)]
    print("\nCombinaison de depart (n=20, s=2, h=3, 12-15h) par tranche : trades, net bp/trade, t")
    for k, g in enumerate(R[(20, 2.0, 3, "12-15h")]):
        print("  tranche %d : %4d trades  %+6.2f bp  t=%+5.2f" % (k + 1, len(g), g.mean(), t_stat(g, 3)))
    print("\nPar tranche : part des 180 combinaisons nettes positives, et des 36 de chaque fenetre")
    for k in range(5):
        tot = np.mean([v[k].mean() > 0 for v in R.values() if len(v[k]) > 30])
        par = {nf: np.mean([v[k].mean() > 0 for c, v in R.items() if c[3] == nf and len(v[k]) > 30]) for nf in FENETRES}
        print("  tranche %d : %3.0f %%   " % (k + 1, 100 * tot) + "  ".join("%s %3.0f %%" % (nf, 100 * p) for nf, p in par.items()))
    print("\nEpreuve glissante : meilleure combinaison (t) sur les tranches passees -> tranche suivante")
    hors = []
    for k in range(1, 5):
        best, bt = None, -9
        for c, v in R.items():
            g = np.concatenate(v[:k])
            t = t_stat(g, c[2])
            if len(g) >= 150 and t == t and t > bt:
                best, bt = c, t
        g = R[best][k]
        hors.append((g, best[2]))
        print("  reglage tranches 1-%d : %s t=%+.2f -> tranche %d : %4d trades %+6.2f bp t=%+5.2f" % (
            k, best, bt, k + 1, len(g), g.mean(), t_stat(g, best[2])))
    tout = np.concatenate([g for g, _ in hors])
    hm = np.mean([h for _, h in hors])
    print("  ENSEMBLE hors echantillon : %d trades, %+.2f bp net par trade, t=%+.2f" % (len(tout), tout.mean(), t_stat(tout, hm)))
    print("\nToutes heures confondues, meme regle (n=20, s=2, h=3), par tranche horaire de 3 h serveur : net bp (trades)")
    print("  " + "  ".join("%02d-%02dh %+5.2f (%d)" % (3 * b, 3 * b + 3, g.mean(), len(g))
                           for b in range(8) for i, g in [gains(d, 20, 2.0, 3, (3 * b, 3 * b + 1, 3 * b + 2))]))
    print("\nEssais de ce banc : 180")
