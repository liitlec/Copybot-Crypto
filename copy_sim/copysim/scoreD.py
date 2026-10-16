"""Règle D (figée le 16/10, prereg/scalp_rule_d.json) : sélection par le score de qualité du PC (nuit/scalp_score.py)
+ sortie de C. Évaluée uniquement sur les lancements créés après sa fixation, et de façon causale :
- le score est réappris toutes les 30 min, uniquement sur les lancements dont les 10 min de suivi étaient finies ;
- seuil = 80e centile des scores de cet apprentissage (on garde les 20 % meilleurs) ;
- achat à +5 s (comme le score), revente comme C (≥ +20 % à 60 s -> on garde, stop suiveur −30 %, max 9 min).
Comparaison sur les mêmes lancements : même sélection revendue à 60 s, et tous les lancements avec la sortie C."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULE_PATH = ROOT / "prereg" / "scalp_rule_d.json"


def _score_mod():
    sys.path.insert(0, str(ROOT / "nuit"))
    import scalp_score  # noqa: E402  (code du PC, chemins data_grpc/)
    return scalp_score


def run_d(L, t_end):
    """Retourne {nom: [(bt, mint, rendement), ...]} pour D et ses deux comparaisons."""
    from .scalpgrpc import evaluate, evaluate_c
    if not RULE_PATH.exists():
        return {}
    rule = json.loads(RULE_PATH.read_text(encoding="utf-8"))
    start, q, refit = rule["debut_ts"], rule["quantile"], rule["reapprentissage_s"]
    S = _score_mod()
    enrich = {}
    p = ROOT / "data_grpc" / "pump_enrich.jsonl"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if "tx_err" not in r:
                enrich[r["sig"]] = r
    rows = S.build(L, enrich)  # variables connues à +5 s (historique strictement passé)
    byc = {(c["bt"], c["mint"]): (c, rs) for c, rs in L}
    models: dict[int, tuple] = {}
    out = {rule["nom"]: [], "même sélection, revente à 60 s": [], "tous les lancements, sortie C": []}
    for r in rows:
        if r["bt"] < start or not r["enriched"]:
            continue
        c, rs = byc[(r["bt"], r["mint"])]
        if t_end - c["bt"] < 5.0 + 540.0 + 30:
            continue  # suivi de 9 min pas encore complet
        k = int((r["bt"] + 5.0) // refit)
        if k not in models:
            cutoff = k * refit
            train = [x for x in rows if x["enriched"] and x["bt"] + 600 <= cutoff]
            if len(train) < 400:
                models[k] = None
            else:
                sc = S.Scorecard().fit(train)
                scores = sorted(sc.score(x["f"]) for x in train)
                models[k] = (sc, scores[int(q * (len(scores) - 1))])
        xc = evaluate_c(c, rs, 5.0, 1e9, 60.0, 0.20, 0.30, 540.0)
        if xc is None:
            continue
        out["tous les lancements, sortie C"].append((c["bt"], c["mint"], xc))
        m = models[k]
        if m is None or m[0].score(r["f"]) < m[1]:
            continue
        out[rule["nom"]].append((c["bt"], c["mint"], xc))
        out["même sélection, revente à 60 s"].append((c["bt"], c["mint"], evaluate(c, rs, 5.0, 60.0, 1e9)))
    return out
