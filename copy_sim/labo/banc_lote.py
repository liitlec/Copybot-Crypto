"""Banc Lot E (PRIORITES 23/11 12 h) : verifier l'etude d'Astra « type de seance sur l'or » (copy_sim/labo/astra_seances/).
CONTRAT FIGE ET POUSSE AVANT LES RESULTATS DES POINTS 2 A 5 (seules l'inspection des donnees et l'alignement des heures,
ci-dessous, ont ete faits avant).

CONSTATS D'INSPECTION (avant contrat) :
  - Source H4 GitHub (tohaitrieu GOLD-H4) : vraies bougies 4 h seulement a partir de 06/2013 (avant : 1 bougie par jour).
    Donc ~12,7 ans de H4 (06/2013 -> 06/02/2026), PAS 20 ans.
  - Fuseau : heure de la source = heure serveur STARTRADER - 3 h, ete comme hiver (ecart median des clotures H4 contre
    nos H1 regroupees : 0,2 pb a -3 h, >= 7 pb sinon ; seules les semaines de mars ou les changements d'heure US / Europe
    different restent a 1,6 pb). Le « 9 h » d'Astra = 12:00 serveur = 11 h a Paris (ete comme hiver).

POINT 1 — reproduction : ses scripts, sans modification, dans une copie du dossier (detecter, cassure, verifier,
  calendrier, figer) ; on compare aux tableaux de Resultats_pour_Claude.md (precision « calme », FOMC 0/76, cassure).

POINTS 2-3 — robots du labo, or H1 du courtier 01/08/2022 -> 11/11/2026, decision a 12:00 serveur (son « 9 h ») :
  Drapeaux ecrits chaque jour : FOMC (date de decision programmee, donnees/fomc.csv) ; alerte calme (score_matin.score
  sur nos H1 decalees de -3 h et regroupees en H4 de la source, parametres.json fige, seuil 0,2617) ; cassure
  (sortie « hausse » / « baisse » de score_matin) ; « indetermine » sinon.
  Familles (inchangees, regime_socle._fam_trades) : bt_or (bt_or_h1), tendance = cassure_h1, retour = retour_h1. P&L par
  jour d'entree, en R ; chaque famille mise a ecart-type journalier 1 sur la chauffe 08/2022-01/2023 (risque egal).
  Couts : spread reel x 1,5 (spread + provision de glissement 50 %, comme banc_astra) ; stress spread x 3.
  Bases : bt_or seul, retour seul, 50/50 = 0,5 bt_or + 0,5 retour.
  Regles (12) : sur les jours a drapeau X (FOMC, calme, cassure), suspendre UNE famille pour les entrees a partir de
  12:00 serveur ce jour-la ; les positions ouvertes avant 12:00 sont gardees et suivies a part ; jours sans drapeau
  inchanges. 50/50 : X x {bt_or, retour} = 6 ; bt_or seul : X -> bt_or coupe = 3 ; retour seul : X -> retour coupe = 3.
  Temoin obligatoire : coupure aleatoire, meme nombre de jours coupes dans chaque mois, meme famille, 2000 tirages ;
  p = part des tirages au gain >= gain reel. Rapporte : nombre de signaux, gain contre la base, pire baisse, part des
  semaines perdantes, esperance par semaine et IC 95 % (bootstrap par semaines). Blocs B1 = 08/2022-09/2024,
  B2 = 10/2024-11/2026. Correction : Holm sur les 12 p du temoin.
  RETENU si : bat sa base en B1 ET B2 ET p temoin corrige (Holm) < 0,05 ET bat encore sa base au stress spread x 3.

POINT 4 — le « jour » du lot D sur la source H4 (06/2013 -> 02/2026) : jour serveur = bougies source 21 h (veille), 1, 5,
  9, 13, 17 ; decisions a 7 h Paris (apres la bougie source 1 h), 11 h (apres 5 h) et 15 h (apres 9 h), les heures du
  quadrillage H4 les plus proches de 9 h / 11 h / 14 h. Etiquette = efficacite du reste du jour >= mediane de
  l'apprentissage. Memes 16 variables et memes modeles que banc_lotd_jour (annonces : FOMC + premier vendredi du mois ;
  CPI non disponible avant 2022 ; VIX et GVZ FRED, decalage de 2 jours). Walk-forward croissant (>= 250 jours).
  Argent : bt_or rejoue sur H4 (banc_bt_regulier.simule, span 12, entrees aux bougies source 1, 5, 9, 13 h, spread
  0,51 pb du prix), valide si correlation des R mensuels avec le vrai bt_or H1 (08/2022 -> 02/2026) >= 0,6 et meme
  signe en B1 et B2 ; sinon la partie argent est indicative et seule l'AUC compte.
  RETENU si : borne basse de l'IC 95 % de l'AUC > 0,5 ET (bt_or H4 valide ET bat « toujours 1 » a risque egal en
  2014-2019 ET 2020-2026 ET placebo p < 0,05 ET SPA p < 0,05 sur les 6 regles).

POINT 5 — variante demo `_opt` hors totaux seulement si une regle est RETENUE.
Usage : python3 banc_lote.py
"""
import contextlib, io, json, os, sys, urllib.request, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import regime_socle as S
    import banc_bt_regulier as BR
    import banc_lotd_jour as LJ
