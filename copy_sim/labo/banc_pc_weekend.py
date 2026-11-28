"""Banc PC-WE : le week-end crypto pour la poche « pari court » (PRIORITES 17/11 20 h 10). Usage : python3 banc_pc_weekend.py
Plan fixe d'avance (rien n'a ete regarde avant d'ecrire la grille) :
0. Le courtier cote-t-il BTCUSD / ETHUSD le week-end ? M5 courtier 01/2026 -> 11/2026 : bougies par jour de la semaine,
   spread median par jour, trous de cotation.
1. Donnees de preuve : Yahoo journalier BTC-USD 2014-09 -> 2026-11, ETH-USD 2017-11 -> 2026-11 (donnees/gj_btc, gj_eth ;
   jour = 0 h -> 24 h UTC, ouvert 7 j / 7). Vendredi = cloture du vendredi 24 h UTC (samedi 2 h / 3 h serveur).
2. Grille par marche (28 reglages ; 2 marches -> 56) :
   « we2 » vendredi soir -> dimanche soir (2 nuits), « we3 » vendredi soir -> lundi soir (3 nuits) :
      sens fixe achat / vente (2 x 2 = 4) ;
      selon le mouvement de la semaine (dimanche soir -> vendredi soir, 5 j) ou du vendredi (1 j) : suite / contre-pied,
      seuil |mouvement| > k x sigma(60 j) x racine(jours), k dans {0, 1} : 2 fenetres x 2 x 2 x 2 = 16 ;
   « lun » le lundi (dimanche soir -> lundi soir, 1 nuit) : sens fixe achat / vente (2) ; selon le mouvement du week-end
      (vendredi soir -> dimanche soir) : suite / contre-pied, k dans {0, 1, 2} (6) => 8.
   Leviers de la poche : 10, 25, 50, 100 (4). N = 56 x 4 = 224 essais (Bonferroni sur 224, tres prudent : le levier ne
   change pas le t).
3. Couts : spread median du courtier tire des M5 (BTC ~2,3 bp, ETH ~11,5 bp, identique le week-end) + glissement 1 bp
   + financement CFD crypto PRUDENT 25 % par an / 365 par nuit tenue (achat ET vente payent ; aucun swap reel n'est
   disponible dans etat.json ni le journal). Sensibilite : 10 % et 0 %.
4. Walk-forward : chaque annee civile, le reglage (par marche) au meilleur t net sur les 3 annees precedentes (>= 20
   trades, moyenne > 0, sinon rien cette annee-la) est joue l'annee suivante. BTC : hors-echantillon 2018-2026, ETH : 2021-2026.
5. Controles : t hors-echantillon, deux moitiés, temoin simple (toujours acheteur sur le meme creneau), entrees au
   hasard (memes durees, memes sens, n'importe quel jour, 2 000 tirages), reality check de White (bootstrap par blocs
   de 4 semaines du max des t sur les 56 reglages centres), Bonferroni.
6. Controle courtier : les trades 2026 du walk-forward rejoues sur les M5 (prix d'achat = bid + spread de la bougie).
   Variante intrajournaliere (descriptive, 10 mois seulement, comptee dans N) : grand week-end puis contre-pied a
   l'ouverture US du lundi (13 h 30 UTC -> lundi 24 h UTC).
7. Poche : comparer() de pari_court_commun pour 100 et 500, leviers 10 / 25 / 50 / 100, sur les trades hors echantillon ;
   sortie donnees/pc_pc_weekend.csv. Unite = 0,01 lot x prix d'aujourd'hui (BTC 638 $, ETH 17,9 $)."""
import os, sys
import numpy as np, pandas as pd

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import pari_court_commun as PC

DON, MT5 = os.path.join(ICI, "donnees"), os.path.join(ICI, "mt5", "donnees")
SCR = "/tmp/claude-0/-home-user-Copybot-Crypto/266229b5-4b1a-583f-a0ab-324e661078db/scratchpad"
FIN_AN, GLISS = 0.25, 1e-4
PRIX = {"BTC": 63801.42, "ETH": 1789.84}          # etat.json « symboles », 17/11/2026
LEVIERS = (10, 25, 50, 100)
rng = np.random.default_rng(1711)
out_lignes = []


def dire(*a):
    s = " ".join(str(x) for x in a); print(s); out_lignes.append(s)


