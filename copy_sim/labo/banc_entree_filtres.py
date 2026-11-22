"""Banc ENTREE-FILTRES : bt_or doit mieux entrer en position, pistes 3 et 4 (PRIORITES 22/11 ; compte demo seulement).
Mecanique bt_or INCHANGEE (banc_bt_regulier.simule) : heures fixes, sens = cloture contre EMA 2 jours, un panier par
cote, ajouts tous les 0,25 ATR (3 positions), sortie de tout au recul de 0,667 ATR depuis le meilleur prix, spread reel.
On ajoute seulement des FILTRES d'entree : a une heure fixe, si le filtre dit non, pas de panier.
Methode exacte de banc_decompose_bt : chaque panier possible (heure d'entree x sens) est precalcule (sortie, gain 3 pos.,
MAE de la 1re position, marques journalieres du gain latent) puis la regle de blocage est rejouee pour chaque suite de sens.
Fond et volatilite lus sur le fichier D1 du courtier (xau_d1_5k, depuis 2018), JOUR PRECEDENT COMPLET seulement (sans
fuite) : C = cloture J-1, MM20 / MM50 = moyennes des clotures, pente20 = MM20(J-1) - MM20(J-6), ATRn = moyenne de n TR.
Heure serveur verifiee sur les donnees : pic de volatilite des chiffres US a 15:30 serveur ete comme hiver, ouverture
New York 16:30 serveur, 1re bougie du lundi 01:00 -> serveur = UTC+2 / UTC+3 = Paris + 1 h toute l'annee. Donc les heures
bt_or 08:00 / 08:30 / 12:00 serveur = 06:00 / 06:30 / 10:00 a Londres (avant et debut de seance), 15:45 / 16:00 / 16:30
= 08:45 / 09:00 / 09:30 a New York (chiffres US puis ouverture). En H1 (bougie h, decision a sa cloture h+1) :
03:05 -> 2 h ; 08:00/08:30 -> 7 h ; 12:00 -> 11 h ; 15:45/16:00 -> 14 h ; 16:30 -> 15 h (banc_jumeau.H_H1).
GRILLE FIXEE AVANT EXECUTION, N = 17 variantes candidates (memes regles sur H1 et M5) :
  sens EMA 2 j + accord du fond : F20 (achat si C > MM20, vente si C < MM20), F50 (idem MM50), FP20 (pente20 > 0 / < 0) ;
  fond seul (sens = tendance journaliere, plus d'EMA 2 j) : D20, D50, DP20 ;
  toujours acheteur + filtre de fond (achat seulement si fond haussier, sinon rien) : A20, A50, AP20 ;
  volatilite (sens EMA 2 j) : V5_20 (ATR5 > ATR20), V20_100 (ATR20 > ATR100) ;
  heure (sens EMA 2 j) : HLON (08:00, 08:30, 12:00 serveur ; H1 7 h, 11 h), HNY (15:45, 16:00, 16:30 ; H1 14 h, 15 h),
    H-0305 (toutes sauf 03:05 ; H1 sans 2 h) ;
  3 combinaisons : F50+H-0305, FP20+V5_20, A50+V20_100.
  References (hors N) : bt_or, sens au hasard aux instants bt_or, toujours acheteur + pyramide (ACH).
Mesures : paniers, total R brut (gain au jour de sortie, panier jamais sorti non compte), R/panier, courbe JOURNALIERE
marquee (gain latent a la cloture de la derniere bougie du jour) -> pire baisse ; fa = pire baisse bt_or / pire baisse
variante, total a risque egal = total x fa (tout l'echantillon ; en walk-forward fa appris sur l'apprentissage).
Qualite d'entree : MAE de la 1re position en R (depuis son prix d'entree spread compris, bougies suivantes jusqu'a la
sortie, niveau de sortie sur la bougie de sortie), mediane et 75e centile ; % stop initial = MAE >= 1 R (perte de 1 R
avant tout gain de 1 R : une fois +1 R atteint le suiveur interdit -1 R).
Contre le hasard : 2000 tirages par variante (graine 2211), sens tire au sort AUX MEMES INSTANTS (ceux ou la variante
donne un sens), blocage compris -> p = (1 + nb tirages >= reel) / 2001 ; ecart avec toujours acheteur aux memes instants.
Moities H1 par date d'ouverture : 2022-08 -> 2024-09 et 2024-10 -> 2026-11.
Walk-forward : H1 12 mois / 3 mois, M5 6 / 1 ; choix au meilleur gain / pire baisse d'apprentissage parmi les 17 ;
mise fa apprise ; compare sur les memes mois a bt_or (tel quel) et a ACH (a son fa appris).
Essais multiples : White (banc_bt_regulier.white) sur jours x 17 (serie journaliere x fa - bt_or) -> p corrige par jeu.
VERDICT FIXE D'AVANCE : TIENT = la variante choisie en walk-forward bat bt_or ET ACH hors echantillon a risque egal sur
H1 ET M5, p White < 0,10 sur H1, p contre le sens au hasard < 0,10 sur CHACUNE des moities H1 (variante la plus choisie
en walk-forward H1), et MAE mediane ou % stops initiaux meilleurs que bt_or (H1) ; PRESQUE = walk-forward du bon cote sur
les deux jeux mais un autre critere manque ; sinon NE TIENT PAS.
Controle : la ligne bt_or redonne +153,4 R / 956 paniers en H1 (et +114,1 R / 295 en M5), somme de la courbe marquee =
total des paniers sortis.
RESULTAT (execution du 22/11/2026, 13 s) : verdict NE TIENT PAS. Controles exacts (H1 956 / +153,4 R ; M5 295 /
  +114,1 R ; courbe marquee = paniers a 1e-13). Pire baisse marquee bt_or : H1 -42,2 R, M5 -18,2 R.
  H1 (risque egal) : bt_or +153,4 ; ACH +243,7 brut / +425,2 ; A50 +184,1 / +451,8 (meilleure, White p 0,010) ;
    F50 +162,3 / +248,4 ; F50+H-0305 +153,6 / +259,5 ; D50 +179,8 / +227,0 ; HLON +158,7 / +194,6.
  Walk-forward H1 12/3 (2023-08 -> 2026-11) : choix +241,5 R, bt_or +179,0, ACH +319,6 -> bat bt_or, PAS l'achat seul.
  Walk-forward M5 6/1 (2025-12 -> 2026-11) : choix +90,7, bt_or +62,5, ACH +30,2 -> bat les deux ; White M5 p 0,103.
  1re moitie H1 : aucune variante a sens EMA 2 j ne bat le hasard (p 0,34-0,91) ; seules les variantes acheteuses
  (p <= 0,007) et D50 (0,068) : la tendance de l'or, pas une meilleure entree. MAE mediane 0,49-0,52 R partout (bt_or
  0,51) : les filtres choisissent des periodes, ils n'ameliorent pas l'entree ; % stop initial tres rare (1-5 %, le
  suiveur part au premier mouvement), HLON 0,7 % et F50+H-0305 1,0 % contre 1,9 % pour bt_or.
Ecrit donnees/entree_filtres.csv. Usage : python3 banc_entree_filtres.py
"""
import os, time, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_bt_regulier as BR
import banc_jumeau as BJ

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
NT, GRAINE = 2000, 2211
COUPE = pd.Timestamp("2024-10-01").timestamp()
CAND = ["F20", "F50", "FP20", "D20", "D50", "DP20", "A20", "A50", "AP20", "V5_20", "V20_100", "HLON", "HNY", "H-0305",
        "F50+H-0305", "FP20+V5_20", "A50+V20_100"]


