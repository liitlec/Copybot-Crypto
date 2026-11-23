"""Banc Lot C (PRIORITES 23/11 11 h, demande ecrite de Baptiste) : « encaisser plus qu'on ne depose ».
Compte DEMO / labo, aucun ordre. Critere de ce lot : ARGENT NET ENCAISSE = retraits cumules - depots cumules (recharges
apres ruine comprises), a 6, 12 et 24 mois. Le capital restant sur le compte N'EST PAS compte (il est donne a part :
« net + compte »).

CONTRAT FIXE AVANT TOUT RESULTAT (commit separe, avant le premier lancement) :
Strategies (rien n'est regle, tout est importe tel quel) :
  bt_or    : banc_bt_regulier.simule sur l'or H1 du courtier 08/2022 -> 11/2026 (reglage H1 : EMA 48, heures
             banc_jumeau.H_H1, debut 60) ; controle attendu 956 paniers / +153,4 R (banc_gpt_tour2b). 1 R = perte de la
             1re position a son stop initial ; le panier peut ajouter 2 positions (pire cas 4,125 R).
  calme    : regle d'Astra « cassure apres seance tres calme » = banc_gpt_pyramide.simule_regle version A, or H1, entree a
             l'ouverture de la bougie de 08:00 (comme banc_gpt_tour2a « or H1 ») ; controle 220 paniers / +82,45 R.
             1 R = perte de V au stop initial (renforts compris dans g ; pire cas ~1,35 R).
  rebonds  : repli_ind (4 indices US, chaque indice = ses propres trades) + rebond_nas, construits comme regime_socle
             (D1 du courtier, financement de nuit compris) ; un trade = une periode continue en position ; cout = 1 spread
             reel par aller-retour. Pas de stop : 1 R = ecart-type des rendements de trade de la sous-regle sur les trades
             SORTIS AVANT le 01/08/2022 (connu d'avance).
  Risque f = fraction du capital perdue a 1 R (meme convention pour les 3 ; « toutes couches » plus haut, voir ci-dessus).
Blocs : B1 = paniers ouverts du 01/08/2022 au 30/09/2024, B2 = a partir du 01/10/2024 (coupe de banc_gpt_pyramide).
Moteur (le meme pour rejeu et Monte-Carlo) : semaines civiles (lundi -> dimanche, rattachement par heure de SORTIE du
  panier), paniers d'une semaine joues un par un dans l'ordre de sortie ; mise d'un panier = f x m^k x capital (plafond
  100 % du capital), k = nombre de pertes d'affilee (plafond 3 paliers), remis a 0 apres un panier >= 0. Le chevauchement
  de paniers est ignore (approximation : la mise est fixee sur le capital apres le panier precedent).
  Ruine = capital < 20 % du depot (1) : le reste est retire (compte comme encaisse), puis recharge de 1 si il en reste
  (0, 1 ou 2 recharges permises), sinon arret.
  Regles de retrait (fin de semaine) : 0 aucune ; a = retirer le depot (1) des que le capital >= 2, une fois par depot,
  puis jouer avec les gains ; b = retirer 50 % du gain de la semaine s'il est positif ; c = retirer tout ce qui depasse
  1,5 fois le depot.
  Grille : m = 1 / 1,5 / 2 / 3 ; f = 1 / 2 / 3 / 6 / 12 % ; retraits 0 / a / b / c ; recharges 0 / 1 / 2.
  Temoin de chaque combinaison = meme f, meme retrait, meme recharge, m = 1 (mise fixe).
Scenarios : mesure ; prudent = chaque panier perd la moitie du R moyen du bloc (avantage / 2, obligatoire) ; nul = tout
  le R moyen retire (le jeu est equitable : montre si les retraits changent l'esperance).
Monte-Carlo : bootstrap stationnaire de semaines entieres (blocs moyens 4 semaines), 104 semaines, 2 000 parcours,
  tire dans B1 seul, dans B2 seul, et dans les deux (« tout »). Rejeu historique reel : (i) chaque bloc depuis son debut
  (104 semaines ou ce qui existe) ; (ii) departs glissants chaque 4 semaines sur 08/2022 -> 11/2026, horizon 52 semaines.
Mesures : net encaisse (moyenne, mediane, 10e centile), P(net > 0) a 6 / 12 / 24 mois, ruines moyennes, pire net
  (1er centile), net + compte (moyenne).
Point 1 : calme par bloc, rejeu, f = 12 % et 1 %, m = 1 et m = 2 (« mise augmentee apres perte »), aucun retrait :
  % par semaine (geometrique), pire baisse du capital (paniers). Point 2 : bt_or idem a f = 0,5 / 1 / 2 / 3 %.
VERDICT FIXE D'AVANCE (point 4) : une combinaison « PASSE » si, en PRUDENT, sur le Monte-Carlo B1 ET sur B2, a 24 mois :
  net encaisse moyen > 0, median > 0 et P(net > 0) >= 50 %. Une combinaison avec m > 1 ne compte que si elle bat aussi
  son temoin m = 1 (net moyen prudent) sur B1 ET B2 ; sinon c'est la mise fixe qui est retenue. Variante demo `_opt`
  seulement si une combinaison passe ET differe de ce qui tourne deja (bt_or a mise fixe sans retrait).
RESULTAT (execution du 23/11/2026, 374 s) : controles exacts (bt_or 956 / +153,4 R ; calme 220 / +82,45 R).
  R moyen par panier B1 / B2 : bt_or -0,002 / +0,325 ; calme +0,269 / +0,509 ; rebonds +0,136 / +0,286.
  Point 1 (calme, rejeu, sans retrait) : 1 % -> +0,25 / +0,41 %/sem. (pire baisse -25 / -12 %) ; 12 % -> x0,71 avec -98 %
    (B1) et ruine (B2) ; mise x2 apres perte : 1 % -> -0,34 / +0,67 %/sem. (-88 / -58 %), 12 % -> ruine sur les deux.
  Point 2 (bt_or, rejeu) : B1 -0,03 / -0,09 / -0,34 / -0,73 %/sem. a 0,5 / 1 / 2 / 3 % ; B2 +0,66 / +1,26 / +2,29 / +3,11.
  Point 3 : les retraits ne creent pas d'esperance (scenario nul : net + compte ~0 partout ; en mesure ils baissent le
    total, ex. bt_or 3 % : 6,0 depots sans retrait contre 1,2 a 3,7) ; ils changent la forme (argent deja sorti).
    Pas d'effet « apres une perte » dans les donnees (R du panier suivant : calme -0,42 puis +0,28, t < 1 ; rebonds
    -0,09 / -0,20) : la mise augmentee = mise plus grosse, rien de plus.
  Point 4 : 44 combinaisons PASSENT (calme et rebonds ; une seule bt_or : m 2 / 1 % / b / 1 recharge, rejeu reel B1
    -0,72 depot, ecartee de fait). Retenue pour la demo (poche virtuelle
    encaisse_calme_opt, v26) : calme, m 1,5, 6 %, retrait c, 2 recharges : prudent B1 / B2 net moyen +1,58 / +1,52
    depot, median +0,88 / +1,10, P(net > 0) 59 / 64 %, 10e centile -2,43 / -2,12, ruines moyennes 2,5 / 2,0 ; rejeu
    reel 24 mois +2,77 / +6,74 (mesure). Plus sure mais a mise fixe : rebonds 12 % / c / 2 recharges (P 56 / 87 %,
    10e centile -1,00 / -0,24, ~0 ruine).
Ecrit donnees/lotc.csv. Usage : python3 banc_lotc.py
"""
import os, time, contextlib, io, warnings, itertools
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_bt_regulier as BR
    import banc_jumeau as BJ
    import banc_gpt_pyramide as GP
    import regime_socle as S

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
DEBUT, COUPE = pd.Timestamp("2022-08-01"), pd.Timestamp("2024-10-01")
MS, FS, RETS, RECH = (1.0, 1.5, 2.0, 3.0), (0.01, 0.02, 0.03, 0.06, 0.12), ("0", "a", "b", "c"), (0, 1, 2)
KMAX, NPAR, NSEM, BLOC, PLANCHER = 3, 2000, 104, 4.0, 0.2
HZ = {6: 26, 12: 52, 24: 104}
rng = np.random.default_rng(23112311)
LIGNES = []


