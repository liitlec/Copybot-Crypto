"""Banc AP : la « poche pari » (PRIORITES 17/11 12 h 45). Compte de depart 100 $, on accepte de tout perdre.
Regle : on ne parie qu'avec un avantage MESURE. Candidats retenus (avantage mesure au banc) :
  rebond_nas : contre-pied d'une grande journee du Nasdaq (banc_vol_retour.py ; robot rebond_nas.py), D1 courtier 2018-2026
  repli_ind  : repli des 4 indices US (RSI 2 j < 10 au-dessus de la moyenne 200 j ; sortie cloture > moyenne 5 j ou
               10 jours ; stop 2 ATR), D1 courtier 2020-09 -> 2026-11 (S&P et Dow commencent en 2020)
  bt_or      : mecanique BlockTrend sur l'or (pas 0,25 / stop 0,667 ATR / 3 positions), H1 courtier 08/2022-11/2026
               (4 ans, periode plate comprise) ; la version M5 15 mois (hausse de l'or) est donnee a part, optimiste.
Ecartes : « suivre ce qui marche » (pas d'avantage prouve face a la tendance seule, t = 0,4) ; tout le reste ne tient pas.
Tailles REELLES du courtier a 100 $ : or 0,01 lot = 1 once ; indices 0,1 lot x 1 $ par point (Dow verifie en direct ;
NAS100+, SP500+, US2000+ supposes pareils). Prix d'aujourd'hui : chaque trade est rejoue en % puis converti a la taille
qu'il aurait aujourd'hui. Couts : indices 1 bp aller-retour (spread d'ouverture) + financement de nuit 1,8 bp par nuit
(repli) ; or : spread reel a chaque entree (dans le banc). Marge supposee : indices 1 %, or 0,2 %.
Mise : « unites » = lots minimum. unites = max(1, plancher(f x compte / risque d'une unite)), ou le risque d'une unite
est le notionnel (indices : f = levier) ou le stop initial en $ (or : f = part du compte risquee par position).
f = multiples du Kelly (0,5 / 1 / 2 / 3 / 5) calcule sur les trades, plus « lot mini fixe ». Le plancher a 1 lot rend
la mise plus grosse que voulu quand le compte est petit : c'est la realite d'une poche de 100 $.
Monte-Carlo : 10 000 parcours de 63 jours (3 mois) et 252 jours (12 mois) ; jours de bourse tires par blocs de 20 jours
(garde les series de pertes) ; trades d'un jour = trades ENTRES ce jour-la, gain compte d'un coup ; liquidation si la
pire excursion (bas/haut pendant la tenue) x taille mange le compte jusqu'a 50 % de la marge. Ruine = compte < 20 $ (une liquidation laisse ~14 $ sur le Nasdaq)
(« poche vide = on s'arrete »). Trois scenarios : historique ; avantage divise par 2 (chaque trade ampute de la moitie
du gain moyen) ; hors echantillon (Kelly mesure sur la 1re moitie, jours tires dans la 2de moitie seulement).
Choix fixe d'avance : le montage qui maximise la chance de x5 a 12 mois dans le scenario « avantage / 2 », parmi ceux
dont la chance de ruine a 12 mois (meme scenario) est <= 50 %. Usage : python3 banc_pari.py"""
import os, sys, contextlib, io
import numpy as np, pandas as pd

ICI = os.path.dirname(os.path.abspath(__file__))
DON = os.path.join(ICI, "mt5", "donnees")
sys.path.insert(0, ICI)
with contextlib.redirect_stdout(io.StringIO()):
    import banc_bt_regulier as BR

DEPART, RUINE, NPAR = 100.0, 20.0, 10000
COUT_IND, NUIT = 1.0e-4, 1.8e-4
rng = np.random.default_rng(1245)


