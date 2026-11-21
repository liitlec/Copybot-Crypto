"""Banc AL : pari court a FORT levier autour des annonces US (PRIORITES 21/11, piste 2, point 4a). Compte DEMO, aucun ordre.
Question : un pari court par annonce (emploi NFP et inflation CPI a 8 h 30 NY = bougie 15:30 serveur ; decision FOMC a
14 h NY = 21:00 serveur ; serveur = New York + 7 h, verifie par banc_annonces.py) peut-il donner 10-20 % par mois avec
une securite : stop dur, perte prevue par annonce = X % du compte, pause apres 2 pertes ?
Deja vu (ne pas refaire) : banc_annonces.py (suivre/contrer la bougie 15:30, sans stop ni taille : rien), banc_pc_annonces.py
(ordres des deux cotes : PRESQUE, glissement inconnu), banc_pause_annonces.py (pause du robot : ne tient pas),
banc_calendrier.py (FOMC jour sur indices). NEUF ici : stop/objectif en ATR jour, ENTREE AVANT l'annonce (on traverse
l'annonce avec un stop dur), mise a fort risque par annonce, pause apres 2 pertes, sauts et ruine d'un compte cent.
Calendrier : NFP/CPI 10/2024 -> 11/2026 et FOMC repris de banc_pc_annonces.py (controles dans les bougies la-bas) ;
08/2022 -> 09/2024 reconstruits ici (calendriers BLS publies), controles ici par l'amplitude de la bougie d'annonce.
Helious n'a pas d'historique avant le 14/11/2026 (APIS.md) : inutile pour un banc.
Donnees (mt5/donnees) : or M5 xau_m5_2025a + xau_m5_90k (06/2025 -> 11/2026, jeu principal) ; or M1 xau_m1_90k (3 mois,
CONTROLE de l'ordre intrabougie) ; NAS100 M5 (nas_m5_2025a + 90k), SP500 M5 (sp_m5_90k) ; or H1 xau_h1_50k depuis le
01/08/2022 (approximatif : une bougie H1 contient l'annonce, l'entree « avant » se fait 30 min avant, « apres » a 16:00).
REGLE (par annonce, une seule position) :
- unite : A = ATR jour 20 j (veille, vrai range du jour serveur) ; stop dur a ks x A du prix d'entree ; objectif
  ordre limite a obj x stop (ou aucun : sortie au temps) ; tenue max 60 min apres l'entree (avant 23 h : pas de swap).
- « avant » : entree a l'ouverture de la bougie d'annonce (= cloture 15:25 en M5), sens = derive des 2 h d'avant
  (cloture 15:25 - ouverture 13:30) ; « suite » = dans le sens de la derive, « contre » = a l'oppose.
- « apres » : entree a l'ouverture de 15:35 (M5/M1 ; 16:00 en H1), sens = mouvement de la bougie d'annonce (cloture
  15:30-15:34 - cloture 15:25) ; suite / contre.
- couts : achat a l'ask (prix + sp de la bougie), vente au bid ; spread d'entree « apres » = max des sp des bougies
  d'annonce (15:30, 15:35) ; stop d'une vente declenche quand haut + sp touche ; stop saute => sortie a l'ouverture ;
  stop touche dans les 10 premieres minutes de l'annonce : glissement EN PLUS d'1 sp de la bougie (pessimiste).
  Ordre dans une bougie : stop avant objectif (pessimiste) ; la convention optimiste est donnee pour une ligne.
- taille : lot = X % du solde / stop (perte prevue au stop = X %), plafond de marge 1:500 (marge <= 50 % des fonds).
  Compte cent (ruine) : lot arrondi au pas de 0,01 once (or) ; indices en lot continu (approximation).
- pause : apres 2 pertes de suite, les 2 annonces suivantes ne sont pas jouees (puis compteur remis a zero).
GRILLE FIXEE D'AVANCE (rien d'ajoute ensuite), N = 72 par jeu :
  mode {avant-suite, avant-contre, apres-suite, apres-contre} x stop ks {0,1 ; 0,2} x objectif {1R, 2R, temps}
  x risque X {2 %, 5 %, 10 %}. Memes 72 sur chaque jeu (or M5, or H1, NAS M5, SP M5).
MESURES (par variante et jeu) : gain median par mois (% du compte, compose), % de mois positifs, pire baisse (courbe par
annonce, perte latente au pire point de la position comprise), annonces jouees/mois ; SAUTS = perte >= 10 % du compte
en une annonce : nombre, un tous les N mois, taille mediane et pire, mois de gain median effaces ; RUINE compte cent
100 / 500 EUR (1,16 $/EUR) : (a) rejeu historique depuis chaque debut de mois (12 et 24 mois, or H1 ; 12 mois or M5),
(b) bootstrap stationnaire d'ANNONCES (blocs moyens 3 annonces ~ 1 mois, 5000 tirages, graine 17), autant d'annonces
par mois que l'historique, 12 et 24 mois ; ruine = solde < 20 % de la mise ou lot minimum impossible ; aussi « finir
sous la mise ».
RIGUEUR : walk-forward M5 6 mois -> 1 mois, H1 12 -> 3 mois ; choix au meilleur gain / pire baisse d'apprentissage
parmi les variantes sans saut > 25 % ; compare a ne rien faire et a bt_or (banc_bt_regulier.simule, 1 R = X % de la
variante choisie) sur les memes mois. White (BR.white, jours x 72 variantes, rendements journaliers % du compte, contre 0).
VERDICT FIXE D'AVANCE (sur l'or, M5 et H1 ; indices rapportes a part) : TIENT = walk-forward hors echantillon > 0 et
> bt_or au meme risque sur M5 ET H1, p corrige < 0,10 sur les deux, ET ruine 24 mois (bootstrap, 500 EUR) < 5 % pour
la variante la plus choisie par le walk-forward M5 (sur les annonces M5 et H1) ; PRESQUE = du bon cote hors
echantillon sur les deux jeux mais p >= 0,10 ou ruine >= 5 % ; sinon NE TIENT PAS. OBJECTIF « 10 %/mois » atteint
seulement si TIENT et gain median mensuel hors echantillon >= 10 % sur M5 et H1.
Controles : M1 contre M5 sur les memes annonces (3 mois) ; amplitude de la bougie d'annonce (>= 2 x l'habituelle) ;
spread de la bougie d'annonce (mediane) ; un trade detaille imprime.
RESULTAT (execution du 21/11/2026, 77 s, 5000 tirages, rien de reduit) : verdict NE TIENT PAS ; objectif 10 %/mois
  non atteint (aucune des 288 lignes jeu x variante n'a un gain median >= 10 %/mois ; meilleur or M5 +1,5 %).
  Controles : bougie d'annonce >= 2 x l'habituelle (or M5 NFP 15/15, CPI 15/16, FOMC 12/12 ; dates reconstruites
  08/2022-09/2024 en H1 65/68). Spread enregistre de la bougie 15:30 / 15:35 : mediane 0,20 / 0,20 $ (general 0,19 $,
  rapport 1,00) : le fichier NE MONTRE PAS l'elargissement reel => couts plutot optimistes.
  Walk-forward : or M5 (12 mois de test) +24,1 % compose, median/mois -2,5 %, 5/12 mois > 0, contre bt_or au meme
  risque +341 % ; or H1 (39 mois) -88,9 %, median -9,7 %, contre bt_or +373 %. White (N = 72 ; 24 geometries x 3
  risques) : or M5 p = 0,099, or H1 p = 0,070, NAS 0,42, SP 0,145 ; meilleure sur les deux jeux d'or :
  avant-contre/s0.1/temps (+0,66 R M5, +0,54 R H1, t 1,4 / 2,1) mais profil de loterie (27-32 % de gagnants, trade
  median -1 R, gain concentre sur quelques FOMC, 1re moitie M5 negative) et non retenue par le walk-forward.
  Variante la plus choisie (or M5) apres-suite/s0.1/1R/10 % : M5 +1,5 %/mois median, 50 % de mois > 0, pire baisse
  -33 %, 11 sauts (1 tous les 1,6 mois, 10,2 % median, 10,4 % pire) ; H1 -0,26 R/annonce (t -3,2), ruine 24 m 500 EUR
  31,5 %. Controle M1 (9 annonces) : identique a M5. Optimiste (objectif avant stop) : +0,32 R contre +0,26 R.
Ecrit donnees/annonces_levier.csv (une ligne par jeu x variante). Usage : python3 banc_annonces_levier.py
"""
import os, time, warnings
warnings.simplefilter("ignore")
import numpy as np, pandas as pd
import banc_bt_regulier as BR

