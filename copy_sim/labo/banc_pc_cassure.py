"""Banc PC-cassure : poche « pari court » (PRIORITES 17/11 20 h 10), cassures PYRAMIDEES et expansion apres compression.
Ce qui est NEUF par rapport aux bancs deja refutes (banc_compression.py : cassure apres compression, 1 position, stop au
milieu, sortie au temps ; banc_blocktrend.py sur BTC/ETH : entrees a heures fixes dans le sens de l'EMA 2 j) :
  - l'entree est une CASSURE (plus haut / plus bas de N bougies, ou de la seance d'Asie, ou d'une fourchette comprimee) ;
  - le PYRAMIDAGE : +1 position a chaque « pas » franchi a la cloture M5 dans le sens du gain (niveau saute si la cloture
    est deja a plus d'un demi-pas au-dela), 4 ou 10 positions au plus, STOP SUIVEUR serre, tout le panier sort au stop ;
  - la MISE FORTE (levier 10 a 100 sur 100 / 500 $) via pari_court_commun.comparer().
La preuve n'est PAS relachee : walk-forward, spread reel, glissement, essais comptes, temoin au hasard, deux moitiees.

Donnees : bougies M5 du courtier (mt5/donnees) : BTCUSD, ETHUSD (01/2026 -> 11/2026, 10,4 mois seulement : moins que
les 15 mois du protocole, dit dans le verdict), NAS100+ et XAUUSD (08/2025 -> 11/2026, 15 mois).
Couts : achat a l'ask (bid + spread de la bougie), vente au bid ; la vente a decouvert rachete a l'ask ; glissement de
0,5 spread sur chaque sortie ; pas de financement de nuit (tenue max 2 jours, presque toujours quelques heures).
Mecanique commune (un panier a la fois par marche et par reglage) : signal a la cloture de la bougie i, entree a
l'ouverture de i+1 ; stop suiveur a la distance « stop » du meilleur prix atteint AVANT la bougie (prudent) ; si
l'ouverture saute le stop, sortie a l'ouverture ; sortie au temps apres 576 bougies (2 jours). Distance de stop au
moins 2 spreads (fixe d'avance).

Piste 1 « cassure pyramidee » (5 x 3 x 3 x 3 = 135 reglages par marche, x 4 marches = 540) :
  entree : 1re cloture au-dela du plus haut (achat) / plus bas (vente) des N bougies M5 precedentes,
           N = 12 (1 h, ~ 12 M5 / 4 M15), 36 (3 h, ~ 12 M15 / 3 H1), 96 (8 h, 8 H1), 288 (24 h, 24 H1),
           ou « asie » : fourchette des heures serveur 1 h - 9 h du jour, cassure entre 9 h et 22 h serveur ;
  pas = 0,1 / 0,2 / 0,4 ATR journalier 20 j (de la veille) ; stop = 0,1 / 0,2 / 0,4 ATR ; positions max 1 / 4 / 10.
Piste 2 « expansion apres compression » (3 x 2 x 2 x 2 x 3 = 72 reglages par marche, x 4 = 288) :
  fourchette des n dernieres bougies (n = 12, 24, 48) la plus etroite des M dernieres (M = 100, 300 bougies) ;
  entree sur la 1re cloture hors de la fourchette dans les n bougies suivantes ; stop de l'autre cote (= lo/hi) ou a
  0,5 fourchette (milieu), puis suiveur a cette distance ; pas = 0,5 / 1 fourchette ; positions max 1 / 4 / 10.
N = 540 + 288 = 828 reglages (+ 4 leviers x 2 departs dans comparer, + 2 regles de walk-forward : libre / 1 position).

Walk-forward (fixe d'avance) : mois civils (heure serveur). Pour chaque mois m, on regarde les 4 mois precedents :
reglage = meilleur t des gains par panier (somme des positions, en fraction du notionnel d'une position ; >= 10
paniers) ; on ne joue le mois m que si ce t est > 0. Une serie par (piste, marche) = 8 series, + le portefeuille des 4
marches par piste ; refait avec « 1 position seulement » (temoin sans pyramide). Bonferroni sur 20 series.
Temoin au hasard : memes heures d'entree, meme reglage, sens tire a pile ou face (5 000 tirages) -> p temoin.
Le meilleur montage hors echantillon (plus grand t), et la meilleure serie de la piste 1, passent dans
pari_court_commun.comparer(T, L, 100 / 500), L = 10, 25, 50, 100.
Sorties : donnees/pc_cassure.csv (trades hors echantillon, une ligne par position, colonnes t0, t1, r, cout, mae,
unite, groupe, regle, marche) ; resume dans le scratchpad res_pc_cassure.md (ecrit a la main d'apres la sortie).
Usage : python3 banc_pc_cassure.py   (~ 3-4 min, 4 coeurs)"""
import os, sys, math, itertools
from multiprocessing import Pool
import numpy as np, pandas as pd

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import banc_grille as G
import pari_court_commun as C