def m5(nom):
    d = pd.read_csv(os.path.join(MT5, nom.lower() + "_m5_90k.csv.gz"))
    srv = pd.to_datetime(d.heure, unit="s")
    # heure serveur = New York + 7 h  ->  UTC
    d["utc"] = (srv - pd.Timedelta(hours=7)).dt.tz_localize("America/New_York", ambiguous="NaT",
                                                              nonexistent="shift_forward").dt.tz_convert(None)
    d = d.dropna(subset=["utc"])
    d["sp"] = d.spread_points * 0.01
    return d


def etape0():
    dire("## 0. Cotation du week-end (M5 courtier)")
    sp = {}
    for nom in ("BTC", "ETH"):
        d = m5(nom); dw = d.utc.dt.dayofweek
        b = d.sp / d.cloture * 1e4
        t = d.groupby(dw).agg(bougies=("sp", "size"), spread_bp=("sp", lambda x: (x / d.cloture[x.index] * 1e4).median()),
                              ticks=("volume_ticks", "median"))
        t.index = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]
        trous = (d.utc.diff() > pd.Timedelta(minutes=30)).sum()
        dire("%s : %s -> %s, %d bougies, %d trous > 30 min (maintenance), spread median %.2f bp (sam/dim %.2f bp)" % (
            nom, d.utc.min().date(), d.utc.max().date(), len(d), trous, b.median(), b[dw >= 5].median()))
        dire(t.round(2).T.to_string())
        sp[nom] = b.median() * 1e-4
    return sp


def jour(nom):
    d = pd.read_csv(os.path.join(DON, "gj_%s.csv.gz" % nom.lower()), parse_dates=["date"]).set_index("date")
    d = d.asfreq("D").ffill()
    d["sig"] = np.log(d.close).diff().rolling(60).std()
    return d


def evenements(d):
    """Une ligne par semaine (vendredi F) avec les prix utiles."""
    E = []
    for F in d.index[(d.index.dayofweek == 4)]:
        D, L, J, S = F + pd.Timedelta(days=2), F + pd.Timedelta(days=3), F - pd.Timedelta(days=1), F - pd.Timedelta(days=5)
        if L not in d.index or S not in d.index or np.isnan(d.sig[F]):
            continue
        E.append(dict(F=F, cF=d.close[F], cJ=d.close[J], cS=d.close[S], cD=d.close[D], cL=d.close[L],
                      sigF=d.sig[F], sigD=d.sig[D]))
    return pd.DataFrame(E)


def grille():
    G = []
    for f in ("we2", "we3"):
        for s in (1, -1):
            G.append((f, "aucun", s, 0))
        for c in ("semaine", "vendredi"):
            for s in (1, -1):
                for k in (0, 1):
                    G.append((f, c, s, k))
    for s in (1, -1):
        G.append(("lun", "aucun", s, 0))
    for s in (1, -1):
        for k in (0, 1, 2):
            G.append(("lun", "weekend", s, k))
    return G


def nom_reg(g):
    f, c, s, k = g
    if c == "aucun":
        return "%s %s" % (f, "achat" if s > 0 else "vente")
    return "%s %s %s k%d" % (f, "suite" if s > 0 else "contre", c, k)


def trades(d, E, g, cout_fixe, fin):
    f, c, s, k = g
    if f == "lun":
        e0, e1, nuits, t0 = E.cD, E.cL, 1, E.F + pd.Timedelta(days=3)
    else:
        e0, e1, nuits, t0 = E.cF, (E.cD if f == "we2" else E.cL), (2 if f == "we2" else 3), E.F + pd.Timedelta(days=1)
    if c == "aucun":
        sens = pd.Series(s, index=E.index)
    else:
        if c == "semaine":
            m, sg = np.log(E.cF / E.cS), E.sigF * np.sqrt(5)
        elif c == "vendredi":
            m, sg = np.log(E.cF / E.cJ), E.sigF
        else:
            m, sg = np.log(E.cD / E.cF), E.sigD * np.sqrt(2)
        sens = np.sign(m) * s * (np.abs(m) > k * sg)
    ok = sens != 0
    T = pd.DataFrame(dict(t0=t0[ok], t1=t0[ok] + pd.Timedelta(days=nuits), sens=sens[ok].astype(int),
                          brut=(sens * (e1 / e0 - 1))[ok], semaine=E.F[ok]))
    cout = cout_fixe + nuits * fin / 365
    T["cout"] = cout; T["r"] = T.brut - cout
    # pire excursion pendant la tenue (bas / hauts journaliers des jours tenus)
    mae = []
    for a, b, sn in zip(T.t0, T.t1, T.sens):
        x = d.loc[a:b - pd.Timedelta(days=1)]
        ent = d.close[a - pd.Timedelta(days=1)]
        mae.append(max(0.0, 1 - x.low.min() / ent) if sn > 0 else max(0.0, x.high.max() / ent - 1))
    T["mae"] = mae
    return T.reset_index(drop=True)


