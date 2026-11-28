"""Banc FQ : « plus de paniers bt_or » -- peut-on augmenter la FREQUENCE de la mecanique bt_or sur l'or (XAUUSD, compte
DEMO, aucun ordre) sans perdre l'avantage par unite de risque ?
Mecanique bt_or (banc_bt_regulier.simule) : sens = cloture contre l'EMA 2 jours ; entree a la cloture des bougies aux
heures serveur fixes ; ajouts dans le sens du prix tous les 0,25 ATR jour 20 j (veille), niveau saute au-dela d'un
demi-pas, 3 positions au plus ; sortie de TOUT le panier au recul de 0,667 ATR depuis le meilleur prix. Spread reel
(achat cloture + spread, vente cloture - spread ; sortie au niveau du stop, vente declenchee par haut + spread),
sans fuite : stop avec le meilleur prix d'AVANT la bougie, puis meilleur prix, puis ajouts a la cloture, puis entrees.
GRILLE FIXEE D'AVANCE (ecrite avant l'execution, rien d'ajoute ensuite), N = 22, reference = H7/N1/std = bt_or actuel.
 (a) heures d'entree (M5 : bougie hh:00 ; H1 : bougie qui FERME a hh:00, c.-a-d. ouverte a hh-1, comme banc_jumeau.H_H1) :
     H7  = les 7 actuelles (M5 03:05, 08:00, 08:30, 12:00, 15:45, 16:00, 16:30 ; H1 = BJ.H_H1 = bougies de 2,7,11,14,15 h)
     H1h = toutes les heures pleines (24/jour) ; H2h = heures paires ; H4h = 0,4,8,12,16,20 h ;
     LNY = seance Londres+NY, chaque heure pleine de 8 h a 20 h serveur inclus (13/jour) ;
     REP = H7 + reprise immediate : quand un panier se ferme, nouveau panier du meme cote a la cloture de la bougie
           SUIVANTE si le sens (cloture contre EMA) est toujours le meme (sinon on attend l'heure fixe suivante).
 (b) paniers simultanes du meme cote : N1 (actuel), N2, N3 (nouveau panier independant a l'heure d'entree suivante
     meme si un panier de ce cote est ouvert ; chacun a son pas, son stop suiveur et ses 3 positions).
 (c) echelle de temps : std = EMA 2 j (576 M5 / 48 H1), pas 0,25 / stop 0,667 ATR jour ;
     rap = EMA 12 h (144 M5 / 12 H1), pas 0,125 / stop 0,333 ATR jour ;
     len = EMA 5 j (1440 M5 / 120 H1), pas 0,5 / stop 1,333 ATR jour.
 Pas de croisement complet : (a) x (b) a l'echelle std (18) ; puis (c) rap et len avec H7 et H1h, N1 (4).
Donnees : or M5 du courtier xau_m5_2025a + xau_m5_90k (06/2025 -> 11/2026) ; or H1 xau_h1_50k depuis le 01/08/2022.
Unites : 1 R = perte d'UNE position au stop initial de SON panier (risque constant, comme le robot). Une variante
« rapide » a donc un R plus petit en $ : la comparaison se fait a RISQUE EGAL.
Courbe JOURNALIERE marquee a la derniere cloture du jour (gain latent compris, achat au bid, vente a l'ask).
Mesures par variante et par jeu : paniers/mois, R total brut, R moyen par panier (t), positions/panier, correlation
journaliere avec bt_or ; A RISQUE EGAL (facteur fa = pire baisse journaliere de bt_or / pire baisse de la variante,
sur tout le jeu) : total, gain / pire baisse, Sharpe journalier annualise (x racine 252), % de mois negatifs, moities ;
« rend./an par pire baisse » = (gain annualise) / pire baisse (= gain/pire baisse divise par le nombre d'annees).
Walk-forward glissant (M5 6 -> 1 mois ; H1 12 -> 3 mois) : choix de la variante au meilleur gain/pire baisse
d'apprentissage, fa appris sur l'apprentissage ; « meilleur hors echantillon » = gain/pire baisse > bt_or ET total
>= bt_or sur les memes mois de test.
Essais multiples : reality check de White (banc_bt_regulier.white : bootstrap stationnaire de JOURS apparies, blocs
moyens 5 jours, 2000 tirages, graine 17) sur la difference journaliere fa x variante - bt_or (max des 21) -> p corrige
par jeu ; p brut par variante (meme bootstrap).
Verdict fixe d'avance : TIENT = la variante du walk-forward meilleure que bt_or hors echantillon sur M5 ET H1, et
p corrige < 0,10 sur chaque jeu ; PRESQUE = du bon cote sur les deux jeux mais p >= 0,10 ; sinon NE TIENT PAS.
Controle : H7/N1/std redonne banc_bt_regulier.simule panier par panier.
Reutilise banc_bt_regulier (charge, simule, boot, white) et banc_jumeau (mesure, creux, H_H1).
RESULTAT (execution du 21/11/2026, 3 s, 2000 tirages, rien de reduit) : verdict NE TIENT PAS. Controles exacts
  (M5 295 paniers / +114,1 R ; H1 956 / +153,4 R).
  bt_or : gain/creux M5 6,34 (an/creux 4,54), H1 3,66 (0,86). Plus de paniers multiplie surtout la MEME exposition :
  correlation journaliere 0,92-0,99 avec bt_or pour toutes les variantes « std » ; le facteur de risque egal les
  ramene presque au meme total. Meilleur que bt_or sur les deux jeux (tout l'echantillon) : H7/N3, REP/N1, REP/N2,
  REP/N3, de 1 a 31 % seulement. Seules les echelles rap/len sont peu correlees (0,5-0,75) mais rap s'effondre en H1
  et len en M5. Walk-forward : M5 1,17 contre 3,51 ; H1 5,62 contre 7,67 -> mauvais cote sur les deux.
  Reality check : p corrige M5 0,827, H1 0,271.
Ecrit donnees/freq.csv. Usage : python3 banc_freq.py"""
import os, time, warnings
from multiprocessing import Pool
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_bt_regulier as BR
import banc_jumeau as BJ

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
MAXP = BR.MAXP
HEURES = {"H7": None, "H1h": list(range(24)), "H2h": list(range(0, 24, 2)), "H4h": list(range(0, 24, 4)),
          "LNY": list(range(8, 21)), "REP": None}
