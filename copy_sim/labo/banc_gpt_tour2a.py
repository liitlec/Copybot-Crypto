"""Banc G2A : la regle proposee par GPT Astra, tour 2, points 1, 2 et 3 (PRIORITES 23/11, 11 h ; compte DEMO / labo,
aucun ordre). Regle = version A (laisser courir), simulee par banc_gpt_pyramide.simule_regle IMPORTEE telle quelle
(regle figee du 23/11 ; parametres D1 de l'or = GP.params_d1, autres marches = banc_multi_marches.params_d1, memes
formules). Jeux : or H1 08/2022 -> 11/2026 (entree a l'ouverture de la bougie H1 de 08:00, comme GP), or M15 du
courtier (09/2024 -> 11/2026) ; « tous marches » = or M15 + Nasdaq + S&P + EUR/USD (M5 du courtier regroupees en M15,
spread reel) sur la periode commune (semaines entieres du lundi 01/09/2025 au dimanche 08/11/2026, 62 semaines ;
chaque marche risque f par panier, donc jusqu'a 4 f en meme temps).
CE QUI EST FIXE AVANT :
(1) RISQUE PAR PANIER f = 0,5 / 1 / 2 / 3 / 12 % du capital, TOUTES COUCHES COMPRISES. Comptage : la perte maximale
  possible au stop pendant la vie du panier vaut 1,25 R de V (avant renfort : V au stop initial = 1 R ; des la 1re
  cloture a +1 R le stop passe au prix moyen = 1re entree, donc apres les 2 renforts : V 0, renfort 1 (0,5 V entre a
  >= +1 R) -0,5 R, renfort 2 (0,5 V a >= +1,5 R) -0,75 R) ; le spread est deja dans les prix d'entree ; on ajoute
  0,10 R de marge pour glissement et swaps -> K = 1,35 R. Donc V est pose pour que sa perte au stop initial vaille
  f / 1,35 du capital (12 % « toutes couches » = 8,9 % sur V seul). Le banc imprime la pire perte reelle d'un panier
  (en R, trous et swaps compris) pour controle.
  Monte-Carlo par BLOCS DE SEMAINES CIVILES ENTIERES (lundi -> dimanche) : chaque semaine tiree garde son parcours
  journalier marque (gain latent a la cloture de chaque jour) et, pour « tous marches », les 4 marches de la MEME
  semaine (positions simultanees). Tirage avec remise, 104 semaines = 24 mois, 10 000 tirages. Mise recalculee chaque
  lundi (compose par semaine, tailles fixes dans la semaine). Ruine = capital sous 20 % du depart (on s'arrete).
  Mesures : probabilite de franchir -30 % depuis un sommet (journalier), ruine, valeur mediane finale (x depart).
  Scenarios : mesure ; prudent = chaque panier perd la moitie du R moyen de son marche (retire au jour de sortie) ;
  nul = tout le R moyen retire. Jeux : or H1 4 ans, or M15, tous marches. Rappel verifie : n = ln(0,7)/ln(1-r) pertes
  completes a r pour atteindre -30 % (et le meme n si une perte ordinaire = 1 R de V = r / 1,35).
(2) COMPTE CENT (100 et 500 EUR, EURUSD 1,16) : lot min = pas = 0,01 lot cent. Valeur d'un pas (0,01 lot cent) par
  unite de prix : or 0,01 $ (0,01 once) ; indices 0,0001 $ par point (banc_plan_cent : 1 lot standard = 1 $/point,
  lot cent = 0,01 standard ; variante : lot min indices x 10 = 0,1 lot cent) ; EUR/USD 10 $ par 1,0 (1 lot standard =
  100 000 EUR). Volume V = 2k pas (pour que le renfort 0,5 V tombe sur le pas), k = plancher(f x capital / (2 x K x
  valeur du pas x R)) ; si k < 1 (V ou le demi-lot de renfort ne tient pas dans le budget), le signal est IGNORE.
  Gain du panier = 2k x valeur du pas x R x g (g = R du panier, renforts et swaps compris). REJEU HISTORIQUE (pas de
  Monte-Carlo), compose au fil des paniers (taille fixee a l'ouverture sur le capital realise), pire baisse sur le
  capital realise ; compare au meme rejeu sans contrainte de lot (fraction exacte f / K). R en $ = R historique ;
  variante « prix d'aujourd'hui » : R = (R / prix d'entree) x derniere cloture. f = 0,5 / 1 / 2 / 3 %.
(3) PLACEBO du filtre « veille tres calme OU inside day » : candidats = toutes les seances ou la regle POURRAIT entrer
  (bougie de 08:00 presente, tendance SMA 50 definie, R defini), filtre ou non. Pour chaque candidat on simule le panier
  seul (simule_regle sur une tranche de donnees commencant a cette seance, meme code : horaires, renforts, stops,
  swaps, spread). Un tirage choisit au hasard, MOIS PAR MOIS, autant de seances que le filtre reel en a retenu ce
  mois-la dans chaque case (sens achat/vente x tercile de R / prix, R = 0,25 x amplitude 14 j) ; puis on rejoue
  chronologiquement avec un seul panier ouvert a la fois (comme la regle). 1 000 tirages par jeu. Controle : le filtre
  reel rejoue ainsi redonne simule_regle complet. p = (1 + nb placebos >= reel) / (1 + 1 000), sur le R total et le
  R/panier ; H1 4 ans, ses moities (paniers ouverts avant / a partir du 01/10/2024), M15.
VERDICT FIXE D'AVANCE : point 3 -- le filtre « VAUT » si p (R total) < 0,10 sur H1 4 ans ET sur M15 ; sinon « NE VAUT
  PAS » (le p du R/panier est donne a cote). Points 1-2 : pas de verdict, des chiffres ; on dit quel f garde
  P(-30 % en 24 mois) < 10 % en PRUDENT, et si 100 / 500 EUR suffisent.
RESULTAT (execution du 23/11/2026, 16 s) : point 3 NE VAUT PAS (p R total H1 4 ans 0,042, M15 0,119 ; R/panier
  0,029 et 0,107 ; moities H1 0,101 et 0,118). Le filtre reel fait +82,5 R (H1, 220 paniers) contre une mediane
  placebo de +25,4 R ; sur M15 +48,5 contre +20,7. Controle : le rejeu des seances filtrees redonne exactement
  simule_regle (220 / +82,45 R ; 97 / +48,52 R).
  Point 1 : pire perte reelle d'un panier -1,42 R sur l'or (-2,16 R Nasdaq, 2 paniers sous -1,35 R). Plus grand f avec
  P(-30 % en 24 mois) < 10 % en PRUDENT : 1 % pour l'or seul (H1 1,9 %, M15 0,7 %) ; 0,5 % pour les 4 marches ensemble
  (6,2 % ; a 1 % : 60 %). A 2 % or H1 : 13 % mesure / 41 % prudent / 72 % nul ; a 3 % : 49 / 81 / 95 % ; a 12 % :
  100 % partout, ruine 18 % mesure / 50 % prudent (or H1). Ruine ~0 a 0,5-2 % (or seul). Rappel 1-(1-r)^n verifie :
  72 / 36 / 18 / 12 / 3 pertes completes (0,5 / 1 / 2 / 3 / 12 %).
  Point 2 : 500 EUR -> 0 signal ignore partout ; 100 EUR -> or ignore 12-13 % (H1) / 36-38 % (M15) des signaux a
  0,5 %, 1-4 % a 1 %, 0 a 2-3 % ; 4 marches : 9-11 % a 0,5 %. Ecart au rejeu sans contrainte : quelques % du capital
  final (100 EUR, 1 %, or H1 : x1,65 contre x1,83). Budget minimal d'un panier d'or (0,02 lot cent + renforts) aux prix
  d'aujourd'hui : 0,48 EUR ; indices et EUR/USD : 0,03 EUR (lot min indices x 10 : aucun changement).
Ecrit donnees/gpt_tour2a.csv. Usage : python3 banc_gpt_tour2a.py
"""
import os, time, contextlib, io, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_bt_regulier as BR
    import banc_gpt_pyramide as GP
    import banc_multi_marches as MM

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
COUPE = pd.Timestamp("2024-10-01")
K = 1.35
FS = (0.005, 0.01, 0.02, 0.03, 0.12)
FS2 = (0.005, 0.01, 0.02, 0.03)
NPAR, NSEM, PLANCHER, EURUSD = 10000, 104, 0.20, 1.16
NPLA = 1000
PAS = {"or": 0.01, "Nasdaq": 1e-4, "S&P": 1e-4, "EUR/USD": 10.0}       # $ par unite de prix pour 0,01 lot cent
rng = np.random.default_rng(23112026)
ROWS = []


