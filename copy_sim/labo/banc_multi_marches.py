"""Banc MM : la mecanique bt_or et la regle « renforts gagnants » (GPT Astra, version A) sur d'AUTRES marches
(PRIORITES 23/11, ajout de Baptiste ; compte DEMO / labo, aucun ordre). Rien n'est regle par marche.
Mecaniques : (1) bt_or = banc_bt_regulier.simule (EMA 2 jours, pas 0,25 ATR, 3 positions, stop suiveur 0,667 ATR,
  heures fixes de l'or BR.H_M5 ; gain compte au jour de SORTIE) ; (2) regle GPT version A (laisser courir) =
  banc_gpt_pyramide.simule_regle IMPORTEE telle quelle (bougies M15, entree a la cloture de la M15 de 08:00 serveur,
  swaps 6 %/an compris). Les parametres D1 de la regle (R = 0,25 x amplitude moyenne 14 j, SMA 50, calme / inside day)
  sont recalcules par marche avec EXACTEMENT les formules de banc_gpt_pyramide.params_d1 (qui est ecrite pour l'or seul).
  Gain d'un panier GPT compte au jour de sa sortie (comme bt_or).
Donnees (la meilleure disponible par marche) :
  M5 du courtier, spread reel : or (xau_m5_2025a + 90k, 06/2025 -> 11/2026), argent, Nasdaq (2025a + 90k), S&P, Dow,
    EUR/USD (08/2025 -> 11/2026) ; BTC, ETH (01/2026 -> 11/2026 seulement). GPT : M5 regroupees en M15.
  USD/JPY : M1 du courtier regroupees (3 mois seulement, 08 -> 11/2026 ; trop court pour la SMA 50 + l'ATR : indicatif).
  Russell : bougies H1 de la seance cash (yahoo_1h_indices ^RUT, 12/2023 -> 11/2026), spread typique AJOUTE 0,4 pt ;
    heures adaptees a la seance (heure NY decalee de -1 h 30 : la 1re bougie 09:30 NY devient « 08:00 ») : bt_or entre
    a 09:30, 10:30, 12:30, 14:30 NY, EMA = 14 bougies (2 seances) ; GPT entre a l'OUVERTURE de la 1re bougie (comme le
    jeu H1 de banc_gpt_pyramide).
  DAX (ger_d1_5k du courtier, spread = mediane reelle de ger_m1), petrole (gj_oil, spread typique 0,04 $) : D1 seulement,
    08/2022 -> 11/2026. APPROXIMATION : chaque bougie D1 devient 4 pseudo-bougies (ouverture -> 1er extreme -> 2e
    extreme -> cloture ; bas avant haut si la seance finit en hausse, sinon l'inverse) ; bt_or entre une fois par jour a
    l'ouverture (EMA 8 pseudo-bougies = 2 jours) ; GPT entre a l'ouverture. Controle de l'approximation : l'or en D1
    pseudo-bougies contre l'or H1 reel sur 08/2022 -> 11/2026.
  GBP/USD : absent de l'inventaire -> passe.
  Parametres D1 de la regle GPT : D1 du courtier si elle existe (or, Nasdaq, S&P, Dow, DAX, Russell = us2000), sinon les
  series gj (argent, EUR, BTC, ETH, petrole ; dates calendaires = jour serveur approche), sinon D1 rebatie (USD/JPY).
Reference : bt_or sur l'or M5 (controle : 295 paniers / +114,1 R) pour les marches M5 ; bt_or sur l'or H1 08/2022+
  (BJ.H_H1, EMA 48) pour les marches H1 / D1. Meme periode = intersection des jours couverts.
Mesures par marche x mecanique : paniers, R/panier, total R, pire baisse (cumul journalier), mois positifs, total a
  risque egal (facteur = pire baisse de bt_or or / pire baisse du marche sur la meme periode), moities (2022-08 ->
  2024-09 / 2024-10 -> 2026-11 si la donnee couvre, sinon la periode coupee en deux), correlation journaliere (jours
  calendaires, 0 sans sortie) et mensuelle avec bt_or or, total pendant les mois negatifs de bt_or (brut et a risque egal).
Portefeuille « paniers multi-marches » (par mecanique) sur la fenetre M5 commune 11/08/2025 -> 11/11/2026, marches
  couvrant >= 80 % de chaque moitie (exclus : BTC, ETH, USD/JPY) : parite de risque (poids = 1 / ecart-type journalier,
  appris sur une moitie, rejoue sur l'autre, dans les deux sens), (a) tous, (b) total > 0 sur l'apprentissage ; mis a
  l'ecart-type de bt_or seul de l'apprentissage ; compare a bt_or seul : total, pire baisse, mois negatifs, gain / pire
  baisse (insensible a l'echelle). White (BR.white) des courbes journalieres de tous les marches x mecaniques de la
  fenetre contre zero.
VERDICT FIXE D'AVANCE : marche « AJOUTE » = positif sur les deux moities ET correlation mensuelle avec bt_or < 0,3 ET
  positif pendant les mois negatifs de bt_or ; portefeuille « TIENT » = gain / pire baisse hors echantillon > celui de
  bt_or seul dans les DEUX sens de decoupe.
Ecrit donnees/multi_marches.csv. Usage : python3 banc_multi_marches.py
"""
import os, time, contextlib, io, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_bt_regulier as BR
    import banc_jumeau as BJ
    import banc_gpt_pyramide as GP

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
DON = os.path.join(ICI, "donnees")
COUPE = pd.Timestamp("2024-10-01")
DEB_LONG = pd.Timestamp("2022-08-01")


