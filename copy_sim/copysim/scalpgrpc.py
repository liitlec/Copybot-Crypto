"""Scalp pump.fun A / B rejoué EXACTEMENT comme sur le PC (nuit/scalp.py, nuit/scalp_regle.py, nuit/scalp_live.py,
prereg/scalp_rule.json du 15/10, repris tels quels depuis l'historique de la session du PC), sur les données du hub
gRPC du cloud (data_grpc/pumpfun.jsonl). Aucune transaction : on rejoue l'état exact des courbes enregistrées."""
from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev

# --- nuit/scalp.py (constantes et formules de courbe)
FEE = 0.0125
SIZE = 0.1
BASE_COST = 0.000105  # signature + petite priority fee, par transaction
V_SOL0, V_TOK0 = 30.0, 1_073_000_000.0
K = V_SOL0 * V_TOK0
V_TOK_OFFSET = 1_073_000_000.0 - 1_000_000_000.0  # tokens virtuels − tokens réels (courbe pump.fun)


def tokens_for(v_tok, sol_in):
    v_sol = K / v_tok
    return v_tok - K / (v_sol + sol_in * (1 - FEE))


def sol_for(v_tok, tokens):
    v_sol = K / v_tok
    return (v_sol - K / (v_tok + tokens)) * (1 - FEE)


# --- nuit/scalp_regle.py
ENTRY_S, HOLD_S, MAX_SOL = 1.0, 60.0, 0.5
CREATE_RENT = 0.03  # dépense du créateur hors achat (comptes, métadonnées), estimation prudente


def launches(path: Path, since: float = 0.0):
    creates, acc2c, rows = [], {}, defaultdict(list)
    for l in path.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        try:
            r = json.loads(l)
        except ValueError:
            continue
        if r["kind"] == "create":
            if r["bt"] < since:
                continue
            creates.append(r)
            for a in set(r.get("accs") or []) | {r["mint"]}:
                acc2c.setdefault(a, len(creates) - 1)
        else:
            k = acc2c.get(r["mint"])
            if k is not None:
                rows[k].append(r)
    out = []
    for k, c in enumerate(creates):
        rs = sorted(rows[k], key=lambda r: (r["slot"], r["idx"]))
        if any(r.get("quote") != "sol" for r in rs):
            continue  # coté dans un autre token
        rs = [r for r in rs if r.get("vault_tok")]
        for r in rs:
            r["v_tok"] = r["vault_tok"] + V_TOK_OFFSET
        out.append((c, rs))
    return out


def evaluate(c, rs, entry_s=ENTRY_S, hold_s=HOLD_S, max_sol=MAX_SOL):
    """None si la règle n'achète pas ; sinon le rendement net."""
    t_in = c["bt"] + entry_s
    if any(r["slot"] == c["slot"] and r["kind"] == "buy" for r in rs):
        return None  # bundle du créateur
    before = [r for r in rs if r["bt"] <= t_in]
    after = [r for r in rs if r["bt"] > t_in]
    if before:
        v_in = before[-1]["v_tok"]
    elif after:
        v_in = after[0]["v_tok"] + after[0]["curve_tok"]  # état juste avant le 1er trade = état à +entry_s
    else:  # aucun trade : courbe après le seul achat du créateur (estimé depuis sa dépense)
        dev = max(-c.get("signer_sol", 0.0) - CREATE_RENT, 0.0)
        v_in = V_TOK0 - tokens_for(V_TOK0, dev) if dev > 0 else V_TOK0
    if K / v_in - V_SOL0 >= max_sol:
        return None
    tok = tokens_for(v_in, SIZE)
    exit_rows = [r for r in rs if r["bt"] <= t_in + hold_s]
    v_out = exit_rows[-1]["v_tok"] if exit_rows and exit_rows[-1]["bt"] > t_in else v_in
    if exit_rows and exit_rows[-1]["bt"] <= t_in:
        v_out = v_in
    return (sol_for(v_out, tok) - BASE_COST) / (SIZE + BASE_COST) - 1


