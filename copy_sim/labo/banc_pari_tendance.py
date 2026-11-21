"""Banc PT : « poche pari tendance » (PRIORITES 21/11 15 h 20, demande de Baptiste). Compte DEMO / labo, aucun ordre.
Poche separee de 100 ou 200 EUR (compte cent) ; on mise gros sur les paniers de tendance de l'or et on ENCAISSE des
que l'objectif est atteint (on s'arrete) ; plancher : poche sous 20 % du depart = on s'arrete (ruine).
Paniers REELS de la mecanique bt_or (banc_bt_plus.simule_plus, memes entrees / sorties / spread reel) :
  bt_or      = tailles 1-1-1, 3 positions (robot bt_or) ;
  bt_or_plus = tailles 1-2-3-4-5, 5 positions (robot bt_or_plus_opt, « ajouts 1-2-3 »).
  Jeux : or M5 06/2025 -> 11/2026 (~18 mois, hausse de l'or) et or H1 08/2022 -> 11/2026 (~4 ans, periode plate comprise).
Mise : f = 3 / 5 / 7,5 / 10 / 15 % du compte (au debut du panier) par 1 R, 1 R = perte d'UNE position de base au stop
  initial (0,667 ATR jour). Compte cent : 1 unite = 0,01 lot cent = 0,01 once ; unites = max(1, plancher(f x compte /
  risque d'une unite)), risque d'une unite = stop relatif du panier x 4 000 $ x 0,01 (prix d'aujourd'hui) ; EUR = 1,16 $.
  Gain du panier = unites x risque d'une unite x R du panier (R de la variante, tailles comprises).
Objectifs : x2, x3, x5 (compte >= objectif a la cloture d'un panier -> on encaisse et on s'arrete).
Monte-Carlo : 10 000 parcours, bootstrap stationnaire de la SUITE des paniers (dans l'ordre de cloture, blocs moyens de
  10 paniers, garde les series), horizon 24 mois (paniers par mois du jeu), graine 2115. Les paniers sont joues l'un
  apres l'autre (approximation : deux paniers ouverts en meme temps sont comptes en sequence).
Scenarios : mesure ; prudent = avantage / 2 (chaque panier perd la moitie du R moyen de la variante) ; nul = R moyen retire.
Mesures par montage (variante x f x objectif x depart x jeu x scenario) : chance d'atteindre l'objectif avant la ruine en
  24 mois, chance de ruine, ni l'un ni l'autre, duree mediane jusqu'a l'arret (mois, parmi les parcours arretes),
  esperance de la valeur finale (objectif encaisse, plancher, ou compte a 24 mois) en multiple du depart.
Semaine 16-20/11 (robot en demo, journal) : un seul panier bt_or ferme, +13,18 R ; bt_or_plus_opt +39,56 R (les paniers
  encore ouverts le vendredi soir ne sont pas comptes). Resultat de la poche = depart x (1 + f x R), objectif plafonne.
Reference : pari_opt (repli S&P + Russell, banc_pari_triple, avantage / 2, 5 ans) : x3 56 %, ruine 39 %, ~1,4 an.
CHOIX FIXE D'AVANCE : parmi les montages dont la ruine (PRUDENT, H1 4 ans, 100 EUR, 24 mois) est <= 40 % (celle de
  pari_opt), celui qui a la plus forte esperance de valeur finale (PRUDENT, H1, 100 EUR). S'il n'y en a aucun dont
  l'esperance prudente H1 depasse 1,0 (le depart), on ne met rien sur la demo.
RESULTAT (execution du 21/11/2026, 26 s, 10 000 parcours) : CHOIX = bt_or, mise 3 % par R, objectif x5 (esperance
  prudente H1 1,96 fois le depart, ruine 11 %). A 100 EUR, 24 mois : x5 atteint mesure M5 94 % / H1 49 %, prudent H1 23 %,
  sans avantage 8 % ; ruine mesure H1 2 %, prudent 11 %, sans avantage 36 % ; duree mediane ~15 mois ; rien atteint en
  24 mois 66 % (prudent). x3 a 3 % : 39 % / ruine 11 % (prudent H1). Plus de mise = plus de ruine sans plus d'objectif :
  a 5 % la ruine prudente passe a 37-48 %, a 15 % a 60-80 %. bt_or_plus (1-2-3) est moins bon partout (pire panier
  -6,6 R ; a 3 % : ruine prudente 50-71 %). Le choix tombe au bord de la grille (3 %) : une mise plus petite n'a pas ete
  testee. Semaine 16-20/11 (paniers fermes) : bt_or 3 % = x1,40 ; bt_or_plus 7,5 % aurait fait x3,97.
  Reference pari_opt : x3 56 % en 5 ans, ruine 39 %.
Ecrit donnees/pari_tendance.csv. Usage : python3 banc_pari_tendance.py"""
import os, time, contextlib, io, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_bt_regulier as BR
    import banc_jumeau as BJ
    import banc_bt_plus as BP

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
NPAR, BLOC, MOIS = 10000, 10.0, 24
FS = (0.03, 0.05, 0.075, 0.10, 0.15)
OBJ = (2.0, 3.0, 5.0)
DEPARTS = (100.0, 200.0)
PLANCHER, EURUSD, PX = 0.20, 1.16, 4000.0
VARS = {"bt_or": BP.NOMV.index("1-1-1/3/tjrs"), "bt_or_plus": BP.NOMV.index("1-2-3/5/tjrs")}
SEMAINE = {"bt_or": 13.18, "bt_or_plus": 39.56}
rng = np.random.default_rng(2115)


