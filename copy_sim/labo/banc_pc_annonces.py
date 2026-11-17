"""Banc PC-annonces (lot « pari court », PRIORITES 17/11 20 h 10) : ordres des DEUX cotes avant les annonces US.
Plan fixe d'avance (avant de voir un resultat) :
- Annonces : emploi (NFP) et inflation (CPI) a 8 h 30 New York = 15:30 serveur ; decision Fed (FOMC, donnees/fomc.csv)
  a 14 h NY = 21:00 serveur (serveur = New York + 7 h, verifie par banc_annonces.py et ici par l'amplitude de la bougie
  d'annonce). Dates NFP/CPI reconstruites (calendriers BLS publies, reports dus aux fermetures de l'administration
  oct.-nov. 2025 et fev. 2026 ; BLS et FRED injoignables d'ici) puis CONTROLEES dans les bougies : chaque date doit
  montrer une bougie d'annonce >= 2 x l'amplitude habituelle sur l'or et le Nasdaq, sinon elle est signalee.
- Marches : or (XAU), NAS100+, SP500+, DJ30+, EURUSD, bougies M5 du courtier (aout 2025 -> nov. 2026 ; or et Nasdaq
  completes par les fichiers 2025a : juin -> aout 2025). M1 (aout -> nov. 2026, or / Nasdaq / SP) sert de CONTROLE du
  remplissage ; or M15 (oct. 2024 -> juin 2025, periode jamais vue) sert d'echantillon independant.
- Montage : a la cloture de la bougie T-5 min (prix P, juste avant l'annonce T), ordre stop d'achat a P + d et de
  vente a P - d, d = k x amplitude M5 moyenne des 2 h d'avant. Le premier touche prend la position, l'autre est annule ;
  ordres annules si rien ne part en 15 min. Stop : « milieu » (P, risque ~ d) ou « oppose » (l'autre niveau, ~ 2d).
  Sortie : objectif 2R, 3R, 5R ; stop suiveur a 1R du plus haut (mis a jour en fin de bougie) ; « suiveur+pyr » et
  « 5R+pyr » : a +1R on ajoute une 2e unite et le stop des deux passe au prix d'entree de la 1re. Tenue max 3 h
  (et avant 23:45 serveur).
- Couts PRUDENTS : entree = spread elargi (max des 3 bougies d'annonce) + 2 x ce spread de glissement (ordre stop
  servi au pire prix), ou au prix d'ouverture si la bougie saute le niveau ; sortie au stop = + 1 x ce spread de
  glissement (spread de la bougie apres 15 min) ; objectif = ordre limite, sans glissement. Dans une bougie ou le
  niveau d'entree ET le stop sont touches, on suppose le PIRE (stoppe) ; stop avant objectif si les deux sont touches.
- Grille : k {0,5 ; 1 ; 2} x stop {milieu, oppose} x sortie {2R, 3R, 5R, suiveur, suiveur+pyr, 5R+pyr} = 36 reglages,
  sur 6 univers (panier des 5 marches a notionnel egal + chaque marche seul) : N = 216 (+ 4 leviers x 2 departs pour
  la mise, qui ne changent pas l'avantage).
- Walk-forward : apprentissage 6 mois glissants, test le mois suivant, reglage au meilleur t (par annonce) de
  l'apprentissage. Hors-echantillon concatene : gain moyen par annonce, t, deux moities, p de Bonferroni (N = 216),
  reality check de White (t studentise, bootstrap stationnaire blocs 3 annonces, 2000 tirages) sur les 216 reglages.
  Temoins : (1) meme montage, memes heures, sur des jours ouvres SANS ces annonces tires au hasard (200 tirages) ;
  (2) sens au hasard, meme entree / meme tenue (et la reference « sans avantage » de pari_court_commun).
- Verdict fixe d'avance (protocole) : TIENT = hors-ech. > 0, p corrige < 0,05, > 0 sur les 2 moities, bat le temoin
  (centile >= 95) ; PRESQUE = signe constant non significatif ; sinon NE TIENT PAS.
- Sorties : donnees/pc_annonces.csv (trades hors-echantillon, colonnes regle, marche, t0, t1, r, cout, mae, unite,
  groupe) ; tableaux comparer() pour 100 et 500, leviers 10/25/50/100, dans le scratchpad res_pc_annonces.md (imprime).
Usage : python3 banc_pc_annonces.py   (~1-2 min)"""
import os, sys, math
import numpy as np, pandas as pd
import pari_court_commun as PC