T00 = time.time()
ICI = os.path.dirname(os.path.abspath(__file__))
EUR = 1.16
# ------------------------------------------------------------------ calendrier
NFP_A = ["2022-08-05", "2022-09-02", "2022-10-07", "2022-11-04", "2022-12-02", "2023-01-06", "2023-02-03", "2023-03-10",
         "2023-04-07", "2023-05-05", "2023-06-02", "2023-07-07", "2023-08-04", "2023-09-01", "2023-10-06", "2023-11-03",
         "2023-12-08", "2024-01-05", "2024-02-02", "2024-03-08", "2024-04-05", "2024-05-03", "2024-06-07", "2024-07-05",
         "2024-08-02", "2024-09-06"]
CPI_A = ["2022-08-10", "2022-09-13", "2022-10-13", "2022-11-10", "2022-12-13", "2023-01-12", "2023-02-14", "2023-03-14",
         "2023-04-12", "2023-05-10", "2023-06-13", "2023-07-12", "2023-08-10", "2023-09-13", "2023-10-12", "2023-11-14",
         "2023-12-12", "2024-01-11", "2024-02-13", "2024-03-12", "2024-04-10", "2024-05-15", "2024-06-12", "2024-07-11",
         "2024-08-14", "2024-09-11"]
NFP_B = ["2024-10-04", "2024-11-01", "2024-12-06", "2025-01-10", "2025-02-07", "2025-03-07", "2025-04-04", "2025-05-02",
         "2025-06-06", "2025-07-03", "2025-08-01", "2025-09-05", "2025-11-20", "2025-12-16", "2026-01-09", "2026-02-11",
         "2026-03-06", "2026-04-03", "2026-05-08", "2026-06-05", "2026-07-02", "2026-08-07", "2026-09-04", "2026-10-02",
         "2026-11-06"]          # repris de banc_pc_annonces.py
