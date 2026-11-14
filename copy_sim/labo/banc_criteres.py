"""Banc P : une strategie « a criteres multiples » sur l'or (M5 du courtier, 15 mois), fixee d'avance, sans recherche.
Idee : acheter un repli dans une tendance haussiere etablie (et l'inverse a la vente), seulement quand tout est reuni :
  1 seance active (10 h - 19 h serveur)        5 or agite (mouvement 24 h > mediane 60 jours)
  2 tendance de fond (cours contre moy. 20 h)   6 spread normal (<= 1,5 x sa mediane)
  3 pente de la moyenne 20 h dans le meme sens  7 bougie de confirmation (cloture dans le bon sens, moitie haute/basse)
  4 structure M15 : creux/sommets ascendants    8 repli : ecart a la moyenne 20 bougies < -1,5 ecart-type (ou > +1,5)
Entree a l'ouverture suivante, sortie au temps, spread paye. Reglage 60 % -> verdict 40 %.
On teste la regle complete, puis la meme en retirant un critere a la fois (pour voir ce que chacun apporte).
Usage : python3 banc_criteres.py"""
import numpy as np, pandas as pd
import banc_grille as G


def criteres(d):
    c, o, h, l = d["cloture"], d["ouverture"], d["haut"], d["bas"]
    ma = c.rolling(240).mean()
    fond = np.sign(c - ma)
    pente = np.sign(ma - ma.shift(48))
    z = (c - c.rolling(20).mean()) / c.rolling(20).std()
    sens = -np.sign(z).where(z.abs() > 1.5, 0)                     # on achete un repli, on vend un rebond
    creux = l.rolling(36).min() > l.rolling(36).min().shift(36)
    sommets = h.rolling(36).max() < h.rolling(36).max().shift(36)
    v = np.log(c).diff().abs().rolling(288).mean()
    agite = v > v.rolling(17280, min_periods=5000).median().shift(1)
    spn = d["sp"] <= 1.5 * d["sp"].rolling(2000, min_periods=200).median()
    milieu = (h + l) / 2
    conf = ((c > o) & (c > milieu) & (sens > 0)) | ((c < o) & (c < milieu) & (sens < 0))
    K = {"1 seance": d["h"].between(10, 18),
         "2 tendance de fond": fond == sens,
         "3 pente de la moyenne": pente == sens,
         "4 structure M15": (creux & (sens > 0)) | (sommets & (sens < 0)),
         "5 or agite": agite.fillna(False),
         "6 spread normal": spn,
         "7 bougie de confirmation": conf}
    return sens, K


def juge(d, sens, masque, h):
    c, o, sp = d["cloture"].values, d["ouverture"].values, d["sp"].values
    n = len(c)
    i = np.where(masque & (sens != 0) & (np.arange(n) < n - h - 1))[0]
    keep, last = [], -99
    for k in i:                                                    # une position a la fois
        if k - last >= h:
            keep.append(k); last = k
    i = np.array(keep, dtype=int)
    if len(i) == 0:
        return i, np.array([])
    s = sens[i]
    g = (s * (c[i + h] - o[i + 1]) - sp[i + 1]) / o[i + 1] * 1e4
    return i, g


if __name__ == "__main__":
    d = G.charge("xau_m5_90k")
    n = len(d); coupe = int(n * 0.6)
    sens, K = criteres(d)
    sens = sens.fillna(0).values
    tout = np.ones(n, bool)
    for v in K.values():
        tout &= v.values.astype(bool)
    print("Or M5, %d bougies. bp nets par trade ; reglage (60 %%) -> verdict (40 %%)" % n)
    essais = 0
    t = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 15 and x.std() > 0 else float("nan")
    for h in (3, 6, 12):
        print("\nTenue %d bougies (%d min)" % (h, 5 * h))
        lignes = [("TOUS les criteres", tout)]
        for nom in K:
            m = np.ones(n, bool)
            for autre, v in K.items():
                if autre != nom:
                    m &= v.values.astype(bool)
            lignes.append(("sans « %s »" % nom, m))
        lignes.append(("AUCUN critere (repli seul)", np.ones(n, bool)))
        for nom, m in lignes:
            i, g = juge(d, sens, m, h); essais += 1
            a, b = g[i < coupe], g[i >= coupe]
            print("  %-34s %5d trades | reglage %+6.2f (t=%+.1f, %d) | verdict %+6.2f (t=%+.1f, %d) | par jour %.2f" % (
                nom, len(g), a.mean() if len(a) else np.nan, t(a), len(a), b.mean() if len(b) else np.nan, t(b), len(b), len(g) / 330.0))
    print("\nEssais :", essais)