MARCHES = {"BTCUSD": ("btc_m5_90k", 0.01 * 63801.0), "ETHUSD": ("eth_m5_90k", 0.01 * 1790.0),
           "NAS100+": ("nas_m5_90k", 0.1 * 28530.0), "XAUUSD": ("xau_m5_90k", 1.0 * 3854.0)}
HMAX, SLIP, TRAIN = 576, 0.5, 4
P1 = list(itertools.product((12, 36, 96, 288, "asie"), (0.1, 0.2, 0.4), (0.1, 0.2, 0.4), (1, 4, 10)))
P2 = list(itertools.product((12, 24, 48), (100, 300), ("cote", "milieu"), (0.5, 1.0), (1, 4, 10)))
_D = {}


def prepare(ident):
    if ident in _D:
        return _D[ident]
    d = G.charge(ident)
    t = d.heure.values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": d.haut, "l": d.bas, "c": d.cloture}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    mois = pd.to_datetime(t, unit="s").to_period("M").astype(str).values
    D = dict(o=d.ouverture.values, h=d.haut.values, l=d.bas.values, c=d.cloture.values, sp=d.sp.values, t=t,
             heure=(t // 3600) % 24, jour=jour, atr=atr, mois=mois, d=d)
    _D[ident] = D
    return D


def panier(D, j, s, stop, pas, maxpos):
    """Panier ouvert a l'ouverture de la bougie j, sens s. Rend (K sortie, liste de (bougie, r, mae, cout))."""
    o, h, l, c, sp = D["o"], D["h"], D["l"], D["c"], D["sp"]
    n = len(o)
    for Hc in (48, HMAX):
        b = min(n, j + Hc)
        oo, hh, ll = o[j:b], h[j:b], l[j:b]
        if s > 0:
            best = np.maximum.accumulate(np.r_[oo[0], hh[:-1]]); lev = best - stop
            hit = np.flatnonzero(ll <= lev)
        else:
            best = np.minimum.accumulate(np.r_[oo[0], ll[:-1]]); lev = best + stop
            hit = np.flatnonzero(hh + sp[j:b] >= lev)
        if hit.size or b == n or Hc == HMAX:
            break
    if hit.size:
        k = hit[0]
        if s > 0:
            X = min(oo[k], lev[k]) - SLIP * sp[j + k]
        else:
            X = max(oo[k] + sp[j + k], lev[k]) + SLIP * sp[j + k]
    else:
        k = b - j - 1
        X = c[b - 1] - SLIP * sp[b - 1] if s > 0 else c[b - 1] + sp[b - 1] + SLIP * sp[b - 1]
    K = j + k
    # positions : (indice relatif d'entree, prix d'entree, spread paye, debut de la surveillance de l'excursion)
    pos = [(0, oo[0] + (sp[j] if s > 0 else 0.0), sp[j] if s > 0 else sp[K], 0)]
    if maxpos > 1 and k > 0:
        cc = c[j:j + k]
        for m in range(1, maxpos):
            L = oo[0] + s * m * pas
            q = np.flatnonzero(s * (cc - L) >= 0)
            if not q.size:
                break
            q = q[0]
            if s * (cc[q] - L) <= 0.5 * pas:
                pos.append((q, cc[q] + (sp[j + q] if s > 0 else 0.0), sp[j + q] if s > 0 else sp[K], q + 1))
    out = []
    for q, e, cs, w0 in pos:
        if s > 0:
            pire = min(ll[w0:k].min() if k > w0 else X, X); mae = max(0.0, e - pire) / e
        else:
            pire = max((hh[w0:k] + sp[j + w0:j + k]).max() if k > w0 else X, X); mae = max(0.0, pire - e) / e
        out.append((j + q, s * (X - e) / e, mae, (cs + SLIP * sp[K]) / e))
    return K, out


def signaux_p1(D, N):
    c, h, l = D["c"], D["h"], D["l"]
    if N == "asie":
        df = pd.DataFrame({"jour": D["jour"], "h": h, "l": l})
        a = (D["heure"] >= 1) & (D["heure"] < 9)
        g = df[a].groupby("jour").agg(h=("h", "max"), l=("l", "min"))
        hi = g.h.reindex(D["jour"]).values; lo = g.l.reindex(D["jour"]).values
        ok = (D["heure"] >= 9) & (D["heure"] < 22)
    else:
        hi = pd.Series(h).rolling(N).max().shift(1).values; lo = pd.Series(l).rolling(N).min().shift(1).values
        ok = np.ones(len(c), bool)
    up = ok & (c > hi); dn = ok & (c < lo)
    up &= ~np.r_[False, up[:-1]]; dn &= ~np.r_[False, dn[:-1]]
    i = np.flatnonzero(up | dn)
    return [(x, 1 if up[x] else -1, None) for x in i]


def signaux_p2(D, n, M):
    c, h, l = D["c"], D["h"], D["l"]
    hi = pd.Series(h).rolling(n).max().values; lo = pd.Series(l).rolling(n).min().values
    w = hi - lo
    comp = w <= pd.Series(w).rolling(M).min().shift(1).values
    out, fin, box = [], -1, None
    for i in range(len(c)):
        if comp[i]:
            box, fin = (hi[i], lo[i]), i + n
            continue
        if box is not None and i <= fin:
            if c[i] > box[0] or c[i] < box[1]:
                out.append((i, 1 if c[i] > box[0] else -1, box)); box = None
    return out


def simule(args):
    """Un groupe de reglages partageant les memes signaux. Rend une liste (piste, marche, reglage, paniers)."""
    piste, marche, cle, regs = args
    D = prepare(MARCHES[marche][0])
    sig = signaux_p1(D, cle) if piste == 1 else signaux_p2(D, *cle)
    res = []
    for reg in regs:
        P, K = [], -1
        for i, s, box in sig:
            j = i + 1
            if i < K or j >= len(D["o"]) - 2:
                continue
            if piste == 1:
                a = D["atr"][i]
                if not a == a:
                    continue
                stop, pas, mp = reg[1] * a, reg[0] * a, reg[2]
            else:
                bord, pk, mp = reg
                wdt = box[0] - box[1]
                niv = (box[1] if s > 0 else box[0]) if bord == "cote" else (box[0] + box[1]) / 2
                stop, pas = s * (D["o"][j] - niv), pk * wdt
            stop = max(stop, 2 * D["sp"][i])
            K, pos = panier(D, j, s, stop, pas, mp)
            P.append((i, j, K, s, stop, pas, mp, pos))
        res.append((piste, marche, (cle,) + tuple(reg), P))
    return res


def taches():
    T = []
    for m in MARCHES:
        for N in (12, 36, 96, 288, "asie"):
            T.append((1, m, N, [(p, st, mp) for p, st, mp in itertools.product((0.1, 0.2, 0.4), (0.1, 0.2, 0.4), (1, 4, 10))]))
        for n, M in itertools.product((12, 24, 48), (100, 300)):
            T.append((2, m, (n, M), list(itertools.product(("cote", "milieu"), (0.5, 1.0), (1, 4, 10)))))
    return T


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / x.std(ddof=1) * math.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else 0.0


def walk_forward(R, piste, marche, un_seul=False):
    """R : {reglage: paniers}. Rend la liste des paniers hors echantillon (avec leur reglage)."""
    D = prepare(MARCHES[marche][0])
    mois_all = sorted(set(D["mois"]))
    tab = {}
    for reg, P in R.items():
        if un_seul and reg[-1] != 1:
            continue
        if not P:
            continue
        mo = D["mois"][[p[0] for p in P]]
        g = np.array([sum(x[1] for x in p[7]) for p in P])
        tab[reg] = (mo, g, P)
    oos = []
    for k in range(TRAIN, len(mois_all)):
        tr = set(mois_all[k - TRAIN:k]); te = mois_all[k]
        best, bt = None, 0.0
        for reg, (mo, g, P) in tab.items():
            x = g[np.isin(mo, list(tr))]
            if len(x) >= 10:
                t = tstat(x)
                if t > bt:
                    best, bt = reg, t
        if best is None:
            continue
        mo, g, P = tab[best]
        oos += [(best, p) for p, m in zip(P, mo) if m == te]
    return oos


def lignes(oos, marche, regle):
    D = prepare(MARCHES[marche][0])
    t = D["t"]
    rows = []
    for b, (reg, p) in enumerate(oos):
        K = p[2]
        for q, r, mae, cout in p[7]:
            rows.append((t[q], t[K] + 300, r, cout, mae, MARCHES[marche][1], "%s_%d" % (marche, p[1]), regle, marche, str(reg)))
    T = pd.DataFrame(rows, columns=["t0", "t1", "r", "cout", "mae", "unite", "groupe", "regle", "marche", "reglage"])
    T["t0"] = pd.to_datetime(T.t0, unit="s"); T["t1"] = pd.to_datetime(T.t1, unit="s")
    return T


def resume(nom, oos, rng, marche_de=None):
    """Gains par panier (somme des positions, bp du notionnel d'une position)."""
    if len(oos) < 5:
        return dict(serie=nom, paniers=len(oos))
    g = np.array([sum(x[1] for x in p[7]) for _, p in oos]) * 1e4
    npos = np.array([len(p[7]) for _, p in oos])
    h = len(g) // 2
    # temoin : meme reglage, memes heures, sens oppose precalcule -> tirage a pile ou face
    alt = []
    for (reg, p), m in zip(oos, marche_de):
        D = prepare(MARCHES[m][0])
        _, pos = panier(D, p[1], -p[3], p[4], p[5], p[6])
        alt.append(sum(x[1] for x in pos) * 1e4)
    alt = np.array(alt)
    tir = rng.random((5000, len(g))) < 0.5
    moy_h = np.where(tir, g, alt).mean(1)
    t = tstat(g)
    p1 = 0.5 * math.erfc(t / math.sqrt(2))
    srt = np.sort(g)[::-1]
    return dict(serie=nom, paniers=len(g), pos_moy=npos.mean(), bp=g.mean(), t=t, p=p1, p_bonf=min(1, 20 * p1),
                m1=g[:h].mean(), t1=tstat(g[:h]), m2=g[h:].mean(), t2=tstat(g[h:]), gagnants=(g > 0).mean(),
                part_top5=srt[:5].sum() / g.sum() if g.sum() > 0 else float("nan"),
                temoin_bp=moy_h.mean(), p_temoin=(moy_h >= g.mean()).mean())


def main():
    rng = np.random.default_rng(2010)
    with Pool(4) as pool:
        out = [r for lot in pool.map(simule, taches(), chunksize=1) for r in lot]
    R = {}
    for piste, marche, reg, P in out:
        R.setdefault((piste, marche), {})[reg] = P
    # en echantillon : meilleur reglage sur toute la periode (pour info, a corriger par N = 828)
    print("Meilleur reglage SUR TOUTE LA PERIODE (biaise ; a juger avec N = 828) : bp par panier, t")
    for (piste, marche), RR in sorted(R.items()):
        sc = []
        for reg, P in RR.items():
            if len(P) >= 30:
                g = np.array([sum(x[1] for x in p[7]) for p in P]) * 1e4
                gb = np.array([sum(x[1] + x[3] for x in p[7]) for p in P]) * 1e4
                sc.append((tstat(g), g.mean(), len(g), reg, np.mean([len(p[7]) for p in P]), gb.mean()))
        sc.sort(key=lambda x: -x[0])
        tb, mb, nb, rb, pb, bb = sc[0]
        pos = sum(1 for x in sc if x[1] > 0)
        pyr = [x for x in sc if x[3][-1] > 1]; un = [x for x in sc if x[3][-1] == 1]
        print("  piste %d %-8s : %3d reglages, %3d positifs ; meilleur %-32s %5d paniers %+7.1f bp (t %+.2f, Bonferroni p %.2f), %.1f pos./panier ;"
              " medianes : t %+.2f, net %+.1f bp, AVANT couts %+.1f bp ; pyramide / 1 position : net %+.1f / %+.1f bp" % (
            piste, marche, len(sc), pos, str(rb), nb, mb, tb, min(1, 828 * 0.5 * math.erfc(tb / math.sqrt(2))), pb, np.median([x[0] for x in sc]),
            np.median([x[1] for x in sc]), np.median([x[5] for x in sc]), np.median([x[1] for x in pyr]), np.median([x[1] for x in un])))
    print("\nWalk-forward (4 mois -> 1 mois, glissant), hors echantillon : bp par panier (notionnel d'une position)")
    S, toutes = [], []
    for un in (False, True):
        for piste in (1, 2):
            pf = []
            for marche in MARCHES:
                oos = walk_forward(R[(piste, marche)], piste, marche, un_seul=un)
                nom = "p%d_%s%s" % (piste, marche, "_1pos" if un else "")
                S.append(resume(nom, oos, rng, [marche] * len(oos)))
                pf += [(o, marche) for o in oos]
                if not un:
                    toutes.append(lignes(oos, marche, "cassure_pyr" if piste == 1 else "compression_pyr"))
            pf.sort(key=lambda x: prepare(MARCHES[x[1]][0])["t"][x[0][1][1]])
            S.append(resume("p%d_4marches%s" % (piste, "_1pos" if un else ""), [o for o, _ in pf], rng, [m for _, m in pf]))
    S = pd.DataFrame(S)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(S.round(3).to_string(index=False))
    T = pd.concat(toutes, ignore_index=True)
    T.assign(r=T.r.round(6), cout=T.cout.round(6), mae=T.mae.round(6)).to_csv(os.path.join(ICI, "donnees", "pc_cassure.csv"), index=False)
    # meilleur montage hors echantillon (parmi les series libres, plus grand t) -> comparer()
    lib = S[~S.serie.str.endswith("_1pos") & S.paniers.ge(30)].sort_values("t", ascending=False)
    p1 = lib[lib.serie.str.startswith("p1")].iloc[0].serie
    for best in dict.fromkeys([lib.iloc[0].serie, p1]):     # meilleur montage, puis meilleure cassure pyramidee
        montage(best, T)


def montage(best, T):
    piste = 1 if best.startswith("p1") else 2
    regle = "cassure_pyr" if piste == 1 else "compression_pyr"
    Tb = T[T.regle == regle]
    if not best.endswith("4marches"):
        Tb = Tb[Tb.marche == best.split("_", 1)[1]]
    print("\nMontage hors echantillon : %s (%d positions, %d paniers ; r moyen %+.1f bp par position, cout %.1f bp)" % (
        best, len(Tb), Tb.groupe.nunique(), 1e4 * Tb.r.mean(), 1e4 * Tb.cout.mean()))
    cols = ["version", "horizon", "fenetres", "ruine", "x2", "x3", "x5", "x10", "esperance", "bat_ref"]
    for dep in (100.0, 500.0):
        for L in (10, 25, 50, 100):
            Rc = C.comparer(Tb[["t0", "t1", "r", "cout", "mae", "unite", "groupe"]], L, depart=dep)
            print("\n-- depart %.0f $, levier %d --" % (dep, L))
            print(Rc[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