from banc_lotd import spa, sr

ICI = os.path.dirname(os.path.abspath(__file__))
AS = os.path.join(ICI, "astra_seances")
sys.path.insert(0, AS)
from score_matin import score
PARAMS = json.load(open(os.path.join(AS, "parametres.json")))
B2_0 = pd.Timestamp("2024-10-01")
rng = np.random.default_rng(31)
FOMC = pd.DatetimeIndex(pd.to_datetime(pd.read_csv(os.path.join(S.DONL, "fomc.csv")).annonce))


def drapeaux():
    h = S.OR_H1.copy(); h.index = h.index - pd.Timedelta(hours=3)
    h = h.rename(columns={"ouverture": "o", "haut": "h", "bas": "l", "cloture": "c"})
    g = h.resample("4h", offset="1h")
    f = g.agg({"o": "first", "h": "max", "l": "min", "c": "last"})[g.size() == 4].dropna()
    rows = {}
    for J in S.JOURS:
        try:
            r = score(f.loc[J - pd.Timedelta(days=65):J + pd.Timedelta(hours=9)], J, PARAMS)
            rows[J] = (r["alerte_calme"], r["cassure_9h"] != "aucune", r["score_calme"])
        except ValueError:
            rows[J] = (False, False, np.nan)
    D = pd.DataFrame(rows, index=["calme", "cassure", "score"]).T
    D["fomc"] = D.index.isin(FOMC)
    D["indetermine"] = ~(D.calme.astype(bool) | D.cassure.astype(bool) | D.fomc)
    return D


def familles(cout):
    T = S._fam_trades(cout)
    e = T.dec + pd.to_timedelta(np.where(T.fam == "bt_or_h1", 3600, 0), unit="s")
    T["apres"] = e.dt.hour >= 12
    out = {}
    for f, k in (("bt_or_h1", "bt_or"), ("retour_h1", "retour"), ("cassure_h1", "tendance")):
        t = T[T.fam == f]
        av = t[~t.apres].groupby("jour").g.sum().reindex(S.JOURS, fill_value=0.0)
        ap = t[t.apres].groupby("jour").g.sum().reindex(S.JOURS, fill_value=0.0)
        out[k] = (av, ap)
    return out


def stats(x):
    eq = x.cumsum(); w = x.groupby(x.index.to_period("W")).sum()
    bs = [w.values[rng.integers(len(w), size=len(w))].mean() for _ in range(1000)]
    return eq.min() if False else (eq - eq.cummax()).min(), (w < 0).mean(), w.mean(), np.quantile(bs, [.025, .975])


def holm(p):
    p = np.asarray(p); o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0
    for k, i in enumerate(o):
        run = max(run, (m - k) * p[i]); adj[i] = min(1, run)
    return adj


