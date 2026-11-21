"""Évaluation hors ligne des règles de copie pré-enregistrées (prereg/copy_rules.json) sur les trades
réellement simulés en live et sur les cotations enregistrées (price_paths.jsonl). On compare toujours au
PnL de la copie simple, sur les mêmes trades."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


def load_paths(path: Path) -> dict[tuple, list[tuple[float, float, float]]]:
    """(leader, mint, opened_ts arrondi) -> [(age_s, ret_vs_cost, sell_value_sol), ...] triés."""
    out: dict[tuple, list] = defaultdict(list)
    if not path.exists():
        return out
    for line in path.open(encoding="utf-8"):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("ret_vs_cost") is not None:
            out[(r["leader"], r["mint"], round(r["opened_ts"]))].append((r["age_s"], r["ret_vs_cost"],
                                                                           r["sell_value_sol"]))
    for v in out.values():
        v.sort()
    return out


def r1_delta(t: dict, seuil: float) -> float:
    """R1 : le trade n'aurait pas eu lieu -> on retire son PnL."""
    es = t.get("entry_slippage")
    return -t["pnl_sol"] if es is not None and es > seuil else 0.0


def r2_delta(t: dict, path: list, seuil: float, frac: float, bot_fee_pct: float, tx_fee: float) -> float:
    """R2 : vente de `frac` au premier point ≥ seuil (cotation de la ligne entière, donc prudente)."""
    hit = next((p for p in path if p[1] >= seuil), None)
    if not hit:
        return 0.0
    early = frac * hit[2] * (1 - bot_fee_pct / 100) - tx_fee
    rest = (1 - frac) * t["proceeds_sol"]
    return early + rest - t["proceeds_sol"]


def r3_delta(t: dict, trades: list[dict], fenetre: float, mult: float) -> float:
    """R3 : mise multipliée si un autre leader du test a acheté le même token à moins de `fenetre` s."""
    other = any(o is not t and o["mint"] == t["mint"] and o["leader"] != t["leader"]
                and abs(o["opened_ts"] - t["opened_ts"]) <= fenetre for o in trades)
    return (mult - 1) * t["pnl_sol"] if other else 0.0


def evaluate(trades: list[dict], paths: dict, pre: dict, bot_fee_pct: float, tx_fee: float) -> dict:
    R = pre["regles"]
    rows = {"base": [], "R1": [], "R2": [], "R3": []}
    for t in trades:
        key = (t["leader"], t["mint"], round(t["opened_ts"]))
        rows["base"].append(t["pnl_sol"])
        rows["R1"].append(r1_delta(t, R["R1_prix_entree_max"]["seuil_entry_slippage"]))
        rows["R2"].append(r2_delta(t, paths.get(key, []), R["R2_moitie_a_plus_50"]["seuil_ret_vs_cost"],
                                   R["R2_moitie_a_plus_50"]["fraction_vendue"], bot_fee_pct, tx_fee))
        rows["R3"].append(r3_delta(t, trades, R["R3_confluence"]["fenetre_s"], R["R3_confluence"]["multiplicateur"]))
    half = len(trades) // 2
    out = {"n": len(trades), "base": sum(rows["base"]), "with_path": sum(1 for t in trades
           if paths.get((t["leader"], t["mint"], round(t["opened_ts"]))))}
    for k in ("R1", "R2", "R3"):
        d = rows[k]
        out[k] = {"delta": sum(d), "h1": sum(d[:half]), "h2": sum(d[half:]), "touches": sum(1 for x in d if x)}
    return out


def closed_trades(state_path: Path, since_ts: float) -> list[dict]:
    st = json.loads(state_path.read_text(encoding="utf-8"))
    st = st.get("engine", st)
    t = [c for c in st["closed"] if not c.get("still_open") and c["opened_ts"] > since_ts]
    return sorted(t, key=lambda c: c["opened_ts"])


def render(results: dict[str, dict], pre: dict) -> str:
    k = pre["criteres_de_reussite"]
    md = [f"# Règles de copie pré-enregistrées", "", f"Fixées le {pre['fixee_le_utc']} UTC ; évaluées uniquement "
          "sur les trades ouverts après. Écart de PnL (SOL) par rapport à la copie simple, sur les mêmes trades.", "",
          "| test | trades | PnL copie simple | R1 prix d'entrée max | R2 moitié à +50 % | R3 confluence |",
          "|---|---|---|---|---|---|"]
    verdicts = []
    for name, r in results.items():
        if not r["n"]:
            md.append(f"| {name} | 0 | - | - | - | - |")
            continue
        cell = lambda x: f"{x['delta']:+.4f} ({x['touches']} trades ; {x['h1']:+.4f} / {x['h2']:+.4f})"
        md.append(f"| {name} | {r['n']} | {r['base']:+.4f} | {cell(r['R1'])} | {cell(r['R2'])} | {cell(r['R3'])} |")
        for rule in ("R1", "R2", "R3"):
            x = r[rule]
            if r["n"] < k["trades_min"]:
                v = f"⏳ {r['n']}/{k['trades_min']} trades"
            else:
                v = "✅ validée" if x["delta"] > 0 and x["h1"] > 0 and x["h2"] > 0 else "❌ rejetée"
            verdicts.append(f"- {name} / {rule} : {v}")
    md += ["", "Entre parenthèses : trades concernés ; écart sur la 1re / 2e moitié chronologique.", "",
           f"Critères : ≥ {k['trades_min']} trades, amélioration du PnL total et sur chaque moitié.", ""] + verdicts
    md += ["", "R2 n'est évaluable que sur les trades qui ont des cotations enregistrées (--record-paths).", ""]
    return "\n".join(md)
