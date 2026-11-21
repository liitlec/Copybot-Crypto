"""Chaîne complète scan -> résolution -> rapport avec des APIs simulées (aucun réseau)."""
from datetime import datetime, timezone

import pytest

from conftest import nyc_event, seoul_event
from weather_arb import http, scanner
from weather_arb.report import build_report
from weather_arb.resolution import resolve_all
from weather_arb.store import read_json, read_jsonl


def _hourly(day: str, tmax_c: float):
    times = [f"{day}T{h:02d}:00" for h in range(24)]
    vals = [tmax_c - 6 + 6 * (1 - abs(h - 14) / 14) for h in range(24)]
    return {"hourly": {"time": times, "temperature_2m": vals}}


def _iem(station: str, day: str, max_f: float) -> str:
    rows = [f"{station},{day} {h:02d}:00,{max_f - abs(h - 14) * 0.8:.2f}" for h in range(24)]
    return "station,valid,tmpf\n" + "\n".join(rows) + "\n"


class FakeAPI:
    def __init__(self):
        self.calls = []

    def __call__(self, url, params=None, **kw):
        self.calls.append((url, params))
        p = dict(params) if isinstance(params, list) else (params or {})
        if "gamma-api" in url and url.endswith("/events"):
            if "tag_slug" in p:
                return [seoul_event(), nyc_event()] if p.get("offset", 0) == 0 else []
            if p.get("slug") == "highest-temperature-in-seoul-on-may-17":
                return [seoul_event(closed=True, winner="23°C")]
            return []
        if "gamma-api" in url and "/markets/" in url:
            raise RuntimeError("404")
        if "//api.open-meteo.com" in url:
            tmax = 28.0 if p["longitude"] > 100 else 23.5  # Séoul vs NYC
            return _hourly("2026-05-17", tmax)
        if "mesonet" in url:
            if p["station"] == "RKSI":
                return _iem("RKSI", "2026-05-17", 73.4)  # 23 °C
            return _iem("LGA", "2026-05-17", 76.0)
        raise AssertionError(f"URL inattendue {url}")


@pytest.fixture
def fake(monkeypatch):
    api = FakeAPI()
    monkeypatch.setattr(http, "get", api)
    monkeypatch.setattr(scanner, "now_utc", lambda: datetime(2026, 5, 16, 0, 0, tzinfo=timezone.utc))
    return api


def test_scan_resolve_report(settings, fake):
    res = scanner.scan_once(settings, log=lambda *a: None)
    assert res["events"] == 2 and res["markets_evaluated"] == 13
    trades = read_json(settings.trades_path, [])
    assert len(trades) == len(res["new_trades"]) >= 1
    assert len({t["event_slug"] for t in trades}) == len(trades)  # max 1 trade / événement
    seoul = next(t for t in trades if t["city"] == "Seoul")
    assert seoul["side"] == "YES" and seoul["bucket"] == ">=26°C" and seoul["lead_days"] == 1
    assert seoul["entry_price"] == pytest.approx(0.50)  # ask 0.49 + slippage
    assert seoul["sigma_source"] == "default" and seoul["sigma"] == pytest.approx(1.8)
    assert 0.9 < seoul["p_side"] < 0.93  # et non 0.99+ comme avec sigma=0.7

    # Re-scan : aucun doublon de trade, aucun doublon de prédiction pour le même horizon.
    scanner.scan_once(settings, log=lambda *a: None)
    assert len(read_json(settings.trades_path, [])) == len(trades)
    assert len(read_jsonl(settings.predictions_path)) == 13

    out = resolve_all(settings, log=lambda *a: None)
    trades = read_json(settings.trades_path, [])
    seoul = next(t for t in trades if t["city"] == "Seoul")
    assert seoul["result"] == "LOSS" and seoul["resolution_method"] == "polymarket"
    assert seoul["observed_reported"] == 23 and seoul["obs_mismatch"] is False
    assert seoul["pnl"] == pytest.approx(-10.1)
    nyc = [t for t in trades if t["city"] == "NYC"]
    assert all(t["status"] == "PROVISIONAL" for t in nyc)  # obs METAR, officiel indisponible
    assert out["mismatches"] == 0

    preds = read_jsonl(settings.predictions_path)
    assert sum(p.get("outcome_yes") is True for p in preds if p["city"] == "Seoul") == 1

    md, data = build_report(settings)
    assert data["counts"]["resolved"] == len(trades)
    assert "Par horizon" in md and "Fiabilité du modèle" in md
    assert data["predictions"]["forecast_errors"][1]["n"] == 1


def test_fahrenheit_market_uses_fahrenheit(settings, fake):
    scanner.scan_once(settings, log=lambda *a: None)
    nyc = [p for p in read_jsonl(settings.predictions_path) if p["city"] == "NYC"]
    assert nyc[0]["forecast_raw"] == pytest.approx(23.5 * 1.8 + 32, abs=0.01)
    assert sum(p["p_model"] for p in nyc) == pytest.approx(1.0, abs=0.05)
