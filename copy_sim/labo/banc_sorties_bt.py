"""Banc X (16/11, PRIORITES 11 h 40) : sorties de la mecanique bt (bt_or : pas 0,25 ATR, stop suiveur 0,667 ATR,
3 positions au plus) sur l'or, le BTC et l'ETH (bougies M5 du courtier, spread reel). Variantes de sortie :
prise partielle (moitie de chaque position a +k R), stop resserre au-dela de X R, objectif en R, sortie au temps,
sortie au retournement de la moyenne 2 jours. 1 R = distance du stop initial (perte d'une position).
Avance glissante simple : choix sur la 1re moitie, verdict sur la 2de ; nombre d'essais affiche.
Usage : python3 banc_sorties_bt.py [ident ...]"""
import sys
import numpy as np, pandas as pd
import banc_grille as G

HEURES = {(3, 5), (8, 0), (8, 30), (12, 0), (15, 45), (16, 0), (16, 30)}


def simule(d, pas_k=0.25, stop_k=0.6667, max_pos=3, partiel=None, serre=None, objectif=None, temps=None, ema_sortie=False):
    c, hi, lo, sp, t = (d[x].values for x in ("cloture", "haut", "bas", "sp", "heure"))
    hh, mm = (t // 3600) % 24, (t // 60) % 60
    ema = d["cloture"].ewm(span=576, min_periods=576).mean().values
    jour = t // 86400
    j = pd.DataFrame({"jour": jour, "h": hi, "l": lo, "c": c}).groupby("jour").agg(h=("h", "max"), l=("l", "min"), c=("c", "last"))
    tr = np.maximum(j.h - j.l, np.maximum((j.h - j.c.shift(1)).abs(), (j.l - j.c.shift(1)).abs()))
    atr = tr.rolling(20).mean().shift(1).reindex(jour).values
    P, ouvert = [], {}

    def ferme(s, prix, i):
        p = ouvert.pop(s)
        g = p["acquis"] + sum(w * s * (prix - e) for e, w in zip(p["e"], p["w"])) / p["stop"]
        P.append((p["i"], g))

    for i in range(600, len(c)):
        for s in list(ouvert):
            p = ouvert[s]
            dist = p["stop"]
            if serre and s * (p["meilleur"] - p["c0"]) >= serre[0] * p["stop"]:
                dist = serre[1] * p["stop"]
            niveau = p["meilleur"] - s * dist
            if (lo[i] <= niveau) if s > 0 else (hi[i] + sp[i] >= niveau):
                ferme(s, niveau, i); continue
            if objectif and s * ((hi[i] if s > 0 else lo[i] + sp[i]) - p["c0"]) >= objectif * p["stop"]:
                ferme(s, p["c0"] + s * objectif * p["stop"], i); continue
            if temps and i - p["i"] >= temps:
                ferme(s, c[i] - (0 if s > 0 else -sp[i]) if s < 0 else c[i], i); continue
            if ema_sortie and s * (c[i] - ema[i]) < 0:
                ferme(s, c[i] + (sp[i] if s < 0 else 0.0), i); continue
            if partiel:
                for k, e in enumerate(p["e"]):
                    if p["w"][k] == 1.0 and s * ((hi[i] if s > 0 else lo[i] + sp[i]) - e) >= partiel * p["stop"]:
                        p["w"][k] = 0.5; p["acquis"] += 0.5 * partiel
            p["meilleur"] = max(p["meilleur"], hi[i]) if s > 0 else min(p["meilleur"], lo[i])
            while len(p["e"]) < max_pos and s * (c[i] - p["prochain"]) >= 0:
                if s * (c[i] - p["prochain"]) <= 0.5 * p["pas"]:
                    p["e"].append(c[i] + (sp[i] if s > 0 else -sp[i])); p["w"].append(1.0)
                p["prochain"] += s * p["pas"]
        if (hh[i], mm[i]) in HEURES and atr[i] == atr[i] and ema[i] == ema[i] and atr[i] > 0:
            s = 1 if c[i] > ema[i] else -1
            if s not in ouvert:
                ouvert[s] = {"i": i, "e": [c[i] + (sp[i] if s > 0 else -sp[i])], "w": [1.0], "acquis": 0.0, "c0": c[i],
                             "meilleur": c[i], "stop": stop_k * atr[i], "pas": pas_k * atr[i],
                             "prochain": c[i] + s * pas_k * atr[i]}
    return P


VARIANTES = [("actuel (stop suiveur 0,667 ATR)", {}),
             ("moitie a +1 R", {"partiel": 1.0}), ("moitie a +2 R", {"partiel": 2.0}),
             ("stop 0,5 R au-dela de +2 R", {"serre": (2.0, 0.5)}), ("stop 0,5 R au-dela de +3 R", {"serre": (3.0, 0.5)}),
             ("stop 0,3 R au-dela de +2 R", {"serre": (2.0, 0.3)}),
             ("objectif +2 R", {"objectif": 2.0}), ("objectif +4 R", {"objectif": 4.0}),
             ("sortie apres 1 jour", {"temps": 288}), ("sortie apres 3 jours", {"temps": 864}),
             ("sortie au retournement EMA 2 j", {"ema_sortie": True}),
             ("moitie +2 R et stop 0,5 R au-dela de +3 R", {"partiel": 2.0, "serre": (3.0, 0.5)})]


def stats(g):
    g = np.array(g)
    if len(g) < 2:
        return "%3d paniers" % len(g)
    cum = np.cumsum(g); top = np.sort(g)[::-1]
    part = top[:max(1, len(g) // 10)].sum() / g.sum() if g.sum() > 0 else float("nan")
    return "%3d paniers  total %+6.1f R  moy %+5.2f (t=%+4.1f)  creux %+5.1f R  part des 10 %% meilleurs %4.0f %%" % (
        len(g), g.sum(), g.mean(), g.mean() / g.std() * np.sqrt(len(g)), (cum - np.maximum.accumulate(cum)).min(), 100 * part)


if __name__ == "__main__":
    print("essais : %d variantes x symboles (correction : un t > 2 sur %d essais est attendu par hasard ~%.1f fois)" % (
        len(VARIANTES), len(VARIANTES), len(VARIANTES) * 0.023))
    for ident in (sys.argv[1:] or ["xau_m5_90k", "btc_m5_90k", "eth_m5_90k"]):
        d = G.charge(ident)
        n = len(d); mi = n // 2
        print("\n%s : %d bougies M5, %s -> %s" % (ident, n, *pd.to_datetime(d["heure"].iloc[[0, -1]], unit="s").dt.date))
        res = []
        for nom, kw in VARIANTES:
            P = simule(d, **kw)
            a = [g for i, g in P if i < mi]; b = [g for i, g in P if i >= mi]
            res.append((nom, sum(a), a, b, [g for _, g in P]))
            print("  %-42s 1re moitie %+6.1f R | 2de moitie %+6.1f R | tout : %s" % (nom, sum(a), sum(b), stats([g for _, g in P])))
        best = max(res[1:], key=lambda r: r[1])
        print("  -> choisi sur la 1re moitie : %s ; 2de moitie %+.1f R contre %+.1f R pour l'actuel" % (best[0], sum(best[3]), sum(res[0][3])))
