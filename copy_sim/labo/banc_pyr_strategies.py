"""Banc PS : renforts sur nos autres strategies (PRIORITES 23/11, Lot A ; compte DEMO / labo, aucun ordre).
Regle : pour chaque strategie on rejoue ses entrees et sa sortie d'origine (origine), puis deux versions avec renforts,
memes entrees (une version ne sort jamais plus tard que l'origine, donc une position a la fois reste vraie) :
  P1 « renforts gagnants » (regle figee du 23/11, partie renforts / stop) : 0,5 x le volume initial quand une bougie
     CLOTURE a >= +1 R puis >= +1,5 R (depuis la 1re entree) et que l'OUVERTURE suivante est encore au-dela (ajout a
     cette ouverture) ; a la 1re cloture >= +1 R stop au prix d'entree moyen ; ensuite stop = max(stop, meilleure
     cloture - 1,5 R) (symetrique en vente), jamais en recul. La sortie d'origine (temps, signal, objectif, stop
     d'origine) reste valable en plus. Pas de stop initial ajoute quand la strategie n'en a pas au banc.
  P2 pyramide bt_or : +1 position de meme taille quand une cloture atteint chaque palier de 0,25 ATR jour (ATR 20 j,
     connu la veille) dans le sens du gain (ajout a la cloture si elle n'a pas depasse le palier de plus d'un demi-pas,
     comme banc_bt_regulier.simule), 3 positions au plus ; sortie d'origine.
Unite R (= stop d'origine) : repli_ind 2 x ATR 20 j (stop du banc et du robot) ; rebond_nas / rebond_sp / fomc_dax :
  pas de stop au banc -> stop dur du robot 3 x ATR 20 j ; elan_m15 / cassure_m15 / exces_m5 : pas de stop au banc ->
  stop dur du robot (4 x amplitude moyenne des 48 dernieres bougies, au moins 3 $) ; retour_court_ar : son stop court
  (extreme des 2 dernieres bougies +/- 0,5 $, au moins 3 $) ; tendance 50/200 S&P : pas de stop -> 1 ATR 20 j ;
  toujours acheteur or : son stop 0,667 ATR jour (recul depuis le meilleur prix).
Strategies et donnees (celles de leurs bancs) :
  repli_ind : D1 du courtier NAS100+, SP500+, DJ30+, GER40+, US2000+ ; RSI 2 j < 10 et cloture > moyenne 200 j ->
    achat a l'ouverture suivante, stop 2 ATR touche dans la bougie, sortie a l'ouverture qui suit une cloture > moyenne
    5 j ou apres 10 j ; couts 2 bp + (taux 3 mois + 2,5 %)/360 par nuit (= banc_blockrange_ohlc.trades).
  rebond_nas / rebond_sp : D1 du courtier ; amplitude/cloture veille > 1,5 x mediane 20 j -> sens contraire, ouverture
    -> cloture du meme jour ; 2 bp. Trade d'une seule bougie D1 : P1 et P2 n'ont aucune cloture intermediaire, donc
    = origine PAR CONSTRUCTION (approximation D1, dite).
  fomc_dax : DAX Yahoo jour (banc_calendrier), achat cloture J-2 jours ouvres, sortie cloture J ; 2 bp + financement.
  tendance 50/200 S&P : D1 du courtier SP500+, achat a l'ouverture apres une cloture ou moyenne 50 > moyenne 200,
    sortie a l'ouverture apres une cloture ou elle repasse dessous ; 2 bp + financement.
  elan_m15 (sens des 12 dernieres bougies), cassure_m15 (sortie de la fourchette des 48 bougies precedentes),
    exces_m5 (bougie > 3 ecarts-types des 100 precedentes, on la suit) : or M15 xau_m15_50k / M5 xau_m5_2025a+90k,
    decision a la cloture, entree a l'ouverture suivante, sortie a la cloture 12 (M15) / 3 (M5) bougies apres,
    une position a la fois, spread reel (banc_or.trades), pause au calme v11 (veille sous la mediane 60 j).
  retour_court_ar : or M15, regle « retour » du robot, objectif milieu du range du jour, stop court, sortie a 3 h.
  toujours acheteur or : or H1 depuis 08/2022, mecanique bt_or toujours achat (banc_decompose_bt e1 = origine, e3 = P2
    exactement), heures BJ.H_H1, ATR jour 20.
  Bougies D1 / H1 : renforts et stops sur ces bougies (approximation, dite).
Mesures (gains en bp du notionnel initial ; gain compte au jour de sortie) : trades, R/trade, total, pire baisse
  (courbe journaliere), mois positifs, total A RISQUE EGAL = total x (pire baisse de l'origine / pire baisse de la
  version), par moitie (D1 : 01/2022 -> 06/2024 / 07/2024 -> 11/2026 ; or : periode disponible coupee en deux).
Walk-forward : choix origine / P1 / P2 sur l'apprentissage (12 mois / test 3 mois en D1-H1 ; 6 / 1 en M5-M15) au
  total a risque egal, rejoue (gain du choix x facteur d'apprentissage) contre l'origine sur les memes mois de test.
Essais multiples : N = 20 (10 strategies x 2 versions), White (BR.white) sur la matrice jours (2022+) x 20 des
  differences journalieres version x facteur - origine.
VERDICT FIXE D'AVANCE par strategie : TIENT = une version avec renforts meilleure a risque egal que l'origine sur les
  deux moities ET walk-forward > origine hors echantillon, ET p de White < 0,10 ; sinon NON.
RESULTAT (execution du 23/11/2026, 2 s) : 1 strategie TIENT sur 10, « toujours acheteur » or avec P2 (= bt_or toujours
  achat 3 positions, deja connu : banc_decompose_bt e3) ; toutes les autres NON. Controles : repli_ind origine = banc_
  blockrange_ohlc.trades sur la D1 du courtier (NAS100+ 62 trades +24,9 bp, SP500+ 54 trades +40,4 bp, identiques) ;
  achat_or origine / P2 = banc_decompose_bt e1 / e3 (H1 : +76,17 R / +243,67 R, identiques). White N = 20 : meilleure
  colonne achat_or/P2, p = 0,001 (seule colonne qui gagne nettement). Totaux a risque egal (bp), moitie 1 / moitie 2,
  origine / P1 / P2 : repli_ind 1024/1024/811 | 6093/6093/4303 ; rebond_nas et rebond_sp : P1 = P2 = origine (trade d'une
  bougie D1) ; fomc_dax 1258/1258/798 | 25/25/5 ; elan_m15 1459/1382/716 | 50/81/-339 ; cassure_m15 13/-122/169 |
  1430/1051/-86 ; exces_m5 805/754/746 | 658/686/692 ; retour_court_ar -3852/-4011/-3949 | -2361/-2509/-2481 ; tendance
  50/200 S&P (3 trades seulement) -145/-145/-145 | 3132/49/8597 ; achat_or 3032/2157/3701 | 3702/4206/9349 (WF +10 940
  contre +5 840, P2 choisi 13 fois sur 14). P1 (unite R = stop d'origine, 2-3 ATR en D1) ne se declenche presque jamais
  sur les strategies D1 ; sur l'or intrajour il retire un peu (cassure, elan moitie 1) ou ne change rien (exces).
Ecrit donnees/pyr_strategies.csv. Usage : python3 banc_pyr_strategies.py
"""
import os, time, contextlib, io, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_bt_regulier as BR
    import banc_jumeau as BJ

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
DEBUT, COUPE = pd.Timestamp("2022-01-01"), pd.Timestamp("2024-07-01")
VERS = ("origine", "P1", "P2")
rng = np.random.default_rng(2311)


