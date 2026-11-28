"""Banc regime, piste 2 (Lot B, PRIORITES 23/11) : mesures TENDANCE / BRUIT -> poids des 6 familles du socle.
Idee : quand le marche « tend » (deplacements efficaces, rendements qui se prolongent), les familles qui suivent
(bt_or_h1, cassure_h1, tendance_sp) devraient gagner et celles qui contrent (retour_h1, rebond_nas) perdre ; quand il
« bruite » (allers-retours autour de la moyenne du jour), l'inverse. repli_ind (achat de creux en tendance de fond)
n'est pas classee : poids 1 toujours. Aucune nouvelle regle de trading, seulement des poids 0..2.

Donnees (rien d'autre) :
  or H1 du courtier (xau_h1_50k, depuis 09/2018 : l'historique avant 2022 sert seulement de passe pour les z et les
  quantiles), index = DEBUT de bougie, heure serveur. Mesures calculees bougie par bougie sur une fenetre glissante
  de bougies, puis on garde la valeur a la DERNIERE bougie du jour serveur D (bougie 23 h -> fermee a minuit).
  Mesures or (signe : + = tendance) :
    er     ratio d'efficacite de Kaufman sur 24 H1 : |c_t - c_t-24| / somme |dc| ;
    hurst  exposant de Hurst glissant (variance agregee) : pente de log ecart-type des sommes de k rendements
           (k = 1, 2, 4, 8, 16, blocs disjoints) contre log k, sur 480 H1 ;
    vr     ratio de variance de Lo-MacKinlay q = 6 sur 240 H1 : Var(somme 6) / (6 Var(1)) - 1 ;
    ac     autocorrelation d'ordre 1 des rendements H1 sur 120 H1 ;
    adx    ADX de Wilder 14 sur H1 ;
    xvw    - (nombre de croisements de la VWAP du jour par la cloture H1 / nombre de bougies du jour) ; VWAP = moyenne
           (haut+bas+cloture)/3 ponderee par volume_ticks depuis le debut du jour serveur (pas de volume reel).
  indices D1 du courtier (SP et NAS, moyenne des deux z) : er 20 j, adx 14, vr q = 5 sur 120 j, ac ordre 1 sur 60 j.
Lissage : EMA de span L jours sur la mesure journaliere. z : (x - moyenne) / ecart-type sur les 500 jours de mesure
precedents INCLUS le jour D lui-meme (min 120) -> que du passe vu de J. Score = moyenne des z disponibles.
Sources : « or » = moyenne des 6 z or ; « ind » = moyenne des 4 z indices ; « tout » = moyenne des 10 ;
« marche » = score or pour les familles or (bt_or_h1, cassure_h1, retour_h1) et score indices pour les familles
indices (tendance_sp, rebond_nas).

Calendrier / decalages (verifies dans le code, commentaires « DECALAGE ») :
  mesure or du jour serveur D = bougies dont le debut est <= D 23 h, toutes fermees au plus tard a minuit = debut de
  D+1 ; mesure indices du jour D = barre D1 datee D, cloturee a la fin du jour serveur D. Les deux sont ensuite
  re-datees a D + 1 jour et propagees (ffill) sur JOURS : le jour J utilise la derniere mesure d'un jour D < J
  (lundi -> vendredi). EMA, z et quantiles sont calcules sur la serie datee D, donc ne voient rien apres D.

Poids (fonction cout -> W ; le cout ne change pas W) :
  continu : t = clip(score, -1, 1) ; tendance (bt_or_h1, cassure_h1, tendance_sp) = 1 + t ; bruit (retour_h1,
            rebond_nas) = 1 - t ; repli_ind = 1.
  bascule q : score > quantile (1-q) des 500 jours precedents (inclus D, min 120) -> tendance 2, bruit 0 ;
            score < quantile q -> tendance 0, bruit 2 ; entre les deux -> tout a 1 ; repli_ind = 1.

GRILLE FIXEE D'AVANCE (ecrite avant tout lancement, N = 30) :
  4 sources {or, ind, tout, marche} x 2 lissages L {5, 20} x 3 regles {continu, bascule q = 0,30, bascule q = 0,20}
  = 24 reglages ;
  + 6 mesures or seules (er, hurst, vr, ac, adx, xvw), L = 5, continu, appliquees a toutes les familles = 6 reglages.
Aucun parametre ne sera change apres avoir vu les resultats ; la periode reservee (>= 05/2026) ne sert a rien regler.
Controle (n'influe sur rien) : correlation, avant 05/2026, entre les mesures or H1 du jour et les memes mesures sur les
M5 de mt5/donnees/xau_m5_*.csv.gz (couvrent 06/2025 -> 11/2026 seulement) : les H1 decrivent-ils le meme regime ?

Verdict fixe d'avance = critere du socle (regime_socle.evalue) : au spread reel, walk-forward > 0 en P1 et P2, bat TOUT
et SUIVRE5 en P1 et P2, p corrige (White, 30 reglages + wf) < 0,05, et bat encore les deux references en P1 et P2
au spread double. Sinon « ne tient pas ».
Usage : python3 banc_regime_p2.py"""
import time
import numpy as np, pandas as pd
import regime_socle as S

