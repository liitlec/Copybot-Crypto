"""Banc DIX : « que faut-il pour viser +10 % par mois, et a quel prix ? » avec les pieces DEJA mesurees au labo.
Le labo calcule seulement : AUCUN ordre n'est passe (compte demo / compte cent simule).
Pieces et outils REUTILISES par import (rien n'est re-ecrit) : banc_plan_cent (series jointes 08/2022-11/2026 de bt_or H1,
repli_ind, rebond_nas, rebond_sp ; parite de risque ; scenarios ; courbe a mise hebdomadaire ; calibre ; creux ; lots),
banc_retrait (tirages bootstrap stationnaire blocs 20 j sur 24 mois, graine 20261118 ; regle b de retrait).
Compte cent de 100 EUR ou 500 EUR, reinvestissement (mise en % du compte recalculee chaque semaine), regle b : retrait
de la mise de depart a la fin du 1er mois ou le compte vaut >= 2 fois la mise (puis rien). Tout est proportionnel
(compte en unites de mise) sauf l'arrondi des lots, donne a part pour 100 et 500 EUR.
MONTAGES (fixes d'avance ; memes tirages pour tous) :
 M0  melange (bt_or + repli_ind + rebond_nas + rebond_sp, parite de risque) au plan -30 % (L de banc_plan_cent).
 M1m le meme melange, L tel que la MEDIANE du rendement mensuel compose sur 12 mois (= mediane du compte a 12 mois
     ^(1/12) - 1) vaille 10 % en scenario MESURE (bissection, branche montante de la courbe de croissance).
 M1p idem en scenario PRUDENT ; si 10 % n'est pas atteignable : L du sommet de la croissance mediane prudente (Kelly).
 M2  coeur + poche pari : 80 % au plan -30 % (M0) + 20 % dans la poche (repli des 4 indices, chaque position a 100 fois
     la poche comme pari_court / banc_pc_rebonds, soit 400 x la serie repli_ind qui est a notionnel 1/4 par indice ;
     poche marquee chaque jour, arret de la poche a x3 ou sous 20 % de sa dotation ; dans les deux cas ce qui reste
     revient au coeur ; la poche est redotee a 20 % du compte total au debut du mois suivant seulement). Variante 90/10.
 M3  melange au plan -50 % (L de banc_plan_cent).
 M4  bt_or seul au L qui donne une mediane de 10 %/mois en MESURE (ou son sommet s'il n'y arrive pas).
ARRET AUTOMATIQUE : seuil = quantile 95 % de la pire baisse a 12 mois du scenario PRUDENT du montage (sans arret),
plafonne a 60 % (M0 : ~34 %, celui de banc_plan_cent) ; mesure sur l'indice de performance (retraits neutralises) ;
apres l'arret le compte reste en especes (« ruine pratique »). Chiffres AVEC et SANS arret.
MESURES (5000 tirages, 12 et 24 mois ; mois = 1/12 d'annee de 261 jours ouvres) : mediane des mois (tous mois x
tirages, comme banc_plan_cent : c'est le CONTROLE M0 +2,8 % mesure / +0,3 % prudent) ; mediane composee ; chance
qu'un mois >= +10 % ; chance que la moyenne geometrique sur l'horizon >= 10 %/mois (x3,14 en 12 mois) ; % mois < 0 ;
pire baisse mediane et q90 ; ruine = compte + retraits < 20 % de la mise (a un moment) ; arret declenche ; fin sous la
mise (retraits comptes) ; mise retiree.
Rejeu historique reel 08/2022-11/2026 (UNE trajectoire) ; walk-forward de M1m (poids + L appris par MC mesure sur une
moitie, rejoues sur l'autre) ; M1m et M4 (L appris sur tout) rejoues sur la 1re moitie seule (bt_or y fait ~ -6 R).
Controle de realisme : notionnel maximal / capital (toutes pieces ouvertes ensemble) contre levier 1:500 du courtier
(alerte si > 200 x), lots cent voulus contre lot minimum 0,01 lot cent (100 et 500 EUR).
LIMITES : poche marquee en cloture journaliere (pas de liquidation intrajour : optimiste pour la poche) ; transferts de
la poche au coeur appliques comme une remise a l'echelle du coeur dans la semaine ; meme passe que banc_plan_cent.
Ecrit donnees/dix.csv. Usage : python3 banc_dix.py"""
import os, time, contextlib, io, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_plan_cent as PC
    import banc_retrait as BRT

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
J12, J24 = PC.JOURS, 2 * PC.JOURS
FINS = np.round(np.arange(1, 25) * PC.JOURS / 12).astype(int) - 1      # fins de mois (indices de jour)
CIBLE = 1.10 ** 12                                                       # x3,138 en 12 mois
SC = {"mesure": 0.0, "prudent": 0.5, "nul": 1.0}
POCHE_L = 400.0                                                          # 100 x la poche par indice, 4 indices
CAPS = PC.CAPS


