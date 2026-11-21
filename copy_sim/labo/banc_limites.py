"""Banc K : entrees a cours limite sur l'or (M1 du courtier, 3 mois). Un ordre limite ne paie pas le spread a
l'entree, mais il n'est servi que si le prix vient le chercher (selection adverse).
Simulation prudente sur bougies en prix vendeur (bid) :
  achat limite a L : servi si le prix acheteur (ask = bid + spread) descend a L, donc si bas <= L - spread, dans les
    m bougies suivantes ; prix d'entree = L (aucune amelioration de prix comptee) ;
  vente limite a L : servie si bid monte a L, donc si haut >= L ;
  sortie au marche h bougies apres le service (achat : au bid ; vente : au bid + spread).
Ordre pose a la cloture, a k spreads du bon cote : achat a bid - k x spread, vente a ask + k x spread.
k = 0 : achat pose AU bid (on gagne tout le spread si on est servi).
Cote choisi : les deux, sens de l'elan (3 min), sens du retour (contre la derniere minute).
Reglage sur 60 %, verdict sur 40 %. En points de base nets par trade servi. Usage : python3 banc_limites.py"""
import numpy as np
import banc_or as B


if __name__ == "__main__":
    d, _ = B.charge("xau_m1_90k")
    n = len(d); coupe = int(n * 0.6)
    lr = np.log(d["cloture"])
    cotes = {"les deux cotes": None,
             "sens de l'elan 3 min": np.nan_to_num(np.sign(lr - lr.shift(3)).values),
             "contre la derniere min": np.nan_to_num(-np.sign(lr - lr.shift(1)).values)}
    print("Ordres limites sur XAUUSD M1 : %d bougies. Net en bp par trade servi (1 bp = 0,40 $ a 0,01 lot)" % n)
    print("%-24s %2s %2s %3s | %8s %7s | reglage %7s t | verdict %7s t" % ("cote", "k", "m", "h", "servis", "taux", "bp", "bp"))
    lignes = []
    for nom, cote in cotes.items():
        for k in (0, 1, 2, 4):
            for m in (1, 3):
                for h in (1, 3, 5, 15):
                    c, hi, lo, sp = (d[x].values for x in ("cloture", "haut", "bas", "sp"))
                    tot_i, tot_g = [], []
                    for sens in (1, -1):
                        L = c - k * sp if sens > 0 else c + sp + k * sp
                        servi = np.full(n, -1)
                        for dj in range(m, 0, -1):
                            j = np.minimum(np.arange(n) + dj, n - 1)
                            f = (np.arange(n) + dj < n) & ((lo[j] <= L - sp[j]) if sens > 0 else (hi[j] >= L))
                            servi[f] = j[f]
                        pose = np.ones(n, bool) if cote is None else (cote == sens)
                        i = np.where(pose & (servi >= 0) & (servi + h < n))[0]
                        x = servi[i] + h
                        g = (c[x] - L[i]) if sens > 0 else (L[i] - (c[x] + sp[x]))
                        tot_i.append(i); tot_g.append(g / c[i] * 1e4)
                        poses = pose.sum() if sens > 0 else poses + pose.sum()
                    i = np.concatenate(tot_i); g = np.concatenate(tot_g)
                    a, b = g[i < coupe], g[i >= coupe]
                    t = lambda v: v.mean() / v.std() * np.sqrt(len(v) / max(1, h)) if len(v) > 30 else float("nan")
                    lignes.append((nom, k, m, h, len(g), 100 * len(g) / poses, a.mean(), t(a), b.mean(), t(b)))
    for l in sorted(lignes, key=lambda l: -l[6]):
        print("%-24s %2d %2d %3d | %8d %6.1f%% | %+7.2f %+6.1f | %+7.2f %+6.1f" % l)
    pos = [l for l in lignes if l[6] > 0]
    print("\n%d combinaisons ; positives au reglage : %d ; parmi elles positives au verdict : %d ; avec t > 2 au verdict : %d" % (
        len(lignes), len(pos), sum(l[8] > 0 for l in pos), sum(l[9] > 2 for l in pos)))
