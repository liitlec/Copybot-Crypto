"""Banc FIN DE SEANCE : momentum de la derniere demi-heure sur les indices US (PRIORITES 22/11, contre-expertise, point 3).
Effet publie (Gao, Han, Li, Zhou ; ETF SPY 1993-2013) : le rendement de la cloture de la veille (16 h New York) a 10 h
NY predit le sens de la derniere demi-heure (15 h 30 -> 16 h). Regle : prendre le sens de ce rendement du matin a
15 h 30 NY, sortir a 16 h NY. Une position par indice et par jour, pas de stop, rien la nuit (pas de financement).

Donnees
  - Courtier M5 (prix BID + colonne sp = spread en prix, BR.charge) : SP500+ (sp_m5_90k, 08/2025 -> 11/2026),
    NAS100+ (nas_m5_2025a + nas_m5_90k, 06/2025 -> 11/2026), DJ30+ (dj_m5_90k, 08/2025 -> 11/2026).
    Horloge serveur = New York + 7 h toute l'annee (verifie ici : bougie M5 la plus ample = 16:30 serveur = 9 h 30 NY,
    en ete, en hiver et pendant les semaines de decalage Europe / Etats-Unis). Donc : cloture de la veille = cloture
    de la bougie 22:55 serveur de la seance precedente ; 10 h NY = cloture de la bougie 16:55 ; 15 h NY = ouverture de
    22:00 ; 15 h 30 NY = ouverture de 22:30 ; 16 h NY = cloture de 22:55 ; 14 h 30 NY = ouverture de 21:30.
    Calendrier de bourse = jours Yahoo ayant une bougie 15 h 30 (exclut feries et demi-seances).
    Couts : calculs au prix MILIEU (bid + sp/2) ; on paie un demi-spread reel a l'entree (bougie d'entree) et un
    demi-spread reel a la sortie (bougie 22:55), soit un spread par aller-retour (~0,5 bp SP, 0,3 bp NAS, 0,2 bp DJ).
  - PERIODE RESERVEE : les 12 derniers mois de chaque serie courtier (debut = derniere bougie - 365 jours, soit
    ~11/2025 -> 11/2026), lue UNE SEULE FOIS a la fin avec la regle et le reglage choisis sur l'apprentissage.
    Avant la reserve il ne reste que ~3 mois (SP, DJ) a ~5 mois (NAS) de courtier : l'apprentissage utilise AUSSI
    Yahoo 1 h des indices au comptant (donnees/yahoo_1h_indices.csv, 12/2023 -> ; bougies 9 h 30, 10 h 30, ...,
    15 h 30 NY ; pas de spread : on ajoute le spread median du courtier rapporte au prix). Approximations Yahoo
    (dites d'avance) : signal du matin = cloture veille -> 10 h 30 (pas de 10 h) ; entree 15 h 30 = ouverture de la
    bougie 15 h 30, sortie = sa cloture ; « entree 15 h » = ouverture de la bougie 14 h 30 (1 h 30 de tenue) ;
    2e signal = bougie 14 h 30 (14 h 30 -> 15 h 30) pour l'entree 15 h 30, bougie 13 h 30 pour l'entree « 15 h ».
    Pour chaque date d'apprentissage : courtier si disponible (ecart-type du signal calculable), sinon Yahoo.
  - Russell 2000 : le courtier n'a us2000 qu'en D1 -> PAS testable en intrajournalier sur le CFD. A titre
    d'information seulement (hors verdict) : ^RUT Yahoo 1 h + spread median du CFD us2000 D1 (0,32 point).

Grille FIXEE AVANT (12 reglages, les memes pour les 3 indices) :
  seuil k sur |r_matin| / ecart-type des 60 seances precedentes (au moins 20, passe seulement) : 0 / 0,25 / 0,5
  x entree 15 h 30 ou 15 h NY (sortie 16 h dans les deux cas)
  x avec / sans 2e signal (rendement de la demi-heure qui precede l'entree : 15 h -> 15 h 30 pour l'entree 15 h 30,
    14 h 30 -> 15 h pour l'entree 15 h) : comme l'article, on ne trade que si les deux rendements ont le meme signe.
  Serie jugee = panier a poids egal des 3 CFD (moyenne des bp des 3 indices, 0 si pas de trade ce jour-la).
  Choix : reglage au meilleur t (jours du panier) sur l'apprentissage. Reality check de White (BR.white, bootstrap
  stationnaire, blocs moyens 5 j, 2000 tirages) des 12 contre zero sur l'apprentissage.
Mesures : trades, gain moyen en points et en bp apres spread, t, % gagnants, pire baisse (bp cumules), mois > 0.
Portefeuille : bt_or = BR.simule(xau_m5_90k) en R par jour de sortie ; correlation journaliere et mensuelle avec le
  panier fin de seance (periode courtier : apprentissage courtier + reserve), resultat pendant les mois NEGATIFS de
  bt_or ; meme chose pour repli_ind (moyenne des 4 replis RSI 2 de banc_portefeuille.piece_repli, comme banc_mix).
Verdict (fixe d'avance) : TIENT = moyenne apres spread > 0 sur la reserve (panier) ET t >= 2 sur l'ensemble
  (apprentissage + reserve, panier) ET p de White < 0,10 sur l'apprentissage ET somme >= 0 pendant les mois ou bt_or
  perd ; PRESQUE = positif sur la reserve mais t < 2 ou p >= 0,10 (ou negatif les mois faibles de bt_or) ;
  sinon NE TIENT PAS.
Ecrit donnees/fin_seance.csv (trades du reglage choisi, 3 CFD + RUT d'information).
RESULTAT (execution du 22/11/2026, 3 s, reserve lue une seule fois) : verdict NE TIENT PAS (aucune des 4 conditions).
  Horloge confirmee (pic 16:30 serveur ete, hiver et 03/2026) ; SP500+ / ^GSPC : correlation 15 h 30 -> 16 h = 0,992.
  Apprentissage (Yahoo 01/2024 -> 07-09/2025 + courtier) : 11 reglages sur 12 negatifs apres spread ; la regle de
  l'article (k = 0, 15 h 30, sans 2e signal) -0,71 bp/jour (t -0,7). Choisi : k = 0,5, entree 15 h, avec 2e signal,
  +0,28 bp (t +0,16) ; White p = 0,807. Reserve (11/2025 -> 11/2026), panier 124 j : -2,74 bp (t -1,75), 45 %
  gagnants, creux -405 bp ; SP -3,95 bp (t -1,4), NAS -3,74 (t -1,0), DJ -6,08 (t -2,2) ; ensemble t -0,70.
  RUT (information, Yahoo) : -0,97 bp puis +1,85 bp (t +0,5). Portefeuille (09/2025 -> 11/2026) : correlation avec
  bt_or jour -0,05 / mois +0,03 ; pendant les 6 mois negatifs de bt_or -236 bp (1/6 > 0) contre repli_ind +609 bp
  (6/6 > 0, correlation +0,06 / +0,11). Rien a coder.
Usage : python3 banc_fin_seance.py   (FIN_SEANCE_SANS_RESERVE=1 : mise au point sans lire la reserve)
"""
import os, time, io, contextlib, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_bt_regulier as BR
    import banc_portefeuille as BP

