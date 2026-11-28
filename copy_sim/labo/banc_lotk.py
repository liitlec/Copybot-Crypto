"""Banc Lot K (PRIORITES 27/11 9 h 35, demande écrite de Baptiste) : taille des renforts de bt_or_plus par coefficient.
CONTRAT FIGÉ ET POUSSÉ AVANT TOUT RÉSULTAT.

DONNÉES et CADRE : ceux du lot J (banc_lotj) : or M5 du courtier, principal = paniers fermés 06/08/2025 -> 31/08/2026,
RÉSERVE = 01/09 -> 11/11/2026 ; spread réel puis doublé ; même entrée, mêmes renforts (tous les 0,25 ATR, 5 positions),
SORTIE v4 (point mort dès 4 positions + paliers +2/+4 R) pour TOUTES les variantes. Seule change la taille w_n du
n-ième ordre du panier (w_1 = 1, en lots de base). H1 2022-24 / 2024-26 en information.
VARIANTES (13 + référence) :
  REF       v4 : w_n = n (1-2-3-4-5) ;
  g1,2 / g1,4 / g1,6 / g2,0   géométrique fixe w_n = c^(n-1), 5 positions ; g1,4x6 : c = 1,4 et 6 positions ;
  d0,8      décroissant w_n = 0,8^(n-1) ;
  Adaptatifs (w_n = w_(n-1) x c, c calculé au moment du renfort avec les seules bougies fermées, borné 1,0-2,0) :
  er4, er12      c = 1 + efficacité de Kaufman de la clôture sur 48 / 144 bougies M5 (4 h / 12 h) ;
  er4x2          c = 1 + 2 x efficacité 4 h (borné à 2) ;
  gain2, gain4   c = 1 + gain latent du panier en R / 2 (resp. / 4), borné ;
  volbas, volhaut  c = 1 + (1 - ATR/médiane 20 j de l'ATR) (calme -> plus gros) / 1 + (ATR/médiane - 1) (agité -> plus
                 gros), bornés.
MESURES : brut (base 1) : total R, gain÷pire baisse, Sharpe journalier ; À RISQUE ÉGAL : chaque variante multipliée par
  un facteur constant qui donne le même écart-type journalier que REF sur la période principale (le même facteur sert
  sur la réserve et pour l'argent) ; réserve : total et gain÷pire baisse ; argent : 20 000 USC, base 0,05 x solde /
  20 000 (v3) x facteur, P(arrêt -34 %) en 12 mois (Monte-Carlo du lot I, 1 000 parcours) ; plus grosse position et
  plus gros panier en lots à base 0,05 x facteur (signalé si une position dépasse le plafond local 0,25 lot) et marge
  maximale du panier au levier 500 (contrat 1 : marge = lots x prix / 500 $) ; paniers démo/réels depuis le 18/11
  (rejeu GC=F 5 min du lot J, descriptif).
TESTS : placebo = signes des différences appariées (paniers de même ouverture, séries à risque égal) tirés au hasard,
  2 000 tirages, période principale ; correction de Holm sur les 13.
RETENUE si (à risque égal) : gain÷pire baisse ET Sharpe > REF sur la période principale ; total ET gain÷pire baisse >
  REF sur la réserve ; p Holm < 0,05 ; > REF au spread doublé (principale) ; P(arrêt) pas plus de 2 points au-dessus de
  REF ; aucune position au-dessus de 0,25 lot à base 0,05.
Si une variante est RETENUE : préparer le robot réel v5 SANS le publier (VERSION inchangée) ; Baptiste décide.
Usage : python3 banc_lotk.py
"""
import os, json, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_loth as H
import banc_loti as I
import banc_lotj as LJ
import banc_lotg as G

ICI = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(2711)
V4 = {"pm": 4, "pal": (2, 4)}
VARS = {"REF": ("arith", None, 5)}
for c in (1.2, 1.4, 1.6, 2.0):
    VARS["g%s" % str(c).replace(".", ",")] = ("geo", c, 5)
VARS["g1,4x6"] = ("geo", 1.4, 6)
VARS["d0,8"] = ("geo", 0.8, 5)
VARS.update({"er4": ("er", (48, 1.0), 5), "er12": ("er", (144, 1.0), 5), "er4x2": ("er", (48, 2.0), 5),
             "gain2": ("gain", 2.0, 5), "gain4": ("gain", 4.0, 5), "volbas": ("volbas", None, 5),
             "volhaut": ("volhaut", None, 5)})


