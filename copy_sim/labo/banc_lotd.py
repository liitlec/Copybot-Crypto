"""Banc Lot D (PRIORITES 23/11 11 h 15) : « les prochains MOIS de l'or seront-ils en tendance ? » sur historique long.
CONTRAT FIGE ET POUSSE AVANT TOUT RESULTAT (rien ci-dessous ne sera change apres le premier lancement ; tout ecart
eventuel sera ecrit dans AVIS.md comme ecart au contrat).

DONNEES (publiques, sans cle) :
  - GLD journalier Yahoo (OHLC reels, 18/11/2004 -> 11/2026) = source PRINCIPALE du mime. GC=F journalier Yahoo
    (08/2000 ->) n'a pas de haut/bas avant 2008 (45 % de bougies plates) : seulement en CONTROLE, de 2009 a la fin.
  - FRED : GVZCLS (2008+), DFII10 (2003+), dollar DTWEXM (jusqu'a 12/2005) puis DTWEXBGS (2006+) : seules les
    variations sur 3 mois servent, calculees dans chaque serie (pas de raccord de niveaux). Valeur connue en fin de
    mois = derniere observation datee au plus tard 2 jours avant le dernier jour de bourse du mois (dollar : 10 jours).
  - Vrai bt_or : banc_bt_regulier.simule sur or H1 du courtier (xau_h1_50k, span 48, heures H1 du socle), 08/2022 -> fin.

POINT 1 — MIME JOURNALIER DE bt_or (copie de la mecanique, aucun reglage nouveau) :
  sens = cloture d'hier contre EMA(span 2) des clotures jusqu'a hier ; a l'ouverture du jour, ouvrir un panier dans ce
  sens s'il n'y en a pas deja un de ce cote (les deux cotes peuvent coexister, comme bt_or) ; ATR = moyenne 20 j du
  vrai range, connue hier ; renforts tous les 0,25 ATR dans le sens du prix, 3 positions au plus ; sortie du panier sur
  recul de 0,6667 ATR depuis le meilleur prix. Chemin dans la bougie : O -> bas -> haut -> C si C >= O, sinon
  O -> haut -> bas -> C (convention usuelle) ; un renfort et le stop ne sont jamais declenches sur le meme segment
  dans le sens favorable. Cout = 0,51 pb du prix par entree (spread median de l'or chez le courtier) ; x2 en test.
  Gain d'un panier en R (1 R = perte d'une position au stop initial), rattache au mois d'OUVERTURE.
  VALIDATION (seuil fixe) : sur 08/2022 -> 11/2026, correlation de Pearson des R mensuels mime GLD / vrai bt_or H1
  (rattache aussi au mois d'ouverture) >= 0,6 ET meme signe du total sur B1 = 08/2022-09/2024 et B2 = 10/2024-11/2026.
  Si le mime echoue, rien d'autre ne compte (les points 2-3 sont alors donnes a titre indicatif seulement).
  Pas de variante du mime essayee pour passer le seuil.

POINT 2 — FILTRES LENTS, decides au dernier jour de bourse du mois M avec ce qui est connu, appliques aux paniers
OUVERTS en M+1. N = 18 filtres, chacun donne un score ; mise = 0 / 1 / 2 selon le tercile du score parmi TOUS les
scores des mois precedents (fenetre croissante, 24 mois au moins : sinon mise 1). Sauf F18 (binaire 2 / 0).
  F1-F3   momentum de l'or 3 / 6 / 12 mois (rendement, signe compris)
  F4-F6   |momentum| 3 / 6 / 12 mois divise par la volatilite journaliere 12 mois x racine(jours)  (force de tendance)
  F7      prix / moyenne 200 jours - 1 (signe compris)      F8   |prix / moyenne 200 j - 1|
  F9-F10  efficacite de Kaufman 60 j / 120 j                F11  |pente de regression du log-prix sur 120 j| / vol
  F12     GVZ (niveau)                                      F13  GVZ, variation sur 3 mois
  F14     - variation du taux reel 10 ans sur 3 mois         F15  - variation du dollar sur 3 mois (en %)
  F16-F17 R du mime sur le dernier mois / les 3 derniers mois
  F18     courbe de gains du mime au-dessus de sa moyenne mobile 6 mois -> 2, sinon 0
  F12-F13 commencent quand GVZ a 24 mois d'historique de score ; avant, mise 1.
  WF = choix en walk-forward : chaque mois, le filtre au meilleur rapport moyenne/ecart-type passe (fenetre croissante,
  >= 36 mois de resultats) ; c'est la serie « une seule regle choisie honnetement ».

POINT 3 — JUGEMENT. Serie d'un filtre = mise x R du panier. Reference = « toujours 1 ». Evaluation 01/2007 -> 11/2026.
  Risque egal : chaque serie mensuelle est mise a l'ecart-type mensuel de « toujours 1 » sur tout l'echantillon
  (equivalent a comparer les rapports moyenne/ecart-type) ; totaux montres a risque egal.
  - SPA de Hansen (et White) sur les 18 filtres + WF : differences mensuelles contre « toujours 1 » a risque egal,
    bootstrap stationnaire blocs moyens 6 mois, 2000 tirages -> p corrige.
  - Placebo : la serie de mises du filtre decalee circulairement de 6 a 18 mois (tirage uniforme), 1000 tirages ;
    p = part des placebos au rapport moyenne/ecart-type >= reel.
  - Decennies : D1 = 2007-2016, D2 = 2017-2026.
  - 2022-2026 : memes mises appliquees aux paniers du VRAI bt_or H1 (mois d'ouverture), blocs B1 et B2.
  RETENU si : mime valide ET p SPA < 0,05 ET placebo p < 0,05 ET bat « toujours 1 » a risque egal en D1 ET en D2
  ET sur le vrai bt_or en B1 ET en B2 ET bat encore « toujours 1 » sur tout 2007-2026 au cout double.

POINT 4 — ECHELLE DE TEMPS : regime « tendance » = mois ou la somme glissante sur 6 mois du mime est > 0 ; on compte
  les regimes (suites de meme etat de 3 mois ou plus) sur 2007-2026, sur 2022-2026 et sur les 15 derniers mois ;
  autocorrelation des R mensuels du mime (retards 1 a 3) ; puissance : ecart de rapport moyenne/ecart-type annuel
  detectable a 2 ecarts-types avec n mois (2 x racine(12 / n)), et avec n regimes.

POINT 5 — variante demo bt_or_filtre_opt seulement si un filtre est RETENU. Sinon, dire la meilleure piste restante.
Usage : python3 banc_lotd.py   (ecrit donnees/lotd.csv)
"""
import contextlib, io, os, sys, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_bt_regulier as BR