ICI = os.path.dirname(os.path.abspath(__file__))
DON = os.path.join(ICI, "mt5", "donnees")
POINT = {"xau": 0.01, "nas": 0.01, "sp": 0.01, "dj": 0.01, "eur": 0.00001}
NOMS = {"xau": "XAUUSD", "nas": "NAS100+", "sp": "SP500+", "dj": "DJ30+", "eur": "EURUSD"}


def charge(f, mk):
    d = pd.read_csv(os.path.join(DON, f + ".csv.gz"))
    d.index = pd.to_datetime(d.heure, unit="s")
    d["sp"] = d.spread_points * POINT[mk]
    return d[["ouverture", "haut", "bas", "cloture", "sp"]].astype(float)


def charge_m5(mk):
    a = charge(mk + "_m5_90k", mk)
    if os.path.exists(os.path.join(DON, mk + "_m5_2025a.csv.gz")):
        b = charge(mk + "_m5_2025a", mk)
        a = pd.concat([b[b.index < a.index[0]], a])
    return a[~a.index.duplicated()]


# ------------------------------------------------------------------ calendrier (reconstruit, controle plus bas)
NFP = ["2024-10-04", "2024-11-01", "2024-12-06", "2025-01-10", "2025-02-07", "2025-03-07", "2025-04-04", "2025-05-02",
       "2025-06-06", "2025-07-03", "2025-08-01", "2025-09-05", "2025-11-20", "2025-12-16", "2026-01-09", "2026-02-11",
       "2026-03-06", "2026-04-03", "2026-05-08", "2026-06-05", "2026-07-02", "2026-08-07", "2026-09-04", "2026-10-02",
       "2026-11-06"]                                   # oct. 2025 annule (fermeture), fev. 2026 reporte au 11
CPI = ["2024-10-10", "2024-11-13", "2024-12-11", "2025-01-15", "2025-02-12", "2025-03-12", "2025-04-10", "2025-05-13",
       "2025-06-11", "2025-07-15", "2025-08-12", "2025-09-11", "2025-10-24", "2025-12-18", "2026-01-13", "2026-02-13",
       "2026-03-11", "2026-04-10", "2026-05-12", "2026-06-10", "2026-07-14", "2026-08-12", "2026-09-11", "2026-10-14",
       "2026-11-10"]                                   # nov. 2025 annule
FOMC = [d for d in pd.read_csv(os.path.join(ICI, "donnees", "fomc.csv")).annonce if "2024-09-01" <= d <= "2026-11-17"]
EV = sorted([(pd.Timestamp(d + " 15:30"), "NFP") for d in NFP] + [(pd.Timestamp(d + " 15:30"), "CPI") for d in CPI]
            + [(pd.Timestamp(d + " 21:00"), "FOMC") for d in FOMC])
EV = pd.DataFrame(EV, columns=["quand", "type"])

M5 = {mk: charge_m5(mk) for mk in NOMS}
UNITE = {"xau": 1 * M5["xau"].cloture.iloc[-1], "nas": 0.1 * M5["nas"].cloture.iloc[-1], "sp": 0.1 * M5["sp"].cloture.iloc[-1],
         "dj": 0.1 * M5["dj"].cloture.iloc[-1], "eur": 1000 * M5["eur"].cloture.iloc[-1]}

KS = (0.5, 1.0, 2.0); STOPS = ("milieu", "oppose"); SORTIES = ("2R", "3R", "5R", "suiveur", "suiveur+pyr", "5R+pyr")
GRILLE = [(k, s, x) for k in KS for s in STOPS for x in SORTIES]
UNIVERS = ["panier"] + list(NOMS)
N = len(GRILLE) * len(UNIVERS)
nomg = lambda g: "k%.1f %s %s" % g