ECH = {"std": (2.0, 0.25, BR.STOP), "rap": (0.5, 0.125, 0.3333), "len": (5.0, 0.5, 1.3333)}   # EMA en jours, pas, stop
VAR = [(h, n, "std") for h in HEURES for n in (1, 2, 3)] + [(h, 1, e) for e in ("rap", "len") for h in ("H7", "H1h")]
NOMV = ["%s/N%d/%s" % v for v in VAR]
NV = len(VAR)
REF = NOMV.index("H7/N1/std")


def heures_de(h, m5):
    if h in ("H7", "REP"):
        return BR.H_M5 if m5 else BJ.H_H1
    return {(x, 0) for x in HEURES[h]} if m5 else {((x - 1) % 24, 0) for x in HEURES[h]}


def simule_v(d, m5, h, nmax, ech, debut):
    """Une variante. Rend les paniers (DataFrame) et la courbe journaliere marquee (Series, R cumules)."""
    c, hi, lo, sp, t = (d[x].values for x in ("cloture", "haut", "bas", "sp", "heure"))
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ej, pas_k, stop_k = ECH[ech]
    span = int(round(ej * (288 if m5 else 24)))
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    fin_j = np.r_[jour[1:] != jour[:-1], True]
    H = heures_de(h, m5); entree_h = np.array([(a, b) in H for a, b in zip(hh, mm)])
    rep = h == "REP"
    P, EQ, JO = [], [], []
    ouvert = {1: [], -1: []}
    attente = {1: False, -1: False}
    acc = 0.0
    for i in range(debut, len(c)):
        ferme = {1: False, -1: False}
        for s in (1, -1):
            garde = []
            for p in ouvert[s]:
                niveau = p["meilleur"] - s * p["stop"]
                if (lo[i] <= niveau) if s > 0 else (hi[i] + sp[i] >= niveau):
                    g = sum(s * (niveau - e) for e in p["e"]) / p["stop"]
                    acc += g
                    P.append((t[p["i"]], t[i], s, g, len(p["e"])))
                    ferme[s] = True
                    continue
                p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
                while len(p["e"]) < MAXP and s * (c[i] - p["prochain"]) >= 0:
                    if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                        p["e"].append(c[i] + (sp[i] if s > 0 else -sp[i]))
                    p["prochain"] += s * p["pas"]
                garde.append(p)
            ouvert[s] = garde
        if atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if (entree_h[i] or (rep and attente[s])) and len(ouvert[s]) < nmax:
                ouvert[s].append({"i": i, "e": [c[i] + (sp[i] if s > 0 else -sp[i])], "meilleur": c[i],
                                  "stop": stop_k * atr[i], "pas": pas_k * atr[i], "prochain": c[i] + s * pas_k * atr[i]})
        attente = ferme                           # reprise : seulement a la bougie qui suit la fermeture
        if fin_j[i]:
            lat = 0.0
            for s in (1, -1):
                x = c[i] if s > 0 else c[i] + sp[i]
                for p in ouvert[s]:
                    lat += sum(s * (x - e) for e in p["e"]) / p["stop"]
            EQ.append(acc + lat); JO.append(jour[i])
    P = pd.DataFrame(P, columns=["t0", "t1", "s", "g", "n"]).sort_values(["t0", "s"], kind="stable").reset_index(drop=True)
    return P, pd.Series(EQ, pd.to_datetime(np.array(JO) * 86400, unit="s"))