T0 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
SANS_RES = os.environ.get("FIN_SEANCE_SANS_RESERVE") == "1"
GRILLE = [(k, e, s2) for k in (0.0, 0.25, 0.5) for e in ("15h30", "15h") for s2 in (False, True)]
tst = BR.tst
creux = BR.creux

# ------------------------------------------------------------------ calendrier et Yahoo
Y = pd.read_csv(os.path.join(ICI, "donnees", "yahoo_1h_indices.csv"))
Y["t"] = pd.to_datetime(Y.ny); Y["d"] = Y.t.dt.normalize(); Y["hm"] = Y.t.dt.strftime("%H:%M")
CAL = pd.DatetimeIndex(sorted(Y[(Y.tk == "^GSPC") & (Y.hm == "15:30")].d.unique()))


def table_yahoo(tk, cout_bp):
    y = Y[Y.tk == tk].set_index(["d", "hm"])
    g = lambda h, c: y.xs(h, level="hm")[c].reindex(CAL)
    T = pd.DataFrame({"veille": g("15:30", "close").shift(1), "matin": g("09:30", "close"),
                      "e15h30": g("15:30", "open"), "e15h": g("14:30", "open"), "sortie": g("15:30", "close"),
                      "a15h30_0": g("14:30", "open"), "a15h30_1": g("14:30", "close"),
                      "a15h_0": g("13:30", "open"), "a15h_1": g("13:30", "close")})
    T["sp_e"] = T["sp_s"] = cout_bp * 1e-4 * T.sortie      # spread typique du courtier, en prix
    T["src"] = "yahoo"
    return T


