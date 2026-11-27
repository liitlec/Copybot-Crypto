"""Banc « Ajout au lot N » (PRIORITES 27/11 13 h 40, Baptiste : améliorer les règles courtes pour plus de gain).
CONTRAT FIGÉ ET POUSSÉ AVANT TOUT CALCUL DE CES VARIANTES. Même cadre et même jugement que banc_lotn.py.

RÈGLES (robot réel, réglages actuels de banc_lotg.REGLES, données du courtier 06/08/2025 -> 11/11/2026) :
  elan_m15 (12, tenue 12 M15), cassure_m15 (48, 12 M15), exces_m5 (3, 3 M5), exces_m1 (3, 12 M1),
  retour_court_ar (2,5, 12 M15, avec son objectif / stop propres). REF = chaque règle telle quelle (banc_lotg.joue),
  0,01 lot, une position à la fois par règle. PRINCIPAL = trades entrés 06/08/2025 -> 31/08/2026 ; RÉSERVE =
  01/09 -> 11/11/2026 ; spread réel puis doublé. Le lot G (seuils, tenues, stop 0,5 ATR, heures, sens du panier
  bt_or) n'est PAS refait.
VARIANTES PAR RÈGLE (8 x 5 règles = 40), seule la partie nommée change :
  Sorties, au lieu de la tenue fixe (tenue maximale = 4 x la tenue actuelle ; stop de sécurité 1 ATR jour sauf TS ;
  pour retour_court_ar on garde en plus son stop d'extrême) :
    O05, O10, O15  objectif à +0,5 / +1 / +1,5 ATR jour ;
    TS             stop suiveur à 0,5 ATR jour du meilleur prix (haut / bas) depuis l'entrée ;
    ES             essoufflement : 1re clôture contre le sens sur l'unité de la règle (M15 pour les règles M15, M5
                   pour exces_m5 et exces_m1 — pour celle-ci, clôtures M5 reconstruites des M1) ;
    PM             tenue actuelle, mais stop ramené au prix d'entrée dès que le meilleur prix a fait +0,5 ATR.
  F    filtre du sens (EMA 576 M5, le sens de bt_or) avec la sortie actuelle : tendance courte (elan, cassure,
       exces_m5) seulement si clôture M5 du côté du sens ; contre-tendance (exces_m1, retour_court_ar) seulement si
       l'entrée est DANS le sens (achat de repli en tendance haussière, vente de rebond en baissière).
  Q    taille selon la qualité du signal, sortie actuelle : 0,02 lot si la force du signal dépasse la médiane des
       200 signaux PRÉCÉDENTS de la règle, sinon 0,01 (force : elan = |rendement sur k| / écart-type glissant 100 de
       ce rendement ; cassure = dépassement du canal / ATR ; exces = |z| ; retour = |c - m| / (k x écart-type)).
MESURES : par variante, principal / réserve / spread doublé : trades, total $, $ par trade ; écart à REF ; et pour
  l'ensemble avec bt_or_plus v4 : la règle remplacée par sa variante dans les règles courtes du Monte-Carlo apparié de
  banc_lotm_astra (2 000 parcours, base 0,05) -> P(arrêt -34 %) et equity médiane.
PLACEBOS (graine 2711_1340, 2 000 tirages ; statistique = écart de total à REF sur le principal) :
  sorties : signes des différences appariées (trades de même signal) tirés au hasard ;
  F : autant de trades retirés au hasard (même part) ; Q : autant de trades doublés au hasard (même nombre).
  Correction de Holm sur les 40.
« TIENT » si : total > REF au principal, au spread doublé ET sur la réserve ; p Holm < 0,05 ; P(arrêt) pas plus de
  1 point au-dessus de v4 + REF. « PRESQUE » : tout sauf Holm (p brut < 0,05). Ce qui tient -> démo `_opt` d'abord
  (version démo suivante), JAMAIS en réel sans accord écrit de Baptiste.
Usage : python3 banc_lotn_courtes.py
"""
import os, time, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_loth as H, banc_lotg as G, banc_lotl as LL
import banc_lotm_astra as M

ICI = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(27111340)
FIN, R0 = M.FIN, M.R0
DEBUT = pd.Timestamp("2025-08-06")
VARS = ["REF", "O05", "O10", "O15", "TS", "ES", "PM", "F", "Q"]
UNITE5 = {"exces_m1": 5}          # clôtures M5 reconstruites pour l'essoufflement de exces_m1


