"""Banc T2B : reponse de GPT Astra (tour 2), points 4, 5 et 6 (PRIORITES 23/11, 11 h ; compte DEMO / labo, aucun ordre).
La regle proposee par GPT Astra (version A, laisser courir) = banc_gpt_pyramide.simule_regle IMPORTEE telle quelle ;
bt_or = banc_bt_regulier.simule (et banc_decompose_bt pour les paniers possibles). Rien n'est regle.

POINT 4 - Diversification a risque global constant (GPT version A, et bt_or), donnees M5 du courtier (spread reel ; GPT :
  M5 regroupees en M15, parametres D1 comme banc_multi_marches). Gain d'un panier compte au jour de SA SORTIE (comme
  banc_multi_marches), jours calendaires, 0 sans sortie. Portefeuille a k marches : chaque marche a 1/k du risque
  (resultat du jour = somme des R des marches / k : meme perte totale si tous les stops initiaux sont touches) ; or seul
  = 1 x R de l'or. Etapes : (1) or seul ; (2) or + indice + EUR/USD, indice = Nasdaq ou S&P, le meilleur total R sur la
  1re MOITIE de la fenetre seulement (par mecanique) ; (3) + argent ; (4) + BTC ; (5) + ETH.
  Fenetres : principale = periode commune or / Nasdaq / S&P / EUR / argent (28/08/2025 -> 11/11/2026) pour les etapes
  1-3 ; BTC et ETH n'existent qu'a partir du 01/01/2026 -> etapes 1-5 refaites sur 01/01/2026 -> 11/11/2026 (or seul
  recalcule sur la meme fenetre). Index choisi sur la 1re moitie de la fenetre principale (meme choix sur la courte).
  Mesures fixees d'avance : jours ou les strategies PERDENT ENSEMBLE = jours ou >= 2 marches du portefeuille ont un
  resultat < 0 : nombre, somme du portefeuille ces jours-la, pire de ces jours (et l'or seul a 100 % du risque sur les
  MEMES jours) ; croissance nette (total R) ; temps sous le dernier sommet (% des jours, plus longue periode en jours) ;
  pire baisse. Correlations : rendements journaliers des cours (derniere cloture M5 du jour) et resultats journaliers
  des strategies, or contre chaque marche.
  VERDICT FIXE D'AVANCE : la diversification « AIDE » (par etape) si la perte des jours communs (somme du portefeuille)
  est MOINS forte que celle de l'or seul les memes jours ET le % de temps sous le sommet baisse, sans que le total R
  baisse de plus de 20 % (total >= total or - 0,2 x |total or|).

POINT 5 - Interrupteur de pyramide causal. Regle GPT version A : B = panier tel que simule (2 renforts 0,5 V a +1 R et
  +1,5 R) ; A = la 1re position seule, memes prix (meme bid/ask), meme stop (le point mort a +1 R est pris avant que le
  1er renfort n'existe : stop = 1re entree, puis meilleure cloture - 1,5 R), donc meme sortie ; swaps de A recalcules
  sur le seul volume V. Delta_i = (PnL_B - PnL_A) / risque initial (R). bt_or : A = 1 position, B = 3 positions (meme
  sortie, banc_decompose_bt.paniers_possibles + rejoue avec le signal reel). Interrupteur : avant 20 paires fermees,
  joue B ; ensuite, a chaque entree, somme des 20 derniers Delta des paires FERMEES avant l'entree (ordre des sorties)
  < 0 -> joue A, sinon B. Politiques comparees chronologiquement : toujours A, toujours B, interrupteur, temoins
  « deux renforts fixes a risque reduit » : B x 1/3,25 (GPT : pire cas, chaque couche au stop initial 1 + 0,5x2 +
  0,5x2,5) et B x 1/2 (meme volume total que A) ; bt_or : B x 1/3 (meme volume) et B x 1/4,125 (pire cas : 1 +
  (0,25+0,667)/0,667 + (0,5+0,667)/0,667). Jeux : or H1 08/2022 -> 11/2026 (et ses moities, paniers ouverts avant /
  a partir du 01/10/2024) et or M15 du courtier (bt_or : EMA 192, heures M15 de banc_gpt_pyramide).
  Mesures : B - A apparie par moitie (somme, moyenne, % Delta > 0, t) ; par politique : total R, pire baisse (ordre des
  sorties) ; pertes evitees = somme des -Delta des paires jouees en A ou Delta < 0, gains manques = somme des Delta > 0
  joues en A ; nombre des 5 meilleurs paniers B (PnL_B) joues en A.
  VERDICT FIXE D'AVANCE : l'interrupteur « TIENT » s'il bat « toujours B » (total R) sur les deux moities H1 ET sur M15.

POINT 6 - Sens aleatoire de bt_or (reprise de banc_decompose_bt, graine 2211, 2000 tirages) : distribution du total R
  (moyenne, ecart-type, centiles 5/25/50/75/95), rang (centile parmi les tirages) de bt_or reel et de « toujours
  acheteur », avec (3 positions) et sans (1 position) renforts ; or H1 4 ans, ses moities, or M5 18 mois. Pas de verdict.

RESULTAT (execution du 23/11/2026, 9 s) : controles exacts (bt_or or M5 295 / +114,1 R ; bt_or H1 956 / +153,4 R ;
  A = B a 1e-15 pres pour les paniers GPT sans renfort ; moyenne du hasard H1 3 pos. +108,1 = banc_decompose_bt).
  4 : N'AIDE PAS, a aucune etape, pour les deux mecaniques. Index choisi : Nasdaq (bt_or), S&P (GPT). bt_or : la
    croissance s'effondre (or seul +122,1 R -> +41,9 avec indice + EUR, +35,6 avec argent ; -66 % a -71 %) et le temps
    sous le sommet ne baisse pas (88 % -> 89-91 %) ; jours communs -81 R contre -46 R pour l'or seul les memes jours.
    GPT A (fenetre principale) : +29,5 -> +24,8 R (-16 %, dans la tolerance), creux -11,5 -> -6,9, mais temps sous le
    sommet 73 % -> 79 % et jours communs -11,7 contre -8,3 pour l'or ; fenetre courte (BTC / ETH) : rien n'aide non
    plus (or + S&P + EUR : +18,0 contre +4,5, sous le sommet 78 % contre 84 %, mais jours communs -7,3 contre -6,6).
    Correlations des cours avec l'or 0,34-0,46 (argent 0,84) ; des resultats journaliers ~0 (argent bt_or 0,44).
  5 : NE TIENT PAS (GPT et bt_or). B - A apparie : GPT -1,7 R sur 2022-2024 (123 paires), +11,8 sur 2024-2026 (97),
    +12,3 sur M15 ; bt_or -12,6 puis +107,6, M15 +95,4. Interrupteur GPT : bat B sur 2022-2024 (+42,4 contre +33,1)
    mais pas sur 2024-2026 (+48,0 contre +49,4) ni M15 (+41,6 contre +48,5) ; bt_or : +2,0 contre -0,9, puis +122,2
    contre +154,2, M15 +102,3 contre +146,9. Temoins a risque reduit tres en dessous de B en R (B/3,25 : +25 R H1).
  6 : sens au hasard bt_or H1 3 pos. : moyenne +108,1 R (e-t 26,4 ; c5 +63, c50 +109, c95 +151) ; bt_or reel +153,4
    au centile 96 ; toujours acheteur +243,7 au-dessus de tous les tirages. 2022-2024 : bt_or -0,9 au centile 12.
Ecrit donnees/gpt_tour2b.csv. Usage : python3 banc_gpt_tour2b.py
"""
import os, time, contextlib, io, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_bt_regulier as BR
    import banc_jumeau as BJ
    import banc_gpt_pyramide as GP
    import banc_multi_marches as MM
    import banc_decompose_bt as DB

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
COUPE = pd.Timestamp("2024-10-01")
LIGNES = []