# ================================================================ paniers
def paniers():
    dh = BR.charge("xau_h1_50k")
    dh = dh[dh.heure >= DEBUT.timestamp()].reset_index(drop=True)
    P = BR.simule(dh, span=48, heures=BJ.H_H1, debut=60)
    print("controle bt_or H1 : %d paniers %+.1f R (attendu 956 / +153,4)" % (len(P), P.g.sum()))
    out = {"bt_or": pd.DataFrame(dict(t0=pd.to_datetime(P.t0, unit="s"), t1=pd.to_datetime(P.t1, unit="s"), g=P.g))}
    Q, _, _ = GP.simule_regle(dh, GP.params_d1(), sortie="A", entree_ouverture=True)
    print("controle calme H1 : %d paniers %+.2f R (attendu 220 / +82,45)" % (len(Q), Q.g.sum()))
    out["calme"] = pd.DataFrame(dict(t0=pd.to_datetime(Q.t0, unit="s"), t1=pd.to_datetime(Q.t1, unit="s"), g=Q.g))
    rows = []
    for k, o in S.IND.items():
        c = o["cloture"]; dc = c.diff(); up, dn = dc.clip(lower=0), (-dc).clip(lower=0)
        rsi = 100 - 100 / (1 + up.ewm(alpha=.5, adjust=False).mean() / dn.ewm(alpha=.5, adjust=False).mean())
        m200, m5 = c.rolling(200).mean(), c.rolling(5).mean()
        ret = (c.pct_change().fillna(0) - S.finance(c.index)).values
        spr = (o["sp"] / c).values
        i, n = 200, len(c)
        while i < n - 1:
            if rsi.iloc[i] < 10 and c.iloc[i] > m200.iloc[i]:
                j = i + 1
                while j < n - 1 and not (c.iloc[j] > m5.iloc[j] or j - i >= 10):
                    j += 1
                r = np.prod(1 + ret[i + 1:j + 1]) - 1 - spr[i]
                rows.append(("repli_" + k, c.index[i], c.index[j], r))
                i = j + 1
            else:
                i += 1
    o = S.IND["NAS"]; c = o["cloture"]
    amp = (o["haut"] - o["bas"]) / c.shift(1); med = amp.shift(1).rolling(20).median()
    s = -np.sign(c - c.shift(1)).where(amp > 1.5 * med, 0).shift(1).fillna(0)
    r = (o["cloture"] - o["ouverture"]) / o["ouverture"]
    for t in s.index[s != 0]:
        rows.append(("rebond_nas", t, t, s[t] * r[t] - o["sp"][t] / o["ouverture"][t]))
    T = pd.DataFrame(rows, columns=["sous", "t0", "t1", "r"])
    T["t1"] = T.t1 + pd.Timedelta("23h")
    ech = T[T.t1 < DEBUT].groupby("sous").r.std()
    print("rebonds : 1 R (ecart-type avant 08/2022) :", ", ".join("%s %.2f %%" % (k, 100 * v) for k, v in ech.items()),
          "; trades avant :", T[T.t1 < DEBUT].groupby("sous").size().to_dict())
    T["g"] = T.r / T.sous.map(ech)
    T = T[T.t0 >= DEBUT]
    out["rebonds"] = T[["t0", "t1", "g"]].reset_index(drop=True)
    for k, P in out.items():
        P = P.sort_values("t1", kind="stable").reset_index(drop=True)
        P["bloc"] = np.where(P.t0 < COUPE, "B1", "B2")
        out[k] = P
        for b in ("B1", "B2"):
            x = P[P.bloc == b].g
            print("  %-8s %s : %4d paniers, R moyen %+.3f, total %+7.1f R" % (k, b, len(x), x.mean(), x.sum()))
    return out