def tstat(r):
    r = np.asarray(r)
    return r.mean() / r.std(ddof=1) * np.sqrt(len(r)) if len(r) > 2 and r.std() > 0 else 0.0


def white(TT, semaines, nb=2000, bloc=4):
    """Reality check de White : matrice semaines x reglages (0 si pas de trade), centree ; max des t."""
    M = np.zeros((len(semaines), len(TT))); pos = {w: i for i, w in enumerate(semaines)}
    for j, T in enumerate(TT):
        for w, r in zip(T.semaine, T.r):
            M[pos[w], j] += r
    def tm(X):
        s = X.std(0, ddof=1); s[s == 0] = np.inf
        return X.mean(0) / s * np.sqrt(len(X))
    obs = tm(M).max(); C = M - M.mean(0); n = len(M); bs = []
    for _ in range(nb):
        st = rng.integers(0, n, n // bloc + 1)
        idx = (st[:, None] + np.arange(bloc)).ravel()[:n] % n
        bs.append(tm(C[idx]).max())
    return obs, (np.array(bs) >= obs).mean()


def hasard(d, T, cout_fixe, fin, debut, nb=2000):
    """Memes durees, memes sens, n'importe quel jour de la periode : moyenne nette."""
    jours = d.index[(d.index >= debut) & (d.index < d.index[-1] - pd.Timedelta(days=4))]
    c = d.close.values; ix = {j: i for i, j in enumerate(d.index)}
    n = ((T.t1 - T.t0).dt.days).values; s = T.sens.values
    res = []
    for _ in range(nb):
        j = rng.integers(0, len(jours), len(T)); i0 = np.array([ix[jours[x]] for x in j]) - 1
        b = s * (c[i0 + n] / c[i0] - 1) - cout_fixe - n * fin / 365
        res.append(b.mean())
    return np.array(res)


def walk_forward(d, E, G, cout_fixe, fin, an0):
    TT = {g: trades(d, E, g, cout_fixe, fin) for g in G}
    oos, choix = [], []
    for an in range(an0, 2027):
        best, bt = None, -np.inf
        for g, T in TT.items():
            x = T[(T.t0.dt.year >= an - 3) & (T.t0.dt.year < an)]
            if len(x) >= 20 and x.r.mean() > 0 and tstat(x.r) > bt:
                best, bt = g, tstat(x.r)
        choix.append((an, nom_reg(best) if best else "rien", round(bt, 2) if best else None))
        if best:
            oos.append(TT[best][TT[best].t0.dt.year == an].assign(regle=nom_reg(best)))
    return TT, pd.concat(oos, ignore_index=True), choix


def controle_m5(nom, T, sp_med):
    """Rejoue les trades 2026 sur les M5 courtier : achat = bid + spread de la bougie d'entree, vente au bid."""
    d = m5(nom).set_index("utc").sort_index()
    out = []
    for _, x in T[T.t0 >= d.index[0]].iterrows():
        a = d.loc[x.t0 - pd.Timedelta(minutes=5):].head(1); b = d.loc[x.t1 - pd.Timedelta(minutes=5):].head(1)
        if len(a) == 0 or len(b) == 0 or b.index[0] - x.t1 > pd.Timedelta(hours=2):
            continue
        pa, sa, pb, sb = a.cloture.iloc[0], a.sp.iloc[0], b.cloture.iloc[0], b.sp.iloc[0]
        if x.sens > 0:
            r = (pb - (pa + sa)) / (pa + sa)
        else:
            r = (pa - (pb + sb)) / pa
        nuits = (x.t1 - x.t0).days
        out.append((x.t0, x.r, r - GLISS - nuits * FIN_AN / 365))
    return pd.DataFrame(out, columns=["t0", "r_yahoo", "r_m5"])


def lundi_us(nom, k=1.0):
    """Descriptif : grand week-end (|ven 24 h -> lun 13 h 30 UTC| > k sigma) puis contre-pied 13 h 30 -> 24 h UTC."""
    d = m5(nom).set_index("utc").sort_index()
    c = d.cloture.resample("D").last().dropna(); sig = np.log(c).diff().rolling(60).std()
    R = []
    for L in c.index[c.index.dayofweek == 0]:
        try:
            pf = d.loc[:L - pd.Timedelta(days=2)].cloture.iloc[-1]
            e = d.loc[L + pd.Timedelta(hours=13, minutes=30):].head(1); f = d.loc[:L + pd.Timedelta(days=1)].tail(1)
        except IndexError:
            continue
        if len(e) == 0 or np.isnan(sig.get(L - pd.Timedelta(days=3), np.nan)):
            continue
        m = np.log(e.cloture.iloc[0] / pf)
        if abs(m) <= k * sig[L - pd.Timedelta(days=3)] * np.sqrt(2.5):
            continue
        s = -np.sign(m); pa, sa, pb = e.cloture.iloc[0], e.sp.iloc[0], f.cloture.iloc[0]
        r = (pb - pa - sa) / pa if s > 0 else (pa - pb - f.sp.iloc[0]) / pa
        R.append(r - GLISS)
    return np.array(R)


def main():
    sp = etape0()
    G = grille(); N = 2 * len(G) * len(LEVIERS)
    dire("\n## 1-5. Preuve sur Yahoo journalier (couts : spread median + 1 bp + financement %d %%/an)" % (FIN_AN * 100))
    dire("Grille : %d reglages par marche, 2 marches, %d leviers => N = %d" % (len(G), len(LEVIERS), N))
    tous_oos, tous_TT, sem = [], [], set()
    lignes = []
    for nom, an0 in (("BTC", 2018), ("ETH", 2021)):
        d = jour(nom); E = evenements(d); cf = sp[nom] + GLISS
        TT, oos, choix = walk_forward(d, E, G, cf, FIN_AN, an0)
        oos["marche"] = nom
        dire("\n### %s : %s -> %s, %d week-ends" % (nom, d.index[0].date(), d.index[-1].date(), len(E)))
        # tableau plein echantillon des reglages (pour info, le choix reel est le walk-forward)
        P = pd.DataFrame([(nom_reg(g), len(T), T.r.mean() * 1e4, tstat(T.r), T.brut.mean() * 1e4) for g, T in TT.items()],
                         columns=["reglage", "trades", "net_bp", "t", "brut_bp"]).sort_values("t", ascending=False)
        dire("Plein echantillon (net apres couts ; brut = avant couts) :")
        dire(P.round(2).to_string(index=False))
        dire("Choix du walk-forward (annee, reglage, t sur les 3 ans d'avant) : %s" % choix)
        h = len(oos) // 2
        t_oos = tstat(oos.r)
        tem = TT[("we2", "aucun", 1, 0)]; tem = tem[tem.t0.dt.year >= an0]
        hz = hasard(d, oos, cf, FIN_AN, pd.Timestamp("%d-01-01" % an0))
        p_h = (hz >= oos.r.mean()).mean()
        from math import erf, sqrt
        p1 = 1 - 0.5 * (1 + erf(t_oos / sqrt(2)))
        dire("Hors-echantillon %s : %d trades, moyenne %.1f bp, t = %.2f (p unilateral %.3f, Bonferroni x%d : %.2f) ; "
             "moities %.1f / %.1f bp (t %.2f / %.2f) ; temoin achat we2 %.1f bp (t %.2f) ; hasard : moyenne %.1f bp, "
             "p = %.3f" % (nom, len(oos), oos.r.mean() * 1e4, t_oos, p1, N, min(1, p1 * N), oos.r[:h].mean() * 1e4,
                          oos.r[h:].mean() * 1e4, tstat(oos.r[:h]), tstat(oos.r[h:]), tem.r.mean() * 1e4, tstat(tem.r),
                          hz.mean() * 1e4, p_h))
        # sensibilite au financement
        for fa in (0.10, 0.0):
            _, o2, ch2 = walk_forward(d, E, G, cf, fa, an0)
            dire("  financement %d %%/an : hors-ech. %d trades, %.1f bp, t = %.2f ; choix %s" % (
                fa * 100, len(o2), o2.r.mean() * 1e4, tstat(o2.r), [c[1] for c in ch2]))
        lignes.append((nom, "%s->%s" % (d.index[0].date(), d.index[-1].date()), len(G) * len(LEVIERS), "WF annuel",
                       len(oos), oos.r.mean() * 1e4, t_oos, (oos.r[:h].mean() * 1e4, oos.r[h:].mean() * 1e4),
                       tem.r.mean() * 1e4, min(1, p1 * N), p_h))
        tous_oos.append(oos); tous_TT += [T.assign(semaine=T.semaine) for T in TT.values()]
        sem |= set(E.F)
        # controle courtier
        cm = controle_m5(nom, oos, sp[nom])
        if len(cm):
            dire("Controle M5 courtier (trades 2026 du walk-forward) : %d trades, Yahoo %.1f bp, M5 spread reel %.1f bp, "
                 "correlation %.2f" % (len(cm), cm.r_yahoo.mean() * 1e4, cm.r_m5.mean() * 1e4,
                                       np.corrcoef(cm.r_yahoo, cm.r_m5)[0, 1]))
        lu = lundi_us(nom)
        dire("Descriptif M5 : contre-pied lundi 13 h 30 UTC apres grand week-end (k=1) : %d trades, %.1f bp, t = %.2f" % (
            len(lu), lu.mean() * 1e4 if len(lu) else np.nan, tstat(lu)))
    obs, pw = white(tous_TT, sorted(sem))
    dire("\nReality check de White (56 reglages, plein echantillon) : meilleur t = %.2f, p = %.3f" % (obs, pw))
    O = pd.concat(tous_oos, ignore_index=True).sort_values("t0").reset_index(drop=True)
    tO = tstat(O.r)
    dire("Hors-echantillon BTC + ETH : %d trades, %.1f bp, t = %.2f" % (len(O), O.r.mean() * 1e4, tO))

    # poche : comparer() sur les trades hors echantillon
    O["unite"] = O.marche.map(lambda m: 0.01 * PRIX[m])
    O["t0"] = O.t0.dt.strftime("%Y-%m-%dT%H:%M:%S"); O["t1"] = O.t1.dt.strftime("%Y-%m-%dT%H:%M:%S")
    O[["regle", "marche", "t0", "t1", "sens", "r", "cout", "mae", "unite"]].to_csv(
        os.path.join(DON, "pc_pc_weekend.csv"), index=False)
    T = O.assign(t0=pd.to_datetime(O.t0), t1=pd.to_datetime(O.t1))
    dire("\n## 7. Poche pari court : comparer() sur les %d trades hors echantillon (BTC + ETH)" % len(T))
    tables = {}
    for dep in (100, 500):
        for L in LEVIERS:
            R = PC.comparer(T[["t0", "t1", "r", "cout", "mae", "unite"]], L, depart=dep)
            tables[(dep, L)] = R
            dire("\n### depart %d, levier %d" % (dep, L))
            dire(R.drop(columns=["se_x3"]).round(3).to_string(index=False))
    # borne OPTIMISTE (choisie en voyant tout l'echantillon, donc biaisee) : BTC « lun achat », meilleur t plein echantillon
    d = jour("BTC"); B = trades(d, evenements(d), ("lun", "aucun", 1, 0), sp["BTC"] + GLISS, FIN_AN)
    B = B.assign(unite=0.01 * PRIX["BTC"])
    dire("\n## Borne optimiste, biaisee (BTC lun achat, plein echantillon 2014-2026, %d trades, %.1f bp)" % (len(B), B.r.mean() * 1e4))
    for dep in (100, 500):
        R = PC.comparer(B[["t0", "t1", "r", "cout", "mae", "unite"]], 25, depart=dep)
        dire("\n### depart %d, levier 25 (optimiste)" % dep)
        dire(R.drop(columns=["se_x3"]).round(3).to_string(index=False))
    with open(os.path.join(SCR, "pc_weekend_sortie.txt"), "w") as f:
        f.write("\n".join(out_lignes))
    dire("\nLIGNES : " + repr(lignes))


if __name__ == "__main__":
    main()
