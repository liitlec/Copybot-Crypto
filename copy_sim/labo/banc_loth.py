"""Banc Lot H, tests B1 à B4 (PRIORITES 26/11 19 h 30, demande écrite de Baptiste : « pousser la stratégie au
maximum… s'adapter en live aux trades passés »). CONTRAT FIGÉ ET POUSSÉ AVANT TOUT RÉSULTAT.

DONNÉES : or du courtier, spread réel de chaque bougie (puis doublé). M5 08/2025 -> 11/2026 (15 mois) ; H1 08/2022 ->
11/2026 (4 ans), blocs B1 = 08/2022-09/2024, B2 = 10/2024-11/2026. Mécanique bt_or_plus (entrées bt_or, sens EMA
2 jours, renforts tous les « pas » ATR à la clôture, sortie de tout le panier au recul depuis le meilleur prix), même
convention que banc_lotg.plus. Unité R = perte d'une position de taille 1 au recul de référence 0,6667 ATR.
Argent : compte cent, contrat 1 (journal réel), 1 USD de mouvement x 1 lot = 100 USC ; gain d'un panier en USC =
base x somme(taille_k x sens x (sortie - entrée_k)) x 100. Départ 20 000 USC. Arrêt du pont à -34 % du plus haut.

B1 — INTÉRÊTS COMPOSÉS. Mise fixe (base 0,05) contre mise proportionnelle au solde (v3 : base = 0,05 x solde / 20 000,
  vers le bas au pas 0,01, fixée à l'ouverture de chaque panier, 5 x base <= plafond ; plafond 0,25 = aujourd'hui,
  et 0,50 = borne du pont). Paniers de bt_or_plus tel quel (REF). Rejeu réel (H1 depuis le début de B1 et de B2, M5
  depuis son début) et Monte-Carlo (2 000 parcours, blocs de semaines entières tirées au hasard, longueur moyenne
  4 semaines) sur 6 / 12 / 24 mois ; scénarios mesuré et prudent (avantage ÷ 2 : chaque panier diminué de la moitié du
  R moyen). Mesures : valeur finale (médiane, 10e centile), pire baisse, temps médian pour x2, probabilité d'atteindre
  l'arrêt -34 %.
B2 — FORME DE LA PYRAMIDE (une dimension à la fois autour de REF = 5 positions, pas 0,25, tailles 1-2-3-4-5) :
  positions max {4, 6, 7} ; pas {0,20 ; 0,35} ATR ; tailles {1-1-2-2-3, 1-1,5-2-2,5-3, constante 1}. 8 variantes + REF.
  Les paniers s'ouvrent et se ferment aux mêmes instants (seuls les renforts changent) : comparaison appariée.
  Mesures : gain÷pire baisse et Sharpe journalier (indépendants de la mise : risque égal), total R ; M5, H1 B1, H1 B2 ;
  placebo = signes des différences appariées tirés au hasard (2 000) ; reality check de White sur les 8 ; walk-forward
  (M5 6->1 mois, H1 12->3 mois, choix au meilleur gain÷pire baisse). RETENUE si gain÷pire baisse ET Sharpe > REF sur M5,
  H1 B1 et H1 B2, p White < 0,05 sur un jeu et < 0,15 sur l'autre, walk-forward >= REF sur les deux, et > REF au spread
  double.
B3 — RETRAITS (calcul seulement ; le robot ne retire jamais rien) sur la mise proportionnelle (plafond 0,50), rejeu et
  Monte-Carlo 12 / 24 mois : (a) retirer 20 000 USC au premier doublement ; (b) 25 % et 50 % des gains de la semaine
  chaque lundi ; (c) chaque lundi, tout ce qui dépasse 40 000 USC. Mesures : argent retiré (médiane, 10e centile),
  valeur restante, total (retiré + restant), probabilité d'arrêt -34 %, contre « sans retrait ».
B4 — ADAPTATION EN DIRECT AUX TRADES PASSÉS. Grille bt_or_plus (27) : pas {0,20 ; 0,25 ; 0,35} x recul de sortie
  {0,50 ; 0,6667 ; 0,85} ATR x positions max {3, 5, 7}. Chaque lundi, le réglage est re-choisi sur les paniers FERMÉS
  des N dernières semaines (N = 4, 13, 26 ; critère : total R, puis gain÷pire baisse : 6 règles d'adaptation) et appliqué
  aux paniers ouverts la semaine suivante. Contre « réglage fixe » REF (pas 0,25, recul 0,6667, 5 positions), hors
  échantillon. Placebo : réglage tiré au hasard chaque lundi (même grille), 500 tirages ; p = part des placebos >= réel.
  Règles courtes (listes de trades REF du lot G, M15/M5, 15 mois) : poids de chaque règle chaque lundi = 1 si son résultat
  sur les N dernières semaines est > 0, sinon 0 ; et « proportionnel » (poids = résultat / moyenne des résultats positifs,
  plafonné à 2) ; contre poids 1 fixe ; placebo = poids permutés entre règles chaque semaine (500 tirages).
  Comparaison à risque égal (rapport moyenne/écart-type des P&L hebdomadaires) et en total. RETENUE si bat le fixe en
  B1 ET B2 (H1) et sur M5, p placebo < 0,05 (Holm sur les règles d'adaptation essayées), et encore au spread double.
B5 — ce qui est RETENU -> version réelle suivante (mode auto) ; sinon on reste en v3. Résultats en tête d'AVIS.md.
Usage : python3 banc_loth.py
"""
import os, time, itertools, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_bt_regulier as BR
import banc_lotg as G