CPI_B = ["2024-10-10", "2024-11-13", "2024-12-11", "2025-01-15", "2025-02-12", "2025-03-12", "2025-04-10", "2025-05-13",
         "2025-06-11", "2025-07-15", "2025-08-12", "2025-09-11", "2025-10-24", "2025-12-18", "2026-01-13", "2026-02-13",
         "2026-03-11", "2026-04-10", "2026-05-12", "2026-06-10", "2026-07-14", "2026-08-12", "2026-09-11", "2026-10-14",
         "2026-11-10"]
FOMC = [d for d in pd.read_csv(os.path.join(ICI, "donnees", "fomc.csv")).annonce if "2022-08-01" <= d <= "2026-11-17"]
EV = sorted([(pd.Timestamp(d + " 15:30"), "NFP") for d in NFP_A + NFP_B] + [(pd.Timestamp(d + " 15:30"), "CPI") for d in CPI_A + CPI_B]
            + [(pd.Timestamp(d + " 21:00"), "FOMC") for d in FOMC])

MODES = ("avant-suite", "avant-contre", "apres-suite", "apres-contre")
KS = (0.1, 0.2); OBJ = (1.0, 2.0, None); RISQ = (0.02, 0.05, 0.10)
GEO = [(m, k, o) for m in MODES for k in KS for o in OBJ]                          # 24 geometries
VAR = [(g, x) for g in GEO for x in RISQ]                                           # 72 variantes
nomg = lambda g: "%s/s%.1f/%s" % (g[0], g[1], "temps" if g[2] is None else "%gR" % g[2])
nomv = lambda v: "%s/%d%%" % (nomg(v[0]), round(v[1] * 100))
NV = len(VAR)


# ------------------------------------------------------------------ donnees
def charge(*ids, depuis=None):
    ds = [BR.charge(i) for i in ids]
    d = ds[-1]
    for b in reversed(ds[:-1]):
        d = pd.concat([b[b.heure < d.heure.iloc[0]], d])
    d = d.drop_duplicates("heure").sort_values("heure").reset_index(drop=True)
    if depuis:
        d = d[d.heure >= pd.Timestamp(depuis).timestamp()].reset_index(drop=True)
    return d


