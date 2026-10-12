"""Tendance BTC/ETH avec arbitrage quand la tendance baisse.

Pour chaque crypto (moitie du capital chacune), signal a la cloture de la veille :
  - cloture > moyenne `sma` jours : on DETIENT la crypto, sans couverture. La taille est reduite quand
    la volatilite des 20 derniers jours depasse `vol_target` (taille = vol_target / volatilite, max 100 %).
  - sinon (et pour la part non investie) : arbitrage neutre, comptant + vente du perpetuel, on encaisse
    le financement.

    python -m tendance.algo backtest                    # 2021 -> fin des donnees, seul et melange a l'arbitrage
    python -m tendance.algo backtest --sma 100 --vol-target 0.6
    python -m tendance.algo backtest --exchange hyperliquid --borrow 0.06   # tout sur Hyperliquid, emprunt quand ca paie
    python -m tendance.algo signal                      # position a tenir aujourd'hui (+ Telegram)

Emprunt quand ca paie (option --borrow) : la part arbitrage passe a 1,5x le capital quand le financement moyen
14 j de BTC/ETH depasse le cout d'emprunt + 5 points, a 2x au-dela de + 10 points ; taille revue chaque semaine.

Donnees : data/1d (python -m momentum.data) et data/funding/binance (python -m funding.backtest download).
"""
import argparse
import os

import numpy as np
import pandas as pd

from common.notify import telegram
from funding.backtest import Params, load_daily, run
from momentum.data import BASE, DATA_DIR

COINS = ("BTC", "ETH")
SWITCH_COST = 0.001  # frais + glissement quand on ajoute ou retire la couverture


def prices(coin):
    return pd.read_csv(os.path.join(DATA_DIR, "1d", f"{coin}USDT.csv"), parse_dates=["date"]).set_index("date")["close"]


def exposure(p, sma, vol_target):
    """Part du capital detenue sans couverture, decidee a la cloture (a appliquer le lendemain)."""
    r = p.pct_change()
    up = (p > p.rolling(sma).mean()).astype(float)
    vol = r.rolling(20).std() * np.sqrt(365)
    return (up * (vol_target / vol).clip(upper=1.0)).fillna(0.0)


def daily_returns(coin, funding, sma=50, vol_target=0.4, carry_notional=0.95):
    p = prices(coin)
    f = funding[coin].reindex(p.index).fillna(0.0) if coin in funding else pd.Series(0.0, index=p.index)
    ex = exposure(p, sma, vol_target).shift(1).fillna(0.0)
    return ex * p.pct_change().fillna(0) + (1 - ex) * carry_notional * f - ex.diff().abs().fillna(0) * SWITCH_COST


def with_borrowing(r, core_apr, borrow, notional=0.95, leg_cost=0.00095, steps=((0.10, 2.0), (0.05, 1.5))):
    """Agrandit la position d'arbitrage avec de l'argent emprunte quand l'ecart financement - emprunt le justifie."""
    k = core_apr.reindex(r.index).fillna(0).map(lambda a: next((m for gap, m in steps if a > borrow + gap), 1.0))
    k = k.where(np.arange(len(k)) % 7 == 0).ffill().fillna(1.0)
    cost = k.diff().abs().fillna(0) * notional * leg_cost
    return r * k - (k - 1) * borrow / 365 - cost, k


def summary(r, name):
    c = (1 + r).cumprod()
    yrs = max((c.index[-1] - c.index[0]).days / 365.25, 1e-9)
    cagr = c.iloc[-1] ** (1 / yrs) - 1
    dd = (c / c.cummax() - 1).min()
    y = c.resample("YE").last()
    y = y / y.shift(1).fillna(1) - 1
    m = c.resample("ME").last()
    m = m / m.shift(1).fillna(1) - 1
    print(f"{name:40s} {cagr:+6.1%}/an | pire chute {dd:6.1%} | mois negatifs {int((m < 0).sum())}/{len(m)} | "
          + " ".join(f"{d.year}:{v:+.0%}" for d, v in y.items()))


def backtest(a):
    fd = load_daily(a.exchange, a.start)
    tr = sum(daily_returns(c, fd, a.sma, a.vol_target) for c in COINS) / len(COINS)
    carry, _ = run(fd, Params(core=COINS, top_n=2, min_apr=0.20, lookback=14, rebalance=7, lev=19, eth_stake=0.03,
                              spot_fee=0.00075, perp_fee=0.0002, slip=0.0))
    rc = carry.pct_change().fillna(carry.iloc[0] - 1)
    idx = rc.index.intersection(tr.loc[a.start:].index)
    rc, tr = rc.loc[idx], tr.loc[idx]
    if a.borrow is not None:
        core_apr = fd[list(COINS)].mean(axis=1).rolling(14).mean().shift(1) * 365
        summary(rc, "Arbitrage optimise, sans emprunt")
        rc, k = with_borrowing(rc, core_apr, a.borrow)
        print(f"Emprunt a {a.borrow:.0%}/an : actif {float((k > 1).mean()):.0%} du temps (1,5x {float((k == 1.5).mean()):.0%}, "
              f"2x {float((k == 2).mean()):.0%})")
    hold = sum(prices(c).pct_change().reindex(idx).fillna(0) for c in COINS) / len(COINS)
    print(f"Periode {idx[0]:%d/%m/%Y} -> {idx[-1]:%d/%m/%Y}, correlation tendance/arbitrage {np.corrcoef(rc, tr)[0, 1]:.2f}")
    summary(hold, "BTC+ETH achetes et gardes")
    summary(rc, "Arbitrage optimise" + (" avec emprunt" if a.borrow is not None else ""))
    summary(tr, f"Tendance (SMA{a.sma}, volatilite {a.vol_target:.0%})")
    for w in (0.2, 0.3, 0.5):
        summary((1 - w) * rc + w * tr, f"{1 - w:.0%} arbitrage + {w:.0%} tendance")


def signal(a):
    import requests
    lines = [f"Tendance BTC/ETH (SMA{a.sma}, volatilite cible {a.vol_target:.0%})"]
    for coin in COINS:
        kl = requests.get(BASE + "/api/v3/klines", params={"symbol": coin + "USDT", "interval": "1d", "limit": a.sma + 40},
                          timeout=30).json()[:-1]  # la bougie du jour n'est pas terminee
        p = pd.Series([float(k[4]) for k in kl], index=pd.to_datetime([k[0] for k in kl], unit="ms"))
        ex = exposure(p, a.sma, a.vol_target).iloc[-1]
        sma = p.rolling(a.sma).mean().iloc[-1]
        state = "HAUSSE" if p.iloc[-1] > sma else "baisse"
        lines.append(f"  {coin} : {p.iloc[-1]:,.0f} $ ({state}, moyenne {sma:,.0f} $) -> detenir {ex:.0%} sans couverture, "
                     f"{1 - ex:.0%} en arbitrage")
    msg = "\n".join(lines)
    print(msg)
    telegram(msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("backtest", "signal"))
    ap.add_argument("--sma", type=int, default=50)
    ap.add_argument("--vol-target", type=float, default=0.4)
    ap.add_argument("--start", default="2021-01-01")
    ap.add_argument("--exchange", default="binance", choices=("binance", "hyperliquid"))
    ap.add_argument("--borrow", type=float, help="cout d'emprunt annuel : active l'emprunt quand ca paie (ex. 0.06)")
    a = ap.parse_args()
    (backtest if a.action == "backtest" else signal)(a)


if __name__ == "__main__":
    main()
