"""Banc PC : PLAN DE MISE pour un compte « cent » (memes conditions que la demo, tout divise par 100 :
1 lot cent = 0,01 lot standard). Le labo calcule seulement : AUCUN ordre n'est passe.
Melange fixe d'avance : bt_or (panier de tendance sur l'or, H1, gain latent, 1 R = 1 % du capital a mise unitaire)
+ repli_ind + rebond_nas + rebond_sp (pieces d'indices de banc_mix / banc_portefeuille, notionnel 1, couts inclus),
poids relatifs en parite de risque (1 / vol journaliere, apprise sur l'apprentissage) ; et bt_or seul.
Un seul parametre : le levier global L sur le portefeuille normalise (somme des poids = 1), exprime aussi en fraction
du Kelly (Kelly scalaire k = moyenne / variance des rendements journaliers). Mise recalculee chaque SEMAINE en % du
compte (reinvestissement compose ; dans la semaine, tailles fixes).
Scenarios : mesure ; prudent = avantage / 2 (chaque piece perd la moitie de sa moyenne, retiree sur ses jours actifs) ;
nul = toute la moyenne retiree (risque nu).
Monte-Carlo : bootstrap stationnaire (blocs moyens 20 jours ouvres) des series JOINTES, 12 mois = 261 jours ouvres,
5000 tirages, semaines de 5 jours, mois = 1/12 de l'annee. Pour chaque cible de pire baisse (-15/-30/-50 %) : L tel que
90 % des trajectoires du scenario PRUDENT aient une pire baisse moins profonde que la cible (bissection, memes tirages).
Seuil d'arret = quantile 95 % de la pire baisse en 12 mois du scenario prudent ; compte des franchissements dans
l'historique rejoue (episodes : on re-arme quand le compte refait un plus haut).
Walk-forward : poids et L appris sur 08/2022-09/2024 (MC sur cette moitie), rejoues sur 10/2024-11/2026, et l'inverse.
HYPOTHESES DE LOT (ecrites ici, a verifier chez le courtier cent) :
  - lot cent = 0,01 lot standard ; lot minimum ET pas de lot du compte cent = 0,01 lot cent (= 0,0001 lot standard),
    pour l'or comme pour les indices (sur la demo les indices ont un lot minimum de 0,1 standard : si le compte cent
    garde « 0,1 » pour les indices, multiplier le lot minimum indices par 10 -> cas indique a part) ;
  - or : 1 lot standard = 100 onces (bt_or.py : 0,01 lot = 1 once) ; 1 R par position = 0,6667 x ATR jour (20 j) x onces ;
  - indices : 1 lot standard = 1 unite d'indice (essais_robot / banc_pari : taille_contrat 1, 1 $ par point par lot) ;
    repli_ind = 4 indices (NAS100, SP500, DJ30, US2000) a notionnel 1/4 chacun du poids ; lot par trade = notionnel / prix ;
  - prix et ATR = dernieres bougies D1 du courtier (mt5/donnees) ; compte en euros, EURUSD = derniere cloture M5.
Ecrit donnees/plan_cent.csv (une ligne par portefeuille x cible x capital x scenario). Usage : python3 banc_plan_cent.py"""
import os, time, contextlib, io, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_bt_regulier as BR
    import banc_jumeau as BJ
    import banc_portefeuille as BP
    import banc_mix as BM

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
DON = os.path.join(ICI, "mt5", "donnees")
NPAR, JOURS, BLOC, SEM = 5000, 261, 20.0, 5
CIBLES = (0.15, 0.30, 0.50)
CAPS = (100.0, 500.0)
LOT_MIN_CENT, PAS_CENT = 0.01, 0.01
COUPE = pd.Timestamp("2024-10-01")
rng = np.random.default_rng(20261118)
pd.set_option("display.width", 220)


# ------------------------------------------------------------------ donnees
def series():
    dh = BR.charge("xau_h1_50k"); dh = dh[dh.heure >= BM.DEB.timestamp()].reset_index(drop=True)
    xh, _, gh = BM.bt_or_jour(dh, dict(span=48, heures=BJ.H_H1, debut=60))
    with contextlib.redirect_stdout(io.StringIO()):
        D = BP.donnees()
    idx = D["SP"].index[D["SP"].index >= "1990-01-01"]
    rep = {n: BP.piece_repli(D, n)[0].reindex(idx).fillna(0) for n in ("SP", "NAS", "DJ", "RUT")}
    rnas = BP.piece_rebond(D)[0].reindex(idx).fillna(0)
    rsp = BP.pieces_externes(idx)["grande_journee:gj_fige:sp"]
    B = pd.bdate_range(BM.DEB, min(xh.index[-1], idx[-1]))
    X = pd.DataFrame({"bt_or": BM.vers_ouvres(xh / 100, B),
                      "repli_ind": sum(BM.vers_ouvres(rep[n], B) for n in rep) / 4,
                      "rebond_nas": BM.vers_ouvres(rnas, B), "rebond_sp": BM.vers_ouvres(rsp, B)})
    return X[X.index >= X.bt_or.ne(0).idxmax()], gh


