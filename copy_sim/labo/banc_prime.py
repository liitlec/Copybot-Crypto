"""Banc C : acheter seulement (prime de risque), avec ou sans filtre de tendance, CFD ou comptant sans levier.
Univers : indices, or, argent, BTC, ETH (pas de devises : pas de prime a tenir une devise).
ATTENTION : ce choix d'univers vient apres avoir vu le banc A (les devises y perdent) ; il est donc en partie
contamine. Le vrai verdict sera le registre papier en direct.
Variantes (3) : toujours achete ; achete si cours > moyenne 200 j ; achete en proportion du signal de tendance du banc A.
Usage : python3 banc_prime.py"""
import os
import numpy as np, pandas as pd
import banc_tendance as T
from donnees import UNIVERS

ICI = os.path.dirname(os.path.abspath(__file__))


def poids(r, s, levier, plafond):
    vol = r.ewm(span=60, min_periods=40).std() * np.sqrt(252)
    w = s * (T.RISQUE / vol).clip(upper=plafond)
    n = r.notna().sum(axis=1).clip(lower=1)
    return w.div(n, axis=0) * levier


def net(r, w, taux, mode):
    brut, cout, fin = T.resultat(r, w, taux)
    if mode == "comptant":  # pas de financement ; on touche les dividendes ; frais de fonds 0,2 %/an
        tenu = w.shift(2).fillna(0)
        fin = sum(tenu[a] * (0.002 - T.DIVIDENDE.get(a, 0.0)) for a in w) / 252
    return brut - cout - fin


if __name__ == "__main__":
    r, taux = T.charge()
    r = r["2000":]
    taux = taux.reindex(r.index).ffill()
    cols = [a for a in r if UNIVERS[a][1] != "fx"]
    r = r[cols]
    px = (1 + r.fillna(0)).cumprod().where(r.notna())
    sig = {"toujours achete": r * 0 + 1,
           "achete si > moyenne 200 j": (px > px.rolling(200).mean()).astype(float).where(px.rolling(200).mean().notna()),
           "achete selon tendance A": T.signal(r).clip(lower=0)}
    print("Par periode %s : rendement/an, Sharpe, pire baisse" % (T.PERIODES,))
    sorties = {}
    for mode, levier, plafond in (("CFD", 3.0, 3.0), ("comptant", 1.0, 1.0)):
        for nom, s in sig.items():
            w = poids(r, s, levier, plafond)
            x = net(r, w, taux, mode)
            sorties[(mode, nom)] = x
            print(T.ligne("%s %s" % (mode, nom), x), "| expo moy %.2f" % w["2001":].sum(axis=1).mean())
    # reference : 100 % SP500 comptant
    x = r["SP500"].fillna(0) + 0.013 / 252
    print(T.ligne("ref. 100 % SP500 comptant", x))
    # hasard : filtre 200 j decale au hasard (meme temps passe investi)
    rng = np.random.default_rng(3)
    s0 = sig["achete si > moyenne 200 j"]
    for mode, levier, plafond in (("CFD", 3.0, 3.0), ("comptant", 1.0, 1.0)):
        obs = {p: T.stats(sorties[(mode, "achete si > moyenne 200 j")][p[0]:p[1]])["sharpe"] for p in T.PERIODES}
        tir = {p: [] for p in T.PERIODES}
        for _ in range(200):
            sh = {}
            for a in s0:
                v = s0[a].dropna()
                sh[a] = pd.Series(np.roll(v.values, rng.integers(250, len(v) - 250)), index=v.index)
            x = net(r, poids(r, pd.DataFrame(sh).reindex(s0.index), levier, plafond), taux, mode)
            for p in T.PERIODES:
                tir[p].append(T.stats(x[p[0]:p[1]])["sharpe"])
        print("Hasard %s (filtre decale) : " % mode + " ; ".join(
            "%s-%s filtre %.2f, hasard moyen %.2f, mieux que nous %.0f%%" % (p[0], p[1], obs[p], np.mean(tir[p]), 100 * np.mean(np.array(tir[p]) >= obs[p]))
            for p in T.PERIODES))