ICI = os.path.dirname(os.path.abspath(__file__))
DONL = os.path.join(ICI, "donnees")
PAS, STOP, MAXP, COUT = 0.25, 0.6667, 3, 0.51e-4
H1_HEURES = {(2, 0), (7, 0), (11, 0), (14, 0), (15, 0)}
EVAL0, EVAL1 = pd.Period("2007-01", "M"), pd.Period("2026-11", "M")
B1 = (pd.Period("2022-08", "M"), pd.Period("2024-09", "M")); B2 = (pd.Period("2024-10", "M"), pd.Period("2026-11", "M"))
D1 = (pd.Period("2007-01", "M"), pd.Period("2016-12", "M")); D2 = (pd.Period("2017-01", "M"), EVAL1)
rng = np.random.default_rng(23)


def jour(nom):
    d = pd.read_csv(os.path.join(DONL, nom), index_col=0, parse_dates=True)
    return d[~d.index.duplicated()].sort_index()


def mime(d, cout=1.0):
    """Mime journalier de bt_or. Rend les paniers : ouverture, sortie, sens, R."""
    O, H, L, C = (d[x].values for x in ("open", "high", "low", "close"))
    ema = pd.Series(C).ewm(span=2, min_periods=2).mean().values
    tr = np.maximum(H - L, np.maximum(np.abs(H - np.r_[np.nan, C[:-1]]), np.abs(L - np.r_[np.nan, C[:-1]])))
    atr = pd.Series(tr).rolling(20).mean().values
    idx = d.index; P = []; ouvert = {}

    def ajoute(p, s, prix, saut):
        # renforts : niveau atteint ; au saut (ouverture) regle du demi-pas de bt_or
        while len(p["e"]) < MAXP and s * (prix - p["prochain"]) >= 0:
            if not saut or s * (prix - p["prochain"]) <= 0.5 * p["pas"]:
                px = p["prochain"] if not saut else prix
                p["e"].append(px + s * cout * COUT * px)
            p["prochain"] += s * p["pas"]

    def segment(i, a, b, saut=False):
        for s in list(ouvert):
            p = ouvert[s]
            niveau = p["meilleur"] - s * p["stop"]
            if s * (b - niveau) <= 0:                      # stop touche
                sortie = b if saut else niveau
                if saut is False and s * (a - niveau) <= 0: sortie = a
                g = sum(s * (sortie - e) for e in p["e"]) / p["stop"]
                P.append((p["i"], i, s, g)); ouvert.pop(s); continue
            if s * (b - a) > 0:                             # mouvement favorable
                ajoute(p, s, b, saut)
                p["meilleur"] = max(p["meilleur"], b) if s > 0 else min(p["meilleur"], b)

    for i in range(25, len(C)):
        segment(i, C[i - 1], O[i], saut=True)
        if atr[i - 1] > 0:
            s = 1 if C[i - 1] > ema[i - 1] else -1
            if s not in ouvert:
                ouvert[s] = {"i": i, "e": [O[i] + s * cout * COUT * O[i]], "meilleur": O[i], "stop": STOP * atr[i - 1],
                             "pas": PAS * atr[i - 1], "prochain": O[i] + s * PAS * atr[i - 1]}
        chemin = [O[i], L[i], H[i], C[i]] if C[i] >= O[i] else [O[i], H[i], L[i], C[i]]
        for a, b in zip(chemin[:-1], chemin[1:]):
            segment(i, a, b)
    P = pd.DataFrame(P, columns=["i0", "i1", "s", "g"])
    P["m0"] = idx[P.i0].to_period("M"); P["m1"] = idx[P.i1].to_period("M")
    return P