def semaines(P, bloc=None):
    """Liste des semaines (lundi) du bloc -> matrice (semaines x kmax) de g (NaN = pas de panier)."""
    fin = pd.Timestamp("2026-11-09")
    a, b = {"B1": (DEBUT, COUPE), "B2": (COUPE, fin), None: (DEBUT, fin)}[bloc]
    a = a - pd.Timedelta(days=a.dayofweek)
    lun = pd.date_range(a, b, freq="7D")
    lun = lun[lun + pd.Timedelta(days=7) <= b + pd.Timedelta(days=7)]
    Q = P if bloc is None else P[P.bloc == bloc]
    w = ((Q.t1 - a).dt.days // 7).values
    ok = (w >= 0) & (w < len(lun))
    w, g = w[ok], Q.g.values[ok]
    kmax = max(1, np.bincount(w, minlength=len(lun)).max())
    M = np.full((len(lun), kmax), np.nan)
    pos = np.zeros(len(lun), int)
    for wi, gi in zip(w, g):
        M[wi, pos[wi]] = gi; pos[wi] += 1
    return M, lun


def tirages(n, npar, T):
    neuf = rng.random((npar, T)) < 1 / BLOC; neuf[:, 0] = True
    deb = np.maximum.accumulate(np.where(neuf, np.arange(T), 0), axis=1)
    start = np.take_along_axis(rng.integers(n, size=(npar, T)), deb, axis=1)
    return (start + np.arange(T) - deb) % n


# ================================================================ moteur
def moteur(G, m, configs):
    """G : (parcours, semaines, kmax) de g (NaN = rien). configs : liste de (f, retrait, recharge).
    Rend dict horizon -> (net, net+compte, ruines) de forme (len(configs), parcours) ; et pire baisse, capital final."""
    npar, T, kmax = G.shape
    C = len(configs)
    f = np.repeat([c[0] for c in configs], npar)
    rt = np.repeat([c[1] for c in configs], npar)
    rc = np.repeat([c[2] for c in configs], npar)
    Gx = np.tile(G, (C, 1, 1))
    n = C * npar
    cap, dep, ret = np.ones(n), np.ones(n), np.zeros(n)
    used, vivant, lvl, recup = np.zeros(n), np.ones(n, bool), np.zeros(n), np.zeros(n, bool)
    ruines, pic, dd = np.zeros(n), np.ones(n), np.zeros(n)
    ra, rb, rcc = rt == "a", rt == "b", rt == "c"
    res = {}
    for w in range(T):
        cap0 = cap.copy()
        for k in range(kmax):
            g = Gx[:, w, k]
            act = vivant & ~np.isnan(g)
            if not act.any():
                continue
            gg = np.where(act, g, 0.0)
            mise = np.minimum(f * m ** lvl, 1.0) * cap
            cap = np.maximum(cap + mise * gg, 0.0)
            lvl = np.where(act, np.where(gg < 0, np.minimum(lvl + 1, KMAX), 0), lvl)
            pic = np.maximum(pic, cap); dd = np.minimum(dd, cap / np.maximum(pic, 1e-12) - 1)
            ru = act & (cap < PLANCHER)
            if ru.any():
                ruines += ru; ret += np.where(ru, cap, 0); cap0 = np.where(ru, 0.0, cap0)
                re = ru & (used < rc)
                dep += re; used += re; cap = np.where(ru, np.where(re, 1.0, 0.0), cap)
                cap0 = np.where(re, 1.0, cap0)
                vivant &= ~(ru & ~re); lvl = np.where(ru, 0, lvl); recup = np.where(ru, False, recup)
                pic = np.where(re, 1.0, pic)
        # retraits de fin de semaine
        x = vivant & ra & ~recup & (cap >= 2)
        ret += x; cap -= x; recup |= x
        x = vivant & rb & (cap > cap0)
        y = np.where(x, 0.5 * (cap - cap0), 0); ret += y; cap -= y
        x = vivant & rcc & (cap > 1.5)
        y = np.where(x, cap - 1.5, 0); ret += y; cap -= y
        for h, wk in HZ.items():
            if w == wk - 1:
                res[h] = ((ret - dep).reshape(C, npar), (ret + cap - dep).reshape(C, npar), ruines.reshape(C, npar).copy())
    return res, dd.reshape(C, npar), cap.reshape(C, npar)


def scen(M, P, bloc, part):
    mu = P.g.mean() if bloc is None else P[P.bloc == bloc].g.mean()
    return M - part * mu


GRILLE = [(f, r, k) for f in FS for r in RETS for k in RECH]


def resume(h, net, tot, ru):
    return dict(h=h, moy=net.mean(), med=np.median(net), c10=np.percentile(net, 10), c01=np.percentile(net, 1),
                ppos=(net > 1e-9).mean(), tot=tot.mean(), ruines=ru.mean())


# ================================================================ points 1 et 2 : rejeu sans retrait
def rejeu_simple(PA, strat, fs, ms):
    print("\n=== Point %s : %s, rejeu historique par bloc, aucun retrait, aucune recharge ===" % (
        "1" if strat == "calme" else "2", strat))
    print("%-4s %6s %4s | %5s | %9s | %8s | %8s" % ("bloc", "f", "m", "sem.", "% / sem.", "x final", "pire b."))
    for b in ("B1", "B2"):
        M, lun = semaines(PA[strat], b)
        G = M[None, :, :]
        for m in ms:
            res, dd, cap = moteur(G, m, [(f, "0", 0) for f in fs])
            for i, f in enumerate(fs):
                fin = cap[i, 0]; T = M.shape[0]
                pw = 100 * (fin ** (1 / T) - 1) if fin > 0 else -100.0
                print("%-4s %5.1f%% %4.1f | %5d | %+8.2f%% | %8.2f | %7.0f%%" % (b, 100 * f, m, T, pw, fin, 100 * dd[i, 0]))
                LIGNES.append(dict(point="1-2", strat=strat, bloc=b, f=f, m=m, semaines=T, pct_sem=pw, x_final=fin,
                                   pire_baisse=dd[i, 0]))


# ================================================================ point 3
def point3(PA):
    tab = {}
    for strat, P in PA.items():
        for bloc in ("B1", "B2", None):
            M, lun = semaines(P, bloc)
            idx = tirages(M.shape[0], NPAR, NSEM)
            for nsc, part in (("mesure", 0.0), ("prudent", 0.5), ("nul", 1.0)):
                Gs = scen(M, P, bloc, part)[idx]
                for m in MS:
                    res, _, _ = moteur(Gs, m, GRILLE)
                    for h, (net, tot, ru) in res.items():
                        for i, (f, r, k) in enumerate(GRILLE):
                            d = resume(h, net[i], tot[i], ru[i])
                            d.update(point=3, mode="mc", strat=strat, bloc=bloc or "tout", scen=nsc, m=m, f=f, retrait=r,
                                     recharge=k)
                            LIGNES.append(d); tab[strat, bloc or "tout", nsc, m, f, r, k, h] = d
            print("  %s %s fait (%.0f s)" % (strat, bloc or "tout", time.time() - T00), flush=True)
        # rejeu historique : chaque bloc depuis son debut (mesure et prudent), departs glissants (52 semaines)
        for bloc in ("B1", "B2"):
            M, lun = semaines(P, bloc)
            T = min(NSEM, M.shape[0])
            for nsc, part in (("mesure", 0.0), ("prudent", 0.5)):
                G = scen(M, P, bloc, part)[None, :T, :]
                if T < NSEM:
                    G = np.concatenate([G, np.full((1, NSEM - T, G.shape[2]), np.nan)], axis=1)
                for m in MS:
                    res, _, _ = moteur(G, m, GRILLE)
                    for h, (net, tot, ru) in res.items():
                        for i, (f, r, k) in enumerate(GRILLE):
                            d = dict(point=3, mode="rejeu_bloc", strat=strat, bloc=bloc, scen=nsc, m=m, f=f, retrait=r,
                                     recharge=k, h=h, moy=net[i, 0], med=net[i, 0], tot=tot[i, 0], ruines=ru[i, 0],
                                     semaines_reelles=T)
                            LIGNES.append(d); tab[strat, bloc, "rejeu_" + nsc, m, f, r, k, h] = d
        M, lun = semaines(P, None)
        deps = np.arange(0, M.shape[0] - 52 + 1, 4)
        G = np.stack([M[d0:d0 + 52] for d0 in deps])
        G = np.concatenate([G, np.full((len(deps), NSEM - 52, M.shape[1]), np.nan)], axis=1)
        for m in MS:
            res, _, _ = moteur(G, m, GRILLE)
            net, tot, ru = res[12]
            for i, (f, r, k) in enumerate(GRILLE):
                d = resume(12, net[i], tot[i], ru[i])
                d.update(point=3, mode="rejeu_glissant", strat=strat, bloc="tout", scen="mesure", m=m, f=f, retrait=r,
                         recharge=k, departs=len(deps))
                LIGNES.append(d); tab[strat, "tout", "glissant", m, f, r, k, 12] = d
    return tab


def verdict(tab):
    print("\n=== Point 4 : verdict (prudent, Monte-Carlo B1 ET B2, 24 mois) ===")
    ok = []
    for strat in ("bt_or", "calme", "rebonds"):
        for m, f, r, k in itertools.product(MS, FS, RETS, RECH):
            p = [tab[strat, b, "prudent", m, f, r, k, 24] for b in ("B1", "B2")]
            passe = all(d["moy"] > 0 and d["med"] > 0 and d["ppos"] >= 0.5 for d in p)
            if passe and m > 1:
                t = [tab[strat, b, "prudent", 1.0, f, r, k, 24] for b in ("B1", "B2")]
                passe = all(a["moy"] > b["moy"] for a, b in zip(p, t))
            if passe:
                ok.append((strat, m, f, r, k, p[0]["moy"], p[1]["moy"], p[0]["ppos"], p[1]["ppos"]))
    print("%d combinaisons passent" % len(ok))
    for x in sorted(ok, key=lambda x: -min(x[5], x[6]))[:30]:
        print("  %-8s m %.1f f %4.1f%% retrait %s recharges %d : net moyen B1 %+.2f B2 %+.2f ; P(>0) %.0f / %.0f %%" % (
            x[0], x[1], 100 * x[2], x[3], x[4], x[5], x[6], 100 * x[7], 100 * x[8]))
    return ok


def tableaux(tab):
    print("\n=== Point 3 : resume (Monte-Carlo « tout », 24 mois ; net encaisse en fois le depot) ===")
    for strat in ("bt_or", "calme", "rebonds"):
        print("-- %s --" % strat)
        print("%4s %5s %3s %2s | %-31s | %-31s | %-22s" % ("m", "f", "ret", "rc", "mesure : moy / med / c10 / P>0",
                                                             "prudent : moy / med / c10 / P>0", "nul : moy / P>0 / ruines"))
        for m in MS:
            for f in (0.01, 0.03, 0.12):
                for r in RETS:
                    for k in (0, 2):
                        a, b, c = (tab[strat, "tout", s, m, f, r, k, 24] for s in ("mesure", "prudent", "nul"))
                        print("%4.1f %4.0f%% %3s %2d | %+6.2f %+6.2f %+6.2f %4.0f%% | %+6.2f %+6.2f %+6.2f %4.0f%% | "
                              "%+6.2f %4.0f%% %5.2f" % (m, 100 * f, r, k, a["moy"], a["med"], a["c10"], 100 * a["ppos"],
                                                       b["moy"], b["med"], b["c10"], 100 * b["ppos"], c["moy"],
                                                       100 * c["ppos"], c["ruines"]))


if __name__ == "__main__":
    PA = paniers()
    rejeu_simple(PA, "calme", (0.01, 0.12), (1.0, 2.0))
    rejeu_simple(PA, "bt_or", (0.005, 0.01, 0.02, 0.03), (1.0,))
    tab = point3(PA)
    tableaux(tab)
    ok = verdict(tab)
    pd.DataFrame(LIGNES).to_csv(os.path.join(ICI, "donnees", "lotc.csv"), index=False, float_format="%.5g")
    print("fini en %.0f s" % (time.time() - T00))