B = S.B
TEND, BRUIT = ["bt_or_h1", "cassure_h1", "tendance_sp"], ["retour_h1", "rebond_nas"]
FAM_OR, FAM_IND = ["bt_or_h1", "cassure_h1", "retour_h1"], ["tendance_sp", "rebond_nas"]
MES_OR, MES_IND = ["er", "hurst", "vr", "ac", "adx", "xvw"], ["er", "adx", "vr", "ac"]
ZFEN, ZMIN = 500, 120


# ------------------------------------------------------------------------------------------------ mesures
def adx(h, b, c, n=14):
    up, dn = h.diff(), -b.diff()
    pdm = up.where((up > dn) & (up > 0), 0.0); ndm = dn.where((dn > up) & (dn > 0), 0.0)
    tr = pd.concat([h - b, (h - c.shift(1)).abs(), (b - c.shift(1)).abs()], axis=1).max(axis=1)
    a = 1.0 / n
    atr = tr.ewm(alpha=a, adjust=False).mean()
    pdi = 100 * pdm.ewm(alpha=a, adjust=False).mean() / atr
    ndi = 100 * ndm.ewm(alpha=a, adjust=False).mean() / atr
    dx = 100 * (pdi - ndi).abs() / (pdi + ndi).replace(0, np.nan)
    return dx.ewm(alpha=a, adjust=False).mean()


def er(c, n):
    return (c - c.shift(n)).abs() / c.diff().abs().rolling(n).sum()


def vr(r, q, n):
    rq = r.rolling(q).sum()
    return rq.rolling(n).var() / (q * r.rolling(n).var()) - 1.0


def ac1(r, n):
    return r.rolling(n).corr(r.shift(1))


def hurst_fin(r, idx_fin, n=480, ks=(1, 2, 4, 8, 16)):
    """Hurst (variance agregee) calcule seulement aux positions idx_fin (fenetre des n rendements finissant la)."""
    v = r.values; lk = np.log(ks); out = np.full(len(idx_fin), np.nan)
    for j, i in enumerate(idx_fin):
        if i + 1 < n:
            continue
        w = v[i + 1 - n:i + 1]
        if np.isnan(w).any():
            continue
        sd = [w[len(w) % k:].reshape(-1, k).sum(1).std() for k in ks]
        out[j] = np.polyfit(lk, np.log(sd), 1)[0]
    return out


