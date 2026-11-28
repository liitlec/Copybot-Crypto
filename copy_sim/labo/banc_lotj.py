"""Banc Lot J (PRIORITES 27/11 9 h 15, demande écrite de Baptiste) : protéger les gains du panier bt_or_plus.
CONTRAT FIGÉ ET POUSSÉ AVANT TOUT RÉSULTAT.

DONNÉES : or M5 du courtier 06/08/2025 -> 11/11/2026 (spread réel, puis doublé).
  Période de jugement PRINCIPALE = paniers fermés du 06/08/2025 au 31/08/2026 ; RÉSERVE = 01/09/2026 -> 11/11/2026
  (vérification finale, regardée une seule fois). H1 2022-24 et 2024-26 en information seulement.
Mécanique bt_or_plus (banc_loth.simule : entrées bt_or, sens EMA 2 jours, renforts tous les 0,25 ATR, tailles
1-2-3-4-5, 5 positions). Seule la SORTIE change. Niveaux évalués avec l'état d'avant la bougie (meilleur prix, prix
moyen pondéré, gain maximal latent), touchés par le bas / haut (+ spread pour une vente) ; le plus protecteur s'applique.
VARIANTES (14 + témoin) :
  REF        sortie actuelle : recul de 0,6667 ATR depuis le meilleur prix ;
  pm2, pm3   stop au point mort (prix moyen + spread) dès 3 / 4 positions (après le 2e / 3e renfort) ;
  pal36, pal24, pal153  paliers : recul 0,5 puis 0,35 ATR quand le meilleur prix dépasse +3/+6, +2/+4, +1,5/+3 R
             depuis la 1re entrée ;
  pm3pal36, pm3pal24    combinaison point mort après le 3e renfort + paliers ;
  cl30_2, cl40_2, cl50_2, cl30_3, cl40_3, cl50_3  cliquet : une fois le gain maximal latent du panier >= 2 / 3 R,
             ne jamais rendre plus de 30 / 40 / 50 % de ce gain (stop au prix où le gain latent vaut 70 / 60 / 50 %
             du maximum, avec les positions du moment) ;
  moy3       dès 3 positions, stop au plus protecteur de la sortie actuelle et de « prix moyen - 0,25 ATR » (achat ;
             symétrique en vente) : le stop suiveur se cale sur le prix moyen du panier.
MESURES : total R et en USC (20 000 USC, mise v3 base 0,02), gain÷pire baisse et Sharpe journalier (risque égal),
  gain rendu moyen par panier (gain maximal latent - gain fermé), grands paniers (REF >= +5 R) coupés à moins de la
  moitié, résultat sur la réserve, P(arrêt -34 %) en 12 mois aux bases 0,02 / 0,03 / 0,05 (Monte-Carlo du lot I,
  bt_or_plus seul, 1 000 parcours, période principale + réserve).
TESTS : placebo = signes des différences appariées (paniers de même ouverture) tirés au hasard, 2 000 tirages, sur la
  période principale ; correction de Holm sur les 14 variantes (plus stricte que « 6 essais »).
RETENUE si : gain÷pire baisse ET Sharpe > REF sur la période principale ; total ET gain÷pire baisse > REF sur la
  réserve ; p Holm < 0,05 ; total > REF au spread doublé (principale) ; P(arrêt) à 0,02 pas plus de 2 points au-dessus
  de REF.
PANIERS RÉELS / DÉMO DEPUIS LE 18/11 (descriptif, aucune décision dessus) : les paniers bt_or_plus des journaux (démo
  bt_or_plus_opt et réel), entrées réelles reprises du journal, rejoués sur l'or à terme GC=F 5 min (Yahoo, seule
  source après le 11/11), décalé de l'écart moyen observé entre les prix d'entrée réels et GC=F ; le panier réel
  ouvert du 27/11 est complété jusqu'au dernier prix publié par le pont réel. Approximation dite comme telle.
Si une variante est RETENUE : préparer le robot réel v4 (mode auto) SANS le publier (VERSION inchangée) ; Baptiste décide.
Usage : python3 banc_lotj.py
"""
import os, json, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_loth as H
import banc_loti as I
import banc_lotg as G
import banc_bt_regulier as BR