def ampute(X, part):
    """Retire part x moyenne de chaque piece, repartie sur ses jours actifs (les jours sans position restent a 0)."""
    Y = X.copy()
    for c in X:
        a = X[c] != 0
        if a.any():
            Y.loc[a, c] -= part * X[c].sum() / a.sum()
    return Y


def parite(X):
    sd = X.std().values
    w = 1 / sd
    return w / w.sum()


def kelly(p):
    return p.mean() / p.var() if p.var() > 0 else 0.0


# ------------------------------------------------------------------ Monte-Carlo
def tirages(n):
    neuf = rng.random((NPAR, JOURS)) < 1 / BLOC; neuf[:, 0] = True
    deb = np.maximum.accumulate(np.where(neuf, np.arange(JOURS), 0), axis=1)          # jour du dernier debut de bloc
    start = np.take_along_axis(rng.integers(n, size=(NPAR, JOURS)), deb, axis=1)
    return (start + np.arange(JOURS) - deb) % n


def courbe(P, L, sem=None):
    """P : (tirages x jours) rendements journaliers a levier 1 ; reinvestissement par semaine. Rend la courbe E (depart 1)."""
    P = np.atleast_2d(P)
    T = P.shape[1]
    sem = np.arange(T) // SEM if sem is None else sem
    E = np.empty_like(P); e0 = np.ones(P.shape[0]); c = np.zeros(P.shape[0]); prev = sem[0]
    for t in range(T):
        if sem[t] != prev:
            e0 = E[:, t - 1]; c[:] = 0; prev = sem[t]
        c += L * P[:, t]
        E[:, t] = np.maximum(e0 * (1 + c), 0.0)
        c = np.where(E[:, t] <= 0, -1.0, c)
    return E


def creux(E):
    E1 = np.concatenate([np.ones((E.shape[0], 1)), E], 1)
    return (E1 / np.maximum.accumulate(E1, 1) - 1).min(1)


def mensuel(E):
    b = np.round(np.arange(1, 13) * JOURS / 12).astype(int) - 1
    M = E[:, b]
    return M / np.concatenate([np.ones((E.shape[0], 1)), M[:, :-1]], 1) - 1


def calibre(P, cible, q=0.90):
    lo, hi = 0.0, 1.0
    while np.quantile(-creux(courbe(P, hi)), q) < cible and hi < 1e4:
        hi *= 2
    for _ in range(30):
        m = 0.5 * (lo + hi)
        if np.quantile(-creux(courbe(P, m)), q) < cible:
            lo = m
        else:
            hi = m
    return lo


def resume(E):
    M = mensuel(E); dd = creux(E)
    return dict(m_moy=M.mean(), m_med=np.median(M), p_mneg=(M < 0).mean(), p_moitie=(E.min(1) <= 0.5).mean(),
                p_perte=(E[:, -1] < 1).mean(), dd_q90=np.quantile(-dd, 0.9), dd_q95=np.quantile(-dd, 0.95),
                fin_med=np.median(E[:, -1]))


# ------------------------------------------------------------------ historique rejoue
def rejeu(p, L):
    sem = pd.factorize(p.index.to_period("W-FRI"))[0]
    E = pd.Series(courbe(p.values[None, :], L, sem)[0], index=p.index)
    m = E.groupby(E.index.to_period("M")).last()
    m = m / m.shift(1).fillna(1.0) - 1
    return E, m


def touches(E, seuil):
    dd = E / np.maximum(E.cummax(), 1.0) - 1
    n, arme, pic = 0, True, 1.0
    for e in E.values:
        if e >= pic:
            pic, arme = e, True
        elif arme and e / pic - 1 <= -seuil:
            n += 1; arme = False
    return n, -dd.min()


# ------------------------------------------------------------------ lots
def marche():
    d = lambda n: pd.read_csv(os.path.join(DON, n + "_d1_5k.csv.gz"))
    x = d("xau")
    tr = np.maximum(x.haut - x.bas, np.maximum((x.haut - x.cloture.shift(1)).abs(), (x.bas - x.cloture.shift(1)).abs()))
    eur = pd.read_csv(os.path.join(DON, "eur_m5_90k.csv.gz")).cloture.iloc[-1]
    px = {n: d(n).cloture.iloc[-1] for n in ("nas", "sp", "dj", "us2000")}
    return dict(xau=x.cloture.iloc[-1], atr=tr.tail(20).mean(), eur=eur, **px)