# ---------------------------------------------------------------- donnees
def m5_concat(a, b):
    a, b = BR.charge(a), BR.charge(b)
    return pd.concat([a, b[b.heure > a.heure.iloc[-1]]], ignore_index=True)


def regroupe(d, sec):
    q = d.heure // sec
    g = d.groupby(q).agg(ouverture=("ouverture", "first"), haut=("haut", "max"), bas=("bas", "min"),
                         cloture=("cloture", "last"), sp=("sp", "mean")).reset_index()
    g["heure"] = g.pop("heure") * sec
    return g


def gj(nom):
    d = pd.read_csv(os.path.join(DON, "gj_%s.csv.gz" % nom))
    d = d.rename(columns={"open": "ouverture", "high": "haut", "low": "bas", "close": "cloture"})
    d["heure"] = pd.to_datetime(d.date).values.astype("datetime64[s]").astype(np.int64)
    return d.dropna(subset=["haut", "bas", "cloture"]).reset_index(drop=True)


def pseudo(d1, sp):
    """D1 -> 4 pseudo-bougies 08:00 (ouverture), 12:00, 16:00, 20:00 (chemin O -> X1 -> X2 -> C)."""
    o, h, l, c, t = (d1[x].values for x in ("ouverture", "haut", "bas", "cloture", "heure"))
    up = c >= o
    x1, x2 = np.where(up, l, h), np.where(up, h, l)
    pts = [(o, o), (o, x1), (x1, x2), (x2, c)]
    L = []
    for k, (a, b) in enumerate(pts):
        L.append(pd.DataFrame({"heure": t - t % 86400 + (8 + 4 * k) * 3600, "ouverture": a, "haut": np.maximum(a, b),
                               "bas": np.minimum(a, b), "cloture": b, "sp": sp}))
    return pd.concat(L).sort_values("heure", kind="stable").reset_index(drop=True)


def params_d1(d1):
    """Memes formules que GP.params_d1, pour n'importe quelle serie D1 (heure, haut, bas, cloture)."""
    d1 = d1.reset_index(drop=True)
    amp = d1.haut - d1.bas
    adr = amp.rolling(14).mean()
    calme = amp < 0.6 * adr.shift(1)
    inside = (d1.haut <= d1.haut.shift(1)) & (d1.bas >= d1.bas.shift(1))
    sma = d1.cloture.rolling(50).mean()
    sens = np.where(d1.cloture > sma, 1, np.where(d1.cloture < sma, -1, 0))
    ok = (calme | inside) & adr.notna() & sma.notna() & adr.shift(1).notna() & (sens != 0)
    return d1.heure.values - d1.heure.values % 86400, np.where(ok, sens, 0), (0.25 * adr).values, d1


def d1_de(d):
    j = d.heure // 86400
    g = d.groupby(j).agg(haut=("haut", "max"), bas=("bas", "min"), cloture=("cloture", "last")).reset_index()
    g["heure"] = g.pop("heure") * 86400
    return g


