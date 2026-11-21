"""Banc Q : le melange suivi par Baptiste (elan_m15 + cassure_m15 + exces_m1 + exces_m5 + bt_or) sur l'historique du
courtier : resultat par jour de chaque membre (en $ a 0,01 lot, spread paye, une position a la fois comme le robot),
correlations entre membres, jours de tendance contre jours calmes, et melange a parts egales.
Periode commune : les 15 mois de M5 (exces_m1 n'a que 3 mois de M1 : donne a part). Usage : python3 banc_melange.py"""
import numpy as np, pandas as pd
import banc_or as B, banc_grille as G, banc_blocktrend as BT


def par_jour(d, s, h, usd=0.40):
    x, i = B.trades(d, s, h)
    j = pd.Series(x[:, 0] * usd, index=d.index[i].floor("D"))
    return j.groupby(level=0).sum(), len(x), x[:, 0].mean() * usd


if __name__ == "__main__":
    m15, _ = B.charge("xau_m15_50k"); m5, _ = B.charge("xau_m5_90k"); m1, _ = B.charge("xau_m1_90k")
    debut = m5.index[0]
    m15 = m15[m15.index >= debut]
    J, infos = {}, {}
    lr = np.log(m15["cloture"])
    J["elan_m15"], n, moy = par_jour(m15, np.sign(lr - lr.shift(12)), 12); infos["elan_m15"] = (n, moy)
    ha, ba = m15["haut"].shift(1).rolling(48).max(), m15["bas"].shift(1).rolling(48).min()
    J["cassure_m15"], n, moy = par_jour(m15, (m15["cloture"] > ha).astype(float) - (m15["cloture"] < ba).astype(float), 12); infos["cassure_m15"] = (n, moy)
    r = np.log(m5["cloture"]).diff(); z = r / r.rolling(100).std().shift(1)
    J["exces_m5"], n, moy = par_jour(m5, (z > 3).astype(float) - (z < -3).astype(float), 3); infos["exces_m5"] = (n, moy)
    g = G.charge("xau_m5_90k")
    P = BT.simule(g, 0.25, 0.6667, 3)
    atr = (m5["haut"].groupby(m5.index.floor("D")).max() - m5["bas"].groupby(m5.index.floor("D")).min()).rolling(20).mean().shift(1)
    jb = pd.Series([p[3] for p in P], index=m5.index[[p[0] + p[4] for p in P]].floor("D"))
    stop = (0.6667 * atr).reindex(jb.index).ffill().values
    J["bt_or"] = (jb * stop).groupby(level=0).sum(); infos["bt_or"] = (len(P), float((jb * stop).mean()))
    T = pd.DataFrame(J).fillna(0.0)
    T = T[T.index.dayofweek < 5]
    T["MELANGE"] = T.sum(axis=1)
    jour = m5["cloture"].groupby(m5.index.floor("D")).agg(["first", "last"])
    amp = ((jour["last"] - jour["first"]).abs() / jour["first"] * 1e4).reindex(T.index)
    tend = amp > amp.median()
    print("Or, %s -> %s, %d jours. $ par jour a 0,01 lot par position" % (T.index[0].date(), T.index[-1].date(), len(T)))
    print("%-12s %7s %10s %9s %8s %8s %10s %10s %12s %12s" % ("membre", "trades", "$/trade", "total $", "$/jour", "t jour", "jours +", "pire jour", "jours tend.", "jours calmes"))
    for k in T:
        x = T[k]; n, moy = infos.get(k, (sum(v[0] for v in infos.values()), float("nan")))
        print("%-12s %7d %+10.2f %+9.0f %+8.2f %+8.2f %9.0f%% %+10.0f %+12.2f %+12.2f" % (
            k, n, moy, x.sum(), x.mean(), x.mean() / x.std() * np.sqrt(len(x)), 100 * (x > 0).mean(), x.min(), x[tend].mean(), x[~tend].mean()))
    print("\nCorrelations entre les resultats quotidiens :")
    print(T.drop(columns="MELANGE").corr().round(2).to_string())
    n = len(T); b = [int(n * q / 5) for q in range(6)]
    print("\nMelange par tranche de 3 mois ($) :", "  ".join("%+.0f" % T["MELANGE"].iloc[b[q]:b[q + 1]].sum() for q in range(5)))
    c = T["MELANGE"].cumsum(); print("pire creux du melange : %+.0f $" % (c - c.cummax()).min())
    # exces_m1 a part (3 mois)
    r = np.log(m1["cloture"]).diff(); z = r / r.rolling(100).std().shift(1)
    x, nn, moy = par_jour(m1, -((z > 3).astype(float) - (z < -3).astype(float)), 12)
    autres = T.reindex(x.index).fillna(0)
    print("\nexces_m1 (3 mois seulement) : %d trades, %+.2f $/trade, total %+.0f $ ; correlation quotidienne avec elan_m15 %+.2f, bt_or %+.2f" % (
        nn, moy, x.sum(), np.corrcoef(x, autres["elan_m15"])[0, 1], np.corrcoef(x, autres["bt_or"])[0, 1]))