DATA = {}


def tache(arg):
    jeu, v = arg
    d, m5, debut = DATA[jeu]
    h, n, e = VAR[v]
    return simule_v(d, m5, h, n, e, debut)


shj = lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0.0


def analyse(nom, d, m5, debut, RES, L_app, L_test):
    ref = BR.simule(d, **({} if m5 else dict(span=48, heures=BJ.H_H1, debut=60)))
    P0 = RES[REF][0]
    r0 = ref.sort_values(["t0", "s"], kind="stable")
    ok = len(r0) == len(P0) and np.allclose(r0.g.values, P0.g.values)
    E = pd.DataFrame({v: RES[v][1] for v in range(NV)}).ffill().fillna(0.0)
    X = E.diff(); X.iloc[0] = E.iloc[0]
    mois = X.index.to_period("M"); nm = len(mois.unique())
    ans = (X.index[-1] - X.index[0]).days / 365.25
    print("\n=== %s : %s -> %s, %d jours, %d mois (%.2f ans). Controle reference = banc_bt_regulier.simule (%d paniers, %+.1f R) : %s"
          % (nom, X.index[0].date(), X.index[-1].date(), len(X), nm, ans, len(ref), ref.g.sum(), ok))
    b = BJ.mesure(X[REF], mois)
    rows = []
    for v in range(NV):
        P = RES[v][0]; a = BJ.mesure(X[v], mois)
        fa = b["cr"] / a["cr"] if a["cr"] < 0 else 1.0
        rows.append(dict(jeu=nom, variante=NOMV[v], heures=VAR[v][0], paniers_simult=VAR[v][1], echelle=VAR[v][2],
                         paniers=len(P), paniers_mois=len(P) / nm, pos_moy=P.n.mean(), total_R_brut=a["tot"],
                         R_moy_panier=P.g.mean(), t_panier=BR.tst(P.g), creux_R_brut=a["cr"], facteur=fa,
                         total_R_eg=fa * a["tot"], creux_R_eg=fa * a["cr"], gain_creux=a["rap"], rend_an_creux=a["rap"] / ans,
                         sharpe=shj(X[v]), mois_neg=a["mneg"], mois=a["nm"], pct_mois_neg=100 * a["mneg"] / a["nm"],
                         h1_R_eg=fa * a["h1"], h2_R_eg=fa * a["h2"], corr_bt_or=X[v].corr(X[REF])))
    T = pd.DataFrame(rows)
    # ------------------------------------------------ reality check de White sur fa x variante - bt_or (jours apparies)
    autres = [v for v in range(NV) if v != REF]
    Dm = np.column_stack([T.facteur[v] * X[v].values - X[REF].values for v in autres])
    kb, pc = BR.white(Dm)
    I = BR.boot(len(Dm)); mu = Dm.mean(0)
    Mb = np.stack([Dm[ii].mean(0) for ii in I]) - mu                   # B x 21, centre
    T["p_brut"] = np.nan
    T.loc[autres, "p_brut"] = (Mb >= mu).mean(0)
    T["p_corrige_jeu"] = pc; T["rc_meilleur"] = NOMV[autres[kb]]
    # ------------------------------------------------ walk-forward
    MO = mois.unique()
    oos, oosb, ch = [], [], []
    for i0 in range(L_app, len(MO), L_test):
        app = (mois >= MO[i0 - L_app]) & (mois <= MO[i0 - 1]); te = (mois >= MO[i0]) & (mois <= MO[min(i0 + L_test, len(MO)) - 1])
        M = [BJ.mesure(X[v][app], mois[app]) for v in range(NV)]
        v = max(range(NV), key=lambda k: (M[k]["rap"], k == REF))
        fa = M[REF]["cr"] / M[v]["cr"] if M[v]["cr"] < 0 else 1.0
        oos.append(fa * X[v][te]); oosb.append(X[REF][te]); ch.append(NOMV[v])
    o, ob = pd.concat(oos), pd.concat(oosb); mo = o.index.to_period("M")
    wa, wb = BJ.mesure(o, mo), BJ.mesure(ob, mo)
    wf_ok = wa["rap"] > wb["rap"] + 1e-9 and wa["tot"] >= wb["tot"] - 1e-9
    fq = pd.Series(ch).value_counts()
    T["wf_ok_jeu"] = wf_ok
    # ------------------------------------------------ affichage
    print("%-14s %6s %4s %7s %6s %5s %5s %7s %6s %6s %5s %5s %5s %13s %5s" % (
        "variante", "pan/m", "pos", "totR", "R/pan", "t", "fa", "totR eg", "g/cr", "an/cr", "Shrp", "%m<0", "corr", "moities eg", "pbrut"))
    for _, r in T.sort_values("gain_creux", ascending=False).iterrows():
        print("%-14s %6.1f %4.2f %+7.1f %+6.2f %+5.1f %5.2f %+7.1f %6.2f %6.2f %5.2f %5.0f %5.2f %+6.1f/%+6.1f %5.3f%s" % (
            r.variante, r.paniers_mois, r.pos_moy, r.total_R_brut, r.R_moy_panier, r.t_panier, r.facteur, r.total_R_eg,
            r.gain_creux, r.rend_an_creux, r.sharpe, r.pct_mois_neg, r.corr_bt_or, r.h1_R_eg, r.h2_R_eg, r.p_brut,
            "  <- REF" if r.variante == NOMV[REF] else ""))
    print("Reality check (max des %d, fa x variante - bt_or par jour) : meilleur %s, p corrige %.3f" % (len(autres), NOMV[autres[kb]], pc))
    print("Walk-forward %d -> %d mois, %d fenetres (%s -> %s) ; choix : %s" % (L_app, L_test, len(ch), o.index[0].date(), o.index[-1].date(),
          ", ".join("%s %d" % (k, v) for k, v in fq.head(6).items())))
    for lab, z, s_ in (("choisi (fa appris)", wa, o), ("bt_or actuel", wb, ob)):
        print("  %-19s total %+6.1f R  mois<0 %2d/%d  creux %+5.1f R  gain/creux %5.2f  Sharpe %5.2f" % (
            lab, z["tot"], z["mneg"], z["nm"], z["cr"], z["rap"], shj(s_)))
    print("  -> meilleur que bt_or hors echantillon : %s" % wf_ok)
    W = pd.DataFrame([dict(jeu=nom, variante="WF choisi", total_R_eg=wa["tot"], creux_R_eg=wa["cr"], gain_creux=wa["rap"],
                           sharpe=shj(o), mois_neg=wa["mneg"], mois=wa["nm"], wf_ok_jeu=wf_ok, p_corrige_jeu=pc,
                           rc_meilleur=", ".join("%s %d" % (k, v) for k, v in fq.items())),
                      dict(jeu=nom, variante="WF bt_or", total_R_eg=wb["tot"], creux_R_eg=wb["cr"], gain_creux=wb["rap"],
                           sharpe=shj(ob), mois_neg=wb["mneg"], mois=wb["nm"], wf_ok_jeu=wf_ok, p_corrige_jeu=pc)])
    return T, W, dict(wf_ok=wf_ok, p=pc, ctrl=ok, wa=wa, wb=wb)