def atr_jour(d):
    jour = d.heure.values // 86400
    j = pd.DataFrame({"jour": jour, "h": d.haut.values, "l": d.bas.values, "c": d.cloture.values}).groupby("jour").agg(
        h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    return tr.rolling(20).mean().shift(1)            # serie indexee par jour serveur (entier)


# ------------------------------------------------------------------ un trade
def trade(d, pas, T, g, ATR, optimiste=False):
    """Rend dict(R, mae, S, px, sens, t_e, t_s, sp_a) ou None. Prix bid ; ask = bid + sp. Pas en minutes."""
    mode, ks, obj = g
    t = d._t; o, h, l, c, sp = d._o, d._h, d._l, d._c, d._sp
    P = pd.Timedelta(minutes=pas)
    Ta = T.floor("%dmin" % pas)
    ja = t.searchsorted(Ta)
    if ja >= len(t) or t[ja] != Ta or ja < 30 or t[ja - 1] != Ta - P:
        return None
    A = ATR.get(int(Ta.timestamp()) // 86400, np.nan)
    if not A > 0:
        return None
    fen = T + pd.Timedelta(minutes=10)                      # fenetre « a l'annonce »
    ann = [q for q in range(ja, min(ja + 12, len(t))) if t[q] < fen]
    sp_a = max(sp[q] for q in ann)
    if mode.startswith("avant"):
        jr = t.searchsorted(Ta - pd.Timedelta(hours=2))
        if jr >= ja or (Ta - t[jr]) > pd.Timedelta(hours=2, minutes=30):
            return None
        der = c[ja - 1] - o[jr]; je = ja; spe = sp[ja - 1]
    else:
        Te = (T + pd.Timedelta(minutes=5)).ceil("%dmin" % pas)
        je = t.searchsorted(Te)
        if je >= len(t) or t[je] != Te:
            return None
        der = c[je - 1] - c[ja - 1]; spe = max(sp_a, sp[je])
    if der == 0:
        return None
    s = int(np.sign(der)) * (1 if mode.endswith("suite") else -1)
    S = ks * A; tg = None if obj is None else obj * S
    fin = t[je] + pd.Timedelta(minutes=60)
    jf = je
    while jf + 1 < len(t) and t[jf + 1] < fin and t[jf + 1].date() == t[je].date():
        jf += 1
    if s > 0:
        E = o[je] + spe; stop = E - S
    else:
        E = o[je]; stop = E + S
    pire = 0.0; sortie = None
    for q in range(je, jf + 1):
        spq = max(sp[q], spe) if q in ann else sp[q]
        glis = 0.0 if optimiste else (spq if t[q] < fen else 0.0)
        if s > 0:
            touche_s, touche_o = l[q] <= stop, (tg is not None and h[q] >= E + tg)
            adv = E - l[q]
        else:
            touche_s, touche_o = h[q] + spq >= stop, (tg is not None and l[q] + spq <= E - tg)
            adv = h[q] + spq - E
        if touche_o and (optimiste or not touche_s):
            sortie = (q, tg); pire = max(pire, min(adv, S) if touche_s else adv); break
        if touche_s:
            if s > 0:
                px = min(stop, o[q]) if q > je else stop
                g_ = px - glis - E
            else:
                px = max(stop, o[q] + spq) if q > je else stop
                g_ = E - px - glis
            sortie = (q, g_); pire = max(pire, -g_); break
        pire = max(pire, adv)
    if sortie is None:
        g_ = (c[jf] - E) if s > 0 else (E - c[jf] - sp[jf])
        sortie = (jf, g_)
    q, g_ = sortie
    return dict(R=g_ / S, mae=max(pire, -g_, 0) / S, S=S, px=c[ja - 1], sens=s, t_e=t[je], t_s=t[q], E=E, stop=stop, sp_a=sp_a)


def trades(d, pas, ATR, optimiste=False, evs=EV):
    d._t = pd.DatetimeIndex(pd.to_datetime(d.heure.values, unit="s"))
    d._o, d._h, d._l, d._c, d._sp = (d[x].values.astype(float) for x in ("ouverture", "haut", "bas", "cloture", "sp"))
    ATR = ATR.to_dict()
    rows = []
    for T, ty in evs:
        if T < d._t[0] or T > d._t[-1]:
            continue
        for gi, g in enumerate(GEO):
            x = trade(d, pas, T, g, ATR, optimiste)
            if x is not None:
                x.update(T=T, type=ty, gi=gi); rows.append(x)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ le compte (vectorise sur des tirages)
def compte(R, MAE, S, PX, risque, idx, eq0=1.0, arrondi=False):
    """idx : (B, n) indices d'annonces. Rend r (B,n) rendement par annonce (0 si non joue), bas (B,n) creux latent
    relatif au solde avant, eq (B,n+1), ruine (B,)."""
    B, n = idx.shape
    eq = np.full(B, float(eq0)); EQ = np.empty((B, n + 1)); EQ[:, 0] = eq
    r = np.zeros((B, n)); bas = np.zeros((B, n))
    serie = np.zeros(B, int); saute = np.zeros(B, int); ruine = np.zeros(B, bool)
    for k in range(n):
        i = idx[:, k]
        joue = (~ruine) & (saute == 0)
        lot = risque * eq / S[i]
        cap = 250.0 * eq / PX[i]
        lot = np.minimum(lot, cap)
        if arrondi:
            lot = np.floor(lot / 0.01 + 1e-9) * 0.01
            impossible = joue & (lot <= 0)
            ruine |= impossible; joue &= ~impossible
        pnl = np.where(joue, lot * R[i] * S[i], 0.0)
        bas[:, k] = np.where(joue, -lot * MAE[i] * S[i] / eq, 0.0)
        r[:, k] = pnl / eq
        eq = eq + pnl
        perte = joue & (pnl < 0); gain = joue & (pnl >= 0)
        saute = np.where(joue, saute, np.maximum(saute - 1, 0))
        serie = np.where(perte, serie + 1, np.where(gain, 0, serie))
        stop2 = serie >= 2
        saute = np.where(stop2, 2, saute); serie = np.where(stop2, 0, serie)
        ruine |= eq < 0.2 * eq0
        EQ[:, k + 1] = eq
    return r, bas, EQ, ruine


def pire_baisse(r, bas):
    eq = np.cumprod(1 + r); av = np.concatenate([[1.0], eq[:-1]])
    pic = np.maximum.accumulate(np.concatenate([[1.0], eq]))[:-1]
    low = np.minimum(av * (1 + bas), eq)
    return float((low / pic - 1).min()) if len(r) else 0.0


def mesures(TRg, x, mois_tous):
    """TRg : trades d'une geometrie (tries). Rend dict de mesures (compte continu) + serie r par annonce."""
    n = len(TRg)
    r, bas, _, _ = compte(TRg.R.values, TRg.mae.values, TRg.S.values, TRg.px.values, x, np.arange(n)[None])
    r, bas = r[0], bas[0]
    mo = TRg["T"].dt.to_period("M").values
    rm = pd.Series(np.log1p(r)).groupby(mo).sum().reindex(mois_tous).fillna(0)
    rm = np.expm1(rm)
    med = rm.median()
    sauts = -r[r <= -0.10]
    nmo = len(mois_tous)
    return dict(gain_med_mois=med * 100, mois_pos=(rm > 0).mean() * 100, gain_total=(np.prod(1 + r) - 1) * 100,
                pire_baisse=pire_baisse(r, bas) * 100, annonces_mois=(r != 0).sum() / nmo,
                sauts=len(sauts), saut_tous_n_mois=nmo / len(sauts) if len(sauts) else np.inf,
                saut_med=np.median(sauts) * 100 if len(sauts) else 0.0, saut_pire=sauts.max() * 100 if len(sauts) else 0.0,
                mois_effaces=(np.median(sauts) / med if med > 0 else np.inf) if len(sauts) else 0.0), r, bas


rng = np.random.default_rng(17)


def boot_idx(n, m, B=5000, b=3.0):
    """Bootstrap stationnaire : B chemins de m annonces tirees dans n."""
    out = np.empty((B, m), int)
    for k in range(B):
        neuf = rng.random(m) < 1 / b; neuf[0] = True
        bl = np.cumsum(neuf) - 1; deb = np.flatnonzero(neuf)
        out[k] = (rng.integers(n, size=len(deb))[bl] + np.arange(m) - deb[bl]) % n
    return out


def ruines(TRg, x, par_mois, arrondi=True):
    """Bootstrap 12/24 mois, comptes 100 et 500 EUR : (ruine, sous la mise) en %."""
    out = {}
    n = len(TRg)
    for H in (12, 24):
        idx = boot_idx(n, max(1, int(round(par_mois * H))))
        for e0 in (100, 500):
            _, _, EQ, ru = compte(TRg.R.values, TRg.mae.values, TRg.S.values, TRg.px.values, x, idx, e0 * EUR, arrondi)
            out["ruine%d_%d" % (H, e0)] = ru.mean() * 100
            out["sous%d_%d" % (H, e0)] = ((EQ[:, -1] < e0 * EUR) | ru).mean() * 100
    return out


def rejeu(TRg, x, H, e0, arrondi=True):
    """Rejeu historique depuis chaque debut de mois : (fenetres, % ruine, % sous la mise)."""
    mo = TRg["T"].dt.to_period("M")
    M = mo.unique(); res = []
    for m0 in M:
        if m0 + H - 1 > M[-1]:
            break
        sel = np.flatnonzero((mo >= m0) & (mo <= m0 + H - 1))
        _, _, EQ, ru = compte(TRg.R.values, TRg.mae.values, TRg.S.values, TRg.px.values, x, sel[None], e0 * EUR, arrondi)
        res.append((ru[0], EQ[0, -1] < e0 * EUR or ru[0]))
    if not res:
        return 0, np.nan, np.nan
    a = np.array(res)
    return len(a), a[:, 0].mean() * 100, a[:, 1].mean() * 100


# ------------------------------------------------------------------ un jeu complet
def jeu(nom, d, pas, ATR, app, test, arrondi, d_bt=None, bt_kw=None, verbose=True):
    TR = trades(d, pas, ATR).sort_values(["T", "gi"]).reset_index(drop=True)
    t0, t1 = pd.to_datetime(d.heure.iloc[[0, -1]], unit="s")
    mois_tous = pd.period_range(t0.to_period("M"), t1.to_period("M"), freq="M")
    jours = pd.bdate_range(t0.floor("D"), t1.floor("D"))
    lignes, RS, DM = [], {}, np.zeros((len(jours), NV))
    for vi, (g, x) in enumerate(VAR):
        gi = GEO.index(g)
        TRg = TR[TR.gi == gi].reset_index(drop=True)
        m, r, bas = mesures(TRg, x, mois_tous)
        par_mois = len(TRg) / len(mois_tous)
        m.update(ruines(TRg, x, par_mois, arrondi))
        for H in (12, 24):
            for e0 in (100, 500):
                nf, pr, ps = rejeu(TRg, x, H, e0, arrondi)
                m["hist_ruine%d_%d" % (H, e0)] = pr; m["hist_sous%d_%d" % (H, e0)] = ps; m["hist_fen%d" % H] = nf
        m.update(jeu=nom, variante=nomv((g, x)), mode=g[0], stop_atr=g[1], objectif="temps" if g[2] is None else "%gR" % g[2],
                 risque=x * 100, annonces=len(TRg), R_moyen=TRg.R.mean(), t_R=BR.tst(TRg.R))
        lignes.append(m)
        RS[vi] = (TRg, r, bas)
        dj = pd.Series(r, index=TRg["T"].dt.floor("D")).groupby(level=0).sum().reindex(jours).fillna(0)
        DM[:, vi] = dj.values * 100
    kb, pw = BR.white(DM)
    # ---- walk-forward
    MO = mois_tous; fen = []
    i = app
    while i + test <= len(MO):
        fen.append((MO[i - app], MO[i - 1], MO[i:i + test])); i += test
    bt = BR.simule(d_bt if d_bt is not None else d, **(bt_kw or {}))
    bt["mo"] = bt.jour.dt.to_period("M")
    oos, oos_bt, choix = [], [], []
    for a, b, tm in fen:
        best, bs = None, -np.inf
        for vi, (g, x) in enumerate(VAR):
            TRg, r, bas = RS[vi]
            mo = TRg["T"].dt.to_period("M")
            s = ((mo >= a) & (mo <= b)).values
            if not s.any() or (r[s] <= -0.25).any():
                continue
            gn = np.prod(1 + r[s]) - 1; pb = -pire_baisse(r[s], bas[s])
            sc = gn / pb if pb > 0 else (np.inf if gn > 0 else 0.0)
            if sc > bs:
                best, bs = vi, sc
        if best is None:
            for m_ in tm:
                oos.append((m_, 0.0)); oos_bt.append((m_, 0.0))
            choix.append("rien"); continue
        TRg, r, bas = RS[best]; x = VAR[best][1]
        mo = TRg["T"].dt.to_period("M")
        choix.append(nomv(VAR[best]))
        for m_ in tm:
            s = (mo == m_).values
            oos.append((m_, np.prod(1 + r[s]) - 1))
            gb = bt.g[bt.mo == m_].values
            oos_bt.append((m_, np.prod(1 + x * gb) - 1))
    O = pd.Series(dict(oos)); OB = pd.Series(dict(oos_bt))
    res = dict(nom=nom, TR=TR, L=pd.DataFrame(lignes), white=(nomv(VAR[kb]), pw), O=O, OB=OB, choix=pd.Series(choix),
               RS=RS, mois=mois_tous, jours=len(jours))
    if verbose:
        tot, totb = np.prod(1 + O) - 1, np.prod(1 + OB) - 1
        fq = res["choix"].value_counts()
        print("\n=== %s : %s -> %s, %d annonces (%d mois), N = %d, White : meilleure %s, p corrige = %.3f"
              % (nom, t0.date(), t1.date(), TR["T"].nunique(), len(mois_tous), NV, nomv(VAR[kb]), pw))
        print("  walk-forward %d mois de test (%s -> %s) : total %+.1f %% (compose), median/mois %+.1f %%, mois>0 %d/%d ; "
              "bt_or meme risque %+.1f %% (median %+.1f %%) ; choix le plus frequent %s (%d/%d)"
              % (len(O), O.index[0], O.index[-1], tot * 100, O.median() * 100, (O > 0).sum(), len(O), totb * 100,
                 OB.median() * 100, fq.index[0], fq.iloc[0], len(fen)))
    return res


def montre(L, titre, n=8):
    print(titre)
    print("  %-32s %6s %5s %7s %6s %4s %6s %6s %6s %5s | MC ruine 12/24 m 100E   500E   | sous mise 24m 100/500" % (
        "variante", "R moy", "t", "med/m%", "m>0%", "saut", "1/Nm", "med%", "pire%", "baiss"))
    for _, z in L.head(n).iterrows():
        print("  %-32s %+6.3f %+5.1f %+7.1f %6.0f %4d %6.1f %6.1f %6.1f %5.0f | %5.1f/%5.1f  %5.1f/%5.1f | %5.1f/%5.1f" % (
            z.variante, z.R_moyen, z.t_R, z.gain_med_mois, z.mois_pos, z.sauts, z.saut_tous_n_mois, z.saut_med, z.saut_pire,
            z.pire_baisse, z.ruine12_100, z.ruine24_100, z.ruine12_500, z.ruine24_500, z.sous24_100, z.sous24_500))


def main():
    print("Banc annonces a fort levier ; %d annonces au calendrier (NFP %d, CPI %d, FOMC %d) ; N = %d variantes par jeu"
          % (len(EV), len(NFP_A + NFP_B), len(CPI_A + CPI_B), len(FOMC), NV))
    d5 = charge("xau_m5_2025a", "xau_m5_90k")
    A5 = atr_jour(d5)
    dh = charge("xau_h1_50k", depuis="2022-08-01")
    Ah = atr_jour(dh)
    # ---- controle du calendrier et du spread a l'annonce
    for nom, d, pas in (("or M5", d5, 5), ("or H1", dh, 60)):
        t = pd.DatetimeIndex(pd.to_datetime(d.heure.values, unit="s")); amp = (d.haut - d.bas).values
        rows = []
        for T, ty in EV:
            Ta = T.floor("%dmin" % pas); j = t.searchsorted(Ta)
            if j < 30 or j >= len(t) or t[j] != Ta:
                continue
            rows.append((ty, T, amp[j] / np.median(amp[j - 24:j]), d.sp.values[j] / np.median(d.sp.values[j - 24:j]),
                         d.sp.values[j], d.sp.values[min(j + 1, len(t) - 1)]))
        C = pd.DataFrame(rows, columns=["type", "T", "rap", "rsp", "sp0", "sp1"])
        print("Controle %s : bougie d'annonce >= 2 x l'amplitude mediane des 2 h d'avant : %s" % (nom, " ; ".join(
            "%s %d/%d" % (ty, (C[C.type == ty].rap >= 2).sum(), (C.type == ty).sum()) for ty in ("NFP", "CPI", "FOMC"))))
        if pas == 60:
            a = C[C["T"] < "2024-10-01"]
            print("  dates reconstruites 08/2022-09/2024 (H1) : %d/%d >= 2 x ; sous 1,5 x : %s" % (
                (a.rap >= 2).sum(), len(a), ", ".join("%s %s (%.1f)" % (z.type, z["T"].date(), z.rap) for _, z in a[a.rap < 1.5].iterrows()) or "aucune"))
        else:
            print("  spread (sp) de la bougie 15:30 / 15:35 (NFP+CPI) : mediane %.2f / %.2f $ ; FOMC 21:00 : %.2f $ ; "
                  "mediane generale %.2f $ ; rapport bougie d'annonce / 2 h d'avant : mediane %.2f, max %.1f"
                  % (C[C.type != "FOMC"].sp0.median(), C[C.type != "FOMC"].sp1.median(), C[C.type == "FOMC"].sp0.median(),
                     d.sp.median(), C.rsp.median(), C.rsp.max()))
    R = {}
    R["or M5"] = jeu("or M5", d5, 5, A5, 6, 1, True)
    R["or H1"] = jeu("or H1", dh, 60, Ah, 12, 3, True,
                     bt_kw=dict(span=48, heures={(2, 0), (7, 0), (11, 0), (14, 0), (15, 0)}, debut=60))
    dn = charge("nas_m5_2025a", "nas_m5_90k"); ds = charge("sp_m5_90k")
    R["NAS M5"] = jeu("NAS M5", dn, 5, atr_jour(dn), 6, 1, False)
    R["SP M5"] = jeu("SP M5", ds, 5, atr_jour(ds), 6, 1, False)
    L = pd.concat([r["L"] for r in R.values()], ignore_index=True)
    cols = ["jeu", "variante", "mode", "stop_atr", "objectif", "risque", "annonces", "R_moyen", "t_R"] + [c for c in L.columns if c not in (
        "jeu", "variante", "mode", "stop_atr", "objectif", "risque", "annonces", "R_moyen", "t_R")]
    L[cols].round(4).to_csv(os.path.join(ICI, "donnees", "annonces_levier.csv"), index=False)
    # ---- tableaux
    for k in R:
        X = R[k]["L"]
        montre(X[X.risque == 5].sort_values("gain_med_mois", ascending=False), "\n%s : meilleures geometries a 5 %% (gain median/mois)" % k, 6)
    # geometrie la plus choisie par le walk-forward M5
    vchoix = R["or M5"]["choix"].value_counts().index[0]
    print("\nVariante la plus choisie par le walk-forward or M5 : %s" % vchoix)
    for k in R:
        X = R[k]["L"]
        montre(X[X.variante == vchoix], "  sur %s :" % k, 1)
    g0 = vchoix.rsplit("/", 1)[0]
    for k in ("or M5", "or H1"):
        X = R[k]["L"]
        montre(X[X.variante.str.startswith(g0 + "/")], "  %s, meme geometrie a 2/5/10 %% :" % k, 3)
        h = X[X.variante == vchoix].iloc[0]
        print("    rejeu historique (%d fenetres 12 m, %d fen. 24 m) : ruine 12 m 100/500 E %.0f/%.0f %%, 24 m %.0f/%.0f %% ; sous la mise 24 m %.0f/%.0f %%"
              % (h.hist_fen12, h.hist_fen24, h.hist_ruine12_100, h.hist_ruine12_500, h.hist_ruine24_100, h.hist_ruine24_500,
                 h.hist_sous24_100, h.hist_sous24_500))
    # meilleures toutes variantes (or M5), et risque 10 %
    X = R["or M5"]["L"]
    montre(X.sort_values("gain_med_mois", ascending=False), "\nor M5 : 8 meilleures variantes (tous risques) au gain median/mois", 8)
    # ---- moyennes par mode (avantage brut, en R)
    print("\nR moyen par annonce selon le mode (moyenne des 6 geometries ; t de la meilleure geometrie) :")
    for k in R:
        X = R[k]["L"]; X = X[X.risque == 5]
        print("  %-7s " % k + " ; ".join("%s %+.3f (t max %+.1f)" % (m, X[X["mode"] == m].R_moyen.mean(), X[X["mode"] == m].t_R.max()) for m in MODES))
    # ---- convention optimiste (or M5), meme variante
    gv = GEO[[nomg(g) for g in GEO].index(g0)]
    Top = trades(d5, 5, A5, optimiste=True)
    Tp = R["or M5"]["TR"]
    gi = GEO.index(gv)
    print("\nConvention optimiste (objectif avant stop, pas de glissement en plus), or M5, %s : R moyen %+.3f contre %+.3f pessimiste"
          % (g0, Top[Top.gi == gi].R.mean(), Tp[Tp.gi == gi].R.mean()))
    print("  toutes geometries : R moyen optimiste %+.3f contre %+.3f" % (Top.R.mean(), Tp.R.mean()))
    # ---- controle M1 (3 mois)
    d1 = BR.charge("xau_m1_90k")
    T1 = trades(d1, 1, A5)
    deb = pd.to_datetime(d1.heure.iloc[0], unit="s")
    T5 = Tp[Tp["T"] >= deb]
    J = T1.merge(T5, on=["T", "gi"], suffixes=("_m1", "_m5"))
    print("\nControle M1 (%s -> fin, %d annonces) : R moyen M1 %+.3f contre M5 %+.3f (memes annonces, 24 geometries) ; "
          "correlation %.2f ; meme sens %.0f %% ; %s : M1 %+.3f / M5 %+.3f"
          % (deb.date(), J["T"].nunique(), J.R_m1.mean(), J.R_m5.mean(), np.corrcoef(J.R_m1, J.R_m5)[0, 1],
             (J.sens_m1 == J.sens_m5).mean() * 100, g0, J[J.gi == gi].R_m1.mean(), J[J.gi == gi].R_m5.mean()))
    # ---- verdict
    def cote(k):
        O, OB = R[k]["O"], R[k]["OB"]
        return np.prod(1 + O) - 1, np.prod(1 + OB) - 1, R[k]["white"][1], O.median()
    m5, h1 = cote("or M5"), cote("or H1")
    ru = [R[k]["L"].set_index("variante").loc[vchoix, "ruine24_500"] for k in ("or M5", "or H1")]
    bon = all(c[0] > 0 and c[0] > c[1] for c in (m5, h1))
    p_ok = all(c[2] < 0.10 for c in (m5, h1))
    v = "TIENT" if bon and p_ok and max(ru) < 5 else ("PRESQUE" if bon else "NE TIENT PAS")
    print("\nVERDICT (fixe d'avance) : %s. Walk-forward M5 %+.1f %% (bt_or %+.1f %%, median/mois %+.1f %%), H1 %+.1f %% "
          "(bt_or %+.1f %%, median/mois %+.1f %%) ; p corrige White M5 %.3f, H1 %.3f (N = %d) ; ruine 24 m 500 E de %s : M5 %.1f %%, H1 %.1f %%"
          % (v, m5[0] * 100, m5[1] * 100, m5[3] * 100, h1[0] * 100, h1[1] * 100, h1[3] * 100, m5[2], h1[2], NV, vchoix, ru[0], ru[1]))
    print("Objectif 10 %%/mois : %s" % ("atteint" if v == "TIENT" and min(m5[3], h1[3]) >= 0.10 else "non atteint"))
    # ---- un trade detaille (controle)
    x = Tp[(Tp.gi == gi)].iloc[-1]
    print("\nControle : %s, %s %s, sens %+d, entree %s a %.2f, stop %.2f (S = %.2f $), sortie %s, R = %+.3f, sp annonce %.2f"
          % (g0, x.type, x["T"], x.sens, x.t_e, x.E, x.stop, x.S, x.t_s, x.R, x.sp_a))
    print("Duree %.0f s ; ecrit donnees/annonces_levier.csv (%d lignes)" % (time.time() - T00, len(L)))


if __name__ == "__main__":
    main()
