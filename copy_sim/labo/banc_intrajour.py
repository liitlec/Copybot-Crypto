"""Banc INTRAJOUR (PRIORITES 17/11 17 h, point 2) : retour apres exces en INTRAJOURNALIER sur les indices US.
Plan fixe d'avance (avant tout resultat), N = 552 reglages au total, tous comptes.

Donnees
  - Courtier M5 (prix BID, spread reel de chaque bougie) : NAS100+ (nas_m5_2025a + nas_m5_90k, 06/2025 -> 11/2026),
    SP500+ et DJ30+ (sp_m5_90k, dj_m5_90k, 08/2025 -> 11/2026). Horloge serveur = heure de New York + 7 h toute
    l'annee (UTC+2/+3, change d'heure avec les Etats-Unis ; verifie ici : pic de volume a 16 h 30 serveur, y compris
    pendant les semaines de decalage Europe / Etats-Unis). Tout est raisonne en heure de NEW YORK (ouverture 9 h 30 =
    15 h 30 Paris, sauf semaines de decalage ou c'est 14 h 30 Paris ; cloture 16 h = 22 h Paris).
  - Courtier H4 NAS100+ (nas_h4_20k) : ATTENTION, avant le 11/07/2022 ce fichier ne contient que des bougies JOUR
    (une seule bougie a 0 h serveur) ; seule la partie vraiment H4 (07/2022 -> 11/2026, ~4,3 ans) est gardee ;
    spread de la bougie, plancher 0,8 point.
  - Yahoo 1 h des indices au comptant ^NDX ^GSPC ^DJI ^RUT (~3 ans, bougies 9 h 30, 10 h 30, ..., 15 h 30 NY), cache
    donnees/yahoo_1h_indices.csv ; cout = spread median du courtier (NAS 0,8 / SP 0,36 / DJ 1,15 / US2000 0,32 point,
    rapporte au prix). L'ouverture 9 h 30 d'un indice au comptant est figee (actions pas encore cotees) : Yahoo
    n'est donc PAS utilise pour l'ecart d'ouverture ni pour la nuit (familles B et C-nuit), seulement pour A et C-derniere.
  - Taux 3 mois US (^IRX, Yahoo, cache donnees/irx_jour.csv) pour le financement de nuit des CFD : achat (r + 3 %)/360,
    vente max(2,6 % - r, 0)/360 par nuit serveur (week-end = 3 nuits).
Couts : achat au prix vendeur (bid + spread de la bougie d'entree), vente au bid, et inversement a la sortie ;
glissement 0,5 bp par aller-retour, + 1 bp si sortie par stop ; sortie a l'objectif = ordre limite au niveau.

Familles et grille (« contre » = position inverse du mouvement, deux sens ; « achat » = achats seuls)
  A-H1 (courtier M5 x 3 indices, Yahoo 1 h x 4 indices) : bougies d'une heure alignees sur l'ouverture, debut 10 h 30,
     11 h 30, ..., 14 h 30 NY (la 1re heure, dominee par l'ecart d'ouverture, est exclue). Mesure = |rendement|
     (cloture/ouverture - 1) ou amplitude (haut - bas)/ouverture ; signal si mesure > k x mediane de la meme heure sur
     les 20 seances precedentes, k = 2 / 3 / 4 ; entree a l'ouverture de l'heure suivante ; sortie apres 1 h, apres 4 h
     (au plus 16 h) ou a la cloture 16 h ; sens contre / achat (apres une baisse). Une position a la fois.
     2 x 3 x 3 x 2 = 36 par marche -> 7 marches = 252.
  A-H4 (NAS100+ H4 07/2022-11/2026) : meme signal sur les bougies H4 du courtier (mediane du meme creneau, 20 jours) ;
     entree bougie suivante ; tenue 1, 2 ou 6 bougies (4 h, 8 h, ~1 jour) ; contre / achat. 36.
  B ecart d'ouverture (courtier M5 x 3) : ecart = ouverture 9 h 30 / cloture de la veille a 16 h (bougie 15 h 55) - 1 ;
     z = ecart / moyenne quadratique des 20 ecarts precedents ; si |z| > k (1 / 1,5 / 2) : pari sur le comblement
     (sens inverse de l'ecart), entree a l'ouverture 9 h 30, sortie au comblement (cloture de la veille touchee) ou a
     heure fixe 10 h 30 / 12 h / 16 h ; stop aucun ou symetrique (distance = l'ecart) ; contre / achat (ecart en
     baisse). 3 x 3 x 2 x 2 = 36 par marche -> 108.
  C fin de seance (courtier M5 x 3 ; Yahoo x 4 pour la seule fenetre « derniere ») : mouvement M = 9 h 30 -> 15 h NY
     (15 h 30 -> 21 h Paris ; Yahoo : 9 h 30 -> 15 h 30) ; z = M / moyenne quadratique des 20 seances precedentes ;
     si |z| > k (1 / 1,5 / 2) : fenetre « derniere » (15 h -> 16 h), « nuit » (16 h -> 9 h 30 le lendemain, nuit
     contre jour), « fin+nuit » (15 h -> 9 h 30 le lendemain) ; sens contre / suite / achat apres baisse / achat apres
     hausse. Courtier 3 x 3 x 4 = 36 par marche -> 108 ; Yahoo 3 x 4 = 12 par marche -> 48.
  Total : 252 + 36 + 108 + 156 = 552 reglages, en 7 + 1 + 3 + 7 = 18 lignes (famille x marche).
  Neuf par rapport a banc_saisons.py (fenetres d'heures et nuit/jour SANS condition) et banc_vol_retour.py (journalier) :
  ici tout est CONDITIONNE a un exces intrajournalier.

Methode
  - Gain par seance (somme des trades entres ce jour-la, en fraction du notionnel apres couts).
  - Walk-forward glissant par ligne : apprentissage 6 mois -> test 1 mois (H4 : 6 trimestres -> 1 trimestre ; prevu 8, ramene a 6
    quand on a vu que le H4 ne commence qu'en 07/2022, avant tout resultat H4 seul),
    reglage = meilleur t (gain par seance) sur l'apprentissage, sans aucune donnee future.
  - Temoin « acheter aux memes heures au hasard » : chaque trade hors echantillon est rejoue, meme heure d'entree, meme
    duree (ou meme sortie « ouverture du lendemain »), meme sens, sur les AUTRES seances du meme mois ; esperance du
    temoin = moyenne de ces rejeux ; p_hasard = part de 4000 tirages (une seance au hasard par trade) dont le total
    >= celui de la regle. t-temoin = t de (gain - esperance du temoin) par seance.
  - Correction : p corrige = Bonferroni sur les 18 lignes du p unilateral du t hors echantillon ; reality check de White
    (version studentisee, bootstrap stationnaire, blocs moyens 5 seances, 2000 tirages) sur chaque bloc de donnees
    (courtier M5 : 324 reglages ; H4 : 36 ; Yahoo : 192), contre zero et contre le temoin.
  - Moities : le hors-echantillon coupe en deux a la date du milieu.
  Verdict (fixe d'avance) : TIENT = HE > 0, p corrige < 0,05, deux moities > 0, bat le temoin (p_hasard < 0,05) ;
  PRESQUE = HE > 0, t >= 1, deux moities > 0, gain > temoin ; sinon NE TIENT PAS.
Sorties : donnees/rebonds_intrajour.csv (trades hors echantillon des lignes TIENT/PRESQUE) et
donnees/rebonds_intrajour_tout.csv (toute la periode au reglage le plus choisi), colonnes regle, marche, entree,
sortie (dates de New York), sens, r. Usage : python3 banc_intrajour.py  (~2-3 min)"""
import os, json, time, urllib.request, warnings
from statistics import NormalDist
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")