def points23():
    D = drapeaux()
    F = {c: familles(c) for c in (1.5, 3.0)}
    ch = (S.JOURS >= S.DEBUT) & (S.JOURS <= S.CHAUFFE_FIN)
    ech = {k: 1 / (av + ap)[ch].std() for k, (av, ap) in F[1.5].items()}
    bases = {"bt_or seul": {"bt_or": 1.0}, "retour seul": {"retour": 1.0}, "50/50": {"bt_or": .5, "retour": .5}}
    print("POINTS 2-3 : drapeaux a 12:00 serveur (11 h Paris), %d jours : FOMC %d, calme %d, cassure %d, indetermine %d" % (
        len(D), D.fomc.sum(), D.calme.sum(), D.cassure.sum(), D.indetermine.sum()))
    print("  bases (u, spread x1,5) : " + " ; ".join("%s B1 %+.0f B2 %+.0f" % (b, *[sum(a * ech[f] * (F[1.5][f][0] + F[1.5][f][1])[m].sum()
          for f, a in w.items()) for m in (S.JOURS < B2_0, S.JOURS >= B2_0)]) for b, w in bases.items()))
    lignes = []
    for b, w in bases.items():
        for X in ("fomc", "calme", "cassure"):
            for coupe in w:
                drap = D[X].astype(bool).reindex(S.JOURS, fill_value=False)
                res = {}
                for c in (1.5, 3.0):
                    base = sum(a * ech[f] * (F[c][f][0] + F[c][f][1]) for f, a in w.items())
                    perte = w[coupe] * ech[coupe] * F[c][coupe][1]
                    res[c] = (base, base - perte * drap, perte)
                base, x, perte = res[1.5]
                gain = (x - base)
                g1, g2 = gain[S.JOURS < B2_0].sum(), gain[S.JOURS >= B2_0].sum()
                # temoin aleatoire : meme nombre de jours coupes par mois
                mois = S.JOURS.to_period("M"); n_m = drap.groupby(mois).sum()
                pv = perte.values; idx_m = {m: np.flatnonzero(mois == m) for m in n_m.index}
                tir = np.zeros(2000)
                for m, n in n_m.items():
                    if n == 0: continue
                    ii = idx_m[m]
                    tir += np.array([-pv[rng.choice(ii, int(n), replace=False)].sum() for _ in range(2000)])
                p = (tir >= gain.sum()).mean()
                dd_b, pw_b, _, _ = stats(base); dd, pw, mw, ic = stats(x)
                b3, x3, _ = res[3.0]
                lignes.append(dict(base=b, drapeau=X, coupe=coupe, signaux=int(drap.sum()), gain_B1=g1, gain_B2=g2,
                                   gain_total=gain.sum(), temoin_med=np.median(tir), p_temoin=p, pire_baisse=dd, pire_base=dd_b,
                                   sem_perdantes=pw, sem_perd_base=pw_b, esp_sem=mw, ic_bas=ic[0], ic_haut=ic[1],
                                   gain_x3=(x3 - b3).sum()))
    T = pd.DataFrame(lignes); T["p_holm"] = holm(T.p_temoin)
    T["retenu"] = (T.gain_B1 > 0) & (T.gain_B2 > 0) & (T.p_holm < 0.05) & (T.gain_x3 > 0)
    T.to_csv(os.path.join(S.DONL, "lote_robots.csv"), index=False)
    pd.set_option("display.width", 250)
    print(T.round(2).to_string(index=False))
    return D


def h4_serveur():
    g = pd.read_csv(os.path.join(S.DONL, "lote", "GOLD-H4.csv.gz"), parse_dates=["Time"]).set_index("Time")
    g = g[g.index >= "2013-06-01"]; g.index = g.index + pd.Timedelta(hours=3)
    d = pd.DataFrame({"ouverture": g.Open, "haut": g.High, "bas": g.Low, "cloture": g.Close}).reset_index(names="t")
    d["heure"] = (d.t - pd.Timestamp("1970-01-01")).dt.total_seconds().astype(int)
    d["sp"] = 0.51e-4 * d.cloture
    d["jour"], d["h"] = d.t.dt.floor("D"), d.t.dt.hour
    return d[d.t.dt.dayofweek < 5].reset_index(drop=True)


def fred_long(i):
    t = urllib.request.urlopen(urllib.request.Request("https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + i,
                               headers={"User-Agent": "curl/8.5.0"}), timeout=60).read().decode()
    s = pd.to_numeric(pd.read_csv(io.StringIO(t), index_col=0, parse_dates=True).iloc[:, 0], errors="coerce").dropna()
    s.index = s.index + pd.Timedelta(days=2); return s