def ajoute(point, **kw):
    LIGNES.append(dict(point=point, **kw))


# ================================================================ POINT 4
def marches_m5():
    """nom -> (donnee M5, donnee M15, D1 de la regle GPT) ; memes sources que banc_multi_marches.jeux."""
    J = {}
    d = MM.m5_concat("xau_m5_2025a", "xau_m5_90k")
    J["or"] = (d, MM.params_d1(BR.charge("xau_d1_5k")))
    for nom, f, d1 in (("Nasdaq", None, BR.charge("nas_d1_5k")), ("S&P", "sp_m5_90k", BR.charge("sp_d1_5k")),
                       ("EUR/USD", "eur_m5_90k", MM.gj("eur")), ("argent", "xag_m5_90k", MM.gj("xag")),
                       ("BTC", "btc_m5_90k", MM.gj("btc")), ("ETH", "eth_m5_90k", MM.gj("eth"))):
        d = MM.m5_concat("nas_m5_2025a", "nas_m5_90k") if f is None else BR.charge(f)
        J[nom] = (d, MM.params_d1(d1))
    return J


def sous_sommet(x):
    cs = np.cumsum(np.r_[0.0, x.values])
    sous = (cs < np.maximum.accumulate(cs) - 1e-12)[1:]
    lg, cur = 0, 0
    for v in sous:
        cur = cur + 1 if v else 0
        lg = max(lg, cur)
    return 100 * sous.mean(), lg


