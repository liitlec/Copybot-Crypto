"""Banc J : dans quelles conditions elan_m1 et exces_m1 gagnent-ils ? (or M1 du courtier, 3 mois, spread reel)
Decoupes : semaine, heure de Paris, agitation sur 1 h et sur 1 jour (tiers), sens de la tendance de 20 h.
Chaque case est aussi coupee en deux moities de temps : une case ne compte que si elle gagne dans les deux.
En dollars par trade a 0,01 lot (1 bp = 0,40 $). Usage : python3 banc_decoupes.py"""
import numpy as np, pandas as pd
import banc_or as B


def regles(d):
    lr = np.log(d["cloture"])
    r = lr.diff()
    z = r / r.rolling(100).std().shift(1)
    return {"elan_m1": (np.sign(lr - lr.shift(3)), 5),
            "exces_m1": (-((z > 3).astype(float) - (z < -3).astype(float)), 12)}


def ligne(nom, net, brut, moitie):
    n = len(net)
    if n < 20:
        return "  %-22s %6d trades (trop peu)" % (nom, n)
    a, b = net[moitie], net[~moitie]
    et = net.std() / np.sqrt(n)
    return "  %-22s %6d trades  brut %+6.3f  net %+6.3f $ ± %.3f  | 1re moitie %+6.3f (%d)  2e moitie %+6.3f (%d)%s" % (
        nom, n, brut.mean(), net.mean(), et, a.mean() if len(a) else float("nan"), len(a),
        b.mean() if len(b) else float("nan"), len(b),
        "   <== gagne dans les deux" if len(a) >= 20 and len(b) >= 20 and a.mean() > 0 and b.mean() > 0 else "")


if __name__ == "__main__":
    d, _ = B.charge("xau_m1_90k")
    lr = np.log(d["cloture"])
    vol1h = lr.diff().abs().rolling(60).mean()
    vol1j = lr.diff().abs().rolling(1380).mean()
    fond = np.sign(d["cloture"] - d["cloture"].rolling(1200).mean())
    paris = (d.index.hour - 1) % 24
    semaine = d.index.isocalendar().week.values
    cases = 0
    for nom, (s, h) in regles(d).items():
        x, i = B.trades(d, s, h)
        net, brut = x[:, 0] * 0.40, x[:, 1] * 0.40
        moitie = i < len(d) // 2
        sens = np.nan_to_num(s.values)[i]
        print("\n===== %s : %d trades, net %+.3f $ par trade (± %.3f), brut %+.3f $ =====" % (
            nom, len(net), net.mean(), net.std() / np.sqrt(len(net)), brut.mean()))
        print(" Par semaine :")
        for w in sorted(set(semaine[i])):
            m = semaine[i] == w; cases += 1
            print(ligne("semaine %d" % w, net[m], brut[m], moitie[m]))
        print(" Par heure de Paris :")
        for hh in range(24):
            m = paris[i] == hh; cases += 1
            if m.sum():
                print(ligne("%02d h" % hh, net[m], brut[m], moitie[m]))
        for lab, v in (("agitation 1 h", vol1h), ("agitation 1 jour", vol1j)):
            vv = v.values[i]; q = np.nanquantile(vv, [1 / 3, 2 / 3])
            print(" Selon %s (tiers) :" % lab)
            for nm, m in (("calme", vv < q[0]), ("moyen", (vv >= q[0]) & (vv < q[1])), ("agite", vv >= q[1])):
                cases += 1
                print(ligne(nm, net[m], brut[m], moitie[m]))
        print(" Selon la tendance de fond (20 h) :")
        f = fond.values[i]
        for nm, m in (("dans le sens du fond", sens == f), ("contre le fond", sens == -f)):
            cases += 1
            print(ligne(nm, net[m], brut[m], moitie[m]))
    print("\nCases examinees :", cases)