def sens_bt(d):
    """Sens de bt_or (clôture M5 contre EMA 576 M5) à l'heure de chaque bougie de d (dernière M5 close)."""
    m5 = G.charge_tf("xau_m5_90k", DEBUT - pd.Timedelta(days=10))
    s = np.sign(m5.cloture - m5.cloture.ewm(span=576, min_periods=576).mean())
    s.index = s.index + pd.Timedelta(minutes=5)                 # connu à la clôture
    return s.reindex(d.index, method="ffill").fillna(0).values


def force(d, regle, k):
    c = d["cloture"]
    if regle == "elan":
        r = np.log(c) - np.log(c.shift(k)); return (r.abs() / r.rolling(100).std().shift(1)).values
    if regle == "cassure":
        ha, ba = d["haut"].shift(1).rolling(k).max(), d["bas"].shift(1).rolling(k).min()
        return (np.maximum(c - ha, ba - c) / G.atr_jour(d)).values
    if regle in ("exces_suit", "exces_contre"):
        r = np.log(c).diff(); return (r / r.rolling(100).std().shift(1)).abs().values
    m, e = c.shift(1).rolling(20).mean(), c.shift(1).rolling(20).std()
    return ((c - m).abs() / (k * e)).values


def joue2(d, sig, h, var, retour=False, mult=1.0, unite=1, sens=None, qual=None):
    """banc_lotg.joue généralisé. Rend (t signal, s, g en $ à 0,01 lot x taille, taille)."""
    if var in ("REF", "F", "Q"):
        if var == "F":
            contre = retour or sig is None
            sig = np.where(sig * sens > 0, sig, 0.0)
        T = G.joue(d, sig, h, None, retour=retour, mult=mult)
        T["taille"] = 1.0
        if var == "Q":
            pos = d.index.get_indexer(T.t); q = qual[pos]; tl = []
            hist = []
            for v in q:
                tl.append(2.0 if len(hist) >= 20 and v == v and v > np.median(hist[-200:]) else 1.0)
                if v == v:
                    hist.append(v)
            T["taille"] = tl; T["g"] = T.g * T.taille
        return T
    o, hi, lo, c = (d[x].values for x in ("ouverture", "haut", "bas", "cloture")); sp = d["sp"].values * mult
    atr = G.atr_jour(d); idx = d.index; jour = idx.floor("D")
    hmax = (4 * h) if var != "PM" else h
    out, i, n = [], 0, len(c)
    while i < n - hmax - 1:
        s = sig[i]
        if not s or not atr[i] == atr[i]:
            i += 1; continue
        A = atr[i]; e = i + 1; ent = o[e] + (sp[e] if s > 0 else 0.0)
        stop = ent - s * A if var != "TS" else ent - s * 0.5 * A
        obj = ent + s * {"O05": 0.5, "O10": 1.0, "O15": 1.5}[var] * A if var in ("O05", "O10", "O15") else None
        if retour:
            ext = hi[i - 1:i + 1].max() + 0.5 if s < 0 else lo[i - 1:i + 1].min() - 0.5
            stop = max(stop, ext) if s > 0 else min(stop, ext)
        best = ent if s > 0 else ent
        x, prix = min(e + hmax - 1, n - 1), None
        for j in range(e, min(e + hmax, n)):
            if (lo[j] <= stop) if s > 0 else (hi[j] + sp[j] >= stop):
                x, prix = j, stop; break
            if obj is not None and ((hi[j] >= obj) if s > 0 else (lo[j] + sp[j] <= obj)):
                x, prix = j, obj; break
            best = max(best, hi[j]) if s > 0 else min(best, lo[j])
            if var == "TS":
                ns = best - s * 0.5 * A; stop = max(stop, ns) if s > 0 else min(stop, ns)
            if var == "PM" and s * (best - ent) >= 0.5 * A:
                stop = max(stop, ent) if s > 0 else min(stop, ent)
            if var == "ES" and j > e:
                fin_u = (unite == 1) or ((idx[j].minute % 5) == 4)
                if fin_u:
                    prev = c[j - unite] if j - unite >= 0 else c[j - 1]
                    if s * (c[j] - prev) < 0:
                        x = j; break
        if prix is None:
            prix = c[x] if s > 0 else c[x] + sp[x]
        out.append((idx[i], s, s * (prix - ent) if s > 0 else (ent - prix)))
        i = x
    T = pd.DataFrame(out, columns=["t", "s", "g"]); T["taille"] = 1.0
    return T