# ------------------------------------------------------------------ simulation d'un montage sur des bougies
def sim(o, h, l, c, sp, tt, j0, P, d, spE, g, nwin, nmax, slip=2.0, xa=0.0):
    """Rend (sens, r, cout, mae, t_entree, t_sortie) en prix (pas encore divise par P) ou None si rien ne part.
    Vue « achat » : pour une vente on retourne les prix (-o, -l, -h, -c). xa : glissement EN PLUS (prix) a chaque
    ordre stop (entree, ajout, sortie au stop) pour le test de resistance."""
    k, smode, xmode = g
    up, dn = P + d, P - d
    j = None
    for jj in range(j0, min(j0 + nwin, len(o))):
        if h[jj] >= up or l[jj] <= dn:
            j = jj; break
    if j is None:
        return None
    both = h[j] >= up and l[j] <= dn
    s = 1 if h[j] >= up else -1
    if both:
        s = 1 if c[j] < o[j] else -1      # pire cas : on part du cote ou la bougie ne finit pas
    if s == 1:
        O, H, L, C = o, h, l, c; lev = up; stp = P if smode == "milieu" else dn
    else:
        O, H, L, C = -o, -l, -h, -c; lev = -dn; stp = -P if smode == "milieu" else -up
    fill = max(lev, O[j]) if j > j0 else lev
    ce = spE * (1 + slip) + xa
    cout = ce
    R = fill - stp
    tgt = {"2R": 2, "3R": 3, "5R": 5, "5R+pyr": 5}.get(xmode)
    pyr = xmode.endswith("pyr"); trail = xmode.startswith("suiveur")
    stop = stp; best = fill; ajout = None
    jend = min(j0 + nmax, len(o) - 1)
    while jend > j and (tt[jend].hour * 60 + tt[jend].minute) > 23 * 60 + 45 - 5 and tt[jend].date() == tt[j0].date():
        jend -= 1
    pire = fill; sortie = None; nu = 1
    for jj in range(j, jend + 1):
        sl = spE if jj < j0 + nwin else sp[jj]
        # 1) stop (prioritaire ; dans la bougie d'entree, toucher le stop = stoppe)
        if L[jj] <= stop:
            px = min(stop, O[jj]) if jj > j else stop
            sortie = (jj, px - sl - xa); cout += nu * (sl + xa); pire = min(pire, stop); break
        pire = min(pire, L[jj])
        # 2) ajout (pyramide) a +1R
        if pyr and ajout is None and H[jj] >= fill + R:
            ajout = fill + R + sl * (1 + slip) + xa; cout += sl * (1 + slip) + xa; nu = 2
            stop = max(stop, fill)
            if L[jj] <= stop:                  # meme bougie : on suppose le retour au stop
                sortie = (jj, stop - sl - xa); cout += nu * (sl + xa); break
        # 3) objectif (ordre limite)
        if tgt and H[jj] >= fill + tgt * R:
            sortie = (jj, fill + tgt * R); break
        if trail:
            best = max(best, H[jj]); stop = max(stop, best - R)
    if sortie is None:
        sortie = (jend, C[jend])
    js, px = sortie
    # couts d'entree payes en plus du prix ; glissement de sortie deja dans px (et compte dans cout)
    gain = (px - fill) - ce + ((px - ajout) if ajout is not None else 0.0)
    cout_tot = cout
    mae = max(fill - pire, 0) + ce + (max(ajout - pire, 0) if ajout is not None else 0)
    mae = max(mae, -gain)
    return s, gain, cout_tot, mae, tt[j], tt[js]


def prep(D, T, pas):
    """Indices et parametres d'une annonce T dans les bougies D (pas en minutes). None si trou de donnees."""
    t = D.index
    j0 = t.searchsorted(T)
    if j0 >= len(t) or t[j0] != T or j0 < 30:
        return None
    if (t[j0 - 1] != T - pd.Timedelta(minutes=pas)):
        return None
    return j0