ICI = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(26)
B1F, B2_0 = pd.Timestamp("2024-09-30 23:59"), pd.Timestamp("2024-10-01")
DEPART, ARRET = 20000.0, 0.34
TAILLES = {"1-2-3-4-5": lambda k: k + 1.0, "1-1-2-2-3": lambda k: float(k // 2 + 1),
           "1-1,5-2-2,5-3": lambda k: 1.0 + 0.5 * k, "constante": lambda k: 1.0}


def simule(d, span, heures, debut, pas=0.25, recul=0.6667, maxpos=5, tailles="1-2-3-4-5", mult=1.0):
    """bt_or_plus généralisé. Paniers : t0, t1 (s), s, g (R de base à 0,6667 ATR), usd (USD par lot de base x contrat 1)."""
    c, hi, lo, t = (d[x].values for x in ("cloture", "haut", "bas", "heure"))
    sp = d["sp"].values * mult
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=span, min_periods=span).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    taille = TAILLES[tailles]
    P, ouvert = [], {}
    for i in range(debut, len(c)):
        for s in list(ouvert):
            p = ouvert[s]
            niveau = p["meilleur"] - s * p["recul"]
            if (lo[i] <= niveau) if s > 0 else (hi[i] + sp[i] >= niveau):
                usd = sum(w * s * (niveau - e) for w, e in zip(p["w"], p["e"]))
                P.append((t[p["i"]], t[i], s, usd / p["unite"], usd))
                del ouvert[s]
                continue
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            while len(p["e"]) < maxpos and s * (c[i] - p["prochain"]) >= 0:
                if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                    p["e"].append(c[i] + (sp[i] if s > 0 else -sp[i])); p["w"].append(taille(len(p["w"])))
                p["prochain"] += s * p["pas"]
        if (hh[i], mm[i]) in heures and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if s not in ouvert:
                ouvert[s] = {"i": i, "e": [c[i] + (sp[i] if s > 0 else -sp[i])], "w": [taille(0)], "meilleur": c[i],
                             "recul": recul * atr[i], "unite": 0.6667 * atr[i], "pas": pas * atr[i],
                             "prochain": c[i] + s * pas * atr[i]}
    P = pd.DataFrame(P, columns=["t0", "t1", "s", "g", "usd"])
    P["d0"] = pd.to_datetime(P.t0, unit="s"); P["d1"] = pd.to_datetime(P.t1, unit="s"); P["jour"] = P.d1.dt.floor("D")
    return P