def lots(cols, w, L, cap, M):
    """Lots cent voulus (non arrondis) par piece : bt_or = par position, indices = par trade (repli : par indice)."""
    usd = cap * M["eur"]; out = {}
    for c, wi in zip(cols, w):
        if c == "bt_or":
            out["bt_or"] = L * wi * 0.01 * usd / (0.6667 * M["atr"] * 100) * 100
        elif c == "repli_ind":
            out["repli_nas"] = L * wi / 4 * usd / M["nas"] * 100
            out["repli_us2000"] = L * wi / 4 * usd / M["us2000"] * 100
            out["repli_sp"] = L * wi / 4 * usd / M["sp"] * 100
            out["repli_dj"] = L * wi / 4 * usd / M["dj"] * 100
        elif c == "rebond_nas":
            out[c] = L * wi * usd / M["nas"] * 100
        elif c == "rebond_sp":
            out[c] = L * wi * usd / M["sp"] * 100
    return out


def arrondi(v, lmin=LOT_MIN_CENT):
    """Lot reellement passe et ecart relatif (lot minimum impose si v < lmin : on sur-risque)."""
    r = max(lmin, np.round(v / PAS_CENT) * PAS_CENT) if v > 0 else 0.0
    return r, (r / v - 1) if v > 0 else np.nan


def texte_lots(D, lmin=LOT_MIN_CENT):
    s, pire = [], 0.0
    for k, v in D.items():
        r, e = arrondi(v, lmin)
        pire = max(pire, abs(e))
        s.append("%s %.3f->%.2f" % (k, v, r))
    return " ".join(s), pire


