"""Banc Lot L (PRIORITES 27/11 9 h 50, demande écrite de Baptiste, fait sur Opus) : tirer plus des tendances sans
augmenter le risque d'arrêt. CONTRAT FIGÉ ET POUSSÉ AVANT TOUT RÉSULTAT.

CADRE : celui des lots J/K. Or M5 du courtier ; principal = paniers / trades fermés 06/08/2025 -> 31/08/2026 ; RÉSERVE =
01/09 -> 11/11/2026 ; H1 2024-26 en information. Référence REF = robot actuel : bt_or_plus v4 (renforts 1-2-3-4-5 tous
les 0,25 ATR, sortie point mort dès 4 positions + paliers +2/+4 R) + les 5 règles courtes telles quelles (0,01 lot).
PISTES NOUVELLES (8 variantes ; seule la partie concernée change, le reste = REF) :
  P1 « pyramide de paniers » : quand un panier atteint un gain latent >= 2 R (P1a) / 4 R (P1b), un 2e panier INDÉPENDANT
     s'ouvre dans le même sens à la clôture suivante (mêmes renforts, même sortie v4, au plus 2 paniers par sens).
  P2 « réentrée » : après une sortie de panier au-delà de +2 R (palier ou point mort en gain), réouverture dans le même
     sens sans attendre les heures d'entrée : P2a à la clôture suivante si la clôture reste du bon côté de l'EMA 2 jours ;
     P2b seulement si une clôture dépasse le prix de sortie (sens du panier) dans les 12 bougies (1 h).
  P3 « renforts sur replis » : à la place de la grille sur cassure, renfort (même taille n, même maximum 5) quand le
     panier est en gain et que la clôture revient toucher la moyenne exponentielle courte (P3a EMA 20 M5, P3b EMA 50 M5)
     dans le sens du panier ; un renfort au plus par repli (il faut ressortir de la moyenne de 0,25 ATR).
  P4 « règles courtes avec le panier » : P4a elan_m15 et cassure_m15 seulement dans le sens d'un panier bt_or_plus d'au
     moins 4 positions ouvert au moment du signal (les 3 autres règles inchangées) ; P4b toutes les règles inchangées
     sauf la tenue d'elan_m15 / cassure_m15 portée de 12 à 24 bougies M15 quand un tel panier est ouvert dans leur sens.
MESURES (série journalière combinée en USC : bt_or_plus = USD par lot de base x 0,05 x 100, règles courtes = gain à 0,01
  lot) : total, gain÷pire baisse, Sharpe ; À RISQUE ÉGAL (facteur constant pour le même écart-type journalier que REF sur
  la période principale, appliqué aussi à la réserve et au Monte-Carlo) ; réserve : total et gain÷pire baisse ; P(arrêt
  -34 %) en 12 mois (Monte-Carlo par semaines du lot I, base 0,05 v3, 1 000 parcours) ; positions simultanées maximales
  (plafond du pont : 10) ; rejeu du panier réel / démo depuis le 18/11 quand c'est calculable.
PLACEBO (par piste, 200 tirages ; p = part des placebos au gain÷pire baisse à risque égal >= réel, période principale) :
  P1 : 2e panier ouvert à des clôtures tirées au hasard pendant la vie d'un panier du même sens (même fréquence) ;
  P2 : réouvertures à des clôtures tirées au hasard après une sortie (même nombre) ; P3 : renforts à des clôtures tirées au
  hasard pendant que le panier est en gain (même fréquence) ; P4 : le même nombre de trades d'elan/cassure gardés (P4a)
  ou allongés (P4b) tirés au hasard par mois. Correction de Holm sur les 8.
RETENUE si (à risque égal) : gain÷pire baisse ET Sharpe > REF sur la période principale ; total ET gain÷pire baisse >
  REF sur la réserve ; p Holm < 0,05 ; > REF au spread doublé ; P(arrêt) pas plus de 2 points au-dessus de REF ; jamais
  plus de 10 positions simultanées. Si une piste est RETENUE : préparer la v5 réelle SANS la publier ; Baptiste décide.
Usage : python3 banc_lotl.py
"""
import os, warnings, time
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_loth as H
import banc_loti as I
import banc_lotj as LJ
import banc_lotg as G

ICI = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(2750)
V4 = {"pm": 4, "pal": (2, 4)}


