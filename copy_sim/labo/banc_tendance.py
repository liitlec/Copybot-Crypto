"""Banc A : suivi de tendance journalier, diversifie, apres couts (ecart, glissement, financement CFD).
Regle fixee AVANT de regarder les resultats (aucun reglage) :
  signal = moyenne des signes du rendement sur 20, 60, 120 et 250 jours ;
  taille = signal x (10 %/an de risque vise / volatilite 60 j), plafonnee a 3x par actif, /N actifs, x LEVIER ;
  decision a la cloture J, execution a la cloture J+1 (un jour de retard, prudent).
Usage : python3 banc_tendance.py"""
import os
import numpy as np, pandas as pd
from donnees import UNIVERS

ICI = os.path.dirname(os.path.abspath(__file__))
HORIZONS = (20, 60, 120, 250)
RISQUE, PLAFOND, LEVIER = 0.10, 3.0, 3.0
COUT_BP = {"fx": 1.0, "metal": 2.0, "indice": 1.5, "crypto": 8.0}   # par sens, en points de base
MARGE_FIN = 0.025        # marge du courtier sur le financement indices / metaux (par an)
DIVIDENDE = {"SP500": 0.015, "NASDAQ": 0.008, "NIKKEI": 0.018, "FTSE": 0.035, "DAX": 0.0}
FIN_FX = 0.01            # cout de portage FX suppose des deux cotes (ecart de taux ignore, faute de donnees)
FIN_CRYPTO = (0.15, 0.05)  # long, court


def charge():
    p = pd.read_csv(os.path.join(ICI, "data", "jour.csv.gz"), index_col=0, parse_dates=True)
    p = p[p.index.dayofweek < 5]
    taux = (p.pop("TAUX_US_3M").ffill() / 100).clip(lower=0)
    p = p.ffill(limit=5)
    r = p.pct_change(fill_method=None)
    for a in r:  # points aberrants Yahoo
        lim = 0.06 if UNIVERS[a][1] == "fx" else 0.5
        r.loc[r[a].abs() > lim, a] = 0.0
    return r, taux


def signal(r, horizons=HORIZONS):
    px = (1 + r.fillna(0)).cumprod().where(r.notna())
    s = sum(np.sign(px / px.shift(h) - 1) for h in horizons) / len(horizons)
    return s


def poids(r, s):
    vol = r.ewm(span=60, min_periods=40).std() * np.sqrt(252)
    w = s * (RISQUE / vol).clip(upper=PLAFOND)
    n = w.notna().sum(axis=1).clip(lower=1)
    return w.div(n, axis=0) * LEVIER


def resultat(r, w, taux):
    """Rendement journalier net du portefeuille et detail. w = poids decides a la cloture J."""
    tenu = w.shift(2)                       # execute a J+1, gagne le rendement de J+2
    brut = (tenu * r).sum(axis=1)
    echange = (w.shift(1) - w.shift(2)).abs()
    cout = sum(echange[a].fillna(0) * COUT_BP[UNIVERS[a][1]] / 1e4 for a in w)
    fin = pd.Series(0.0, index=w.index)
    for a in w:
        cl, x = UNIVERS[a][1], tenu[a].fillna(0)
        lg, ct = x.clip(lower=0), (-x).clip(lower=0)
        if cl == "fx":
            f = (lg + ct) * FIN_FX
        elif cl == "crypto":
            f = lg * FIN_CRYPTO[0] + ct * FIN_CRYPTO[1]
        else:
            d = DIVIDENDE.get(a, 0.0)
            f = lg * (taux + MARGE_FIN - d) + ct * (MARGE_FIN - taux + d)
        fin += f / 252
    return brut, cout, fin


def stats(x):
    x = x.dropna()
    if len(x) < 50 or x.std() == 0:
        return dict(an=np.nan, vol=np.nan, sharpe=np.nan, pire=np.nan)
    c = (1 + x).cumprod()
    an = c.iloc[-1] ** (252 / len(x)) - 1
    return dict(an=an, vol=x.std() * np.sqrt(252), sharpe=x.mean() / x.std() * np.sqrt(252),
                pire=(c / c.cummax() - 1).min())


def ligne(nom, x):
    out = []
    for deb, fin in PERIODES:
        s = stats(x[deb:fin])
        out.append("%+6.1f%% %5.2f %+6.1f%%" % (100 * s["an"], s["sharpe"], 100 * s["pire"]))
    return "%-28s | %s" % (nom, " | ".join(out))


PERIODES = (("2001", "2015"), ("2016", "2026"), ("2023", "2026"))

if __name__ == "__main__":
    r, taux = charge()
    r = r["2000":]
    taux = taux.reindex(r.index).ffill()
    print("Periodes : %s   (par periode : rendement/an, Sharpe, pire baisse)" % (PERIODES,))
    s = signal(r)
    w = poids(r, s)
    brut, cout, fin = resultat(r, w, taux)
    net = brut - cout - fin
    print(ligne("TENDANCE brut", brut))
    print(ligne("TENDANCE net (principal)", net))
    print("  couts/an : echanges %.2f%%, financement %.2f%% ; levier brut moyen %.2f" % (
        100 * cout["2001":].mean() * 252, 100 * fin["2001":].mean() * 252, w["2001":].abs().sum(axis=1).mean()))
    # references
    wl = poids(r, s * 0 + 1)
    b, c, f = resultat(r, wl, taux)
    print(ligne("Tout acheter (meme risque) net", b - c - f))
    print("Ne rien faire                : 0 % partout (reference)")
    # sensibilite (4 essais de plus, non retenus)
    for h in HORIZONS:
        b, c, f = resultat(r, poids(r, signal(r, (h,))), taux)
        print(ligne("  horizon seul %d j net" % h, b - c - f))
    # par classe
    for cl in ("fx", "metal", "indice", "crypto"):
        cols = [a for a in r if UNIVERS[a][1] == cl]
        b, c, f = resultat(r[cols], w[cols], taux)
        print(ligne("  part %s net" % cl, b - c - f))
    # hasard : memes signaux decales au hasard dans le temps (meme rotation, meme persistance)
    rng = np.random.default_rng(1)
    obs = {p: stats(net[p[0]:p[1]])["sharpe"] for p in PERIODES}
    tir = {p: [] for p in PERIODES}
    for _ in range(300):
        sh = {}
        for a in s:
            v = s[a].dropna()
            if len(v) > 600:
                sh[a] = pd.Series(np.roll(v.values, rng.integers(250, len(v) - 250)), index=v.index)
        sh = pd.DataFrame(sh).reindex(s.index)
        b, c, f = resultat(r, poids(r, sh), taux)
        x = b - c - f
        for p in PERIODES:
            tir[p].append(stats(x[p[0]:p[1]])["sharpe"])
    for p in PERIODES:
        t = np.array(tir[p])
        print("Hasard %s-%s : Sharpe moyen %.2f, 95e centile %.2f ; tendance %.2f ; part du hasard qui fait mieux %.1f%%"
              % (p[0], p[1], np.nanmean(t), np.nanpercentile(t, 95), obs[p], 100 * np.mean(t >= obs[p])))
    net.to_frame("net").join(brut.rename("brut")).to_csv(os.path.join(ICI, "data", "tendance_jour.csv.gz"), float_format="%.6f")
