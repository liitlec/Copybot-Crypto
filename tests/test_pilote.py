"""Comptabilite du portefeuille fictif du pilote, avec une source de donnees inventee."""
import numpy as np
import pandas as pd

from pilote.bot import Config, new_state, step


class FakeSource:
    def __init__(self, prices, rate, trend_up=False):
        self.prices, self.rate, self.up = prices, rate, trend_up

    def coins(self, t):
        return ["BTC", "ETH", "ALT"]

    def funding_apr(self, coin, t, days):
        return self.rate * 24 * 365 if coin != "ALT" else 0.0

    def funding_sum(self, coin, t0, t1):
        return self.rate * (t1 - t0) / pd.Timedelta(hours=1)

    def price(self, coin, t):
        return self.prices[coin]

    def trend_closes(self, coin, t):
        idx = pd.date_range(end=t, periods=260, freq="D")
        return pd.Series(np.linspace(100, 200, 260) if self.up else np.linspace(200, 100, 260), index=idx)

    def borrow_rate(self, t, default):
        return default


def test_arbitrage_neutre_encaisse_le_financement():
    cfg = Config(capital=1000, eth_stake=0.0, spot_fee=0, perp_fee=0)
    src = FakeSource({"BTC": 100.0, "ETH": 10.0, "ALT": 1.0}, rate=0.00001)   # ~8,8 %/an : pas d'emprunt
    t = pd.Timestamp("2026-01-01")
    state = new_state(cfg, t)
    step(src, state, t, cfg)
    assert state["weekly"]["k"] == 1.0 and state["weekly"]["sats"] == []
    assert all(abs(state["spot"][c] + state["perp"][c]) < 1e-9 for c in state["spot"])  # tendance baissiere : neutre
    src.prices = {"BTC": 50.0, "ETH": 5.0, "ALT": 1.0}                                   # krach de 50 %
    day = step(src, state, t + pd.Timedelta(days=1), cfg)
    assert abs(day["pnl"]["prix"]) < 1e-9                                                # le prix ne compte pas
    expected = 1000 * 0.95 * 0.00001 * 24                                                # tout le capital couvert
    assert abs(day["pnl"]["financement"] - expected) < 1e-6


def test_emprunt_quand_ca_paie_et_tendance():
    cfg = Config(capital=1000, eth_stake=0.0, spot_fee=0, perp_fee=0)
    src = FakeSource({"BTC": 100.0, "ETH": 10.0, "ALT": 1.0}, rate=0.00003, trend_up=True)  # ~26 %/an > 6 % + 10 pts
    t = pd.Timestamp("2026-01-01")
    state = new_state(cfg, t)
    step(src, state, t, cfg)
    assert state["weekly"]["k"] == 2.0
    expo = sum(state["spot"][c] + state["perp"][c] for c in state["spot"])
    assert expo > 0                                                                       # part tendance exposee au prix
    day = step(src, state, t + pd.Timedelta(days=1), cfg)
    assert day["pnl"]["emprunt"] < 0
