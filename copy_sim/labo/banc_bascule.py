"""Banc bascule : passer vite d'une famille de regles a l'autre en cours de journee sur l'or (suite de banc_famille_wf.py,
dont la piste 1 « le marche choisit » n'est pas refaite ici).
Regle de base (bougies M5 du courtier, prix vendeur + spread reel colonne sp, 1 position a la fois, $ pour 0,01 lot = 1 once) :
  fourchette = plus haut / plus bas des n bougies precedentes (n = 30 min, 1 h ou 2 h) ; signal a la cloture d'une
  bougie qui sort de la fourchette. TENDANCE = on suit la sortie, RETOUR = on la contre. Entree a l'ouverture de la
  bougie suivante ; stop a k x largeur de la fourchette, objectif a m x stop, sinon sortie au temps (2 x la duree de la
  fourchette) ou avant un trou de cotation de plus de 30 min. Stop et objectif touches dans la meme bougie = stop.
Etat courant TENDANCE ou RETOUR (depart TENDANCE), regle de bascule :
  (a) bascule apres chaque trade perdant ; (b2) apres 2 stops de suite de la famille active ;
  (c3/c5) famille dont les 3 / 5 derniers trades « virtuels » (chaque famille suivie seule sur le papier, trades deja
  sortis) font le plus ; egalite = on garde ; (d30/d60) efficacite du prix sur 30 / 60 min (|deplacement net| / chemin
  parcouru) au-dessus de sa mediane des ~20 jours precedents -> TENDANCE, sinon RETOUR.
Grille fixee d'avance : 6 regles x 3 fourchettes x 2 sorties {stop 0,5 objectif 2 ; stop 1 objectif 1} = N 36
  (b1 « 1 stop » omis car quasi identique a (a) ; les 4 couples stop/objectif x 7 regles x 3 fourchettes = 84 > 40).
Methode : walk-forward glissant 6 mois -> 1 mois (meilleur t du gain par jour), serie hors echantillon concatenee ;
references : chaque famille seule au meme reglage de base, alternance au hasard au meme nombre de bascules par mois
(100 tirages), ne rien faire ; bascules par jour, cout des bascules ratees (trades pris entre une bascule et la bascule
inverse survenue en moins de 3 trades), part du spread ; reality check de White (bootstrap stationnaire, blocs 5 j,
2000 tirages) des 36 reglages contre 0 ; controle sur M1 (3 mois seulement) du reglage le plus choisi.
Usage : python3 banc_bascule.py"""
import numpy as np, pandas as pd
import banc_or as B

GRILLE = [(r, n, ex) for r in ("a", "b2", "c3", "c5", "d30", "d60") for n in (30, 60, 120) for ex in ((0.5, 2.0), (1.0, 1.0))]


def charge_m5():
    a, _ = B.charge("xau_m5_2025a"); b, _ = B.charge("xau_m5_90k")
    d = pd.concat([a[a.index < b.index[0]], b])
    return d[~d.index.duplicated()]


def issues(d, nb, k, m):
    """Pour chaque signal : barre, et par famille (0 tendance, 1 retour) gain $, barre de sortie, stop touche, spread paye."""
    o, h, l, c, sp = (d[x].values for x in ("ouverture", "haut", "bas", "cloture", "sp"))
    ha = d["haut"].shift(1).rolling(nb).max().values; ba = d["bas"].shift(1).rolling(nb).min().values
    s = np.where(c > ha, 1, np.where(c < ba, -1, 0))
    H, N = 2 * nb, len(c)
    sig = np.flatnonzero(s[: N - H - 2] != 0); sig = sig[sig > nb]
    E = sig[:, None] + 1 + np.arange(H)[None, :]
    trou = np.r_[False, np.diff(d.index.values).astype("timedelta64[m]").astype(int) > 30]
    t_trou = trou[E].copy(); t_trou[:, 0] = False
    vide = np.cumsum(t_trou, 1) > 0                                    # barres apres un trou : hors fenetre
    der = np.where(vide.any(1), vide.argmax(1) - 1, H - 1)
    W = (ha - ba)[sig]; D = k * W
    out = {"bar": sig, "prix": o[sig + 1]}
    for f, dirn in ((0, s[sig]), (1, -s[sig])):
        e = sig + 1
        P = np.where(dirn > 0, o[e] + sp[e], o[e])
        stp, obj = P - dirn * D, P + dirn * m * D
        hb, lb, spb, ob = h[E], l[E], sp[E], o[E]
        lg = (dirn > 0)[:, None]
        hs = np.where(lg, lb <= stp[:, None], hb + spb >= stp[:, None]) & ~vide
        ht = np.where(lg, hb >= obj[:, None], lb + spb <= obj[:, None]) & ~vide
        i_s = np.where(hs.any(1), hs.argmax(1), H); i_t = np.where(ht.any(1), ht.argmax(1), H)
        stop = (i_s <= i_t) & (i_s < H); tgt = (i_t < i_s)
        it = np.where(stop, i_s, np.where(tgt, i_t, der))
        r = np.arange(len(sig)); xb = E[r, it]
        px_t = np.where(dirn > 0, c[xb], c[xb] + sp[xb])
        ost = np.where(dirn > 0, np.minimum(stp, ob[r, it]), np.maximum(stp, ob[r, it] + spb[r, it]))
        ost = np.where(it == 0, stp, ost)
        px = np.where(stop, ost, np.where(tgt, obj, px_t))
        out[f] = dict(g=dirn * (px - P), ex=xb, stop=stop, sp=np.where(dirn > 0, sp[e], sp[xb]))
    return out