# ------------------------------------------------------------------ outils propres a ce banc
def med12(P, L):
    return np.median(PC.courbe(P[:, :J12], L)[:, -1])


def sommet(P):
    """L qui maximise la mediane du compte a 12 mois (grille log puis affinage)."""
    g = np.geomspace(0.05, 3000, 60)
    v = [med12(P, L) for L in g]
    i = int(np.argmax(v))
    lo, hi = g[max(0, i - 1)], g[min(len(g) - 1, i + 1)]
    for _ in range(25):
        a, b = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        if med12(P, a) < med12(P, b):
            lo = a
        else:
            hi = b
    L = 0.5 * (lo + hi)
    return L, med12(P, L)


def vise(P, cible=CIBLE):
    """L (branche montante) tel que mediane du compte a 12 mois = cible ; sinon (L du sommet, False)."""
    Lk, mk = sommet(P)
    if mk < cible:
        return Lk, False, Lk, mk
    lo, hi = 0.0, Lk
    for _ in range(40):
        m = 0.5 * (lo + hi)
        if med12(P, m) < cible:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi), True, Lk, mk


def retraits(V, fins):
    """Regle b sur un indice de performance V : rend compte W et retraits cumules R (memes dimensions)."""
    n, T = V.shape
    s = np.ones(n); R = np.zeros((n, T)); fait = np.zeros(n, bool); W = V.copy()
    for t in fins:
        if t >= T:
            break
        A = V[:, t] * s
        x = (~fait) & (A >= 2)
        s = np.where(x, s * (A - 1) / np.where(x, A, 1), s)
        fait |= x
        R[:, t:] += x[:, None]
        W[:, t + 1:] = V[:, t + 1:] * s[:, None]
        W[:, t] = np.where(x, A - 1, W[:, t])
    return W, R


def m2(Pc, Pp, L, f, fins, sem=None):
    """Coeur (Pc a levier L, mise hebdo) + poche (rendement journalier Pp, deja a son levier). Rend V, W, R."""
    n, T = Pc.shape
    Vc = PC.courbe(Pc, L, sem)
    Vc = np.concatenate([np.ones((n, 1)), Vc], 1)
    fins = set(int(x) for x in fins)
    C = np.full(n, 1 - f); K = np.full(n, f); K0 = K.copy(); act = np.ones(n, bool)
    Rc = np.zeros(n); fait = np.zeros(n, bool); v = np.ones(n)
    V, W, R = (np.empty((n, T)) for _ in range(3))
    for t in range(T):
        avant = C + K
        r = np.where(Vc[:, t] > 0, Vc[:, t + 1] / np.where(Vc[:, t] > 0, Vc[:, t], 1), 1.0)
        C = C * r
        K = np.where(act, np.maximum(K * (1 + Pp[:, t]), 0.0), K)
        sort = act & ((K >= 3 * K0) | (K < 0.2 * K0))
        C = C + np.where(sort, K, 0); K = np.where(sort, 0, K); act &= ~sort
        v = v * np.where(avant > 0, (C + K) / np.where(avant > 0, avant, 1), 1.0)
        if t in fins:
            tot = C + K
            x = (~fait) & (tot >= 2)
            C = C - x; fait |= x; Rc = Rc + x
            neg = C < 0; K = np.where(neg, K + C, K); C = np.where(neg, 0, C)
            re = ~act & ((C + K) > 0)
            nk = f * (C + K)
            K = np.where(re, nk, K); C = np.where(re, C - nk, C); K0 = np.where(re, nk, K0); act |= re
        V[:, t] = v; W[:, t] = C + K; R[:, t] = Rc
    return V, W, R


