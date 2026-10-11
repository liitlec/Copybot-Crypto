"""Calibration du sigma : prévisions ECMWF passées (Previous Runs API) vs observations METAR,
par station et par horizon. Produit data/sigma_table.json utilisé par le scanner."""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import fmean

from .forecast import fetch_previous_runs
from .observations import daily_extremes, fetch_metar_temps
from .stations import Station


def residual_stats(res: list[float]) -> dict:
    n = len(res)
    if n == 0:
        return {"n": 0}
    bias = fmean(res)
    sd = math.sqrt(sum((r - bias) ** 2 for r in res) / max(n - 1, 1))
    rmse = math.sqrt(fmean(r * r for r in res))
    mae = fmean(abs(r) for r in res)
    # Queues : fraction hors ±2 sd (attendu 4.6 % si gaussien). Bien plus = queues épaisses.
    tail2 = sum(abs(r - bias) > 2 * sd for r in res) / n if sd > 0 else 0.0
    return {"n": n, "bias": round(bias, 3), "sd": round(sd, 3), "rmse": round(rmse, 3),
            "mae": round(mae, 3), "tail_2sd": round(tail2, 3)}


def station_residuals(st: Station, model: str, start: date, end: date, kind: str = "high",
                      cache_dir: Path | None = None) -> dict[int, list[tuple[date, float, float]]]:
    """-> {lead: [(jour, prévision °C, observé °C)]}."""
    fc = fetch_previous_runs(st, model, start, end, kind, cache_dir=cache_dir)
    obs = daily_extremes(fetch_metar_temps(st, start, end, cache_dir=cache_dir), kind, "C")
    out: dict[int, list] = {}
    for lead, series in fc.items():
        out[lead] = [(d, f, obs[d]["value"]) for d, f in sorted(series.items()) if d in obs]
    return out


def calibrate(stations: list[Station], model: str, days: int, kind: str = "high",
              cache_dir: Path | None = None, log=print) -> dict:
    end = date.today() - timedelta(days=2)  # obs finalisées
    start = end - timedelta(days=days)
    per_station: dict[str, dict] = {}
    pooled_raw: dict[int, list[float]] = {}
    pooled_debiased: dict[int, list[float]] = {}
    for st in stations:
        try:
            res = station_residuals(st, model, start, end, kind, cache_dir)
        except RuntimeError as exc:
            log(f"  {st.icao}: échec ({exc})")
            continue
        per_station[st.icao] = {}
        for lead, rows in res.items():
            r = [o - f for _, f, o in rows]
            stats = residual_stats(r)
            per_station[st.icao][str(lead)] = stats
            if stats["n"]:
                pooled_raw.setdefault(lead, []).extend(r)
                pooled_debiased.setdefault(lead, []).extend(x - stats["bias"] for x in r)
        l1 = per_station[st.icao].get("1", {})
        log(f"  {st.icao:5s} {st.name[:28]:28s} J+1 n={l1.get('n', 0):3d} "
            f"biais={l1.get('bias', float('nan')):+.2f} sd={l1.get('sd', float('nan')):.2f}")
    glob = {}
    for lead in sorted(pooled_raw):
        raw = residual_stats(pooled_raw[lead])
        deb = residual_stats(pooled_debiased[lead])
        glob[str(lead)] = {"n": raw["n"], "rmse": raw["rmse"], "bias": raw["bias"],
                           "sd": deb["sd"], "tail_2sd": deb["tail_2sd"]}
    return {
        "meta": {"model": model, "kind": kind, "start": start.isoformat(), "end": end.isoformat(),
                 "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "truth": "METAR (IEM), max des obs en heure locale",
                 "note": "bias = obs - prévision (°C), à ajouter à la prévision"},
        "global": glob,
        "stations": per_station,
    }


def format_table(table: dict) -> str:
    lines = ["| Horizon | n | biais moyen °C | RMSE brut °C | sd débiaisé °C | hors ±2sd |",
             "|---|---|---|---|---|---|"]
    for lead, g in sorted(table.get("global", {}).items(), key=lambda kv: int(kv[0])):
        lines.append(f"| J+{lead} | {g['n']} | {g['bias']:+.2f} | {g['rmse']:.2f} | {g['sd']:.2f} | "
                     f"{g['tail_2sd']:.1%} |")
    lines += ["", "| Station | J0 biais/sd | J+1 biais/sd | J+3 biais/sd | n (J+1) |", "|---|---|---|---|---|"]
    for icao, leads in sorted(table.get("stations", {}).items()):
        def cell(l):
            s = leads.get(str(l), {})
            return f"{s['bias']:+.2f} / {s['sd']:.2f}" if s.get("n") else "-"
        lines.append(f"| {icao} | {cell(0)} | {cell(1)} | {cell(3)} | {leads.get('1', {}).get('n', 0)} |")
    return "\n".join(lines)
