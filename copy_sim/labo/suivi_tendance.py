"""Variante papier « suivre ce qui marche » (banc AB, piste 2), mesuree sur les VRAIS trades de la demo, sans ouvrir
de position en plus : les trades elan_m15 et cassure_m15 du robot sont gardes seulement si la somme de la famille
sur les 3 jours de bourse precedents est positive (regle fixee le 17/11/2026, jugee sur les trades suivants).
Jour = jour de Paris de la sortie du trade. Usage : python3 suivi_tendance.py"""
import json, os, collections, datetime

ICI = os.path.dirname(os.path.abspath(__file__))
FAMILLE = ("elan_m15", "cassure_m15")
DEPUIS = "2026-11-17"                      # regle fixee ce jour-la : avant = pour information


def lire():
    ouv, tr = {}, []
    for l in open(os.path.join(ICI, "mt5", "robot_journal.jsonl"), encoding="utf-8"):
        try:
            x = json.loads(l)
        except ValueError:
            continue
        if x.get("type") != "note" or x.get("hypothese") not in FAMILLE:
            continue
        if x.get("evenement") == "sortie":
            p = x.get("profit", x.get("dernier_profit"))
            if p is None:
                continue
            t = datetime.datetime.fromisoformat(x["heure"].replace("Z", "+00:00")) + datetime.timedelta(hours=1)   # Paris (hiver)
            tr.append((t.date().isoformat(), x["hypothese"], float(p)))
    return tr


if __name__ == "__main__":
    tr = lire()
    jours = collections.OrderedDict()
    for j, h, p in tr:
        jours.setdefault(j, []).append(p)
    noms = list(jours)
    print("%-11s %6s %9s %14s %s" % ("jour", "trades", "famille $", "3 j d'avant $", "variante suivi"))
    tot = totv = 0.0; nv = 0
    for k, j in enumerate(noms):
        s = sum(jours[j]); av = sum(sum(jours[x]) for x in noms[max(0, k - 3):k]) if k >= 3 else None
        garde = av is not None and av > 0
        print("%-11s %6d %+9.2f %14s %s" % (j, len(jours[j]), s, "%+.2f" % av if av is not None else "-", ("trade (%+.2f $)" % s) if garde else "en pause"))
        if j >= DEPUIS:
            tot += s
            if garde:
                totv += s; nv += len(jours[j])
    print("Depuis le %s : famille complete %+.2f $ ; variante suivi %+.2f $ (%d trades)" % (DEPUIS, tot, totv, nv))