def point4():
    J = marches_m5()
    SER, PX = {}, {}
    for nom, (d, D1) in J.items():
        Pb = BR.simule(d)
        Pg, _, _ = GP.simule_regle(MM.regroupe(d, 900), D1, sortie="A")
        SER[nom, "bt_or"], SER[nom, "GPT A"] = MM.journalier(Pb), MM.journalier(Pg)
        PX[nom] = d.groupby(pd.to_datetime(d.heure, unit="s").dt.floor("D")).cloture.last()
        if nom == "or":
            print("  controle bt_or or M5 : %d paniers %+.1f R (attendu 295 / +114,1)" % (len(Pb), Pb.g.sum()))
    deb = {n: pd.to_datetime(J[n][0].heure.iloc[0], unit="s").floor("D") for n in J}
    fin = pd.Timestamp("2026-11-11")
    a_long = max(deb[n] for n in ("or", "Nasdaq", "S&P", "EUR/USD", "argent"))
    a_court = max(deb.values())
    mi = a_long + (fin - a_long) / 2
    print("  fenetre principale %s -> %s (1re moitie jusqu'au %s) ; fenetre courte %s -> %s" % (
        a_long.date(), fin.date(), mi.date(), a_court.date(), fin.date()))
    # correlations (fenetre principale ; BTC / ETH sur la courte)
    R = pd.DataFrame({n: PX[n] for n in J}).pct_change()
    for meca in ("bt_or", "GPT A"):
        for n in J:
            if n == "or":
                continue
            a = a_court if n in ("BTC", "ETH") else a_long
            r = R[["or", n]].loc[a:fin].dropna()
            xo, xn = MM.sur(SER["or", meca], a, fin), MM.sur(SER[n, meca], a, fin)
            ajoute("4 correlations", mecanique=meca, marche=n, debut=a.date(), corr_cours=r["or"].corr(r[n]),
                   corr_resultats_jour=xo.corr(xn),
                   corr_resultats_mois=xo.groupby(xo.index.to_period("M")).sum().corr(xn.groupby(xn.index.to_period("M")).sum()))
    C = pd.DataFrame([l for l in LIGNES if l["point"] == "4 correlations"])
    print("  correlations avec l'or (cours journaliers / resultats journaliers / mensuels) :")
    print(C.pivot_table(index="marche", columns="mecanique", values=["corr_cours", "corr_resultats_jour", "corr_resultats_mois"]).round(2).to_string())
    print("\n  %-6s %-9s %-36s %4s %8s %7s %7s %8s %8s %7s %6s %6s %s" % (
        "meca", "fenetre", "portefeuille", "k", "total R", "creux", "%sous", "plus long", "j.comm.", "somme", "pire", "or ces j.", "AIDE ?"))
    for meca in ("bt_or", "GPT A"):
        tot1 = {n: MM.sur(SER[n, meca], a_long, mi).sum() for n in ("Nasdaq", "S&P")}
        idx = max(tot1, key=tot1.get)
        etapes = [["or"], ["or", idx, "EUR/USD"], ["or", idx, "EUR/USD", "argent"],
                  ["or", idx, "EUR/USD", "argent", "BTC"], ["or", idx, "EUR/USD", "argent", "BTC", "ETH"]]
        for fen, a in (("principale", a_long), ("courte", a_court)):
            X = pd.DataFrame({n: MM.sur(SER[n, meca], a, fin) for n in J})
            xo = X["or"]
            so_pct, so_lg = sous_sommet(xo)
            for et in etapes:
                if fen == "principale" and ("BTC" in et):
                    continue
                k = len(et)
                x = X[et].sum(1) / k
                if k > 1:
                    jc = (X[et] < 0).sum(1) >= 2
                else:
                    jc = xo < 0                    # or seul : ses propres jours perdants
                pct, lg = sous_sommet(x)
                s_jc, pire_jc, or_jc = x[jc].sum(), x[jc].min() if jc.any() else 0.0, xo[jc].sum()
                aide = (k > 1) and (s_jc > or_jc) and (pct < so_pct) and (x.sum() >= xo.sum() - 0.2 * abs(xo.sum()))
                nomp = " + ".join(et)
                print("  %-6s %-9s %-36s %4d %+8.1f %+7.1f %6.0f%% %6d j %8d %+7.1f %+6.1f %+8.1f %s" % (
                    meca, fen, nomp, k, x.sum(), MM.creux(x.values), pct, lg, jc.sum(), s_jc, pire_jc, or_jc,
                    ("AIDE" if aide else "n'aide pas") if k > 1 else "(reference, index choisi : %s, 1re moitie Nasdaq %+.1f / S&P %+.1f)" % (idx, tot1["Nasdaq"], tot1["S&P"])))
                ajoute("4 diversification", mecanique=meca, fenetre=fen, debut=a.date(), fin=fin.date(), portefeuille=nomp,
                       k=k, index_choisi=idx, total_R=x.sum(), pire_baisse_R=MM.creux(x.values), pct_sous_sommet=pct,
                       plus_long_sous_sommet_j=lg, jours_communs=int(jc.sum()), somme_jours_communs=s_jc,
                       pire_jour_commun=pire_jc, or_seul_memes_jours=or_jc, or_seul_total=xo.sum(),
                       or_seul_pct_sous_sommet=so_pct, verdict=("AIDE" if aide else "n'aide pas") if k > 1 else "reference")


