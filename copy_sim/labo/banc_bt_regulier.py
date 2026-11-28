"""Banc AE : rendre la mecanique bt_or (BlockTrend, reglage serre de l'or) plus reguliere (PRIORITES 17/11, B).
Regle FIGEE (celle de bt_or, aucun reglage par marche) : sens = cloture contre l'EMA de 2 jours ; entree aux heures
serveur 03:05, 08:00, 08:30, 12:00, 15:45, 16:00, 16:30 s'il n'y a pas de panier de ce cote ; ajouts dans le sens du
prix tous les 0,25 ATR jour 20 j (cloture de bougie, niveau saute au-dela d'un demi-pas), 3 positions au plus ;
sortie de tout le panier sur recul de 0,6667 ATR depuis le meilleur prix (stop suiveur = stop initial au depart).
Couts : spread reel du courtier (colonne sp) a chaque entree ; gain d'un panier compte au jour de sa SORTIE.
1 R = perte d'une position au stop initial (taille au risque constant en $ = mise selon l'ATR).
(a) Chaque marche en bougies M5 du courtier (ger et jpy : M1 regroupees en M5, 3 mois seulement) ; historique long :
    or H1 et Nasdaq H4 08/2022-11/2026 (avant 07/2022 les fichiers n'ont qu'~1 bougie par jour ; memes heures
    arrondies a la bougie, EMA = 2 jours de bougies). Pas de rejeu en D1 : le stop (0,67 ATR) tient dans une bougie.
    Reality check de White (bootstrap stationnaire, blocs moyens 5 j, 2000 tirages) du meilleur marche contre zero.
(b)+(c) Portefeuilles sur les 6 marches M5 de 15 mois (xau, xag, nas, sp, dj, eur). Grille fixee d'avance, N = 12 :
    selection {tous ; marches au total > 0 sur l'apprentissage ; marches a t > 1 sur l'apprentissage}
    x mise {risque constant (ATR) ; lot fixe (gain x stop / stop moyen du marche : meme risque moyen)}
    x poids {egal ; inverse de l'ecart-type journalier du marche sur l'apprentissage}.
    Walk-forward glissant : apprentissage 6 mois, test 1 mois ; reglage au meilleur t ; chaque mois de test est mis a la
    volatilite de bt_or seul sur l'apprentissage (comparaison a risque egal). Reference : bt_or seul (et ne rien faire).
    Reality check de White sur les 12 contre bt_or seul (series mises a la meme volatilite sur tout l'echantillon).
Verdict (fixe d'avance) : tient = hors echantillon > ref ET (t >= 2,6 OU p RC < 0,05) ; presque = > ref et
(1,5 <= t < 2,6 ou p < 0,15) ; sinon ne tient pas. Critere en plus : mois negatifs contre bt_or seul.
Usage : python3 banc_bt_regulier.py"""
import os, itertools, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd

ICI = os.path.dirname(os.path.abspath(__file__))
DON = os.path.join(ICI, "mt5", "donnees")
PAS, STOP, MAXP = 0.25, 0.6667, 3
H_M5 = {(3, 5), (8, 0), (8, 30), (12, 0), (15, 45), (16, 0), (16, 30)}


def charge(ident, m1_vers_m5=False):
    d = pd.read_csv(os.path.join(DON, ident + ".csv.gz"))
    dec = max(len(("%.5f" % v).rstrip("0").split(".")[1]) for v in d["cloture"].iloc[:2000])
    d["sp"] = d["spread_points"] * 10.0 ** (-dec)
    if m1_vers_m5:
        d = d.groupby(d["heure"] // 300).agg(heure=("heure", "first"), haut=("haut", "max"), bas=("bas", "min"),
                                              cloture=("cloture", "last"), sp=("sp", "mean")).reset_index(drop=True)
        d["heure"] = d["heure"] // 300 * 300
    return d


def simule(d, span=576, heures=H_M5, debut=600):
    """Copie de banc_sorties_bt.simule (variante « actuel ») rendue generique. Rend un DataFrame de paniers."""
    c, hi, lo, sp, t = (d[x].values for x in ("cloture", "haut", "bas", "sp", "heure"))
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
            niveau = p["meilleur"] - s * p["stop"]
            if (lo[i] <= niveau) if s > 0 else (hi[i] + sp[i] >= niveau):
                p = ouvert.pop(s)
                g = sum(s * (niveau - e) for e in p["e"]) / p["stop"]
                P.append((t[p["i"]], t[i], s, g, p["stop"], c[p["i"]]))
                continue
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            while len(p["e"]) < MAXP and s * (c[i] - p["prochain"]) >= 0:
                if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                    p["e"].append(c[i] + (sp[i] if s > 0 else -sp[i]))
                p["prochain"] += s * p["pas"]
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if s not in ouvert:
                ouvert[s] = {"i": i, "e": [c[i] + (sp[i] if s > 0 else -sp[i])], "meilleur": c[i], "stop": STOP * atr[i],
                             "pas": PAS * atr[i], "prochain": c[i] + s * PAS * atr[i]}
    P = pd.DataFrame(P, columns=["t0", "t1", "s", "g", "stop", "px"])
    P["jour"] = pd.to_datetime(P.t1, unit="s").dt.floor("D")
    P["bp"] = P.g * P.stop / P.px * 1e4
    P["lot"] = P.g * P.stop / P.stop.mean()          # lot fixe, meme risque moyen
    return P