# ---------------------------------------------------------------- donnees
def jeux():
    D1o = GP.params_d1()
    dh = BR.charge("xau_h1_50k"); dh = dh[dh.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
    J = {"or H1": (dh, D1o, True), "or M15": (BR.charge("xau_m15_50k"), D1o, False),
         "Nasdaq": (MM.regroupe(MM.m5_concat("nas_m5_2025a", "nas_m5_90k"), 900), MM.params_d1(BR.charge("nas_d1_5k")), False),
         "S&P": (MM.regroupe(BR.charge("sp_m5_90k"), 900), MM.params_d1(BR.charge("sp_d1_5k")), False),
         "EUR/USD": (MM.regroupe(BR.charge("eur_m5_90k"), 900), MM.params_d1(MM.gj("eur")), False)}
    return J


def increments(EQ, P, part):
    """Increments journaliers (R de V), moins part x R moyen par panier au jour de sortie."""
    x = GP.incr(EQ)
    if part and len(P):
        a = P.groupby(pd.to_datetime(P.t1, unit="s").dt.floor("D")).size() * part * P.g.mean()
        x = x.add(-a, fill_value=0.0)
    return x


def semaines(series, a, b):
    """series : liste de Series journalieres ; a lundi, b dimanche -> matrice (semaines x 7) de la somme."""
    idx = pd.date_range(a, b)
    s = sum(x[(x.index >= a) & (x.index <= b)].reindex(idx).fillna(0.0) for x in series)
    return s.values.reshape(-1, 7)


def lundi_apres(t):
    t = t.normalize(); return t + pd.Timedelta(days=(7 - t.dayofweek) % 7)


def dimanche_avant(t):
    t = t.normalize(); return t - pd.Timedelta(days=(t.dayofweek + 1) % 7)


# ---------------------------------------------------------------- point 1 : Monte-Carlo par semaines
def mc_semaines(W, f, I):
    fv = f / K
    E, pic, dd = np.ones(NPAR), np.ones(NPAR), np.zeros(NPAR)
    mort = np.zeros(NPAR, bool)
    for t in range(I.shape[1]):
        path = E[:, None] * np.maximum(1 + fv * np.cumsum(W[I[:, t]], 1), 0.0)
        path[mort] = E[mort, None]
        sous = path < PLANCHER
        neuf = sous.any(1) & ~mort
        if neuf.any():
            j = sous[neuf].argmax(1)
            v = path[neuf, j]
            path[neuf] = np.where(np.arange(7)[None, :] >= j[:, None], v[:, None], path[neuf])
            mort |= neuf
        pk = np.maximum.accumulate(np.concatenate([pic[:, None], path], 1), 1)[:, 1:]
        dd = np.minimum(dd, (path / pk - 1).min(1))
        pic, E = pk[:, -1], path[:, -1]
    return dict(p_moins30=(dd <= -0.30).mean(), p_ruine=mort.mean(), mediane_x=np.median(E),
                pire_baisse_med=np.median(dd))


# ---------------------------------------------------------------- point 2 : rejeu compte cent
def rejeu(B, f, dep, contrainte, colR="R", kmin=None):
    """B : paniers (t0, t1, g, R, marche) ; compose sur le capital realise ; rend (x final, pire baisse, % ignores)."""
    kmin = kmin or {}
    ev = sorted([(r.t1, 0, i) for i, r in enumerate(B.itertuples())] + [(r.t0, 1, i) for i, r in enumerate(B.itertuples())])
    C0 = dep * EURUSD; C = C0; pic = C0; dd = 0.0; mise = {}; ign = 0
    g, R, mk = B.g.values, B[colR].values, B.marche.values
    for _, typ, i in ev:
        if typ == 1:
            budget = f * max(C, 0.0)
            if contrainte:
                u = PAS[mk[i]]
                k = np.floor(budget / (2 * K * u * R[i]) + 1e-9)
                if k < kmin.get(mk[i], 1):
                    ign += 1; continue
                mise[i] = 2 * k * u * R[i]
            else:
                mise[i] = budget / K
        elif i in mise:
            C += mise.pop(i) * g[i]
            pic = max(pic, C); dd = min(dd, C / pic - 1)
    return C / C0, dd, 100 * ign / max(len(B), 1)


# ---------------------------------------------------------------- point 3 : placebo
def candidats(d, D1, eo):
    hd, _, Rd, d1 = D1
    amp = d1.haut - d1.bas; adr = amp.rolling(14).mean()
    calme = (amp < 0.6 * adr.shift(1)).values
    inside = ((d1.haut <= d1.haut.shift(1)) & (d1.bas >= d1.bas.shift(1))).values
    sma = d1.cloture.rolling(50).mean()
    sens = np.where(d1.cloture > sma, 1, np.where(d1.cloture < sma, -1, 0))
    ok = (adr.notna() & sma.notna() & adr.shift(1).notna()).values & (sens != 0)
    t = d.heure.values; jour = t // 86400
    j8 = np.unique(jour[((t // 3600) % 24 == 8) & ((t // 60) % 60 == 0)])
    k = np.searchsorted(hd, j8 * 86400, "left") - 1
    m = (k >= 0) & ok[np.maximum(k, 0)] & (Rd[np.maximum(k, 0)] > 0)
    C = pd.DataFrame({"jour": j8[m], "k": k[m]})
    C["sens"] = sens[C.k]; C["filtre"] = calme[C.k] | inside[C.k]
    C["rel"] = Rd[C.k] / d1.cloture.values[C.k]
    C["terc"] = pd.qcut(C.rel, 3, labels=False)
    C["mois"] = pd.to_datetime(C.jour * 86400, unit="s").dt.to_period("M")
    debut = np.searchsorted(jour, C.jour.values)
    res = []
    for jj, kk, ss, i0 in zip(C.jour, C.k, C.sens, debut):
        s1 = np.zeros(len(hd), int); s1[kk] = ss
        r = (np.inf, np.inf, 0.0)
        for L in (30, 200, None):
            i1 = len(d) if L is None else np.searchsorted(jour, jj + L)
            P = GP.simule_regle(d.iloc[i0:i1].reset_index(drop=True), (hd, s1, Rd, d1), "A", entree_ouverture=eo)[0]
            if len(P):
                r = (P.t0.iloc[0], P.t1.iloc[0], P.g.iloc[0]); break
            if i1 >= len(d):
                break
        res.append(r)
    C["t0"], C["t1"], C["g"] = np.array(res).T
    return C


def sequence(t0, t1, g, idx):
    """idx trie par t0 ; un panier a la fois (entree seulement si le precedent est sorti avant)."""
    fin, L = -np.inf, []
    for i in idx:
        if t0[i] > fin:
            fin = t1[i]
            if np.isfinite(t1[i]):
                L.append(i)
    return np.array(L, int)


def mesures(C, sel, coupe):
    t0 = C.t0.values[sel]; g = C.g.values[sel]
    out = {"tout": (g.sum(), g.mean() if len(g) else np.nan, len(g))}
    if coupe:
        a = t0 < coupe.timestamp()
        out["1re moitie"] = (g[a].sum(), g[a].mean(), a.sum()); out["2de moitie"] = (g[~a].sum(), g[~a].mean(), (~a).sum())
    return out


def placebo(nom, C, coupe):
    t0, t1, g = C.t0.values, C.t1.values, C.g.values
    reel = sequence(t0, t1, g, np.flatnonzero(C.filtre.values))
    M0 = mesures(C, reel, coupe)
    cases = C[C.filtre].groupby(["mois", "sens", "terc"]).size()
    pools = {key: np.flatnonzero(((C.mois == key[0]) & (C.sens == key[1]) & (C.terc == key[2])).values) for key in cases.index}
    TIR = []
    for _ in range(NPLA):
        ch = np.sort(np.concatenate([rng.choice(pools[key], n, replace=False) for key, n in cases.items()]))
        TIR.append(mesures(C, sequence(t0, t1, g, ch), coupe))
    out = []
    for part in M0:
        tot = np.array([x[part][0] for x in TIR]); moy = np.array([x[part][1] for x in TIR])
        r = dict(section="placebo", jeu=nom, partie=part, paniers_reel=M0[part][2], R_total_reel=M0[part][0],
                 R_panier_reel=M0[part][1], placebo_R_total_med=np.median(tot), placebo_R_total_q90=np.quantile(tot, 0.9),
                 placebo_R_panier_med=np.nanmedian(moy), placebo_paniers_med=np.median([x[part][2] for x in TIR]),
                 p_R_total=(1 + (tot >= M0[part][0]).sum()) / (1 + NPLA),
                 p_R_panier=(1 + (moy >= M0[part][1]).sum()) / (1 + NPLA))
        out.append(r)
    return out, reel


# ---------------------------------------------------------------- programme
if __name__ == "__main__":
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    J = jeux()
    SIM = {}
    for nom, (d, D1, eo) in J.items():
        SIM[nom] = GP.simule_regle(d, D1, "A", entree_ouverture=eo)
        P = SIM[nom][0]
        print("%-8s %s -> %s : %3d paniers, R/panier %+.3f, total %+6.1f R, pire perte d'un panier %+.2f R" % (
            nom, pd.to_datetime(d.heure.iloc[0], unit="s").date(), pd.to_datetime(d.heure.iloc[-1], unit="s").date(),
            len(P), P.g.mean(), P.g.sum(), P.g.min()))
    print("Controle du comptage K = %.2f R : pire perte reelle d'un panier (tous jeux) %+.2f R ; paniers sous -1,35 R : %d"
          % (K, min(SIM[n][0].g.min() for n in SIM), sum(int((SIM[n][0].g < -K).sum()) for n in SIM)))

    # ------------------------------------------------ point 1
    print("\n=== Rappel 1-(1-r)^n : pertes pour atteindre -30 %")
    for f in FS:
        n1 = np.log(0.7) / np.log(1 - f); n2 = np.log(0.7) / np.log(1 - f / K)
        print("  r = %5.1f %% : %5.1f pertes completes (toutes couches) -> %d ; pertes ordinaires (1 R de V = %.2f %%) : %d"
              % (100 * f, n1, int(np.ceil(n1)), 100 * f / K, int(np.ceil(n2))))
        ROWS.append(dict(section="rappel", risque=f, n_pertes_completes=int(np.ceil(n1)), n_pertes_1R=int(np.ceil(n2))))
    MARCHES4 = ["or M15", "Nasdaq", "S&P", "EUR/USD"]
    a4 = lundi_apres(max(SIM[m][1].index[0] for m in MARCHES4)); b4 = dimanche_avant(min(SIM[m][1].index[-1] for m in MARCHES4))
    CAS = {"or H1 4 ans": (["or H1"], lundi_apres(SIM["or H1"][1].index[0]), dimanche_avant(SIM["or H1"][1].index[-1])),
           "or M15": (["or M15"], lundi_apres(SIM["or M15"][1].index[0]), dimanche_avant(SIM["or M15"][1].index[-1])),
           "or seul (periode commune)": (["or M15"], a4, b4),
           "or+Nas+S&P+EUR": (MARCHES4, a4, b4)}
    print("\n=== Point 1 : Monte-Carlo par semaines civiles entieres, 24 mois (104 sem.), %d tirages ; risque f toutes "
          "couches (V = f / %.2f)" % (NPAR, K))
    L1 = []
    for cas, (mk, a, b) in CAS.items():
        Ws = {sc: semaines([increments(SIM[m][1], SIM[m][0], part) for m in mk], a, b)
              for sc, part in (("mesure", 0.0), ("prudent", 0.5), ("nul", 1.0))}
        nw = len(Ws["mesure"])
        I = rng.integers(nw, size=(NPAR, NSEM))
        print("  %s : %s -> %s, %d semaines, R/semaine moyen %+.3f" % (cas, a.date(), b.date(), nw, Ws["mesure"].sum(1).mean()))
        for f in FS:
            for sc, W in Ws.items():
                r = dict(section="MC semaines", cas=cas, semaines=nw, risque=f, scenario=sc, **mc_semaines(W, f, I))
                L1.append(r); ROWS.append(r)
    T1 = pd.DataFrame(L1)
    for v, lib in (("p_moins30", "P(-30 % depuis un sommet)"), ("p_ruine", "P(ruine, sous 20 %)"), ("mediane_x", "valeur mediane (x depart)")):
        print("\n  -- %s" % lib)
        print(T1.pivot_table(index=["cas", "risque"], columns="scenario", values=v, sort=False)[["mesure", "prudent", "nul"]]
              .round(3).to_string())
    ok = T1[(T1.scenario == "prudent") & (T1.p_moins30 < 0.10)].groupby("cas", sort=False).risque.max()
    print("  Plus grand f avec P(-30 %%) < 10 %% en prudent : %s" % " ; ".join("%s %s" % (c, "%.1f %%" % (100 * v)) for c, v in ok.items()))

    # ------------------------------------------------ point 2
    print("\n=== Point 2 : rejeu historique compte cent (V = 2k pas de 0,01 lot cent ; signal ignore si k < 1)")
    def paniers(mk, a=None):
        L = []
        for m in mk:
            P = SIM[m][0].copy(); P["marche"] = "or" if m.startswith("or") else m
            dernier = J[m][0].cloture.iloc[-1]
            P["R_auj"] = P.rrel * dernier
            if a is not None:
                P = P[P.t0 >= a.timestamp()]
            L.append(P)
        return pd.concat(L, ignore_index=True)
    REJ = {"or H1 4 ans": paniers(["or H1"]), "or M15": paniers(["or M15"]), "or+Nas+S&P+EUR": paniers(MARCHES4, a4)}
    L2 = []
    for cas, B in REJ.items():
        for colR, libR in (("R", "R historique"), ("R_auj", "prix d'aujourd'hui")):
            for dep in (100.0, 500.0):
                for f in FS2:
                    xl, ddl, _ = rejeu(B, f, dep, False, colR)
                    xc, ddc, ign = rejeu(B, f, dep, True, colR)
                    r = dict(section="cent", cas=cas, prix=libR, depart=dep, risque=f, paniers=len(B), pct_ignores=ign,
                             x_final=xc, pire_baisse=ddc, x_final_sans_contrainte=xl, pire_baisse_sans_contrainte=ddl)
                    if cas.startswith("or+"):
                        r["x_final_ind_min10"], r["pire_baisse_ind_min10"], r["pct_ignores_ind_min10"] = rejeu(
                            B, f, dep, True, colR, {"Nasdaq": 10, "S&P": 10})
                    L2.append(r); ROWS.append(r)
    T2 = pd.DataFrame(L2)
    print(T2.round(3).to_string(index=False))
    # detail : pas de budget minimal par marche (prix d'aujourd'hui)
    print("  Budget minimal d'un panier (V = 0,02 lot cent + renforts, K = %.2f R), prix d'aujourd'hui, R median :" % K)
    for m in MARCHES4:
        P = SIM[m][0]; Rm = (P.rrel * J[m][0].cloture.iloc[-1]).median()
        bmin = 2 * K * PAS["or" if m.startswith("or") else m] * Rm / EURUSD
        print("    %-8s R median %.5g -> %.3f EUR, soit %.2f %% de 100 EUR / %.2f %% de 500 EUR" % (m, Rm, bmin, bmin, bmin / 5))
        ROWS.append(dict(section="budget minimal", cas=m, R_median=Rm, budget_min_eur=bmin))

    # ------------------------------------------------ point 3
    print("\n=== Point 3 : placebo du filtre calme / inside day (%d tirages, mois x sens x tercile de R/prix)" % NPLA)
    L3 = []
    for nom, coupe in (("or H1", COUPE), ("or M15", None)):
        t1 = time.time()
        d, D1, eo = J[nom]
        C = candidats(d, D1, eo)
        out, reel = placebo(nom, C, coupe)
        P = SIM[nom][0]
        print("  %s : %d seances candidates, %d filtrees ; CONTROLE rejeu du filtre reel %d paniers %+.2f R contre "
              "simule_regle %d paniers %+.2f R (%.0f s)" % (nom, len(C), int(C.filtre.sum()), len(reel), C.g.values[reel].sum(),
                                                         len(P), P.g.sum(), time.time() - t1))
        print("    toutes seances candidates (sans filtre, un panier a la fois) : R/panier %+.3f" %
              C.g.values[sequence(C.t0.values, C.t1.values, C.g.values, np.arange(len(C)))].mean())
        L3 += out; ROWS.extend(out)
    T3 = pd.DataFrame(L3)
    print(T3.drop(columns="section").round(3).to_string(index=False))
    pH = T3[(T3.jeu == "or H1") & (T3.partie == "tout")].p_R_total.iloc[0]
    pM = T3[(T3.jeu == "or M15") & (T3.partie == "tout")].p_R_total.iloc[0]
    verdict = "VAUT" if pH < 0.10 and pM < 0.10 else "NE VAUT PAS"
    print("\nVERDICT point 3 (fixe d'avance) : le filtre %s  [p R total : H1 4 ans %.3f, M15 %.3f]" % (verdict, pH, pM))
    ROWS.append(dict(section="verdict", cas=verdict, p_H1=pH, p_M15=pM))
    pd.DataFrame(ROWS).round(5).to_csv(os.path.join(ICI, "donnees", "gpt_tour2a.csv"), index=False)
    print("Duree %.0f s ; ecrit donnees/gpt_tour2a.csv" % (time.time() - T00))