# ------------------------------------------------------------------ principal
if __name__ == "__main__":
    X, gh = series()
    M = marche()
    print("Donnees %s -> %s, %d jours ouvres ; bt_or %+.0f R (controle banc_mix ~ +154 R)." % (
        X.index[0].date(), X.index[-1].date(), len(X), gh.sum()))
    print("Marche : or %.0f $, ATR 20 j %.1f $ -> 1 R par position = %.1f $ par lot standard x0,01 (1 once) ; "
          "NAS %.0f, SP %.0f, DJ %.0f, US2000 %.0f ; EURUSD %.4f" % (
              M["xau"], M["atr"], 0.6667 * M["atr"], M["nas"], M["sp"], M["dj"], M["us2000"], M["eur"]))
    JEUX = {"melange": list(X.columns), "bt_or seul": ["bt_or"]}
    SC = {"mesure": 0.0, "prudent": 0.5, "nul": 1.0}
    I = tirages(len(X))
    rows, plans = [], {}

    print("\n=== 1. Kelly (rendements journaliers, k = moyenne / variance, levier sur le portefeuille normalise)")
    for j, cols in JEUX.items():
        w = parite(X[cols])
        k = {s: kelly(ampute(X[cols], a).values @ w) for s, a in SC.items() if s != "nul"}
        p = X[cols].values @ w
        print("  %-10s poids %s | vol %.1f %%/an, moy %+.1f %%/an | Kelly mesure %.1f, prudent %.1f (bt_or : %.2f %% et %.2f %% du compte par R)"
              % (j, " ".join("%s %.3f" % (c, x) for c, x in zip(cols, w)), 100 * p.std() * np.sqrt(252), 100 * p.mean() * 252,
                 k["mesure"], k["prudent"], k["mesure"] * w[0], k["prudent"] * w[0]))
        plans[j] = dict(cols=cols, w=w, k=k)

    print("\n=== 2. Plans (L calibre : 90 %% des trajectoires PRUDENTES a pire baisse < cible, 12 mois, %d tirages)" % NPAR)
    print("  %-10s %5s %6s %5s %5s %6s | %-7s %7s %7s %6s %6s %6s %6s | lots cent 100 EUR / 500 EUR" % (
        "portef.", "cible", "L", "fK_m", "fK_p", "%R_or", "scen.", "moy/m", "med/m", "Pm<0", "P-50", "Pperte", "dd95"))
    for j, pl in plans.items():
        cols, w = pl["cols"], pl["w"]
        Ps = {s: (ampute(X[cols], a).values @ w)[I] for s, a in SC.items()}
        pl["L"], pl["seuil"] = {}, {}
        for cb in CIBLES:
            L = calibre(Ps["prudent"], cb)
            pl["L"][cb] = L
            res = {s: resume(courbe(Ps[s], L)) for s in SC}
            seuil = res["prudent"]["dd_q95"]; pl["seuil"][cb] = seuil
            Eh, _ = rejeu(pd.Series(X[cols].values @ w, index=X.index), L)
            nt, ddh = touches(Eh, seuil)
            pl.setdefault("hist", {})[cb] = (nt, ddh)
            lt = {cap: texte_lots(lots(cols, w, L, cap, M)) for cap in CAPS}
            lt10 = {cap: texte_lots({k: v for k, v in lots(cols, w, L, cap, M).items() if k != "bt_or"}, 0.1)[1] for cap in CAPS}
            for s in SC:
                r = res[s]
                print("  %-10s %4.0f%% %6.2f %5.2f %5.2f %5.2f%% | %-7s %+6.2f%% %+6.2f%% %5.0f%% %5.1f%% %5.1f%% %5.1f%% | %s" % (
                    j, -100 * cb, L, L / pl["k"]["mesure"], L / pl["k"]["prudent"], L * w[0],
                    s, 100 * r["m_moy"], 100 * r["m_med"], 100 * r["p_mneg"], 100 * r["p_moitie"], 100 * r["p_perte"],
                    100 * r["dd_q95"], "" if s != "mesure" else ""))
                for cap in CAPS:
                    rows.append(dict(portefeuille=j, cible=-cb, capital_eur=cap, scenario=s, L=L, frac_kelly_mesure=L / pl["k"]["mesure"],
                                     frac_kelly_prudent=L / pl["k"]["prudent"], risque_R_or_pct=L * w[0],
                                     lots_cent=lt[cap][0], ecart_arrondi_max=lt[cap][1], ecart_arrondi_indices_lotmin01=lt10[cap],
                                     rend_mois_moy=r["m_moy"], rend_mois_med=r["m_med"], p_mois_neg=r["p_mneg"],
                                     p_moins50_12m=r["p_moitie"], p_annee_perte=r["p_perte"], dd_q90=r["dd_q90"],
                                     seuil_arret=seuil, touches_hist=nt, pire_baisse_hist=ddh))
            for cap in CAPS:
                print("      %3.0f EUR : %s  (ecart d'arrondi max %.0f %% ; indices si lot min 0,1 cent : %.0f %%)" % (
                    cap, lt[cap][0], 100 * lt[cap][1], 100 * lt10[cap]))
            print("      seuil d'arret %.1f %% depuis le plus haut ; historique 08/2022-11/2026 rejoue : pire baisse %.1f %%, seuil touche %d fois"
                  % (100 * seuil, 100 * ddh, nt))

    print("\n=== 3. Walk-forward (poids + L appris sur une moitie par MC prudent, rejoues tels quels sur l'autre, reinvestissement hebdo)")
    print("  %-10s %-10s %5s %6s %6s | %8s %7s %6s %6s %8s" % ("portef.", "sens", "cible", "L", "fK_p", "pire bs", "moy/m", "m<0", "nmois", "total"))
    H1, H2 = X[X.index < COUPE], X[X.index >= COUPE]
    for j, cols in JEUX.items():
        for sens, A, T in (("1re->2de", H1, H2), ("2de->1re", H2, H1)):
            w = parite(A[cols]); kp = kelly(ampute(A[cols], 0.5).values @ w)
            Ia = tirages(len(A))
            Pa = (ampute(A[cols], 0.5).values @ w)[Ia]
            for cb in CIBLES:
                L = calibre(Pa, cb)
                E, m = rejeu(pd.Series(T[cols].values @ w, index=T.index), L)
                dd = -(E / np.maximum(E.cummax(), 1) - 1).min()
                print("  %-10s %-10s %4.0f%% %6.2f %6.2f | %7.1f%% %+6.2f%% %5.0f%% %6d %+7.0f%%" % (
                    j, sens, -100 * cb, L, L / kp if kp > 0 else np.nan, -100 * dd, 100 * m.mean(), 100 * (m < 0).mean(), len(m),
                    100 * (E.iloc[-1] - 1)))
                rows.append(dict(portefeuille=j, cible=-cb, capital_eur=np.nan, scenario="wf " + sens, L=L,
                                 frac_kelly_prudent=L / kp if kp > 0 else np.nan, rend_mois_moy=m.mean(), p_mois_neg=(m < 0).mean(),
                                 pire_baisse_hist=dd))

    print("\n=== 5. Sensibilite avantage NUL, plan cible -30 %% : voir lignes « nul » ci-dessus ; resume :")
    for j in JEUX:
        r = [x for x in rows if x["portefeuille"] == j and x["cible"] == -0.30 and x["scenario"] == "nul"][0]
        print("  %-10s L %.2f : P(-50 %% en 12 mois) %.1f %%, P(annee en perte) %.1f %%, P(mois < 0) %.0f %%, rend. median/mois %+.2f %%"
              % (j, r["L"], 100 * r["p_moins50_12m"], 100 * r["p_annee_perte"], 100 * r["p_mois_neg"], 100 * r["rend_mois_med"]))
    pd.DataFrame(rows).to_csv(os.path.join(ICI, "donnees", "plan_cent.csv"), index=False, float_format="%.5g")
    print("\nEcrit donnees/plan_cent.csv (%d lignes). Duree %.0f s." % (len(rows), time.time() - T00))
