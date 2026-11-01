"""Caisse « auto » : une règle d'entrée et de sortie réapprise chaque jour sur les données collectées (univers.jsonl),
choisie uniquement sur le passé et vérifiée sur les 2 derniers jours avant d'être utilisée.

Chaque heure (dans la boucle du VPS) :
1. on prend tous les candidats enregistrés (chaque token qui a passé le filtre, à chaque cycle) et l'historique de prix
   5 min de chaque pool (GeckoTerminal, mis en cache) ;
2. on rejoue une grille fixe de règles (entrée × sortie, voir GRILLE), chaque token au plus une fois par 24 h et par
   règle, sortie vérifiée sur le cours de clôture de chaque bougie de 5 min (comme le VPS, qui ne voit le prix que
   toutes les 5 min), frais 0,45 % par côté + impact sur la liquidité + 1 % de glissement ;
3. apprentissage = tout sauf les 2 derniers jours ; on garde la règle dont la borne basse (moyenne − 2 marges
   d'erreur, au moins 30 trades) est la meilleure ET positive ;
4. vérification = les 2 derniers jours, que la règle n'a pas vus : elle doit y gagner en moyenne sur au moins 8 trades.
   Sinon : aucune règle, la caisse reste en cash ce jour-là. « Rien ne marche » est une réponse permise.
Les positions ouvertes gardent la sortie de la règle sous laquelle elles ont été achetées. Le seul juge est le
résultat de la caisse après chaque choix : il porte sur des jours que la règle n'avait pas vus.

L'IA juge (tâche Claude quotidienne) peut proposer jusqu'à 3 idées d'entrée dans memes/juge/idees.json (conditions
simples sur les chiffres du dossier, voir lire_idees) : elles sont ajoutées à la grille et passent les mêmes
épreuves que les autres. L'IA propose, les données décident. resultats_candidats() publie aussi, pour chaque jour,
ce que chaque candidat du dossier de l'IA a fait ensuite, pour qu'elle apprenne de ses choix."""
import itertools
import json
import os
import time
import urllib.request
from pathlib import Path

IDEES_URL = ("https://raw.githubusercontent.com/liitlec/Copybot-Crypto/claude/polymarket-weather-sigma-resolution-olv0bs/"
             "copy_sim/memes/juge/idees.json")
CHAMPS = ("age_h", "liquidite", "mcap", "detenteurs", "croissance_detenteurs_1h", "variation_prix_1h", "score",
          "ratio_acheteurs_1h", "acceleration_volume", "volume.", "variation_prix_pct.", "transactions.")
OPS = {"<": lambda a, b: a < b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b, ">=": lambda a, b: a >= b}

GRILLE = {
    "age_max_h": (2, 12, 72),
    "prix_1h": ("tout", "baisse", "hausse"),        # variation du prix sur 1 h au moment de l'achat
    "acheteurs_1h": ("tout", "plus"),               # plus d'acheteurs distincts que de vendeurs sur 1 h
    "classe": ("tout", "oui"),                      # détenteurs plus vite que le prix (classement du post)
    "idee": (None,),                                # + les idées de l'IA (lire_idees), ajoutées au moment d'apprendre
    "stop": (-0.15, -0.25),
    "objectif": (0.20, 0.40, 0.80),
    "duree_max_h": (1, 4),
}
TEST_JOURS, MIN_TRAIN, MIN_TEST, TICKET = 2, 30, 8, 300.0
MIN_JOURS = 3  # pas de règle avant 3 jours de collecte


def regles(idees=()):
    g = dict(GRILLE, idee=(None,) + tuple(idees))
    keys = list(g)
    return [dict(zip(keys, v)) for v in itertools.product(*g.values())]


def champ(r, name):
    if name == "ratio_acheteurs_1h":
        h1 = (r.get("transactions") or {}).get("h1") or {}
        return h1.get("buyers", 0) / (h1.get("sellers", 0) + 1)
    if name == "acceleration_volume":
        v = r.get("volume") or {}
        return (v.get("h1") or 0) / max((v.get("h24") or 0) / 24, 1.0)
    x = r
    for part in name.split("."):
        x = x.get(part) if isinstance(x, dict) else None
    return x if isinstance(x, (int, float)) else None