def paniers(d, kw):
    P, GR, _, _, _, _ = BP.simule_plus(d, **kw)
    Q = BR.simule(d, **kw)                           # memes paniers (ouverture, sortie) : stop et prix
    assert len(Q) == len(P) and (Q.t1.values == P.t1.values).all()
    o = np.argsort(P.t1.values, kind="stable")
    mois = (P.t1.max() - P.t0.min()) / 86400 / 30.44
    return {k: GR[o, j] for k, j in VARS.items()}, (Q.stop / Q.px).values[o], len(P) / mois


def tirages(n, m):
    out = np.empty((NPAR, m), int)
    for k in range(NPAR):
        neuf = rng.random(m) < 1 / BLOC; neuf[0] = True
        bl = np.cumsum(neuf) - 1; deb = np.flatnonzero(neuf)
        out[k] = (rng.integers(n, size=len(deb))[bl] + np.arange(m) - deb[bl]) % n
    return out


def parcours(R, srel, II, f, obj, dep_eur):
    dep = dep_eur * EURUSD
    E = np.full(NPAR, dep); fin = np.zeros(NPAR, int); etat = np.zeros(NPAR, int)   # 1 objectif, -1 ruine
    for t in range(II.shape[1]):
        a = etat == 0
        if not a.any():
            break
        i = II[a, t]
        ru = srel[i] * PX * 0.01                              # risque d'une unite (0,01 once) en $
        u = np.maximum(1, np.floor(f * E[a] / ru))
        E[a] = E[a] + u * ru * R[i]
        x = np.flatnonzero(a)
        g, r = E[a] >= obj * dep, E[a] < PLANCHER * dep
        etat[x[g]] = 1; etat[x[r & ~g]] = -1; fin[x[g | r]] = t + 1
        E[x[g]] = obj * dep; E[x[r & ~g]] = np.maximum(E[x[r & ~g]], 0.0)
    return E / dep, etat, fin


if __name__ == "__main__":
    a5, b5 = BR.charge("xau_m5_2025a"), BR.charge("xau_m5_90k")
    d5 = pd.concat([a5, b5[b5.heure > a5.heure.iloc[-1]]], ignore_index=True)
    dh = BR.charge("xau_h1_50k")
    dh = dh[dh.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
    JEUX = {"M5": paniers(d5, {}), "H1": paniers(dh, dict(span=48, heures=BJ.H_H1, debut=60))}
    rows = []
    for jeu, (RR, srel, pm) in JEUX.items():
        m = int(round(pm * MOIS))
        II = tirages(len(srel), m)
        for v, R0 in RR.items():
            mu = R0.mean()
            print("%s %-10s %4d paniers (%.1f/mois)  R moyen %+.3f  pire panier %+.2f R  meilleur %+.1f R"
                  % (jeu, v, len(R0), pm, mu, R0.min(), R0.max()))
            for sc, R in (("mesure", R0), ("prudent", R0 - mu / 2), ("nul", R0 - mu)):
                for f in FS:
                    for obj in OBJ:
                        for dep in DEPARTS:
                            V, etat, fin = parcours(R, srel, II, f, obj, dep)
                            arr = etat != 0
                            rows.append(dict(jeu=jeu, variante=v, scenario=sc, mise=f, objectif=obj, depart=dep,
                                             p_objectif=(etat == 1).mean(), p_ruine=(etat == -1).mean(),
                                             p_rien=(etat == 0).mean(), sous_depart=(V < 1).mean(),
                                             duree_med_mois=np.median(fin[arr]) / pm if arr.any() else np.nan,
                                             esperance=V.mean(), semaine=min(obj, 1 + f * SEMAINE[v])))
    T = pd.DataFrame(rows)
    T.round(4).to_csv(os.path.join(ICI, "donnees", "pari_tendance.csv"), index=False)
    pd.set_option("display.width", 220); pd.set_option("display.max_rows", 400)
    k = ["variante", "mise", "objectif"]
    def vue(jeu, sc, dep=100.0):
        return T[(T.jeu == jeu) & (T.scenario == sc) & (T.depart == dep)].set_index(k)
    H = vue("H1", "prudent")
    tab = pd.DataFrame({
        "obj_mes_M5": vue("M5", "mesure").p_objectif, "obj_mes_H1": vue("H1", "mesure").p_objectif,
        "obj_pru_H1": H.p_objectif, "ruine_pru_H1": H.p_ruine, "obj_nul_H1": vue("H1", "nul").p_objectif,
        "ruine_nul_H1": vue("H1", "nul").p_ruine, "duree_pru_H1": H.duree_med_mois, "esp_pru_H1": H.esperance,
        "esp_mes_M5": vue("M5", "mesure").esperance, "semaine": H.semaine})
    print("\n100 EUR, 24 mois (chances en fraction ; duree en mois ; esperance en fois le depart)")
    print(tab.round(3).to_string())
    ok = H[H.p_ruine <= 0.40]
    if len(ok) and ok.esperance.max() > 1.0:
        best = ok.esperance.idxmax()
        print("\nCHOIX (fixe d'avance) : %s mise %.3f objectif x%g  esperance prudente H1 %.3f, ruine %.3f, objectif %.3f"
              % (best + (ok.esperance.max(), ok.p_ruine[best], ok.p_objectif[best])))
        print(T[(T.variante == best[0]) & (T.mise == best[1]) & (T.objectif == best[2])].round(3).to_string())
    else:
        print("\nCHOIX : aucun montage n'a une esperance prudente H1 > 1 avec ruine <= 40 % : rien sur la demo.")
    print("Duree %.0f s ; ecrit donnees/pari_tendance.csv (%d lignes)" % (time.time() - T00, len(T)))
