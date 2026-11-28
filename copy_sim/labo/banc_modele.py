"""Banc N : modeles appris (gradient boosting) sur l'or M1 du courtier, 3 mois, 26 variables a la fois.
Cible : rendement des h prochaines minutes (de l'ouverture suivante a la cloture h bougies plus tard), en bp.
Validation glissante stricte : 4 tours, le modele est appris sur tout le passe et juge sur le bloc suivant
(50 % -> 62,5 %, ... -> 100 %). On ne trade que les previsions les plus fortes (les 10 % ou les 2 % les plus
grandes en valeur absolue, seuil fixe sur le passe), dans le sens prevu, spread reel paye.
Temoin : meme chaine avec les cibles d'apprentissage melangees (ce que donne le hasard).
Besoin de scikit-learn (pip install scikit-learn). Usage : python3 banc_modele.py"""
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
import banc_or as B


def variables(d):
    c, o, h, l, v = d["cloture"], d["ouverture"], d["haut"], d["bas"], d["volume_ticks"]
    lr = np.log(c)
    X = pd.DataFrame(index=d.index)
    for k in (1, 2, 3, 5, 10, 15, 30, 60, 240):
        X["r%d" % k] = (lr - lr.shift(k)) * 1e4
    amp = (h - l) / c * 1e4
    X["amp"] = amp
    X["amp_rel"] = amp / amp.rolling(60).mean()
    X["vol10_60"] = lr.diff().abs().rolling(10).mean() / lr.diff().abs().rolling(60).mean()
    X["vol60_1j"] = lr.diff().abs().rolling(60).mean() / lr.diff().abs().rolling(1380).mean()
    for n in (20, 60, 240):
        X["z%d" % n] = (c - c.rolling(n).mean()) / c.rolling(n).std()
        X["pos%d" % n] = (c - l.rolling(n).min()) / (h.rolling(n).max() - l.rolling(n).min())
    X["corps"] = (c - o) / (h - l).replace(0, np.nan)
    X["meche_h"] = (h - np.maximum(c, o)) / (h - l).replace(0, np.nan)
    X["ticks_rel"] = v / v.rolling(60).mean()
    X["spread"] = d["sp"] / c * 1e4
    hh = d.index.hour + d.index.minute / 60
    X["h_sin"], X["h_cos"] = np.sin(2 * np.pi * hh / 24), np.cos(2 * np.pi * hh / 24)
    s = np.sign(lr.diff())
    X["serie"] = s.groupby((s != s.shift()).cumsum()).cumcount() * s
    jour = d.index.floor("D")
    X["dist_haut_j"] = (h.groupby(jour).cummax() - c) / c * 1e4
    X["dist_bas_j"] = (c - l.groupby(jour).cummin()) / c * 1e4
    return X


def tour(X, y, cout, bornes, quant, rng=None):
    net, brut, cor = [], [], []
    for a, b in bornes:
        ya = y[:a].copy()
        ok = np.isfinite(ya)
        if rng is not None:
            ya[ok] = rng.permutation(ya[ok])
        m = HistGradientBoostingRegressor(max_depth=4, learning_rate=0.05, max_iter=150, min_samples_leaf=300, random_state=0)
        m.fit(X[:a][ok], ya[ok])
        seuil = np.quantile(np.abs(m.predict(X[:a][ok])), 1 - quant)
        p = m.predict(X[a:b]); yt = y[a:b]; ct = cout[a:b]
        k = (np.abs(p) >= seuil) & np.isfinite(yt)
        g = np.sign(p[k]) * yt[k]
        brut.append(g); net.append(g - ct[k])
        f = np.isfinite(yt)
        cor.append(np.corrcoef(p[f], yt[f])[0, 1])
    return np.concatenate(net), np.concatenate(brut), cor


if __name__ == "__main__":
    d, _ = B.charge("xau_m1_90k")
    X = variables(d).values
    n = len(d)
    o, c, sp = d["ouverture"].values, d["cloture"].values, d["sp"].values
    bornes = [(int(n * (0.5 + 0.125 * k)), int(n * (0.5 + 0.125 * (k + 1)))) for k in range(4)]
    print("Or M1, %d bougies, 26 variables ; 4 tours de validation glissante. bp par trade (1 bp = 0,40 $ a 0,01 lot)" % n)
    essais = 0
    for h in (5, 15):
        y = np.full(n, np.nan)
        y[:n - h - 1] = (c[np.arange(n - h - 1) + h] - o[1:n - h]) / o[1:n - h] * 1e4
        cout = np.roll(sp, -1) / o * 1e4
        for quant in (0.10, 0.02):
            net, brut, cor = tour(X, y, cout, bornes, quant); essais += 1
            t = net.mean() / net.std() * np.sqrt(len(net) / h)
            print("horizon %2d min, %2.0f %% des previsions les plus fortes : %5d trades, brut %+5.2f, net %+5.2f bp (t=%+.1f) ; lien prevision/realite par tour : %s" % (
                h, 100 * quant, len(net), brut.mean(), net.mean(), t, " ".join("%+.3f" % x for x in cor)))
            rng = np.random.default_rng(3)
            tem = [tour(X, y, cout, bornes, quant, rng) for _ in range(3)]
            print("     temoin (cibles melangees, 3 tirages) : brut %s ; net %s" % (
                " ".join("%+5.2f" % t_[1].mean() for t_ in tem), " ".join("%+5.2f" % t_[0].mean() for t_ in tem)))
    print("Essais :", essais)
