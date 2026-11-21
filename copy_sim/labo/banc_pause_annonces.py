"""Banc AC : pause du robot autour des annonces fortes (suite de banc_annonces.py, qui testait l'or a 8 h 30 NY
SANS calendrier). Ici on ne cherche pas a trader l'annonce : on se demande si NE PAS etre en position autour
d'elle ameliore les 4 regles de base de banc_famille.py (elan_m15, cassure_m15, fcassure_m5, contre_exces_m5 ;
meme pause au calme v11, spread reel du courtier, $ a 0,01 lot).
Regle de pause : aucune position ouverte entre (annonce - AVANT) et (annonce + APRES) : un signal est refuse si
sa tenue prevue [entree, sortie] touche cette fenetre (le signal est masque, la regle peut reprendre ensuite).
Calendrier : Helious (api.helious.io, sans cle, copie dans data/helious_calendrier.json.gz). Son historique
d'annonces economiques ne commence que le 14/11/2026 (avant : seulement des jours feries), donc il ne couvre
AUCUN jour des bougies de l'or (06/08/2025 -> 11/11/2026). On le complete par une liste reconstruite de dates
publiques : emploi US (NFP), inflation US (CPI) a 8 h 30 NY, decisions FOMC a 14 h NY (dates de la Fed), avec les
reports dus aux fermetures de l'administration de 2025-2026 ; variante « monde » = US + BCE (8 h 15 NY) + BoE
(7 h NY). Serveur du courtier = New York + 7 h (verifie dans banc_annonces.py). Les evenements Helious High qui
tomberaient dans les donnees sont ajoutes automatiquement (aucun aujourd'hui).
Grille fixee d'avance : AVANT {15, 30, 60} min x APRES {15, 30, 60, 120} min x {US, monde} = 24 reglages.
Methode : gains par jour (jour de la decision) ; walk-forward glissant apprentissage 6 mois / test 1 mois, choix
du reglage au meilleur t sur l'apprentissage ; difference par jour avec la meme regle sans pause ; reality check
de White (bootstrap stationnaire, blocs 5 j, 2000 tirages) des 24 reglages contre la regle sans pause ; temoin a
exposition egale : memes fenetres placees sur des jours ouvres tires au hasard (100 tirages).
Verdict fixe d'avance sur la difference : tient = diff > 0 et (t >= 2,6 ou p RC < 0,05) ; presque = diff > 0 et
(1,5 <= t < 2,6 ou p < 0,15). Usage : python3 banc_pause_annonces.py"""
import contextlib, io, os, json, gzip, urllib.request
import numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    import banc_famille as F
m15, m5, REGLES, tr, USD = F.m15, F.m5, F.REGLES, F.tr, F.USD
idx = F.D.index[F.D.index.dayofweek < 5]
BAR = {"elan_m15": "15min", "cassure_m15": "15min", "fcassure_m5": "5min", "contre_exces_m5": "5min"}
ICI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ICI, "data", "helious_calendrier.json.gz")

# ---------------------------------------------------------------- calendrier
def helious():
    if not os.path.exists(CACHE):
        try:
            r = urllib.request.urlopen("https://api.helious.io/api/calendar", timeout=20).read()
            os.makedirs(os.path.dirname(CACHE), exist_ok=True)
            with gzip.open(CACHE, "wb") as f:
                f.write(r)
        except Exception as e:
            print("Helious injoignable (%s) : calendrier reconstruit seul" % e)
            return pd.DataFrame(columns=["t", "type", "impact", "country"])
    j = pd.DataFrame(json.load(gzip.open(CACHE)))
    j["t"] = pd.to_datetime(j["datetime_utc"], utc=True)
    return j


def serveur(t_utc):
    """Heure UTC -> horloge du serveur (New York + 7 h)."""
    t = pd.DatetimeIndex(t_utc)
    return t.tz_convert("America/New_York").tz_localize(None) + pd.Timedelta("7h")


NFP = ["2025-09-05", "2025-11-20", "2025-12-16", "2026-01-09", "2026-02-11", "2026-03-06", "2026-04-03", "2026-05-08",
       "2026-06-05", "2026-07-02", "2026-08-07", "2026-09-04", "2026-10-02", "2026-11-06"]     # oct. 2025 annule