def efficacite(c, n):
    s = pd.Series(c)
    return ((s - s.shift(n)).abs() / s.diff().abs().rolling(n).sum()).fillna(0).values


def simule(d, span, heures, debut, var, mult=1.0):
    mode, prm, maxpos = var
    c, hi, lo, t = (d[x].values for x in ("cloture", "haut", "bas", "heure"))
    sp = d["sp"].values * mult
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr_j = tr.rolling(20).mean().shift(1)
    vr = (atr_j / atr_j.rolling(20).median().shift(1)).reindex(jour).values     # ATR / médiane 20 j (connue)
    atr = atr_j.reindex(jour).values
    er = {n: efficacite(c, n) for n in (48, 144)}
    P, ouvert = [], {}

    def taille(p, i, s):
        n = len(p["w"]) + 1
        if mode == "arith":
            return float(n)
        if mode == "geo":
            return prm ** (n - 1)
        if mode == "er":
            k = min(max(1 + prm[1] * er[prm[0]][i], 1.0), 2.0)
        elif mode == "gain":
            x = c[i] if s > 0 else c[i] + sp[i]
            gR = sum(w * s * (x - e) for w, e in zip(p["w"], p["e"])) / p["unite"]
            k = min(max(1 + gR / prm, 1.0), 2.0)
        elif mode == "volbas":
            k = min(max(1 + (1 - vr[i]), 1.0), 2.0) if vr[i] == vr[i] else 1.0
        else:
            k = min(max(1 + (vr[i] - 1), 1.0), 2.0) if vr[i] == vr[i] else 1.0
        return p["w"][-1] * k

    for i in range(debut, len(c)):
        for s in list(ouvert):
            p = ouvert[s]
            niv = LJ.niveau_sortie(V4, s, p["meilleur"], p["e"], p["w"], p["A"], p["unite"], 0.0, sp[i])
            if (lo[i] <= niv) if s > 0 else (hi[i] + sp[i] >= niv):
                usd = sum(w * s * (niv - e) for w, e in zip(p["w"], p["e"]))
                P.append((t[p["i"]], t[i], s, usd / p["unite"], usd, max(p["w"]), sum(p["w"]), c[i]))
                del ouvert[s]
                continue
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            while len(p["e"]) < maxpos and s * (c[i] - p["prochain"]) >= 0:
                if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                    w = taille(p, i, s)
                    p["e"].append(c[i] + (sp[i] if s > 0 else -sp[i])); p["w"].append(w)
                p["prochain"] += s * p["pas"]
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if s not in ouvert:
                ouvert[s] = {"i": i, "e": [c[i] + (sp[i] if s > 0 else -sp[i])], "w": [1.0], "meilleur": c[i],
                             "A": atr[i], "unite": 0.6667 * atr[i], "pas": 0.25 * atr[i], "prochain": c[i] + s * 0.25 * atr[i]}
    P = pd.DataFrame(P, columns=["t0", "t1", "s", "g", "usd", "wmax", "wsum", "prix"])
    P["d0"] = pd.to_datetime(P.t0, unit="s"); P["d1"] = pd.to_datetime(P.t1, unit="s"); P["jour"] = P.d1.dt.floor("D")
    return P