def entry_state(c, rs, t_in):
    """État de la courbe (v_tok) à l'entrée, calculé comme dans evaluate()."""
    before = [r for r in rs if r["bt"] <= t_in]
    after = [r for r in rs if r["bt"] > t_in]
    if before:
        return before[-1]["v_tok"]
    if after:
        return after[0]["v_tok"] + after[0]["curve_tok"]
    dev = max(-c.get("signer_sol", 0.0) - CREATE_RENT, 0.0)
    return V_TOK0 - tokens_for(V_TOK0, dev) if dev > 0 else V_TOK0


def evaluate_c(c, rs, entry_s, max_sol, base_hold_s, keep_if, trail, max_hold_s):
    """Règle C (cloud, 16/10) : entrée de B ; à base_hold_s, revente si le gain < keep_if (comme B), sinon on garde
    et on revend dès que la valeur retombe de `trail` sous son plus haut, au plus tard à max_hold_s."""
    t_in = c["bt"] + entry_s
    if any(r["slot"] == c["slot"] and r["kind"] == "buy" for r in rs):
        return None
    v_in = entry_state(c, rs, t_in)
    if K / v_in - V_SOL0 >= max_sol:
        return None
    tok = tokens_for(v_in, SIZE)
    ret = lambda v: (sol_for(v, tok) - BASE_COST) / (SIZE + BASE_COST) - 1  # noqa: E731
    first = [r for r in rs if t_in < r["bt"] <= t_in + base_hold_s]
    v60 = first[-1]["v_tok"] if first else v_in
    if ret(v60) < keep_if:
        return ret(v60)
    peak = ret(v60)
    last = v60
    for r in rs:
        if not t_in + base_hold_s < r["bt"] <= t_in + max_hold_s:
            continue
        x = ret(r["v_tok"])
        last = r["v_tok"]
        if x <= (1 + peak) * (1 - trail) - 1:
            return x
        peak = max(peak, x)
    return ret(last)


# règle C figée le 16/10 dans prereg/scalp_rule_c.json (avant toute évaluation) : évaluée sur les lancements postérieurs
REGLE_C = {"nom": "C : entrée de B, gardée au-delà de 60 s si ≥ +20 %, stop suiveur −30 %, max 9 min",
           "entree_s": 5.0, "min_acheteurs": 1, "max_sol_courbe": 2.5, "base_s": 60.0, "garder_si": 0.20,
           "stop_suiveur": 0.30, "max_s": 540.0}
VERDICT_C = ("après au moins 1 000 trades de C : gagnant seulement si la moyenne dépasse 2 fois sa marge d'erreur, "
             "reste positive sans les 3 meilleurs trades ET bat B sur les mêmes lancements")


# --- prereg/scalp_rule.json du PC (variantes figées le 15/10 à 20:17)
VARIANTES = [
    {"nom": "B confirmé : +5 s, au moins 1 autre acheteur", "entree_s": 5.0, "vente_s": 60.0, "min_acheteurs": 1,
     "max_sol_courbe": 2.5},
    {"nom": "A brut : +1 s, sans confirmation", "entree_s": 1.0, "vente_s": 60.0, "min_acheteurs": 0,
     "max_sol_courbe": 0.5},
]
VERDICT = ("après au moins 1 000 trades de B : gagnant seulement si la moyenne dépasse 2 fois sa marge d'erreur "
           "ET reste positive sans les 3 meilleurs trades")


# --- nuit/scalp_live.py
def confirmed(c, rs, entry_s, n):
    buyers = {r["signer"] for r in rs
              if r["bt"] <= c["bt"] + entry_s and r["kind"] == "buy" and r["signer"] != c["signer"]}
    return len(buyers) >= n


def run_once(path: Path, start: float):
    L = launches(path, since=start)
    if not L:
        return None
    t_end = max(max([c["bt"]] + [r["bt"] for r in rs]) for c, rs in L)
    out = {}
    for v in VARIANTES:
        trades = []
        for c, rs in L:
            if t_end - c["bt"] < v["entree_s"] + v["vente_s"] + 30:
                continue  # fenêtre pas encore complète
            if v["min_acheteurs"] and not confirmed(c, rs, v["entree_s"], v["min_acheteurs"]):
                continue
            x = evaluate(c, rs, v["entree_s"], v["vente_s"], v["max_sol_courbe"])
            if x is not None:
                trades.append((c["bt"], c["mint"], x))
        out[v["nom"]] = sorted(trades)
    out.update(run_c(L, t_end))
    from .scoreD import run_d
    out.update(run_d(L, t_end))
    return out


