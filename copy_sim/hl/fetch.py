"""Récupère l'historique public de Hyperliquid (lecture seule) pour le test de prédiction de direction :
bougies 4 h des tokens les plus échangés (jusqu'à 5 000 bougies, ≈ 830 jours) et historique des frais de financement.
Sortie : data_hl/candles_4h/<coin>.json, data_hl/funding/<coin>.json, data_hl/universe.json"""
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_hl"
API = "https://api.hyperliquid.xyz/info"
BAR_MS = 4 * 3600 * 1000


def post(body, tries=6):
    for k in range(tries):
        try:
            req = urllib.request.Request(API, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=30))
        except Exception as exc:  # 429 ou coupure : on attend et on recommence
            wait = 5 * (k + 1)
            print(f"  {body.get('type')} {body.get('coin', '')} : {exc} -> nouvel essai dans {wait} s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"échec {body}")


def universe(n):
    meta, ctxs = post({"type": "metaAndAssetCtxs"})
    rows = [(float(c["dayNtlVlm"]), a["name"], a["maxLeverage"]) for a, c in zip(meta["universe"], ctxs)
            if not a.get("isDelisted")]
    rows.sort(reverse=True)
    return [{"coin": name, "max_leverage": lev, "volume_24h": vol} for vol, name, lev in rows[:n]]


def candles(coin, now_ms):
    return post({"type": "candleSnapshot", "req": {"coin": coin, "interval": "4h",
                                                     "startTime": now_ms - 5000 * BAR_MS, "endTime": now_ms}})


def funding(coin, start_ms, now_ms):
    out, t = [], start_ms
    while t < now_ms:
        page = post({"type": "fundingHistory", "coin": coin, "startTime": t})
        if not page:
            break
        out += page
        last = page[-1]["time"]
        if last <= t:
            break
        t = last + 1
        time.sleep(1.2)
    return out


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    with_funding = "--funding" in sys.argv
    (OUT / "candles_4h").mkdir(parents=True, exist_ok=True)
    (OUT / "funding").mkdir(parents=True, exist_ok=True)
    now_ms = int(time.time() * 1000)
    uni = universe(n)
    coins = [u["coin"] for u in uni]
    if "BTC" not in coins:
        uni.append({"coin": "BTC", "max_leverage": 40, "volume_24h": None})
    (OUT / "universe.json").write_text(json.dumps({"fetched_ms": now_ms, "assets": uni}, indent=1))
    for u in uni:
        coin = u["coin"]
        c = candles(coin, now_ms)
        (OUT / "candles_4h" / f"{coin}.json").write_text(json.dumps(c))
        print(f"{coin}: {len(c)} bougies", flush=True)
        time.sleep(1.5)
        if with_funding and c:
            f = funding(coin, int(c[0]["t"]), now_ms)
            (OUT / "funding" / f"{coin}.json").write_text(json.dumps(f))
            print(f"{coin}: {len(f)} taux de financement", flush=True)


if __name__ == "__main__":
    main()
