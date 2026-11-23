"""Lot B, piste 7 : regles ROBUSTES aux deux regimes (PRIORITES 23/11). Au lieu de deviner le type de marche, la
SORTIE des familles or H1 s'adapte toute seule. Socle commun : regime_socle.py (jours, familles, couts, echelle,
references TOUT / SUIVRE5, walk-forward, White, periodes, critere) ; rien n'y est modifie.

Mecanique (copies de banc_bt_regulier.simule et banc_or.trades, ces fichiers ne sont pas touches) :
  bt_or_h1 : entree / renforts / plafond identiques (pas 0,25 ATR, 3 positions, EMA 48 H1, heures H1 du socle) ;
             1 R = stop initial 0,6667 ATR (inchange) ; seule la sortie change :
    (a) stop suiveur resserre selon le ratio d'efficacite de Kaufman ER(n) = |c[k]-c[k-n]| / somme |c[j]-c[j-1]|,
        calcule a k = i-1 (derniere bougie H1 FERMEE avant la bougie i ou le stop peut etre touche) : si ER < seuil,
        distance = 0,5 x stop, sinon stop ; le niveau ne recule jamais (cliquet).
    (b) sortie au temps : a la CLOTURE de la bougie i (bougie i fermee), si i - i0 >= 12 bougies et que le meilleur
        prix n'a pas avance de 0,5 ATR depuis l'entree, tout le panier sort a cette cloture (vente : cloture + spread).
    (c) objectif partiel : moitie de chaque position fermee a entree + 1 ATR (ordre limite, touche par le haut de la
        bougie ; vente : bas + spread), puis plus de renfort ; le reste suit le stop.
    Ordre dans une bougie : stop (sur le niveau calcule avec les bougies <= i-1) puis objectif, puis meilleur, puis
    sortie au temps a la cloture, puis renforts (comme l'original).
  cassure_h1 adaptee : meme signal (cloture hors fourchette des 12 H1 precedentes) et meme entree ; a la cloture de
    la 3e bougie, si ER(6) des bougies x-5..x (toutes fermees) >= 0,4 ET le trade est gagnant, on prolonge bougie
    par bougie tant que c'est vrai, 6 bougies au plus ; sinon sortie a la cloture (comme l'original).
Spread reel x cout (1 puis 2) comme le socle ; meme echelle que la famille d'origine (regime_socle.base(1.0)[2]),
donc risque comparable : 1 u = ecart-type journalier de la famille ORIGINALE sur la chauffe.

GRILLE FIXEE D'AVANCE (N = 24) : ER {aucun ; ER 12 H1 < 0,25 ; ER 24 H1 < 0,25} x sortie au temps {non ; 12 h sans
+0,5 ATR} x objectif partiel {non ; 1/2 a +1 ATR} x cassure {originale ; adaptee}. Le reglage « aucun/non/non/
originale » est exactement le portefeuille TOUT (controle). Portefeuille candidat = les 6 familles poids 1, bt_or_h1
et cassure_h1 remplacees par leur version du reglage. Evaluation EXACTEMENT celle de regime_socle.evalue (egal, walk
6 mois / 1 mois au meilleur t, White sur les 24 + walk contre TOUT et SUIVRE5, P1 / P2 / RES, spread reel et double,
meme critere). Rien n'est regle sur la periode reservee (>= 05/2026) : la grille est fixee ici, le walk n'apprend
que sur les 6 mois precedant chaque mois de test.
Controle M5 (sans selection) : bt_or M5 d'origine (banc_bt_regulier.simule, reglage M5) contre les 12 variantes de
sortie bt_or (memes regles, fenetres en heures converties en bougies M5 : 12 h = 144, 24 h = 288), or M5
06/2025 -> 11/2026 (xau_m5_2025a + xau_m5_90k), gain en R, spread reel.
Usage : python3 banc_regime_p7.py"""
import itertools, time, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import regime_socle as S
import banc_bt_regulier as BR

PAS, STOP, MAXP = BR.PAS, BR.STOP, BR.MAXP
ER_OPT = {"er-": None, "er12": (12, 0.25), "er24": (24, 0.25)}
TPS_OPT = {"t-": None, "t12": (12, 0.5)}
OBJ_OPT = {"o-": None, "o1": 1.0}
CAS_OPT = ("cas0", "casA")
SERRE = 0.5


def eff(c, n):
    """Ratio d'efficacite de Kaufman a chaque bougie k (bougies k-n..k) ; nan au debut."""
    c = pd.Series(c)
    return ((c - c.shift(n)).abs() / c.diff().abs().rolling(n).sum()).values