ICI = os.path.dirname(os.path.abspath(__file__))
DON, OUT = os.path.join(ICI, "mt5", "donnees"), os.path.join(ICI, "donnees")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
SLIP, SLIP_STOP = 0.5e-4, 1.0e-4
rng = np.random.default_rng(1711)
N_LIGNES = 18


# ------------------------------------------------------------------ donnees
def yahoo_json(tk, q):
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%s?%s" % (urllib.request.quote(tk), q)
    for essai in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            return json.load(urllib.request.urlopen(req, timeout=30))["chart"]["result"][0]
        except Exception as e:
            err = e; time.sleep(2 * (essai + 1))
    raise RuntimeError("echec %s : %s" % (tk, err))


def yahoo_1h():
    f = os.path.join(OUT, "yahoo_1h_indices.csv")
    if not os.path.exists(f):
        L = []
        for tk in ("^NDX", "^GSPC", "^DJI", "^RUT"):
            r = yahoo_json(tk, "interval=1h&range=730d")
            q = r["indicators"]["quote"][0]
            d = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")})
            d["ny"] = pd.to_datetime(r["timestamp"], unit="s", utc=True).tz_convert("America/New_York").tz_localize(None)
            d["tk"] = tk; L.append(d.dropna()); time.sleep(0.5)
        d = pd.concat(L)
        d = d[d.ny.dt.normalize() < d.ny.max().normalize()]          # seance du jour (incomplete) exclue
        d.to_csv(f, index=False, float_format="%.6g")
    return pd.read_csv(f, parse_dates=["ny"])