def mensuel(P, col, mois):
    return P.groupby(col).g.sum().reindex(mois, fill_value=0.0)


def vrai_bt_or():
    d = BR.charge("xau_h1_50k")
    d = d[d.heure >= pd.Timestamp("2022-08-01").timestamp()].reset_index(drop=True)
    P = BR.simule(d, span=48, heures=H1_HEURES, debut=60)
    P["m0"] = pd.to_datetime(P.t0, unit="s").dt.to_period("M")
    return P


def fin_de_mois(serie, jours_bourse, retard):
    """Valeur connue au dernier jour de bourse de chaque mois (observation datee <= fin - retard jours)."""
    fins = pd.Series(jours_bourse).groupby(pd.Series(jours_bourse).dt.to_period("M")).max()
    s = serie.dropna()
    out = {}
    for m, f in fins.items():
        v = s[s.index <= f - pd.Timedelta(days=retard)]
        out[m] = v.iloc[-1] if len(v) else np.nan
    return pd.Series(out)


def scores(g, F, Rferme):
    c = g.close; lr = np.log(c).diff()
    fin = c.groupby(c.index.to_period("M")).apply(lambda x: x.index[-1])
    vol = lr.rolling(252).std()
    out = {}
    def at(s): return pd.Series({m: s.get(f, np.nan) for m, f in fin.items()})
    for k, n in ((3, 63), (6, 126), (12, 252)):
        mom = c / c.shift(n) - 1
        out["F%d mom %dm" % ({3: 1, 6: 2, 12: 3}[k], k)] = at(mom)
    for k, n in ((3, 63), (6, 126), (12, 252)):
        f = np.log(c / c.shift(n)).abs() / (vol * np.sqrt(n))
        out["F%d |mom| %dm" % ({3: 4, 6: 5, 12: 6}[k], k)] = at(f)
    mm = c / c.rolling(200).mean() - 1
    out["F7 prix/MM200"] = at(mm); out["F8 |prix/MM200|"] = at(mm.abs())
    for n, nm in ((60, "F9"), (120, "F10")):
        er = (c - c.shift(n)).abs() / c.diff().abs().rolling(n).sum()
        out["%s Kaufman %dj" % (nm, n)] = at(er)
    x = np.arange(120); x = x - x.mean()
    pente = np.log(c).rolling(120).apply(lambda y: (x * (y - y.mean())).sum() / (x * x).sum(), raw=True)
    out["F11 |pente 120j|"] = at(pente.abs() * 120 / (vol * np.sqrt(120)))
    jb = pd.Series(c.index)
    gvz = fin_de_mois(F.GVZCLS, jb, 2); out["F12 GVZ"] = gvz; out["F13 GVZ var 3m"] = gvz - gvz.shift(3)
    tr = fin_de_mois(F.DFII10, jb, 2); out["F14 -taux reel 3m"] = -(tr - tr.shift(3))
    dm = fin_de_mois(F.DTWEXM[F.index <= "2005-12-31"], jb, 10); db = fin_de_mois(F.DTWEXBGS, jb, 10)
    vd = (db / db.shift(3) - 1).where(db.index >= pd.Period("2006-01", "M"), dm / dm.shift(3) - 1)
    out["F15 -dollar 3m"] = -vd
    mois = fin.index
    rf = Rferme.reindex(mois, fill_value=0.0)
    out["F16 mime 1m"] = rf; out["F17 mime 3m"] = rf.rolling(3).sum()
    eq = rf.cumsum(); out["F18 courbe>MM6"] = (eq > eq.rolling(6).mean()).astype(float).where(eq.rolling(6).count() == 6)
    S = pd.DataFrame(out).reindex(mois)
    S.loc[S.index < pd.Period("2005-01", "M"), ["F16 mime 1m", "F17 mime 3m", "F18 courbe>MM6"]] = np.nan
    return S