CPI = ["2025-08-12", "2025-09-11", "2025-10-24", "2025-12-18", "2026-01-13", "2026-02-13", "2026-03-11", "2026-04-10",
       "2026-05-12", "2026-06-10", "2026-07-14", "2026-08-12", "2026-09-11", "2026-10-14", "2026-11-10"]  # nov. 2025 annule
FOMC = ["2025-09-17", "2025-10-29", "2025-12-10", "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29",
        "2026-09-16", "2026-10-28"]
BCE = ["2025-09-11", "2025-10-30", "2025-12-18", "2026-02-05", "2026-03-19", "2026-04-30", "2026-06-11", "2026-07-23",
       "2026-09-10", "2026-10-29"]
BOE = ["2025-09-18", "2025-11-06", "2025-12-18", "2026-02-05", "2026-03-19", "2026-04-30", "2026-06-18", "2026-07-30",
       "2026-09-17", "2026-11-05"]
ts = lambda L, hm: [pd.Timestamp(d + " " + hm) for d in L]
EV = {"NFP": ts(NFP, "15:30"), "CPI": ts(CPI, "15:30"), "FOMC": ts(FOMC, "21:00"), "BCE": ts(BCE, "15:15"), "BoE": ts(BOE, "14:00")}
H = helious()
hh = H[(H.impact == "High") & (H.type != "holiday")]
fin = m5.index[-1]
hh_in = hh[(serveur(hh.t) >= m5.index[0]) & (serveur(hh.t) <= fin)]
CAL = {"US": sorted(set(EV["NFP"] + EV["CPI"] + EV["FOMC"] + list(serveur(hh_in[hh_in.country.fillna("US") == "US"].t))))}
CAL["monde"] = sorted(set(CAL["US"] + EV["BCE"] + EV["BoE"] + list(serveur(hh_in.t))))
eco = H[H.type == "economic"]
print("Helious : %d evenements, annonces economiques du %s au %s ; High (hors feries) avant la fin des bougies (%s) : %d"
      % (len(H), eco.t.min().date() if len(eco) else "-", eco.t.max().date() if len(eco) else "-", fin.date(), len(hh_in)))
print("=> historique Helious utile < 1 mois (exige : 15) : calendrier RECONSTRUIT (NFP %d, CPI %d, FOMC %d ; monde + BCE %d, BoE %d)"
      % tuple(len(EV[k]) for k in ("NFP", "CPI", "FOMC", "BCE", "BoE")))
a = m5.haut - m5.bas
rap = a / a.rolling(24).mean().shift(1)
hm = m5.index.hour * 60 + m5.index.minute
ctl = " ; ".join("%s %.1fx" % (k, np.nanmedian([rap.get(t, np.nan) for t in v])) for k, v in EV.items())
print("Controle des dates : amplitude de la bougie M5 d'annonce / 2 h d'avant, mediane : %s (jour ordinaire 15:30 %.1fx, 21:00 %.1fx)"
      % (ctl, rap[hm == 930].median(), rap[hm == 1260].median()))

# ---------------------------------------------------------------- pause
def masque(n, evts, av, ap):
    """True = signal autorise ; False si la tenue [entree, sortie] touche une fenetre [t-av, t+ap]."""
    d, s, h, _ = REGLES[n]
    t = d.index.values
    ent = np.r_[t[1:], t[-1:]]
    ext = np.r_[t[h:], np.repeat(t[-1:], h)] + pd.Timedelta(BAR[n]).to_timedelta64()
    ok = np.ones(len(d), bool)
    for e in evts:
        ws, we = np.datetime64(e - pd.Timedelta(minutes=av)), np.datetime64(e + pd.Timedelta(minutes=ap))
        i0 = np.searchsorted(ext, ws, side="right"); i1 = np.searchsorted(ent, we, side="left")
        ok[i0:i1] = False
    return ok


def jour(x):
    g = x.g.groupby(x.index.floor("D"))
    return g.sum().reindex(idx).fillna(0), g.size().reindex(idx).fillna(0)


