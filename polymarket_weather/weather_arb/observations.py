"""Températures observées à la station (METAR via Iowa Environmental Mesonet).

Pourquoi IEM et pas ERA5 (archive Open-Meteo) : le marché se résout sur la station
(Wunderground affiche les METAR de l'aéroport), pas sur une maille de réanalyse. Calibrer
contre ERA5 masquerait précisément le biais station/maille qu'on cherche à mesurer.

Limites connues (à garder en tête dans l'analyse) :
  * Wunderground = max des METAR horaires/spéciaux -> inférieur au vrai max continu (~0.3-0.5 °C).
    IEM utilise les mêmes METAR, donc c'est cohérent avec la résolution.
  * Hors US, METAR en °C entiers -> la valeur rapportée est déjà entière.
  * Écarts possibles de ±1 degré avec WU sur des cas limites : la résolution officielle
    Polymarket (Gamma) reste prioritaire, l'observation sert de contrôle.
"""
from __future__ import annotations

import csv
import io
import math
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from . import http
from .config import IEM_ASOS
from .stations import Station


def round_half_up(x: float) -> int:
    return math.floor(x + 0.5)


def fetch_metar_temps(st: Station, start: date, end: date, cache_dir: Path | None = None
                      ) -> list[tuple[str, float]]:
    """-> [(heure locale 'YYYY-MM-DD HH:MM', temp °F)] entre start et end inclus."""
    stop = end + timedelta(days=1)
    params = [
        ("station", st.iem_id), ("data", "tmpf"), ("tz", st.tz), ("format", "onlycomma"),
        ("latlon", "no"), ("missing", "M"), ("trace", "T"), ("direct", "no"),
        ("year1", start.year), ("month1", start.month), ("day1", start.day),
        ("year2", stop.year), ("month2", stop.month), ("day2", stop.day),
        ("report_type", 3), ("report_type", 4),  # routine + spéciaux
    ]
    finished = end < date.today() - timedelta(days=2)
    text = http.get(IEM_ASOS, params, as_text=True, timeout=60,
                    cache_dir=cache_dir, cache_ttl_s=None if finished else 900)
    return parse_iem_csv(text)


def parse_iem_csv(text: str) -> list[tuple[str, float]]:
    rows = []
    reader = csv.DictReader(io.StringIO("\n".join(l for l in text.splitlines() if not l.startswith("#"))))
    for r in reader:
        v = (r.get("tmpf") or "").strip()
        if v in ("", "M", "T"):
            continue
        try:
            rows.append((r["valid"], float(v)))
        except (KeyError, ValueError):
            continue
    return rows


def f_to_unit(v_f: float, unit: str) -> float:
    return v_f if unit == "F" else (v_f - 32) * 5 / 9


def daily_extremes(rows: list[tuple[str, float]], kind: str = "high", unit: str = "C",
                   min_obs: int = 12) -> dict[date, dict]:
    """-> {jour: {'value': extrême (unité), 'reported': entier arrondi, 'n': nb obs}}."""
    by_day: dict[date, list[float]] = defaultdict(list)
    for t, v_f in rows:
        by_day[date.fromisoformat(t[:10])].append(f_to_unit(v_f, unit))
    out = {}
    for d, vs in by_day.items():
        if len(vs) < min_obs:
            continue  # journée incomplète -> pas de résolution fiable
        val = max(vs) if kind == "high" else min(vs)
        out[d] = {"value": val, "reported": round_half_up(val), "n": len(vs)}
    return out


def observed_extreme(st: Station, day: date, kind: str, unit: str, cache_dir: Path | None = None
                     ) -> dict | None:
    rows = fetch_metar_temps(st, day, day, cache_dir=cache_dir)
    return daily_extremes(rows, kind, unit).get(day)


def observed_so_far(st: Station, day: date, kind: str, unit: str) -> float | None:
    """Extrême observé depuis minuit local (pour conditionner les marchés J0)."""
    rows = fetch_metar_temps(st, day, day)
    vals = [f_to_unit(v, unit) for t, v in rows if t[:10] == day.isoformat()]
    if not vals:
        return None
    return max(vals) if kind == "high" else min(vals)