def fond_d1():
    d = pd.read_csv(os.path.join(BR.DON, "xau_d1_5k.csv.gz"))
    j = pd.DataFrame({"jour": d.heure // 86400, "C": d.cloture})
    tr = np.maximum(d.haut - d.bas, np.maximum((d.haut - d.cloture.shift(1)).abs(), (d.bas - d.cloture.shift(1)).abs()))
    j["MM20"], j["MM50"] = d.cloture.rolling(20).mean(), d.cloture.rolling(50).mean()
    j["P20"] = j.MM20 - j.MM20.shift(5)
    for n in (5, 20, 100):
        j["ATR%d" % n] = tr.rolling(n).mean()
    return j


def paniers(d, span=576, heures=BR.H_M5, debut=600):
    """Chaque panier possible : sortie, gain 3 pos., MAE 1re pos., increments journaliers de la courbe marquee."""
    c, hi, lo, sp, t = (d[x].values for x in ("cloture", "haut", "bas", "sp", "heure"))
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    uj = np.unique(jour); jx = np.searchsorted(uj, jour)
    fin = np.r_[jour[1:] != jour[:-1], True]
    n = len(c)
    ik = np.array([i for i in range(debut, n) if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0])
    K = len(ik)
    EX = np.full((K, 2), n, int); G3 = np.zeros((K, 2)); MAE = np.zeros((K, 2))
    RK, RS, RJ, RI = [], [], [], []
    for k, i in enumerate(ik):
        for si, s in ((0, 1), (1, -1)):
            stop, pas = BR.STOP * atr[i], BR.PAS * atr[i]
            e = [c[i] + (sp[i] if s > 0 else -sp[i])]
            meilleur, prochain = c[i], c[i] + s * pas
            mae, prec, lig = 0.0, 0.0, []
            if fin[i]:
                prec = s * ((c[i] if s > 0 else c[i] + sp[i]) - e[0]) / stop; lig.append((jx[i], prec))
            for q in range(i + 1, n):
                niveau = meilleur - s * stop
                if (lo[q] <= niveau) if s > 0 else (hi[q] + sp[q] >= niveau):
                    EX[k, si] = q
                    G3[k, si] = sum(s * (niveau - x) for x in e) / stop
                    mae = max(mae, s * (e[0] - niveau) / stop)
                    lig.append((jx[q], G3[k, si] - prec))
                    break
                mae = max(mae, (e[0] - lo[q]) / stop if s > 0 else (hi[q] + sp[q] - e[0]) / stop)
                meilleur = max(meilleur, hi[q]) if s > 0 else min(meilleur, lo[q])
                while len(e) < BR.MAXP and s * (c[q] - prochain) >= 0:
                    if s * (c[q] - prochain) <= 0.5 * pas:
                        e.append(c[q] + (sp[q] if s > 0 else -sp[q]))
                    prochain += s * pas
                if fin[q]:
                    px = c[q] if s > 0 else c[q] + sp[q]
                    m = sum(s * (px - x) for x in e) / stop
                    lig.append((jx[q], m - prec)); prec = m
            MAE[k, si] = mae
            if EX[k, si] < n:
                for a, b in lig:
                    RK.append(k); RS.append(si); RJ.append(a); RI.append(b)
    signal = np.where(c[ik] > ema[ik], 0, 1)
    return dict(ik=ik, EX=EX, G3=G3, MAE=MAE, signal=signal, t=t, n=n, jour=jour, uj=uj, hm=list(zip(hh[ik], mm[ik])),
                RK=np.array(RK), RS=np.array(RS), RJ=np.array(RJ), RI=np.array(RI))


def rejoue(B, idx, S):
    """S : N x len(idx) sens (0 achat / 1 vente) aux seuls instants idx. Rend O (ouvert ET sorti) et gains."""
    N, K = S.shape
    bu = np.zeros((N, 2), int); r = np.arange(N); O = np.zeros((N, K), bool)
    ik, EX = B["ik"], B["EX"]
    for j, k in enumerate(idx):
        sd = S[:, j]
        ok = bu[r, sd] <= ik[k]
        O[ok, j] = True
        bu[r[ok], sd[ok]] = EX[k, sd[ok]]
    X = EX[idx[None, :], S]
    O &= X < B["n"]
    return O, np.where(O, B["G3"][idx[None, :], S], 0.0)


def regles(B, F, h1):
    """Pour chaque nom : (instants autorises, sens) ; fond lu au jour precedent complet."""
    jk = B["jour"][B["ik"]]
    p = np.searchsorted(F.jour.values, jk, "left") - 1
    f = {k: F[k].values[p] for k in ("C", "MM20", "MM50", "P20", "ATR5", "ATR20", "ATR100")}
    up = {"20": f["C"] > f["MM20"], "50": f["C"] > f["MM50"], "P20": f["P20"] > 0}
    dn = {"20": f["C"] < f["MM20"], "50": f["C"] < f["MM50"], "P20": f["P20"] < 0}
    sig = B["signal"]; K = len(sig); tout = np.ones(K, bool)
    hm = B["hm"]
    lon = {(7, 0), (11, 0)} if h1 else {(8, 0), (8, 30), (12, 0)}
    ny = {(14, 0), (15, 0)} if h1 else {(15, 45), (16, 0), (16, 30)}
    asie = {(2, 0)} if h1 else {(3, 5)}
    H = lambda E: np.array([x in E for x in hm])
    accord = lambda c: (up[c] & (sig == 0)) | (dn[c] & (sig == 1))
    V = {"V5_20": f["ATR5"] > f["ATR20"], "V20_100": f["ATR20"] > f["ATR100"]}
    R = {"bt_or": (tout, sig), "ACH": (tout, np.zeros(K, int))}
    for c, nm in (("20", "20"), ("50", "50"), ("P20", "P20")):
        R["F" + nm] = (accord(c), sig)
        R["D" + nm] = (up[c] | dn[c], np.where(up[c], 0, 1))
        R["A" + nm] = (up[c], np.zeros(K, int))
    for k, v in V.items():
        R[k] = (v, sig)
    R["HLON"], R["HNY"], R["H-0305"] = (H(lon), sig), (H(ny), sig), (~H(asie), sig)
    R["F50+H-0305"] = (R["F50"][0] & R["H-0305"][0], sig)
    R["FP20+V5_20"] = (R["FP20"][0] & V["V5_20"], sig)
    R["A50+V20_100"] = (R["A50"][0] & V["V20_100"], np.zeros(K, int))
    return R


def courbe(B, idx, S, O):
    """Serie journaliere marquee des paniers ouverts (O, S sur une ligne)."""
    K = len(B["ik"]); ouv = np.zeros((K, 2), bool)
    ouv[idx[O], S[O]] = True
    m = ouv[B["RK"], B["RS"]]
    return np.bincount(B["RJ"][m], weights=B["RI"][m], minlength=len(B["uj"]))


def pb(x):
    cs = np.r_[0.0, np.cumsum(x)]
    return (cs - np.maximum.accumulate(cs)).min()


def jeu(nom, d, kw, h1):
    t1 = time.time()
    B = paniers(d, **kw)
    F = fond_d1()
    R = regles(B, F, h1)
    t_ouv = B["t"][B["ik"]]
    moit = [("1re", t_ouv < COUPE), ("2e", t_ouv >= COUPE)] if h1 else []
    rng = np.random.default_rng(GRAINE)
    res, serie = {}, {}
    for v, (ok, sens) in R.items():
        idx = np.flatnonzero(ok)
        S = sens[idx][None, :]
        O, g = rejoue(B, idx, S)
        Oa, ga = rejoue(B, idx, np.zeros_like(S))
        Sr = rng.integers(0, 2, size=(NT, len(idx)))
        Or, gr = rejoue(B, idx, Sr)
        x = courbe(B, idx, S[0], O[0])
        serie[v] = x
        mae = B["MAE"][idx[O[0]], S[0][O[0]]]
        r = dict(jeu=nom, variante=v, instants=len(idx), paniers=int(O[0].sum()), total_R=g.sum(),
                 R_panier=g.sum() / max(O[0].sum(), 1), pire_baisse=pb(x), MAE_med=np.median(mae),
                 MAE_p75=np.percentile(mae, 75), pct_stop=100 * (mae >= 1).mean(),
                 p_hasard=(1 + (gr.sum(1) >= g.sum()).sum()) / (NT + 1), hasard_moy=gr.sum(1).mean(),
                 achat_memes_instants=ga.sum(), ecart_achat=g.sum() - ga.sum(), controle_courbe=x.sum() - g.sum())
        for mn, m in moit:
            mm_ = m[idx]
            r["total_" + mn] = g[0, mm_].sum(); r["pan_" + mn] = int(O[0, mm_].sum())
            r["Rpan_" + mn] = r["total_" + mn] / max(r["pan_" + mn], 1)
            r["p_" + mn] = (1 + (gr[:, mm_].sum(1) >= r["total_" + mn]).sum()) / (NT + 1)
        if v == "bt_or":    # ligne « hasard » : sens tire au sort aux instants bt_or
            Ms = np.concatenate([B["MAE"][idx[Or[i]], Sr[i][Or[i]]] for i in range(200)])
            h = dict(jeu=nom, variante="hasard (moy. %d tirages)" % NT, instants=len(idx), paniers=Or.sum(1).mean(),
                     total_R=gr.sum(1).mean(), R_panier=gr.sum(1).mean() / Or.sum(1).mean(), MAE_med=np.median(Ms),
                     MAE_p75=np.percentile(Ms, 75), pct_stop=100 * (Ms >= 1).mean())
            for mn, m in moit:
                h["total_" + mn] = gr[:, m[idx]].sum(1).mean()
        res[v] = r
    bt = serie["bt_or"]; pbt = res["bt_or"]["pire_baisse"]
    for v in res:
        res[v]["fa"] = pbt / res[v]["pire_baisse"] if res[v]["pire_baisse"] < 0 else np.nan
        res[v]["total_risque_egal"] = res[v]["total_R"] * res[v]["fa"]
    # ---- White : jours x 17, serie x fa - bt_or
    Dm = np.column_stack([serie[v] * res[v]["fa"] - bt for v in CAND])
    kb, pw = BR.white(Dm)
    # ---- walk-forward
    mois = pd.to_datetime(B["uj"] * 86400, unit="s").to_period("M")
    MO = mois.unique(); la, lt = (12, 3) if h1 else (6, 1)
    oos = {"choix": 0.0, "bt_or": 0.0, "ACH": 0.0}; choix = []; mt = []
    for i in range(la, len(MO), lt):
        app = (mois >= MO[i - la]) & (mois <= MO[i - 1]); te = (mois >= MO[i]) & (mois <= MO[min(i + lt - 1, len(MO) - 1)])
        dbt = pb(bt[app])
        sc = {v: serie[v][app].sum() / -min(pb(serie[v][app]), -1e-9) for v in CAND}
        best = max(CAND, key=sc.get); choix.append(best); mt.append(str(MO[i]))
        for cle, v in (("choix", best), ("ACH", "ACH")):
            fa = dbt / pb(serie[v][app]) if pb(serie[v][app]) < 0 else 1.0
            oos[cle] += (serie[v][te] * fa).sum()
        oos["bt_or"] += bt[te].sum()
    fq = pd.Series(choix).value_counts()
    print("\n=== %s : %d instants bt_or, precalcul + %d x %d tirages en %.0f s" % (nom, len(B["ik"]), len(R), NT, time.time() - t1))
    print("Controle bt_or : %d paniers %+.1f R ; courbe marquee - paniers = %.2e ; pire baisse marquee %.1f R"
          % (res["bt_or"]["paniers"], res["bt_or"]["total_R"], max(abs(r["controle_courbe"]) for r in res.values()), pbt))
    lignes = [res["bt_or"], h, res["ACH"]] + [res[v] for v in CAND]
    T = pd.DataFrame(lignes)
    cols = ["variante", "paniers", "total_R", "fa", "total_risque_egal", "R_panier", "MAE_med", "MAE_p75", "pct_stop",
            "p_hasard", "ecart_achat"] + (["total_1re", "p_1re", "total_2e", "p_2e"] if h1 else [])
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(T[cols].round(3).to_string(index=False))
    print("White (17 contre bt_or, risque egal) : meilleure %s, p corrige = %.3f" % (CAND[kb], pw))
    print("Walk-forward %d/%d, %d fenetres (%s -> %s) ; choix : %s" % (la, lt, len(choix), mt[0], mt[-1], dict(fq)))
    print("  hors echantillon : choix %+.1f R ; bt_or %+.1f R ; ACH (risque egal) %+.1f R" % (oos["choix"], oos["bt_or"], oos["ACH"]))
    T["white_p"] = pw; T["white_meilleure"] = CAND[kb]
    wf = dict(jeu=nom, variante="walk-forward (choix %s)" % ",".join("%s:%d" % kv for kv in fq.items()),
              total_risque_egal=oos["choix"], wf_bt_or=oos["bt_or"], wf_ACH=oos["ACH"], white_p=pw)
    T = pd.concat([T, pd.DataFrame([wf])], ignore_index=True)
    return T, oos, pw, fq.index[0], res


if __name__ == "__main__":
    a5, b5 = BR.charge("xau_m5_2025a"), BR.charge("xau_m5_90k")
    d5 = pd.concat([a5, b5[b5.heure > a5.heure.iloc[-1]]], ignore_index=True)
    dh = BR.charge("xau_h1_50k")
    dh = dh[dh.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
    TH, oh, pwh, vh, rh = jeu("or H1", dh, dict(span=48, heures=BJ.H_H1, debut=60), True)
    T5, o5, pw5, v5, r5 = jeu("or M5", d5, {}, False)
    wf_ok = all(o["choix"] > o["bt_or"] and o["choix"] > o["ACH"] for o in (oh, o5))
    r = rh[vh]
    mae_ok = r["MAE_med"] < rh["bt_or"]["MAE_med"] or r["pct_stop"] < rh["bt_or"]["pct_stop"]
    autres = pwh < 0.10 and r["p_1re"] < 0.10 and r["p_2e"] < 0.10 and mae_ok
    verdict = "TIENT" if wf_ok and autres else ("PRESQUE" if wf_ok else "NE TIENT PAS")
    print("\nVERDICT : %s (walk-forward bon cote H1+M5 : %s ; White H1 p %.3f ; variante la plus choisie H1 %s : p moities "
          "%.3f / %.3f, MAE med %.2f vs %.2f, %% stop %.1f vs %.1f)" % (verdict, wf_ok, pwh, vh, r["p_1re"], r["p_2e"],
          r["MAE_med"], rh["bt_or"]["MAE_med"], r["pct_stop"], rh["bt_or"]["pct_stop"]))
    T = pd.concat([TH, T5], ignore_index=True)
    T["verdict"] = verdict
    T.drop(columns=["controle_courbe"]).round(4).to_csv(os.path.join(ICI, "donnees", "entree_filtres.csv"), index=False)
    print("Duree totale %.0f s. Ecrit donnees/entree_filtres.csv (%d lignes)." % (time.time() - T00, len(T)))