def arrete(V, W, R, seuil):
    """Gele tout au 1er jour ou la baisse depuis le plus haut (depart 1 compris) atteint le seuil."""
    pic = np.maximum.accumulate(np.concatenate([np.ones((V.shape[0], 1)), V], 1), 1)[:, 1:]
    hit = V / pic - 1 <= -seuil
    tau = np.where(hit.any(1), hit.argmax(1), V.shape[1])
    T = np.arange(V.shape[1])[None, :]
    k = np.minimum(np.where(T >= tau[:, None], tau[:, None], T), V.shape[1] - 1)
    g = lambda Z: np.take_along_axis(Z, k, 1)
    return g(V), g(W), g(R), tau


def mesures(V, W, R, tau, h):
    T = FINS[h - 1] + 1
    b = FINS[:h]
    Mv = V[:, b] / np.concatenate([np.ones((V.shape[0], 1)), V[:, b[:-1]]], 1) - 1
    dd = -PC.creux(V[:, :T])
    tot = W[:, :T] + R[:, :T]
    geo = V[:, T - 1] ** (1 / h) - 1
    return dict(med_mois=np.median(Mv), med_compose=np.median(V[:, T - 1]) ** (1 / h) - 1, moy_mois=Mv.mean(),
                p_mois_10=(Mv >= 0.10).mean(), p_geo_10=(geo >= 0.10 - 1e-12).mean(), p_mois_neg=(Mv < 0).mean(),
                dd_med=np.median(dd), dd_q90=np.quantile(dd, 0.9), p_ruine=(tot.min(1) < 0.2).mean(),
                p_arret=(tau < T).mean(), p_sous_mise=(tot[:, -1] < 1).mean(), p_mise_retiree=(R[:, T - 1] >= 1).mean(),
                fin_med=np.median(tot[:, -1]))


def notionnel(cols, w, L, M):
    """Notionnel maximal / capital, toutes pieces ouvertes ensemble (bt_or : 3 positions)."""
    n = 0.0
    for c, wi in zip(cols, w):
        n += L * wi * 0.01 * 3 * M["xau"] / (0.6667 * M["atr"]) if c == "bt_or" else L * wi
    return n


def lots_poche(fp, cap, M):
    usd = fp * cap * M["eur"]
    return {"poche_" + k: 100 * usd / M[k] * 100 for k in ("nas", "sp", "dj", "us2000")}