def etude():
    d, k = G.jeu_m5(); k.pop("bars_h")
    R = {m: {v: simule(d, var=x, mult=m, **k) for v, x in VARS.items()} for m in (1.0, 2.0)}
    dh, kh = G.jeu_h1(); kh.pop("bars_h")
    RH = {v: simule(dh, var=x, **kh) for v, x in VARS.items()}
    ref = R[1.0]["REF"]
    princ = lambda P: P[P.d1 <= LJ.FIN_PRINC]
    sd = lambda P: princ(P).groupby("jour").g.sum().reindex(pd.date_range("2025-08-06", "2026-08-31"), fill_value=0).std()
    s_ref = sd(ref)
    lignes = []
    for v in VARS:
        P = R[1.0][v]; f = s_ref / sd(P)
        Q = P.assign(g=P.g * f, usd=P.usd * f)
        pr, rs = princ(Q), Q[Q.d1 >= LJ.RES0]
        mb, mp, mr = H.mesures(princ(P)), H.mesures(pr), H.mesures(rs)
        row = dict(variante=v, facteur=f, brut_total=mb["total"], brut_g_creux=mb["g_creux"], total=mp["total"],
                   g_creux=mp["g_creux"], sharpe=mp["sharpe"], res_total=mr["total"], res_g_creux=mr["g_creux"])
        P2 = R[2.0][v]; row["total_x2"] = princ(P2).g.sum() * f
        L = I.semaines(I.evenements(Q))
        row["arret_0,05"] = I.mc(L, 0.05, {"bt": 0.0, "c": 0.0}, n=1000).arret.mean()
        u = I.chemin(I.evenements(Q.sort_values("t1")), 0.05, {"bt": 0.0, "c": 0.0})
        row["usc_0,05"], row["pire_0,05"] = u["final"] - I.DEPART, u["pire"]
        row["pos_max_lots"] = 0.05 * f * P.wmax.max()
        row["panier_max_lots"] = 0.05 * f * P.wsum.max()
        row["marge_max_usd"] = (0.05 * f * P.wsum * P.prix / 500).max()
        row["depasse_0,25"] = int((0.05 * f * P.wmax > 0.25 + 1e-9).sum())
        if v != "REF":
            m = princ(ref).merge(pr, on="t0", suffixes=("_r", "_v")); dif = (m.g_v - m.g_r).values
            row["placebo_p"] = (np.array([(dif * rng.choice((-1, 1), len(dif))).sum() for _ in range(2000)]) >= dif.sum()).mean()
        ph = RH[v]
        for bn, msk in (("H1_22_24", ph.jour <= H.B1F), ("H1_24_26", ph.jour >= H.B2_0)):
            row[bn] = H.mesures(ph[msk])["g_creux"]
        lignes.append(row)
    T = pd.DataFrame(lignes)
    idx = T.index[T.variante != "REF"]
    T.loc[idx, "p_holm"] = H.holm(T.loc[idx, "placebo_p"].values)
    r0 = T.iloc[0]
    T["retenue"] = [bool(r.variante != "REF" and r.g_creux > r0.g_creux and r.sharpe > r0.sharpe and r.res_total > r0.res_total
                         and r.res_g_creux > r0.res_g_creux and r.p_holm < 0.05 and r.total_x2 > r0.total_x2
                         and r["arret_0,05"] <= r0["arret_0,05"] + 0.02 and r["depasse_0,25"] == 0) for _, r in T.iterrows()]
    return T


def reels(T):
    """Paniers démo fermés depuis le 18/11 rejoués (lot J) avec les tailles fixes de chaque variante (adaptatifs : non)."""
    gc = pd.read_csv(os.path.join(ICI, "donnees", "lotj_gc_5m.csv.gz"), index_col=0, parse_dates=True)
    gc.columns = ["open", "high", "low", "close"]
    demo = [p for p in LJ.paniers_journal(os.path.join(ICI, "mt5", "robot_journal.jsonl"), "bt_or_plus_opt")
            if p["fin"] is not None and None not in p["e"]]
    out = []
    for p in demo:
        row = {"ouverture": str(p["t"][0])[:16], "positions": len(p["e"]), "R_journal": p["R"]}
        for v, (mode, prm, mx) in VARS.items():
            if mode not in ("arith", "geo"):
                continue
            q = dict(p, w=[float(n + 1) if mode == "arith" else prm ** n for n in range(len(p["e"]))])
            f = float(T.loc[T.variante == v, "facteur"].iloc[0])
            row[v] = LJ.rejoue_reel(q, gc, V4)[0] * f
        out.append(row)
    return pd.DataFrame(out)


if __name__ == "__main__":
    pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40)
    T = etude(); T.to_csv(os.path.join(ICI, "donnees", "lotk_renforts.csv"), index=False)
    print(T.round(3).to_string(index=False))
    TR = reels(T); TR.to_csv(os.path.join(ICI, "donnees", "lotk_paniers_reels.csv"), index=False)
    print("\npaniers demo depuis le 18/11 (rejeu GC=F, sortie v4, a risque egal)"); print(TR.round(2).to_string(index=False))