def taux_us():
    f = os.path.join(OUT, "irx_jour.csv")
    if not os.path.exists(f):
        r = yahoo_json("^IRX", "interval=1d&period1=1500000000&period2=%d" % int(time.time()))
        s = pd.Series(r["indicators"]["quote"][0]["close"], index=pd.to_datetime(r["timestamp"], unit="s").normalize())
        s.dropna().rename("irx").to_csv(f, float_format="%.4f")
    s = pd.read_csv(f, index_col=0, parse_dates=True)["irx"] / 100
    return s[~s.index.duplicated()]


TAUX = taux_us()


class Barres:
    """Bougies triees ; t = minutes depuis 1970 en heure de New York (naive)."""
    def __init__(self, nom, ny, o, h, l, c, sp, pas):
        k = np.argsort(ny.values); ny = ny.values[k]
        t = ny.astype("datetime64[m]").astype(np.int64)
        ok = np.r_[True, np.diff(t) > 0]
        self.nom, self.pas = nom, pas
        self.t = t[ok]
        self.o, self.h, self.l, self.c, self.sp = (np.asarray(v, float)[k][ok] for v in (o, h, l, c, sp))
        self.day, self.mod = self.t // 1440, self.t % 1440
        self.sday = (self.t + 7 * 60) // 1440                     # jour du serveur (bascule a 17 h NY)
        dd = pd.to_datetime(self.day, unit="D")
        self.mois = (dd.year * 12 + dd.month - 1).values
        r = TAUX.reindex(TAUX.index.union(pd.DatetimeIndex(np.unique(dd)))).ffill().bfill()
        self.taux = r.reindex(dd).values

    def at(self, T):
        """indice de la bougie qui commence exactement a T (minutes), -1 sinon."""
        T = np.asarray(T, np.int64); i = np.searchsorted(self.t, T)
        i2 = np.minimum(i, len(self.t) - 1)
        return np.where((i < len(self.t)) & (self.t[i2] == T), i2, -1)

    def last_lt(self, T, mini):
        """derniere bougie qui commence avant T et apres mini (meme seance), -1 sinon."""
        T = np.asarray(T, np.int64); i = np.searchsorted(self.t, T) - 1
        i2 = np.maximum(i, 0)
        return np.where((i >= 0) & (self.t[i2] >= mini), i2, -1)


