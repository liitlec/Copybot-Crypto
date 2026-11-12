"""Resultats en direct du robot sur la demo, par hypothese. Lit mt5/robot_journal.jsonl (ecrit par le pont).
Gain en dollars pour 0,01 lot (1 once), spread deja paye. Usage : python3 analyse_robot.py"""
import json, os, math, collections

ICI = os.path.dirname(os.path.abspath(__file__))


def lire():
    out = []
    with open(os.path.join(ICI, "mt5", "robot_journal.jsonl"), encoding="utf-8") as f:
        for l in f:
            try:
                out.append(json.loads(l))
            except ValueError:
                pass
    return out


def tableau(lignes):
    ouv = {}                                    # ticket -> ordre d'ouverture
    gains = collections.defaultdict(list)       # hypothese -> gains $
    gliss, spreads, refus = [], [], 0
    stops = collections.Counter()
    for x in lignes:
        if x.get("type") == "ordre" and x.get("action") == "ouverture":
            if x.get("ok"):
                ouv[x["ticket"]] = x
                s = 1 if x["sens"] == "achat" else -1
                gliss.append(s * (x["prix_obtenu"] - x["prix_demande"]))     # > 0 = moins bon que demande
                spreads.append(x.get("spread_points", 0) / 100.0)
            else:
                refus += 1
        elif x.get("type") == "ordre" and x.get("action") == "fermeture" and x.get("ok") and x.get("ticket") in ouv:
            o = ouv.pop(x["ticket"])
            s = 1 if o["sens"] == "achat" else -1
            gains[o.get("id", "?")].append(s * (x["prix_obtenu"] - o["prix_obtenu"]) * 100 * o["lots"])
        elif x.get("type") == "note" and x.get("evenement") == "sortie" and x.get("raison", "").startswith("stop"):
            o = ouv.pop(x.get("ticket"), None)
            if o and x.get("dernier_profit") is not None:
                gains[o.get("id", "?")].append(x["dernier_profit"])     # sortie au stop : dernier profit vu (approx.)
                stops[o.get("id", "?")] += 1
    print("%-16s %6s %6s %10s %10s %8s %9s" % ("hypothese", "trades", "stops", "moyen $", "+/- (1 et)", "t", "total $"))
    for h in sorted(gains):
        g = gains[h]
        n, m = len(g), sum(g) / len(g)
        e = math.sqrt(sum((v - m) ** 2 for v in g) / (n - 1) / n) if n > 1 else float("nan")
        print("%-16s %6d %6d %+10.3f %10.3f %+8.2f %+9.2f" % (h, n, stops[h], m, e, m / e if e and e == e else float("nan"), sum(g)))
    if gliss:
        print("Ouvertures : %d, refus : %d ; spread moyen a l'entree %.3f $ ; glissement moyen %+.4f $ (max %+.2f)"
              % (len(gliss), refus, sum(spreads) / len(spreads), sum(gliss) / len(gliss), max(gliss)))
    print("Positions encore ouvertes :", len(ouv))


if __name__ == "__main__":
    tableau(lire())