def mesures_or(coupe=None):
    """DataFrame indexe par jour serveur D (bougies de D, toutes fermees a minuit = debut de D+1).
    coupe : ne garder que les bougies commencant avant cette date (test de fuite)."""
    d, _ = B.charge("xau_h1_50k")
    d = d[~d.index.duplicated()].sort_index()
    if coupe is not None:
        d = d[d.index < coupe]
    c = d["cloture"]; r = np.log(c).diff()
    jour = d.index.floor("D")
    dern = pd.Series(np.arange(len(d)), index=d.index).groupby(jour).max()   # derniere bougie de chaque jour D
    M = pd.DataFrame(index=dern.index)
    M["er"] = er(c, 24).values[dern.values]
    M["vr"] = vr(r, 6, 240).values[dern.values]
    M["ac"] = ac1(r, 120).values[dern.values]
    M["adx"] = adx(d["haut"], d["bas"], c).values[dern.values]
    M["hurst"] = hurst_fin(r, dern.values)
    # croisements de la VWAP du jour (volume_ticks) : uniquement les bougies du jour D
    tp = (d["haut"] + d["bas"] + c) / 3; v = d["volume_ticks"].clip(lower=1)
    vw = (tp * v).groupby(jour).cumsum() / v.groupby(jour).cumsum()
    sg = np.sign(c - vw)
    x = ((sg != sg.groupby(jour).shift(1)) & sg.groupby(jour).shift(1).notna()).astype(float)
    M["xvw"] = -(x.groupby(jour).sum() / x.groupby(jour).count()).reindex(M.index).values
    M = M[M.index.dayofweek < 5]          # les 9 bougies du samedi : jour trop court, ignore
    return M


def mesures_ind():
    """Par indice (SP, NAS) : DataFrame indexe par la date de la barre D1 (cloturee a la fin du jour serveur D)."""
    out = {}
    for k in ("SP", "NAS"):
        o = S.IND[k]; c = o["cloture"]; r = np.log(c).diff()
        out[k] = pd.DataFrame({"er": er(c, 20), "adx": adx(o["haut"], o["bas"], c), "vr": vr(r, 5, 120),
                               "ac": ac1(r, 60)})
    return out


def lisse_z(x, L):
    """EMA L puis z sur les ZFEN mesures precedentes, jour D inclus (aucune valeur apres D)."""
    e = x.ewm(span=L, adjust=False, ignore_na=True).mean() if L > 1 else x
    m = e.rolling(ZFEN, min_periods=ZMIN).mean(); s = e.rolling(ZFEN, min_periods=ZMIN).std()
    return (e - m) / s


def vers_jours(s):
    """DECALAGE : valeur du jour D (connue a minuit = debut de D+1) re-datee D+1, puis propagee sur JOURS.
    Le jour J recoit donc la derniere valeur d'un jour D <= J-1 calendaire (lundi : vendredi)."""
    s = s.dropna().copy(); s.index = s.index + pd.Timedelta(days=1)
    return s.reindex(s.index.union(S.JOURS)).ffill().reindex(S.JOURS)


MO, MI = mesures_or(), mesures_ind()
_SC = {}


def scores(L):
    """Scores journaliers (dates D, non decales) pour le lissage L : or, ind, tout, et z par mesure or."""
    if L in _SC:
        return _SC[L]
    zo = pd.DataFrame({m: lisse_z(MO[m], L) for m in MES_OR})
    zi = {k: pd.DataFrame({m: lisse_z(MI[k][m], L) for m in MES_IND}) for k in MI}
    zi = (zi["SP"] + zi["NAS"]) / 2                   # meme calendrier D1 des deux indices (courtier)
    so, si = zo.mean(1, skipna=True), zi.mean(1, skipna=True)
    tout = pd.concat([zo, zi.add_prefix("i_")], axis=1).sort_index()
    tout = tout.ffill(limit=3)                         # jours ou un des deux marches n'a pas de barre : derniere valeur D' <= D
    st = tout.mean(1, skipna=True)
    _SC[L] = {"or": so, "ind": si, "tout": st, **{"m_" + m: zo[m] for m in MES_OR}}
    return _SC[L]


# ------------------------------------------------------------------------------------------------ poids
def _poids_un(sc, regle):
    """Serie de score (dates D) -> (poids tendance, poids bruit) sur JOURS (decales, connus au debut de J)."""
    if regle == "continu":
        t = vers_jours(sc.clip(-1, 1)).fillna(0.0)
        return 1 + t, 1 - t
    q = regle
    hi = sc.rolling(ZFEN, min_periods=ZMIN).quantile(1 - q); lo = sc.rolling(ZFEN, min_periods=ZMIN).quantile(q)
    etat = pd.Series(np.where(sc > hi, 1.0, np.where(sc < lo, -1.0, 0.0)), index=sc.index).where(hi.notna())
    e = vers_jours(etat).fillna(0.0)
    return 1 + e, 1 - e


