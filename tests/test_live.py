import numpy as np

from momentum.backtest import Params, panel_from_frames, run
from momentum.live import daily_report
from test_backtest import frame


def test_rapport_du_jour():
    rng = np.random.default_rng(3)
    frames = {"BTCUSDT": frame(np.linspace(100, 300, 300))}
    for k in range(15):
        frames[f"C{k}USDT"] = frame(10 * np.exp(np.cumsum(rng.normal(0.003, 0.05, 300))), vol=rng.lognormal(16.5, 0.8, 300))
    res = run(panel_from_frames(frames, start="2022-05-01"), Params())
    msg = daily_report(res, 10_000)
    assert "Capital" in msg and "simulation" in msg
    for p in res.open_positions:
        assert p["sym"] in msg