def simule_adapt(d, span, heures, debut, er=None, tps=None, obj=None, nb_h=1):
    """Copie de BR.simule avec sortie adaptative. nb_h = bougies par heure (1 en H1, 12 en M5) pour les fenetres."""
    c, hi, lo, sp, t = (d[x].values for x in ("cloture", "haut", "bas", "sp", "heure"))
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values           # ATR des jours PRECEDENTS (shift 1)
    E = eff(c, er[0] * nb_h) if er else None
    P, ouvert = [], {}
    for i in range(debut, len(c)):
        for s in list(ouvert):
            p = ouvert[s]
            # --- distance du stop : ER de la bougie i-1 (fermee) seulement ; aucune info de la bougie i
            dist = p["stop"]
            if er and E[i - 1] == E[i - 1] and E[i - 1] < er[1]:
                dist = SERRE * p["stop"]
            niv = p["meilleur"] - s * dist
            p["niveau"] = niv if p["niveau"] is None else (max(p["niveau"], niv) if s > 0 else min(p["niveau"], niv))
            niveau = p["niveau"]
            if (lo[i] <= niveau) if s > 0 else (hi[i] + sp[i] >= niveau):
                p = ouvert.pop(s)
                g = p["g"] + sum(q * s * (niveau - e) for e, q in zip(p["e"], p["q"])) / p["stop"]
                P.append((t[p["i"]], t[i], s, g, p["stop"], c[p["i"]]))
                continue
            # --- objectif partiel (ordre limite pose a l'avance, touche pendant la bougie i)
            if obj and not p["part"]:
                L = p["e0"] + s * obj * p["atr"]
                if (hi[i] >= L) if s > 0 else (lo[i] + sp[i] <= L):
                    p["g"] += sum(0.5 * q * s * (L - e) for e, q in zip(p["e"], p["q"])) / p["stop"]
                    p["q"] = [0.5 * q for q in p["q"]]; p["part"] = True
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            # --- sortie au temps a la CLOTURE de la bougie i (bougie i fermee : decision et execution a c[i])
            if tps and i - p["i"] >= tps[0] * nb_h and s * (p["meilleur"] - p["e0"]) < tps[1] * p["atr"]:
                px = c[i] if s > 0 else c[i] + sp[i]
                p = ouvert.pop(s)
                g = p["g"] + sum(q * s * (px - e) for e, q in zip(p["e"], p["q"])) / p["stop"]
                P.append((t[p["i"]], t[i], s, g, p["stop"], c[p["i"]]))
                continue
            while not p["part"] and len(p["e"]) < MAXP and s * (c[i] - p["prochain"]) >= 0:
                if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                    p["e"].append(c[i] + (sp[i] if s > 0 else -sp[i])); p["q"].append(1.0)
                p["prochain"] += s * p["pas"]
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if s not in ouvert:
                ouvert[s] = {"i": i, "e": [c[i] + (sp[i] if s > 0 else -sp[i])], "q": [1.0], "meilleur": c[i],
                             "stop": STOP * atr[i], "pas": PAS * atr[i], "prochain": c[i] + s * PAS * atr[i],
                             "niveau": None, "e0": c[i], "atr": atr[i], "part": False, "g": 0.0}
    return pd.DataFrame(P, columns=["t0", "t1", "s", "g", "stop", "px"])


def cassure_adapt(d, s, h=3, hmax=6, n_er=6, seuil=0.4):
    """Copie de B.trades (decision cloture i, entree ouverture i+1) avec prolongation : a la cloture x (fermee),
    on garde si x < i+hmax, ER(6) des bougies x-5..x >= seuil et trade gagnant ; sinon sortie a c[x]."""
    o, c, sp = d["ouverture"].values, d["cloture"].values, d["sp"].values
    E = eff(c, n_er)
    s = np.nan_to_num(s.values)
    res, idx, fin, i, n = [], [], [], 0, len(c)
    while i < n - hmax - 1:
        if s[i] != 0:
            e, x = i + 1, i + h
            while x < i + hmax and E[x] >= seuil and s[i] * (c[x] - o[e]) > 0:
                x += 1                                   # decision a la cloture x : n'utilise que les bougies <= x
            if s[i] > 0:
                g = (c[x] - (o[e] + sp[e])) / o[e]
            else:
                g = (o[e] - (c[x] + sp[x])) / o[e]
            res.append(g * 1e4); idx.append(i); fin.append(x)
            i = x
        else:
            i += 1
    return np.array(res), np.array(idx, int), np.array(fin, int)


_CT = {}


