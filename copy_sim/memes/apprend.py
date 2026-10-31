"""Caisse « auto » : une règle d'entrée et de sortie réapprise chaque jour sur les données collectées (univers.jsonl),
choisie uniquement sur le passé et vérifiée sur les 2 derniers jours avant d'être utilisée.

Chaque jour (00:30 UTC environ, dans la boucle du VPS) :
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
résultat de la caisse après chaque choix : il porte sur des jours que la règle n'avait pas vus."""
import itertools
import json
import os
import time
from pathlib import Path

GRILLE = {
    "age_max_h": (2, 12, 72),
    "prix_1h": ("tout", "baisse", "hausse"),        # variation du prix sur 1 h au moment de l'achat
    "acheteurs_1h": ("tout", "plus"),               # plus d'acheteurs distincts que de vendeurs sur 1 h
    "classe": ("tout", "oui"),                      # détenteurs plus vite que le prix (classement du post)
    "stop": (-0.15, -0.25),
    "objectif": (0.20, 0.40, 0.80),
    "duree_max_h": (1, 4),
}
TEST_JOURS, MIN_TRAIN, MIN_TEST, TICKET = 2, 30, 8, 300.0
MIN_JOURS = 3  # pas de règle avant 3 jours de collecte


def regles():
    keys = list(GRILLE)
    return [dict(zip(keys, v)) for v in itertools.product(*GRILLE.values())]


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


def bougies(pool, cache_dir, get, now):
    """Historique 5 min d'un pool, mis en cache et complété au plus une fois par jour."""
    f = cache_dir / f"{pool}.json"
    old = json.loads(f.read_text()) if f.exists() else {"t": 0, "c": []}
    if now - old["t"] > 20 * 3600:
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


def trades(rule, rows, paths, until):
    out, last = [], {}
    for r in rows:
        if r["t"] > until - rule["duree_max_h"] * 3600:  # trade pas encore terminé
            break
        if r["t"] - last.get(r["token"], -1e18) < 24 * 3600 or not entre(rule, r):
            continue
        c = paths.get(r["pool"])
        if not c:
            continue
        last[r["token"]] = r["t"]
        out.append((r["t"], sortie(rule, r["prix"], c, r["t"]) - couts(r.get("liquidite"))))
    return out


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
    rows = charger(path, now - 30 * 86400)
    if not rows or now - rows[0]["t"] < MIN_JOURS * 86400:
        return {"t": now, "regle": None, "raison": f"moins de {MIN_JOURS} jours de collecte"}
    cache = out_dir / "ohlcv"
    cache.mkdir(exist_ok=True)
    paths = {p: bougies(p, cache, get, now) for p in sorted({r["pool"] for r in rows})}
    split = now - TEST_JOURS * 86400
    best = None
    for rule in regles():
        tr = trades(rule, [r for r in rows if r["t"] < split], paths, split)
        s = stats([x for _, x in tr])
        if s["n"] >= MIN_TRAIN and s["bas"] is not None and s["bas"] > 0 and (best is None or s["bas"] > best[1]["bas"]):
            best = (rule, s)
    if best is None:
        return {"t": now, "regle": None, "raison": "aucune règle n'a une borne basse positive sur l'apprentissage",
                "regles_testees": len(regles())}
    te = stats([x for _, x in trades(best[0], [r for r in rows if r["t"] >= split], paths, now)])
    ok = te["n"] >= MIN_TEST and te["m"] is not None and te["m"] > 0
    return {"t": now, "regle": best[0] if ok else None, "apprentissage": best[1], "verification": te,
            "regles_testees": len(regles()),
            "raison": "retenue" if ok else "meilleure règle du passé perdante ou trop rare sur les 2 derniers jours"}


if __name__ == "__main__":  # essai manuel : python3 apprend.py DOSSIER_DATA
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from memes_paper import get
    print(json.dumps(apprendre(Path(sys.argv[1]), get, time.time()), ensure_ascii=False, indent=1))
