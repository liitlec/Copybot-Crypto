"""Banc ORB (17/11, PRIORITES 15/11 15 h et 17/11 10 h 30) : la cassure de la fourchette d'ouverture du dépôt
Jakeschincariol/day-trader-skill, sur les indices du courtier (M5, ~15 mois, spread réel). Ouverture US = 16 h 30
serveur (pic de volume vérifié). Règle du dépôt : fourchette des 15 premières minutes (3 bougies M5) ; entrée à la
première clôture M5 au-dessus (achat) / au-dessous (vente) de la fourchette, avant 17 h 45 serveur (« fenêtre ») ;
stop au milieu de la fourchette ; objectif 1 R ; sinon sortie à 22 h 55 serveur. Variantes : objectif 2 R, stop à
l'autre bout, fourchette 30 min. Un trade par jour au plus. Résultat en R (1 R = distance entrée-stop), après spread.
Usage : python3 banc_orb.py"""
import itertools
import numpy as np, pandas as pd
import banc_grille as G


def orb(d, n_or=3, obj=1.0, stop="mid", fin_entree=1745, fin=2255):
    t = d["heure"].values
    hm = ((t // 3600) % 24) * 100 + (t // 60) % 60
    jour = t // 86400
    o, hi, lo, c, sp = (d[x].values for x in ("ouverture", "haut", "bas", "cloture", "sp"))
    R = []
    for j in np.unique(jour):
        idx = np.where(jour == j)[0]
        k0 = idx[hm[idx] == 1630]
        if not len(k0):
            continue
        k0 = k0[0]
        if k0 + n_or >= idx[-1]:
            continue
        H, L = hi[k0:k0 + n_or].max(), lo[k0:k0 + n_or].min()
        if H <= L:
            continue
        for k in range(k0 + n_or, idx[-1] + 1):
            if hm[k] > fin_entree:
                break
            s = 1 if c[k] > H else (-1 if c[k] < L else 0)
            if not s:
                continue
            e = c[k] + (sp[k] if s > 0 else 0.0)
            st = (H + L) / 2 if stop == "mid" else (L if s > 0 else H)
            risque = s * (e - st)
            if risque <= 0:
                break
            cible = e + s * obj * risque
            r = None
            for i in range(k + 1, idx[-1] + 1):
                if (s > 0 and lo[i] <= st) or (s < 0 and hi[i] + sp[i] >= st):
                    r = -1.0; break
                if (s > 0 and hi[i] >= cible) or (s < 0 and lo[i] + sp[i] <= cible):
                    r = obj; break
                if hm[i] >= fin:
                    r = s * ((c[i] if s > 0 else c[i] + sp[i]) - e) / risque; break
            if r is None:
                r = s * (c[idx[-1]] - e) / risque
            R.append((j, r))
            break
    return pd.DataFrame(R, columns=["jour", "r"])


if __name__ == "__main__":
    reglages = [("depot : 15 min, stop milieu, 1 R", {}), ("objectif 2 R", {"obj": 2.0}),
                ("stop a l'autre bout, 1 R", {"stop": "bout"}), ("fourchette 30 min, 1 R", {"n_or": 6})]
    print("essais : %d reglages x 3 indices (un t > 2 par hasard attendu ~%.1f fois)" % (len(reglages), 12 * 0.023))
    for ident in ("nas_m5_90k", "sp_m5_90k", "dj_m5_90k"):
        d = G.charge(ident)
        print("\n%s : %s -> %s" % (ident, *pd.to_datetime(d["heure"].iloc[[0, -1]], unit="s").dt.date))
        for nom, kw in reglages:
            x = orb(d, **kw)
            r = x.r.values; mi = len(r) // 2
            t_ = r.mean() / r.std() * np.sqrt(len(r)) if len(r) > 1 and r.std() > 0 else 0
            print("  %-30s %3d trades  moy %+5.2f R (t=%+4.1f)  gagnants %2.0f %%  1re %+5.1f R  2de %+5.1f R" % (
                nom, len(r), r.mean(), t_, 100 * (r > 0).mean(), r[:mi].sum(), r[mi:].sum()))