def jeux():
    d5, k5 = G.jeu_m5(); dh, kh = G.jeu_h1()
    k5.pop("bars_h"); kh.pop("bars_h")
    return {"M5": (d5, k5), "H1": (dh, kh)}


def mesures(P):
    x = P.groupby("jour").g.sum(); eq = x.cumsum(); dd = (eq - eq.cummax()).min()
    return dict(paniers=len(P), total=P.g.sum(), creux=dd, g_creux=P.g.sum() / -dd if dd < 0 else np.inf,
                sharpe=x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0.0)


# ------------------------------------------------------------------------------------------------ B1 / B3 : argent
def chemin(usd, semaines, plafond=None, prop=True, retrait=None, prudent=0.0):
    """Rejoue une suite de paniers (usd par lot de base, dans l'ordre) avec la mise. Rend dict de mesures.
    semaines : numéro de semaine de chaque panier (retraits du lundi). prudent : USD retirés à chaque panier par lot."""
    solde, haut, retire, arret, t2 = DEPART, DEPART, 0.0, False, None
    pire, s_prec, debut_sem = 0.0, None, DEPART
    double_fait = False
    for k, (u, w) in enumerate(zip(usd, semaines)):
        if s_prec is not None and w != s_prec and retrait is not None and not arret:
            gain_sem = solde - debut_sem
            x = 0.0
            if retrait == "double" and not double_fait and solde >= 2 * DEPART:
                x, double_fait = DEPART, True
            elif retrait in (0.25, 0.5) and gain_sem > 0:
                x = retrait * gain_sem
            elif retrait == "plafond" and solde > 2 * DEPART:
                x = solde - 2 * DEPART
            solde -= x; retire += x
            if x:
                haut = solde        # le plus haut du pont doit repartir après un retrait (sinon arrêt -34 % à tort)
        if s_prec is None or w != s_prec:
            debut_sem = solde
        s_prec = w
        if arret:
            continue
        if prop:
            base = np.floor(0.05 * solde / DEPART / 0.01 + 1e-9) * 0.01
            base = min(base, np.floor(plafond / 5 / 0.01 + 1e-9) * 0.01)
            if base < 0.01:
                arret = True
                continue
        else:
            base = 0.05
        solde += base * (u - prudent) * 100.0
        haut = max(haut, solde)
        pire = min(pire, solde / haut - 1)
        if t2 is None and solde + retire >= 2 * DEPART:
            t2 = k
        if solde <= (1 - ARRET) * haut:
            arret = True
    return dict(final=solde, retire=retire, total=solde + retire, pire=pire, arret=arret, t2=t2)


def montecarlo(P, mois, n=2000, **kw):
    """Blocs de semaines entières (longueur moyenne 4) tirés au hasard ; horizon = mois x 4,33 semaines."""
    P = P.sort_values("t1")
    sem = P.d1.dt.to_period("W")
    groupes = [g.usd.values for _, g in P.groupby(sem)]
    toutes = pd.period_range(sem.min(), sem.max(), freq="W")
    par = {w: g.usd.values for w, g in P.groupby(sem)}
    liste = [par.get(w, np.array([])) for w in toutes]
    H = int(round(mois * 4.33)); R = []
    for _ in range(n):
        u, w, k = [], [], 0
        i = rng.integers(len(liste))
        while k < H:
            if rng.random() < 0.25:
                i = rng.integers(len(liste))
            for x in liste[i % len(liste)]:
                u.append(x); w.append(k)
            k += 1; i += 1
        R.append(chemin(u, w, **kw))
    return pd.DataFrame(R)