NOMS = list(REGLES)
BASE = {n: jour(F.T[n]) for n in NOMS}
GRILLE = [(v, av, ap) for v in ("US", "monde") for av in (15, 30, 60) for ap in (15, 30, 60, 120)]
CFG = {n: {} for n in NOMS + ["4 regles"]}
for k in GRILLE:
    tot, nb = 0, 0
    for n in NOMS:
        d, s, h, _ = REGLES[n]
        g, c = jour(tr(d, s, h, masque(n, CAL[k[0]], k[1], k[2])))
        CFG[n][k] = (g, c); tot = tot + g; nb = nb + c
    CFG["4 regles"][k] = (tot, nb)
BASE["4 regles"] = (sum(BASE[n][0] for n in NOMS), sum(BASE[n][1] for n in NOMS))
N = len(GRILLE)

# ---------------------------------------------------------------- walk-forward + reality check
tstat = lambda x: x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else 0.0
creux = lambda x: (x.cumsum() - x.cumsum().cummax()).min()
mois = idx.to_period("M"); MO = mois.unique()
fen = [(MO[i - 6], MO[i - 1], MO[i]) for i in range(6, len(MO))]
rng = np.random.default_rng(17)
def boot_idx(n, b=5.0):
    i = np.empty(n, int); i[0] = rng.integers(n)
    neuf = rng.random(n) < 1 / b; nv = rng.integers(n, size=n)
    for t in range(1, n):
        i[t] = nv[t] if neuf[t] else (i[t - 1] + 1) % n
    return i
I = [boot_idx(len(idx)) for _ in range(2000)]
nom_k = lambda k: "%s -%d/+%d" % k

print("Or, bougies du courtier %s -> %s (%d jours ouvres) ; N = %d reglages par regle ; %d fenetres de test %s -> %s ; Bonferroni : t >= %.1f"
      % (idx[0].date(), idx[-1].date(), len(idx), N, len(fen), fen[0][2], fen[-1][2], 2.6))
print("Walk-forward (hors echantillon concatene, $ a 0,01 lot) : avec pause | sans pause memes jours | difference")
print("%-16s %-16s %5s %7s %5s %6s %5s %5s %6s | %7s %6s | %6s %5s %6s %-11s" % ("regle", "reglage le + pris", "nb", "total", "t", "mois+", "trad", "bp/tr", "creux", "sans", "creux", "diff", "t", "p RC", "verdict"))
RES = {}
for n in NOMS + ["4 regles"]:
    oos, nb, choix = [], [], []
    for a_, b_, t_ in fen:
        app, te = (mois >= a_) & (mois <= b_), mois == t_
        best = max(GRILLE, key=lambda k: tstat(CFG[n][k][0][app]))
        choix.append(best); oos.append(CFG[n][best][0][te]); nb.append(CFG[n][best][1][te])
    o, c = pd.concat(oos), pd.concat(nb)
    b0 = BASE[n][0][o.index]; dd = o - b0
    pm = o.groupby(o.index.to_period("M")).sum()
    M = np.column_stack([CFG[n][k][0].values for k in GRILLE]) - BASE[n][0].values[:, None]
    mu = M.mean(0); V = np.sqrt(len(idx)) * mu.max()
    p = (np.array([np.sqrt(len(idx)) * (M[ii].mean(0) - mu).max() for ii in I]) >= V).mean()
    t = tstat(dd)
    v = "tient" if dd.sum() > 0 and (t >= 2.6 or p < 0.05) else ("presque" if dd.sum() > 0 and (1.5 <= t < 2.6 or p < 0.15) else "ne tient pas")
    fq = pd.Series([nom_k(k) for k in choix]).value_counts()
    RES[n] = (fq.index[0], GRILLE[int(mu.argmax())], mu.max() * len(idx))
    print("%-16s %-16s %5s %+7.0f %+5.1f %3d/%-2d %5d %+5.1f %+6.0f | %+7.0f %+6.0f | %+6.0f %+5.1f %6.3f %-11s" % (
        n, fq.index[0], "%d/%d" % (fq.iloc[0], len(fen)), o.sum(), tstat(o), (pm > 0).sum(), len(pm), c.sum(),
        o.sum() / USD / max(c.sum(), 1), creux(o), b0.sum(), creux(b0), dd.sum(), t, p, v))