# ================================================================ POINT 5
def paires_gpt(d, D1, eo):
    """Paniers de la regle GPT version A (B, 2 renforts) et la 1re position seule (A), memes prix, meme sortie."""
    P, _, _ = GP.simule_regle(d, D1, "A", False, entree_ouverture=eo)
    t, c = d.heure.values, d.cloture.values
    jour = t // 86400
    tr = np.r_[False, jour[1:] != jour[:-1]]
    nuit = np.where(tr, np.r_[0.0, c[:-1]] * GP.SWAP * np.r_[0, np.diff(jour)], 0.0)
    cum = np.cumsum(nuit)
    i0, i1 = np.searchsorted(t, P.t0.values), np.searchsorted(t, P.t1.values)
    swA = (cum[i1] - cum[i0]) / P.R.values
    gA = P.s.values * (P.px1.values - P.e0.values) / P.R.values - swA
    ok0 = P.renforts.values == 0
    print("    controle A = B quand aucun renfort : %d paniers, ecart max %.2e R" % (ok0.sum(), np.abs(gA[ok0] - P.g.values[ok0]).max()))
    return pd.DataFrame(dict(t0=P.t0.values, t1=P.t1.values, gA=gA, gB=P.g.values))


def paires_bt(d, kw):
    B = DB.paniers_possibles(d, **kw)
    O, X, g3, g1 = DB.rejoue(B, B["signal"][None, :])
    o = O[0]
    t = B["t"]
    return pd.DataFrame(dict(t0=t[B["ik"][o]], t1=t[X[0][o]], gA=g1[0][o], gB=g3[0][o])), B