def simule(O, kind, etat=None, arg=0, flips=None, js=None, st0=0):
    """Une position a la fois. Rend la liste des trades (j, famille)."""
    bar = O["bar"]; st, busy, cons, res, ntr = st0, -1, 0, [], 0
    for j in (range(len(bar)) if js is None else js):
        i = bar[j]
        if i < busy:
            continue
        if kind in "cd" and etat[j] >= 0:
            st = etat[j]
        elif kind == "h" and ntr in flips:
            st ^= 1
        f = st; res.append((j, f)); ntr += 1
        F = O[f]; busy = F["ex"][j]
        if kind == "a" and F["g"][j] < 0:
            st ^= 1
        elif kind == "b":
            cons = cons + 1 if F["stop"][j] else 0
            if cons >= arg:
                st ^= 1; cons = 0
    return np.array(res, int).reshape(-1, 2)


def tableau(d, O, tr):
    j, f = tr[:, 0], tr[:, 1]
    g = np.where(f == 0, O[0]["g"][j], O[1]["g"][j]); spc = np.where(f == 0, O[0]["sp"][j], O[1]["sp"][j])
    return pd.DataFrame({"g": g, "sp": spc, "f": f, "bp": g / O["prix"][j] * 1e4}, index=d.index[O["bar"][j] + 1])