print("Meilleur reglage sur tout l'echantillon (celui que juge le reality check) : " + " ; ".join(
    "%s %s %+.0f $" % (n, nom_k(RES[n][1]), RES[n][2]) for n in NOMS + ["4 regles"]))

print("\nTout l'echantillon, 4 regles ensemble : difference avec / sans pause ($) et trades retires")
print("%-14s" % "" + "".join("%15s" % ("apres %d min" % ap) for ap in (15, 30, 60, 120)))
bt, bn = BASE["4 regles"]
for v in ("US", "monde"):
    for av in (15, 30, 60):
        print("%-14s" % ("%s avant %d" % (v, av)) + "".join("%+8.0f (%4d)" % (CFG["4 regles"][(v, av, ap)][0].sum() - bt.sum(), bn.sum() - CFG["4 regles"][(v, av, ap)][1].sum()) for ap in (15, 30, 60, 120)))
print("Sans pause : 4 regles %+.0f $ en %d trades ; par regle : %s" % (bt.sum(), bn.sum(), ", ".join("%s %+.0f" % (n, BASE[n][0].sum()) for n in NOMS)))

# ---------------------------------------------------------------- temoin a exposition egale
k = [kk for kk in GRILLE if nom_k(kk) == RES["4 regles"][0]][0]
reel = CFG["4 regles"][k][0].sum() - bt.sum()
jours = idx[(idx >= m5.index[0].floor("D")) & (idx < fin.floor("D"))]
ann = set(pd.Timestamp(e).floor("D") for e in CAL["monde"])
libres = np.array([j for j in jours if j not in ann])
r2 = np.random.default_rng(3); pl = []
for _ in range(100):
    tir = r2.choice(libres, len(CAL[k[0]]), replace=False)
    ev = [pd.Timestamp(j) + (e - e.floor("D")) for j, e in zip(tir, CAL[k[0]])]
    pl.append(sum(jour(tr(*REGLES[n][:3], masque(n, ev, k[1], k[2])))[0].sum() for n in NOMS) - bt.sum())
pl = np.array(pl)
print("Temoin (reglage %s, memes heures sur %d jours ouvres tires au hasard, 100 tirages) : diff reelle %+.0f $ ; temoin moyen %+.0f $, 5e-95e centiles %+.0f / %+.0f ; part des temoins >= reel %.2f"
      % (nom_k(k), len(CAL[k[0]]), reel, pl.mean(), np.percentile(pl, 5), np.percentile(pl, 95), (pl >= reel).mean()))

# ---------------------------------------------------------------- controle : retrait simple des trades touches
def retrait(evts, av, ap):
    """Somme des gains des trades de base (4 regles) dont la tenue touche une fenetre : ce que la pause enleve
    SANS decaler les trades suivants (elan_m15 enchaine ses trades : masquer un signal decale toute la suite)."""
    tot = 0.0
    for n in NOMS:
        d, s, h, _ = REGLES[n]
        ok = masque(n, evts, av, ap)
        x = F.T[n]
        tot += x.g[~ok[d.index.get_indexer(x.index)]].sum()
    return -tot
for v in ("US", "monde"):
    print("Retrait simple, %-5s avant 30 min, apres 15/30/60/120 : %s $ (a comparer au tableau : l'ecart vient du decalage des trades suivants)"
          % (v, " / ".join("%+.0f" % retrait(CAL[v], 30, ap) for ap in (15, 30, 60, 120))))
k = ("US", 30, 60); dd = CFG["4 regles"][k][0] - bt
ja = set(pd.Timestamp(e).floor("D") for e in CAL["US"])
print("Reglage US -30/+60, 4 regles : diff %+.0f $ dont %+.0f $ les jours d'annonce et %+.0f $ les autres jours ; sans les 2 meilleurs jours %+.0f $"
      % (dd.sum(), dd[dd.index.isin(ja)].sum(), dd[~dd.index.isin(ja)].sum(), dd.sum() - dd.nlargest(2).sum()))