CONTRAT_CLIQUET_PARTIEL = """AJOUT AU LOT K (Baptiste 27/11 9 h 45 : « retirer une partie des gains si ça descend trop, laisser courir le
reste »). CONTRAT FIGÉ ET POUSSÉ AVANT SES RÉSULTATS. Pyramide actuelle 1-2-3-4-5 et sortie v4 pour le reste.
Déclencheur, une seule fois par panier : le gain maximal latent du panier (clôtures) a atteint 2 / 3 R et le panier en
a rendu 30 / 40 / 50 % (niveau de prix où le gain latent vaut 70 / 60 / 50 % du maximum, touché par bas/haut + spread).
Fermeture partielle à ce niveau : « moitié » = la moitié de chaque position ; « récents » = les positions les plus
récentes (ce sont aussi les plus grosses en 1-2-3-4-5) jusqu'à au moins la moitié de la taille du panier. Le reste
continue sous la sortie v4 (point mort recalculé sur ce qui reste). 12 variantes (3 x 2 x 2) + REF (v4).
Mêmes mesures, même jugement et même correction (Holm sur les 12) que le lot K, à risque égal ; plus : le panier réel
du 27/11 (0,02 @3563,54 + 0,04 @3598,58 + 0,06 @3648,08, meilleur 3 664) calculé directement.
"""


PARTIELS = {"REF": None}
for k_ in (0.3, 0.4, 0.5):
    for s_ in (2, 3):
        for m_ in ("moitie", "recents"):
            PARTIELS["p%d_%d_%s" % (k_ * 100, s_, m_)] = (k_, s_, m_)


def simule_partiel(d, span, heures, debut, cfg, mult=1.0):
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
            vivants = [(w, e) for w, e in zip(p["w"], p["e"]) if w > 0]
            W = sum(w for w, _ in vivants)
            if cfg and not p["fait"] and p["gmax"] >= cfg[1] * p["unite"] and W > 0:
                moyen = sum(w * e for w, e in vivants) / W
                nivp = moyen + s * (1 - cfg[0]) * p["gmax"] / W
                if (lo[i] <= nivp) if s > 0 else (hi[i] + sp[i] >= nivp):
                    p["fait"] = True
                    if cfg[2] == "moitie":
                        p["real"] += sum(0.5 * w * s * (nivp - e) for w, e in zip(p["w"], p["e"]))
                        p["w"] = [0.5 * w for w in p["w"]]
                    else:
                        ferme = 0.0
                        for q in range(len(p["w"]) - 1, -1, -1):
                            if ferme >= 0.5 * W:
                                break
                            if p["w"][q] > 0:
                                p["real"] += p["w"][q] * s * (nivp - p["e"][q]); ferme += p["w"][q]; p["w"][q] = 0.0
            vw = [w for w in p["w"] if w > 0]
            if vw:
                ee = [e for w, e in zip(p["w"], p["e"]) if w > 0]
                niv = LJ.niveau_sortie(V4, s, p["meilleur"], ee if len(p["e"]) >= 4 else ee, vw, p["A"], p["unite"], 0.0, sp[i]) \
                    if len(p["e"]) >= 4 else LJ.niveau_sortie({"pal": (2, 4)}, s, p["meilleur"], [p["e"][0]] + ee[1:], vw, p["A"], p["unite"], 0.0, sp[i])
                touche = (lo[i] <= niv) if s > 0 else (hi[i] + sp[i] >= niv)
            else:
                touche, niv = True, c[i]
            if touche:
                usd = p["real"] + sum(w * s * (niv - e) for w, e in zip(p["w"], p["e"]) if w > 0)
                P.append((t[p["i"]], t[i], s, usd / p["unite"], usd))
                del ouvert[s]
                continue
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            while len(p["e"]) < 5 and s * (c[i] - p["prochain"]) >= 0:
                if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                    p["e"].append(c[i] + (sp[i] if s > 0 else -sp[i])); p["w"].append(float(len(p["e"])))
                p["prochain"] += s * p["pas"]
            if not p["fait"]:
                x = c[i] if s > 0 else c[i] + sp[i]
                p["gmax"] = max(p["gmax"], sum(w * s * (x - e) for w, e in zip(p["w"], p["e"])))
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if s not in ouvert:
                ouvert[s] = {"i": i, "e": [c[i] + (sp[i] if s > 0 else -sp[i])], "w": [1.0], "meilleur": c[i],
                             "A": atr[i], "unite": 0.6667 * atr[i], "pas": 0.25 * atr[i], "prochain": c[i] + s * 0.25 * atr[i],
                             "gmax": 0.0, "fait": False, "real": 0.0}
    P = pd.DataFrame(P, columns=["t0", "t1", "s", "g", "usd"])
    P["d0"] = pd.to_datetime(P.t0, unit="s"); P["d1"] = pd.to_datetime(P.t1, unit="s"); P["jour"] = P.d1.dt.floor("D")
    return P