def resume_mc(R, mois):
    t2 = R.t2.dropna()
    return dict(final_med=R.final.median(), final_p10=R.final.quantile(0.1), total_med=R.total.median(),
                total_p10=R.total.quantile(0.1), retire_med=R.retire.median(), pire_med=R.pire.median(),
                p_arret=R.arret.mean(), p_x2=(R.total >= 2 * DEPART).mean())


def b1_b3(P, nom):
    P = P.sort_values("t1"); sem = P.d1.dt.to_period("W").astype(str).values
    mu = P.usd.mean()
    out = []
    for mois in (6, 12, 24):
        for lab, kw in (("fixe 0,05", dict(prop=False)), ("prop., plafond 0,25", dict(plafond=0.25)),
                        ("prop., plafond 0,50", dict(plafond=0.50))):
            for scen, pr in (("mesure", 0.0), ("prudent", mu / 2)):
                r = resume_mc(montecarlo(P, mois, n=1000, prudent=pr, **kw), mois)
                out.append(dict(jeu=nom, test="B1", mois=mois, mise=lab, scenario=scen, **r))
    for mois in (12, 24):
        for lab, rt in (("sans retrait", None), ("20 000 au doublement", "double"), ("25 % des gains/sem.", 0.25),
                        ("50 % des gains/sem.", 0.5), ("au-dessus de 40 000", "plafond")):
            for scen, pr in (("mesure", 0.0), ("prudent", mu / 2)):
                r = resume_mc(montecarlo(P, mois, n=1000, prudent=pr, plafond=0.50, retrait=rt), mois)
                out.append(dict(jeu=nom, test="B3", mois=mois, mise=lab, scenario=scen, **r))
    return out


def rejeu(P, debut, fin, **kw):
    x = P[(P.d1 >= debut) & (P.d1 <= fin)].sort_values("t1")
    return chemin(x.usd.values, x.d1.dt.to_period("W").astype(str).values, **kw)


# ------------------------------------------------------------------------------------------------ B2 : pyramide
B2_VARS = {"REF": {}, "pos4": {"maxpos": 4}, "pos6": {"maxpos": 6}, "pos7": {"maxpos": 7}, "pas0,20": {"pas": 0.20},
           "pas0,35": {"pas": 0.35}, "1-1-2-2-3": {"tailles": "1-1-2-2-3"}, "1-1,5-2-2,5-3": {"tailles": "1-1,5-2-2,5-3"},
           "constante": {"tailles": "constante"}}


