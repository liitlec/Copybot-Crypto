"""Banc AE : reagir plus vite aux retournements (PRIORITES 16/11 10 h 30, idees 2, 3, 4 ; l'idee 1, l'alignement sur
la tendance de fond, est refutee au banc AB). Or M15 du courtier, 15 mois, spread reel, pause au calme comme la v11,
$ a 0,01 lot. Regles de tendance du test : elan_m15 (sens des 3 dernieres heures) et cassure_m15 (sortie de la
fourchette de 12 h), tenue 3 h au plus, une position a la fois. A = amplitude moyenne des 48 dernieres bougies M15.
Sorties comparees (stop ou sortie jugee dans la bougie, au pire prix) :
  base      : sortie au temps, 3 h ;
  extreme1h : sortie si une cloture depasse, contre la position, le plus haut / plus bas des 4 bougies precedentes ;
  inversion : sortie si l'elan de 3 h change de signe ;
  zero X    : stop ramene au prix d'entree apres un gain de X fois A (X = 1, 2) ;
  suiveur K : stop suiveur a K fois A du meilleur prix (K = 2, 3) ;
  retourne  : comme extreme1h, puis position inverse tenue jusqu'a la fin des 3 h.
Reglage = 1re moitie, verdict = 2de. 2 regles x 8 sorties = 16 essais. Usage : python3 banc_retournement.py"""
import numpy as np, pandas as pd
import banc_or as B

USD = 0.40
m15, _ = B.charge("xau_m15_50k"); m5, _ = B.charge("xau_m5_90k")
m15 = m15[m15.index >= m5.index[0]]
jd = m5.index.floor("D")
D = m5.groupby(jd).agg(h=("haut", "max"), b=("bas", "min"), o=("cloture", "first"))
rg = (D.h - D.b) / D.o
calme_v = (rg.shift(1) < rg.shift(1).rolling(60, min_periods=20).median()).fillna(False)
calme = calme_v.reindex(m15.index.floor("D")).fillna(False).values
o, h, l, c, sp = (m15[x].values for x in ("ouverture", "haut", "bas", "cloture", "sp"))
A = (m15["haut"] - m15["bas"]).rolling(48).mean().shift(1).values
lr = np.log(m15["cloture"])
elan = np.sign(lr - lr.shift(12)).fillna(0).values
ha, ba = m15["haut"].shift(1).rolling(48).max(), m15["bas"].shift(1).rolling(48).min()
cass = ((m15["cloture"] > ha).astype(float) - (m15["cloture"] < ba).astype(float)).values
h4 = m15["haut"].shift(1).rolling(4).max().values; b4 = m15["bas"].shift(1).rolling(4).min().values
n = len(c); H = 12


def jouer(sig, mode, x=0.0):
    out, i = [], 50
    while i < n - H - 2:
        s = sig[i]
        if s == 0 or calme[i] or not A[i] > 0:
            i += 1; continue
        e = o[i + 1]; a = A[i]
        stop = None; meilleur = e; g = None; fin = i + H
        for j in range(i + 1, fin + 1):
            adverse = l[j] if s > 0 else h[j] + sp[j]
            if stop is not None and (adverse - stop) * s <= 0:
                g = s * (stop - e); break
            fav = h[j] if s > 0 else l[j]
            if (fav - meilleur) * s > 0:
                meilleur = fav
            if mode == "zero" and (meilleur - e) * s >= x * a:
                stop = e
            if mode == "suiveur":
                stop = meilleur - s * x * a
            if mode in ("extreme1h", "retourne") and ((s > 0 and c[j] < b4[j]) or (s < 0 and c[j] > h4[j])):
                g = s * (c[j] - e)
                if mode == "retourne" and j < fin:
                    g += -s * (c[fin] - c[j]) - sp[j]          # position inverse jusqu'a la fin, un spread de plus
                break
            if mode == "inversion" and elan[j] == -s:
                g = s * (c[j] - e); break
        if g is None:
            j = fin; g = s * (c[fin] - e)
        out.append((i, (g - sp[i + 1]) / e * 1e4 * USD))
        i = j if mode != "retourne" else fin
    return np.array(out)


def st(x):
    return "%4d tr %+5.2f $ (t %+.1f), total %+6.0f $" % (len(x), x.mean(), x.mean() / x.std() * np.sqrt(len(x)), x.sum())


mil = n // 2
print("%-34s | reglage %36s | verdict" % ("", ""))
for nom, sig in (("elan_m15", elan), ("cassure_m15", cass)):
    for lib, mode, x in (("base (3 h)", "base", 0), ("sortie extreme 1 h", "extreme1h", 0), ("sortie inversion de l'elan", "inversion", 0),
                         ("stop a zero apres +1 A", "zero", 1), ("stop a zero apres +2 A", "zero", 2), ("suiveur 2 A", "suiveur", 2),
                         ("suiveur 3 A", "suiveur", 3), ("retournement", "retourne", 0)):
        t = jouer(sig, mode, x)
        print("  %-12s %-26s | %s | %s" % (nom, lib, st(t[t[:, 0] < mil, 1]), st(t[t[:, 0] >= mil, 1])))