def trades_mod(er, tps, obj, cas, cout):
    """DataFrame (fam, dec, fin, g, jour) des 3 familles or H1, comme regime_socle._fam_trades, version modifiee."""
    cle = (er, tps, obj, cas, cout)
    if cle in _CT:
        return _CT[cle]
    d = S.OR_H1.copy(); d["sp"] = d["sp"] * cout
    dd = d.reset_index(drop=True)
    kb = ("bt", er, tps, obj, cout)
    if kb not in _CT:
        _CT[kb] = simule_adapt(dd, 48, S.H1_HEURES, 60, ER_OPT[er], TPS_OPT[tps], OBJ_OPT[obj])
    P = _CT[kb]
    out = [pd.DataFrame({"fam": "bt_or_h1", "dec": pd.to_datetime(P.t0, unit="s"),
                         "fin": pd.to_datetime(P.t1, unit="s") + pd.Timedelta("1h"), "g": P.g.values})]
    hh, bb = d["haut"].shift(1).rolling(12).max(), d["bas"].shift(1).rolling(12).min()
    sc = (d["cloture"] > hh).astype(float) - (d["cloture"] < bb).astype(float)
    for nom, sg in (("cassure_h1", sc), ("retour_h1", -sc)):
        if nom == "cassure_h1" and cas == "casA":
            g, i, x = cassure_adapt(d, sg)
            out.append(pd.DataFrame({"fam": nom, "dec": d.index[i] + pd.Timedelta("1h"),
                                     "fin": d.index[x] + pd.Timedelta("1h"), "g": g}))
            continue
        xx, i = S.B.trades(d, sg, 3, mult=1.0)
        out.append(pd.DataFrame({"fam": nom, "dec": d.index[i] + pd.Timedelta("1h"),
                                 "fin": d.index[np.minimum(i + 3, len(d) - 1)] + pd.Timedelta("1h"), "g": xx[:, 0]}))
    T = pd.concat(out, ignore_index=True)
    T["jour"] = T.dec.dt.floor("D")
    T = T[(T.jour >= S.DEBUT) & (T.jour <= S.FIN)].reset_index(drop=True)
    _CT[cle] = T
    return T


def pnl_mod(cfg, cout):
    T = trades_mod(*cfg, cout)
    _, J, ech = S.base(cout)                       # ech = echelle de la famille d'ORIGINE (spread reel, chauffe)
    return S._pnl_fams(T, J, S.W_tout(), ech)


def evalue_p7(nom, grille, cout_double=True):
    """Copie de regime_socle.evalue ; seul change le P&L des candidats (familles modifiees, poids TOUT)."""
    res = {}
    for cout in ((1.0, 2.0) if cout_double else (1.0,)):
        Wt, Ws5 = S.W_tout(), S.W_suivre5(cout)
        Sx = {c: S.egal(pnl_mod(cfg, cout).sum(1), Wt) for c, cfg in grille.items()}
        tout = S.egal(S.pnl(Wt, cout), Wt); s5 = S.egal(S.pnl(Ws5, cout), Ws5)
        wf, choix = S.walk(Sx)
        tout_o, s5_o = tout.reindex(wf.index), s5.reindex(wf.index)
        Dm_t = np.column_stack([wf - tout_o] + [Sx[c].reindex(wf.index) - tout_o for c in Sx])
        Dm_5 = np.column_stack([wf - s5_o] + [Sx[c].reindex(wf.index) - s5_o for c in Sx])
        p_t, p_5 = S.white(Dm_t), S.white(Dm_5)
        r = {"wf": wf, "tout": tout_o, "suivre5": s5_o, "choix": choix, "p_tout": p_t, "p_s5": p_5,
             "p_corr": max(p_t, p_5), "S": Sx}
        for lab, s in (("wf", wf), ("tout", tout_o), ("suivre5", s5_o)):
            p1, p2, rr = S._per(s)
            r[lab + "_P1"], r[lab + "_P2"], r[lab + "_RES"] = p1.sum(), p2.sum(), rr.sum()
        p1w, p2w, _ = S._per(wf - tout_o); p15, p25, _ = S._per(wf - s5_o)
        r["t_tout"], r["t_s5"] = S.tst(wf - tout_o), S.tst(wf - s5_o)
        r["bat"] = (r["wf_P1"] > 0 and r["wf_P2"] > 0 and p1w.sum() > 0 and p2w.sum() > 0
                    and p15.sum() > 0 and p25.sum() > 0)
        res[cout] = r
    r1 = res[1.0]
    ok = r1["bat"] and r1["p_corr"] < 0.05 and (2.0 not in res or res[2.0]["bat"])
    res["retenu"] = bool(ok)
    res["N"] = len(grille)
    print("\n=== %s : %d reglages, walk-forward 6 mois / 1 mois, exposition egale a TOUT, unite u ===" % (nom, len(grille)))
    print("%-8s %-10s %9s %9s %9s %8s %8s" % ("spread", "serie", "P1 22-24", "P2 24-26", "dont RES", "t/TOUT", "t/SUIV5"))
    for cout in res:
        if not isinstance(cout, float):
            continue
        r = res[cout]
        for lab in ("wf", "tout", "suivre5"):
            print("%-8s %-10s %+9.1f %+9.1f %+9.1f %8s %8s" % ("x%.0f" % cout, lab, r[lab + "_P1"], r[lab + "_P2"],
                  r[lab + "_RES"], "%+.2f" % r["t_tout"] if lab == "wf" else "", "%+.2f" % r["t_s5"] if lab == "wf" else ""))
        print("         p corrige (White, %d reglages + wf) : contre TOUT %.3f, contre SUIVRE5 %.3f" % (len(grille), r["p_tout"], r["p_s5"]))
    cs = pd.Series([c for _, c in r1["choix"]]).value_counts()
    print("  Reglages choisis (spread reel) : " + ", ".join("%s x%d" % (k, v) for k, v in cs.head(6).items()))
    print("  VERDICT %s : %s" % (nom, "RETENU" if ok else "ne tient pas"))
    return res


