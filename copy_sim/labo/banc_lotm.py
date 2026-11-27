"""Banc Lot M (27/11, demande de Baptiste : « au min de pas retourner à 0 mais un peu plus quand même »).
CONTRAT FIGÉ ET POUSSÉ AVANT LES RÉSULTATS. Cadre du lot J/K (or M5 courtier, principal 08/2025-08/2026, réserve
09-11/2026, bt_or_plus 1-2-3-4-5, paliers +2/+4 R). Seule change la sortie « point mort » dès 4 positions : au lieu du
prix moyen + spread, prix moyen + spread + k x ATR jour, k = 0 (v4 actuelle), 0,05, 0,10, 0,15, 0,25 ATR (4 variantes).
Mesures et jugement du lot K (à risque égal : gain÷pire baisse et Sharpe sur le principal, total et gain÷pire baisse sur
la réserve, placebo = signes des différences appariées, Holm sur 4, spread doublé, P(arrêt -34 %) à 0,05 au plus +2 pts).
En plus : bénéfice garanti sur le panier réel du 27/11 (4 positions, moyen 3 641,4, ATR ≈ 110 $) pour chaque k.
Si une variante est RETENUE : préparer la v5 sans la publier ; Baptiste décide."""
import os, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_loth as H, banc_loti as I, banc_lotj as LJ, banc_lotg as G

ICI = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(2712)
KS = {"v4 (k=0)": 0.0, "k=0,05": 0.05, "k=0,10": 0.10, "k=0,15": 0.15, "k=0,25": 0.25}


def simule(d, span, heures, debut, k, mult=1.0):
    c, hi, lo, t = (d[x].values for x in ("cloture", "haut", "bas", "heure"))
    sp = d["sp"].values * mult
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    P, ouvert = [], {}
    for i in range(debut, len(c)):
        for s in list(ouvert):
            p = ouvert[s]
            niv = LJ.niveau_sortie({"pal": (2, 4)}, s, p["meilleur"], p["e"], p["w"], p["A"], p["unite"], 0.0, sp[i])
            if len(p["e"]) >= 4:
                moyen = sum(w * e for w, e in zip(p["w"], p["e"])) / sum(p["w"])
                pm = moyen + s * (sp[i] + k * p["A"])
                niv = max(niv, pm) if s > 0 else min(niv, pm)
            if (lo[i] <= niv) if s > 0 else (hi[i] + sp[i] >= niv):
                usd = sum(w * s * (niv - e) for w, e in zip(p["w"], p["e"]))
                P.append((t[p["i"]], t[i], s, usd / p["unite"], usd))
                del ouvert[s]
                continue
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            while len(p["e"]) < 5 and s * (c[i] - p["prochain"]) >= 0:
                if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                    p["e"].append(c[i] + (sp[i] if s > 0 else -sp[i])); p["w"].append(float(len(p["w"]) + 1))
                p["prochain"] += s * p["pas"]
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if s not in ouvert:
                ouvert[s] = {"i": i, "e": [c[i] + (sp[i] if s > 0 else -sp[i])], "w": [1.0], "meilleur": c[i],
                             "A": atr[i], "unite": 0.6667 * atr[i], "pas": 0.25 * atr[i], "prochain": c[i] + s * 0.25 * atr[i]}
    P = pd.DataFrame(P, columns=["t0", "t1", "s", "g", "usd"])
    P["d0"] = pd.to_datetime(P.t0, unit="s"); P["d1"] = pd.to_datetime(P.t1, unit="s"); P["jour"] = P.d1.dt.floor("D")
    return P


def etude():
    d, k = G.jeu_m5(); k.pop("bars_h")
    R = {m: {v: simule(d, k=x, mult=m, **k) for v, x in KS.items()} for m in (1.0, 2.0)}
    dh, kh = G.jeu_h1(); kh.pop("bars_h")
    RH = {v: simule(dh, k=x, **kh) for v, x in KS.items()}
    princ = lambda P: P[P.d1 <= LJ.FIN_PRINC]
    sd = lambda P: princ(P).groupby("jour").g.sum().reindex(pd.date_range("2025-08-06", "2026-08-31"), fill_value=0).std()
    ref = R[1.0]["v4 (k=0)"]; s_ref = sd(ref)
    L = []
    for v in KS:
        P = R[1.0][v]; f = s_ref / sd(P); Q = P.assign(g=P.g * f, usd=P.usd * f)
        pr, rs = princ(Q), Q[Q.d1 >= LJ.RES0]
        mp, mr = H.mesures(pr), H.mesures(rs)
        row = dict(variante=v, total_brut=princ(P).g.sum(), g_creux=mp["g_creux"], sharpe=mp["sharpe"], res_total=mr["total"],
                   res_g_creux=mr["g_creux"], total_x2=princ(R[2.0][v]).g.sum() * f,
                   arret_005=I.mc(I.semaines(I.evenements(Q)), 0.05, {"bt": 0.0, "c": 0.0}, n=1000).arret.mean())
        if v != "v4 (k=0)":
            m = princ(ref).merge(pr, on="t0", suffixes=("_r", "_v")); dif = (m.g_v - m.g_r).values
            row["placebo_p"] = (np.array([(dif * rng.choice((-1, 1), len(dif))).sum() for _ in range(2000)]) >= dif.sum()).mean()
        ph = RH[v]
        for bn, msk in (("H1_22_24", ph.jour <= H.B1F), ("H1_24_26", ph.jour >= H.B2_0)):
            row[bn] = H.mesures(ph[msk])["g_creux"]
        L.append(row)
    T = pd.DataFrame(L); idx = T.index[1:]
    T.loc[idx, "p_holm"] = H.holm(T.loc[idx, "placebo_p"].values)
    r0 = T.iloc[0]
    T["retenue"] = [bool(i > 0 and r.g_creux > r0.g_creux and r.sharpe > r0.sharpe and r.res_total > r0.res_total
                         and r.res_g_creux > r0.res_g_creux and r.p_holm < 0.05 and r.total_x2 > r0.total_x2
                         and r.arret_005 <= r0.arret_005 + 0.02) for i, r in T.iterrows()]
    return T


def panier_27():
    lots, e = [0.02, 0.04, 0.06, 0.08], [3563.54, 3598.58, 3648.08, 3677.30]
    moyen = sum(l * z for l, z in zip(lots, e)) / sum(lots); A = 73.46 / 0.6667
    return pd.DataFrame([dict(variante=v, niveau=round(moyen + 0.4 + k * A, 2),
                              garanti_usd=round(sum(l * (moyen + 0.4 + k * A - z) for l, z in zip(lots, e)), 2)) for v, k in KS.items()])


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    T = etude(); T.to_csv(os.path.join(ICI, "donnees", "lotm.csv"), index=False)
    print(T.round(3).to_string(index=False)); print(panier_27().to_string(index=False))
