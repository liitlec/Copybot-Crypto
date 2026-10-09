"""Tests de mecanique du backtest sur donnees synthetiques (aucun resultat de marche ici)."""
import numpy as np
import pandas as pd

from momentum.backtest import Params, panel_from_frames, run, stats


def frame(closes, vol=1e7, spread=0.01, opens=None):
    c = np.asarray(closes, float)
    o = np.r_[c[0], c[:-1]] if opens is None else np.asarray(opens, float)
    df = pd.DataFrame({"open": o, "high": np.maximum(o, c) * (1 + spread), "low": np.minimum(o, c) * (1 - spread),
                       "close": c, "volume": 1.0, "quote_volume": vol},
                      index=pd.date_range("2022-01-01", periods=len(c), freq="D"))
    return df


def base(n=120):
    btc = frame(np.linspace(100, 200, n))  # BTC toujours au-dessus de sa moyenne : regime haussier
    flat = 10 + 0.05 * np.sin(np.arange(n))
    return btc, flat


def test_breakout_entre_au_lendemain_puis_stop():
    btc, alt = base()
    alt = alt.copy()
    alt[80] = 12.0               # cassure le jour 80
    vol = np.full(len(alt), 1e7)
    vol[80] = 5e7                # avec gros volume
    alt[81:] = 12.0
    alt[85:] = 6.0               # effondrement -> stop
    a = frame(alt)
    a["quote_volume"] = vol
    res = run(panel_from_frames({"BTCUSDT": btc, "ALTUSDT": a}), Params(max_pos=1))
    t = res.trades[res.trades["sym"] == "ALTUSDT"]
    assert len(t) == 1
    assert t["entry_date"].iloc[0] == a.index[81]       # execution le lendemain du signal
    assert t["entry"].iloc[0] == a["open"].iloc[81]
    assert t["why"].iloc[0] in ("stop", "stop_gap")
    assert t["r"].iloc[0] < -0.9                          # perte d'environ 1 R ou plus (trou de prix)


def test_pas_d_entree_sans_regime():
    n = 120
    btc = frame(np.linspace(200, 100, n))                 # BTC baissier
    alt = 10 + 0.05 * np.sin(np.arange(n))
    alt[80:] = 12.0
    a = frame(alt)
    a.loc[a.index[80], "quote_volume"] = 5e7
    res = run(panel_from_frames({"BTCUSDT": btc, "ALTUSDT": a}), Params())
    assert res.trades.empty or not (res.trades["sym"] == "ALTUSDT").any()


def test_risque_et_levier_respectes():
    rng = np.random.default_rng(0)
    frames = {"BTCUSDT": frame(np.linspace(100, 300, 400))}
    for k in range(20):
        frames[f"C{k}USDT"] = frame(10 * np.exp(np.cumsum(rng.normal(0.002, 0.05, 400))), vol=rng.lognormal(16.5, 0.8, 400))
    p = panel_from_frames(frames)
    res = run(p, Params(risk=0.02, lev=3))
    assert len(res.trades) > 0
    assert res.trades["r"].min() > -3                     # aucune perte demesuree par rapport au risque prevu
    s = stats(res)
    assert np.isfinite(s["cagr"]) and -1 <= s["max_dd"] <= 0
