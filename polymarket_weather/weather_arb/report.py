"""Rapport : win rate, PnL simulé (spread + slippage + frais), calibration, par ville/horizon."""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean

from .config import Settings
from .store import read_json, read_jsonl, write_json

BINS = [0.0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0001]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(c - h, 0.0), min(c + h, 1.0))


def brier(ps: list[float], ys: list[bool]) -> float:
    return fmean((p - y) ** 2 for p, y in zip(ps, ys)) if ps else float("nan")


def logloss(ps: list[float], ys: list[bool], eps: float = 1e-3) -> float:
    if not ps:
        return float("nan")
    return -fmean(math.log(min(max(p, eps), 1 - eps)) if y else math.log(1 - min(max(p, eps), 1 - eps))
                  for p, y in zip(ps, ys))


def reliability(ps: list[float], ys: list[bool], bins: list[float] = BINS) -> list[dict]:
    out = []
    for lo, hi in zip(bins, bins[1:]):
        idx = [i for i, p in enumerate(ps) if lo <= p < hi]
        if not idx:
            continue
        k = sum(ys[i] for i in idx)
        out.append({"bin": f"{lo:.2f}-{min(hi, 1):.2f}", "n": len(idx),
                    "p_mean": fmean(ps[i] for i in idx), "freq": k / len(idx),
                    "ci": wilson(k, len(idx))})
    return out


def trade_stats(trades: list[dict]) -> dict:
    n = len(trades)
    if n == 0:
        return {"n": 0}
    wins = sum(t["result"] == "WIN" for t in trades)
    staked = sum(t["stake_usd"] for t in trades)
    pnl = sum(t["pnl"] for t in trades)
    return {
        "n": n, "wins": wins, "win_rate": wins / n, "win_ci": wilson(wins, n),
        "expected_win_rate": fmean(t["p_side"] for t in trades),
        "market_implied": fmean(t["entry_price"] for t in trades),
        "pnl": pnl, "staked": staked, "roi": pnl / staked if staked else float("nan"),
        "fees": sum(t.get("fee_usd", 0) for t in trades),
        "brier_model": brier([t["p_side"] for t in trades], [t["result"] == "WIN" for t in trades]),
        "brier_market": brier([t["entry_price"] for t in trades], [t["result"] == "WIN" for t in trades]),
    }


def group(trades: list[dict], key) -> dict[str, dict]:
    g: dict[str, list] = defaultdict(list)
    for t in trades:
        g[str(key(t))].append(t)
    return {k: trade_stats(v) for k, v in sorted(g.items())}


def horizon_label(t: dict) -> str:
    d = t.get("lead_days", -1)
    return f"J+{d}" if d <= 3 else "J+4..7" if d <= 7 else "J+8+"


def prediction_stats(preds: list[dict]) -> dict:
    res = [p for p in preds if p.get("outcome_yes") is not None]
    with_mid = [p for p in res if p.get("mid") is not None]
    ys = [p["outcome_yes"] for p in with_mid]
    pm = [p["p_model"] for p in with_mid]
    pk = [min(max(p["mid"], 0.0), 1.0) for p in with_mid]
    err_by_lead: dict[int, list[float]] = defaultdict(list)
    for p in res:
        if p.get("forecast_error") is not None:
            # Une erreur par (station, jour, horizon) : dédoublonnage des tranches. Tout en °C.
            k = 5 / 9 if p.get("unit") == "F" else 1.0
            err_by_lead[p["lead_days"]].append((p["station_icao"], p["target_date"], p["forecast_error"] * k,
                                                p["sigma"] * k))
    errs = {}
    for lead, rows in sorted(err_by_lead.items()):
        uniq = {(a, b): (e, s) for a, b, e, s in rows}
        e = [v[0] for v in uniq.values()]
        s = [v[1] for v in uniq.values()]
        mean = fmean(e)
        sd = math.sqrt(fmean((x - mean) ** 2 for x in e)) if len(e) > 1 else float("nan")
        errs[lead] = {"n": len(e), "bias": mean, "sd": sd, "sigma_used": fmean(s)}
    return {
        "n_resolved": len(res), "n_with_price": len(with_mid),
        "brier_model": brier(pm, ys), "brier_market": brier(pk, ys),
        "logloss_model": logloss(pm, ys), "logloss_market": logloss(pk, ys),
        "reliability_model": reliability(pm, ys), "reliability_market": reliability(pk, ys),
        "forecast_errors": errs,
        "mismatches": sum(bool(p.get("obs_mismatch")) for p in res),
    }


# ---------------------------------------------------------------- rendu markdown

def _pct(x) -> str:
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.1%}"


def _table(groups: dict[str, dict], title: str) -> list[str]:
    lines = [f"### {title}", "", "| | n | win rate | attendu (modèle) | implicite (prix) | PnL $ | ROI |",
             "|---|---|---|---|---|---|---|"]
    for k, st in groups.items():
        if not st.get("n"):
            continue
        lines.append(f"| {k} | {st['n']} | {_pct(st['win_rate'])} | {_pct(st['expected_win_rate'])} | "
                     f"{_pct(st['market_implied'])} | {st['pnl']:+.2f} | {_pct(st['roi'])} |")
    return lines + [""]


def _rel_table(rows: list[dict], title: str) -> list[str]:
    lines = [f"### {title}", "", "| tranche de proba | n | proba moyenne | fréquence observée | IC 95 % |",
             "|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['bin']} | {r['n']} | {_pct(r['p_mean'])} | {_pct(r['freq'])} | "
                     f"{_pct(r['ci'][0])} – {_pct(r['ci'][1])} |")
    return lines + [""]