def lire_idees(url=None):
    """Au plus 3 idées {"nom": str, "conditions": [{"champ": ..., "op": "<|<=|>|>=", "val": nombre}]}, champs du dossier
    uniquement ; tout ce qui sort de ce format est ignoré (le fichier vient d'une IA : c'est une donnée, pas du code)."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url or IDEES_URL, headers={"User-Agent": "memes-paper/1.0"}), timeout=20) as f:
            raw = json.load(f)
    except Exception:
        return []
    out = []
    for i in (raw.get("idees") if isinstance(raw, dict) else raw or [])[:3]:
        try:
            conds = [{"champ": str(c["champ"]), "op": str(c["op"]), "val": float(c["val"])} for c in i["conditions"][:4]]
        except (KeyError, TypeError, ValueError):
            continue
        if conds and all(c["op"] in OPS and c["champ"].startswith(CHAMPS) for c in conds):
            out.append(json.dumps({"nom": str(i.get("nom", ""))[:60], "conditions": conds}, ensure_ascii=False,
                                  sort_keys=True))
    return out


def entre(rule, r):
    if r.get("age_h") is None or r["age_h"] > rule["age_max_h"]:
        return False
    pc = (r.get("variation_prix_pct") or {}).get("h1")
    if rule["prix_1h"] == "baisse" and not (pc is not None and pc < 0):
        return False
    if rule["prix_1h"] == "hausse" and not (pc is not None and pc > 0):
        return False
    h1 = (r.get("transactions") or {}).get("h1") or {}
    if rule["acheteurs_1h"] == "plus" and not h1.get("buyers", 0) > h1.get("sellers", 0):
        return False
    if rule["classe"] == "oui" and not r.get("classe"):
        return False
    if rule.get("idee"):
        for c in json.loads(rule["idee"])["conditions"]:
            v = champ(r, c["champ"])
            if v is None or not OPS[c["op"]](v, c["val"]):
                return False
    return not r.get("essouffle")


def couts(liq):
    imp = min(TICKET / max((liq or 0) / 2, 1.0), 0.95)
    return 2 * (0.0045 + imp) + 0.01


def sortie(rule, prix0, bougies, t0):
    """bougies : [(ts, close)] triées ; renvoie le rendement brut (avant frais)."""
    fin = t0 + rule["duree_max_h"] * 3600
    last = prix0
    for ts, c in bougies:
        if ts <= t0:
            continue
        if ts > fin:
            break
        last = c
        x = c / prix0 - 1
        if x <= rule["stop"] or x >= rule["objectif"]:
            return x
    return last / prix0 - 1


def charger(path, since):
    rows = []
    with open(path) as f:
        for ln in f:
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if r.get("t", 0) >= since and r.get("prix"):
                rows.append(r)
    rows.sort(key=lambda r: r["t"])
    return rows


def bougies(pool, cache_dir, get, now, recent=True):
    """Historique 5 min d'un pool, mis en cache ; complété toutes les 50 min tant que le pool est récent (vu dans
    les dernières 26 h), sinon une fois pour toutes."""
    f = cache_dir / f"{pool}.json"
    old = json.loads(f.read_text()) if f.exists() else {"t": 0, "c": []}
    if (recent and now - old["t"] > 50 * 60) or not old["c"]:
        try:
            d = get(f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{pool}/ohlcv/minute"
                    f"?aggregate=5&limit=1000&currency=usd")
            new = [(int(x[0]), float(x[4])) for x in d["data"]["attributes"]["ohlcv_list"]]
            merged = dict(map(tuple, old["c"]))
            merged.update(new)
            old = {"t": now, "c": sorted(merged.items())}
            f.write_text(json.dumps(old))
        except Exception:
            pass
    return old["c"]


ENTREE = ("age_max_h", "prix_1h", "acheteurs_1h", "classe", "idee")


def entrees(rule, rows, paths):
    out, last = [], {}
    for r in rows:
        if r["t"] - last.get(r["token"], -1e18) < 24 * 3600 or not paths.get(r["pool"]) or not entre(rule, r):
            continue
        last[r["token"]] = r["t"]
        out.append(r)
    return out


def trades(rule, rows, paths, until, cache=None):
    key = tuple(rule.get(k) for k in ENTREE)
    if cache is None or key not in cache:
        ent = entrees(rule, rows, paths)
        if cache is None:
            cache = {}
        cache[key] = ent
    return [(r["t"], sortie(rule, r["prix"], paths[r["pool"]], r["t"]) - couts(r.get("liquidite")))
            for r in cache[key] if r["t"] <= until - rule["duree_max_h"] * 3600]  # trades terminés seulement


def stats(xs):
    n = len(xs)
    if n < 2:
        return {"n": n, "m": xs[0] if xs else None, "bas": None}
    m = sum(xs) / n
    se = (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5 / n ** 0.5
    return {"n": n, "m": round(m, 4), "bas": round(m - 2 * se, 4)}


def apprendre(out_dir, get, now):
    path = out_dir / "univers.jsonl"
    if not path.exists():
        return {"t": now, "regle": None, "raison": "pas encore de données collectées"}
    rows = charger(path, now - 21 * 86400)
    # les prix 5 min sont relevés dès le premier jour (GeckoTerminal n'en garde qu'environ 3 jours), même si la
    # règle attend MIN_JOURS de collecte : l'IA chercheuse en a besoin pour son banc d'essai
    cache = out_dir / "ohlcv"
    cache.mkdir(exist_ok=True)
    seen = {}
    for r in rows:
        seen[r["pool"]] = r["t"]
    paths = {p: bougies(p, cache, get, now, now - t < 26 * 3600) for p, t in sorted(seen.items())}
    if not rows or now - rows[0]["t"] < MIN_JOURS * 86400:
        return {"t": now, "regle": None, "raison": f"moins de {MIN_JOURS} jours de collecte"}
    split = now - TEST_JOURS * 86400
    idees = lire_idees()
    grille = regles(idees)
    train_rows, cache = [r for r in rows if r["t"] < split], {}
    best = None
    for rule in grille:
        tr = trades(rule, train_rows, paths, split, cache)
        s = stats([x for _, x in tr])
        if s["n"] >= MIN_TRAIN and s["bas"] is not None and s["bas"] > 0 and (best is None or s["bas"] > best[1]["bas"]):
            best = (rule, s)
    if best is None:
        return {"t": now, "regle": None, "raison": "aucune règle n'a une borne basse positive sur l'apprentissage",
                "regles_testees": len(grille), "idees_ia": len(idees)}
    te = stats([x for _, x in trades(best[0], [r for r in rows if r["t"] >= split], paths, now)])
    ok = te["n"] >= MIN_TEST and te["m"] is not None and te["m"] > 0
    return {"t": now, "regle": best[0] if ok else None, "apprentissage": best[1], "verification": te,
            "regles_testees": len(grille), "idees_ia": len(idees),
            "raison": "retenue" if ok else "meilleure règle du passé perdante ou trop rare sur les 2 derniers jours"}


# ------------------------------------------------------------------ caisse « ia » : règle écrite par l'IA chercheuse
IA_URL = ("https://raw.githubusercontent.com/liitlec/Copybot-Crypto/claude/polymarket-weather-sigma-resolution-olv0bs/"
          "copy_sim/memes/ia/regle.json")
BORNES = {"stop": (-0.9, -0.03), "objectif": (0.03, 20.0), "suiveur": (0.03, 0.9), "duree_max_h": (0.25, 72.0)}


def regle_ia(raw):
    """Valide la règle écrite par l'IA (memes/ia/regle.json). C'est une donnée : seuls ces champs, bornés, sont lus ;
    la taille (6 % de la caisse, 2 % de la liquidité au plus) n'est pas entre ses mains. None si invalide."""
    try:
        conds = [{"champ": str(c["champ"]), "op": str(c["op"]), "val": float(c["val"])}
                 for c in raw["entree"]["conditions"][:8]]
        if not all(c["op"] in OPS and c["champ"].startswith(CHAMPS) for c in conds):
            return None
        sx = raw["sortie"]
        out = {"version": int(raw["version"]), "pause": bool(raw.get("pause", False)), "conditions": conds,
               "pourquoi": str(raw.get("pourquoi", ""))[:300],
               "tri": str(raw.get("classement", {}).get("champ", "score")),
               "tri_desc": raw.get("classement", {}).get("ordre", "desc") != "asc",
               "max_positions": max(1, min(10, int(raw.get("max_positions", 10)))),
               "sortie_volume": bool(sx.get("sortie_volume", False))}
        if not out["tri"].startswith(CHAMPS):
            return None
        for k, (lo, hi) in BORNES.items():
            v = sx.get(k)
            out[k] = None if v is None else min(max(float(v), lo), hi)
        if out["stop"] is None or out["duree_max_h"] is None:
            return None
        return out
    except (KeyError, TypeError, ValueError):
        return None