def fabrique(source, L, regle):
    def f(cout):
        W = pd.DataFrame(1.0, index=S.JOURS, columns=S.FAMS)
        sc = scores(L)
        if source == "marche":
            for src, fams in (("or", FAM_OR), ("ind", FAM_IND)):
                pt, pb = _poids_un(sc[src], regle)
                for fm in fams:
                    W[fm] = pt if fm in TEND else pb
        else:
            pt, pb = _poids_un(sc[source], regle)
            W[TEND] = np.repeat(pt.values[:, None], len(TEND), 1); W[BRUIT] = np.repeat(pb.values[:, None], len(BRUIT), 1)
        return W.clip(0, 2)
    return f


GRILLE = {}
for src in ("or", "ind", "tout", "marche"):
    for L in (5, 20):
        for regle, nr in (("continu", "cont"), (0.30, "q30"), (0.20, "q20")):
            GRILLE["%s L%d %s" % (src, L, nr)] = fabrique(src, L, regle)
for m in MES_OR:
    GRILLE["seule %s L5 cont" % m] = fabrique("m_" + m, 5, "continu")
assert len(GRILLE) == 30


# ------------------------------------------------------------------------------------------------ controle M5
def controle_m5():
    """Correlation (jours D < 05/2026) entre mesures or du jour sur H1 et sur M5 (memes definitions, fenetres x12)."""
    a, _ = B.charge("xau_m5_2025a"); b, _ = B.charge("xau_m5_90k")        # labo/mt5/donnees
    d = pd.concat([a[a.index < b.index[0]], b]).sort_index(); d = d[~d.index.duplicated()]
    d = d[d.index < S.RES]                              # rien de la periode reservee
    c = d["cloture"]; r = np.log(c).diff(); jour = d.index.floor("D")
    dern = pd.Series(np.arange(len(d)), index=d.index).groupby(jour).max()
    M5 = pd.DataFrame(index=dern.index)
    M5["er"] = er(c, 288).values[dern.values]
    M5["ac"] = ac1(r, 1440).values[dern.values]
    M5["vr"] = vr(r, 72, 2880).values[dern.values]
    k = M5.index.intersection(MO.index)
    print("  controle M5 (%d jours, %s -> %s, avant RES) : correlation H1 / M5 du meme jour : %s" % (
        len(k), k.min().date() if len(k) else "-", k.max().date() if len(k) else "-",
        ", ".join("%s %.2f" % (m, MO.loc[k, m].corr(M5.loc[k, m])) for m in M5.columns)))


if __name__ == "__main__":
    t0 = time.time()
    # test de fuite : les z or du dernier jour D < J doivent etre identiques si l'on supprime toutes les bougies >= J
    for J in ("2023-06-14", "2024-03-04", "2025-10-20"):
        J = pd.Timestamp(J); Mc = mesures_or(J)
        za = pd.DataFrame({m: lisse_z(MO[m], 20) for m in MES_OR}); zc = pd.DataFrame({m: lisse_z(Mc[m], 20) for m in MES_OR})
        dmax = (za.loc[:J - pd.Timedelta("1s")].iloc[-1] - zc.iloc[-1]).abs().max()
        assert zc.index[-1] < J and dmax < 1e-9, (J, dmax)
    print("Test de fuite (troncature des H1 a J) : OK")
    print("Mesures or : %s -> %s (%d jours) ; indices SP : %s -> %s" % (MO.index[0].date(), MO.index[-1].date(),
          len(MO), MI["SP"].index[0].date(), MI["SP"].index[-1].date()))
    print("Correlation des z or (L5) :")
    print(pd.DataFrame({m: lisse_z(MO[m], 5) for m in MES_OR}).loc["2022-08":"2026-04"].corr().round(2).to_string())
    res = S.evalue("p2 mesures", GRILLE)
    S.ligne_csv("p2 mesures", res)
    print("  Choix mois par mois (spread reel) : " + " ".join("%s:%s" % (m, c) for m, c in res[1.0]["choix"]
                                                             if m < "2026-05"))
    try:
        controle_m5()
    except Exception as e:                              # le controle n'influe sur rien
        print("  controle M5 impossible :", e)
    print("%.0f s" % (time.time() - t0))