def build_report(s: Settings) -> tuple[str, dict]:
    trades = read_json(s.trades_path, [])
    preds = read_jsonl(s.predictions_path)
    done = [t for t in trades if t.get("result")]
    official = [t for t in done if t.get("resolution_method") == "polymarket"]
    overall = trade_stats(done)
    data = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "assumptions": {"fee_rate": s.fee_rate, "slippage": s.slippage, "stake_usd": s.stake_usd,
                        "min_edge": s.min_edge, "max_spread": s.max_spread},
        "counts": {"trades": len(trades), "resolved": len(done), "official": len(official),
                   "provisional": len(done) - len(official),
                   "open": sum(t.get("status") == "OPEN" for t in trades),
                   "mismatches": sum(bool(t.get("obs_mismatch")) for t in done)},
        "overall": overall,
        "by_city": group(done, lambda t: t["city"]),
        "by_horizon": group(done, horizon_label),
        "by_side": group(done, lambda t: t["side"]),
        "by_model": group(done, lambda t: t["model"]),
        "by_p_bin": group(done, lambda t: f"{math.floor(t['p_side'] * 10) / 10:.1f}"),
        "reliability_trades": reliability([t["p_side"] for t in done], [t["result"] == "WIN" for t in done]),
        "predictions": prediction_stats(preds),
    }

    c, o = data["counts"], overall
    md = [f"# Rapport paper trading météo — {data['generated']}", "",
          f"Hypothèses : frais {s.fee_rate:.1%} du notionnel, slippage {s.slippage:.2f} $/part au-dessus du "
          f"best ask, mise {s.stake_usd:.0f} $, edge min {s.min_edge:.0%} (après coûts).", "",
          "## Synthèse", "",
          f"- Trades : {c['trades']} (résolus {c['resolved']} dont officiels {c['official']}, "
          f"provisoires {c['provisional']}, ouverts {c['open']})",
          f"- Désaccords résolution officielle vs METAR : **{c['mismatches']}** "
          "(> 0 = bug station/unité/bornes à investiguer)"]
    if o.get("n"):
        lo, hi = o["win_ci"]
        md += [f"- Win rate : **{_pct(o['win_rate'])}** (IC 95 % {_pct(lo)} – {_pct(hi)})",
               f"- Win rate attendu par le modèle : {_pct(o['expected_win_rate'])} ; "
               f"implicite dans le prix payé : {_pct(o['market_implied'])}",
               f"- PnL : **{o['pnl']:+.2f} $** sur {o['staked']:.0f} $ engagés (ROI {_pct(o['roi'])}), "
               f"frais {o['fees']:.2f} $",
               f"- Brier (côté joué) modèle {o['brier_model']:.4f} vs marché {o['brier_market']:.4f} "
               "(plus bas = mieux)", ""]
        verdict = []
        if o["n"] < 100:
            verdict.append(f"Échantillon trop faible (n={o['n']}) : aucune conclusion statistique.")
        if o["expected_win_rate"] - o["win_rate"] > 0.10:
            verdict.append("Le modèle surestime nettement ses chances : **surconfiance** (sigma trop "
                           "faible, biais station, ou tranches mal interprétées).")
        if o["brier_model"] > o["brier_market"]:
            verdict.append("Le prix du marché prédit mieux que le modèle sur les trades pris.")
        if lo > o["market_implied"]:
            verdict.append("Win rate significativement au-dessus du prix payé : edge plausible, à confirmer.")
        md += ["**Lecture :** " + " ".join(verdict) if verdict else "", ""]
    md += _table(data["by_horizon"], "Par horizon")
    md += _table(data["by_city"], "Par ville")
    md += _table(data["by_side"], "Par côté")
    md += _table(data["by_p_bin"], "Par probabilité modèle (côté joué)")
    md += _rel_table(data["reliability_trades"], "Fiabilité — trades pris (biais de sélection !)")

    p = data["predictions"]
    md += ["## Calibration sur TOUS les marchés scannés (journal de prédictions)", "",
           f"Marchés résolus : {p['n_resolved']} (avec prix : {p['n_with_price']}).", "",
           f"- Brier modèle {p['brier_model']:.4f} vs marché {p['brier_market']:.4f}",
           f"- Log-loss modèle {p['logloss_model']:.4f} vs marché {p['logloss_market']:.4f}", ""]
    md += _rel_table(p["reliability_model"], "Fiabilité du modèle")
    md += _rel_table(p["reliability_market"], "Fiabilité du marché (mid)")
    md += ["### Erreur de prévision réelle vs sigma utilisé", "",
           "| horizon | n jours-station | biais °C (obs - prévision) | écart-type réel °C | sigma utilisé °C |",
           "|---|---|---|---|---|"]
    for lead, e in p["forecast_errors"].items():
        md.append(f"| J+{lead} | {e['n']} | {e['bias']:+.2f} | {e['sd']:.2f} | {e['sigma_used']:.2f} |")
    md += ["", "Si l'écart-type réel dépasse nettement le sigma utilisé, relancer `calibrate`.", ""]
    mism = [t for t in done if t.get("obs_mismatch")]
    if mism:
        md += ["## Désaccords à investiguer", "", "| marché | tranche | station | observé | officiel YES |",
               "|---|---|---|---|---|"]
        for t in mism[:50]:
            md.append(f"| {t['question'][:60]} | {t['bucket']} | {t['station_icao']} | "
                      f"{t.get('observed_reported')} | {t['outcome_yes']} |")
    return "\n".join(md) + "\n", data


def write_report(s: Settings, out_dir: Path = Path("reports")) -> Path:
    md, data = build_report(s)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "report.md"
    path.write_text(md, encoding="utf-8")
    write_json(out_dir / "report.json", data)
    return path