def b2(J):
    R = {(j, m): {v: simule(d, mult=m, **k, **prm) for v, prm in B2_VARS.items()} for j, (d, k) in J.items() for m in (1.0, 2.0)}
    lignes = []
    for j in J:
        Rj = R[(j, 1.0)]; ref = Rj["REF"]
        difs = {}
        for v in B2_VARS:
            if v == "REF":
                continue
            m = ref.merge(Rj[v], on="t0", suffixes=("_r", "_v"))
            difs[v] = (m.g_v - m.g_r).values
        n = min(len(x) for x in difs.values())
        _, pw = BR.white(np.column_stack([difs[v][:n] for v in difs]))
        for v in B2_VARS:
            P = Rj[v]; row = dict(jeu=j, variante=v, **mesures(P))
            if j == "H1":
                for bn, msk in (("B1", P.jour <= B1F), ("B2", P.jour >= B2_0)):
                    mb = mesures(P[msk]); row[bn + "_gc"], row[bn + "_sh"], row[bn + "_tot"] = mb["g_creux"], mb["sharpe"], mb["total"]
            m2 = mesures(R[(j, 2.0)][v]); row["gc_x2"], row["total_x2"] = m2["g_creux"], m2["total"]
            if v != "REF":
                d_ = difs[v]
                row["placebo_p"] = (np.array([(d_ * rng.choice((-1, 1), len(d_))).sum() for _ in range(2000)]) >= d_.sum()).mean()
                row["white_p"] = pw
            lignes.append(row)
        # walk-forward
        app, tst = (6, 1) if j == "M5" else (12, 3)
        mois = sorted(set(Rj["REF"].jour.dt.to_period("M")))
        wf = rf = 0.0
        for k in range(app, len(mois), tst):
            tr, te = mois[k - app:k], mois[k:k + tst]
            def gc(P):
                x = P[P.jour.dt.to_period("M").isin(tr)]
                if len(x) < 3: return -9
                mm = mesures(x); return mm["g_creux"] if np.isfinite(mm["g_creux"]) else 99
            best = max(B2_VARS, key=lambda v: gc(Rj[v]))
            wf += Rj[best][Rj[best].jour.dt.to_period("M").isin(te)].g.sum()
            rf += Rj["REF"][Rj["REF"].jour.dt.to_period("M").isin(te)].g.sum()
        for row in lignes:
            if row["jeu"] == j:
                row["wf"], row["wf_ref"] = wf, rf
    T = pd.DataFrame(lignes)
    r5 = T[(T.jeu == "M5") & (T.variante == "REF")].iloc[0]; rh = T[(T.jeu == "H1") & (T.variante == "REF")].iloc[0]
    def ok(v):
        if v == "REF": return False
        a = T[(T.jeu == "M5") & (T.variante == v)].iloc[0]; b = T[(T.jeu == "H1") & (T.variante == v)].iloc[0]
        c = (a.g_creux > r5.g_creux and a.sharpe > r5.sharpe and b.B1_gc > rh.B1_gc and b.B1_sh > rh.B1_sh
             and b.B2_gc > rh.B2_gc and b.B2_sh > rh.B2_sh)
        ps = sorted([a.white_p, b.white_p])
        return bool(c and ps[0] < 0.05 and ps[1] < 0.15 and a.wf >= a.wf_ref and b.wf >= b.wf_ref
                    and a.total_x2 > r5.total_x2 and b.total_x2 > rh.total_x2)
    T["retenue"] = T.variante.map(ok)
    return T


# ------------------------------------------------------------------------------------------------ B4 : adaptation
GRILLE = list(itertools.product((0.20, 0.25, 0.35), (0.50, 0.6667, 0.85), (3, 5, 7)))
REFG = (0.25, 0.6667, 5)
ADAPT = [(n, crit) for n in (4, 13, 26) for crit in ("total", "g_creux")]


def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0
    for k, i in enumerate(o):
        run = max(run, (m - k) * p[i]); adj[i] = min(1, run)
    return adj


def serie_semaines(V):
    """V : dict réglage -> paniers. Rend (semaines, matrice réglage x semaine des R par semaine d'OUVERTURE,
    matrice des R par semaine de FERMETURE)."""
    toutes = set()
    for P in V.values():
        toutes |= set(P.d0.dt.to_period("W")) | set(P.d1.dt.to_period("W"))
    sem = pd.period_range(min(toutes), max(toutes), freq="W")
    O = np.array([V[g].groupby(V[g].d0.dt.to_period("W")).g.sum().reindex(sem, fill_value=0).values for g in GRILLE])
    F = np.array([V[g].groupby(V[g].d1.dt.to_period("W")).g.sum().reindex(sem, fill_value=0).values for g in GRILLE])
    return sem, O, F


def choix_adapt(F, n, crit):
    """Réglage choisi chaque semaine w à partir des paniers fermés dans les n semaines d'avant (indices)."""
    nb, W = F.shape; ch = np.full(W, GRILLE.index(REFG))
    for w in range(n, W):
        X = F[:, w - n:w]
        if crit == "total":
            sc = X.sum(1)
        else:
            eq = np.cumsum(X, 1); dd = (eq - np.maximum.accumulate(eq, 1)).min(1)
            sc = np.where(dd < 0, X.sum(1) / -np.minimum(dd, -1e-9), X.sum(1) * 1e3)
        ch[w] = int(np.argmax(sc)) if X.any() else ch[w]
    return ch


