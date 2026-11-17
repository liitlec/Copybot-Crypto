"""Banc AC : cassure de la fourchette d'ouverture (ORB) sur les indices americains (PRIORITES 15/11 15 h et 17/11
10 h 30). Bougies du courtier, spread reel ; le serveur est a New York + 7 h, donc l'ouverture de 9 h 30 tombe a
16:30 serveur (15 h 30 a Paris) et la cloture de 16 h a 23:00.
Regle classique : fourchette = plus haut / plus bas des N premieres minutes (5, 15, 30) ; entree a l'ouverture de la
bougie qui suit la premiere cloture hors de la fourchette, avant 12 h (New York) ; stop = l'autre borne de la
fourchette (ou son milieu) ; objectif = 1 R, 2 R ou aucun ; sortie a 15 h 55 au plus tard ; un trade par jour.
Resultat en R (1 R = distance entree - stop) apres spread, et en points de base. Reglage = 1re moitie, verdict = 2de.
Usage : python3 banc_orb.py [ident ...]"""
import sys
import numpy as np, pandas as pd
import banc_grille as G


def orb(d, pas, n_min, stop_mode, obj):
    t = d["heure"].values
    o, h, l, c, sp = (d[x].values for x in ("ouverture", "haut", "bas", "cloture", "sp"))
    mn = (t // 60) % 1440
    jour = t // 86400
    out = []
    for j in np.unique(jour):
        ix = np.flatnonzero(jour == j)
        m = mn[ix]
        a = ix[(m >= 990) & (m < 990 + n_min)]                    # 16:30 serveur = 990 min
        if len(a) < n_min // pas:
            continue
        hi, lo = h[a].max(), l[a].min()
        suite = ix[(m >= 990 + n_min) & (m < 1375)]               # jusqu'a 22:55
        if len(suite) < 5 or hi <= lo:
            continue
        e = None
        for k in suite:
            if mn[k] >= 1140:                                     # 19:00 serveur = 12 h New York : plus d'entree
                break
            s = 1 if c[k] > hi else (-1 if c[k] < lo else 0)
            if s:
                e = k + 1; break
        if e is None or e > suite[-1]:
            continue
        px = o[e] + (sp[e] if s > 0 else 0)                       # achat a l'ask ; bougies en prix vendeur
        ref = (lo if s > 0 else hi) if stop_mode == "borne" else (hi + lo) / 2
        R = abs(px - ref)
        if R <= 0:
            continue
        stop = px - s * R
        cible = px + s * obj * R if obj else None
        x = None
        for k in suite[suite >= e]:
            bas_k, haut_k = l[k], h[k] + sp[k]
            if (s > 0 and bas_k <= stop) or (s < 0 and haut_k >= stop):
                x = stop; break
            if cible is not None and ((s > 0 and h[k] >= cible) or (s < 0 and l[k] + sp[k] <= cible)):
                x = cible; break
        if x is None:
            k = suite[-1]
            x = c[k] + (sp[k] if s < 0 else 0)
        out.append((t[e], s * (x - px) / R, s * (x - px) / px * 1e4, s))
    return pd.DataFrame(out, columns=["t", "R", "bp", "s"])


def st(x):
    if len(x) < 10:
        return "%3d tr       -            " % len(x)
    return "%3d tr %+5.2f R (t %+.1f), %+5.1f bp, %2.0f %% gagn." % (len(x), x.R.mean(), x.R.mean() / x.R.std() * np.sqrt(len(x)), x.bp.mean(), 100 * (x.R > 0).mean())


if __name__ == "__main__":
    for ident in (sys.argv[1:] or ["nas_m5_90k", "nas_m1_90k", "sp_m1_90k"]):
        d = G.charge(ident)
        pas = int(np.median(np.diff(d["heure"].values[:500])) // 60)
        t0, t1 = pd.to_datetime(d["heure"].iloc[[0, -1]], unit="s")
        mil = d["heure"].iloc[len(d) // 2]
        print("\n%s (bougies de %d min, %s -> %s) : reglage | verdict" % (ident, pas, t0.date(), t1.date()))
        for n_min in (5, 15, 30):
            if n_min < pas:
                continue
            for stop_mode in ("borne", "milieu"):
                for obj in (1, 2, 0):
                    x = orb(d, pas, n_min, stop_mode, obj)
                    print("  fourchette %2d min, stop %-6s, objectif %-5s | %s | %s" % (
                        n_min, stop_mode, ("%d R" % obj) if obj else "aucun", st(x[x.t < mil]), st(x[x.t >= mil])))