def simule(d, span, heures, debut, mode=None, prm=None, mult=1.0, hasard=None):
    """bt_or_plus v4 + piste. mode : None (REF), 'p1' (prm = seuil R), 'p2a', 'p2b', 'p3' (prm = n de l'EMA courte).
    hasard = probabilité par bougie éligible (placebo de la piste). Rend (paniers, pleins, compteurs)."""
    c, hi, lo, t = (d[x].values for x in ("cloture", "haut", "bas", "heure"))
    sp = d["sp"].values * mult
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    ec = d["cloture"].ewm(span=prm, min_periods=prm).mean().values if mode == "p3" else None
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    P, pleins, ouverts, attente = [], [], [], {}
    cpt = {"evenements": 0, "eligibles": 0, "max_pos": 0}

    def ouvre(i, s, extra=False):
        ouverts.append({"i": i, "s": s, "e": [c[i] + (sp[i] if s > 0 else -sp[i])], "w": [1.0], "meilleur": c[i],
                        "A": atr[i], "unite": 0.6667 * atr[i], "pas": 0.25 * atr[i], "prochain": c[i] + s * 0.25 * atr[i],
                        "extra": extra, "second": False, "arme": False, "plein": None})

    for i in range(debut, len(c)):
        for p in list(ouverts):
            s = p["s"]
            niv = LJ.niveau_sortie(V4, s, p["meilleur"], p["e"], p["w"], p["A"], p["unite"], 0.0, sp[i])
            if (lo[i] <= niv) if s > 0 else (hi[i] + sp[i] >= niv):
                usd = sum(w * s * (niv - e) for w, e in zip(p["w"], p["e"]))
                P.append((t[p["i"]], t[i], s, usd / p["unite"], usd, p["extra"]))
                if p["plein"] is not None:
                    pleins.append((p["plein"], t[i], s))
                ouverts.remove(p)
                if mode in ("p2a", "p2b") and usd / p["unite"] >= 2:
                    attente[s] = (i, niv)
                continue
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            x = c[i] if s > 0 else c[i] + sp[i]
            latent = sum(w * s * (x - e) for w, e in zip(p["w"], p["e"])) / p["unite"]
            if mode == "p3":
                if len(p["e"]) < 5 and latent > 0 and ec[i] == ec[i]:
                    if s * (c[i] - ec[i]) >= 0.25 * p["A"]:
                        p["arme"] = True
                    touche = (lo[i] <= ec[i]) if s > 0 else (hi[i] >= ec[i])
                    if hasard is not None:
                        cpt["eligibles"] += 1
                        touche, ok = rng.random() < hasard, True
                    else:
                        ok = p["arme"]
                    if touche and ok:
                        p["e"].append(c[i] + (sp[i] if s > 0 else -sp[i])); p["w"].append(float(len(p["w"]) + 1))
                        p["arme"] = False; cpt["evenements"] += 1
            else:
                while len(p["e"]) < 5 and s * (c[i] - p["prochain"]) >= 0:
                    if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                        p["e"].append(c[i] + (sp[i] if s > 0 else -sp[i])); p["w"].append(float(len(p["w"]) + 1))
                    p["prochain"] += s * p["pas"]
            if p["plein"] is None and len(p["e"]) >= 4:
                p["plein"] = t[i]
            if mode == "p1" and not p["extra"] and not p["second"] and sum(q["s"] == s for q in ouverts) < 2:
                if hasard is not None:
                    cpt["eligibles"] += 1
                    go = rng.random() < hasard
                else:
                    go = latent >= prm
                if go:
                    p["second"] = True; cpt["evenements"] += 1
                    ouvre(i, s, extra=True)
        cpt["max_pos"] = max(cpt["max_pos"], sum(len(q["e"]) for q in ouverts))
        if mode in ("p2a", "p2b") and atr[i] == atr[i] and ema[i] == ema[i]:
            for s in (1, -1):
                if any(q["s"] == s for q in ouverts):
                    attente.pop(s, None); continue
                if hasard is not None:
                    if s in attente and i - attente[s][0] <= 12:
                        cpt["eligibles"] += 1
                        if rng.random() < hasard:
                            attente.pop(s); cpt["evenements"] += 1; ouvre(i, s)
                    continue
                if s not in attente:
                    continue
                i0, xs = attente[s]
                if mode == "p2a" and i == i0 + 1:
                    attente.pop(s)
                    if s * (c[i] - ema[i]) > 0:
                        cpt["evenements"] += 1; ouvre(i, s)
                elif mode == "p2b":
                    if i - i0 > 12:
                        attente.pop(s)
                    elif s * (c[i] - xs) > 0:
                        attente.pop(s); cpt["evenements"] += 1; ouvre(i, s)
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if not any(q["s"] == s and not q["extra"] for q in ouverts):
                ouvre(i, s)
    P = pd.DataFrame(P, columns=["t0", "t1", "s", "g", "usd", "extra"])
    P["d0"] = pd.to_datetime(P.t0, unit="s"); P["d1"] = pd.to_datetime(P.t1, unit="s"); P["jour"] = P.d1.dt.floor("D")
    for p in ouverts:
        if p["plein"] is not None:
            pleins.append((p["plein"], t[-1], p["s"]))
    return P, pleins, cpt