def run_c(L, t_end, rule=None):
    """C et B sur les MÊMES lancements (postérieurs à la fixation de C) pour une comparaison directe."""
    v = rule or REGLE_C
    since = C_START_TS()
    c_tr, b_tr = [], []
    for c, rs in L:
        if c["bt"] < since or t_end - c["bt"] < v["entree_s"] + v["max_s"] + 30:
            continue  # fenêtre de 9 min pas encore complète
        if not confirmed(c, rs, v["entree_s"], v["min_acheteurs"]):
            continue
        x = evaluate_c(c, rs, v["entree_s"], v["max_sol_courbe"], v["base_s"], v["garder_si"], v["stop_suiveur"],
                       v["max_s"])
        if x is not None:
            c_tr.append((c["bt"], c["mint"], x))
            b_tr.append((c["bt"], c["mint"], evaluate(c, rs, v["entree_s"], v["base_s"], v["max_sol_courbe"])))
    return {v["nom"]: sorted(c_tr), "B sur les mêmes lancements que C": sorted(b_tr)}


def C_START_TS() -> float:  # noqa: N802
    p = Path(__file__).resolve().parents[1] / "prereg" / "scalp_rule_c.json"
    return json.loads(p.read_text(encoding="utf-8"))["debut_ts"] if p.exists() else float("inf")


def report(out, start: float) -> str:
    lines = [f"_Mis à jour : {time.strftime('%Y-%m-%d %H:%M:%S')} — test démarré le "
             f"{time.strftime('%d/%m %H:%M', time.localtime(start))} (cloud, hub gRPC Chainstack), règles du PC "
             "(prereg/scalp_rule.json du 15/10)_", "",
             "Paper trading : état exact des courbes pump.fun enregistré en gRPC, mise 0.1 SOL par trade, frais pump.fun "
             "1.25 % par côté. Les lancements que personne n'achète ensuite sont comptés.", "",
             "| variante | trades | moyenne / trade | ± | gagnants | total SOL | sans les 3 meilleurs |",
             "|---|---|---|---|---|---|---|"]
    names = [v["nom"] for v in VARIANTES] + [REGLE_C["nom"], "B sur les mêmes lancements que C"]
    names += [k for k in out if k.startswith("D ")] + ["même sélection, revente à 60 s", "tous les lancements, sortie C"]
    for name in names:
        r = [x for *_, x in out.get(name, []) if x is not None]
        if len(r) >= 2:
            srt = sorted(r, reverse=True)
            lines.append(f"| {name} | {len(r)} | {mean(r):+.2%} | {pstdev(r) / len(r) ** .5:.2%} | "
                         f"{sum(x > 0 for x in r) / len(r):.0%} | {sum(r) * SIZE:+.3f} | "
                         f"{mean(srt[3:]) if len(srt) > 3 else 0:+.2%} |")
        else:
            lines.append(f"| {name} | {len(r)} | — | — | — | — | — |")
    lines += ["", f"Verdict prévu (A, B) : {VERDICT}",
              f"Verdict prévu (C) : {VERDICT_C}", "",
              "C n'est compté que sur les lancements postérieurs à sa fixation (prereg/scalp_rule_c.json), avec 9 min "
              "de suivi complètes ; la ligne « B sur les mêmes lancements » sert de comparaison directe.", "",
              "## 15 derniers trades (variante principale)", "",
              "| heure | token | résultat |", "|---|---|---|"]
    for bt, mint, x in out.get(VARIANTES[0]["nom"], [])[-15:][::-1]:
        lines.append(f"| {time.strftime('%H:%M:%S', time.localtime(bt))} | {mint[:4]}…{mint[-4:]} | {x:+.1%} |")
    return "\n".join(lines) + "\n"