tst = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else 0.0
creux = lambda x: (np.cumsum(x) - np.maximum.accumulate(np.cumsum(x))).min()
rng = np.random.default_rng(17)


def boot(n, B=2000, b=5.0):
    """Indices du bootstrap stationnaire (Politis-Romano), vectorise."""
    out = np.empty((B, n), int)
    for k in range(B):
        neuf = rng.random(n) < 1 / b; neuf[0] = True
        bl = np.cumsum(neuf) - 1; deb = np.flatnonzero(neuf)
        out[k] = (rng.integers(n, size=len(deb))[bl] + np.arange(n) - deb[bl]) % n
    return out


def white(Dm):
    n = len(Dm); mu = Dm.mean(0); V = np.sqrt(n) * mu.max()
    Vb = np.array([np.sqrt(n) * (Dm[ii].mean(0) - mu).max() for ii in boot(n)])
    return int(mu.argmax()), (Vb >= V).mean()


if __name__ == "__main__":
    MARCHES = [("xau", "xau_m5_90k", {}), ("xag", "xag_m5_90k", {}), ("nas", "nas_m5_90k", {}), ("sp", "sp_m5_90k", {}),
               ("dj", "dj_m5_90k", {}), ("eur", "eur_m5_90k", {}), ("ger*", "ger_m1_90k", "m1"), ("jpy*", "jpy_m1_90k", "m1"),
               ("btc*", "btc_m5_90k", {}), ("eth*", "eth_m5_90k", {}),
               ("xau H1 2022+", "xau_h1_50k", dict(span=48, heures={(2, 0), (7, 0), (11, 0), (14, 0), (15, 0)}, debut=60)),
               ("nas H4 2022+", "nas_h4_20k", dict(span=12, heures={(0, 0), (4, 0), (8, 0), (12, 0)}, debut=30))]
    R = {}
    print("(a) Mecanique bt_or figee (pas 0,25 / stop 0,667 ATR / 3 positions). * = moins de 15 mois. Gains en R.")
    print("%-12s %-23s %5s %7s %5s %7s %7s %6s %6s %6s" % ("marche", "periode", "pan.", "total", "t", "1re moit", "2de moit", "bp/pan", "creux", "mois<0"))
    for nom, ident, kw in MARCHES:
        d = charge(ident, m1_vers_m5=(kw == "m1"))
        if "2022+" in nom:   # avant 07/2022 ces fichiers n'ont qu'environ 1 bougie par jour : inutilisables
            d = d[d.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
        P = simule(d, **(kw if isinstance(kw, dict) else {}))
        R[nom] = P
        t0, t1 = pd.to_datetime(d.heure.iloc[[0, -1]], unit="s")
        mi = t0 + (t1 - t0) / 2
        m = P.groupby(P.jour.dt.to_period("M")).g.sum()
        print("%-12s %s->%s %5d %+7.1f %+5.1f %+7.1f %+7.1f %+6.1f %+6.1f %3d/%-2d" % (
            nom, t0.date(), t1.date(), len(P), P.g.sum(), tst(P.g), P.g[P.jour < mi].sum(), P.g[P.jour >= mi].sum(),
            P.bp.mean(), creux(P.g.values), (m < 0).sum(), len(m)))
    # ---------------------------------------------------------------- series par jour, 6 marches de 15 mois
    M6 = ["xau", "xag", "nas", "sp", "dj", "eur"]
    deb = max(pd.to_datetime(charge(i).heure.iloc[0], unit="s") for _, i, _ in MARCHES[:6]).floor("D") + pd.Timedelta(days=5)
    fin = min(R[m].jour.max() for m in M6)
    idx = pd.bdate_range(deb, fin)
    JR = pd.DataFrame({m: R[m].groupby("jour").g.sum() for m in M6}).reindex(idx).fillna(0)
    JL = pd.DataFrame({m: R[m].groupby("jour").lot.sum() for m in M6}).reindex(idx).fillna(0)
    ii, pc = white(JR.values)
    print("Reality check sur les 6 marches de 15 mois (%s -> %s) contre zero : meilleur %s, p = %.3f ; Bonferroni : t >= %.1f"
          % (idx[0].date(), idx[-1].date(), M6[ii], pc, 2.6))
    C = JR.corr(); Cm = JR.groupby(idx.to_period("M")).sum().corr()
    print("(b) Correlation avec l'or, jour / mois : " + " ; ".join("%s %+.2f / %+.2f" % (m, C.loc["xau", m], Cm.loc["xau", m]) for m in M6[1:])
          + " ; moyenne des paires (jour) %+.2f" % C.values[np.triu_indices(6, 1)].mean())
    mois = idx.to_period("M"); MO = mois.unique()
    ref = JR["xau"]

    def ligne(nom, x):
        x = x * ref.std() / x.std()                      # meme volatilite que bt_or seul
        mm = x.groupby(mois).sum()
        print("  %-38s total %+6.1f R  t %+4.1f  mois<0 %2d/%d  pire mois %+5.1f  creux %+5.1f  bp/jour %+.2f" % (
            nom, x.sum(), tst(x), (mm < 0).sum(), len(mm), mm.min(), creux(x.values), x.mean()))
        return x
    print("Portefeuilles a la volatilite de bt_or seul (tout l'echantillon, sans walk-forward) :")
    ligne("bt_or seul, risque constant (ATR)", ref); ligne("bt_or seul, lot fixe", JL["xau"])
    ligne("6 marches, risque egal, ATR", JR.mean(1)); ligne("6 marches, risque egal, lot fixe", JL.mean(1))
    ligne("or + argent + indices (sans eur), ATR", JR[M6[:5]].mean(1))
    # ---------------------------------------------------------------- walk-forward, N = 12
    fen = [(MO[i - 6], MO[i - 1], MO[i]) for i in range(6, len(MO))]
    GR = list(itertools.product(("tous", "total>0", "t>1"), ("ATR", "lot"), ("egal", "inv. vol")))

    def serie(cfg, app):
        sel, mise, pw = cfg
        X = JR if mise == "ATR" else JL
        a = X[app]
        ok = [m for m in M6 if sel == "tous" or (sel == "total>0" and a[m].sum() > 0) or (sel == "t>1" and tst(a[m]) > 1)]
        if not ok:
            return pd.Series(0.0, idx)
        w = pd.Series(1.0, ok) if pw == "egal" else 1 / a[ok].std().replace(0, np.nan).fillna(1e9)
        return (X[ok] * (w / w.sum())).sum(1)
    oos, choix, nsel = [], [], []
    for a, b, t in fen:
        app, te = (mois >= a) & (mois <= b), mois == t
        S = {k: serie(k, app) for k in GR}
        best = max(GR, key=lambda k: tst(S[k][app]))
        x = S[best]; k = ref[app].std() / x[app].std() if x[app].std() > 0 else 0
        oos.append(x[te] * k); choix.append(" ".join(best))
    o = pd.concat(oos); r0 = ref[o.index]; dd = o - r0
    om, rm = o.groupby(o.index.to_period("M")).sum(), r0.groupby(r0.index.to_period("M")).sum()
    Dm = np.column_stack([(lambda s: s * ref.std() / s.std())(serie(k, np.ones(len(idx), bool))) - ref for k in GR])
    kb, prc = white(Dm)
    fq = pd.Series(choix).value_counts()
    print("Walk-forward 6 mois / 1 mois, N = %d reglages, %d mois de test (%s -> %s) ; reglage le plus choisi : %s (%d/%d)"
          % (len(GR), len(fen), fen[0][2], fen[-1][2], fq.index[0], fq.iloc[0], len(fen)))
    print("  hors echantillon %+.1f R (t %+.1f), mois gagnants %d/%d, mois<0 %d (bt_or seul : %+.1f R, mois<0 %d), creux %+.1f (bt_or %+.1f)"
          % (o.sum(), tst(o), (om > 0).sum(), len(om), (om < 0).sum(), r0.sum(), (rm < 0).sum(), creux(o.values), creux(r0.values)))
    print("  difference contre bt_or seul %+.1f R (t %+.1f) ; reality check des 12 contre bt_or : meilleur %s, p = %.3f"
          % (dd.sum(), tst(dd), " ".join(GR[kb]), prc))
    v = "tient" if dd.sum() > 0 and (tst(dd) >= 2.6 or prc < 0.05) else (
        "presque" if dd.sum() > 0 and (tst(dd) >= 1.5 or prc < 0.15) else "ne tient pas")
    print("  Verdict (fixe d'avance) : %s ; contre ne rien faire : %+.1f R (t %+.1f)" % (v, o.sum(), tst(o)))
