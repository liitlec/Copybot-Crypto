import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SEOUL_DESC = (
    "This market will resolve to the temperature range that contains the highest temperature "
    "recorded at the Incheon Intl Airport Station in degrees Celsius on 17 May '26. The resolution "
    "source for this market will be information from Wunderground, specifically the highest temperature "
    "recorded for all times on this day by the Forecast for the Incheon Intl Airport Station once "
    "information is finalized, available here: https://www.wunderground.com/history/daily/kr/incheon/RKSI. "
    "The resolution source for this market measures temperatures to whole degrees Celsius (eg, 9°C)."
)

NYC_DESC = (
    "This market will resolve to the temperature range that contains the highest temperature recorded "
    "at the LaGuardia Airport Station in degrees Fahrenheit on 17 May '26. Resolution source: "
    "https://www.wunderground.com/history/daily/us/ny/new-york-city/KLGA. Whole degrees Fahrenheit."
)


def _market(mid, label, bid, ask, closed=False, final=None, title="Seoul"):
    prices = final if final is not None else [str((bid + ask) / 2), str(1 - (bid + ask) / 2)]
    return {
        "id": mid, "conditionId": f"0x{mid}", "slug": f"m-{mid}", "groupItemTitle": label,
        "question": f"Will the highest temperature in {title} be {label} on May 17?",
        "outcomes": json.dumps(["Yes", "No"]), "outcomePrices": json.dumps(prices),
        "bestBid": bid, "bestAsk": ask, "liquidityNum": 5000, "closed": closed,
        "acceptingOrders": not closed,
    }


def seoul_event(closed=False, winner=None):
    labels = ["20°C or below", "21°C", "22°C", "23°C", "24°C", "25°C", "26°C or higher"]
    quotes = [(0.01, 0.02), (0.02, 0.03), (0.05, 0.06), (0.10, 0.12), (0.15, 0.17), (0.18, 0.20), (0.47, 0.49)]
    mkts = []
    for i, (lab, (b, a)) in enumerate(zip(labels, quotes)):
        final = None
        if closed:
            final = ["1", "0"] if lab == winner else ["0", "1"]
        mkts.append(_market(str(100 + i), lab, b, a, closed, final))
    return {"id": "9001", "slug": "highest-temperature-in-seoul-on-may-17",
            "title": "Highest temperature in Seoul on May 17?", "description": SEOUL_DESC,
            "endDate": "2026-05-17T12:00:00Z", "markets": mkts}


def nyc_event():
    labels = ["69°F or below", "70-71°F", "72-73°F", "74-75°F", "76-77°F", "78°F or higher"]
    quotes = [(0.03, 0.05), (0.10, 0.12), (0.25, 0.27), (0.30, 0.32), (0.15, 0.17), (0.05, 0.07)]
    mkts = [_market(str(200 + i), lab, b, a, title="NYC") for i, (lab, (b, a)) in enumerate(zip(labels, quotes))]
    return {"id": "9002", "slug": "highest-temperature-in-nyc-on-may-17",
            "title": "Highest temperature in NYC on May 17?", "description": NYC_DESC,
            "endDate": "2026-05-17T12:00:00Z", "markets": mkts}


@pytest.fixture
def settings(tmp_path):
    from weather_arb.config import Settings
    s = Settings()
    s.data_dir = tmp_path / "data"
    s.prob_model = "normal"
    s.min_edge, s.max_spread, s.min_liquidity = 0.08, 0.10, 200
    s.fee_rate, s.slippage, s.stake_usd, s.prob_clip = 0.01, 0.01, 10, 0.02
    s.max_trades_per_event, s.require_station = 1, True
    return s
