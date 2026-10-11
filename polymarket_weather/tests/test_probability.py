import json

import pytest

from weather_arb.forecast import local_daily_extreme
from weather_arb.markets import Bucket
from weather_arb.observations import daily_extremes, parse_iem_csv, round_half_up
from weather_arb.probability import (SigmaTable, bucket_prob_ensemble, bucket_prob_normal,
                                     condition_on_observed, dress_sigma, event_distribution,
                                     recenter_members)

BUCKETS = [Bucket(None, 20), *[Bucket(v, v) for v in range(21, 26)], Bucket(26, None)]


def test_normal_partition_sums_to_one():
    probs = [bucket_prob_normal(b, 23.3, 1.8) for b in BUCKETS]
    assert sum(probs) == pytest.approx(1.0)


def test_or_higher_uses_half_degree():
    # Prévision pile à 26.0 : "26 or higher" = P(T >= 25.5) > 50 %, pas 50 %.
    assert bucket_prob_normal(Bucket(26, None), 26.0, 1.0) == pytest.approx(0.6915, abs=1e-3)


def test_wider_sigma_reduces_overconfidence():
    narrow = bucket_prob_normal(Bucket(26, None), 28.0, 0.7)
    wide = bucket_prob_normal(Bucket(26, None), 28.0, 2.0)
    assert narrow > 0.99 and wide < 0.90


def test_ensemble_dressing_smooths_counts():
    members = [23.0] * 51  # ensemble dégénéré
    p = bucket_prob_ensemble(Bucket(23, 23), members, 1.0)
    assert 0.3 < p < 0.5  # pas 100 %


def test_recenter_and_dress():
    m = recenter_members([20.0, 22.0, 24.0], 25.0)
    assert m == [23.0, 25.0, 27.0]
    assert dress_sigma(2.0, [24.0, 26.0], 0.5) == pytest.approx(3 ** 0.5)
    assert dress_sigma(1.0, [20.0, 30.0], 0.5) == 0.5


def test_condition_on_observed_high():
    probs = event_distribution(BUCKETS, lambda b: bucket_prob_normal(b, 22.0, 1.5), True)
    cond = condition_on_observed(BUCKETS, probs, 24, "high")
    assert all(p == 0 for p in cond[:4])  # <=20,21,22,23 impossibles
    assert sum(cond) == pytest.approx(1.0)


def test_sigma_table_shrinkage(tmp_path):
    path = tmp_path / "t.json"
    path.write_text(json.dumps({
        "global": {"0": {"n": 1000, "rmse": 2.0, "bias": 0.0, "sd": 1.5},
                   "1": {"n": 1000, "rmse": 2.4, "bias": 0.0, "sd": 1.8}},
        "stations": {"RKSI": {"1": {"n": 20, "bias": -2.0, "sd": 1.8}}},
    }))
    t = SigmaTable(path, shrink_k=20, floor_c=0.6)
    e = t.get("RKSI", 1)
    assert e.source == "station" and e.bias_c == pytest.approx(-1.0) and e.sigma_c == pytest.approx(1.8)
    g = t.get("XXXX", 0)
    assert g.source == "global" and g.sigma_c == 2.0 and g.bias_c == 0.0
    far = t.get("XXXX", 5)  # extrapolation au-delà du dernier horizon connu
    assert far.sigma_c == pytest.approx(2.4 + 4 * 0.3)
    assert SigmaTable(None).get("RKSI", 1).source == "default"


def test_local_daily_extreme_requires_full_day():
    times = [f"2026-05-17T{h:02d}:00" for h in range(24)] + ["2026-05-18T00:00"]
    vals = [15 + (h if h <= 14 else 28 - h) * 0.5 for h in range(24)] + [10]
    out = local_daily_extreme(times, vals, "high")
    assert out == {__import__("datetime").date(2026, 5, 17): 22.0}


def test_iem_parsing_and_rounding():
    csv = "station,valid,tmpf\nRKSI,2026-05-17 13:00,77.00\nRKSI,2026-05-17 14:00,M\n" + "".join(
        f"RKSI,2026-05-17 {h:02d}:30,{60 + h}.00\n" for h in range(12))
    rows = parse_iem_csv(csv)
    d = list(daily_extremes(rows, "high", "C").values())[0]
    assert d["reported"] == 25 and d["n"] == 13
    assert round_half_up(24.5) == 25 and round_half_up(-0.5) == 0