def b4_bt(J):
    out = []
    for j, (d, k) in J.items():
        for mult in (1.0, 2.0):
            V = {g: simule(d, pas=g[0], recul=g[1], maxpos=g[2], mult=mult, **k) for g in GRILLE}
            sem, O, F = serie_semaines(V)
            ref = O[GRILLE.index(REFG)]
            debut = 26                                         # même période hors échantillon pour toutes les règles
            blocs = {"tout": np.arange(debut, len(sem))}
            if j == "H1":
                st = sem.start_time
                blocs = {"B1": np.flatnonzero((np.arange(len(sem)) >= debut) & (st <= B1F)),
                         "B2": np.flatnonzero(st >= B2_0)}
            for n, crit in ADAPT:
                ch = choix_adapt(F, n, crit)
                x = O[ch, np.arange(len(sem))]
                row = dict(jeu=j, spread="x2" if mult == 2 else "reel", regle="%d sem., %s" % (n, crit))
                for bn, ix in blocs.items():
                    sr = lambda y: y.mean() / y.std() * np.sqrt(52) if y.std() > 0 else 0
                    row[bn + "_adapt"], row[bn + "_fixe"] = x[ix].sum(), ref[ix].sum()
                    row[bn + "_sh_adapt"], row[bn + "_sh_fixe"] = sr(x[ix]), sr(ref[ix])
                if mult == 1.0:
                    ix = np.arange(debut, len(sem))
                    pl = np.array([O[rng.integers(len(GRILLE), size=len(sem)), np.arange(len(sem))][ix].sum() for _ in range(500)])
                    row["placebo_p"] = (pl >= x[ix].sum()).mean()
                    row["placebo_med"] = np.median(pl)
                    row["reglage_freq"] = str(pd.Series([GRILLE[c] for c in ch[debut:]]).value_counts().index[0])
                out.append(row)
    T = pd.DataFrame(out)
    return T


def b4_courtes():
    debut = pd.Timestamp("2025-08-06")
    S = {}
    for nom, (fic, regle, ks, hs, ref) in G.REGLES.items():
        d = G.charge_tf(fic, debut)
        T = G.joue(d, G.signal(d, regle, ref[0]), ref[1], None, retour=(regle == "retour"))
        S[nom] = T.groupby(T.t.dt.to_period("W")).g.sum()
    M = pd.DataFrame(S).fillna(0.0).sort_index()
    out = []
    for n in (4, 13, 26):
        for mode in ("0/1", "proportionnel"):
            W = np.ones_like(M.values)
            for w in range(len(M)):
                if w < n:
                    continue
                r = M.values[w - n:w].sum(0)
                if mode == "0/1":
                    W[w] = (r > 0).astype(float)
                else:
                    pos = r[r > 0]
                    W[w] = np.clip(r / pos.mean(), 0, 2) if len(pos) else 0.0
            ix = np.arange(26, len(M))
            x = (W * M.values).sum(1)[ix]; f = M.values.sum(1)[ix]
            pl = []
            for _ in range(500):
                Wp = np.array([rng.permutation(row) for row in W])
                pl.append((Wp * M.values).sum(1)[ix].sum())
            sr = lambda y: y.mean() / y.std() * np.sqrt(52) if y.std() > 0 else 0
            moit = len(ix) // 2
            out.append(dict(regle="%d sem., %s" % (n, mode), semaines=len(ix), adapt=x.sum(), fixe=f.sum(),
                            adapt_m1=x[:moit].sum(), fixe_m1=f[:moit].sum(), adapt_m2=x[moit:].sum(), fixe_m2=f[moit:].sum(),
                            sh_adapt=sr(x), sh_fixe=sr(f), placebo_p=(np.array(pl) >= x.sum()).mean()))
    return pd.DataFrame(out)