ICI = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(27)
FIN_PRINC, RES0 = pd.Timestamp("2026-08-31 23:59"), pd.Timestamp("2026-09-01")
VARS = {"REF": {}, "pm2": {"pm": 3}, "pm3": {"pm": 4}, "pal36": {"pal": (3, 6)}, "pal24": {"pal": (2, 4)},
        "pal153": {"pal": (1.5, 3)}, "pm3pal36": {"pm": 4, "pal": (3, 6)}, "pm3pal24": {"pm": 4, "pal": (2, 4)}}
for k_ in (0.3, 0.4, 0.5):
    for s_ in (2, 3):
        VARS["cl%d_%d" % (k_ * 100, s_)] = {"cl": (k_, s_)}
VARS["moy3"] = {"moy": 3}


def niveau_sortie(v, s, meilleur, e, w, A, unite, gmax, sp):
    """Niveau de sortie (le plus protecteur) selon la variante, état d'avant la bougie."""
    dist = 0.6667 * A
    if "pal" in v:
        gR = s * (meilleur - e[0]) / unite
        dist = 0.35 * A if gR >= v["pal"][1] else (0.5 * A if gR >= v["pal"][0] else dist)
    niv = meilleur - s * dist
    W = sum(w); moyen = sum(a * b for a, b in zip(w, e)) / W
    cand = [niv]
    if "pm" in v and len(e) >= v["pm"]:
        cand.append(moyen + s * sp)
    if "moy" in v and len(e) >= v["moy"]:
        cand.append(moyen - s * 0.25 * A)
    if "cl" in v and gmax >= v["cl"][1] * unite:
        k, _ = v["cl"]
        cand.append(moyen + s * (1 - k) * gmax / W)
    return max(cand) if s > 0 else min(cand)


def simule(d, span, heures, debut, v, mult=1.0):
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
            niv = niveau_sortie(v, s, p["meilleur"], p["e"], p["w"], p["A"], p["unite"], p["gmax"], sp[i])
            if (lo[i] <= niv) if s > 0 else (hi[i] + sp[i] >= niv):
                usd = sum(w * s * (niv - e) for w, e in zip(p["w"], p["e"]))
                P.append((t[p["i"]], t[i], s, usd / p["unite"], usd, p["gmax"] / p["unite"], len(p["e"])))
                del ouvert[s]
                continue
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            while len(p["e"]) < 5 and s * (c[i] - p["prochain"]) >= 0:
                if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                    p["e"].append(c[i] + (sp[i] if s > 0 else -sp[i])); p["w"].append(float(len(p["w"]) + 1))
                p["prochain"] += s * p["pas"]
            x = c[i] if s > 0 else c[i] + sp[i]
            p["gmax"] = max(p["gmax"], sum(w * s * (x - e) for w, e in zip(p["w"], p["e"])))
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if s not in ouvert:
                ouvert[s] = {"i": i, "e": [c[i] + (sp[i] if s > 0 else -sp[i])], "w": [1.0], "meilleur": c[i],
                             "A": atr[i], "unite": 0.6667 * atr[i], "pas": 0.25 * atr[i],
                             "prochain": c[i] + s * 0.25 * atr[i], "gmax": 0.0}
    P = pd.DataFrame(P, columns=["t0", "t1", "s", "g", "usd", "mfe", "npos"])
    P["d0"] = pd.to_datetime(P.t0, unit="s"); P["d1"] = pd.to_datetime(P.t1, unit="s"); P["jour"] = P.d1.dt.floor("D")
    return P


def argent(P, b=0.02):
    """Rejeu en USC, mise v3 (base b x solde / 20 000, fixée par panier)."""
    r = I.chemin(I.evenements(P.sort_values("t1")), b, {"bt": 0.0, "c": 0.0})
    return r["final"] - I.DEPART, r["pire"]