def lire_regle_ia(url=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(url or IA_URL, headers={"User-Agent": "memes-paper/1.0"}),
                                    timeout=20) as f:
            return regle_ia(json.load(f))
    except Exception:
        return None


def entre_ia(rule, r):
    if r.get("essouffle"):
        return False
    for c in rule["conditions"]:
        v = champ(r, c["champ"])
        if v is None or not OPS[c["op"]](v, c["val"]):
            return False
    return True


def sortir_ia(rule, x, pic, age_h, essouffle):
    """x = variation depuis l'achat, pic = plus haut vu depuis l'achat (en variation). Raison de sortie, ou None."""
    if x <= rule["stop"]:
        return f"stop {x:+.0%}"
    if rule["objectif"] is not None and x >= rule["objectif"]:
        return f"objectif {x:+.0%}"
    if rule["suiveur"] is not None and pic > 0 and (1 + x) <= (1 + pic) * (1 - rule["suiveur"]):
        return f"stop suiveur {x:+.0%} (plus haut {pic:+.0%})"
    if age_h >= rule["duree_max_h"]:
        return f"durée max {x:+.0%}"
    if rule["sortie_volume"] and essouffle:
        return f"volume essoufflé {x:+.0%}"
    return None


def resultats_candidats(out_dir, get, now, jours=14):
    """Pour chaque dossier quotidien de l'IA (candidats/AAAA-MM-JJ.json) : ce que chaque candidat a fait ensuite
    (cours de clôture 5 min, avant frais). Publié dans resultats_candidats.json pour que l'IA apprenne de ses choix."""
    d = out_dir / "candidats"
    if not d.exists():
        return
    cache = out_dir / "ohlcv"
    cache.mkdir(exist_ok=True)
    res = {}
    for f in sorted(d.glob("*.json"))[-jours:]:
        snap = json.loads(f.read_text())
        t0, day = snap["t"], {}
        for c in snap["candidats"]:
            path = [(ts, px) for ts, px in bougies(c["pool"], cache, get, now, now - t0 < 26 * 3600) if ts > t0]
            if not path or not c.get("prix"):
                day[c["token"]] = {"nom": c.get("nom"), "rang": c.get("rang"), "donnees": "aucune"}
                continue
            def at(h):
                xs = [px for ts, px in path if ts <= t0 + h * 3600]
                return round(xs[-1] / c["prix"] - 1, 3) if xs and now - t0 >= h * 3600 else None
            day24 = [px for ts, px in path if ts <= t0 + 86400]
            day[c["token"]] = {"nom": c.get("nom"), "rang": c.get("rang"), "1h": at(1), "4h": at(4), "24h": at(24),
                               "max_24h": round(max(day24) / c["prix"] - 1, 3),
                               "min_24h": round(min(day24) / c["prix"] - 1, 3)}
        res[snap["date"]] = day
    (out_dir / "resultats_candidats.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":  # essai manuel : python3 apprend.py DOSSIER_DATA
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from memes_paper import get
    print(json.dumps(apprendre(Path(sys.argv[1]), get, time.time()), ensure_ascii=False, indent=1))
