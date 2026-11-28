from datetime import date

import pytest

from conftest import nyc_event, seoul_event
from weather_arb import markets as mk


@pytest.mark.parametrize("label,lo,hi", [
    ("26°C or higher", 26, None),
    ("17°C or below", None, 17),
    ("25°C", 25, 25),
    ("84-85°F", 84, 85),
    ("between 84-85°F", 84, 85),
    ("83°F or lower", None, 83),
    ("94°F or above", 94, None),
    ("-2°C", -2, -2),
    ("-3--2°C", -3, -2),
    ("Will the highest temperature in Seoul be 26°C or higher on May 17?", 26, None),
    ("Will the highest temperature in Seoul be 22°C on May 17?", 22, 22),
])
def test_parse_bucket(label, lo, hi):
    assert mk.parse_bucket(label) == mk.Bucket(lo, hi)


def test_bucket_continuous_bounds_are_half_degree():
    b = mk.Bucket(25, 25)
    assert (b.cont_lo, b.cont_hi) == (24.5, 25.5)
    assert mk.Bucket(26, None).cont_lo == 25.5
    assert mk.Bucket(None, 20).cont_hi == 20.5
    assert mk.Bucket(84, 85).contains(85) and not mk.Bucket(84, 85).contains(86)


def test_parse_event_seoul():
    ev = mk.parse_event(seoul_event())
    assert (ev.city, ev.kind, ev.target_date, ev.unit) == ("Seoul", "high", date(2026, 5, 17), "C")
    assert ev.station_icao == "RKSI"
    assert ev.station_name == "Incheon Intl Airport"
    assert ev.resolution_source == "wunderground"
    assert ev.warnings == []
    assert ev.markets[0].mid == pytest.approx(0.015)
    assert ev.markets[-1].bucket == mk.Bucket(26, None)


def test_parse_event_nyc_fahrenheit():
    ev = mk.parse_event(nyc_event())
    assert ev.unit == "F" and ev.station_icao == "KLGA" and ev.city == "NYC"
    assert [m.bucket for m in ev.markets][1] == mk.Bucket(70, 71)
    assert not mk.check_partition([m.bucket for m in ev.markets])


def test_year_rollover():
    _, _, d = mk.parse_title("Highest temperature in Tokyo on December 31?", "2027-01-01T00:00:00Z")
    assert d == date(2026, 12, 31)


def test_partition_gap_detected():
    w = mk.check_partition([mk.Bucket(None, 20), mk.Bucket(22, 22), mk.Bucket(23, None)])
    assert any("trou" in x for x in w)


def test_official_resolution():
    ev = mk.parse_event(seoul_event(closed=True, winner="23°C"))
    res = {m.label: m.resolved_yes() for m in ev.markets}
    assert res["23°C"] is True and res["26°C or higher"] is False


def test_unknown_station_warns():
    raw = seoul_event()
    raw["description"] = "Resolves per the Hong Kong Observatory daily maximum in degrees Celsius."
    ev = mk.parse_event(raw)
    assert ev.station_icao is None and ev.resolution_source == "hko"
    assert any("ICAO" in w for w in ev.warnings)