# ------------------------------------------------------------------------------------------------ règles courtes
def courtes(pleins, mode=None, mult=1.0, hasard=None):
    """Trades des 5 règles (temps de décision t en secondes, g en $ à 0,01 lot). mode 'p4a' / 'p4b' (voir contrat)."""
    debut = pd.Timestamp("2025-08-06")
    pl = sorted(pleins)
    def plein_dans(t, s):
        return any(a <= t < b and ss == s for a, b, ss in pl)
    out = []
    for nom, (fic, regle, ks, hs, ref) in G.REGLES.items():
        d = G.charge_tf(fic, debut)
        if mult != 1.0:
            d = d.assign(sp=d.sp * mult)
        sig = G.signal(d, regle, ref[0])
        ts = ((d.index - pd.Timestamp("1970-01-01")).total_seconds()).astype(int).values
        if mode == "p4b" and nom in ("elan_m15", "cassure_m15"):
            o, c_, sp_ = d["ouverture"].values, d["cloture"].values, d["sp"].values
            i, n = 0, len(c_)
            while i < n - 25:
                s = sig[i]
                if not s:
                    i += 1; continue
                long_ = plein_dans(ts[i], s) if hasard is None else rng.random() < hasard
                h = 24 if long_ else ref[1]
                e, x = i + 1, i + h
                g = (c_[x] - (o[e] + sp_[e])) if s > 0 else (o[e] - (c_[x] + sp_[x]))
                out.append((ts[i], nom, g, long_))
                i = x
            continue
        T = G.joue(d, sig, ref[1], None, retour=(regle == "retour"))
        tt = ((T.t - pd.Timestamp("1970-01-01")).dt.total_seconds()).astype(int).values
        for a, s, g in zip(tt, T.s.values, T.g.values):
            garde = True
            if mode == "p4a" and nom in ("elan_m15", "cassure_m15"):
                garde = plein_dans(a, s) if hasard is None else rng.random() < hasard
            if garde:
                out.append((a, nom, g, False))
    C = pd.DataFrame(out, columns=["t", "regle", "g", "long"])
    C["d"] = pd.to_datetime(C.t, unit="s")
    return C


# ------------------------------------------------------------------------------------------------ jugement
J0, FIN, R0, R1 = pd.Timestamp("2025-08-06"), LJ.FIN_PRINC, LJ.RES0, pd.Timestamp("2026-11-12")


def serie(P, C):
    """Série journalière en USC (base 0,05 fixe, courtes 0,01 lot)."""
    a = (P.usd * 0.05 * 100).groupby(P.jour).sum()
    b = C.g.groupby(C.d.dt.floor("D")).sum()
    idx = pd.date_range(J0, R1, freq="D")
    return a.reindex(idx, fill_value=0) + b.reindex(idx, fill_value=0)


def mes(x):
    eq = x.cumsum(); dd = (eq - eq.cummax()).min()
    return dict(total=x.sum(), g_creux=x.sum() / -dd if dd < 0 else np.inf, sharpe=x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0)


def evenements(P, C, f):
    ev = [(t, "bt", u * f) for t, u in zip(P.t1.values, P.usd.values)] + [(t, "c", g * f) for t, g in zip(C.t.values, C.g.values)]
    ev.sort(key=lambda x: x[0]); return ev


VARIANTES = {"REF": (None, None, None), "P1a": ("p1", 2.0, None), "P1b": ("p1", 4.0, None), "P2a": ("p2a", None, None),
             "P2b": ("p2b", None, None), "P3a": ("p3", 20, None), "P3b": ("p3", 50, None), "P4a": (None, None, "p4a"),
             "P4b": (None, None, "p4b")}


def un_jeu(d, k, nom, mult=1.0, hasard=None, hasard_c=None, ref_pleins=None):
    mode, prm, cm = VARIANTES[nom]
    P, pleins, cpt = simule(d, mode=mode, prm=prm, mult=mult, hasard=hasard, **k)
    C = courtes(pleins, mode=cm, mult=mult, hasard=hasard_c)
    return P, C, cpt


