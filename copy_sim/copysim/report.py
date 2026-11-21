"""Statistiques et rapport markdown."""
from __future__ import annotations

from collections import defaultdict
from statistics import median

from .engine import EngineState
from .swaps import SwapEvent


def max_drawdown(curve: list[tuple[float, float]], start: float) -> float:
    peak, mdd = start, 0.0
    for _, eq in curve:
        peak = max(peak, eq)
        if peak > 0:
            mdd = max(mdd, 1 - eq / peak)
    return mdd


def stats(st: EngineState, bankroll: float) -> dict:
    realized = [c for c in st.closed if not c["still_open"]]
    still = [c for c in st.closed if c["still_open"]]
    wins = [c for c in realized if c["pnl_sol"] > 0]
    losses = [c for c in realized if c["pnl_sol"] <= 0]
    gross_w = sum(c["pnl_sol"] for c in wins)
    gross_l = -sum(c["pnl_sol"] for c in losses)
    slips = [c["entry_slippage"] for c in st.closed if c.get("entry_slippage") is not None]
    final = st.cash + sum(p["cost_sol"] - p["proceeds_sol"] for p in st.positions.values())
    by_leader: dict[str, list] = defaultdict(list)
    for c in realized:
        by_leader[c["leader"]].append(c)
    return {
        "bankroll": bankroll, "final_equity": final, "return": final / bankroll - 1,
        "n_closed": len(realized), "win_rate": len(wins) / len(realized) if realized else None,
        "avg_win": gross_w / len(wins) if wins else 0.0, "avg_loss": -gross_l / len(losses) if losses else 0.0,
        "profit_factor": gross_w / gross_l if gross_l > 0 else None,
        "worst": min((c["ret"] for c in realized), default=None),
        "max_drawdown": max_drawdown(st.equity_curve, bankroll),
        "median_entry_slippage": median(slips) if slips else None,
        "open_at_end": len(still), "open_value": sum(c["proceeds_sol"] for c in still),
        "open_no_price": sum(c["reason"].endswith("(compté 0)") for c in still),
        "skips": dict(sorted(st.skips.items(), key=lambda kv: -kv[1])),
        "rotations": len(st.rotations),
        "by_leader": {l: {"n": len(v), "wins": sum(c["pnl_sol"] > 0 for c in v),
                          "pnl": sum(c["pnl_sol"] for c in v)} for l, v in by_leader.items()},
    }


def leader_baseline(events: list[SwapEvent]) -> dict[str, dict]:
    """Résultat propre de chaque leader sur les tokens qu'il a achetés ET revendus (≥ 98 %) dans la fenêtre."""
    agg: dict[tuple, dict] = defaultdict(lambda: {"in": 0.0, "out": 0.0, "bought": 0.0, "sold": 0.0})
    for e in events:
        a = agg[(e.wallet, e.mint)]
        if e.side == "BUY":
            a["in"] += e.sol_amount
            a["bought"] += e.token_amount
        elif a["bought"] > 0:
            a["out"] += e.sol_amount
            a["sold"] += e.token_amount
    out: dict[str, dict] = defaultdict(lambda: {"n": 0, "wins": 0, "pnl": 0.0, "invested": 0.0})
    for (w, _), a in agg.items():
        if a["bought"] > 0 and a["sold"] >= 0.98 * a["bought"]:
            r = out[w]
            r["n"] += 1
            r["wins"] += a["out"] > a["in"]
            r["pnl"] += a["out"] - a["in"]
            r["invested"] += a["in"]
    return dict(out)


def _p(x) -> str:
    return "-" if x is None else f"{x:+.1%}" if abs(x) < 100 else f"{x:+.0f}x"


def short(addr: str) -> str:
    return f"{addr[:4]}…{addr[-4:]}"


def render(results: dict[str, dict], baseline: dict[str, dict] | None, meta: dict) -> str:
    md = [f"# Simulation copy trading — {meta.get('title', '')}", "",
          "Hypothèses : " + ", ".join(f"{k}={v}" for k, v in meta.get("assumptions", {}).items()), "",
          "## Résultat par scénario", "",
          "| scénario | capital final (SOL) | rendement | trades clos | win rate | gain moyen | perte moyenne | "
          "profit factor | drawdown max | slippage d'entrée médian vs leader | ouvertes à la fin |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, r in results.items():
        wr = "-" if r["win_rate"] is None else f"{r['win_rate']:.0%}"
        pf = "-" if r["profit_factor"] is None else f"{r['profit_factor']:.2f}"
        md.append(f"| {name} | {r['final_equity']:.3f} | {_p(r['return'])} | {r['n_closed']} | {wr} | "
                  f"{r['avg_win']:+.4f} | {r['avg_loss']:+.4f} | {pf} | {r['max_drawdown']:.0%} | "
                  f"{_p(r['median_entry_slippage'])} | {r['open_at_end']} ({r['open_no_price']} sans prix) |")
    md.append("")
    first = next(iter(results.values()), None)
    if first:
        md += ["## Trades ignorés (premier scénario)", ""]
        md += [f"- {k} : {v}" for k, v in first["skips"].items()] or ["- aucun"]
        md += ["", f"Rotations de leader : {first['rotations']}", ""]
        md += ["## Par leader (premier scénario)", "", "| leader | trades | gagnants | PnL SOL |", "|---|---|---|---|"]
        for l, v in first["by_leader"].items():
            md.append(f"| {short(l)} | {v['n']} | {v['wins']} | {v['pnl']:+.4f} |")
        md.append("")
    if baseline:
        md += ["## Résultat propre des leaders (sans copie, mêmes tokens)", "",
               "| leader | tokens achetés et revendus | gagnants | PnL SOL | investi SOL |", "|---|---|---|---|---|"]
        for l, v in baseline.items():
            md.append(f"| {short(l)} | {v['n']} | {v['wins']} | {v['pnl']:+.3f} | {v['invested']:.2f} |")
        md += ["", "Écart leader vs copieur = coût réel de la copie (retard, slippage, frais).", ""]
    md += ["## Comment lire", "",
           "- **neutral** et **pessimistic** encadrent la réalité ; si même *neutral* perd, la stratégie perd.",
           "- Un win rate élevé avec un profit factor < 1 = beaucoup de petits gains, quelques grosses pertes.",
           "- Le slippage d'entrée médian mesure combien plus cher que le leader on achète : c'est l'edge qu'il "
           "garde pour lui (et ce que les copieurs lui paient quand il revend).", ""]
    return "\n".join(md)