def etats(d, O, regle, bpm, seuls):
    if regle[0] == "c":
        Nv = int(regle[1:]); sc = []
        for f in (0, 1):
            t = seuls[f]; ex = O[f]["ex"][t[:, 0]]; o = np.argsort(ex, kind="stable")
            ex, cs = ex[o], np.r_[0, np.cumsum(O[f]["g"][t[:, 0]][o])]
            k = np.searchsorted(ex, O["bar"], side="right")
            sc.append(np.where(k >= Nv, cs[k] - cs[np.maximum(k - Nv, 0)], np.nan))
        return np.where(np.isnan(sc[0]) | np.isnan(sc[1]) | (sc[0] == sc[1]), -1, np.where(sc[0] > sc[1], 0, 1))
    w = int(regle[1:]) // bpm                                     # fenetre en bougies
    c = d["cloture"]
    er = (c - c.shift(w)).abs() / c.diff().abs().rolling(w).sum()
    nj = 20 * 1380 // bpm                                          # ~20 jours de cotation
    seuil = er.rolling(nj, min_periods=nj // 4).median().shift(1)
    e, s = er.values[O["bar"]], seuil.values[O["bar"]]
    return np.where(np.isnan(s) | np.isnan(e), -1, np.where(e > s, 0, 1))


def lance(d, cfg, bpm, seuls_cache, O_cache):
    regle, n, (k, m) = cfg
    nb = n // bpm
    if (n, k, m) not in O_cache:
        O = issues(d, nb, k, m); O_cache[(n, k, m)] = O
        seuls_cache[(n, k, m)] = [simule(O, "f", st0=0), simule(O, "f", st0=1)]
    O, seuls = O_cache[(n, k, m)], seuls_cache[(n, k, m)]
    if regle[0] in "cd":
        tr = simule(O, regle[0], etat=etats(d, O, regle, bpm, seuls))
    elif regle == "a":
        tr = simule(O, "a")
    else:
        tr = simule(O, "b", arg=int(regle[1:]))
    return O, tr


def bascules(t):
    """Nombre de bascules, et cout des bascules ratees (bascule inverse en moins de 3 trades)."""
    f, g = t.f.values, t.g.values
    s = np.flatnonzero(np.diff(f) != 0) + 1
    cout, nr = 0.0, 0
    for a, b in zip(s, np.r_[s[1:], len(f) + 99]):
        if b - a < 3:
            cout += g[a:b].sum(); nr += 1
    return len(s), nr, cout


tstat = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else 0.0
creux = lambda x: (x.cumsum() - x.cumsum().cummax()).min()

if __name__ == "__main__":
    d = charge_m5()
    jours = pd.DatetimeIndex(sorted(set(d.index.floor("D"))))
    jours = jours[jours.dayofweek < 5]
    OC, SC, TR = {}, {}, {}
    CFG = {}
    for cfg in GRILLE:
        O, tr = lance(d, cfg, 5, SC, OC)
        t = tableau(d, O, tr); TR[cfg] = t
        CFG[cfg] = t.g.groupby(t.index.floor("D")).sum().reindex(jours).fillna(0)
    SEUL = {}
    for key, O in OC.items():
        for f in (0, 1):
            t = tableau(d, O, SC[key][f]); SEUL[(key, f)] = (t, t.g.groupby(t.index.floor("D")).sum().reindex(jours).fillna(0))
    N = len(CFG)
    mois = jours.to_period("M"); MO = mois.unique()
    fen = [(MO[i - 6], MO[i - 1], MO[i]) for i in range(6, len(MO))]
    print("Or M5 courtier %s -> %s, %d jours ouvres, %d mois ; walk-forward 6 -> 1 mois : %d tests (%s -> %s) ; N = %d"
          % (d.index[0].date(), d.index[-1].date(), len(jours), len(MO), len(fen), fen[0][2], fen[-1][2], N))
    oos, refT, refR, choix, tro = [], [], [], [], []
    rng = np.random.default_rng(11)
    HAS = np.zeros(100)
    for a, b, te in fen:
        app, tm = (mois >= a) & (mois <= b), mois == te
        best = max(CFG, key=lambda c: tstat(CFG[c][app]))
        choix.append(best); oos.append(CFG[best][tm])
        key = (best[1],) + best[2]
        refT.append(SEUL[(key, 0)][1][tm]); refR.append(SEUL[(key, 1)][1][tm])
        t = TR[best]; t = t[t.index.to_period("M") == te]; tro.append(t)
        nbasc = bascules(t)[0]
        O = OC[key]; jm = np.flatnonzero(d.index[O["bar"] + 1].to_period("M") == te)
        for r in range(100):
            fl = set(rng.choice(np.arange(1, max(len(t), 2)), size=min(nbasc, max(len(t) - 1, 0)), replace=False).tolist())
            trh = simule(O, "h", flips=fl, js=jm, st0=int(rng.integers(2)))
            HAS[r] += tableau(d, O, trh).g.sum()
    o, rT, rR = pd.concat(oos), pd.concat(refT), pd.concat(refR)
    T = pd.concat(tro)
    nb_b = sum(bascules(t)[0] for t in tro); nr = sum(bascules(t)[1] for t in tro); cr = sum(bascules(t)[2] for t in tro)
    gm = o.groupby(o.index.to_period("M")).sum()
    fq = pd.Series([" ".join(map(str, (c[0], c[1], c[2][0], c[2][1]))) for c in choix]).value_counts()
    print("Reglages choisis (regle, fourchette min, stop, objectif) : " + " ; ".join("%s x%d" % (k, v) for k, v in fq.items()))
    print("%-34s %8s %6s %6s %7s %7s %8s" % ("hors echantillon", "total $", "t", "trades", "bp/tr", "mois>0", "creux $"))
    print("%-34s %+8.0f %+6.2f %6d %+7.2f %4d/%-2d %+8.0f" % ("bascule (walk-forward)", o.sum(), tstat(o), len(T), T.bp.mean(), (gm > 0).sum(), len(gm), creux(o)))
    for nom, r in (("tendance seule (meme base)", rT), ("retour seul (meme base)", rR)):
        mm = r.groupby(r.index.to_period("M")).sum()
        print("%-34s %+8.0f %+6.2f %6s %7s %4d/%-2d %+8.0f" % (nom, r.sum(), tstat(r), "", "", (mm > 0).sum(), len(mm), creux(r)))
    for nom, r in (("bascule - tendance seule", o - rT), ("bascule - retour seul", o - rR)):
        print("%-34s %+8.0f %+6.2f" % (nom, r.sum(), tstat(r)))
    print("Hasard a bascules egales (100 tirages) : moyenne %+.0f $, 5e-95e centile %+.0f / %+.0f $, part >= bascule %.2f"
          % (HAS.mean(), np.percentile(HAS, 5), np.percentile(HAS, 95), (HAS >= o.sum()).mean()))
    nj = (mois >= fen[0][2]).sum()
    print("Bascules : %d en %d jours = %.1f / jour ; %.0f %% du temps en tendance ; bascules ratees %d (%.0f %%), cout %+.0f $"
          % (nb_b, nj, nb_b / nj, 100 * (T.f == 0).mean(), nr, 100 * nr / max(nb_b, 1), cr))
    brut = T.g.sum() + T.sp.sum()
    spbp = (T.sp / (T.g / T.bp * 1e4).where(T.g != 0)).mean() * 1e4
    print("Spread paye %.0f $ ; resultat brut %+.0f $ -> net %+.0f $ (spread = %.0f %% du brut absolu ; %.2f bp/trade)"
          % (T.sp.sum(), brut, T.g.sum(), 100 * T.sp.sum() / max(abs(brut), 1e-9), spbp))
    # reality check de White contre 0
    rngb = np.random.default_rng(17)
    def boot_idx(n, b=5.0):
        i = np.empty(n, int); i[0] = rngb.integers(n)
        neuf = rngb.random(n) < 1 / b; nv = rngb.integers(n, size=n)
        for t in range(1, n):
            i[t] = nv[t] if neuf[t] else (i[t - 1] + 1) % n
        return i
    M = np.column_stack([CFG[c].values for c in CFG]); n = len(jours)
    mu = M.mean(0); V = np.sqrt(n) * mu.max()
    Vb = np.array([np.sqrt(n) * (M[ii].mean(0) - mu).max() for ii in (boot_idx(n) for _ in range(2000))])
    kb = list(CFG)[int(mu.argmax())]
    p_rc = (Vb >= V).mean()
    from statistics import NormalDist
    print("Reality check (36 reglages, contre 0) : meilleur %s fourchette %d min stop %.1f obj %.0f = %+.0f $ sur tout l'echantillon (t %+.2f), p = %.3f ; Bonferroni t >= %.2f"
          % (kb[0], kb[1], kb[2][0], kb[2][1], mu.max() * n, tstat(CFG[kb]), p_rc, NormalDist().inv_cdf(1 - 0.05 / N)))
    pos = sorted(((CFG[c].sum(), c) for c in CFG), reverse=True)
    print("Reglages > 0 sur tout l'echantillon : %d / %d ; pire %+.0f $ ; mediane %+.0f $" % (sum(v > 0 for v, _ in pos), N, pos[-1][0], np.median([v for v, _ in pos])))
    par = {}
    for c in CFG:
        par.setdefault(c[0], []).append(CFG[c].sum())
    print("Total plein echantillon par regle de bascule (moyenne des 6 bases) : " + " ; ".join("%s %+.0f" % (r, np.mean(v)) for r, v in par.items()))
    sb = {}
    for (key, f), (t, s) in SEUL.items():
        sb.setdefault(f, []).append(s.sum())
    print("Familles seules plein echantillon (moyenne des 6 bases) : tendance %+.0f $, retour %+.0f $" % (np.mean(sb[0]), np.mean(sb[1])))
    # controle M1 (3 mois) du reglage le plus choisi
    c1 = choix[[" ".join(map(str, (c[0], c[1], c[2][0], c[2][1]))) for c in choix].index(fq.index[0])]
    m1, _ = B.charge("xau_m1_90k")
    O1, tr1 = lance(m1, c1, 1, {}, {})
    t1 = tableau(m1, O1, tr1); j1 = t1.g.groupby(t1.index.floor("D")).sum()
    s1 = [tableau(m1, O1, simule(O1, "f", st0=f)).g.sum() for f in (0, 1)]
    t5 = TR[c1]; t5 = t5[(t5.index >= m1.index[0]) & (t5.index <= m1.index[-1])]
    print("Controle M1 %s -> %s, reglage %s %d min : %+.0f $ (t %+.2f, %d trades, %.1f bascules/j) ; tendance seule %+.0f, retour seul %+.0f ; meme reglage en M5 sur ces dates %+.0f $"
          % (m1.index[0].date(), m1.index[-1].date(), c1[0], c1[1], t1.g.sum(), tstat(j1), len(t1), bascules(t1)[0] / max(len(j1), 1), s1[0], s1[1], t5.g.sum()))
    tt = tstat(o)
    v = "tient" if o.sum() > 0 and (tt >= 2.6 or p_rc < 0.05) else ("presque" if o.sum() > 0 and (1.5 <= tt < 2.6 or p_rc < 0.15) else "ne tient pas")
    print("Verdict (fixe d'avance) : %s (hors echantillon %+.0f $, t %+.2f, p RC %.3f)" % (v, o.sum(), tt, p_rc))