def barres_courtier(nom, ids, plancher=0.0, debut=None):
    d = pd.concat([pd.read_csv(os.path.join(DON, i + ".csv.gz")) for i in ids]).drop_duplicates("heure")
    if debut:
        d = d[pd.to_datetime(d.heure, unit="s") >= debut]
    ny = pd.to_datetime(d.heure, unit="s") - pd.Timedelta(hours=7)
    pas = int(np.median(np.diff(np.sort(d.heure.values))) // 60)
    return Barres(nom, ny, d.ouverture, d.haut, d.bas, d.cloture, np.maximum(d.spread_points * 0.01, plancher), pas)


def verifie_fuseau(ids):
    d = pd.concat([pd.read_csv(os.path.join(DON, i + ".csv.gz")) for i in ids]).drop_duplicates("heure")
    t = pd.to_datetime(d.heure, unit="s"); d = d[(t.dt.hour >= 13) & (t.dt.hour < 20)]
    t = pd.to_datetime(d.heure, unit="s")
    pic = d.groupby(t.dt.normalize()).apply(lambda x: pd.to_datetime(x.heure.loc[x.volume_ticks.idxmax()], unit="s"))
    dec = pic[(pic.dt.month == 3) & (pic.dt.day >= 9) & (pic.dt.day <= 27)]       # semaines de decalage de mars
    return pic.dt.strftime("%H:%M").value_counts().head(3).to_dict(), dec.dt.strftime("%H:%M").value_counts().head(2).to_dict()


# ------------------------------------------------------------------ evaluation des trades
def financement(B, e, x, s):
    n = (B.sday[x] - B.sday[e]).astype(float)
    r = B.taux[e]
    a = np.where(s > 0, r + 0.03, np.maximum(0.026 - r, 0.0))
    return a * n / 360


def valeur(B, e, x, s, kx, pout=None, stop=None):
    """kx = 0 : sortie a la cloture de x ; 1 : a l'ouverture de x. pout (bid si achat, ask si vente) remplace."""
    e, x, s = np.asarray(e), np.asarray(x), np.asarray(s, float)
    pin = B.o[e] + np.where(s > 0, B.sp[e], 0.0)
    px = np.where(np.asarray(kx) == 1, B.o[x], B.c[x])
    po = px + np.where(s < 0, B.sp[x], 0.0)
    if pout is not None:
        po = np.where(np.isnan(pout), po, pout)
    r = s * (po - pin) / pin - SLIP - financement(B, e, x, s)
    if stop is not None:
        r = r - SLIP_STOP * stop
    return r


class Trades:
    """Trades d'un reglage. spec : (0, duree) sortie cloture de la derniere bougie avant t_e + duree ;
    (1, 0) sortie a l'ouverture 9 h 30 de la seance suivante ; (2, h) sortie a l'ouverture de e + h bougies."""
    def __init__(self, B, e, x, s, kx, spec, r):
        self.B, self.e, self.x, self.s, self.kx, self.spec, self.r = B, e, x, s, kx, spec, r


def suivante_ouverture(B, e):
    """indice de la bougie 9 h 30 de la seance suivante (premier jour > jour de e qui en a une)."""
    o930 = np.where(B.mod == 570)[0]
    j = np.searchsorted(B.day[o930], B.day[e], side="right")
    return np.where(j < len(o930), o930[np.minimum(j, len(o930) - 1)], -1)


def rejeu(T):
    """Pour chaque trade : valeurs des rejeux sur les autres seances du meme mois (meme heure, meme duree, meme sens)."""
    B = T.B; out = []
    jours = pd.Series(np.unique(B.day)); mois_j = pd.to_datetime(jours, unit="D")
    mj = (mois_j.dt.year * 12 + mois_j.dt.month - 1).values
    for k in range(len(T.e)):
        e = T.e[k]; cand = jours.values[(mj == B.mois[e]) & (jours.values != B.day[e])]
        e2 = B.at(cand * 1440 + B.mod[e]); e2 = e2[e2 >= 0]
        if len(e2) == 0:
            out.append(np.array([T.r[k]])); continue
        typ, par = T.spec[k]
        if typ == 0:
            x2 = B.last_lt(B.t[e2] + par, B.t[e2]); kx = 0
        elif typ == 1:
            x2 = suivante_ouverture(B, e2); kx = 1
        else:
            x2 = e2 + par; x2 = np.where(x2 < len(B.t), x2, -1); kx = 1
        ok = x2 >= 0
        if not ok.any():
            out.append(np.array([T.r[k]])); continue
        out.append(valeur(B, e2[ok], x2[ok], np.full(ok.sum(), T.s[k]), kx))
    return out


# ------------------------------------------------------------------ familles
def mediane_prec(v, cle, n=20):
    """mediane des n valeurs precedentes de la meme cle (creneau)."""
    s = pd.Series(v); return s.groupby(np.asarray(cle)).transform(lambda z: z.rolling(n, min_periods=15).median().shift(1)).values


def rms_prec(v, n=20):
    return np.sqrt(pd.Series(v ** 2).rolling(n, min_periods=15).mean().shift(1).values)


def sans_chevauchement(e, x):
    k = np.argsort(e, kind="stable"); garde, fin = [], -1
    for i in k:
        if e[i] > fin:
            garde.append(i); fin = x[i]
    return np.array(garde, int)


def famille_A_h1(B):
    """Bougies d'une heure 10 h 30 ... 14 h 30 NY."""
    L = []
    for S in (630, 690, 750, 810, 870):
        days = np.unique(B.day); i0 = B.at(days * 1440 + S); i1 = B.last_lt(days * 1440 + S + 60, days * 1440 + S + 60 - B.pas)
        e = B.at(days * 1440 + S + 60)
        ok = (i0 >= 0) & (i1 >= 0) & (e >= 0)
        for d, a, b, ee in zip(days[ok], i0[ok], i1[ok], e[ok]):
            L.append((d, S, a, b, ee))
    H = pd.DataFrame(L, columns=["day", "S", "a", "b", "e"]).sort_values(["day", "S"]).reset_index(drop=True)
    hi = np.array([B.h[a:b + 1].max() for a, b in zip(H.a, H.b)]); lo = np.array([B.l[a:b + 1].min() for a, b in zip(H.a, H.b)])
    o, c = B.o[H.a.values], B.c[H.b.values]
    H["ret"] = c / o - 1; H["amp"] = (hi - lo) / o
    H["m_ret"] = mediane_prec(H.ret.abs().values, H.S.values); H["m_amp"] = mediane_prec(H.amp.values, H.S.values)
    cfg = {}
    for mes in ("ret", "amp"):
        x = H.ret.abs().values if mes == "ret" else H.amp.values
        base = H["m_" + mes].values
        for k in (2, 3, 4):
            sig = (x > k * base) & ~np.isnan(base) & (H.ret.values != 0)
            for ten in ("1h", "4h", "seance"):
                Tx = H.day.values * 1440 + {"1h": np.minimum(H.S.values + 120, 960), "4h": np.minimum(H.S.values + 300, 960),
                                            "seance": np.full(len(H), 960)}[ten]
                for sens in ("contre", "achat"):
                    m = sig & ((H.ret.values < 0) if sens == "achat" else True)
                    e = H.e.values[m]; Txm = Tx[m]
                    xx = B.last_lt(Txm, Txm - 60); s = -np.sign(H.ret.values[m])
                    g = xx >= e
                    e, xx, s, Txm = e[g], xx[g], s[g], Txm[g]
                    kk = sans_chevauchement(e, xx); e, xx, s, Txm = e[kk], xx[kk], s[kk], Txm[kk]
                    r = valeur(B, e, xx, s, 0)
                    spec = [(0, int(Txm[i] - B.t[e[i]])) for i in range(len(e))]
                    cfg["A %s k%d %s %s" % (mes, k, ten, sens)] = Trades(B, e, xx, s, np.zeros(len(e)), spec, r)
    return cfg


def famille_A_h4(B):
    v = np.abs(B.c / B.o - 1); amp = (B.h - B.l) / B.o; ret = B.c / B.o - 1
    base = {"ret": mediane_prec(v, B.mod), "amp": mediane_prec(amp, B.mod)}
    n = len(B.t); cfg = {}
    for mes in ("ret", "amp"):
        x = v if mes == "ret" else amp
        for k in (2, 3, 4):
            sig = (x > k * base[mes]) & ~np.isnan(base[mes]) & (ret != 0)
            sig[-8:] = False
            for h in (1, 2, 6):
                for sens in ("contre", "achat"):
                    m = sig & ((ret < 0) if sens == "achat" else True)
                    i = np.where(m)[0]; e = i + 1; xx = e + h
                    g = xx < n; e, xx, i = e[g], xx[g], i[g]
                    kk = sans_chevauchement(e, xx - 1); e, xx, i = e[kk], xx[kk], i[kk]
                    s = -np.sign(ret[i])
                    r = valeur(B, e, xx, s, 1)
                    cfg["A4 %s k%d %db %s" % (mes, k, h, sens)] = Trades(B, e, xx, s, np.ones(len(e)), [(2, h)] * len(e), r)
    return cfg


def jours_seance(B, fin=960):
    """seances avec bougie 9 h 30 et derniere bougie avant 16 h (>= 16 h - 30 min)."""
    days = np.unique(B.day); o = B.at(days * 1440 + 570); c = B.last_lt(days * 1440 + fin, days * 1440 + fin - 30)
    ok = (o >= 0) & (c >= 0)
    return days[ok], o[ok], c[ok]


def famille_B(B):
    days, io, ic = jours_seance(B)
    cprev = np.r_[np.nan, B.c[ic][:-1]]
    consec = np.r_[False, np.diff(days) <= 4]
    gap = np.where(consec, B.o[io] / cprev - 1, np.nan)
    z = gap / rms_prec(np.nan_to_num(gap))
    cfg = {}
    for k in (1, 1.5, 2):
        for Tf in (630, 720, 960):
            for stop in (0, 1):
                for sens in ("contre", "achat"):
                    m = (np.abs(z) > k) & ~np.isnan(z) & ((gap < 0) if sens == "achat" else True)
                    E, X, S, PO, ST, SPEC = [], [], [], [], [], []
                    for j in np.where(m)[0]:
                        e = io[j]; s = -np.sign(gap[j]); cible = cprev[j]
                        xT = B.last_lt(np.array([days[j] * 1440 + Tf]), days[j] * 1440 + Tf - 30)[0]
                        if xT < e:
                            continue
                        dist = abs(B.o[e] - cible)
                        sl = B.o[e] - s * dist
                        hh, ll, oo, spp = B.h[e:xT + 1], B.l[e:xT + 1], B.o[e:xT + 1], B.sp[e:xT + 1]
                        if s > 0:   # achat : niveaux en bid
                            hit_c = hh >= cible; hit_s = (ll <= sl) if stop else np.zeros(len(hh), bool)
                        else:       # vente : rachat au prix vendeur (bid + spread)
                            hit_c = ll + spp <= cible; hit_s = (hh + spp >= sl) if stop else np.zeros(len(hh), bool)
                        jc = np.argmax(hit_c) if hit_c.any() else 10 ** 9; js = np.argmax(hit_s) if hit_s.any() else 10 ** 9
                        if js <= jc and js < 10 ** 9:               # stop d'abord (prudent si meme bougie)
                            x = e + js; po = min(sl, oo[js]) if s > 0 else max(sl, oo[js] + spp[js]); st = 1
                        elif jc < 10 ** 9:
                            x = e + jc; po = max(cible, oo[jc]) if s > 0 else min(cible, oo[jc] + spp[jc]); st = 0
                        else:
                            x = xT; po = np.nan; st = 0
                        E.append(e); X.append(x); S.append(s); PO.append(po); ST.append(st)
                        SPEC.append((0, int(B.t[x] + B.pas - B.t[e])))
                    E, X, S = np.array(E, int), np.array(X, int), np.array(S, float)
                    r = valeur(B, E, X, S, np.zeros(len(E)), np.array(PO, float), np.array(ST, float)) if len(E) else np.array([])
                    cfg["B k%.1f %s %s %s" % (k, {630: "10h30", 720: "12h", 960: "16h"}[Tf], "stop" if stop else "sans",
                                               sens)] = Trades(B, E, X, S, np.zeros(len(E)), SPEC, r)
    return cfg


def famille_C(B, yahoo=False):
    tm = 930 if yahoo else 900
    days, io, ic = jours_seance(B)
    ip = B.last_lt(days * 1440 + tm, days * 1440 + tm - 60)
    ie = B.at(days * 1440 + tm); i16 = B.at(days * 1440 + 960)
    ok = (ip >= 0) & (ie >= 0)
    M = np.where(ok, B.c[np.maximum(ip, 0)] / B.o[io] - 1, np.nan)
    z = M / rms_prec(np.nan_to_num(M))
    nxt = suivante_ouverture(B, io)
    fen = ("derniere",) if yahoo else ("derniere", "nuit", "fin+nuit")
    cfg = {}
    for k in (1, 1.5, 2):
        for f in fen:
            for sens in ("contre", "suite", "achat-contre", "achat-suite"):
                m = (np.abs(z) > k) & ~np.isnan(z)
                if sens == "achat-contre":
                    m &= M < 0
                elif sens == "achat-suite":
                    m &= M > 0
                s = np.sign(M) * (-1 if sens == "contre" else 1)
                if sens.startswith("achat"):
                    s = np.ones(len(M))
                if f == "derniere":
                    e, x, kx = ie, ic, 0
                    spec = lambda j: (0, int(B.t[ic[j]] + B.pas - B.t[ie[j]]))
                else:
                    e = i16 if f == "nuit" else ie
                    x, kx = nxt, 1
                    spec = lambda j: (1, 0)
                m &= (e >= 0) & (x >= 0) & ((x >= e) if kx == 0 else (x > e))
                j = np.where(m)[0]
                r = valeur(B, e[j], x[j], s[j], kx)
                cfg["C k%.1f %s %s" % (k, f, sens)] = Trades(B, e[j], x[j], s[j], np.full(len(j), kx), [spec(q) for q in j], r)
    return cfg


# ------------------------------------------------------------------ statistiques
def tstat(X):
    X = np.asarray(X, float)
    if X.ndim == 1:
        X = X[:, None]
    s = X.std(0, ddof=1)
    return np.where(s > 0, X.mean(0) / np.where(s > 0, s, 1) * np.sqrt(len(X)), 0.0)


def comptes(n, nb, b=5.0):
    neuf = rng.random((nb, n)) < 1 / b; neuf[:, 0] = True
    pos = np.where(neuf, np.arange(n), 0); pos = np.maximum.accumulate(pos, axis=1)
    dep = np.where(neuf, rng.integers(n, size=(nb, n)), 0)
    dep = np.take_along_axis(dep, pos, axis=1)
    ii = (dep + np.arange(n) - pos) % n
    flat = (ii + np.arange(nb)[:, None] * n).ravel()
    return np.bincount(flat, minlength=nb * n).reshape(nb, n).astype(np.float32)


def rc(M):
    """Reality check de White studentise contre zero : p du meilleur reglage."""
    M = np.nan_to_num(np.asarray(M, np.float32)); n = len(M)
    mu = M.mean(0); sd = M.std(0, ddof=1); sd = np.where(sd > 0, sd, np.inf)
    V = (np.sqrt(n) * mu / sd).max()
    Vb = np.concatenate([(np.sqrt(n) * ((comptes(n, 250) @ M) / n - mu) / sd).max(1) for _ in range(8)])
    return float((Vb >= V).mean())


def serie(T, days):
    """gain par seance (jours = index) et temoin (esperance des rejeux)."""
    d = pd.Series(T.r, index=T.B.day[T.e]).groupby(level=0).sum() if len(T.e) else pd.Series(dtype=float)
    return d.reindex(days).fillna(0.0).values


def walk_forward(cfg, days, per, L, rejeux):
    noms = list(cfg); C = np.column_stack([serie(cfg[k], days) for k in noms])
    Pu = np.sort(np.unique(per)); o, ch, tr = np.zeros(len(days)), [], []
    hors = np.zeros(len(days), bool)
    for i in range(L, len(Pu)):
        app, te = np.isin(per, Pu[i - L:i]), per == Pu[i]
        k = noms[int(np.argmax(tstat(C[app])))]
        o[te] = C[te, noms.index(k)]; hors |= te; ch.append(k)
        T = cfg[k]; dd = T.B.day[T.e]; g = np.isin(dd, days[te])
        tr += [(k, j) for j in np.where(g)[0]]
    return C, noms, o, hors, ch, tr


def bilan(nom, cfg, B, per, L, out_trades):
    days = np.unique(B.day)
    per_d = per(days)
    C, noms, o, hors, ch, tr = walk_forward(cfg, days, per_d, L, None)
    # temoin : rejeux des trades hors echantillon
    rj = {k: rejeu(cfg[k]) for k in set(ch)}
    r_he = np.array([cfg[k].r[j] for k, j in tr]); esp = np.array([rj[k][j].mean() for k, j in tr])
    d_he = np.array([cfg[k].B.day[cfg[k].e[j]] for k, j in tr], int)
    ref = pd.Series(esp, index=d_he).groupby(level=0).sum().reindex(days).fillna(0.0).values if len(tr) else np.zeros(len(days))
    oh, rh = o[hors], ref[hors]
    tot = oh.sum(); t = float(tstat(oh)[0]) if len(oh) > 2 else 0.0
    tt = float(tstat(oh - rh)[0]) if len(oh) > 2 else 0.0
    # tirages au hasard : une seance au hasard (meme mois, meme heure, meme duree, meme sens) par trade
    if len(tr):
        tirs = np.zeros(4000)
        for (k, j) in tr:
            v = rj[k][j]; tirs += v[rng.integers(len(v), size=4000)]
        p_h = float((tirs >= r_he.sum()).mean()); mt = tirs.mean()
    else:
        p_h, mt = 1.0, 0.0
    dh = days[hors]; mid = dh[0] + (dh[-1] - dh[0]) / 2
    m1, m2 = oh[dh <= mid].sum(), oh[dh > mid].sum()
    p1 = 1 - NormalDist().cdf(t); pc = min(1.0, N_LIGNES * p1)
    if tot > 0 and pc < 0.05 and m1 > 0 and m2 > 0 and p_h < 0.05:
        v = "TIENT"
    elif tot > 0 and t >= 1 and m1 > 0 and m2 > 0 and tot > mt:
        v = "PRESQUE"
    else:
        v = "NE TIENT PAS"
    fq = pd.Series(ch).value_counts()
    res = dict(ligne=nom, reglage="%s (%d/%d)" % (fq.index[0], fq.iloc[0], len(ch)), mode=fq.index[0], n=len(tr),
               tot=tot, t=t, bp=1e4 * tot / max(len(tr), 1), m1=m1, m2=m2, tem=mt, tt=tt, ph=p_h, pc=pc, verdict=v,
               p0=pd.to_datetime(dh[0], unit="D").date(), p1=pd.to_datetime(dh[-1], unit="D").date(),
               d0=pd.to_datetime(days[0], unit="D").date(), d1=pd.to_datetime(days[-1], unit="D").date(),
               nach=int(sum(cfg[k].s[j] > 0 for k, j in tr)))
    # trades pour le portefeuille
    D = lambda x: pd.to_datetime(x, unit="D").strftime("%Y-%m-%d")
    he = [(nom, B.nom, D(cfg[k].B.day[cfg[k].e[j]]), D(cfg[k].B.day[cfg[k].x[j]]), int(cfg[k].s[j]), cfg[k].r[j]) for k, j in tr]
    T = cfg[res["mode"]]
    tout = [(nom + " | " + res["mode"], B.nom, D(B.day[T.e[j]]), D(B.day[T.x[j]]), int(T.s[j]), T.r[j]) for j in range(len(T.e))]
    out_trades.append((v, he, tout))
    return res, C, noms, (C - np.column_stack([serie_ref(cfg[k], days) for k in noms]))


def serie_ref(T, days):
    """temoin par seance pour un reglage complet : esperance rejeu ~ moyenne sens x rendement des memes heures.
    (approximation rapide : rejeux calcules seulement pour 1 trade sur 1, voir rejeu)"""
    if len(T.e) == 0:
        return np.zeros(len(days))
    rj = rejeu(T); esp = np.array([v.mean() for v in rj])
    return pd.Series(esp, index=T.B.day[T.e]).groupby(level=0).sum().reindex(days).fillna(0.0).values


def mois(days):
    d = pd.to_datetime(days, unit="D"); return (d.year * 12 + d.month - 1).values


def trimestre(days):
    d = pd.to_datetime(days, unit="D"); return (d.year * 4 + (d.month - 1) // 3).values


# ------------------------------------------------------------------ programme
if __name__ == "__main__":
    t0 = time.time()
    print("Fuseau (pic de volume 13-20 h serveur, NAS M5) : toute l'annee %s ; semaines de decalage de mars %s" %
          verifie_fuseau(["nas_m5_2025a", "nas_m5_90k"]))
    MK = {"NAS": barres_courtier("NAS100+", ["nas_m5_2025a", "nas_m5_90k"]),
          "SP": barres_courtier("SP500+", ["sp_m5_90k"]), "DJ": barres_courtier("DJ30+", ["dj_m5_90k"])}
    H4 = barres_courtier("NAS100+ H4", ["nas_h4_20k"], plancher=0.8, debut="2022-07-11")
    Y = yahoo_1h(); SPBP = {"^NDX": 0.8 / 28500, "^GSPC": 0.36 / 7400, "^DJI": 1.15 / 51000, "^RUT": 0.32 / 2790}
    YB = {}
    for tk, g in Y.groupby("tk"):
        YB[tk] = Barres(tk, g.ny, g.open, g.high, g.low, g.close, g.close * SPBP[tk], 60)
    for k, B in list(MK.items()) + [("H4", H4)] + list(YB.items()):
        print("  %-10s %6d bougies  %s -> %s  spread median %.2f bp" % (k, len(B.t), pd.to_datetime(B.t[0], unit="m").date(),
              pd.to_datetime(B.t[-1], unit="m").date(), 1e4 * np.median(B.sp / B.c)))

    lignes, trades, blocs = [], [], {"courtier M5": [], "H4": [], "Yahoo 1h": []}
    plan = [("A-H1 " + k, "courtier M5", famille_A_h1, MK[k], mois, 6) for k in MK]
    plan += [("A-H4 NAS", "H4", famille_A_h4, H4, trimestre, 6)]
    plan += [("B gap " + k, "courtier M5", famille_B, MK[k], mois, 6) for k in MK]
    plan += [("C fin " + k, "courtier M5", famille_C, MK[k], mois, 6) for k in MK]
    plan += [("A-H1 " + k, "Yahoo 1h", famille_A_h1, YB[k], mois, 6) for k in YB]
    plan += [("C fin " + k, "Yahoo 1h", lambda B: famille_C(B, True), YB[k], mois, 6) for k in YB]
    N = 0
    for nom, bloc, fam, B, per, L in plan:
        cfg = fam(B); N += len(cfg)
        res, C, noms, CR = bilan(nom, cfg, B, per, L, trades)
        res["N"] = len(cfg); res["rc"] = rc(C); res["rcr"] = rc(CR); res["bloc"] = bloc
        blocs[bloc].append((C, CR, np.unique(B.day)))
        lignes.append(res)
        print("%-14s %-10s N=%2d HE %s->%s tr %4d (%3d ach.) %+6.2f %% t %+5.2f bp/tr %+6.1f | moities %+5.2f / %+5.2f %% | "
              "temoin %+5.2f %% t-tem %+5.2f p_h %.3f | p_corr %.3f RC %.3f RCtem %.3f | %s | %s  [%.0f s]" % (
                  nom, bloc[:10], len(cfg), res["p0"], res["p1"], res["n"], res["nach"], 100 * res["tot"], res["t"], res["bp"],
                  100 * res["m1"], 100 * res["m2"], 100 * res["tem"], res["tt"], res["ph"], res["pc"], res["rc"], res["rcr"],
                  res["verdict"], res["reglage"], time.time() - t0))
    print("N total = %d reglages, %d lignes" % (N, len(lignes)))
    rcb = {}
    for b, L_ in blocs.items():
        tous = np.unique(np.concatenate([d for _, _, d in L_]))
        def aligne(i):
            M = [pd.DataFrame(x[i], index=x[2]).reindex(tous).fillna(0.0).values for x in L_]
            return np.hstack(M)
        rcb[b] = (rc(aligne(0)), rc(aligne(1)), sum(x[0].shape[1] for x in L_))
        print("Reality check bloc %-12s N = %3d : contre zero p = %.3f ; contre temoin p = %.3f" % (b, rcb[b][2], rcb[b][0], rcb[b][1]))

    # sorties portefeuille
    col = ["regle", "marche", "entree", "sortie", "sens", "r"]
    he = [x for v, h, _ in trades if v in ("TIENT", "PRESQUE") for x in h]
    to = [x for v, _, t in trades if v in ("TIENT", "PRESQUE") for x in t]
    pd.DataFrame(he, columns=col).to_csv(os.path.join(OUT, "rebonds_intrajour.csv"), index=False, float_format="%.6f")
    pd.DataFrame(to, columns=col).to_csv(os.path.join(OUT, "rebonds_intrajour_tout.csv"), index=False, float_format="%.6f")
    pd.DataFrame(lignes).to_csv(os.path.join(OUT, "intrajour_lignes.csv"), index=False, float_format="%.5g")
    print("Trades ecrits : %d hors echantillon, %d toute periode ; duree %.0f s" % (len(he), len(to), time.time() - t0))