# ------------------------------------------------------------------ principal
if __name__ == "__main__":
    X, gh = PC.series()
    Mk = PC.marche()
    cols = list(X.columns); w = PC.parite(X[cols])
    print("Donnees %s -> %s (%d jours) ; bt_or %+.0f R ; poids parite %s" % (
        X.index[0].date(), X.index[-1].date(), len(X), gh.sum(), np.round(w, 3)))
    Xa = {s: PC.ampute(X[cols], a) for s, a in SC.items()}
    I12 = PC.tirages(len(X))
    L30 = PC.calibre((Xa["prudent"].values @ w)[I12], 0.30)
    L50 = PC.calibre((Xa["prudent"].values @ w)[I12], 0.50)
    I = BRT.tirages(len(X), J24)                                       # memes tirages 24 mois pour tous les montages
    Pm = {s: (Xa[s].values @ w)[I] for s in SC}
    Po = {s: Xa[s]["bt_or"].values[I] for s in SC}
    Pp = {s: POCHE_L * Xa[s]["repli_ind"].values[I] for s in SC}
    print("L plan -30 %% = %.3f (controle 7,50) ; L plan -50 %% = %.3f (controle 13,93) ; Kelly scalaire mesure %.1f, prudent %.1f"
          % (L30, L50, PC.kelly(Xa["mesure"].values @ w), PC.kelly(Xa["prudent"].values @ w)))

    L1m, ok1m, Lkm, mkm = vise(Pm["mesure"])
    L1p, ok1p, Lkp, mkp = vise(Pm["prudent"])
    L4, ok4, Lk4, mk4 = vise(Po["mesure"])
    print("Melange, sommet de croissance mediane 12 mois : mesure L %.1f -> x%.2f (%.1f %%/mois) ; prudent L %.1f -> x%.2f (%.1f %%/mois)"
          % (Lkm, mkm, 100 * (mkm ** (1 / 12) - 1), Lkp, mkp, 100 * (mkp ** (1 / 12) - 1)))
    print("M1m : L %.2f (%s) ; M1p : L %.2f (%s) ; M4 bt_or seul : L %.3f (%s ; sommet L %.2f -> %.1f %%/mois)" % (
        L1m, "atteint" if ok1m else "NON atteint, sommet", L1p, "atteint" if ok1p else "NON atteint -> sommet prudent",
        L4, "atteint" if ok4 else "NON atteint, sommet", Lk4, 100 * (mk4 ** (1 / 12) - 1)))

    MONT = {"M0 plan-30": ("mel", L30), "M1m med10 mesure": ("mel", L1m),
            ("M1p med10 prudent" if ok1p else "M1p sommet prudent"): ("mel", L1p),
            "M2 80/20 poche": ("m2", 0.20), "M2 90/10 poche": ("m2", 0.10), "M3 plan-50": ("mel", L50),
            ("M4 bt_or med10" if ok4 else "M4 bt_or sommet"): ("or", L4)}

    def simule(typ, par, s):
        if typ == "m2":
            return m2(Pm[s], Pp[s], L30, par, FINS)
        V = PC.courbe(Pm[s] if typ == "mel" else Po[s], par)
        W, R = retraits(V, FINS)
        return V, W, R

    rows, seuils = [], {}
    nulle = np.full(PC.NPAR, J24)
    print("\n=== Monte-Carlo %d tirages ; AVEC arret (SANS arret entre crochets pour ruine / pire baisse q90)" % PC.NPAR)
    print("%-20s %7s %-7s %3s | %6s %6s %6s %6s %5s | %6s %6s | %5s %5s %6s %6s %6s | %6s %5s" % (
        "montage", "L", "scen.", "h", "medM", "medC", "PM10", "Pg10", "M<0", "ddmed", "ddq90", "ruin", "arret",
        "[ruin]", "[dd90]", "<mise", "retir", "[medC]"))
    for nom, (typ, par) in MONT.items():
        sim = {s: simule(typ, par, s) for s in SC}
        q = np.quantile(-PC.creux(sim["prudent"][0][:, :J12]), 0.95)
        seuil = 0.34 if nom.startswith("M0") else min(0.60, q)
        seuils[nom] = (seuil, q)
        for s in SC:
            V, W, R = sim[s]
            Va, Wa, Ra, tau = arrete(V, W, R, seuil)
            for h in (12, 24):
                a = mesures(Va, Wa, Ra, tau, h); z = mesures(V, W, R, nulle, h)
                Lr = par if typ != "m2" else L30
                print("%-20s %7.2f %-7s %3d | %+5.1f%% %+5.1f%% %5.1f%% %5.1f%% %4.0f%% | %5.1f%% %5.1f%% | %4.1f%% %4.1f%% %5.1f%% %5.1f%% %5.1f%% | %5.1f%% %+5.1f%%" % (
                    nom, Lr, s, h, 100 * a["med_mois"], 100 * a["med_compose"], 100 * a["p_mois_10"], 100 * a["p_geo_10"],
                    100 * a["p_mois_neg"], 100 * a["dd_med"], 100 * a["dd_q90"], 100 * a["p_ruine"], 100 * a["p_arret"],
                    100 * z["p_ruine"], 100 * z["dd_q90"], 100 * a["p_sous_mise"], 100 * a["p_mise_retiree"], 100 * z["med_compose"]))
                for cap in CAPS:
                    d = dict(montage=nom, scenario=s, horizon_mois=h, capital_eur=cap, L=Lr,
                             part_poche=par if typ == "m2" else 0.0, seuil_arret=seuil, q95_baisse_prudent=q, **a)
                    d.update({k + "_sans_arret": v for k, v in z.items()})
                    rows.append(d)

    print("\nSeuils d'arret (q95 pire baisse 12 mois prudent, plafond 60 %) : " + " ; ".join(
        "%s %.0f %% (q95 %.0f %%)" % (k, 100 * a, 100 * b) for k, (a, b) in seuils.items()))

    # ---------------------------------------------------------- realisme : marge et lots
    print("\n=== Marge et lots (notionnel max / capital, toutes pieces ouvertes ; courtier 1:500 ; alerte > 200 x)")
    real = {}
    for nom, (typ, par) in MONT.items():
        if typ == "m2":
            nc = notionnel(cols, w, L30, Mk) * (1 - par); npk = POCHE_L * par
            n_tot, extra = nc + npk, " (coeur %.0f x + poche %.0f x du compte ; poche seule = %.0f x la poche)" % (nc, npk, POCHE_L)
        elif typ == "or":
            n_tot, extra = notionnel(["bt_or"], [1.0], par, Mk), " (risque %.1f %% du compte par position)" % par
        else:
            n_tot, extra = notionnel(cols, w, par, Mk), ""
        lt = {}
        for cap in CAPS:
            if typ == "m2":
                D = {k: v * (1 - par) for k, v in PC.lots(cols, w, L30, cap, Mk).items()}; D.update(lots_poche(par, cap, Mk))
            elif typ == "or":
                D = PC.lots(["bt_or"], [1.0], par, cap, Mk)
            else:
                D = PC.lots(cols, w, par, cap, Mk)
            lt[cap] = PC.texte_lots(D)
        real[nom] = (n_tot, lt)
        print("  %-20s notionnel max %6.1f x le capital, marge 1:500 = %5.1f %% du compte%s%s" % (
            nom, n_tot, 100 * n_tot / 500, " ALERTE > 200 x" if n_tot > 200 else "", extra))
        for cap in CAPS:
            print("      %3.0f EUR : %s (ecart d'arrondi max %.0f %%)" % (cap, lt[cap][0], 100 * lt[cap][1]))
    for d in rows:
        n_tot, lt = real[d["montage"]]
        d.update(notionnel_max_x=n_tot, marge_1_500_pct=n_tot / 500, alerte_200x=n_tot > 200,
                 lots_cent=lt[d["capital_eur"]][0], ecart_arrondi_max=lt[d["capital_eur"]][1])

    # ---------------------------------------------------------- rejeu historique (une seule trajectoire)
    print("\n=== Rejeu historique reel %s -> %s (UNE seule trajectoire, scenario mesure ; poids parite sur tout)" % (
        X.index[0].date(), X.index[-1].date()))
    sem = pd.factorize(X.index.to_period("W-FRI"))[0]
    pm = pd.Series(X[cols].values @ w, index=X.index); po = X["bt_or"]
    fin_h = np.where(X.index.to_period("M") != np.roll(X.index.to_period("M"), -1))[0]

    def hist(nom, typ, par, H=None):
        idx = X.index if H is None else H
        if typ == "m2":
            V = m2((pm.loc[idx].values)[None, :], (POCHE_L * X["repli_ind"].loc[idx].values)[None, :], L30, par,
                   np.where(idx.to_period("M") != np.roll(idx.to_period("M"), -1))[0],
                   pd.factorize(idx.to_period("W-FRI"))[0])[0][0]
            E = pd.Series(V, index=idx)
        else:
            E, _ = PC.rejeu((pm if typ == "mel" else po).loc[idx], par)
        m = E.groupby(E.index.to_period("M")).last(); m = m / m.shift(1).fillna(1.0) - 1
        dd = E / np.maximum(E.cummax(), 1.0) - 1
        s = seuils[nom][0]
        t = dd.index[dd <= -s]
        return dict(moy=m.mean(), med=m.median(), n10=int((m >= 0.10).sum()), nneg=int((m < 0).sum()), nm=len(m),
                    dd=-dd.min(), arret=str(t[0].date()) if len(t) else "non", fin=E.iloc[-1],
                    fin_arret=E.loc[t[0]] if len(t) else E.iloc[-1])

    print("  %-20s %7s | %6s %6s %6s %6s | %6s %-11s | %8s %8s" % ("montage", "L", "moy/m", "med/m", "m>=10", "m<0", "pire", "arret", "fin x", "fin arr."))
    for nom, (typ, par) in MONT.items():
        r = hist(nom, typ, par)
        print("  %-20s %7.2f | %+5.1f%% %+5.1f%% %3d/%-2d %3d/%-2d | %5.1f%% %-11s | %8.2f %8.2f" % (
            nom, par if typ != "m2" else L30, 100 * r["moy"], 100 * r["med"], r["n10"], r["nm"], r["nneg"], r["nm"],
            100 * r["dd"], r["arret"], r["fin"], r["fin_arret"]))
        rows.append(dict(montage=nom, scenario="historique 08/2022-11/2026", capital_eur=np.nan, L=par if typ != "m2" else L30,
                         moy_mois=r["moy"], med_mois=r["med"], n_mois_10=r["n10"], n_mois_neg=r["nneg"], n_mois=r["nm"],
                         dd_hist=r["dd"], arret_hist=r["arret"], fin_hist=r["fin"], fin_hist_arret=r["fin_arret"],
                         seuil_arret=seuils[nom][0]))

    H1, H2 = X.index[X.index < PC.COUPE], X.index[X.index >= PC.COUPE]
    print("\n  Rappel : bt_or 1re moitie %+.0f R, 2de moitie %+.0f R (1 R = 1 %% a mise unitaire)" % (
        100 * X.bt_or.loc[H1].sum(), 100 * X.bt_or.loc[H2].sum()))
    for nom, (typ, par) in MONT.items():
        if nom[:2] not in ("M1", "M4") or "prudent" in nom:
            continue
        r = hist(nom, typ, par, H1)
        print("  %-20s L %6.2f appris sur TOUT, rejoue sur la 1re moitie seule (08/2022-09/2024) : moy %+.1f %%/mois, med %+.1f %%, "
              "mois >= 10 %% %d/%d, mois < 0 %d/%d, pire baisse %.1f %%, arret %s, fin x%.2f (x%.2f avec arret)" % (
                  nom, par, 100 * r["moy"], 100 * r["med"], r["n10"], r["nm"], r["nneg"], r["nm"], 100 * r["dd"], r["arret"],
                  r["fin"], r["fin_arret"]))
        rows.append(dict(montage=nom, scenario="1re moitie seule (L appris sur tout)", L=par, moy_mois=r["moy"], med_mois=r["med"],
                         n_mois_10=r["n10"], n_mois_neg=r["nneg"], n_mois=r["nm"], dd_hist=r["dd"], arret_hist=r["arret"],
                         fin_hist=r["fin"], fin_hist_arret=r["fin_arret"]))

    # ---------------------------------------------------------- walk-forward M1m
    print("\n=== Walk-forward M1m (poids parite + L 'mediane 10 %/mois mesure' appris par MC sur une moitie, rejoues sur l'autre)")
    for sens, A, B in (("1re->2de", H1, H2), ("2de->1re", H2, H1)):
        wa = PC.parite(X.loc[A, cols])
        Pa = (X.loc[A, cols].values @ wa)[PC.tirages(len(A))]
        La, oka, Lka, mka = vise(Pa)
        E, m = PC.rejeu(pd.Series(X.loc[B, cols].values @ wa, index=B), La)
        dd = -(E / np.maximum(E.cummax(), 1) - 1).min()
        s = min(0.60, np.quantile(-PC.creux(PC.courbe((PC.ampute(X.loc[A, cols], 0.5).values @ wa)[PC.tirages(len(A))], La)), 0.95))
        dser = E / np.maximum(E.cummax(), 1.0) - 1; t = dser.index[dser <= -s]
        print("  %-9s L appris %.2f (%s ; sommet appris L %.1f -> %.1f %%/mois) | rejoue : moy %+.1f %%/mois, med %+.1f %%, "
              "mois >= 10 %% %d/%d, mois < 0 %d/%d, pire baisse %.1f %%, arret (%.0f %%) %s, fin x%.2f" % (
                  sens, La, "atteint" if oka else "non atteint", Lka, 100 * (mka ** (1 / 12) - 1), 100 * m.mean(), 100 * m.median(),
                  (m >= 0.10).sum(), len(m), (m < 0).sum(), len(m), 100 * dd, 100 * s, t[0].date() if len(t) else "non", E.iloc[-1]))
        rows.append(dict(montage="M1m med10 mesure", scenario="walk-forward " + sens, L=La, moy_mois=m.mean(), med_mois=m.median(),
                         n_mois_10=int((m >= 0.10).sum()), n_mois_neg=int((m < 0).sum()), n_mois=len(m), dd_hist=dd,
                         arret_hist=str(t[0].date()) if len(t) else "non", fin_hist=E.iloc[-1], seuil_arret=s))

    pd.DataFrame(rows).to_csv(os.path.join(ICI, "donnees", "dix.csv"), index=False, float_format="%.5g")
    print("\nEcrit donnees/dix.csv (%d lignes). Duree %.0f s." % (len(rows), time.time() - T00))