def mises(S):
    W = pd.DataFrame(1.0, index=S.index, columns=S.columns)
    for col in S:
        if col.startswith("F18"):
            W[col] = S[col].map({1.0: 2.0, 0.0: 0.0}).fillna(1.0); continue
        v = S[col].values
        for t in range(len(v)):
            passe = v[:t][~np.isnan(v[:t])]
            if np.isnan(v[t]) or len(passe) < 24: continue
            q1, q2 = np.quantile(passe, [1 / 3, 2 / 3])
            W.iloc[t, W.columns.get_loc(col)] = 0.0 if v[t] < q1 else (2.0 if v[t] > q2 else 1.0)
    return W.shift(1).fillna(1.0)        # decide en fin de M, applique en M+1


sr = lambda x: x.mean() / x.std() if x.std() > 0 else 0.0


def boot(n, B=2000, b=6.0):
    out = np.empty((B, n), int)
    for k in range(B):
        neuf = rng.random(n) < 1 / b; neuf[0] = True
        bl = np.cumsum(neuf) - 1; deb = np.flatnonzero(neuf)
        out[k] = (rng.integers(n, size=len(deb))[bl] + np.arange(n) - deb[bl]) % n
    return out


def spa(D):
    """D : n x k differences. Rend (p SPA de Hansen consistant, p White)."""
    n = len(D); mu = D.mean(0); sd = D.std(0, ddof=1); sd[sd == 0] = 1e-12
    T = max(0.0, (np.sqrt(n) * mu / sd).max()); V = max(0.0, np.sqrt(n) * mu.max())
    seuil = -np.sqrt(2 * np.log(np.log(n)) / n) * sd
    mu_c = np.where(mu >= seuil, mu, 0.0)
    TS, VW = [], []
    for ii in boot(n):
        mb = D[ii].mean(0)
        TS.append(max(0.0, (np.sqrt(n) * (mb - mu_c) / sd).max())); VW.append(max(0.0, np.sqrt(n) * (mb - mu).max()))
    return (np.array(TS) >= T).mean(), (np.array(VW) >= V).mean()