def d1(nom):
    d = pd.read_csv(os.path.join(DON, nom + "_d1_5k.csv.gz"))
    d["jour"] = pd.to_datetime(d.heure, unit="s").dt.floor("D")
    return d.set_index("jour")[["ouverture", "haut", "bas", "cloture"]]


def trades_rebond():
    d = d1("nas"); px = d.cloture.iloc[-1]
    amp = (d.haut - d.bas) / d.cloture.shift(1)
    med = amp.shift(1).rolling(20).median()
    sig = np.where(amp > 1.5 * med, -np.sign(d.cloture - d.cloture.shift(1)), 0)
    T = []
    for i in range(21, len(d) - 1):
        s = sig[i]
        if s == 0:
            continue
        o, h, l, c = d.iloc[i + 1]
        r = s * (c - o) / o - COUT_IND
        mae = ((o - l) if s > 0 else (h - o)) / o
        T.append((d.index[i + 1], r, mae))
    T = pd.DataFrame(T, columns=["jour", "r", "mae"])
    T["notion"] = 0.1 * px                       # notionnel d'un lot mini aujourd'hui
    return T


def trades_repli():
    T = []
    for nom in ("nas", "sp", "dj", "us2000"):
        d = d1(nom); d = d[d.index >= "2020-09-14"]; d_all = d1(nom); px = d_all.cloture.iloc[-1]
        c = d_all.cloture
        dc = c.diff(); up, dn = dc.clip(lower=0), (-dc).clip(lower=0)
        rs = up.ewm(alpha=0.5, adjust=False).mean() / dn.ewm(alpha=0.5, adjust=False).mean()
        rsi = 100 - 100 / (1 + rs)
        ma200, ma5 = c.rolling(200).mean(), c.rolling(5).mean()
        tr = np.maximum(d_all.haut - d_all.bas, np.maximum((d_all.haut - c.shift(1)).abs(), (d_all.bas - c.shift(1)).abs()))
        atr = tr.rolling(20).mean()
        D = d_all.assign(rsi=rsi, ma200=ma200, ma5=ma5, atr=atr)
        D = D[D.index >= "2020-09-14"]
        i, n = 0, len(D)
        while i < n - 1:
            x = D.iloc[i]
            if x.rsi < 10 and x.cloture > x.ma200 and x.ma200 == x.ma200:
                e = D.ouverture.iloc[i + 1]; stop = e - 2 * x.atr; mae, sortie, j = 0.0, None, i + 1
                while j < n:
                    mae = max(mae, (e - D.bas.iloc[j]) / e)
                    if D.bas.iloc[j] <= stop:
                        sortie = stop; break
                    if D.cloture.iloc[j] > D.ma5.iloc[j] or j - i >= 10:
                        sortie = D.cloture.iloc[j]; break
                    j += 1
                if sortie is None:
                    break
                r = (sortie - e) / e - COUT_IND - NUIT * (j - i - 1)
                T.append((D.index[i + 1], r, mae, 0.1 * px, nom))
                i = j + 1
            else:
                i += 1
    return pd.DataFrame(T, columns=["jour", "r", "mae", "notion", "marche"])