def regle(nom, var, mult=1.0):
    fic, rg, ks, hs, ref = G.REGLES[nom]
    d = G.charge_tf(fic, DEBUT)
    sig = G.signal(d, rg, ref[0])
    sens = sens_bt(d) if var == "F" else None
    qual = force(d, rg, ref[0]) if var == "Q" else None
    T = joue2(d, sig, ref[1], var, retour=(rg == "retour"), mult=mult, unite=UNITE5.get(nom, 1), sens=sens, qual=qual)
    T["regle"] = nom; T["tt"] = ((T.t - pd.Timestamp("1970-01-01")).dt.total_seconds()).astype(int)
    return T


def etude(n_plac=2000, n_mc=2000):
    t0 = time.time()
    d5, k = G.jeu_m5(); k.pop("bars_h")
    P1, _ = M.simule(d5, **k)
    C0 = LL.courtes([])
    sem0, w00 = M.par_semaine(P1, C0); B = M.tirages(len(sem0), n_mc)
    base = M.mc_par(sem0, P1, B); a0, f0 = base.arret.values.astype(float), base.final.values
    pr = lambda T: T[T.t <= FIN]; rs = lambda T: T[T.t >= R0]
    L = []
    for nom in G.REGLES:
        ref1, ref2 = regle(nom, "REF"), regle(nom, "REF", 2.0)
        for v in VARS[1:]:
            T1, T2 = regle(nom, v), regle(nom, v, 2.0)
            row = dict(regle=nom, variante=v, trades=len(pr(T1)), total=pr(T1).g.sum(), ref=pr(ref1).g.sum(),
                       res=rs(T1).g.sum(), res_ref=rs(ref1).g.sum(), x2=pr(T2).g.sum(), x2_ref=pr(ref2).g.sum())
            obs = row["total"] - row["ref"]
            if v in ("F", "Q"):
                g = pr(ref1).g.values; m = len(g)
                if v == "F":
                    kq = len(pr(T1)); st = [g[rng.choice(m, kq, replace=False)].sum() - g.sum() for _ in range(n_plac)]
                else:
                    kq = int((pr(T1).taille > 1).sum()); st = [g[rng.choice(m, kq, replace=False)].sum() for _ in range(n_plac)]
            else:
                mm = pr(ref1).merge(pr(T1), on="t", suffixes=("_r", "_v")); dif = (mm.g_v - mm.g_r).values
                obs_p = dif.sum(); st = [(dif * rng.choice((-1, 1), len(dif))).sum() for _ in range(n_plac)]
                row["apparies"] = len(dif); obs = obs_p
            row["placebo_p"] = float((np.array(st) >= obs).mean())
            Cx = pd.concat([C0[C0.regle != nom][["t", "g"]], pd.DataFrame({"t": T1.tt.values, "g": T1.g.values})], ignore_index=True)
            sem, w0 = M.par_semaine(P1, Cx)
            sem = [sem[w - w0] if 0 <= w - w0 < len(sem) else [] for w in range(w00, w00 + len(sem0))]   # mêmes semaines
            R = M.mc_par(sem, P1, B); a = R.arret.values.astype(float)
            row["p_arret"] = a.mean(); row["d_arret"] = "%+.3f [%.3f ; %.3f]" % M.ic(a0, a, np.mean)
            row["d_med"] = "%+.0f [%.0f ; %.0f]" % M.ic(f0, R.final.values, np.median)
            L.append(row)
        print(nom, "%.0f s" % (time.time() - t0), flush=True)
    T = pd.DataFrame(L)
    T["p_holm"] = H.holm(T.placebo_p.values)
    ok = (T.total > T.ref) & (T.x2 > T.x2_ref) & (T.res > T.res_ref) & (T.p_arret <= a0.mean() + 0.01)
    T["verdict"] = np.where(ok & (T.p_holm < 0.05), "tient", np.where(ok & (T.placebo_p < 0.05), "presque", "non"))
    T.attrs["arret_v4"] = a0.mean()
    return T, a0.mean()


if __name__ == "__main__":
    pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40)
    T, a0 = etude(); T.to_csv(os.path.join(ICI, "donnees", "lotn_courtes.csv"), index=False)
    print("arrêt v4 + règles telles quelles : %.3f" % a0)
    print(T.round(3).to_string(index=False))
