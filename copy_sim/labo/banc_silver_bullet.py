"""Banc Silver Bullet (regle ICT/SMC, SKILLS_TRADING.md « A tester en priorite » n° 2) sur bougies M5 du courtier :
or (XAUUSD), NAS100+, SP500+, DJ30+, avec le spread reel de chaque bougie (colonne sp de banc_or.charge).

Horloge : le serveur du courtier suit l'heure d'ete americaine et vaut New York + 7 h toute l'annee (verifie dans les
donnees : le saut de volume de l'ouverture au comptant 9 h 30 NY tombe a 16 h 30 serveur, y compris pendant les
semaines ou l'Europe et les Etats-Unis ne sont pas a la meme heure d'ete) ; Paris = serveur - 1 h (- 2 h ces semaines-la).

Regle (fondu de fausse sortie). Fourchette = plus haut / plus bas des 12 bougies M5 de l'heure H (H:00-H:55 serveur).
Pendant l'heure suivante (H+1:00-H+1:50 pour la bougie de signal) : si le prix a depasse un bord (meche ou cloture
dehors) puis qu'une bougie M5 cloture de nouveau DANS la fourchette, on entre a l'inverse a l'ouverture de la bougie
suivante (achat au prix demandeur = bid + spread, vente au bid). Un seul trade par jour (le premier signal).
Objectif : milieu ou autre bord. Stop : un spread au-dela de l'extreme atteint pendant la fausse sortie, ou a 0,5
largeur de fourchette du prix d'entree. Sortie au plus tard a la cloture de H+1:55 (« fin d'heure ») ou de H+2:55
(« +1 h »). Stop et objectif testes sur le haut/bas de chaque bougie (vente : haut/bas + spread) ; si les deux sont
touches dans la meme bougie, on compte le stop ; ouverture au-dela du stop : sortie a l'ouverture.
Controle (« suivre ») : premiere bougie de l'heure H+1 qui cloture hors de la fourchette -> entree dans son sens ;
objectif bord franchi + 0,5 ou 1 largeur, stop au milieu ou a 0,5 largeur de l'entree, memes sorties.

Grille fixee d'avance, par instrument, N = 24 : heure de fourchette {9-10 NY = 16 h serveur, 10-11 NY = 17 h,
3-4 NY = 10 h} x objectif {milieu, autre bord} x stop {extreme, 0,5 fourchette} x sortie {fin d'heure, +1 h}.
Gains en points de base du prix d'entree, apres spread ; serie par jour (0 sans trade).
Methode : walk-forward glissant (apprentissage 6 mois, test 1 mois, choix du meilleur t des gains par jour),
serie hors echantillon concatenee ; reality check de White (bootstrap stationnaire, blocs moyens 5 j, 2000 tirages)
sur les 4 x 24 = 96 reglages contre « ne rien faire », et aussi par instrument (24) ; seuil Bonferroni rappele.
Verdict fixe d'avance : tient = hors echantillon > 0 et (t >= 2,6 ou p RC < 0,05) ; presque = hors echantillon > 0 et
(1,5 <= t < 2,6 ou p < 0,15) ; sinon ne tient pas. Usage : python3 banc_silver_bullet.py"""
import contextlib, io, itertools
from statistics import NormalDist
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_or as B

INSTR = {"xau": ["xau_m5_2025a", "xau_m5_90k"], "nas": ["nas_m5_2025a", "nas_m5_90k"],
         "sp": ["sp_m5_90k"], "dj": ["dj_m5_90k"]}
FEN = {"9-10NY": 16, "10-11NY": 17, "3-4NY": 10}          # heure de fourchette, horloge serveur
GRILLE = list(itertools.product(FEN, ("milieu", "bord"), ("extreme", "0,5F"), ("fin", "+1h")))
GRILLE_S = list(itertools.product(FEN, ("0,5F", "1F"), ("milieu", "0,5F"), ("fin", "+1h")))


def charge(noms):
    d = pd.concat([B.charge(n)[0] for n in noms]).sort_index()
    return d[~d.index.duplicated(keep="last")]


def decalage(d):
    """Part des jours ou le saut de volume est a 16:30 serveur plutot qu'a 15:30 (9 h 30 NY si serveur = NY+7)."""
    v = d["volume_ticks"]; t = d.index.strftime("%H:%M"); j = pd.Series(v.values, [d.index.date, t])
    r = j.unstack()
    ok = r[["15:25", "15:30", "16:25", "16:30"]].dropna()
    return ((ok["16:30"] / ok["16:25"]) > (ok["15:30"] / ok["15:25"])).mean(), len(ok)


def jours(d):
    """Pour chaque date serveur : tableaux numpy des bougies et leurs heures en minutes."""
    out = {}
    mn = np.asarray(d.index.hour * 60 + d.index.minute)
    O, H, L, C, S = (d[k].values for k in ("ouverture", "haut", "bas", "cloture", "sp"))
    for day, pos in pd.Series(np.arange(len(d)), d.index).groupby(d.index.normalize()):
        p = pos.values
        out[day] = (mn[p], O[p], H[p], L[p], C[p], S[p])
    return out


