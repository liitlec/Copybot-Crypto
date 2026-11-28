"""Verdict du test de la semaine du 16 au 20/11 (critères PRIORITES 15/11 13 h et 13 h 20), trades fermés du lundi 16/11
0 h au vendredi 20/11 23 h (Paris = UTC + 1). Sélection : elan_m15, cassure_m15, exces_m5, exces_m1, fcassure_m1, bt_or,
midi_* (hors _calme), repli_ind ; témoin hasard_m1 ; variantes _calme / _ar / _opt / bt_crypto exclues.
Jour « calme » : le drapeau calme de la v11 a été allumé plus de la moitié des heures du jour (événements « regime »).
Non encaissé : profit des positions ouvertes rapprochées de leur ordre d'ouverture (sens + prix). Usage : python3 verdict_semaine.py"""
import collections, datetime, json, math
R = "mt5/"
DEB, FIN = "2026-11-15T23:00", "2026-11-20T22:00"
JOURS = ["2026-11-16", "2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20"]
NOMS = dict(zip(JOURS, ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]))


def paris(h):
    return datetime.datetime.fromisoformat(h.replace("Z", "+00:00")) + datetime.timedelta(hours=1)


def de_la_selection(k):
    """Variantes exclues : *_ar, *_opt, <regle>_calme ; les etiquettes midi_calme* sont le candidat de midi (inclus)."""
    if not k.startswith(("elan_m15", "cassure_m15", "exces_m5", "exces_m1", "fcassure_m1", "bt_or", "midi", "repli_ind")):
        return False
    return not k.endswith(("_ar", "_opt")) and (k.startswith("midi") or not k.endswith("_calme"))


sel, tem = collections.defaultdict(list), []
regimes = []
for l in open(R + "robot_journal.jsonl"):
    try:
        e = json.loads(l)
    except ValueError:
        continue
    h, ev = e.get("heure", ""), e.get("evenement", "")
    if ev == "regime":
        regimes.append((h, e.get("calme")))
    if not (DEB <= h < FIN) or "sortie" not in ev:
        continue
    k = e.get("hypothese") or ""
    v = e.get("profit") if e.get("profit") is not None else (e.get("dernier_profit") or 0.0)
    j = paris(h).strftime("%Y-%m-%d")
    if k == "hasard_m1":
        tem.append(v or 0.0)
    elif de_la_selection(k):
        sel[j].append(v or 0.0)

# part calme de chaque jour
regimes.sort()
calme_j = {}
for j in JOURS:
    t0 = datetime.datetime.fromisoformat(j + "T00:00+01:00")
    n = c = 0
    for k in range(24):
        t = (t0 + datetime.timedelta(hours=k, minutes=30)).astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M")
        etat = None
        for h, v in regimes:
            if h <= t:
                etat = v
        n += 1; c += bool(etat)
    calme_j[j] = c / n > 0.5

jour = {j: sum(sel.get(j, [])) for j in JOURS}
tot = sum(jour.values())
tous = [x for j in JOURS for x in sel.get(j, [])]
compte, bas = 100.0, 100.0
lignes = []
for j in JOURS:
    compte += jour[j]; bas = min(bas, compte)
    lignes.append((NOMS[j], len(sel.get(j, [])), jour[j], compte, "calme" if calme_j[j] else "agité"))
agites = sum(jour[j] for j in JOURS if not calme_j[j])
calmes = [jour[j] for j in JOURS if calme_j[j]]
cout_calme = -sum(min(0.0, x) for x in calmes) / max(1, len(calmes))


def m_se(x):
    if len(x) < 2:
        return (sum(x) / max(1, len(x)), float("inf"))
    m = sum(x) / len(x)
    s = math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1))
    return m, s / math.sqrt(len(x))


ms, ss = m_se(tous); mt, st = m_se(tem)
ecart, se_e = ms - mt, math.sqrt(ss ** 2 + st ** 2)
meilleur = max(jour.values())

# non encaisse
d = json.load(open(R + "etat.json"))
ids = {}
for l in open(R + "robot_journal.jsonl"):
    if '"type": "ordre"' in l and '"ouverture"' in l:
        try:
            e = json.loads(l); ids[(e.get("sens"), round(float(e.get("prix_obtenu") or 0), 2))] = e.get("id", "")
        except Exception:
            pass
lat = 0.0
for p in d.get("positions_robot", []):
    i = ids.get((p["sens"], round(p["prix_entree"], 2)), "")
    if i and de_la_selection(i.rsplit("_", 1)[0] if i.startswith("bt_") else i):
        lat += p.get("profit") or 0.0

print("pont", d["ecrit"])
for nom, n, v, c, r in lignes:
    print("%-9s %-6s %3d trades  %+8.2f $   compte %7.2f $" % (nom, r, n, v, c))
print("total %+.2f ; non encaissé sélection %+.2f ; total + non encaissé %+.2f" % (tot, lat, tot + lat))
print("crit1 total>0 :", tot > 0, "| avec non encaissé :", tot + lat > 0)
print("crit2a jours agités %+.2f -> %s ; 2b coût moyen des jours calmes %.2f $ (n=%d) -> %s ; 2c part du meilleur jour %.0f %%" % (
    agites, agites > 0, cout_calme, len(calmes), cout_calme < 10, 100 * meilleur / tot if tot > 0 else float("nan")))
print("crit3 sélection %+.3f ± %.3f / trade (n=%d), témoin %+.3f ± %.3f (n=%d) : écart %+.3f, 2 ET = %.3f -> %s" % (
    ms, ss, len(tous), mt, st, len(tem), ecart, 2 * se_e, ecart > 2 * se_e))
print("crit4 plus bas du compte 100 $ : %.2f -> %s ; avec non encaissé à la fin : %.2f" % (bas, bas > 70, compte + lat))
