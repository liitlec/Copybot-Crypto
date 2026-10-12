"""Telechargement des bougies Binance (spot, paires USDT) vers data/<intervalle>/<SYMBOLE>.csv.

    python -m momentum.data                 # toutes les paires USDT, bougies 1d depuis 2020-01-01
    python -m momentum.data --start 2019-01-01 --interval 1d

Les paires retirees de la cote (status != TRADING) sont aussi telechargees quand Binance
les sert encore, pour limiter le biais du survivant. Les mises a jour sont incrementales.
"""
import argparse
import os
import time

import pandas as pd
import requests

# Miroir public des donnees de marche Binance : meme API, accessible depuis les pays ou api.binance.com est bloque.
BASE = os.environ.get("BINANCE_SPOT_URL", "https://data-api.binance.vision")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume"]

# Stablecoins, monnaies classiques et tokens a levier : pas des cryptos qui tendancent.
EXCLUDE_BASE = {
    "USDC", "BUSD", "TUSD", "FDUSD", "USDP", "DAI", "PAX", "USDS", "SUSD", "UST", "USTC", "EUR", "GBP",
    "AUD", "TRY", "BRL", "AEUR", "EURI", "XUSD", "USD1", "BFUSD", "RLUSD", "PYUSD", "USDE", "PAXG", "WBTC",
    "WBETH", "BKRW", "IDRT", "BIDR", "NGN", "RUB", "UAH", "ZAR", "VAI",
}
EXCLUDE_SUFFIX = ("UP", "DOWN", "BULL", "BEAR")


def _get(path, params=None, tries=5):
    for k in range(tries):
        try:
            r = requests.get(BASE + path, params=params, timeout=30)
            if r.status_code == 429 or r.status_code >= 500:
                raise requests.HTTPError(r.status_code)
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError):
            if k == tries - 1:
                raise
            time.sleep(2 ** (k + 1))


def universe():
    info = _get("/api/v3/exchangeInfo")
    out = []
    for s in info["symbols"]:
        base = s["baseAsset"]
        if s["quoteAsset"] != "USDT" or base in EXCLUDE_BASE or base.endswith(EXCLUDE_SUFFIX):
            continue
        out.append(s["symbol"])
    return sorted(out)


def klines(symbol, interval, start_ms):
    rows = []
    while True:
        batch = _get("/api/v3/klines", {"symbol": symbol, "interval": interval, "startTime": start_ms, "limit": 1000})
        if not batch:
            break
        rows += [b[:8] for b in batch]
        if len(batch) < 1000:
            break
        start_ms = batch[-1][0] + 1
    df = pd.DataFrame(rows, columns=COLS)
    if df.empty:
        return df
    for c in COLS[1:6] + ["quote_volume"]:
        df[c] = df[c].astype(float)
    df["date"] = pd.to_datetime(df["open_time"], unit="ms")
    df = df[df["close_time"] < time.time() * 1000]  # la bougie du jour n'est pas terminee : on l'ignore
    return df[["date", "open", "high", "low", "close", "volume", "quote_volume"]]


def download(start="2020-01-01", interval="1d"):
    folder = os.path.join(DATA_DIR, interval)
    os.makedirs(folder, exist_ok=True)
    syms = universe()
    print(f"{len(syms)} paires USDT")
    start_ms = int(pd.Timestamp(start).timestamp() * 1000)
    for n, sym in enumerate(syms, 1):
        path = os.path.join(folder, f"{sym}.csv")
        old = pd.read_csv(path, parse_dates=["date"]) if os.path.exists(path) else None
        since = start_ms if old is None or old.empty else int(old["date"].iloc[-1].timestamp() * 1000) + 1
        try:
            new = klines(sym, interval, since)
        except Exception as e:  # paire retiree sans historique servi, etc.
            print(f"[{n}/{len(syms)}] {sym}: echec ({e})")
            continue
        df = new if old is None else pd.concat([old, new]).drop_duplicates("date", keep="last")
        if not df.empty:
            df.sort_values("date").to_csv(path, index=False)
        print(f"[{n}/{len(syms)}] {sym}: {len(df)} bougies")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2020-01-01")
    ap.add_argument("--interval", default="1d")
    a = ap.parse_args()
    download(a.start, a.interval)
