"""Banc U : signal M5 sur l'or filtre par la STRUCTURE H1 et M15 (PRIORITES 12/11 12 h 30, famille 4).
Or M5 du courtier (15 mois), spread reel paye a chaque trade, entree a l'ouverture de la bougie suivante.
Structure d'une periode (H1 ou M15) : on coupe en blocs de 4 bougies fermees ; « haussiere » si les deux derniers
blocs ont chacun un plus haut ET un plus bas au-dessus de ceux du bloc d'avant (plus hauts et plus bas croissants) ;
« baissiere » a l'inverse ; sinon neutre.
Entrees M5 : elan = cloture au-dela du plus haut/bas des 12 bougies precedentes ; repli = cloture a plus de 1,5
ecart-type de sa moyenne de 20 bougies, contre le mouvement. Filtres : aucun ; structure H1 d'accord ; H1 et M15
d'accord ; H1 contraire. Tenues : 15, 30, 60, 120 min. Une position a la fois par regle.
Reglage = 60 % du debut, verdict = 40 % de la fin. 32 essais. Usage : python3 banc_structure.py"""
import numpy as np, pandas as pd
import banc_grille as G


def structure(d, minutes):
    """Serie alignee sur les bougies M5 : +1 / -1 / 0, connue a la cloture de chaque bougie M5 (blocs FERMES)."""
    pas = 4 * minutes * 60
    b = (d["heure"] // pas).values
    g = d.groupby(b).agg(h=("haut", "max"), l=("bas", "min"))
    up = (g.h > g.h.shift(1)) & (g.l > g.l.shift(1))
    dn = (g.h < g.h.shift(1)) & (g.l < g.l.shift(1))
    s = ((up & up.shift(1)).astype(int) - (dn & dn.shift(1)).astype(int)).shift(1)   # bloc precedent, donc ferme
    return s.reindex(b).fillna(0).values


def jouer(d, sig, tenue):
    o, c, sp = d["ouverture"].values, d["cloture"].values, d["sp"].values
    out, i, n = [], 0, len(d) - tenue - 2
    idx = np.flatnonzero(sig)
    libre = 0
    for i in idx:
        if i < libre or i >= n:
            continue
        e, x = o[i + 1], o[i + 1 + tenue]
        out.append((i, sig[i] * (x - e) / e * 1e4 - sp[i + 1] / e * 1e4))
        libre = i + tenue
    return np.array(out) if out else np.zeros((0, 2))


def res(t, a, b):
    x = t[(t[:, 0] >= a) & (t[:, 0] < b), 1]
    if len(x) < 20:
        return "%5d tr      -      " % len(x)
    return "%5d tr %+5.2f bp (t %+.1f)" % (len(x), x.mean(), x.mean() / x.std() * np.sqrt(len(x)))


if __name__ == "__main__":
    d = G.charge("xau_m5_90k")
    d = d[(d.h >= 3) & (d.h < 23)].reset_index(drop=True)        # hors fermeture nocturne
    c = d["cloture"]
    haut, bas = d["haut"].rolling(12).max().shift(1), d["bas"].rolling(12).min().shift(1)
    elan = ((c > haut).astype(int) - (c < bas).astype(int)).values
    z = (c - c.rolling(20).mean()) / c.rolling(20).std()
    repli = ((z < -1.5).astype(int) - (z > 1.5).astype(int)).values
    h1, m15 = structure(d, 60), structure(d, 15)
    print("or M5 : %d bougies ; structure H1 haussiere %.0f %% du temps, baissiere %.0f %%, neutre %.0f %%"
          % (len(d), 100 * (h1 > 0).mean(), 100 * (h1 < 0).mean(), 100 * (h1 == 0).mean()))
    n = len(d); k = int(n * 0.6)
    print("%-52s | reglage (60 %%)              | verdict (40 %%)" % "")
    for nom, s in (("elan", elan), ("repli", repli)):
        for fn, f in (("sans filtre", np.ones(n, bool)), ("dans le sens de la structure H1", s == h1),
                      ("H1 et M15 d'accord", (s == h1) & (s == m15)), ("contre la structure H1", s == -h1)):
            for tenue in (3, 6, 12, 24):
                t = jouer(d, np.where(f, s, 0), tenue)
                print("  %-50s | %s | %s" % ("%s, %s, %d min" % (nom, fn, tenue * 5), res(t, 0, k), res(t, k, n)))
