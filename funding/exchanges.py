"""Taux de financement des perpetuels : instantane et historique (Binance, Bybit, Hyperliquid), API publiques.

Convention : `rate` est le taux par periode de financement. Positif = les acheteurs paient les vendeurs,
donc une position VENDEUSE sur le perpetuel encaisse `rate` x notionnel a chaque reglement.
"""
import re
import time
from dataclasses import dataclass

import requests

BINANCE_F = "https://fapi.binance.com"
BINANCE_S = "https://api.binance.com"
BYBIT = "https://api.bybit.com"
HL = "https://api.hyperliquid.xyz/info"
EXCHANGES = ("binance", "bybit", "hyperliquid")


@dataclass
class Rate:
    exchange: str
    base: str            # nom de la crypto sur la plateforme (ex. 1000PEPE, kPEPE)
    rate: float          # taux par periode
    interval_h: float    # duree d'une periode, en heures
    volume_usd: float    # volume 24 h du perpetuel
    has_spot: bool       # achat au comptant possible sur la meme plateforme
    price: float = 0.0

    @property
    def apr(self):
        return self.rate * 24 / self.interval_h * 365

    @property
    def coin(self):
        return norm_base(self.base)


def norm_base(base):
    """Meme crypto, noms differents selon la plateforme : 1000PEPE (Binance), kPEPE (Hyperliquid) -> PEPE."""
    b = re.sub(r"^(1000000|100000|10000|1000|1M)(?=[A-Z])", "", base)
    if re.fullmatch(r"k[A-Z0-9]+", b):
        b = b[1:]
    return b


def _call(method, url, tries=5, **kw):
    for k in range(tries):
        try:
            r = requests.request(method, url, timeout=30, **kw)
            if r.status_code == 429 or r.status_code >= 500:
                raise requests.HTTPError(r.status_code)
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError):
            if k == tries - 1:
                raise
            time.sleep(2 ** (k + 1))


def _get(url, params=None):
    return _call("GET", url, params=params)


def _post(url, body):
    return _call("POST", url, json=body)


# ---------- instantane ----------

def binance_snapshot():
    prem = _get(BINANCE_F + "/fapi/v1/premiumIndex")
    interval = {d["symbol"]: float(d.get("fundingIntervalHours") or 8) for d in _get(BINANCE_F + "/fapi/v1/fundingInfo")}
    vol = {d["symbol"]: float(d["quoteVolume"]) for d in _get(BINANCE_F + "/fapi/v1/ticker/24hr")}
    spot = {norm_base(s["baseAsset"]) for s in _get(BINANCE_S + "/api/v3/exchangeInfo")["symbols"]
            if s["status"] == "TRADING" and s["quoteAsset"] == "USDT"}
    out = []
    for d in prem:
        sym = d["symbol"]
        if not sym.endswith("USDT") or d.get("lastFundingRate") in (None, ""):
            continue
        base = sym[:-4]
        out.append(Rate("binance", base, float(d["lastFundingRate"]), interval.get(sym, 8.0), vol.get(sym, 0.0),
                        norm_base(base) in spot, float(d.get("markPrice") or 0)))
    return out


def bybit_snapshot():
    ticks = _get(BYBIT + "/v5/market/tickers", {"category": "linear"})["result"]["list"]
    interval, cursor = {}, ""
    while True:
        res = _get(BYBIT + "/v5/market/instruments-info", {"category": "linear", "limit": 1000, "cursor": cursor})["result"]
        for d in res["list"]:
            interval[d["symbol"]] = float(d.get("fundingInterval") or 480) / 60
        cursor = res.get("nextPageCursor") or ""
        if not cursor:
            break
    spot = {norm_base(d["symbol"][:-4]) for d in _get(BYBIT + "/v5/market/tickers", {"category": "spot"})["result"]["list"]
            if d["symbol"].endswith("USDT")}
    out = []
    for d in ticks:
        sym = d["symbol"]
        if not sym.endswith("USDT") or d.get("fundingRate") in (None, ""):
            continue
        base = sym[:-4]
        out.append(Rate("bybit", base, float(d["fundingRate"]), interval.get(sym, 8.0), float(d.get("turnover24h") or 0),
                        norm_base(base) in spot, float(d.get("markPrice") or 0)))
    return out


def hyperliquid_snapshot():
    meta, ctxs = _post(HL, {"type": "metaAndAssetCtxs"})
    out = []
    for a, c in zip(meta["universe"], ctxs):
        if a.get("isDelisted") or c.get("funding") in (None, ""):
            continue
        # Pas de comptant equivalent sur Hyperliquid pour la plupart des cryptos : couverture sur une autre plateforme.
        out.append(Rate("hyperliquid", a["name"], float(c["funding"]), 1.0, float(c.get("dayNtlVlm") or 0), False,
                        float(c.get("markPx") or 0)))
    return out


SNAPSHOT = {"binance": binance_snapshot, "bybit": bybit_snapshot, "hyperliquid": hyperliquid_snapshot}


def snapshot(exchanges=EXCHANGES):
    out = []
    for ex in exchanges:
        try:
            out += SNAPSHOT[ex]()
        except Exception as e:  # une plateforme en panne ne bloque pas les autres
            print(f"{ex} : echec ({e})")
    return out


# ---------- historique : liste de (temps en ms, taux) ----------

def binance_history(base, start_ms, end_ms):
    rows, t = [], start_ms
    while t < end_ms:
        batch = _get(BINANCE_F + "/fapi/v1/fundingRate", {"symbol": base + "USDT", "startTime": t, "endTime": end_ms, "limit": 1000})
        if not batch:
            break
        rows += [(int(d["fundingTime"]), float(d["fundingRate"])) for d in batch]
        if len(batch) < 1000:
            break
        t = int(batch[-1]["fundingTime"]) + 1
    return rows


def bybit_history(base, start_ms, end_ms):
    rows, end = [], end_ms
    while end > start_ms:
        lst = _get(BYBIT + "/v5/market/funding/history",
                   {"category": "linear", "symbol": base + "USDT", "startTime": start_ms, "endTime": end, "limit": 200})["result"]["list"]
        if not lst:
            break
        rows += [(int(d["fundingRateTimestamp"]), float(d["fundingRate"])) for d in lst]
        oldest = min(int(d["fundingRateTimestamp"]) for d in lst)
        if len(lst) < 200 or oldest <= start_ms:
            break
        end = oldest - 1
    return sorted(set(r for r in rows if r[0] >= start_ms))


def hyperliquid_history(base, start_ms, end_ms):
    rows, t = [], start_ms
    while t < end_ms:
        batch = _post(HL, {"type": "fundingHistory", "coin": base, "startTime": t, "endTime": end_ms})
        if not batch:
            break
        rows += [(int(d["time"]), float(d["fundingRate"])) for d in batch]
        if len(batch) < 500:
            break
        t = int(batch[-1]["time"]) + 1
    return rows


HISTORY = {"binance": binance_history, "bybit": bybit_history, "hyperliquid": hyperliquid_history}