def un_jour(j, h, regle, cfg):
    """Gain en bp du trade du jour (ou None). regle 'fondu' ou 'suivre'."""
    mn, O, H, L, C, S = j
    rg = (mn >= h * 60) & (mn < h * 60 + 60)
    if rg.sum() < 10:
        return None
    rh, rl = H[rg].max(), L[rg].min(); W = rh - rl
    if W <= 0:
        return None
    _, a, b, sortie = cfg
    fin = (h + 2 if sortie == "fin" else h + 3) * 60
    tw = np.flatnonzero((mn >= h * 60 + 60) & (mn <= h * 60 + 110))
    if len(tw) < 6:
        return None
    sig = None; up = dn = False; hx, lx = -np.inf, np.inf
    for i in tw:
        if regle == "fondu":
            if H[i] > rh: up, hx = True, max(hx, H[i])
            if L[i] < rl: dn, lx = True, min(lx, L[i])
            ins = rl < C[i] < rh
            if ins and up and not dn: sig = (i, -1); break
            if ins and dn and not up: sig = (i, +1); break
            if ins and up and dn: return None
        else:
            if C[i] > rh: sig = (i, +1); break
            if C[i] < rl: sig = (i, -1); break
    if sig is None:
        return None
    i, s = sig; e = i + 1
    if e >= len(mn) or mn[e] >= fin or mn[e] != mn[i] + 5:
        return None
    o = O[e]; ent = o + S[e] if s > 0 else o             # prix d'entree reel (demandeur pour un achat)
    mid = (rh + rl) / 2
    if regle == "fondu":
        tg = (mid if a == "milieu" else (rh if s > 0 else rl))
        if b == "extreme":
            st = lx - S[i] if s > 0 else hx + 2 * S[i]    # niveau en bid (achat) ou en demandeur (vente)
        else:
            st = ent - 0.5 * W if s > 0 else ent + 0.5 * W
    else:
        k = 0.5 if a == "0,5F" else 1.0
        tg = rh + k * W if s > 0 else rl - k * W
        st = (mid if b == "milieu" else ent - 0.5 * W) if s > 0 else (mid if b == "milieu" else ent + 0.5 * W)
    # niveaux exprimes dans la cotation de sortie : bid pour un achat, demandeur pour une vente
    if s > 0 and (o >= tg or st >= o): return None
    if s < 0 and (o + S[e] <= tg or st <= o + S[e]): return None
    x = None
    k = e
    while k < len(mn) and mn[k] < fin:
        if s > 0:
            if O[k] <= st: x = O[k]; break
            if L[k] <= st: x = st; break
            if H[k] >= tg: x = tg; break
        else:
            q = S[k]
            if O[k] + q >= st: x = O[k] + q; break
            if H[k] + q >= st: x = st; break
            if L[k] + q <= tg: x = tg; break
        k += 1
    if x is None:
        k -= 1
        x = C[k] if s > 0 else C[k] + S[k]
    return 1e4 * ((x - ent) if s > 0 else (o - x)) / o


def series(J, regle, grille):
    idx = pd.DatetimeIndex(sorted(J))
    res = {}
    for cfg in grille:
        h = FEN[cfg[0]]
        res[cfg] = pd.Series([un_jour(J[d], h, regle, cfg) for d in idx], idx, dtype=float)
    return res


tstat = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else 0.0
creux = lambda x: (x.cumsum() - x.cumsum().cummax()).min()


def walk_forward(R):
    idx = next(iter(R.values())).index
    mois = idx.to_period("M"); MO = mois.unique()
    oos, tr, choix = [], [], []
    for i in range(6, len(MO)):
        app, te = (mois >= MO[i - 6]) & (mois <= MO[i - 1]), mois == MO[i]
        best = max(R, key=lambda k: tstat(R[k][app].fillna(0)))
        choix.append(best); oos.append(R[best][te])
    o = pd.concat(oos)
    return o, pd.Series(choix).value_counts(), MO[6], MO[-1]


rng = np.random.default_rng(17)
def boot_idx(n, b=5.0):
    i = np.empty(n, int); i[0] = rng.integers(n)
    neuf = rng.random(n) < 1 / b; nv = rng.integers(n, size=n)
    for t in range(1, n):
        i[t] = nv[t] if neuf[t] else (i[t - 1] + 1) % n
    return i


def reality_check(M, I):
    n = M.shape[0]; mu = M.mean(0); V = np.sqrt(n) * mu.max()
    Vb = np.array([np.sqrt(n) * (M[ii].mean(0) - mu).max() for ii in I])
    return (Vb >= V).mean(), int(mu.argmax())


def nom(c): return "%s %s/%s/%s" % c