def table_courtier(d):
    """Une ligne par seance (CAL) : prix MILIEU (bid + sp/2) aux heures utiles, spreads reels."""
    t = d.heure.values; jour = pd.to_datetime(t // 86400 * 86400, unit="s"); hm = (t // 60) % 1440
    mo, mc = d.ouverture + d.sp / 2, d.cloture + d.sp / 2
    X = pd.DataFrame({"d": jour, "hm": hm, "o": mo.values, "c": mc.values, "sp": d.sp.values})
    X = X[X.d.isin(CAL)].set_index(["d", "hm"])
    g = lambda m, c: X.xs(m, level="hm")[c].reindex(CAL) if m in X.index.get_level_values(1) else pd.Series(np.nan, CAL)
    H = lambda h, m: h * 60 + m
    T = pd.DataFrame({"veille": g(H(22, 55), "c").shift(1), "matin": g(H(16, 55), "c"),
                      "e15h30": g(H(22, 30), "o"), "e15h": g(H(22, 0), "o"), "sortie": g(H(22, 55), "c"),
                      "a15h30_0": g(H(22, 0), "o"), "a15h30_1": g(H(22, 25), "c"),
                      "a15h_0": g(H(21, 30), "o"), "a15h_1": g(H(21, 55), "c"),
                      "sp_e15h30": g(H(22, 30), "sp"), "sp_e15h": g(H(22, 0), "sp"), "sp_s": g(H(22, 55), "sp")})
    T["src"] = "courtier"
    return T


def trades(T, k, e, s2):
    """Rend un DataFrame (une ligne par trade) pour le reglage (k, e, s2)."""
    r1 = T.matin / T.veille - 1
    sd = r1.rolling(60, min_periods=20).std().shift(1)
    s = np.sign(r1)
    ok = sd.notna() & r1.notna() & T["e" + e].notna() & T.sortie.notna() & (r1.abs() >= k * sd) & (s != 0)
    ra = T["a%s_1" % e] / T["a%s_0" % e] - 1
    if s2:
        ok &= np.sign(ra) == s
    pe, ps = T["e" + e], T.sortie
    spe = T["sp_e" + e] if ("sp_e" + e) in T else T.sp_e
    pts = s * (ps - pe) - (spe + T.sp_s) / 2
    R = pd.DataFrame({"sens": s, "r_matin": r1, "z": r1 / sd, "r_avant": ra, "p_entree": pe, "p_sortie": ps,
                      "sp_entree": spe, "sp_sortie": T.sp_s, "points": pts, "bp": pts / pe * 1e4,
                      "brut_bp": s * (ps - pe) / pe * 1e4, "src": T.src})[ok]
    return R


def stats(R, col="bp"):
    x = R[col].values
    if len(x) == 0:
        return dict(n=0, pts=np.nan, bp=np.nan, t=np.nan, gagn=np.nan, creux=np.nan, mois="-")
    m = R.groupby(R.index.to_period("M"))[col].sum()
    return dict(n=len(x), pts=R.points.mean(), bp=x.mean(), t=tst(x), gagn=100 * (x > 0).mean(), creux=creux(x),
                mois="%d/%d" % ((m > 0).sum(), len(m)))


def ligne(nom, R):
    s = stats(R)
    if s["n"] == 0:
        return "  %-26s %5d" % (nom, 0)
    return "  %-26s %5d %+8.2f %+7.2f %+5.2f %5.1f %+8.1f %7s" % (nom, s["n"], s["pts"], s["bp"], s["t"], s["gagn"], s["creux"], s["mois"])


ENT = "  %-26s %5s %8s %7s %5s %5s %8s %7s" % ("", "trades", "points", "bp", "t", "%gagn", "creux bp", "mois>0")

if __name__ == "__main__":
    # ---------------------------------------------------------------- donnees courtier, verification de l'horloge
    a, b = BR.charge("nas_m5_2025a"), BR.charge("nas_m5_90k")
    COURT = {"SP": BR.charge("sp_m5_90k"), "NAS": pd.concat([a, b[b.heure > a.heure.iloc[-1]]], ignore_index=True),
             "DJ": BR.charge("dj_m5_90k")}
    print("Horloge : 2 bougies M5 les plus amples en mediane (heure serveur ; attendu 16:30 = 9 h 30 NY) :")
    for n, d in COURT.items():
        t = pd.to_datetime(d.heure, unit="s"); hm = t.dt.strftime("%H:%M"); amp = d.haut - d.bas
        out = []
        for lab, m in (("ete", t.dt.month.isin([6, 7, 8])), ("hiver", t.dt.month.isin([12, 1, 2])),
                       ("decalage 03/2026", (t >= "2026-03-09") & (t < "2026-03-28"))):
            out.append("%s %s" % (lab, "/".join(amp[m].groupby(hm[m]).median().sort_values().index[-2:][::-1])))
        print("  %-3s %s ; spread median %.2f pt = %.2f bp" % (n, " ; ".join(out), d.sp.median(), (d.sp / d.cloture).median() * 1e4))
    COUT = {n: (d.sp / d.cloture).median() * 1e4 for n, d in COURT.items()}
    TK = {"SP": "^GSPC", "NAS": "^NDX", "DJ": "^DJI"}
    RES0, TAB = {}, {}
    for n, d in COURT.items():
        RES0[n] = (pd.to_datetime(d.heure.iloc[-1], unit="s") - pd.Timedelta(days=365)).normalize()
        TAB[n] = (table_courtier(d), table_yahoo(TK[n], COUT[n]))
    print("Reserve (12 derniers mois) : " + " ; ".join("%s des le %s" % (n, RES0[n].date()) for n in RES0))
    rx = pd.read_csv(os.path.join(ICI, "mt5", "donnees", "us2000_d1_5k.csv.gz"))
    cout_rut = 0.32 / rx.cloture.iloc[-250:].median() * 1e4
    TRUT = table_yahoo("^RUT", cout_rut)
    Tc, Ty = TAB["SP"]; m = Tc.index < RES0["SP"]
    q = pd.concat([(Tc.sortie / Tc.e15h30 - 1)[m], (Ty.sortie / Ty.e15h30 - 1)[m]], axis=1).dropna()
    print("Controle SP500+ / ^GSPC (seances communes avant la reserve, n = %d) : correlation du rendement 15 h 30 -> 16 h = %.3f"
          % (len(q), q.corr().iloc[0, 1]))
    RES_RUT = (TRUT.sortie.last_valid_index() - pd.Timedelta(days=365)).normalize()

    def tous(n, k, e, s2):
        """Trades d'un indice : courtier quand il a un signal, sinon Yahoo (apprentissage) ; reserve = courtier."""
        Tc, Ty = TAB[n]
        Rc, Ry = trades(Tc, k, e, s2), trades(Ty, k, e, s2)
        # dates ou le courtier a un ecart-type de signal (meme sans trade) : Yahoo exclu ces jours-la
        r1 = Tc.matin / Tc.veille - 1
        cov = r1.index[r1.rolling(60, min_periods=20).std().shift(1).notna()]
        Ry = Ry[(~Ry.index.isin(cov)) & (Ry.index < RES0[n])]
        R = pd.concat([Ry, Rc]).sort_index()
        R["periode"] = np.where(R.index >= RES0[n], "reserve", "apprentissage")
        return R

    ALL = {g: {n: tous(n, *g) for n in TAB} for g in GRILLE}
    print("\nOrigine des jours d'apprentissage (reglage k=0, 15h30, sans 2e signal) : " + " ; ".join(
        "%s yahoo %d (%s -> %s) + courtier %d" % (n, (R.src == "yahoo").sum(), R[R.src == "yahoo"].index[0].date(),
                                                    R[R.src == "yahoo"].index[-1].date(),
                                                    ((R.src == "courtier") & (R.periode == "apprentissage")).sum())
        for n, R in ALL[GRILLE[0]].items()))

    def panier(g, per):
        S = pd.DataFrame({n: R[R.periode == per].bp for n, R in ALL[g].items()})
        return S.fillna(0).mean(1)          # jours ou au moins un indice trade

    # ---------------------------------------------------------------- apprentissage : grille
    APP = pd.DataFrame({g: panier(g, "apprentissage") for g in GRILLE}).fillna(0)
    print("\nAPPRENTISSAGE, panier 3 CFD (bp par jour de trade, apres spread) :")
    print("  %-30s %5s %7s %6s %6s | %s" % ("reglage (k, entree, 2e signal)", "jours", "bp/j", "t", "%gagn", "SP / NAS / DJ (bp moyen par trade, t)"))
    for g in GRILLE:
        x = APP[g][APP[g] != 0]
        det = " / ".join("%+.2f (%+.1f)" % (R[R.periode == "apprentissage"].bp.mean(), tst(R[R.periode == "apprentissage"].bp.values))
                         for R in ALL[g].values())
        print("  k=%-4s %-5s %-19s %5d %+7.2f %+6.2f %5.1f | %s" % (g[0], g[1], "avec 2e" if g[2] else "sans", len(x), x.mean(),
                                                                  tst(APP[g].values), 100 * (x > 0).mean(), det))
    best = max(GRILLE, key=lambda g: tst(APP[g].values))
    ib, p_white = BR.white(APP.values)
    print("Choix (meilleur t) : k=%s, entree %s, %s 2e signal ; White sur les 12 (%d jours) : meilleur %s, p = %.3f"
          % (best[0], best[1], "avec" if best[2] else "sans", len(APP), GRILLE[ib], p_white))
    print("Controle sans spread (meme reglage, apprentissage) : " + " ; ".join(
        "%s %+.2f bp brut" % (n, R[R.periode == "apprentissage"].brut_bp.mean()) for n, R in ALL[best].items()))
    if SANS_RES:
        print("(mise au point : reserve non lue)"); raise SystemExit

    # ---------------------------------------------------------------- reserve : lue une fois
    print("\nRESULTAT par indice, reglage choisi (bp apres spread) :")
    print(ENT)
    for n, R in ALL[best].items():
        for per in ("apprentissage", "reserve"):
            print(ligne("%s %s" % (n, per), R[R.periode == per]))
        print(ligne("%s  dont courtier hors res." % n, R[(R.periode == "apprentissage") & (R.src == "courtier")]))
    PA, PR = panier(best, "apprentissage"), panier(best, "reserve")
    TOT = pd.concat([PA, PR])
    print("  Panier 3 CFD : apprentissage %d j %+.2f bp (t %+.2f) ; RESERVE %d j %+.2f bp (t %+.2f, %% gagn %.0f, creux %+.1f bp) ;"
          " ensemble t %+.2f" % (len(PA), PA.mean(), tst(PA.values), len(PR), PR.mean(), tst(PR.values), 100 * (PR > 0).mean(),
                                 creux(PR.values), tst(TOT.values)))
    rr = trades(TRUT, *best); rr["periode"] = np.where(rr.index >= RES_RUT, "reserve", "apprentissage")
    print("  Information (hors verdict, Yahoo ^RUT au comptant + spread du CFD us2000 %.2f bp, pas de M5 courtier) :" % cout_rut)
    for per in ("apprentissage", "reserve"):
        print(ligne("RUT %s" % per, rr[rr.periode == per]))
    print("  Double spread (robustesse, reserve panier) : %+.2f bp" % (
        pd.DataFrame({n: (R.bp - (R.sp_entree + R.sp_sortie) / 2 / R.p_entree * 1e4)[R.periode == "reserve"]
                      for n, R in ALL[best].items()}).fillna(0).mean(1).mean()))

    # ---------------------------------------------------------------- portefeuille
    P = BR.simule(BR.charge("xau_m5_90k"))
    bt = P.groupby("jour").g.sum()
    with contextlib.redirect_stdout(io.StringIO()):
        D = BP.donnees()
    rep = sum(BP.piece_repli(D, n)[0] for n in ("SP", "NAS", "DJ", "RUT")) / 4 * 1e4      # bp de notionnel
    C = pd.DataFrame({n: R[R.src == "courtier"].bp for n, R in ALL[best].items()}).fillna(0).mean(1)
    deb, fin = max(C.index[0], bt.index[0]), min(C.index[-1], bt.index[-1], rep.index[-1])
    B = pd.bdate_range(deb, fin)
    X = pd.DataFrame({"bt_or": bt, "fin_seance": C, "repli_ind": rep}).reindex(B).fillna(0)
    Mo = X.groupby(X.index.to_period("M")).sum()
    print("\nPORTEFEUILLE (%s -> %s, %d jours ouvres, %d mois ; fin_seance = panier courtier, reglage choisi, bp ;"
          " repli_ind en bp de notionnel ; bt_or en R) :" % (B[0].date(), B[-1].date(), len(B), len(Mo)))
    neg = Mo.bt_or < 0
    print("  bt_or : %+.1f R, %d mois negatifs (%s)" % (X.bt_or.sum(), neg.sum(), ", ".join(str(m) for m in Mo.index[neg])))
    for c in ("fin_seance", "repli_ind"):
        a = Mo[c][neg]
        print("  %-10s corr jour %+.2f, mois %+.2f ; total %+7.1f bp ; mois ou bt_or perd : somme %+7.1f bp, %d/%d > 0 ;"
              " mois ou bt_or gagne : %+7.1f bp" % (c, X.bt_or.corr(X[c]), Mo.bt_or.corr(Mo[c]), X[c].sum(), a.sum(),
                                                    (a > 0).sum(), len(a), Mo[c][~neg].sum()))
    print("  corr fin_seance / repli_ind : jour %+.2f, mois %+.2f" % (X.fin_seance.corr(X.repli_ind), Mo.fin_seance.corr(Mo.repli_ind)))
    faible = Mo.fin_seance[neg].sum()

    # ---------------------------------------------------------------- verdict
    c1, c2, c3, c4 = PR.mean() > 0, tst(TOT.values) >= 2, p_white < 0.10, faible >= 0
    v = "TIENT" if c1 and c2 and c3 and c4 else ("PRESQUE" if c1 else "NE TIENT PAS")
    print("\nVERDICT (fixe d'avance) : %s  [reserve > 0 : %s ; t ensemble >= 2 : %s (%+.2f) ; White < 0,10 : %s (%.3f) ;"
          " mois faibles de bt_or >= 0 : %s (%+.1f bp)]" % (v, c1, c2, tst(TOT.values), c3, p_white, c4, faible))

    # ---------------------------------------------------------------- controles et CSV
    out = []
    for n, R in list(ALL[best].items()) + [("RUT_info", rr.assign(src="yahoo"))]:
        z = R.copy(); z.insert(0, "indice", n); out.append(z)
    O = pd.concat(out); O.index.name = "date"
    O["k"], O["entree_ny"], O["second_signal"] = best
    O.to_csv(os.path.join(ICI, "donnees", "fin_seance.csv"), float_format="%.6g")
    R = ALL[best]["SP"]; R = R[R.periode == "reserve"]
    print("\nControles (SP500+, reserve, prix MILIEU = bid + spread/2 ; heures serveur) :")
    for dte in (R.bp.idxmax(), R.index[len(R) // 2]):
        r = R.loc[dte]; Tc = TAB["SP"][0].loc[dte]
        print("  %s : veille 22:55 %.2f -> 16:55 %.2f (r_matin %+.3f %%, z %+.2f) => %s ; entree %.2f (sp %.2f) ; sortie 22:55 %.2f (sp %.2f) ;"
              " %+.2f points = %+.2f bp apres spread" % (dte.date(), Tc.veille, Tc.matin, 100 * r.r_matin, r.z,
                                                         "ACHAT" if r.sens > 0 else "VENTE", r.p_entree, r.sp_entree, r.p_sortie,
                                                         r.sp_sortie, r.points, r.bp))
    print("Ecrit donnees/fin_seance.csv (%d lignes). Duree %.0f s" % (len(O), time.time() - T0))