def rut_h1():
    y = pd.read_csv(os.path.join(DON, "yahoo_1h_indices.csv"))
    y = y[y.tk == "^RUT"].copy()
    t = pd.to_datetime(y.ny) - pd.Timedelta(minutes=90)      # 09:30 NY -> « 08:00 »
    y["heure"] = t.values.astype("datetime64[s]").astype(np.int64)
    y = y.rename(columns={"open": "ouverture", "high": "haut", "low": "bas", "close": "cloture"})
    y["sp"] = 0.4
    return y[["heure", "ouverture", "haut", "bas", "cloture", "sp"]].reset_index(drop=True)


H_RUT = {(8, 0), (9, 0), (11, 0), (13, 0)}


def jeux():
    """(nom, donnee, periode longue ?, d_bt, kw_bt, d_gpt, D1, kw_gpt)"""
    J = []
    lg = lambda d: d[d.heure >= DEB_LONG.timestamp()].reset_index(drop=True)
    d = m5_concat("xau_m5_2025a", "xau_m5_90k")
    J.append(("or", "M5 courtier, spread reel", False, d, {}, regroupe(d, 900), params_d1(BR.charge("xau_d1_5k")), {}))
    for nom, f, d1 in (("argent", "xag_m5_90k", gj("xag")), ("Nasdaq", None, BR.charge("nas_d1_5k")),
                       ("S&P", "sp_m5_90k", BR.charge("sp_d1_5k")), ("Dow", "dj_m5_90k", BR.charge("dj_d1_5k")),
                       ("EUR/USD", "eur_m5_90k", gj("eur")), ("BTC", "btc_m5_90k", gj("btc")), ("ETH", "eth_m5_90k", gj("eth"))):
        d = m5_concat("nas_m5_2025a", "nas_m5_90k") if f is None else BR.charge(f)
        J.append((nom, "M5 courtier, spread reel", False, d, {}, regroupe(d, 900), params_d1(d1), {}))
    j1 = BR.charge("jpy_m1_90k")
    J.append(("USD/JPY", "M1 courtier -> M5/M15, 3 mois", False, BR.charge("jpy_m1_90k", m1_vers_m5=True), {},
              regroupe(j1, 900), params_d1(d1_de(j1)), {}))
    r = rut_h1()
    J.append(("Russell", "H1 seance cash, spread 0,4 pt ajoute", True, r, dict(span=14, heures=H_RUT, debut=30), r,
              params_d1(BR.charge("us2000_d1_5k")), dict(entree_ouverture=True)))
    sp_ger = float(BR.charge("ger_m1_90k").sp.median())
    g = BR.charge("ger_d1_5k")
    J.append(("DAX", "D1 courtier -> pseudo-bougies, spread %.1f pt" % sp_ger, True, lg(pseudo(g, sp_ger)),
              dict(span=8, heures={(8, 0)}, debut=20), lg(pseudo(g, sp_ger)), params_d1(g), {}))
    o = gj("oil")
    J.append(("petrole", "D1 gj -> pseudo-bougies, spread 0,04 $", True, lg(pseudo(o, 0.04)),
              dict(span=8, heures={(8, 0)}, debut=20), lg(pseudo(o, 0.04)), params_d1(o), {}))
    x1 = BR.charge("xau_d1_5k")
    J.append(("or D1 (controle)", "D1 courtier -> pseudo-bougies, spread 0,17 $", True, lg(pseudo(x1, 0.17)),
              dict(span=8, heures={(8, 0)}, debut=20), lg(pseudo(x1, 0.17)), params_d1(x1), {}))
    return J


# ---------------------------------------------------------------- mesures
creux = lambda x: float((np.cumsum(x) - np.maximum.accumulate(np.cumsum(np.r_[0.0, x]))[1:]).min()) if len(x) else 0.0


def journalier(P, col_t="t1", col_g="g"):
    if P is None or len(P) == 0:
        return pd.Series(dtype=float)
    return P.groupby(pd.to_datetime(P[col_t], unit="s").dt.floor("D"))[col_g].sum()


def sur(s, a, b):
    return s.reindex(pd.date_range(a, b)).fillna(0.0)