# ------------------------------------------------------------------ donnees
def barres(ident):
    d = BR.charge(ident)
    d.index = pd.to_datetime(d.heure, unit="s")
    return d


def atr_jour(d, n=20):
    """ATR 20 jours (vrai range) des journees, connu la veille, rendu par bougie."""
    j = d.groupby(d.index.floor("D")).agg(h=("haut", "max"), l=("bas", "min"), c=("cloture", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    return tr.rolling(n).mean().shift(1).reindex(d.index.floor("D")).values


def taux_fin(idx):
    t = pd.read_csv(os.path.join(ICI, "donnees", "irx_jour.csv"), index_col=0, parse_dates=True)["irx"]
    return (t.reindex(t.index.union(idx)).ffill().bfill().reindex(idx).values / 100 + 0.025) / 360


# ------------------------------------------------------------------ moteur d'un trade
def joue(T, v, A):
    """T : dict du trade ; v : version ; A : arrays du marche. Rend (gain fraction, jour de sortie, gain en R, barre)."""
    o, h, l, c, sp, jn, fin = A["o"], A["h"], A["l"], A["c"], A["sp"], A["jn"], A["fin"]
    e, s, R = T["e"], T["s"], T["R"]
    ref = o[e] if T["ouv"] else c[e]
    pe0 = ref + (sp[e] if s > 0 else 0.0)
    pos = [[pe0, 1.0, jn[e]]]
    j0 = e if T["ouv"] else e + 1
    stop0, trail, cible = T.get("stop"), T.get("trail"), T.get("cible")
    pas = 0.25 * T.get("A", np.nan)
    proch = ref + s * pas
    best_c, best_x = ref, ref
    st1, be, arme, nren, attente = None, False, None, 0, False
    X = lambda px, j: px if s > 0 else px + sp[j]     # prix de sortie (cote vendeur) d'un prix « bid »
    sortie = None
    n = len(c)
    for j in range(j0, min(T["xmax"], n - 1) + 1):
        if attente:
            sortie = (X(o[j], j), j); break
        if v == "P1" and arme is not None and j > e:
            if s * (o[j] - (ref + s * arme * R)) >= 0:
                pos.append([o[j] + (sp[j] if s > 0 else 0.0), 0.5, jn[j]]); nren += 1
            arme = None
        st = [x for x in (stop0, st1) if x is not None]
        if st:
            sv = max(st) if s > 0 else min(st)
            if s > 0 and l[j] <= sv:
                sortie = (min(o[j], sv), j); break
            if s < 0 and h[j] + sp[j] >= sv:
                sortie = (max(o[j] + sp[j], sv), j); break
        if trail is not None:
            niv = best_x - s * trail
            if (s > 0 and l[j] <= niv) or (s < 0 and h[j] + sp[j] >= niv):
                sortie = (niv, j); break
            best_x = max(best_x, h[j]) if s > 0 else min(best_x, l[j])
        if cible is not None:
            if (s > 0 and h[j] >= cible) or (s < 0 and l[j] + sp[j] <= cible):
                sortie = (cible, j); break
        if j == T["xmax"] or (T.get("flag") is not None and T["flag"][j] and T["mode"] == "cloture"):
            sortie = (X(c[j], j), j); break
        if T.get("flag") is not None and T["flag"][j]:
            attente = True
            if j == n - 1:
                sortie = (X(c[j], j), j); break
        if v == "P2" and pas > 0:
            while len(pos) < 3 and s * (c[j] - proch) >= 0:
                if s * (c[j] - proch) <= 0.5 * pas:
                    pos.append([c[j] + (sp[j] if s > 0 else 0.0), 1.0, jn[j]])
                proch += s * pas
        if v == "P1":
            best_c = max(best_c, c[j]) if s > 0 else min(best_c, c[j])
            gr = s * (c[j] - ref) / R
            if gr >= 1.0 and not be:
                W = sum(w for _, w, _ in pos)
                st1 = sum(p * w for p, w, _ in pos) / W
                if stop0 is not None:
                    st1 = max(st1, stop0) if s > 0 else min(st1, stop0)
                be = True
            if be:
                nv = best_c - s * 1.5 * R
                st1 = max(st1, nv) if s > 0 else min(st1, nv)
            if nren < 2 and gr >= (1.0, 1.5)[nren]:
                arme = (1.0, 1.5)[nren]
    if sortie is None:
        return None
    px, j = sortie
    brut = sum(w * s * (px - p) for p, w, _ in pos)
    cout = sum(w * (T["frais"] + T["fin"] * (jn[j] - d0)) for p, w, d0 in pos)
    return brut / pe0 - cout, fin[j], brut / R, j


def sequence(cands, faire, A, ecart):
    """Rejoue l'origine dans l'ordre : une position a la fois ; rend la liste des trades (dict) avec leur sortie."""
    out, libre = [], -1
    for i in cands:
        if i < libre:
            continue
        T = faire(i)
        if T is None:
            continue
        r = joue(T, "origine", A)
        if r is None:
            break
        out.append(T); libre = r[3] + ecart
    return out


def arrays(d, fin_nuit=None, sp=True):
    jn = (d.index.normalize() - pd.Timestamp("1970-01-01")).days.values
    return dict(o=d.ouverture.values, h=d.haut.values, l=d.bas.values, c=d.cloture.values,
                sp=d.sp.values if sp else np.zeros(len(d)), jn=jn, fin=d.index.normalize().values)


# ------------------------------------------------------------------ strategies
def rsi2(c):
    x = c.diff()
    u, b = x.clip(lower=0).ewm(alpha=0.5, adjust=False).mean(), (-x).clip(lower=0).ewm(alpha=0.5, adjust=False).mean()
    return 100 * u / (u + b)


def atr20(d):
    tr = pd.concat([d.haut - d.bas, (d.haut - d.cloture.shift()).abs(), (d.bas - d.cloture.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(20).mean()


def strat_repli(ident):
    d = barres(ident); A = arrays(d, sp=False)
    c = d.cloture; r, m200, m5, at = rsi2(c), c.rolling(200).mean(), c.rolling(5).mean(), atr20(d).values
    fin = taux_fin(d.index)
    flag = (c > m5).values
    n = len(d)
    sig = np.flatnonzero(((r < 10) & (c > m200)).values)
    sig = sig[(sig >= 200) & (sig < n - 2)]

    def faire(i):
        e = i + 1
        # sortie a l'ouverture qui suit une cloture > m5, ou a l'ouverture de i+11 (j - i >= 10)
        return dict(e=e, s=1, ouv=True, R=2 * at[i], A=at[i], stop=d.ouverture.values[e] - 2 * at[i], flag=flag_i(i),
                    mode="ouverture", xmax=min(i + 11, n - 1), frais=2e-4, fin=fin[e])

    def flag_i(i):
        f = flag.copy()
        if i + 10 < n:
            f[i + 10] = True
        return f
    return d, A, sequence(sig, faire, A, 1)


def strat_rebond(ident):
    d = barres(ident); A = arrays(d, sp=False)
    amp = (d.haut - d.bas) / d.cloture.shift(1)
    med = amp.shift(1).rolling(20).median()
    m = d.cloture.diff()
    s = np.where(amp > 1.5 * med, -np.sign(m), 0)
    at = atr20(d).values
    n = len(d)
    sig = [i for i in np.flatnonzero(s != 0) if 21 < i < n - 1]
    faire = lambda i: dict(e=i + 1, s=int(s[i]), ouv=True, R=3 * at[i], A=at[i], xmax=i + 1, frais=2e-4, fin=0.0)
    return d, A, sequence(sig, faire, A, 0)


def strat_tendance():
    d = barres("sp_d1_5k"); A = arrays(d, sp=False)
    c = d.cloture; f50, f200 = c.rolling(50).mean(), c.rolling(200).mean()
    hausse = (f50 > f200).values
    at = atr20(d).values; fin = taux_fin(d.index); n = len(d)
    sig = [i for i in np.flatnonzero(hausse) if 200 <= i < n - 1]
    faire = lambda i: dict(e=i + 1, s=1, ouv=True, R=at[i], A=at[i], flag=~hausse, mode="ouverture", xmax=n - 1,
                           frais=2e-4, fin=fin[i + 1])
    return d, A, sequence(sig, faire, A, 1)


def strat_fomc():
    x = pd.read_csv(os.path.join(ICI, "donnees", "cal_dax.csv.gz"), index_col=0, parse_dates=True).dropna()
    x = x[x.index >= "2017-01-01"]
    d = pd.DataFrame({"ouverture": x.open, "haut": x.high, "bas": x.low, "cloture": x.close, "sp": 0.0}, index=x.index)
    A = arrays(d, sp=False)
    at = atr20(d).values; fin = taux_fin(d.index)
    J = pd.to_datetime(pd.read_csv(os.path.join(ICI, "donnees", "fomc.csv")).annonce)
    pos = {t: k for k, t in enumerate(d.index)}
    sig, xj = [], {}
    for j in J:
        e = j - pd.offsets.BDay(2)
        if e in pos and j in pos and pos[e] >= 20:
            sig.append(pos[e]); xj[pos[e]] = pos[j]
    faire = lambda i: dict(e=i, s=1, ouv=False, R=3 * at[i], A=at[i], xmax=xj[i], frais=2e-4, fin=fin[i])
    return d, A, sequence(sorted(sig), faire, A, 0)


def calme_veille(d):
    D = d.groupby(d.index.floor("D")).agg(h=("haut", "max"), b=("bas", "min"), o=("cloture", "first"))
    rg = (D.h - D.b) / D.o
    cv = (rg.shift(1) < rg.shift(1).rolling(60, min_periods=20).median()).fillna(False)
    return cv.reindex(d.index.floor("D")).fillna(False).values


def ecart_robot(d):
    return np.maximum(4 * (d.haut - d.bas).rolling(48).mean().values, 3.0)


def strat_or(nom):
    if nom == "exces_m5":
        a5, b5 = barres("xau_m5_2025a"), barres("xau_m5_90k")
        d = pd.concat([a5, b5[b5.index > a5.index[-1]]])
        r = np.log(d.cloture).diff(); z = r / r.rolling(100).std().shift(1)
        s, h = ((z > 3).astype(float) - (z < -3).astype(float)).values, 3
    else:
        d = barres("xau_m15_50k")
        c = d.cloture
        if nom == "elan_m15":
            lr = np.log(c); s = np.sign(lr - lr.shift(12)).values
        else:
            ha, ba = d.haut.shift(1).rolling(48).max(), d.bas.shift(1).rolling(48).min()
            s = ((c > ha).astype(float) - (c < ba).astype(float)).values
        h = 12
    s = np.nan_to_num(s); s[calme_veille(d)] = 0
    A = arrays(d); at = atr_jour(d); er = ecart_robot(d); n = len(d)
    sig = [i for i in np.flatnonzero(s != 0) if 100 <= i < n - h - 1 and at[i] == at[i]]
    faire = lambda i: dict(e=i + 1, s=int(s[i]), ouv=True, R=er[i], A=at[i], xmax=i + h, frais=0.0, fin=0.0)
    return d, A, sequence(sig, faire, A, 0)    # B.trades : decision suivante possible a la barre de sortie


def strat_retour():
    d = barres("xau_m15_50k"); A = arrays(d); at = atr_jour(d); n = len(d)
    c, hi, lo, sp, t = d.cloture.values, d.haut.values, d.bas.values, d.sp.values, d.heure.values
    jr = t // 86400
    m20 = pd.Series(c).shift(1).rolling(20).mean().values; e20 = pd.Series(c).shift(1).rolling(20).std().values
    hj = pd.Series(hi).groupby(jr).cummax().values; lj = pd.Series(lo).groupby(jr).cummin().values
    debj = np.r_[0, np.flatnonzero(jr[1:] != jr[:-1]) + 1]
    deb = np.zeros(n, int)
    for k, a in enumerate(debj):
        deb[a:(debj[k + 1] if k + 1 < len(debj) else n)] = a

    def sig_i(i):
        if i < 22:
            return 0
        if e20[i] > 0 and abs(c[i] - m20[i]) > 2.5 * e20[i]:
            return -1 if c[i] > m20[i] else 1
        a = deb[i]
        if i - 1 - a >= 4 and jr[i - 1] == jr[i]:
            hh, ll = hi[a:i - 1].max(), lo[a:i - 1].min()
            if hi[i - 1] > hh and c[i] < hh:
                return -1
            if lo[i - 1] < ll and c[i] > ll:
                return 1
        return 0

    S = np.array([sig_i(i) for i in range(n)])
    sig = [i for i in np.flatnonzero(S != 0) if 48 <= i < n - 13 and at[i] == at[i]]

    def faire(i):
        s, e = int(S[i]), i + 1
        mini = max(3.0, 3 * sp[e])
        bid, ask = d.ouverture.values[e], d.ouverture.values[e] + sp[e]
        mil = (hj[i] + lj[i]) / 2
        cible = mil if (s > 0 and mil > ask + sp[e]) or (s < 0 and mil < bid - sp[e]) else None
        ext = hi[i - 1:i + 1].max() + 0.5 if s < 0 else lo[i - 1:i + 1].min() - 0.5
        stop = min(ext, bid - mini) if s > 0 else max(ext, ask + mini)
        R = abs((ask if s > 0 else bid) - stop)
        return dict(e=e, s=s, ouv=True, R=R, A=at[i], stop=stop, cible=cible, xmax=i + 12, frais=0.0, fin=0.0)
    return d, A, sequence(sig, faire, A, 0)


def strat_achat():
    d = barres("xau_h1_50k"); d = d[d.index >= "2022-08-01"]
    A = arrays(d); at = atr_jour(d); n = len(d)
    hh, mm = d.index.hour.values, d.index.minute.values
    sig = [i for i in range(60, n - 1) if (hh[i], mm[i]) in BJ.H_H1 and at[i] == at[i] and at[i] > 0]
    faire = lambda i: dict(e=i, s=1, ouv=False, R=BR.STOP * at[i], A=at[i], trail=BR.STOP * at[i], xmax=n,
                           frais=0.0, fin=0.0)
    return d, A, sequence(sig, faire, A, 0)


# ------------------------------------------------------------------ mesures
def creux(x):
    cs = np.r_[0, np.cumsum(x)]
    return (cs - np.maximum.accumulate(cs)).min()


def courbe(res, jours):
    s = pd.Series([r[0] * 1e4 for r in res], pd.to_datetime([r[1] for r in res])).groupby(level=0).sum()
    return s.reindex(jours).fillna(0.0)


def mesure(res, x, a, b):
    k = [r for r in res if a <= pd.Timestamp(r[1]) < b]
    y = x[(x.index >= a) & (x.index < b)]
    mo = y.groupby(y.index.to_period("M")).sum()
    return dict(trades=len(k), R_trade=np.mean([r[2] for r in k]) if k else np.nan, bp_trade=np.mean([r[0] for r in k]) * 1e4 if k else np.nan,
                total_bp=y.sum(), pire_baisse_bp=creux(y.values), mois_pos=int((mo > 0).sum()), mois=len(mo))


def wf(X, app, test):
    """X : DataFrame jours x versions (bp). Choix au total a risque egal sur app mois, rejoue test mois."""
    mois = X.index.to_period("M"); um = mois.unique()
    tot_wf = tot_o = 0.0; choix = []
    for k in range(app, len(um), test):
        A_ = X[(mois >= um[k - app]) & (mois < um[k])]; B_ = X[(mois >= um[k]) & (mois <= um[min(k + test - 1, len(um) - 1)])]
        c0 = creux(A_["origine"].values)
        sc = {}
        for v in VERS:
            cv = creux(A_[v].values)
            f = c0 / cv if cv < 0 and c0 < 0 else 1.0
            sc[v] = (A_[v].sum() * f, f)
        v = max(VERS, key=lambda q: sc[q][0])
        choix.append(v); tot_wf += B_[v].sum() * sc[v][1]; tot_o += B_["origine"].sum()
    return tot_wf, tot_o, choix


# ------------------------------------------------------------------ programme
if __name__ == "__main__":
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    STRATS = {}
    t1 = time.time()
    rep = {}
    for ident in ("nas_d1_5k", "sp_d1_5k", "dj_d1_5k", "ger_d1_5k", "us2000_d1_5k"):
        rep[ident] = strat_repli(ident)
    STRATS["repli_ind"] = ("D1", list(rep.values()))
    STRATS["rebond_nas"] = ("D1", [strat_rebond("nas_d1_5k")])
    STRATS["rebond_sp"] = ("D1", [strat_rebond("sp_d1_5k")])
    STRATS["fomc_dax"] = ("D1", [strat_fomc()])
    STRATS["elan_m15"] = ("M15", [strat_or("elan_m15")])
    STRATS["cassure_m15"] = ("M15", [strat_or("cassure_m15")])
    STRATS["exces_m5"] = ("M5", [strat_or("exces_m5")])
    STRATS["retour_court_ar"] = ("M15", [strat_retour()])
    STRATS["tendance_50_200_sp"] = ("D1", [strat_tendance()])
    STRATS["achat_or"] = ("H1", [strat_achat()])
    print("entrees construites en %.0f s" % (time.time() - t1))

    # ---- controle 1 : repli_ind origine contre banc_blockrange_ohlc.trades (meme fonction du banc, D1 du courtier)
    import banc_blockrange_ohlc as BRO
    for ident in ("nas_d1_5k", "sp_d1_5k"):
        d = rep[ident][0]
        dd = pd.DataFrame({"open": d.ouverture.values, "high": d.haut.values, "low": d.bas.values, "close": d.cloture.values},
                          index=d.index.normalize())
        tx = pd.Series((taux_fin(dd.index) * 360 - 0.025) * 100, dd.index)
        tb = BRO.trades(dd, tx, 10)
        mine = [joue(T, "origine", rep[ident][1]) for T in rep[ident][2]]
        print("Controle repli %s : banc_blockrange_ohlc %d trades %+.1f bp/trade ; ce banc (origine) %d trades %+.1f bp/trade"
              % (ident, len(tb), tb.net.mean() * 1e4, len(mine), np.mean([m[0] for m in mine]) * 1e4))

    jours = pd.date_range(DEBUT, "2026-11-30", freq="D")
    rows, DIFF, WF = [], {}, {}
    for nom, (per, jeux) in STRATS.items():
        t1 = time.time()
        R_, X = {}, {}
        for v in VERS:
            res = []
            for d, A, Ts in jeux:
                for T in Ts:
                    r = joue(T, v, A)
                    if r is not None:
                        res.append(r)
            R_[v] = res
            X[v] = courbe(res, jours)
        X = pd.DataFrame(X)
        # periode utile : du 1er trade 2022+ a la fin
        prem = min(pd.Timestamp(r[1]) for r in R_["origine"] if pd.Timestamp(r[1]) >= DEBUT)
        X = X[X.index >= prem.normalize()]
        if per == "D1":
            mi = COUPE
        elif nom == "achat_or":
            mi = pd.Timestamp("2024-10-01")
        else:
            mi = X.index[0] + (X.index[-1] - X.index[0]) / 2
            mi = mi.normalize()
        fen = (("tout", X.index[0], X.index[-1] + pd.Timedelta(days=1)), ("moitie1", X.index[0], mi),
               ("moitie2", mi, X.index[-1] + pd.Timedelta(days=1)))
        cre = {}
        for nf, a, b in fen:
            c0 = creux(X["origine"][(X.index >= a) & (X.index < b)].values)
            for v in VERS:
                m = mesure(R_[v], X[v], a, b)
                f = c0 / m["pire_baisse_bp"] if m["pire_baisse_bp"] < 0 else np.nan
                m.update(strategie=nom, donnee=per, version=v, fenetre=nf, debut=a.date(), fin=(b - pd.Timedelta(days=1)).date(),
                         facteur=f, total_risque_egal=f * m["total_bp"] if f == f else m["total_bp"])
                rows.append(m)
                if nf == "tout":
                    cre[v] = f
        for v in ("P1", "P2"):
            f = cre[v] if cre[v] == cre[v] else 1.0
            DIFF["%s/%s" % (nom, v)] = (X[v] * f - X["origine"]).reindex(jours[jours >= DEBUT]).fillna(0.0)
        app, test = (12, 3) if per in ("D1", "H1") else (6, 1)
        WF[nom] = wf(X, app, test)
        print("%-20s %s : %s en %.0f s" % (nom, per, ", ".join("%s %d tr" % (v, len(R_[v])) for v in VERS), time.time() - t1))

    T = pd.DataFrame(rows)
    # ---- essais multiples
    M = pd.DataFrame(DIFF)
    imax, p_white = BR.white(M.values)
    print("\nWhite (N = %d colonnes, %d jours) : meilleure colonne %s, moyenne %+.2f bp/jour, p = %.3f" % (
        M.shape[1], len(M), M.columns[imax], M.values.mean(0)[imax], p_white))

    # ---- tableau et verdict
    print("\n=== Totaux a risque egal (bp du notionnel initial ; facteur = pire baisse origine / pire baisse version)")
    cols = ["strategie", "version", "fenetre", "trades", "R_trade", "bp_trade", "total_bp", "pire_baisse_bp", "mois_pos", "mois",
            "facteur", "total_risque_egal"]
    print(T[cols].round(2).to_string(index=False))
    print("\n=== Synthese, verdict (TIENT = version meilleure a risque egal sur les 2 moities ET walk-forward > origine ET p < 0,10)")
    syn = []
    for nom in STRATS:
        g = T[T.strategie == nom].set_index(["version", "fenetre"])["total_risque_egal"]
        twf, to, ch = WF[nom]
        ok = [v for v in ("P1", "P2") if g[v, "moitie1"] > g["origine", "moitie1"] + 1e-9 and g[v, "moitie2"] > g["origine", "moitie2"] + 1e-9]
        tient = bool(ok) and twf > to + 1e-9 and p_white < 0.10
        cnt = {v: ch.count(v) for v in VERS}
        print("%-20s M1 o/P1/P2 %+8.0f %+8.0f %+8.0f | M2 %+8.0f %+8.0f %+8.0f | WF %+8.0f contre origine %+8.0f (choix %s) | %s%s" % (
            nom, g["origine", "moitie1"], g["P1", "moitie1"], g["P2", "moitie1"], g["origine", "moitie2"], g["P1", "moitie2"],
            g["P2", "moitie2"], twf, to, cnt, "TIENT " if tient else "NON", ("(deux moities : %s)" % ",".join(ok)) if ok else ""))
        syn.append(dict(strategie=nom, version="synthese", fenetre="walk-forward", total_bp=twf, total_risque_egal=to,
                        choix=str(cnt), verdict="TIENT" if tient else "NON", versions_2_moities=",".join(ok), p_white=p_white))
    T = pd.concat([T, pd.DataFrame(syn)], ignore_index=True)
    T.to_csv(os.path.join(ICI, "donnees", "pyr_strategies.csv"), index=False, float_format="%.4f")
    print("\nEcrit donnees/pyr_strategies.csv ; duree %.0f s" % (time.time() - T00))