def evenements_m5(xs=0.0):
    """Trades de tous les reglages, par marche et par annonce, sur les M5. Aussi le controle des dates."""
    rows, ctl = [], []
    for mk, D in M5.items():
        o, h, l, c, sp = (D[x].values for x in ("ouverture", "haut", "bas", "cloture", "sp")); tt = D.index
        amp = h - l
        for e, (T, ty) in EV.iterrows():
            j0 = prep(D, T, 5)
            if j0 is None or tt[j0 - 24] < T - pd.Timedelta(hours=3):
                continue
            atr = amp[j0 - 24:j0].mean()
            if not atr > 0:
                continue
            P = c[j0 - 1]; spE = sp[j0:j0 + 3].max()
            ctl.append(dict(mk=mk, e=e, T=T, type=ty, rap=amp[j0] / atr, pic=(tt[j0 - 12 + np.argmax(amp[j0 - 12:j0 + 13])] - T) / pd.Timedelta(minutes=1),
                            spE=spE / sp[j0 - 24:j0].mean()))
            for gi, g in enumerate(GRILLE):
                x = sim(o, h, l, c, sp, tt, j0, P, g[0] * atr, spE, g, 3, 36, xa=xs * atr)
                if x is None:
                    continue
                s, gain, cout, mae, t0, t1 = x
                rows.append(dict(mk=mk, e=e, T=T, type=ty, gi=gi, sens=s, r=gain / P, cout=cout / P, mae=mae / P, t0=t0, t1=t1, d=g[0] * atr / P))
    return pd.DataFrame(rows), pd.DataFrame(ctl)


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else 0.0


def matrice(TR, univ):
    """Gain par annonce (lignes) x reglage (colonnes). Panier : moyenne des 5 marches (0 si l'ordre ne part pas)."""
    x = TR if univ == "panier" else TR[TR.mk == univ]
    nm = len(NOMS) if univ == "panier" else 1
    M = x.groupby(["e", "gi"]).r.sum().unstack().reindex(columns=range(len(GRILLE))).fillna(0) / nm
    return M


def walk_forward(TR, P_, muet=False):
    """Walk-forward glissant (6 mois / 1 mois) pour chaque univers ; rend (matrices, hors-echantillon)."""
    ev_t = EV.quand
    mois = ev_t.dt.to_period("M")
    couverts = sorted(TR.e.unique()); m_c = mois[couverts]
    MO = sorted(m_c.unique())
    Ms = {u: matrice(TR, u).reindex(couverts).fillna(0) for u in UNIVERS}
    fen = [(MO[i - 6], MO[i - 1], MO[i]) for i in range(6, len(MO))]
    if not muet:
        P_("\n## Walk-forward (apprentissage 6 mois, test 1 mois) : %d annonces couvertes %s -> %s ; %d mois de test %s -> %s ; N = %d"
           % (len(couverts), ev_t[couverts[0]].date(), ev_t[couverts[-1]].date(), len(fen), fen[0][2], fen[-1][2], N))
        P_("univers | annonces OOS | trades | gain moyen/annonce (bp du notionnel) | t | moitie 1 | moitie 2 | reglage le + pris | p Bonferroni (N=%d)" % N)
    WF = {}
    for u in UNIVERS:
        M = Ms[u]; mm = m_c.reindex(M.index).values
        oos, ch = [], []
        for a, b, t_ in fen:
            app = (mm >= a) & (mm <= b); te = mm == t_
            if app.sum() < 5 or te.sum() == 0:
                continue
            gi = int(np.argmax([tstat(M.loc[app, g]) for g in range(len(GRILLE))]))
            ch += [gi] * te.sum(); oos.append(pd.DataFrame({"e": M.index[te], "gi": gi, "v": M.loc[te, gi].values}))
        O = pd.concat(oos)
        t = tstat(O.v); h1, h2 = np.array_split(O.v.values, 2)
        p1 = 0.5 * math.erfc(t / math.sqrt(2))   # loi normale (a peu pres la loi de Student pour n > 25)
        x = TR if u == "panier" else TR[TR.mk == u]
        ntr = len(x.merge(O[["e", "gi"]], on=["e", "gi"]))
        fq = pd.Series(ch).value_counts()
        O.attrs.update(t=t, h1=h1.mean(), h2=h2.mean(), pb=min(1, N * p1), ntr=ntr, mode=fq.index[0])
        WF[u] = O
        if not muet:
            P_("%-6s | %3d | %4d | %+7.1f | %+5.2f | %+6.1f | %+6.1f | %s (%d/%d) | %.3f"
               % (u, len(O), ntr, 1e4 * O.v.mean(), t, 1e4 * h1.mean(), 1e4 * h2.mean(), nomg(GRILLE[fq.index[0]]), fq.iloc[0], len(O), min(1, N * p1)))
    return Ms, WF