if __name__ == "__main__":
    D = {k: charge(v) for k, v in INSTR.items()}
    p16, nj = decalage(D["nas"])
    print("Horloge : saut de volume a 16:30 serveur (et non 15:30) %.0f %% de %d jours NAS -> serveur = NY + 7 h retenu ;"
          " fourchette 16-17 h serveur = 9-10 h NY = 15-16 h Paris" % (100 * p16, nj))
    for k, d in D.items():
        print("  %-3s %s -> %s, %d bougies M5, spread median %.2f bp" % (k, d.index[0].date(), d.index[-1].date(), len(d),
              (d.sp / d.cloture * 1e4).median()))
    RF, RS = {}, {}
    for k, d in D.items():
        J = jours(d[d.index.dayofweek < 5])
        RF[k], RS[k] = series(J, "fondu", GRILLE), series(J, "suivre", GRILLE_S)
    print("N = %d reglages par instrument, %d au total (fondu) ; controle « suivre la sortie » : %d par instrument" % (
        len(GRILLE), 4 * len(GRILLE), len(GRILLE_S)))
    print("%-6s %-5s %-30s %5s %8s %5s %6s %6s %6s %8s %7s" % ("regle", "instr", "reglage le plus choisi", "nb", "HE bp", "t",
          "mois+", "trades", "bp/tr", "creux", "pRC24"))
    union = sorted(set().union(*[RF[k][GRILLE[0]].index for k in RF]))
    union = pd.DatetimeIndex(union)
    I = None; RESV = {}
    for regle, RR in (("fondu", RF), ("suivre", RS)):
        port = []
        for k in RR:
            o, fq, m0, m1 = walk_forward(RR[k])
            od = o.fillna(0); pm = od.groupby(od.index.to_period("M")).sum()
            Mk = np.column_stack([RR[k][c].fillna(0).values for c in RR[k]])
            Ik = [boot_idx(len(Mk)) for _ in range(2000)]
            pk, _ = reality_check(Mk, Ik)
            nt = o.notna().sum()
            print("%-6s %-5s %-30s %5s %+8.0f %+5.1f %3d/%-2d %6d %+6.1f %+8.0f %7.3f" % (regle, k, nom(fq.index[0]),
                  "%d/%d" % (fq.iloc[0], fq.sum()), od.sum(), tstat(od), (pm > 0).sum(), len(pm), nt, o.mean(), creux(od), pk))
            RESV[(regle, k)] = (od.sum(), tstat(od), pk)
            port.append(od)
        P = pd.concat(port, axis=1, sort=True).fillna(0).sum(axis=1)
        pm = P.groupby(P.index.to_period("M")).sum()
        print("%-6s %-5s %-30s %5s %+8.0f %+5.1f %3d/%-2d %6s %6s %+8.0f" % (regle, "4 ens", "(somme des 4, chacun son choix)", "",
              P.sum(), tstat(P), (pm > 0).sum(), len(pm), "", "", creux(P)))
        RESV[(regle, "4 ens")] = (P.sum(), tstat(P), np.nan)
    print("Tests hors echantillon : %s -> %s (xau/nas : 17 mois de donnees, sp/dj : 15 ; donc 11 et 9 mois de test)" % (m0, m1))
    for regle, RR, G in (("fondu", RF, GRILLE), ("suivre", RS, GRILLE_S)):
        cols = [(k, c) for k in RR for c in G]
        M = np.column_stack([RR[k][c].reindex(union).fillna(0).values for k, c in cols])
        if I is None:
            I = [boot_idx(len(union)) for _ in range(2000)]
        p, j = reality_check(M, I)
        kb, cb = cols[j]; x = RR[kb][cb]
        print("RC %s, %d reglages : meilleur %s %s (tout l'echantillon %+.0f bp, %d trades, %+.1f bp/tr, t %+.1f), p = %.3f"
              % (regle, len(cols), kb, nom(cb), x.sum(), x.notna().sum(), x.mean(), tstat(x.fillna(0)), p))
        RESV[(regle, "best")] = (kb, p)
    for N in (24, 96):
        print("Bonferroni N=%d : t >= %.2f (5 %%, unilateral)" % (N, NormalDist().inv_cdf(1 - 0.05 / N)))
    # tableau plein echantillon compact du fondu : moyenne bp/trade par fenetre et instrument (tous reglages confondus)
    for f in FEN:
        print("fondu %-8s bp/trade moyen sur ses 8 reglages, tout l'echantillon : " % f + "  ".join(
            "%s %+.1f (%d tr)" % (k, np.nanmean([RF[k][c].mean() for c in GRILLE if c[0] == f]),
                                   RF[k][[c for c in GRILLE if c[0] == f][0]].notna().sum()) for k in RF))
    print("Verdict (fixe d'avance ; p = RC par instrument sur 24, le RC global ne vaut que pour l'instrument du meilleur) :")
    for regle in ("fondu", "suivre"):
        kb, pg = RESV[(regle, "best")]
        txt = []
        for k in list(INSTR) + ["4 ens"]:
            s, t, pk = RESV[(regle, k)]
            p = min(pk, pg) if k == kb else pk
            v = "tient" if s > 0 and (t >= 2.6 or p < 0.05) else ("presque" if s > 0 and (1.5 <= t < 2.6 or p < 0.15) else "ne tient pas")
            txt.append("%s %s" % (k, v))
        print("  %s : %s" % (regle, " ; ".join(txt)))