def etude(n_plac=200):
    d, k = G.jeu_m5(); k.pop("bars_h")
    R = {v: un_jeu(d, k, v) for v in VARIANTES}
    R2 = {v: un_jeu(d, k, v, mult=2.0) for v in VARIANTES}
    Pr, Cr, _ = R["REF"]
    xr = serie(Pr, Cr); sref = xr[:FIN].std()
    lignes = []
    for v in VARIANTES:
        P, C, cpt = R[v]
        x = serie(P, C); f = sref / x[:FIN].std()
        xe = x * f
        mp, mr = mes(xe[:FIN]), mes(xe[R0:])
        row = dict(variante=v, facteur=f, total_brut=x[:FIN].sum(), total=mp["total"], g_creux=mp["g_creux"], sharpe=mp["sharpe"],
                   res_total=mr["total"], res_g_creux=mr["g_creux"], evenements=cpt["evenements"], max_positions=cpt["max_pos"],
                   paniers=len(P), extra=int(P.extra.sum()), trades_courts=len(C))
        P2, C2, _ = R2[v]
        row["total_x2"] = (serie(P2, C2) * f)[:FIN].sum()
        L = I.semaines(evenements(P, C, f))
        row["arret_0,05"] = I.mc(L, 0.05, {"bt": 0.0, "c": 0.0}, n=1000).arret.mean()
        if v != "REF":
            mode, prm, cm = VARIANTES[v]
            if cm is None:
                q = cpt["evenements"] / max(cpt["eligibles"], 1) if cpt["eligibles"] else None
                if q is None:      # compter les bougies éligibles une fois (passage placebo à probabilité nulle)
                    _, _, c0 = simule(d, mode=mode, prm=prm, hasard=0.0, **k)
                    q = cpt["evenements"] / max(c0["eligibles"], 1)
                pl = []
                for _ in range(n_plac):
                    Pp, plp, _ = simule(d, mode=mode, prm=prm, hasard=q, **k)
                    xp = serie(Pp, Cr); pl.append(mes((xp * sref / xp[:FIN].std())[:FIN])["g_creux"])
            else:
                if cm == "p4a":
                    tot = ((Cr.regle == "elan_m15") | (Cr.regle == "cassure_m15")).sum()
                    gard = ((C.regle == "elan_m15") | (C.regle == "cassure_m15")).sum()
                    q = gard / max(tot, 1)
                else:
                    q = C["long"].mean() / max(((C.regle == "elan_m15") | (C.regle == "cassure_m15")).mean(), 1e-9)
                pl = []
                _, pleins_ref, _ = simule(d, **k)
                for _ in range(n_plac):
                    Cp = courtes(pleins_ref, mode=cm, hasard=q)
                    xp = serie(Pr, Cp); pl.append(mes((xp * sref / xp[:FIN].std())[:FIN])["g_creux"])
            row["placebo_p"] = float((np.array(pl) >= mp["g_creux"]).mean())
            row["placebo_med"] = float(np.median(pl))
        lignes.append(row)
    T = pd.DataFrame(lignes)
    idx = T.index[T.variante != "REF"]
    T.loc[idx, "p_holm"] = H.holm(T.loc[idx, "placebo_p"].values)
    r0 = T.iloc[0]
    T["retenue"] = [bool(r.variante != "REF" and r.g_creux > r0.g_creux and r.sharpe > r0.sharpe and r.res_total > r0.res_total
                         and r.res_g_creux > r0.res_g_creux and r.p_holm < 0.05 and r.total_x2 > r0.total_x2
                         and r["arret_0,05"] <= r0["arret_0,05"] + 0.02 and r.max_positions <= 10) for _, r in T.iterrows()]
    return T


def h1_info():
    dh, kh = G.jeu_h1(); kh.pop("bars_h")
    out = []
    for v, (mode, prm, cm) in VARIANTES.items():
        if cm is not None:
            continue
        prm2 = max(1, prm // 12) if mode == "p3" else prm
        P, _, _ = simule(dh, mode=mode, prm=prm2, **kh)
        row = {"variante": v}
        for bn, msk in (("H1_22_24", P.jour <= H.B1F), ("H1_24_26", P.jour >= H.B2_0)):
            row[bn] = H.mesures(P[msk])["g_creux"]; row[bn + "_R"] = P[msk].g.sum()
        out.append(row)
    return pd.DataFrame(out)


if __name__ == "__main__":
    pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40)
    t0 = time.time()
    T = etude(); T.to_csv(os.path.join(ICI, "donnees", "lotl_pistes.csv"), index=False)
    print(T.round(3).to_string(index=False))
    Hh = h1_info(); print(Hh.round(2).to_string(index=False))
    print("fait en %.0f s" % (time.time() - t0))