def main():
    out = []
    P_ = lambda *a: (print(*a), out.append(" ".join(str(z) for z in a)))
    TR, CTL = evenements_m5()
    # ---------------- controle des dates
    P_("## Controle du calendrier (bougie d'annonce / amplitude M5 moyenne des 2 h d'avant ; minute du pic +-60 min)")
    for ty in ("NFP", "CPI", "FOMC"):
        z = CTL[(CTL.type == ty) & CTL.mk.isin(["xau", "nas"])]
        P_("- %s : %d annonces couvertes (or+Nasdaq), rapport median %.1fx, pic a l'heure prevue %d %% ; spread elargi median %.1fx l'habituel"
           % (ty, z.e.nunique(), z.rap.median(), 100 * (z.pic.abs() <= 5).mean(), z.spE.median()))
    dout = CTL[CTL.mk.isin(["xau", "nas"])].groupby(["e"]).agg(T=("T", "first"), ty=("type", "first"), rap=("rap", "max"))
    faibles = dout[dout.rap < 2]
    P_("- dates douteuses (rapport < 2 sur l'or ET le Nasdaq) : %s" % (", ".join("%s %s %.1fx" % (r.T.date(), r.ty, r.rap) for r in faibles.itertuples()) or "aucune"))
    Ms, WF = walk_forward(TR, P_)
    # ---------------- reality check de White sur les 216 reglages (t studentise)
    A = np.column_stack([Ms[u][g].values for u in UNIVERS for g in range(len(GRILLE))])
    n = len(A); rng = np.random.default_rng(11)
    sd = A.std(0, ddof=1); sd[sd == 0] = np.inf
    tv = np.sqrt(n) * A.mean(0) / sd
    def bidx():
        i = np.empty(n, int); i[0] = rng.integers(n); nv = rng.integers(n, size=n); neuf = rng.random(n) < 1 / 3
        for k in range(1, n):
            i[k] = nv[k] if neuf[k] else (i[k - 1] + 1) % n
        return i
    mx = np.array([(np.sqrt(n) * (A[ii].mean(0) - A.mean(0)) / sd).max() for ii in (bidx() for _ in range(2000))])
    best = int(np.argmax(tv)); ub, gb = UNIVERS[best // len(GRILLE)], GRILLE[best % len(GRILLE)]
    p_rc = (mx >= tv.max()).mean()
    P_("\nMeilleur des %d reglages sur tout l'echantillon : %s %s, %+.1f bp/annonce, t %+.2f ; reality check de White p = %.3f ; reglages a moyenne > 0 : %d/%d"
       % (N, ub, nomg(gb), 1e4 * A[:, best].mean(), tv.max(), p_rc, (A.mean(0) > 0).sum(), N))
    # tableau resume par sortie / stop (panier, toutes annonces) pour voir la forme
    P_("\nPanier, tout l'echantillon, gain moyen par annonce (bp) par reglage :")
    P_("k / stop      " + "".join("%12s" % x for x in SORTIES))
    for k in KS:
        for s in STOPS:
            P_("%-4.1f %-8s" % (k, s) + "".join("%+12.1f" % (1e4 * Ms["panier"][GRILLE.index((k, s, x))].mean()) for x in SORTIES))
    # detail du panier hors-echantillon
    O = WF["panier"]; ty = O.e.map(EV.type)
    P_("\nPanier hors-echantillon par type : " + " ; ".join("%s %d annonces %+.1f bp (t %+.2f)" % (k, (ty == k).sum(), 1e4 * O.v[ty == k].mean(), tstat(O.v[ty == k])) for k in ("NFP", "CPI", "FOMC")))
    v = O.v.sort_values()
    P_("Concentration : sans les 2 meilleures annonces %+.1f bp/annonce ; sans les 5 meilleures %+.1f ; part des annonces gagnantes %.0f %%"
       % (1e4 * v.iloc[:-2].mean(), 1e4 * v.iloc[:-5].mean(), 100 * (O.v > 0).mean()))
    # test de resistance au glissement : xs x amplitude M5 d'avant EN PLUS a chaque ordre stop, walk-forward refait
    P_("\n## Resistance au glissement (en plus de 3 x le spread : xs x l'amplitude M5 moyenne d'avant, a chaque ordre stop ; walk-forward refait)")
    P_("xs   | " + " | ".join("%-22s" % u for u in UNIVERS))
    lig = "0    | " + " | ".join("%+6.1f bp t %+5.2f      " % (1e4 * WF[u].v.mean(), WF[u].attrs["t"]) for u in UNIVERS)
    P_(lig)
    for xs in (0.1, 0.25, 0.5):
        TRx, _ = evenements_m5(xs)
        _, W = walk_forward(TRx, P_, muet=True)
        P_("%-4.2f | " % xs + " | ".join("%+6.1f bp t %+5.2f      " % (1e4 * W[u].v.mean(), W[u].attrs["t"]) for u in UNIVERS))
    return TR, CTL, WF, Ms, out, (ub, gb, p_rc)


def temoins(TR, WF, u, out, tirages=200):
    """Meme montage, memes heures, jours ouvres sans NFP/CPI/FOMC tires au hasard ; et sens au hasard."""
    P_ = lambda *a: (print(*a), out.append(" ".join(str(z) for z in a)))
    O = WF[u]
    reel = O.v.mean()
    jours_ann = set(EV.quand.dt.normalize())
    mks = list(NOMS) if u == "panier" else [u]
    nm = len(mks)
    rng = np.random.default_rng(5)
    # pre-calcul : pour chaque jour ouvre libre et chaque heure (15:30, 21:00), le gain de chaque reglage utilise
    gis = sorted(O.gi.unique())
    D0 = M5["xau"].index.normalize().unique()
    D0 = D0[(D0.dayofweek < 5) & (D0 >= O.e.map(EV.quand).min().normalize() - pd.Timedelta(days=200))]
    libres = [d for d in D0 if d not in jours_ann]
    cache = {}
    def gain(day, hm, gi):
        key = (day, hm, gi)
        if key in cache:
            return cache[key]
        T = day + pd.Timedelta(hm); tot = 0.0
        for mk in mks:
            D = M5[mk]; j0 = prep(D, T, 5)
            if j0 is None:
                continue
            o, h, l, c, sp = (D[x].values for x in ("ouverture", "haut", "bas", "cloture", "sp"))
            atr = (h[j0 - 24:j0] - l[j0 - 24:j0]).mean()
            if not atr > 0:
                continue
            x = sim(o, h, l, c, sp, D.index, j0, c[j0 - 1], GRILLE[gi][0] * atr, sp[j0:j0 + 3].max(), GRILLE[gi], 3, 36)
            if x is not None:
                tot += x[1] / c[j0 - 1]
        cache[key] = tot / nm
        return cache[key]
    hm = O.e.map(lambda e: "%02d:%02d:00" % (EV.quand[e].hour, EV.quand[e].minute)).values
    res = []
    for _ in range(tirages):
        dd = rng.choice(len(libres), len(O), replace=False)
        res.append(np.mean([gain(libres[i], h_, g) for i, h_, g in zip(dd, hm, O.gi.values)]))
    res = np.array(res)
    # sens au hasard : meme entree, meme tenue, gain = +-|mouvement| ... approxime par r + 2 x cout centre
    x = TR if u == "panier" else TR[TR.mk == u]
    sel = x.merge(O[["e", "gi"]], on=["e", "gi"])
    brut = sel.r + sel.cout
    alea = np.array([((rng.choice([-1, 1], len(sel)) * brut - sel.cout).groupby(sel.e.values).sum() / nm).reindex(O.e).fillna(0).mean() for _ in range(2000)])
    P_("Temoin jours sans annonce (memes heures, memes reglages, %d tirages) : moyen %+.1f bp, 5e-95e %+.1f / %+.1f ; reel %+.1f bp -> centile %.0f"
       % (tirages, 1e4 * res.mean(), 1e4 * np.percentile(res, 5), 1e4 * np.percentile(res, 95), 1e4 * reel, 100 * (res < reel).mean()))
    P_("Temoin sens au hasard (meme entree, meme sortie, couts payes, 2000 tirages) : moyen %+.1f bp, 95e %+.1f ; reel %+.1f -> centile %.0f"
       % (1e4 * alea.mean(), 1e4 * np.percentile(alea, 95), 1e4 * reel, 100 * (alea < reel).mean()))
    return (res < reel).mean()


def controle_m1(TR, out):
    """Memes annonces, memes niveaux (d calcule sur M5), simulees sur M1 : le pire-cas M5 est-il trop pessimiste ?"""
    P_ = lambda *a: (print(*a), out.append(" ".join(str(z) for z in a)))
    rows = []
    for mk in ("xau", "nas", "sp"):
        D = charge(mk + "_m1_90k", mk); D5 = M5[mk]
        o, h, l, c, sp = (D[x].values for x in ("ouverture", "haut", "bas", "cloture", "sp"))
        for e, (T, ty) in EV.iterrows():
            if T < D.index[0] + pd.Timedelta(hours=3) or T > D.index[-1]:
                continue
            j0 = prep(D, T, 1); j5 = prep(D5, T, 5)
            if j0 is None or j5 is None:
                continue
            a5 = (D5.haut.values[j5 - 24:j5] - D5.bas.values[j5 - 24:j5]).mean()
            spE = D5.sp.values[j5:j5 + 3].max(); P = c[j0 - 1]
            for gi, g in enumerate(GRILLE):
                x = sim(o, h, l, c, sp, D.index, j0, P, g[0] * a5, spE, g, 15, 180)
                if x is not None:
                    rows.append(dict(mk=mk, e=e, gi=gi, r1=x[1] / P))
    R1 = pd.DataFrame(rows)
    if R1.empty:
        P_("Controle M1 : aucune annonce couverte"); return
    m = R1.merge(TR[["mk", "e", "gi", "r"]], on=["mk", "e", "gi"], how="left")
    P_("Controle M1 (or, Nasdaq, SP ; %d annonces aout -> nov. 2026, 36 reglages) : gain moyen M1 %+.1f bp contre M5 pire-cas %+.1f bp sur les memes trades ; correlation %.2f"
       % (m.e.nunique(), 1e4 * m.r1.mean(), 1e4 * m.r.mean(), m[["r1", "r"]].corr().iloc[0, 1]))
    by = m.groupby("gi")[["r1", "r"]].mean()
    P_("  reglages a moyenne > 0 : M1 %d/36, M5 %d/36 ; meilleur M1 : %s %+.1f bp" % ((by.r1 > 0).sum(), (by.r > 0).sum(), nomg(GRILLE[by.r1.idxmax()]), 1e4 * by.r1.max()))


def controle_m15(gis, out):
    """Or M15, oct. 2024 -> juin 2025 (avant les M5) : echantillon independant pour les reglages retenus."""
    P_ = lambda *a: (print(*a), out.append(" ".join(str(z) for z in a)))
    D = charge("xau_m15_50k", "xau"); D5 = M5["xau"]
    # calibration amplitude M5 (2 h) / amplitude M15 (2 h) sur la periode commune
    a15 = (D.haut - D.bas).rolling(8).mean(); a5 = (D5.haut - D5.bas).rolling(24).mean()
    com = a15.index.intersection(a5.index)
    ratio = (a5[com] / a15[com]).median()
    o, h, l, c, sp = (D[x].values for x in ("ouverture", "haut", "bas", "cloture", "sp"))
    rows = []
    for e, (T, ty) in EV.iterrows():
        if T >= D5.index[0] - pd.Timedelta(days=1):
            continue
        T15 = T.floor("15min")
        j0 = prep(D, T15, 15)
        if j0 is None:
            continue
        atr = (h[j0 - 8:j0] - l[j0 - 8:j0]).mean() * ratio
        P = c[j0 - 1]; spE = sp[j0:j0 + 1].max()
        for gi, g in enumerate(GRILLE):
            x = sim(o, h, l, c, sp, D.index, j0, P, g[0] * atr, spE, g, 1, 12)
            rows.append(dict(e=e, gi=gi, r=(x[1] / P) if x is not None else 0.0))
    R = pd.DataFrame(rows)
    if R.empty:
        return
    M = R.pivot(index="e", columns="gi", values="r")
    P_("Or M15 hors periode (%s -> %s, %d annonces, amplitude M5 = %.2f x M15, pire-cas M15 encore plus dur) : reglages a moyenne > 0 : %d/36"
       % (EV.quand[M.index[0]].date(), EV.quand[M.index[-1]].date(), len(M), ratio, (M.mean() > 0).sum()))
    for gi in gis:
        P_("  %s : %+.1f bp/annonce, t %+.2f" % (nomg(GRILLE[gi]), 1e4 * M[gi].mean(), tstat(M[gi])))


if __name__ == "__main__":
    TR, CTL, WF, Ms, out, (ub, gb, p_rc) = main()
    P_ = lambda *a: (print(*a), out.append(" ".join(str(z) for z in a)))
    # univers retenu : le panier (choisi d'avance) ; on montre aussi le meilleur marche seul (choix a posteriori)
    tb = {u: tstat(WF[u].v) for u in UNIVERS}
    um = max(UNIVERS[1:], key=lambda u: tb[u])
    P_("\n## Temoins")
    cent = {}
    for u in ("panier", um):
        P_("- %s :" % u)
        cent[u] = temoins(TR, WF, u, out)
    P_("\n## Controles de robustesse")
    controle_m1(TR, out)
    gis = sorted(set(WF["panier"].gi.value_counts().index[:2]) | set(WF[um].gi.value_counts().index[:1]))
    controle_m15(gis, out)
    # ---------------- trades hors-echantillon -> pc_annonces.csv
    lignes = []
    for u in UNIVERS:
        O = WF[u]
        x = TR if u == "panier" else TR[TR.mk == u]
        s = x.merge(O[["e", "gi"]], on=["e", "gi"])
        s = s.assign(regle="annonces_%s_" % u + s.gi.map(lambda g: nomg(GRILLE[g]).replace(" ", "_")), marche=s.mk.map(NOMS),
                     unite=s.mk.map(UNITE), groupe=u + "_" + s.e.astype(str), univers=u)
        lignes.append(s)
    TT = pd.concat(lignes)
    sortie = TT[["regle", "marche", "univers", "t0", "t1", "r", "cout", "mae", "unite", "groupe", "sens"]].copy()
    sortie["t0"] = sortie.t0.dt.strftime("%Y-%m-%dT%H:%M"); sortie["t1"] = sortie.t1.dt.strftime("%Y-%m-%dT%H:%M")
    sortie.to_csv(os.path.join(ICI, "donnees", "pc_annonces.csv"), index=False)
    P_("\nTrades hors-echantillon ecrits : donnees/pc_annonces.csv (%d lignes, %d univers)" % (len(sortie), len(UNIVERS)))
    # ---------------- comparer() du meilleur montage (panier, choisi d'avance) et du meilleur marche seul (a posteriori)
    pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
    for u in ("panier", um):
        T = TT[TT.univers == u][["t0", "t1", "r", "cout", "mae", "unite", "groupe"]].reset_index(drop=True)
        P_("\n## comparer() : %s, %d trades hors-echantillon, r moyen %+.1f bp, cout moyen %.1f bp" % (u, len(T), 1e4 * T.r.mean(), 1e4 * T.cout.mean()))
        for dep in (100, 500):
            for L in (10, 25, 50, 100):
                R = PC.comparer(T, L, depart=dep)
                R = R[["version", "horizon", "fenetres", "ruine", "x2", "x3", "x5", "x10", "esperance", "bat_ref"]]
                P_("\ndepart %d, levier %d" % (dep, L))
                P_(R.to_string(index=False, float_format=lambda v: "%.3f" % v))
    with open(os.path.join("/tmp/claude-0/-home-user-Copybot-Crypto/266229b5-4b1a-583f-a0ab-324e661078db/scratchpad", "sortie_pc_annonces.txt"), "w") as f:
        f.write("\n".join(out))