def etude():
    d, k = G.jeu_m5(); k.pop("bars_h")
    R = {m: {v: simule(d, v=prm, mult=m, **k) for v, prm in VARS.items()} for m in (1.0, 2.0)}
    dh, kh = G.jeu_h1(); kh.pop("bars_h")
    RH = {v: simule(dh, v=prm, **kh) for v, prm in VARS.items()}
    ref = R[1.0]["REF"]
    lignes = []
    for v in VARS:
        P = R[1.0][v]; pr, rs = P[P.d1 <= FIN_PRINC], P[P.d1 >= RES0]
        mp, mr = H.mesures(pr), H.mesures(rs)
        m = ref[ref.d1 <= FIN_PRINC].merge(pr, on="t0", suffixes=("_r", "_v"))
        grands = m[m.g_r >= 5]
        row = dict(variante=v, paniers=len(pr), total=mp["total"], g_creux=mp["g_creux"], sharpe=mp["sharpe"],
                   rendu=(pr.mfe - pr.g).mean(), grands_coupes="%d/%d" % ((grands.g_v < 0.5 * grands.g_r).sum(), len(grands)),
                   res_total=mr["total"], res_g_creux=mr["g_creux"],
                   total_x2=R[2.0][v][R[2.0][v].d1 <= FIN_PRINC].g.sum())
        u, pire = argent(P); row["usc_0,02"], row["pire_0,02"] = u, pire
        L = I.semaines(I.evenements(P))
        for b in (0.02, 0.03, 0.05):
            row["arret_%.2f" % b] = I.mc(L, b, {"bt": 0.0, "c": 0.0}, n=1000).arret.mean()
        if v != "REF":
            dif = (m.g_v - m.g_r).values
            row["placebo_p"] = (np.array([(dif * rng.choice((-1, 1), len(dif))).sum() for _ in range(2000)]) >= dif.sum()).mean()
        ph = RH[v]
        for bn, msk in (("H1_22_24", ph.jour <= H.B1F), ("H1_24_26", ph.jour >= H.B2_0)):
            row[bn] = H.mesures(ph[msk])["g_creux"]
        lignes.append(row)
    T = pd.DataFrame(lignes)
    idx = T.index[T.variante != "REF"]
    T.loc[idx, "p_holm"] = H.holm(T.loc[idx, "placebo_p"].values)
    r0 = T.iloc[0]
    T["retenue"] = [bool(v != "REF" and r.g_creux > r0.g_creux and r.sharpe > r0.sharpe and r.res_total > r0.res_total
                         and r.res_g_creux > r0.res_g_creux and r.p_holm < 0.05 and r.total_x2 > r0.total_x2
                         and r["arret_0.02"] <= r0["arret_0.02"] + 0.02) for v, r in zip(T.variante, T.itertuples(index=False))]
    return T


# ------------------------------------------------------------------------------------------------ paniers réels
def paniers_journal(f, nom):
    ouv, out = {}, []
    for l in open(f, encoding="utf-8"):
        try:
            d = json.loads(l)
        except ValueError:
            continue
        if d.get("hypothese") != nom or pd.Timestamp(d["heure"]) < pd.Timestamp("2026-11-12", tz="UTC"):
            continue
        ev, s = d.get("evenement"), d.get("sens")
        if ev == "ouverture" and d.get("ok"):
            if d.get("niveau") == 1 or s not in ouv:
                ouv[s] = {"s": s, "e": [], "w": [], "t": [], "dist": d.get("distance_stop")}
            ouv[s]["e"].append(d["prix_obtenu"]); ouv[s]["w"].append(float(d.get("niveau") or len(ouv[s]["e"])))
            ouv[s]["t"].append(pd.Timestamp(d["heure"]).tz_convert(None))
        elif ev == "sortie panier" and s in ouv:
            p = ouv.pop(s); p.update(fin=pd.Timestamp(d["heure"]).tz_convert(None), profit=d.get("profit"), R=d.get("R"))
            out.append(p)
    for p in ouv.values():
        p.update(fin=None, profit=None, R=None); out.append(p)
    return [p for p in out if p["fin"] is None or p["fin"] >= pd.Timestamp("2026-11-18")]