def etude_partiel():
    d, k = G.jeu_m5(); k.pop("bars_h")
    R = {m: {v: simule_partiel(d, cfg=x, mult=m, **k) for v, x in PARTIELS.items()} for m in (1.0, 2.0)}
    dh, kh = G.jeu_h1(); kh.pop("bars_h")
    RH = {v: simule_partiel(dh, cfg=x, **kh) for v, x in PARTIELS.items()}
    princ = lambda P: P[P.d1 <= LJ.FIN_PRINC]
    sd = lambda P: princ(P).groupby("jour").g.sum().reindex(pd.date_range("2025-08-06", "2026-08-31"), fill_value=0).std()
    ref = R[1.0]["REF"]; s_ref = sd(ref)
    lignes = []
    for v in PARTIELS:
        P = R[1.0][v]; f = s_ref / sd(P); Q = P.assign(g=P.g * f, usd=P.usd * f)
        pr, rs = princ(Q), Q[Q.d1 >= LJ.RES0]
        mp, mr = H.mesures(pr), H.mesures(rs)
        row = dict(variante=v, facteur=f, brut_total=princ(P).g.sum(), total=mp["total"], g_creux=mp["g_creux"],
                   sharpe=mp["sharpe"], res_total=mr["total"], res_g_creux=mr["g_creux"],
                   total_x2=princ(R[2.0][v]).g.sum() * f)
        row["arret_0,05"] = I.mc(I.semaines(I.evenements(Q)), 0.05, {"bt": 0.0, "c": 0.0}, n=1000).arret.mean()
        if v != "REF":
            m = princ(ref).merge(pr, on="t0", suffixes=("_r", "_v")); dif = (m.g_v - m.g_r).values
            row["placebo_p"] = (np.array([(dif * rng.choice((-1, 1), len(dif))).sum() for _ in range(2000)]) >= dif.sum()).mean()
        ph = RH[v]
        for bn, msk in (("H1_22_24", ph.jour <= H.B1F), ("H1_24_26", ph.jour >= H.B2_0)):
            row[bn] = H.mesures(ph[msk])["g_creux"]
        lignes.append(row)
    T = pd.DataFrame(lignes)
    idx = T.index[T.variante != "REF"]
    T.loc[idx, "p_holm"] = H.holm(T.loc[idx, "placebo_p"].values)
    r0 = T.iloc[0]
    T["retenue"] = [bool(r.variante != "REF" and r.g_creux > r0.g_creux and r.sharpe > r0.sharpe and r.res_total > r0.res_total
                         and r.res_g_creux > r0.res_g_creux and r.p_holm < 0.05 and r.total_x2 > r0.total_x2
                         and r["arret_0,05"] <= r0["arret_0,05"] + 0.02) for _, r in T.iterrows()]
    return T


def panier_27_partiel(meilleur=3664.0, stop_v4=3590.54):
    e, lots = [3563.54, 3598.58, 3648.08], [0.02, 0.04, 0.06]
    L = sum(lots); moyen = sum(l * z for l, z in zip(lots, e)) / L
    gmax = sum(l * (meilleur - z) for l, z in zip(lots, e))
    out = []
    for k in (0.3, 0.4, 0.5):
        niv = moyen + (1 - k) * gmax / L
        for mode in ("moitie", "recents"):
            if mode == "moitie":
                ferme = [l / 2 for l in lots]
            else:
                ferme, cum = [0.0, 0.0, 0.06], 0.06            # la plus récente (0,06) = la moitié de 0,12
            reste = [l - f for l, f in zip(lots, ferme)]
            encaisse = sum(f * (niv - z) for f, z in zip(ferme, e))
            out.append(dict(variante="p%d (%s)" % (k * 100, mode), niveau=round(niv, 2), encaisse_usd=round(encaisse, 2),
                            si_retour_stop_v4=round(encaisse + sum(r * (stop_v4 - z) for r, z in zip(reste, e)), 2),
                            si_3700=round(encaisse + sum(r * (3700 - z) for r, z in zip(reste, e)), 2)))
    out.append(dict(variante="v4 sans cliquet", niveau=stop_v4, encaisse_usd=0.0,
                    si_retour_stop_v4=round(sum(l * (stop_v4 - z) for l, z in zip(lots, e)), 2),
                    si_3700=round(sum(l * (3700 - z) for l, z in zip(lots, e)), 2)))
    return pd.DataFrame(out)
