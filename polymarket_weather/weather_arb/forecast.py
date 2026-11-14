"""Prévisions ECMWF via Open-Meteo, toujours au point exact de la station et en heure LOCALE.

Le max/min journalier est recalculé depuis les valeurs horaires dans le fuseau de la station
(identique en scan et en calibration -> pas de biais de définition entre les deux).
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from . import http
from .config import (OPEN_METEO_ENSEMBLE, OPEN_METEO_FORECAST, OPEN_METEO_HISTORICAL_FC,
                     OPEN_METEO_PREVIOUS_RUNS)
from .stations import Station

MAX_PREVIOUS_DAY = 7  # Open-Meteo Previous Runs : temperature_2m_previous_day1..7


def _series(hourly: dict, var: str, model: str) -> list | None:
    """Open-Meteo renvoie 'var' (1 modèle) ou 'var_<model>' (plusieurs modèles)."""
    if var in hourly:
        return hourly[var]
    return hourly.get(f"{var}_{model}")


def local_daily_extreme(times: list[str], values: list, kind: str = "high",
                        min_hours: int = 20) -> dict[date, float]:
    """Groupe des valeurs horaires (heure locale ISO) par jour et renvoie max (high) ou min (low).
    Un jour avec moins de `min_hours` valeurs non nulles est ignoré (évite un max tronqué)."""
    buckets: dict[date, list[float]] = defaultdict(list)
    for t, v in zip(times, values):
        if v is None:
            continue
        buckets[date.fromisoformat(t[:10])].append(float(v))
    agg = max if kind == "high" else min
    return {d: agg(vs) for d, vs in buckets.items() if len(vs) >= min_hours}


def fetch_deterministic(st: Station, model: str, kind: str = "high") -> dict[date, float]:
    """Prévision du dernier run (°C), par jour local."""
    data = http.get(OPEN_METEO_FORECAST, {
        "latitude": st.lat, "longitude": st.lon, "hourly": "temperature_2m", "models": model,
        "timezone": st.tz, "forecast_days": 16, "past_days": 1,
    })
    hourly = data.get("hourly", {})
    vals = _series(hourly, "temperature_2m", model)
    if vals is None:
        raise RuntimeError(f"Open-Meteo : pas de temperature_2m pour {model} @ {st.icao}")
    return local_daily_extreme(hourly["time"], vals, kind)


def fetch_ensemble(st: Station, model: str = "ecmwf_ifs025", kind: str = "high") -> dict[date, list[float]]:
    """Ensemble ECMWF (contrôle + 50 membres) -> {jour: [extrême de chaque membre]} en °C."""
    data = http.get(OPEN_METEO_ENSEMBLE, {
        "latitude": st.lat, "longitude": st.lon, "hourly": "temperature_2m", "models": model,
        "timezone": st.tz, "forecast_days": 15,
    })
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    members = [k for k in hourly if k.startswith("temperature_2m")]
    if not members:
        raise RuntimeError(f"Open-Meteo ensemble : aucun membre pour {st.icao}")
    out: dict[date, list[float]] = defaultdict(list)
    for k in members:
        for d, v in local_daily_extreme(times, hourly[k], kind).items():
            out[d].append(v)
    return dict(out)


def fetch_previous_runs(st: Station, model: str, start: date, end: date, kind: str = "high",
                        leads: range = range(0, MAX_PREVIOUS_DAY + 1),
                        cache_dir: Path | None = None) -> dict[int, dict[date, float]]:
    """Prévisions passées par horizon : {lead_jours: {jour: Tmax prévue °C}}.

    lead 0 = 'temperature_2m' (run le plus récent pour chaque heure),
    lead n = 'temperature_2m_previous_day{n}' (run émis n jours plus tôt).
    Approximation : chaque heure du jour D vient du run émis ~n jours avant cette heure.
    """
    vars_ = ["temperature_2m" if n == 0 else f"temperature_2m_previous_day{n}" for n in leads]
    out: dict[int, dict[date, float]] = {n: {} for n in leads}
    cur = start
    while cur <= end:
        chunk_end = min(cur + timedelta(days=89), end)
        data = http.get(OPEN_METEO_PREVIOUS_RUNS, {
            "latitude": st.lat, "longitude": st.lon, "hourly": ",".join(vars_), "models": model,
            "timezone": st.tz, "start_date": cur.isoformat(), "end_date": chunk_end.isoformat(),
        }, cache_dir=cache_dir, cache_ttl_s=None if chunk_end < date.today() - timedelta(days=2) else 3600)
        hourly = data.get("hourly", {})
        for n, var in zip(leads, vars_):
            vals = _series(hourly, var, model)
            if vals:
                out[n].update(local_daily_extreme(hourly["time"], vals, kind))
        cur = chunk_end + timedelta(days=1)
    return out


def fetch_historical_forecast(st: Station, model: str, start: date, end: date, kind: str = "high",
                              cache_dir: Path | None = None) -> dict[date, float]:
    """Historical Forecast API : série continue des premières heures de chaque run (~J0).
    Utile en repli si Previous Runs n'a pas d'historique pour ce modèle."""
    data = http.get(OPEN_METEO_HISTORICAL_FC, {
        "latitude": st.lat, "longitude": st.lon, "hourly": "temperature_2m", "models": model,
        "timezone": st.tz, "start_date": start.isoformat(), "end_date": end.isoformat(),
    }, cache_dir=cache_dir)
    hourly = data.get("hourly", {})
    vals = _series(hourly, "temperature_2m", model) or []
    return local_daily_extreme(hourly.get("time", []), vals, kind)


def c_to_unit(v_c: float, unit: str) -> float:
    return v_c * 9 / 5 + 32 if unit == "F" else v_c


def delta_c_to_unit(d_c: float, unit: str) -> float:
    return d_c * 9 / 5 if unit == "F" else d_c