def interrupteur(Q):
    Q = Q.sort_values("t0", kind="stable").reset_index(drop=True)
    dl = (Q.gB - Q.gA).values
    ordre = np.argsort(Q.t1.values, kind="stable")
    t1s, dls = Q.t1.values[ordre], dl[ordre]
    joue = np.ones(len(Q), bool)        # True = B
    for i, t0 in enumerate(Q.t0.values):
        n = np.searchsorted(t1s, t0, "right")       # paires fermees avant (ou a) l'entree
        if n >= 20 and dls[n - 20:n].sum() < 0:
            joue[i] = False
    Q["dl"], Q["joueB"] = dl, joue
    Q["gS"] = np.where(joue, Q.gB, Q.gA)
    return Q


def creux_sorties(Q, col):
    x = Q.sort_values("t1", kind="stable")[col].values
    return MM.creux(x)


def point5():
    dh = BR.charge("xau_h1_50k")
    dh = dh[dh.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
    m15 = BR.charge("xau_m15_50k")
    D1 = GP.params_d1()
    JX = {}
    print("  regle GPT :")
    JX["GPT A", "H1"] = paires_gpt(dh, D1, True)
    JX["GPT A", "M15"] = paires_gpt(m15, D1, False)
    print("  bt_or :")
    JX["bt_or", "H1"], BH = paires_bt(dh, dict(span=48, heures=BJ.H_H1, debut=60))
    JX["bt_or", "M15"], _ = paires_bt(m15, dict(span=192, heures=GP.H_M15, debut=200))
    print("    controle bt_or H1 : %d paniers %+.1f R (attendu 956 / +153,4)" % (len(JX["bt_or", "H1"]), JX["bt_or", "H1"].gB.sum()))
    TEM = {"GPT A": (("temoin B/3,25 (pire cas)", 1 / 3.25), ("temoin B/2 (meme volume)", 0.5)),
           "bt_or": (("temoin B/4,125 (pire cas)", 1 / 4.125), ("temoin B/3 (meme volume)", 1 / 3))}
    verd = {}
    for meca in ("GPT A", "bt_or"):
        for jeu in ("H1", "M15"):
            Q = interrupteur(JX[meca, jeu])
            fen = [(jeu, np.ones(len(Q), bool))]
            if jeu == "H1":
                t0 = pd.to_datetime(Q.t0, unit="s")
                fen += [("H1 2022-08->2024-09", (t0 < COUPE).values), ("H1 2024-10->2026-11", (t0 >= COUPE).values)]
            for nomf, m in fen:
                q = Q[m]
                dl = q.dl
                tt = dl.mean() / dl.std() * np.sqrt(len(dl)) if dl.std() > 0 else 0
                top5 = q.nlargest(5, "gB")
                enA = ~q.joueB
                r = dict(mecanique=meca, jeu=nomf, paires=len(q), B_moins_A=dl.sum(), delta_moyen=dl.mean(),
                         pct_delta_pos=100 * (dl > 0).mean(), t_delta=tt,
                         toujours_A=q.gA.sum(), toujours_B=q.gB.sum(), interrupteur=q.gS.sum(),
                         creux_A=creux_sorties(q, "gA"), creux_B=creux_sorties(q, "gB"), creux_inter=creux_sorties(q, "gS"),
                         joues_A=int(enA.sum()), pertes_evitees=-dl[enA & (dl < 0)].sum(), gains_manques=dl[enA & (dl > 0)].sum(),
                         top5_B_rates=int((~top5.joueB).sum()), inter_bat_B=bool(q.gS.sum() > q.gB.sum()))
                for nt, f in TEM[meca]:
                    r[nt] = f * q.gB.sum()
                    r["creux " + nt] = f * creux_sorties(q, "gB")
                ajoute("5 interrupteur", **r)
                if nomf != "H1":
                    verd.setdefault(meca, []).append((nomf, r["inter_bat_B"]))
    T = pd.DataFrame([l for l in LIGNES if l["point"] == "5 interrupteur"])
    cols = ["mecanique", "jeu", "paires", "B_moins_A", "delta_moyen", "pct_delta_pos", "t_delta", "toujours_A", "toujours_B",
            "interrupteur", "joues_A", "pertes_evitees", "gains_manques", "top5_B_rates", "creux_A", "creux_B", "creux_inter"]
    print(T[cols].round(2).to_string(index=False))
    tc = [c for c in T.columns if c.startswith("temoin") or c.startswith("creux temoin")]
    print(T[["mecanique", "jeu"] + tc].round(2).to_string(index=False))
    for meca, L in verd.items():
        v = "TIENT" if all(b for _, b in L) else "NE TIENT PAS"
        print("  VERDICT interrupteur %s : %s (%s)" % (meca, v, " ; ".join("%s %s" % (n, "bat B" if b else "ne bat pas B") for n, b in L)))
        ajoute("5 verdict", mecanique=meca, verdict=v)
    return dh, BH


# ================================================================ POINT 6
def point6(dh, BH):
    a5, b5 = BR.charge("xau_m5_2025a"), BR.charge("xau_m5_90k")
    d5 = pd.concat([a5, b5[b5.heure > a5.heure.iloc[-1]]], ignore_index=True)
    B5 = DB.paniers_possibles(d5)
    print("  %-22s %-5s %8s %7s %7s %7s %7s %7s %7s | %8s %6s | %8s %6s" % (
        "jeu", "pos.", "moyenne", "e-t", "c5", "c25", "c50", "c75", "c95", "bt_or", "rang", "achat", "rang"))
    for nom, B in (("or H1", BH), ("or M5", B5)):
        K = len(B["ik"])
        per = pd.to_datetime(B["t"], unit="s").to_period("M")
        cal = per.unique(); ms = cal.get_indexer(per)
        rng = np.random.default_rng(DB.GRAINE)
        S = {"a": B["signal"][None, :], "e": np.zeros((1, K), int), "c": rng.integers(0, 2, size=(DB.NT, K))}
        Rr = {k: DB.rejoue(B, v) for k, v in S.items()}
        t_ouv = B["t"][B["ik"]]
        sous = [(nom, np.ones(K, bool))]
        if nom == "or H1":
            c0 = COUPE.timestamp()
            sous += [("or H1 2022-08->2024-09", t_ouv < c0), ("or H1 2024-10->2026-11", t_ouv >= c0)]
        for jn, m in sous:
            for npos, j in ((3, 2), (1, 3)):
                V = {k: DB.mesures(Rr[k][0], Rr[k][1], Rr[k][j], B, m, ms, len(cal))["tot"] for k in Rr}
                c = V["c"]; a, e = V["a"][0], V["e"][0]
                q = np.percentile(c, [5, 25, 50, 75, 95])
                ra, re_ = 100 * (c < a).mean(), 100 * (c < e).mean()
                print("  %-22s %-5d %+8.1f %7.1f %+7.1f %+7.1f %+7.1f %+7.1f %+7.1f | %+8.1f %5.1f%% | %+8.1f %5.1f%%" % (
                    jn, npos, c.mean(), c.std(), *q, a, ra, e, re_))
                ajoute("6 sens aleatoire", jeu=jn, positions=npos, tirages=DB.NT, moyenne=c.mean(), ecart_type=c.std(),
                       c5=q[0], c25=q[1], c50=q[2], c75=q[3], c95=q[4], bt_or_reel=a, rang_bt_or_pct=ra,
                       toujours_acheteur=e, rang_achat_pct=re_, part_tirages_pos=(c > 0).mean())


if __name__ == "__main__":
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print("=== POINT 4 : diversification a risque global constant")
    point4()
    print("  (%.0f s)\n=== POINT 5 : interrupteur de pyramide" % (time.time() - T00))
    dh, BH = point5()
    print("  (%.0f s)\n=== POINT 6 : sens aleatoire de bt_or (%d tirages, graine %d ; rang = %% des tirages sous la valeur)"
          % (time.time() - T00, DB.NT, DB.GRAINE))
    point6(dh, BH)
    out = pd.DataFrame(LIGNES)
    out.round(4).to_csv(os.path.join(ICI, "donnees", "gpt_tour2b.csv"), index=False)
    print("Duree %.0f s ; ecrit donnees/gpt_tour2b.csv (%d lignes)" % (time.time() - T00, len(out)))