def mesure(nom, meca, donnee, P, deb, fin, ref, long_):
    s = journalier(P); x = sur(s, deb, fin); r = sur(ref, deb, fin)
    t1 = pd.to_datetime(P.t1, unit="s") if len(P) else pd.Series(dtype="datetime64[ns]")
    Pm = P[(t1 >= deb) & (t1 <= fin + pd.Timedelta(days=1))] if len(P) else P
    if long_ and deb < COUPE - pd.Timedelta(days=200):
        mi, lib = COUPE, "2022-08->2024-09 / 2024-10->2026-11"
    else:
        mi, lib = deb + (fin - deb) / 2, "moitie %s->%s / %s->%s" % (deb.date(), (deb + (fin - deb) / 2).date(),
                                                                    (deb + (fin - deb) / 2).date(), fin.date())
    xm, rm = x.groupby(x.index.to_period("M")).sum(), r.groupby(r.index.to_period("M")).sum()
    cr, crr = creux(x.values), creux(r.values)
    f = crr / cr if cr < 0 else np.nan
    neg = rm[rm < 0].index
    return dict(marche=nom, mecanique=meca, donnee=donnee, debut=deb.date(), fin=fin.date(), paniers=len(Pm),
                R_panier=x.sum() / max(len(Pm), 1), total_R=x.sum(), pire_baisse_R=cr,
                mois_pos="%d/%d" % ((xm > 0).sum(), len(xm)), facteur_risque_egal=f, total_risque_egal=x.sum() * f,
                decoupe=lib, moitie1_R=x[x.index < mi].sum(), moitie2_R=x[x.index >= mi].sum(),
                corr_jour=x.corr(r), corr_mois=xm.corr(rm), ref_btor_total=r.sum(), ref_btor_pire_baisse=crr,
                mois_neg_btor=len(neg), R_mois_neg_btor=xm.reindex(neg).sum(),
                R_mois_neg_btor_risque_egal=xm.reindex(neg).sum() * f)


def stats_port(x, ref):
    xm = x.groupby(x.index.to_period("M")).sum()
    cr = creux(x.values)
    return dict(total=x.sum(), pire_baisse=cr, mois_neg=int((xm < 0).sum()), mois=len(xm),
                gain_sur_baisse=x.sum() / -cr if cr < 0 else np.nan)


