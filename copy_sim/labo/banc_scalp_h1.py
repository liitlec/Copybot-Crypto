"""Banc B : le scalp simple a l'heure peut-il payer ses couts ? Bougies 1 h (~2 ans, Yahoo).
Famille de regles (18) : on regarde le rendement des k dernieres heures (k = 1, 4, 24), on entre dans le meme sens
(elan) ou en sens inverse (retour), on tient h heures (h = 1, 4, 24), entrees non chevauchantes.
Choix de la meilleure regle par actif sur la 1re moitie, verdict sur la 2e moitie (jamais vue).
Usage : python3 banc_scalp_h1.py"""
import os
import numpy as np, pandas as pd

ICI = os.path.dirname(os.path.abspath(__file__))
# cout aller-retour en points de base (ecart + glissement, compte standard sans commission)
COUT = {"EURUSD": 1.2, "GBPUSD": 1.5, "USDJPY": 1.3, "AUDUSD": 1.6, "OR": 1.5, "SP500": 1.0, "NASDAQ": 1.0,
        "BTC": 6.0, "ETH": 8.0}
REGLES = [(k, h, d) for k in (1, 4, 24) for h in (1, 4, 24) for d in (1, -1)]


def trades(px, k, h, d):
    """Rendements bruts (en bp) des trades non chevauchants de la regle."""
    lp = np.log(px.values)
    i = np.arange(k, len(lp) - h, h)
    sig = np.sign(lp[i] - lp[i - k]) * d
    ret = sig * (lp[i + h] - lp[i]) * 1e4
    return pd.Series(ret[sig != 0], index=px.index[i][sig != 0])


def resume(x, cout):
    n = len(x)
    if n < 30:
        return n, np.nan, np.nan, np.nan
    net = x - cout
    return n, x.mean(), net.mean(), net.mean() / net.std() * np.sqrt(n)


if __name__ == "__main__":
    p = pd.read_csv(os.path.join(ICI, "data", "h1.csv.gz"), index_col=0, parse_dates=True)
    print("1) La barre a franchir : mouvement typique d'une heure contre le cout d'un aller-retour")
    for a in p:
        s = p[a].dropna()
        m = (np.log(s).diff().abs() * 1e4).median()
        print("  %-7s mouvement median 1 h %5.1f bp ; cout %4.1f bp = %3.0f %% du mouvement" % (a, m, COUT[a], 100 * COUT[a] / m))
    print("\n2) Toutes regles, tous actifs, 2 ans entiers : gain moyen par trade (bp), brut puis net")
    lignes = []
    for (k, h, d) in REGLES:
        b, nn, tot = [], [], 0
        for a in p:
            x = trades(p[a].dropna(), k, h, d)
            b.append(x.mean()); nn.append((x - COUT[a]).mean()); tot += len(x)
        lignes.append((np.mean(nn), k, h, d, np.mean(b), tot))
    for nn, k, h, d, b, tot in sorted(lignes, reverse=True):
        print("  %-6s k=%2d h=%2d : brut %+6.2f  net %+6.2f  (%d trades)" % ("elan" if d > 0 else "retour", k, h, b, nn, tot))
    print("\n3) Meilleure regle par actif sur la 1re moitie (nette), puis verdict sur la 2e moitie jamais vue")
    tot2 = []
    for a in p:
        s = p[a].dropna()
        m = len(s) // 2
        best = max(REGLES, key=lambda r: np.nan_to_num(resume(trades(s.iloc[:m], *r), COUT[a])[3], nan=-9))
        n1, b1, e1, t1 = resume(trades(s.iloc[:m], *best), COUT[a])
        x2 = trades(s.iloc[m:], *best)
        n2, b2, e2, t2 = resume(x2, COUT[a])
        tot2.append(x2 - COUT[a])
        print("  %-7s %-6s k=%2d h=%2d | moitie 1 : %4d trades, net %+6.2f bp (t=%+.1f) | moitie 2 : %4d trades, brut %+6.2f, net %+6.2f bp (t=%+.1f)"
              % (a, "elan" if best[2] > 0 else "retour", best[0], best[1], n1, e1, t1, n2, b2, e2, t2))
    z = pd.concat(tot2)
    print("  ENSEMBLE moitie 2 : %d trades, net moyen %+.2f bp, t=%+.1f  (18 regles x %d actifs essayes)"
          % (len(z), z.mean(), z.mean() / z.std() * np.sqrt(len(z)), p.shape[1]))
    print("\n4) Entrees au hasard (pile ou face chaque heure, tenue 1 h) : net moyen par trade")
    rng = np.random.default_rng(7)
    for a in p:
        lp = np.log(p[a].dropna().values)
        r = np.diff(lp) * 1e4
        g = np.mean([np.mean(rng.choice([-1, 1], len(r)) * r) for _ in range(200)])
        print("  %-7s brut %+5.2f bp, net %+5.2f bp" % (a, g, g - COUT[a]))
