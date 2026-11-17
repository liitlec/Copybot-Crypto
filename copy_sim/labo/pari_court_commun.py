"""Outil commun du lot « pari court » (PRIORITES 17/11 20 h 10) : chance de x2, x3, x5, x10 en 1 jour, 1 semaine, 1 mois.
Entree : un tableau de trades (une ligne par position) avec les colonnes
  t0, t1  : debut et fin (pd.Timestamp, heure serveur ou UTC, la meme partout) ;
  r       : rendement du notionnel APRES couts (fraction ; 0.003 = +30 bp) ;
  cout    : couts compris dans r (fraction), pour fabriquer la reference sans avantage ;
  mae     : pire excursion contre la position pendant la tenue (fraction >= 0) ;
  unite   : notionnel en $ d'UN lot minimum du courtier au prix d'aujourd'hui (la taille la plus petite possible) ;
  groupe  : (facultatif) identifiant d'un panier : les positions d'un meme panier sont dimensionnees ensemble.
Simulation sur FENETRES HISTORIQUES REELLES (par defaut une fenetre commence a chaque jour ou un signal apparait, a
l'heure du premier signal : la poche s'engage quand le montage se presente ; option « jours » : chaque jour a 0 h ; les trades qui commencent dans la
fenetre sont joues dans l'ordre du temps) : rien n'est melange, l'ordre et les series de pertes sont ceux du marche.
Mise : chaque position recoit n = max(1, plancher(L x compte / unite)) lots minimum, au compte connu a son debut
(« compose » ; c'est « tout remiser apres un gain ») ; variante « fixe » : n calcule sur le compte de DEPART.
Gain compte a la SORTIE de chaque position ; la mise ne voit que les sorties passees (corrige le 17/11 : la 1re version
comptait le gain a l'entree, ce qui donnait un faux avantage aux positions qui se chevauchent). Liquidation : si
n x unite x mae (plus le risque des positions deja ouvertes) atteint le compte, la position emporte le compte. Ruine = compte < 20 % du
depart : la poche s'arrete. Les objectifs sont atteints au premier passage du compte (apres une sortie).
Trois versions du meme montage : « mesure » (r tel quel), « avantage / 2 » (r - moyenne / 2) et « reference sans
avantage » (r - moyenne - cout moyen : meme volatilite, meme mise, espérance = - couts). Un montage n'est retenu que
s'il bat NETTEMENT la reference a avantage / 2 (ecart sur la chance de x3 > 2 erreurs-types des fenetres
independantes)."""
import numpy as np, pandas as pd

HORIZONS = {"1 jour": pd.Timedelta(days=1), "1 semaine": pd.Timedelta(days=7), "1 mois": pd.Timedelta(days=30)}
PALIERS = (2, 3, 5, 10)


def versions(T):
    m, c = T.r.mean(), T.cout.mean()
    return {"mesure": T, "avantage / 2": T.assign(r=T.r - m / 2), "sans avantage": T.assign(r=T.r - m - c)}


def une_fenetre(t0, t1, r, mae, unite, grp, L, depart, mode, max_lots=50):
    """Trades de la fenetre, tries par t0. Le gain d'une position est compte a sa SORTIE (t1) ; la mise d'une position
    ne voit que les sorties d'AVANT son debut (pas de regard en avant entre positions qui se chevauchent).
    Liquidation : si n x unite x mae de la position (plus celles deja ouvertes) atteint le compte a son debut, la
    position est perdue avec tout le compte restant."""
    E = depart; haut = depart; ruine = False
    taille, ouverts = {}, []          # ouverts : [t1, gain en $, perte max en $]
    def solder(jusqua):
        nonlocal E, haut, ruine
        ouverts.sort(key=lambda x: x[0])
        while ouverts and (jusqua is None or ouverts[0][0] <= jusqua):
            _, g, _ = ouverts.pop(0)
            E = max(0.0, E + g)
            haut = max(haut, E)
            if E < 0.2 * depart:
                ruine = True
                return
    for i in range(len(r)):
        solder(t0[i])
        if ruine:
            break
        base = E if mode == "compose" else depart
        g = grp[i]
        if g not in taille:
            taille[g] = max(1, min(max_lots, int(L * base / unite[i])))
        n = taille[g]
        risque = n * unite[i] * mae[i] + sum(x[2] for x in ouverts)
        gain = -E if risque >= E else n * unite[i] * r[i]
        ouverts.append([t1[i], gain, n * unite[i] * mae[i]])
    if not ruine:
        solder(None)
    return E, haut, ruine


def evaluer(T, L, depart=100.0, mode="compose", horizons=HORIZONS, pas_jours=1, debuts="signaux"):
    """Rend un DataFrame : horizon, fenetres, independantes, ruine, x2, x3, x5, x10, esperance (compte final moyen / depart - 1)."""
    T = T.sort_values("t0").reset_index(drop=True)
    if "groupe" not in T:
        T = T.assign(groupe=np.arange(len(T)))
    t0 = T.t0.values; t1 = T.t1.values; r = T.r.values; mae = T.mae.values; un = T.unite.values; gp = T.groupe.values
    debut, fin = T.t0.min().normalize(), T.t0.max()
    out = []
    for hz, d in horizons.items():
        if debuts == "signaux":       # la poche s'engage au premier signal : une fenetre par jour ou un trade commence
            starts = pd.DatetimeIndex(sorted(set(T.t0.dt.normalize()))); starts = starts[starts <= fin - d + pd.Timedelta(days=1)]
            starts = [max(s, T.t0[T.t0 >= s].min()) for s in starts]
        else:                          # « jours » : une fenetre chaque jour, signal ou pas
            starts = pd.date_range(debut, fin - d, freq="%dD" % pas_jours)
        res = []
        for s in starts:
            a, b = np.searchsorted(t0, np.datetime64(s)), np.searchsorted(t0, np.datetime64(s + d))
            if b <= a:
                res.append((depart, depart, False)); continue
            res.append(une_fenetre(t0[a:b], t1[a:b], r[a:b], mae[a:b], un[a:b], gp[a:b], L, depart, mode))
        if not res:
            continue
        E = np.array([x[0] for x in res]); H = np.array([x[1] for x in res]); R = np.array([x[2] for x in res])
        indep = max(1, min(len(res), int((fin - debut) / d)))
        ligne = dict(horizon=hz, fenetres=len(res), independantes=indep, ruine=R.mean(), esperance=E.mean() / depart - 1)
        for k in PALIERS:
            ligne["x%d" % k] = (H >= k * depart).mean()
        ligne["se_x3"] = np.sqrt(max(ligne["x3"] * (1 - ligne["x3"]), 1e-4) / indep)
        out.append(ligne)
    return pd.DataFrame(out)


def comparer(T, L, depart=100.0, mode="compose", horizons=HORIZONS, debuts="signaux"):
    """Les trois versions cote a cote ; colonne « bat_ref » = chance de x3 (avantage / 2) > reference + 2 erreurs-types."""
    rows = []
    for v, Tv in versions(T).items():
        e = evaluer(Tv, L, depart, mode, horizons, debuts=debuts)
        e.insert(0, "version", v)
        rows.append(e)
    R = pd.concat(rows, ignore_index=True)
    a = R[R.version == "avantage / 2"].set_index("horizon"); z = R[R.version == "sans avantage"].set_index("horizon")
    bat = ((a.x3 - z.x3) > 2 * np.sqrt(a.se_x3 ** 2 + z.se_x3 ** 2)) & (a.esperance > z.esperance)
    R["bat_ref"] = R.horizon.map(bat).where(R.version == "avantage / 2", "")
    return R
