"""Tests de l'arbitrage des taux : lecture des API (reponses simulees), tableaux du scanner, calculs du backtest."""
import numpy as np
import pandas as pd

from funding import exchanges as ex
from funding.backtest import Params, run, stats
from funding.exchanges import Rate, norm_base
from funding.scanner import carry_table, cross_table


def test_norm_base():
    assert norm_base("1000PEPE") == "PEPE"
    assert norm_base("kPEPE") == "PEPE"
    assert norm_base("1INCH") == "1INCH"
    assert norm_base("BTC") == "BTC"


def test_apr_selon_periode():
    assert abs(Rate("binance", "BTC", 0.0001, 8, 1, True).apr - 0.1095) < 1e-9
    assert abs(Rate("hyperliquid", "BTC", 0.0000125, 1, 1, False).apr - 0.1095) < 1e-9


def test_lecture_binance(monkeypatch):
    replies = {
        "/fapi/v1/premiumIndex": [{"symbol": "BTCUSDT", "lastFundingRate": "0.0003", "markPrice": "60000"},
                                  {"symbol": "1000PEPEUSDT", "lastFundingRate": "0.001", "markPrice": "0.01"},
                                  {"symbol": "BTCUSD_PERP", "lastFundingRate": "0.0001", "markPrice": "60000"}],
        "/fapi/v1/fundingInfo": [{"symbol": "1000PEPEUSDT", "fundingIntervalHours": 4}],
        "/fapi/v1/ticker/24hr": [{"symbol": "BTCUSDT", "quoteVolume": "1e9"}, {"symbol": "1000PEPEUSDT", "quoteVolume": "5e7"}],
        "/api/v3/exchangeInfo": {"symbols": [{"baseAsset": "BTC", "quoteAsset": "USDT", "status": "TRADING"},
                                             {"baseAsset": "PEPE", "quoteAsset": "USDT", "status": "TRADING"}]},
    }
    monkeypatch.setattr(ex, "_get", lambda url, params=None: next(v for k, v in replies.items() if url.endswith(k)))
    rs = {r.base: r for r in ex.binance_snapshot()}
    assert set(rs) == {"BTC", "1000PEPE"}
    assert rs["1000PEPE"].interval_h == 4 and rs["1000PEPE"].has_spot and rs["1000PEPE"].coin == "PEPE"
    assert rs["BTC"].interval_h == 8 and rs["BTC"].volume_usd == 1e9


def test_lecture_hyperliquid(monkeypatch):
    reply = [{"universe": [{"name": "BTC"}, {"name": "OLD", "isDelisted": True}]},
             [{"funding": "0.00002", "dayNtlVlm": "1e9", "markPx": "60000"}, {"funding": "0.1", "dayNtlVlm": "1", "markPx": "1"}]]
    monkeypatch.setattr(ex, "_post", lambda url, body: reply)
    rs = ex.hyperliquid_snapshot()
    assert [r.base for r in rs] == ["BTC"] and rs[0].interval_h == 1


def test_scanner_frais_et_ecart():
    rates = [Rate("binance", "ETH", 0.0003, 8, 5e8, True), Rate("hyperliquid", "ETH", -0.00001, 1, 5e8, False),
             Rate("bybit", "DOGE", 0.0005, 8, 1e6, True)]  # DOGE : volume trop faible
    c = carry_table(rates, 2e7, hold_days=14, spot_fee=0.001, perp_fee=0.0005)
    assert list(c["crypto"]) == ["ETH"]
    assert abs(c["net_an"].iloc[0] - (0.0003 * 3 * 365 - 2 * 0.0015 * 365 / 14)) < 1e-9
    x = cross_table(rates, 2e7, hold_days=14, perp_fee=0.0005)
    assert x.iloc[0]["vendre_perp"] == "binance" and x.iloc[0]["couverture"] == "perp hyperliquid"
    assert abs(x.iloc[0]["taux_an"] - (0.0003 * 3 * 365 + 0.00001 * 24 * 365)) < 1e-9


def daily_frame(cols, days=400):
    idx = pd.date_range("2023-01-01", periods=days, freq="D")
    df = pd.DataFrame({k: np.full(days, v, float) for k, v in cols.items()}, index=idx)
    df.attrs["start"] = idx[30]
    return df


def test_backtest_taux_constant():
    # 0,01 % par 8 h = 0,03 %/jour ; notionnel 75 % du capital (levier 3) ; une seule entree, jamais de sortie
    d = daily_frame({"BTC": 0.0003, "ETH": 0.0001})
    curve, held = run(d, Params(top_n=1, min_apr=0.0, rebalance=7, spot_fee=0, perp_fee=0, slip=0))
    assert (held == 1).all()
    expected = (1 + 0.75 * 0.0003) ** 365 - 1
    assert abs(stats(curve, held)["rendement_an"] - expected) < 0.01


def test_backtest_frais_et_taux_negatif():
    d = daily_frame({"BTC": -0.0003})
    curve, held = run(d, Params(top_n=1, min_apr=0.0))
    assert held.sum() == 0 and curve.iloc[-1] == 1.0       # taux negatif : on reste dehors
    d2 = daily_frame({"BTC": 0.0003})
    c0, _ = run(d2, Params(top_n=1, spot_fee=0, perp_fee=0, slip=0))
    c1, _ = run(d2, Params(top_n=1))
    assert c1.iloc[-1] < c0.iloc[-1]                        # les frais coutent