if __name__ == "__main__":
    t0 = time.time()
    pd.set_option("display.width", 320); pd.set_option("display.max_columns", 40)
    J = jeux()
    REF = {j: simule(d, **k) for j, (d, k) in J.items()}
    print("== B1 / B3 : argent (depart 20 000 USC, Monte-Carlo 1 000 parcours)")
    lignes = []
    for j in ("H1", "M5"):
        lignes += b1_b3(REF[j], j)
    A = pd.DataFrame(lignes); A.to_csv(os.path.join(ICI, "donnees", "loth_argent.csv"), index=False)
    print(A.round(3).to_string(index=False))
    P = REF["H1"]
    print("\n  rejeu reel (H1) :")
    for nom, (a, b) in {"B1 2022-24": (pd.Timestamp("2022-08-01"), B1F), "B2 2024-26": (B2_0, pd.Timestamp("2026-12-31"))}.items():
        for lab, kw in (("fixe", dict(prop=False)), ("prop. 0,25", dict(plafond=0.25)), ("prop. 0,50", dict(plafond=0.50))):
            r = rejeu(P, a, b, **kw)
            print("   %-10s %-11s final %8.0f  pire %+.1f %%  arret %s  t2 %s" % (nom, lab, r["final"], 100 * r["pire"], r["arret"], r["t2"]))
    x = REF["M5"]
    for lab, kw in (("fixe", dict(prop=False)), ("prop. 0,25", dict(plafond=0.25)), ("prop. 0,50", dict(plafond=0.50))):
        r = rejeu(x, x.d1.min(), x.d1.max(), **kw)
        print("   M5 15 mois %-11s final %8.0f  pire %+.1f %%  arret %s" % (lab, r["final"], 100 * r["pire"], r["arret"]))
    print("   pire panier (H1) : %.0f USD par lot = %.0f USC a base 0,05 (%.1f %% de 20 000)" % (
        P.usd.min(), P.usd.min() * 0.05 * 100, P.usd.min() * 0.05 * 100 / DEPART * 100))
    print("\n== B2 : forme de la pyramide")
    T2 = b2(J); T2.to_csv(os.path.join(ICI, "donnees", "loth_pyramide.csv"), index=False)
    print(T2.round(3).to_string(index=False))
    print("\n== B4 : adaptation en direct, bt_or_plus (27 reglages)")
    T4 = b4_bt(J)
    h = T4[(T4.jeu == "H1") & (T4.spread == "reel")]
    T4.loc[h.index, "p_holm"] = holm(h.placebo_p.values)
    m5 = T4[(T4.jeu == "M5") & (T4.spread == "reel")].set_index("regle"); x2 = T4[T4.spread == "x2"]
    def ret(r):
        if r.jeu != "H1" or r.spread != "reel": return False
        a = m5.loc[r.regle]
        h2 = x2[(x2.jeu == "H1") & (x2.regle == r.regle)].iloc[0]
        return bool(r.B1_adapt > r.B1_fixe and r.B2_adapt > r.B2_fixe and a.tout_adapt > a.tout_fixe and r.p_holm < 0.05
                    and a.placebo_p < 0.05 and h2.B1_adapt > h2.B1_fixe and h2.B2_adapt > h2.B2_fixe)
    T4["retenue"] = T4.apply(ret, axis=1)
    T4.to_csv(os.path.join(ICI, "donnees", "loth_adapt_bt.csv"), index=False)
    print(T4.round(3).to_string(index=False))
    print("\n== B4 : adaptation des regles courtes (poids sur le resultat recent)")
    T5 = b4_courtes(); T5["p_holm"] = holm(T5.placebo_p.values)
    T5.to_csv(os.path.join(ICI, "donnees", "loth_adapt_courtes.csv"), index=False)
    print(T5.round(3).to_string(index=False))
    print("\nfait en %.0f s" % (time.time() - t0))