def rejoue_reel(p, gc, v, dernier=None):
    """Rejoue un panier réel (entrées réelles) sur GC=F 5 min décalé ; renvoie (gain en R de base, prix de sortie)."""
    s = p["s"]; unite = p["dist"]; A = unite / 0.6667
    x = gc[gc.index >= p["t"][0].floor("5min")]
    if p["fin"] is not None:
        x = x[x.index <= p["fin"] + pd.Timedelta("1h")]
    dec = np.median([e - gc.close.asof(t) for e, t in zip(p["e"], p["t"])])
    x = x + dec
    e, w, meilleur, gmax, k = [p["e"][0]], [p["w"][0]], p["e"][0], 0.0, 1
    for t, b in x.iterrows():
        while k < len(p["e"]) and p["t"][k] <= t:
            e.append(p["e"][k]); w.append(p["w"][k]); k += 1
        niv = niveau_sortie(v, s, meilleur, e, w, A, unite, gmax, 0.2)
        if (b.low <= niv) if s > 0 else (b.high + 0.2 >= niv):
            return sum(a * s * (niv - z) for a, z in zip(w, e)) / unite, niv, len(e)
        meilleur = max(meilleur, b.high) if s > 0 else min(meilleur, b.low)
        gmax = max(gmax, sum(a * s * (b.close - z) for a, z in zip(w, e)))
    fin = dernier if dernier else x.close.iloc[-1]
    return sum(a * s * (fin - z) for a, z in zip(w, e)) / unite, None, len(e)


def panier_ouvert_27(px_actuel, meilleur=3664.0, sp=0.2):
    """Le panier réel du 27/11 (entrées du pont réel), au meilleur prix cité par Baptiste : niveau de sortie de chaque
    variante et résultat en USD si ce niveau est touché (compte cent, contrat 1 : USD = lots x écart de prix)."""
    e, lots, unite = [3563.54, 3598.58, 3648.08], [0.02, 0.04, 0.06], 73.46
    w = [l / 0.02 for l in lots]; A = unite / 0.6667
    gmax = sum(a * (meilleur - z) for a, z in zip(w, e))
    out = []
    for v, prm in VARS.items():
        niv = niveau_sortie(prm, 1, meilleur, e, w, A, unite, gmax, sp)
        out.append(dict(variante=v, niveau_sortie=round(niv, 2), usd_si_touche=round(sum(l * (niv - z) for l, z in zip(lots, e)), 2),
                        usd_au_meilleur=round(sum(l * (meilleur - z) for l, z in zip(lots, e)), 2)))
    return pd.DataFrame(out)


if __name__ == "__main__":
    pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40)
    T = etude(); T.to_csv(os.path.join(ICI, "donnees", "lotj_sorties.csv"), index=False)
    print(T.round(3).to_string(index=False))
    gc = pd.read_csv(os.path.join(ICI, "donnees", "lotj_gc_5m.csv.gz"), index_col=0, parse_dates=True)
    gc.columns = ["open", "high", "low", "close"]
    demo = paniers_journal(os.path.join(ICI, "mt5", "robot_journal.jsonl"), "bt_or_plus_opt")
    print("\npaniers demo fermes depuis le 18/11 (R de la position de base ; rejeu sur GC=F 5 min decale : approximation)")
    lig = []
    for p in demo:
        if p["fin"] is None or None in p["e"]:
            continue
        row = {"ouverture": str(p["t"][0])[:16], "fin": str(p["fin"])[:16], "sens": p["s"], "positions": len(p["e"]),
               "R_journal": p["R"]}
        for v, prm in VARS.items():
            row[v] = rejoue_reel(p, gc, prm)[0]
        lig.append(row)
    TR = pd.DataFrame(lig); TR.to_csv(os.path.join(ICI, "donnees", "lotj_paniers_reels.csv"), index=False)
    print(TR.round(2).to_string(index=False))
    etat = json.load(open(os.path.join(ICI, "mt5_reel", "etat.json")))
    px = next((q["prix_actuel"] for q in etat.get("positions_robot") or [] if q["sens"] == "achat"), None)
    print("\npanier reel ouvert du 27/11 (0,02 @3563,54 + 0,04 @3598,58 + 0,06 @3648,08), meilleur prix 3 664 ; dernier prix publie", px)
    print(panier_ouvert_27(px).to_string(index=False))