def tranche(x, a, b): return x[(x.index >= a) & (x.index <= b)]


if __name__ == "__main__":
    gld = jour("lotd_gld_jour.csv.gz"); gc = jour("lotd_or_jour.csv.gz"); F = jour("lotd_fred.csv.gz")
    mois = pd.period_range(gld.index[0].to_period("M"), EVAL1, freq="M")
    P1, P2 = mime(gld), mime(gld, cout=2.0)
    V = vrai_bt_or()
    # ------------------------------------------------ point 1
    mv = pd.period_range("2022-08", EVAL1, freq="M")
    a, b = mensuel(P1, "m0", mv), V.groupby("m0").g.sum().reindex(mv, fill_value=0.0)
    corr = np.corrcoef(a, b)[0, 1]
    tot = lambda x, B: tranche(x, *B).sum()
    ok = corr >= 0.6 and np.sign(tot(a, B1)) == np.sign(tot(b, B1)) and np.sign(tot(a, B2)) == np.sign(tot(b, B2))
    print("POINT 1 mime GLD vs vrai bt_or H1 (R mensuels, mois d'ouverture, %d mois)" % len(mv))
    print("  correlation %.2f ; B1 mime %+.1f / vrai %+.1f ; B2 mime %+.1f / vrai %+.1f ; paniers/mois %.1f / %.1f -> %s" % (
        corr, tot(a, B1), tot(b, B1), tot(a, B2), tot(b, B2), len(P1[P1.m0 >= mv[0]]) / len(mv), len(V) / len(mv),
        "VALIDE" if ok else "NON VALIDE"))
    Pc = mime(gc); mc = pd.period_range("2009-01", EVAL1, freq="M")
    ac, ag = mensuel(Pc, "m0", mc), mensuel(P1, "m0", mc)
    print("  controle GC=F 2009-2026 : correlation mime GC / mime GLD %.2f ; totaux %+.0f / %+.0f R" % (np.corrcoef(ac, ag)[0, 1], ac.sum(), ag.sum()))
    ac22 = mensuel(Pc, "m0", mv); print("  controle GC=F vs vrai bt_or 2022-26 : correlation %.2f" % np.corrcoef(ac22, b)[0, 1])
    R = mensuel(P1, "m0", mois); R2 = mensuel(P2, "m0", mois)
    for nom, (x, y) in {"2007-2016": D1, "2017-2026": D2}.items():
        r = tranche(R, x, y); print("  mime %s : %+.0f R, %d mois, rapport m/e mensuel %.3f" % (nom, r.sum(), len(r), sr(r)))
    # ------------------------------------------------ point 2
    S = scores(gld, F, P1.groupby("m1").g.sum())
    W = mises(S)
    ev = lambda x: tranche(x, EVAL0, EVAL1)
    Re, R2e = ev(R), ev(R2); We = ev(W)
    sd1 = Re.std()
    X = We.mul(Re, axis=0)
    # WF
    wf = pd.Series(1.0, index=We.index)
    for t, m in enumerate(We.index):
        hist = X.iloc[:t]
        disp = [c for c in X if (ev(W)[c].iloc[:t] != 1).sum() >= 1]
        if t >= 36 and disp:
            best = max(disp, key=lambda c: sr(hist[c])); wf.iloc[t] = We[best].iloc[t]
    We["WF choix"] = wf; X["WF choix"] = wf * Re
    X2 = We.mul(R2e, axis=0)
    eg = lambda x, ref: x * (ref.std() / x.std()) if x.std() > 0 else x
    # vrai bt_or
    Rv = b; Wv = W.reindex(mv); Wv["WF choix"] = wf.reindex(mv)
    lignes = []
    D = np.column_stack([eg(X[c], Re).values - Re.values for c in X])
    pspa, pwhite = spa(D)
    for c in X:
        x = X[c]; xe = eg(x, Re)
        pl = []
        w = We[c].values
        for _ in range(1000):
            k = rng.integers(6, 19); pl.append(sr(pd.Series(np.roll(w, k) * Re.values)))
        pp = (np.array(pl) >= sr(x)).mean()
        d1, d2 = tranche(xe, *D1).sum() - tranche(Re, *D1).sum(), tranche(xe, *D2).sum() - tranche(Re, *D2).sum()
        xv = Wv[c] * Rv; xve = eg(xv, Rv)
        v1, v2 = tranche(xve, *B1).sum() - tranche(Rv, *B1).sum(), tranche(xve, *B2).sum() - tranche(Rv, *B2).sum()
        dc = sr(X2[c]) - sr(R2e)
        retenu = ok and pspa < 0.05 and pp < 0.05 and d1 > 0 and d2 > 0 and v1 > 0 and v2 > 0 and dc > 0
        lignes.append(dict(filtre=c, part0=(We[c] == 0).mean(), part2=(We[c] == 2).mean(), sr=sr(x), d_sr=sr(x) - sr(Re),
                           gain_eg=xe.sum() - Re.sum(), D1=d1, D2=d2, placebo_p=pp, vrai_B1=v1, vrai_B2=v2, d_sr_x2=dc, retenu=retenu))
    T = pd.DataFrame(lignes)
    T.to_csv(os.path.join(DONL, "lotd.csv"), index=False)
    print("\nPOINT 2-3 (eval %s -> %s, %d mois ; toujours 1 : %+.0f R, m/e %.3f ; vrai bt_or B1 %+.1f B2 %+.1f)" % (
        EVAL0, EVAL1, len(Re), Re.sum(), sr(Re), tot(Rv, B1), tot(Rv, B2)))
    print("  SPA Hansen p = %.3f ; White p = %.3f (%d regles)" % (pspa, pwhite, D.shape[1]))
    pd.set_option("display.width", 250)
    print(T.round(3).to_string(index=False))
    # ------------------------------------------------ point 4
    print("\nPOINT 4 echelle de temps")
    etat = (R.rolling(6).sum() > 0).astype(int)
    def regimes(e):
        e = e.dropna(); runs = (e != e.shift()).cumsum(); lg = e.groupby(runs).size()
        return len(lg), int((lg >= 3).sum()), lg.mean()
    for nom, (x, y) in {"2007-2026": (EVAL0, EVAL1), "2022-08 -> 2026-11": B1[:1] + B2[1:], "15 derniers mois": (EVAL1 - 14, EVAL1)}.items():
        e = tranche(etat, x, y); n = len(e); k, k3, lm = regimes(e)
        print("  %-20s %3d mois : %d suites d'etat (%d de 3 mois ou plus, longueur moyenne %.1f mois) ; ecart detectable (rapport annuel) %.2f" % (
            nom, n, k, k3, lm, 2 * np.sqrt(12 / n)))
    r = ev(R)
    print("  autocorrelation des R mensuels du mime : " + ", ".join("retard %d : %+.2f" % (k, r.autocorr(k)) for k in (1, 2, 3)),
          "(seuil 2/racine(n) = %.2f)" % (2 / np.sqrt(len(r))))
    print("  part des mois > 0 : %.0f %% ; rapport m/e annuel du mime %.2f" % (100 * (r > 0).mean(), sr(r) * np.sqrt(12)))