# ---------------------------------------------------------------- programme
if __name__ == "__main__":
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    J = jeux()
    print("Donnees chargees en %.0f s ; GBP/USD : absent de l'inventaire (passe)." % (time.time() - T00))
    dh = BR.charge("xau_h1_50k"); dh = dh[dh.heure >= DEB_LONG.timestamp()].reset_index(drop=True)
    Ph = BR.simule(dh, span=48, heures=BJ.H_H1, debut=60)
    ref_long = journalier(Ph)
    SER, L = {}, []
    for nom, donnee, long_, dbt, kbt, dg, D1, kg in J:
        t1 = time.time()
        Pb = BR.simule(dbt, **kbt)
        Pg, _, _ = GP.simule_regle(dg, D1, sortie="A", **kg)
        if nom == "or":
            ref_m5 = journalier(Pb)
            print("CONTROLE bt_or or M5 : %d paniers %+.1f R (attendu 295 / +114,1)" % (len(Pb), Pb.g.sum()))
        ref = ref_long if long_ else ref_m5
        rd = ref_long.index[0] if long_ else pd.to_datetime(J[0][3].heure.iloc[0], unit="s").floor("D")
        deb = max(pd.to_datetime(dbt.heure.iloc[0], unit="s").floor("D"), rd)
        fin = min(pd.to_datetime(dbt.heure.iloc[-1], unit="s").floor("D"), pd.Timestamp("2026-11-11"))
        for meca, P in (("bt_or", Pb), ("GPT A", Pg)):
            L.append(mesure(nom, meca, donnee, P, deb, fin, ref, long_))
            SER[(nom, meca)] = journalier(P)
        if nom == "or":   # or H1 long : reference des marches H1 / D1
            dhg = BR.charge("xau_h1_50k"); dhg = dhg[dhg.heure >= DEB_LONG.timestamp()].reset_index(drop=True)
            Pgh, _, _ = GP.simule_regle(dhg, D1, sortie="A", entree_ouverture=True)
            a, b = ref_long.index[0], pd.Timestamp("2026-11-11")
            for meca, P in (("bt_or", Ph), ("GPT A", Pgh)):
                L.append(mesure("or H1", meca, "H1 courtier, spread reel", P, a, b, ref_long, True))
        print("  %-18s %.0f s" % (nom, time.time() - t1))
    T = pd.DataFrame(L)
    T["AJOUTE"] = np.where((T.moitie1_R > 0) & (T.moitie2_R > 0) & (T.corr_mois < 0.3) & (T.R_mois_neg_btor > 0)
                           & ~T.marche.str.startswith("or"), "AJOUTE", "")
    cols = ["marche", "mecanique", "debut", "fin", "paniers", "R_panier", "total_R", "pire_baisse_R", "mois_pos",
            "total_risque_egal", "moitie1_R", "moitie2_R", "corr_jour", "corr_mois", "mois_neg_btor", "R_mois_neg_btor", "AJOUTE"]
    print(T[cols].round(3).to_string(index=False))
    # ------------------------------------------------------------ portefeuilles (fenetre M5 commune)
    a, b = pd.Timestamp("2025-08-11"), pd.Timestamp("2026-11-11")
    idx = pd.date_range(a, b); mi = a + (b - a) / 2
    h1, h2 = idx < mi, idx >= mi
    PORT = ["or", "argent", "Nasdaq", "S&P", "Dow", "EUR/USD", "Russell", "DAX", "petrole"]
    r0 = sur(ref_m5, a, b)
    LP = []
    print("\nPortefeuille parite de risque, fenetre %s -> %s, coupe %s ; marches : %s (exclus : BTC, ETH, USD/JPY, trop courts)"
          % (a.date(), b.date(), mi.date(), ", ".join(PORT)))
    for meca in ("bt_or", "GPT A"):
        X = pd.DataFrame({m: sur(SER[(m, meca)], a, b) for m in PORT})
        for sens_, app, te in (("appris moitie 1 -> teste moitie 2", h1, h2), ("appris moitie 2 -> teste moitie 1", h2, h1)):
            ref_t = r0[te]; sr = stats_port(ref_t, ref_t)
            for sel in ("(a) tous", "(b) total>0 a l'apprentissage"):
                ok = [m for m in PORT if sel.startswith("(a)") or X[m][app].sum() > 0]
                w = 1 / X[ok][app].std().replace(0, np.nan)
                w = (w / w.sum()).fillna(0)
                x = (X[ok] * w).sum(1)
                k = r0[app].std() / x[app].std() if x[app].std() > 0 else 0
                s = stats_port(x[te] * k, ref_t)
                tient = s["gain_sur_baisse"] > sr["gain_sur_baisse"]
                LP.append(dict(mecanique=meca, sens=sens_, selection=sel, marches=" ".join(ok),
                               **{"port_" + kk: v for kk, v in s.items()}, **{"btor_" + kk: v for kk, v in sr.items()},
                               bat_btor=tient))
                print("  %-6s %-34s %-30s port. %+6.1f R creux %+5.1f mois<0 %d/%d g/b %5.2f | bt_or seul %+6.1f creux %+5.1f mois<0 %d/%d g/b %5.2f %s"
                      % (meca, sens_, sel, s["total"], s["pire_baisse"], s["mois_neg"], s["mois"], s["gain_sur_baisse"],
                         sr["total"], sr["pire_baisse"], sr["mois_neg"], sr["mois"], sr["gain_sur_baisse"],
                         "bat" if tient else "ne bat pas"))
    TP = pd.DataFrame(LP)
    ver = TP.groupby(["mecanique", "selection"]).bat_btor.all()
    print("Verdict portefeuille (bat bt_or seul en gain/pire baisse dans les deux sens) : "
          + " ; ".join("%s %s : %s" % (k[0], k[1], "TIENT" if v else "ne tient pas") for k, v in ver.items()))
    # ------------------------------------------------------------ White contre zero
    K = [(m, me) for me in ("bt_or", "GPT A") for m in PORT if m != "or"]
    D = np.column_stack([sur(SER[k], a, b).values for k in K])
    ib, p = BR.white(D)
    print("White (bootstrap stationnaire, 2000 tirages) des %d courbes marche x mecanique (hors or) contre zero : "
          "meilleure %s / %s (%+.1f R), p = %.3f" % (len(K), K[ib][0], K[ib][1], D[:, ib].sum(), p))
    T["white_N"], T["white_p"], T["white_meilleur"] = len(K), p, "%s / %s" % K[ib]
    out = pd.concat([T.assign(type="marche"), TP.assign(type="portefeuille")], ignore_index=True)
    out.round(4).to_csv(os.path.join(DON, "multi_marches.csv"), index=False)
    print("Marches AJOUTE : %s" % (", ".join(T[T.AJOUTE == "AJOUTE"].marche + " (" + T[T.AJOUTE == "AJOUTE"].mecanique + ")") or "aucun"))
    print("Duree %.0f s. Ecrit donnees/multi_marches.csv (%d lignes)." % (time.time() - T00, len(out)))