def trades_bt(ident="xau_h1_50k"):
    d = BR.charge(ident)
    if ident == "xau_h1_50k":
        d = d[d.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
        P = BR.simule(d, span=48, heures={(2, 0), (7, 0), (11, 0), (14, 0), (15, 0)}, debut=60)
    else:
        P = BR.simule(d)
    px = 3880.0
    T = pd.DataFrame({"jour": pd.to_datetime(P.t0, unit="s").dt.floor("D"),
                      "R": P.g.values, "stop_rel": (P.stop / P.px).values})
    # 1 unite = 0,01 lot = 1 once ; risque d'une unite = stop initial en $ au prix d'aujourd'hui
    T["risque"] = T.stop_rel * px
    T["usd"] = T.R * T.risque          # gain d'un panier a 1 unite par position (3 positions au plus)
    T["mae"] = 0.0                     # perte bornee par le stop suiveur : pas de liquidation a part
    return T


def kelly(x):
    """f qui maximise E[log(1 + f x)] (x = gain par unite de f) ; recherche sur une grille."""
    x = np.asarray(x)
    fs = np.linspace(0.001, 1.0 / max(1e-9, -x.min()) * 0.999, 2000)
    g = [np.log1p(f * x).mean() for f in fs]
    return fs[int(np.argmax(g))]


def jours_tableau(T, cal, kind):
    """Pour chaque jour du calendrier : tableaux (K trades au plus) de gain/risque/excursion/marge par unite."""
    G = T.groupby("jour")
    K = max(1, G.size().max())
    n = len(cal)
    pnl, risk, mae, marge = (np.zeros((n, K)) for _ in range(4))
    pos = {j: k for k, j in enumerate(cal)}
    for j, g in G:
        if j not in pos:
            continue
        k = pos[j]
        for m, (_, t) in enumerate(g.iterrows()):
            if kind == "bt":
                pnl[k, m], risk[k, m], mae[k, m], marge[k, m] = t.usd, t.risque, 0.0, 3 * 3880 * 0.002
            else:
                pnl[k, m], risk[k, m], mae[k, m], marge[k, m] = t.r * t.notion, t.notion, t.mae * t.notion, 0.01 * t.notion
    return pnl, risk, mae, marge


def monte_carlo(tabs, fs, jours, idx_src=None, bloc=20, depart=DEPART):
    """tabs : liste de (pnl, risk, mae, marge) sur le meme calendrier ; fs : f de chaque piece (None = lot mini fixe)."""
    n = tabs[0][0].shape[0]
    src = np.arange(n) if idx_src is None else idx_src
    E = np.full(NPAR, depart); mort = np.zeros(NPAR, bool)
    t = 0
    pos = rng.integers(len(src), size=NPAR)
    while t < jours:
        if t % bloc == 0:
            pos = rng.integers(len(src), size=NPAR)
        k = src[(pos + t % bloc) % len(src)]
        tot = np.zeros(NPAR); adv = np.zeros(NPAR); mg = np.zeros(NPAR)
        for (pnl, risk, mae, marge), f in zip(tabs, fs):
            p, r, a, m = pnl[k], risk[k], mae[k], marge[k]
            actif = r > 0
            if f is None:
                u = np.ones_like(p)
            else:
                u = np.maximum(1.0, np.floor(f * E[:, None] / np.where(actif, r, 1.0)))
            u = np.where(actif, u, 0.0)
            tot += (u * p).sum(1); adv += (u * a).sum(1); mg += (u * m).sum(1)
        liq = (E - adv) < 0.5 * mg
        # liquidation : le courtier coupe quand il ne reste que 50 % de la marge -> il reste ~ 0,5 x marge
        E = np.where(mort, E, np.where(liq, np.minimum(E, 0.5 * mg), E + tot))
        E = np.maximum(E, 0.0)
        mort |= E < RUINE * depart / DEPART
        t += 1
    return E, mort


def stats(E, mort, depart=DEPART):
    E = E * DEPART / depart            # ramene a un depart de 100
    return {"ruine": mort.mean(), "<50": (E < 50).mean(), "mediane": np.median(E),
            "x2": (E >= 200).mean(), "x5": (E >= 500).mean(), "x10": (E >= 1000).mean()}


def etape2():
    """Etape 2 (ajoutee apres l'etape 1, ou aucun montage ne passe a 100 $) : d'ou vient la ruine ? Le lot minimum.
    (a) meme poche, depart 100 / 300 / 1 000 $ (resultats ramenes a 100) ; (b) repli sur les 2 plus petits contrats
    (SP500+ et US2000+, choisis par la TAILLE du contrat, pas par le resultat). Scenario « avantage / 2 », 1 Kelly et
    lot mini, 12 mois. Seuils de ruine ramenes a 20 % du depart."""
    reb, rep = trades_rebond(), trades_repli()
    c = d1("nas").index
    C = c[c >= "2020-09-15"]
    def moitie(T, col="r"):
        T = T.copy(); T[col] = T[col] - 0.5 * T[col].mean(); return T
    rows = []
    for nom, pieces in (("repli_ind", [rep]), ("rebond+repli", [reb[reb.jour >= C[0]], rep]),
                        ("repli petits contrats (SP, US2000)", [rep[rep.marche.isin(["sp", "us2000"])]]),
                        ("rebond_nas", [reb[reb.jour >= C[0]]])):
        tabs = [jours_tableau(moitie(T), C, "ind") for T in pieces]
        kel = [kelly(moitie(T).r.values) for T in pieces]
        for dep in (100.0, 300.0, 1000.0):
            for mnom, mult in (("lot mini", None), ("1 Kelly", 1.0), ("2 Kelly", 2.0)):
                E, mort = monte_carlo(tabs, [None if mult is None else mult * k for k in kel], 252, depart=dep)
                rows.append(dict(montage=nom, depart=dep, mise=mnom, **stats(E, mort, dep)))
    R = pd.DataFrame(rows)
    for col in ("ruine", "<50", "x2", "x5", "x10"):
        R[col] = (100 * R[col]).round(0).astype(int)
    R["mediane"] = R.mediane.round(0).astype(int)
    print("Etape 2 (avantage / 2, 12 mois ; % ; mediane et paliers ramenes a un depart de 100) :")
    print(R.to_string(index=False))
    R.to_csv(os.path.join(ICI, "donnees", "pari_etape2.csv"), index=False)


if __name__ == "__main__" and sys.argv[1:] == ["etape2"]:
    etape2(); sys.exit()

if __name__ == "__main__":
    reb, rep, bth, btm = trades_rebond(), trades_repli(), trades_bt(), trades_bt("xau_m5_90k")
    tst = lambda x: x.mean() / x.std() * np.sqrt(len(x))
    print("Controle des trades (gain par trade apres couts) :")
    print("  rebond_nas %d trades %s -> %s : %+.1f bp (t = %.1f)" % (len(reb), reb.jour.min().date(), reb.jour.max().date(), 1e4 * reb.r.mean(), tst(reb.r)))
    print("  repli_ind  %d trades : %+.1f bp (t = %.1f) ; par marche : %s" % (len(rep), 1e4 * rep.r.mean(), tst(rep.r),
          ", ".join("%s %+.0f bp (%d)" % (m, 1e4 * g.r.mean(), len(g)) for m, g in rep.groupby("marche"))))
    print("  bt_or H1   %d paniers %s -> %s : %+.2f R (t = %.1f), 1 R a 0,01 lot = %.0f $ en moyenne aujourd'hui" % (
        len(bth), bth.jour.min().date(), bth.jour.max().date(), bth.R.mean(), tst(bth.R), bth.risque.mean()))
    print("  bt_or M5   %d paniers : %+.2f R (t = %.1f)" % (len(btm), btm.R.mean(), tst(btm.R)))

    def cal(debut):
        c = d1("nas").index
        return c[c >= debut]
    C_reb, C_rep, C_bt = cal(reb.jour.min()), cal("2020-09-15"), cal("2022-08-01")
    C_btm = cal(btm.jour.min())
    # x = gain par unite de f (pour le Kelly) : indices -> rendement du notionnel ; or -> gain en R
    PIECES = {"rebond_nas": (reb, "ind", reb.r.values), "repli_ind": (rep, "ind", rep.r.values),
              "bt_or": (bth, "bt", bth.R.values), "bt_or_15mois": (btm, "bt", btm.R.values)}
    KEL = {k: kelly(v[2]) for k, v in PIECES.items()}
    print("Kelly (part du compte : levier pour les indices, risque par position pour l'or) : " +
          ", ".join("%s %.2f" % kv for kv in KEL.items()))
    lev_mini = {"rebond_nas": reb.notion.iloc[0] / DEPART, "repli_ind": rep.groupby("marche").notion.first().mean() / DEPART,
                "bt_or": bth.risque.mean() / DEPART}
    print("Mise imposee par le lot minimum a 100 $ : rebond %.0f x le compte ; repli %.0f x en moyenne ; bt_or %.0f %% du compte par position"
          % (lev_mini["rebond_nas"], lev_mini["repli_ind"], 100 * lev_mini["bt_or"]))

    MONTAGES = {"rebond_nas": ["rebond_nas"], "repli_ind": ["repli_ind"], "bt_or": ["bt_or"],
                "rebond+repli": ["rebond_nas", "repli_ind"], "rebond+repli+bt_or": ["rebond_nas", "repli_ind", "bt_or"],
                "bt_or_15mois (optimiste)": ["bt_or_15mois"]}
    CAL = {"rebond_nas": C_reb, "repli_ind": C_rep, "bt_or": C_bt, "rebond+repli": C_rep,
           "rebond+repli+bt_or": C_bt, "bt_or_15mois (optimiste)": C_btm}
    MISES = [("lot mini", None), ("0,5 Kelly", 0.5), ("1 Kelly", 1.0), ("2 Kelly", 2.0), ("3 Kelly", 3.0), ("5 Kelly", 5.0)]
    lignes = []
    for nom, pieces in MONTAGES.items():
        cal_m = CAL[nom]
        base = {p: jours_tableau(PIECES[p][0][PIECES[p][0].jour >= cal_m[0]], cal_m, PIECES[p][1]) for p in pieces}
        moitie = len(cal_m) // 2
        for scen in ("historique", "avantage / 2", "hors echantillon"):
            tabs, kel = [], []
            for p in pieces:
                T = PIECES[p][0][PIECES[p][0].jour >= cal_m[0]].copy()
                if scen == "avantage / 2":
                    if PIECES[p][1] == "bt":
                        T["R"] = T.R - 0.5 * T.R.mean(); T["usd"] = T.R * T.risque
                    else:
                        T["r"] = T.r - 0.5 * T.r.mean()
                tabs.append(jours_tableau(T, cal_m, PIECES[p][1]) if scen == "avantage / 2" else base[p])
                if scen == "hors echantillon":
                    x = T[T.jour < cal_m[moitie]]
                    kel.append(kelly(x.R.values if PIECES[p][1] == "bt" else x.r.values))
                else:
                    kel.append(kelly(T.R.values if PIECES[p][1] == "bt" else T.r.values))
            src = np.arange(moitie, len(cal_m)) if scen == "hors echantillon" else None
            for mnom, mult in MISES:
                fs = [None if mult is None else mult * k for k in kel]
                for jours, hz in ((63, "3 mois"), (252, "12 mois")):
                    E, mort = monte_carlo(tabs, fs, jours, src)
                    s = stats(E, mort)
                    lignes.append(dict(montage=nom, scenario=scen, mise=mnom, horizon=hz, **s))
    R = pd.DataFrame(lignes)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
    out = R.copy()
    for c in ("ruine", "<50", "x2", "x5", "x10"):
        out[c] = (100 * out[c]).round(0).astype(int).astype(str) + " %"
    out["mediane"] = out.mediane.round(0).astype(int).astype(str) + " $"
    print(out.to_string(index=False))
    R.to_csv(os.path.join(ICI, "donnees", "pari_montecarlo.csv"), index=False)
    ok = R[(R.scenario == "avantage / 2") & (R.horizon == "12 mois") & ~R.montage.str.contains("optimiste")]
    ok2 = ok[ok.ruine <= 0.5]
    meilleur = ok2.loc[ok2.x5.idxmax()] if len(ok2) else None
    print("\nChoix fixe d'avance (max chance de x5 a 12 mois, avantage / 2, ruine <= 50 %) :")
    print(meilleur if meilleur is not None else "aucun montage")