def controle_m5(cfgs):
    a, b = BR.charge("xau_m5_2025a"), BR.charge("xau_m5_90k")
    d = pd.concat([a, b]).drop_duplicates("heure").sort_values("heure").reset_index(drop=True)
    print("\n=== Controle or M5 (%s -> %s, %d bougies), bt_or reglage M5, spread reel, gain en R (sans selection) ==="
          % (pd.to_datetime(d.heure.iloc[0], unit="s").date(), pd.to_datetime(d.heure.iloc[-1], unit="s").date(), len(d)))
    P0 = BR.simule(d)
    m0 = P0.groupby(pd.to_datetime(P0.t1, unit="s").dt.to_period("M")).g.sum()
    print("%-18s %6s %8s %6s %8s %8s" % ("variante", "pan.", "total R", "t", "mois<0", "R/pan."))
    print("%-18s %6d %+8.1f %+6.2f %5d/%-2d %+8.3f" % ("origine (BR)", len(P0), P0.g.sum(), S.tst(P0.g), (m0 < 0).sum(), len(m0), P0.g.mean()))
    out = {}
    for er, tps, obj in cfgs:
        P = simule_adapt(d, 576, BR.H_M5, 600, ER_OPT[er], TPS_OPT[tps], OBJ_OPT[obj], nb_h=12)
        m = P.groupby(pd.to_datetime(P.t1, unit="s").dt.to_period("M")).g.sum()
        out[(er, tps, obj)] = P.g.sum()
        print("%-18s %6d %+8.1f %+6.2f %5d/%-2d %+8.3f" % ("/".join((er, tps, obj)), len(P), P.g.sum(), S.tst(P.g), (m < 0).sum(), len(m), P.g.mean()))
    return P0.g.sum(), out


if __name__ == "__main__":
    t0 = time.time()
    # controle : le reglage neutre reproduit exactement les trades du socle
    T0, _, ech = S.base(1.0)
    Tm = trades_mod("er-", "t-", "o-", "cas0", 1.0)
    print("Controle reglage neutre = socle : %s (ecart max g %.2e)" % (len(T0) == len(Tm), np.abs(T0.g.values - Tm.g.values).max()))
    GR = list(itertools.product(ER_OPT, TPS_OPT, OBJ_OPT, CAS_OPT))
    grille = {"/".join(k): k for k in GR}
    # description (information, spread reel) : familles modifiees seules, en u
    print("\nFamilles modifiees seules (poids 1, spread reel, u) : bt_or_h1 P1 / P2 / RES | cassure_h1 P1 / P2 / RES")
    for k in GR:
        P = pnl_mod(k, 1.0)
        a = [P[f][(P.index >= S.OOS) & (P.index <= S.P1_FIN)].sum() for f in ("bt_or_h1", "cassure_h1")]
        b = [P[f][P.index > S.P1_FIN].sum() for f in ("bt_or_h1", "cassure_h1")]
        r = [P[f][P.index >= S.RES].sum() for f in ("bt_or_h1", "cassure_h1")]
        print("  %-22s %+7.1f %+7.1f %+7.1f | %+7.1f %+7.1f %+7.1f" % ("/".join(k), a[0], b[0], r[0], a[1], b[1], r[1]))
    res = evalue_p7("p7 robuste (sortie adaptative or H1)", grille)
    S.ligne_csv("p7 robuste", res)
    print("  Choix mois par mois : " + " ".join("%s:%s" % (m, c) for m, c in res[1.0]["choix"]))
    controle_m5(list(itertools.product(ER_OPT, TPS_OPT, OBJ_OPT)))
    print("%.0f s" % (time.time() - t0))