def point4():
    LJ.DECS = {"7 h": 8, "11 h": 12, "15 h": 16}
    d = h4_serveur()
    E = LJ.etiquettes(d); jours = E.index
    vf = fred_long("VIXCLS"); gf = fred_long("GVZCLS")
    vix = vf.reindex(vf.index.union(jours)).ffill().reindex(jours); gvz = gf.reindex(gf.index.union(jours)).ffill().reindex(jours)
    vend1 = jours[(jours.dayofweek == 4) & (jours.day <= 7)]
    X = LJ.variables(d, FOMC.union(vend1), vix, gvz)
    # bt_or sur H4
    H = {(4, 0), (8, 0), (12, 0), (16, 0)}
    P = BR.simule(d, span=12, heures=H, debut=30)
    d2 = d.copy(); d2["sp"] *= 2; P2 = BR.simule(d2, span=12, heures=H, debut=30)
    P["t0"] = P.t0 + 4 * 3600; P2["t0"] = P2.t0 + 4 * 3600          # entree a la cloture de la bougie
    V = S._fam_trades(1.0); V = V[V.fam == "bt_or_h1"]
    mv = pd.period_range("2022-08", "2026-01", freq="M")
    a = P.groupby(pd.to_datetime(P.t0, unit="s").dt.to_period("M")).g.sum().reindex(mv, fill_value=0)
    b = V.groupby(V.dec.dt.to_period("M")).g.sum().reindex(mv, fill_value=0)
    c1 = mv <= pd.Period("2024-09", "M")
    ok = np.corrcoef(a, b)[0, 1] >= 0.6 and np.sign(a[c1].sum()) == np.sign(b[c1].sum()) and np.sign(a[~c1].sum()) == np.sign(b[~c1].sum())
    print("\nPOINT 4 : H4 GitHub %s -> %s, %d jours" % (jours[0].date(), jours[-1].date(), len(jours)))
    print("  bt_or H4 contre vrai bt_or H1 (%d mois) : correlation %.2f ; B1 %+.0f / %+.0f ; B2 %+.0f / %+.0f -> %s" % (
        len(mv), np.corrcoef(a, b)[0, 1], a[c1].sum(), b[c1].sum(), a[~c1].sum(), b[~c1].sum(), "VALIDE" if ok else "NON VALIDE (argent indicatif)"))
    effj = d.groupby("jour").apply(lambda x: abs(x.cloture.iloc[-1] - x.ouverture.iloc[0]) / (x.haut.max() - x.bas.min()))
    print("  persistance de l'efficacite du jour : J/J-1 %.3f ; J/moyenne 5 j %.3f (seuil 2/racine(n) %.3f)" % (
        effj.autocorr(1), np.corrcoef(effj.iloc[5:], effj.shift().rolling(5).mean().iloc[5:])[0, 1], 2 / np.sqrt(len(effj))))
    lignes, Dm = [], []
    M = pd.Timestamp("2020-01-01")
    for nom, hd in LJ.DECS.items():
        av, ap = LJ.r_jour(P, hd, jours); av2, ap2 = LJ.r_jour(P2, hd, jours)
        for mod, fit in (("logistique", LJ.logit_fit), ("arbre", LJ.arbre_fit)):
            W, Pr, Y = LJ.walk_forward(X[nom], E[nom], fit)
            idx = W.index; ref = av[idx] + ap[idx]; x = av[idx] + W * ap[idx]
            x2, ref2 = av2[idx] + W * ap2[idx], av2[idx] + ap2[idx]
            eg = x * ref.std() / x.std()
            au = LJ.auc(Pr.values, Y.values.astype(int))
            bt = [LJ.auc(Pr.values[ii], Y.values[ii].astype(int)) for ii in rng.integers(len(Pr), size=(500, len(Pr)))]
            lo_, hi_ = np.nanquantile(bt, [0.025, 0.975])
            per = idx.to_period("M"); Wv, apv, avv = W.values, ap[idx].values, av[idx].values
            grp = [np.flatnonzero(per == m) for m in per.unique()]
            pl = []
            for _ in range(1000):
                ws = Wv.copy()
                for gi in grp: ws[gi] = rng.permutation(Wv[gi])
                pl.append(sr(pd.Series(avv + ws * apv)))
            pp = (np.array(pl) >= sr(x)).mean()
            b1, b2 = idx < M, idx >= M
            Dm.append((eg - ref).values)
            lignes.append(dict(decision=nom, modele=mod, jours=len(idx), debut=str(idx[0].date()), auc=au, auc_bas=lo_, auc_haut=hi_,
                               part0=(W == 0).mean(), part2=(W == 2).mean(), sr_ref=sr(ref) * np.sqrt(252), sr=sr(x) * np.sqrt(252),
                               gain_2014_19=eg[b1].sum() - ref[b1].sum(), gain_2020_26=eg[b2].sum() - ref[b2].sum(),
                               placebo_p=pp, d_sr_x2=(sr(x2) - sr(ref2)) * np.sqrt(252)))
    L = min(len(x) for x in Dm); pspa, pw = spa(np.column_stack([x[-L:] for x in Dm]))
    T = pd.DataFrame(lignes)
    T["retenu"] = (T.auc_bas > 0.5) & ok & (T.gain_2014_19 > 0) & (T.gain_2020_26 > 0) & (T.placebo_p < 0.05) & (pspa < 0.05)
    T.to_csv(os.path.join(S.DONL, "lote_jour_h4.csv"), index=False)
    print("  SPA p = %.3f ; White p = %.3f" % (pspa, pw))
    print(T.round(3).to_string(index=False))


if __name__ == "__main__":
    points23()
    point4()