if __name__ == "__main__":
    a5, b5 = BR.charge("xau_m5_2025a"), BR.charge("xau_m5_90k")
    d5 = pd.concat([a5, b5[b5.heure > a5.heure.iloc[-1]]], ignore_index=True)
    dh = BR.charge("xau_h1_50k")
    dh = dh[dh.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
    DATA["or M5"] = (d5, True, 600); DATA["or H1"] = (dh, False, 60)
    print("Grille fixee : %d variantes ; reference %s. Simulation en parallele (4 processus)." % (NV, NOMV[REF]))
    with Pool(4) as pool:
        out = pool.map(tache, [(j, v) for j in DATA for v in range(NV)])
    print("Simulations : %.0f s" % (time.time() - T00))
    R5 = out[:NV]; RH = out[NV:]
    T5, W5, S5 = analyse("or M5", d5, True, 600, R5, 6, 1)
    TH, WH, SH = analyse("or H1", dh, False, 60, RH, 12, 3)
    T = pd.concat([T5, W5, TH, WH], ignore_index=True)
    T.round(4).to_csv(os.path.join(ICI, "donnees", "freq.csv"), index=False)
    A, B = T5.set_index("variante"), TH.set_index("variante")
    deux = (A.gain_creux > A.gain_creux[NOMV[REF]]) & (B.gain_creux > B.gain_creux[NOMV[REF]])
    print("\n=== Synthese")
    print("gain/pire baisse > bt_or sur M5 ET H1 (tout l'echantillon) : %s" % (", ".join(deux[deux].index) or "aucune"))
    wf2 = S5["wf_ok"] and SH["wf_ok"]
    v = "TIENT" if wf2 and S5["p"] < 0.10 and SH["p"] < 0.10 else ("PRESQUE" if wf2 else "NE TIENT PAS")
    print("Walk-forward meilleur que bt_or : M5 %s, H1 %s ; p corrige M5 %.3f, H1 %.3f ; controles %s/%s"
          % (S5["wf_ok"], SH["wf_ok"], S5["p"], SH["p"], S5["ctrl"], SH["ctrl"]))
    print("Verdict (fixe d'avance) : %s.  Duree totale %.0f s. Ecrit donnees/freq.csv (%d lignes)." % (v, time.time() - T00, len(T)))
