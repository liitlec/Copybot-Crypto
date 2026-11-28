"""Prix d'exécution simulés.

Backtest : bougies 1 minute GeckoTerminal (converties en SOL), avec deux hypothèses qui encadrent la réalité :
  * neutral     : clôture de la minute où arrive la copie
  * pessimistic : plus haut de la minute à l'achat, plus bas à la vente, et jamais mieux que le leader
    (le copieur arrive après lui : sur un memecoin qui pompe, il achète forcément plus cher)
  L'impact de NOTRE taille sur le pool est ignoré en backtest (sous-estime les coûts sur les petits pools).

Live : vraie cotation Jupiter au moment où le swap du leader est détecté (inclut l'impact de prix
pour notre taille). Rien n'est signé ni envoyé.
"""
from __future__ import annotations

import bisect
import time
from dataclasses import dataclass
from pathlib import Path

from . import net
from .config import GECKO_URL, LAMPORTS, USDC, WSOL
from .swaps import SwapEvent

GECKO_HEADERS = {"Accept": "application/json;version=20230302"}
ST_CHART = "https://data.solanatracker.io/chart"


@dataclass
class Fill:
    amount_out: float   # tokens (achat) ou SOL (vente), avant frais du bot
    price_sol: float    # SOL par token
    note: str = ""


class GeckoCandles:
    """Bougies minute par mint. Récupérées en USD sur le pool le plus liquide (quelle que soit la
    cotation : SOL, USDC…), puis converties en SOL avec la bougie SOL/USD de la même minute."""

    def __init__(self, cache_dir: Path | None = None, st_key: str | None = None):
        self.cache_dir = cache_dir
        self.st_key = st_key  # Solana Tracker : 1 requête par token et par fenêtre, bien plus rapide
        self._pools: dict[str, list[tuple[str, str]]] = {}
        self._usd: dict[str, tuple[list[int], list[list[float]]]] = {}
        self._sol_unit: dict[str, tuple[list[int], list[list[float]]]] = {}

    def pools(self, mint: str) -> list[tuple[str, str]]:
        """-> [(adresse pool, 'base'|'quote')] triés par liquidité."""
        if mint not in self._pools:
            data = net.get_json(f"{GECKO_URL}/networks/solana/tokens/{mint}/pools", {"page": 1},
                                headers=GECKO_HEADERS, cache_dir=self.cache_dir)
            rows = []
            for p in data.get("data", []):
                rel = p.get("relationships", {})
                base = rel.get("base_token", {}).get("data", {}).get("id", "").removeprefix("solana_")
                quote = rel.get("quote_token", {}).get("data", {}).get("id", "").removeprefix("solana_")
                if mint not in (base, quote):
                    continue
                reserve = float(p.get("attributes", {}).get("reserve_in_usd") or 0)
                rows.append((reserve, p["attributes"]["address"], "base" if base == mint else "quote"))
            self._pools[mint] = [(a, side) for _, a, side in sorted(rows, reverse=True)]
        return self._pools[mint]

    def _load_solanatracker(self, mint: str, start_ts: int, end_ts: int) -> dict[int, list[float]]:
        out: dict[int, list[float]] = {}
        chunk = 900 * 60  # ≤ 1000 bougies par requête
        t0 = int(start_ts)
        while t0 < end_ts:
            t1 = min(t0 + chunk, int(end_ts))
            data = net.get_json(f"{ST_CHART}/{mint}", {"type": "1m", "time_from": t0, "time_to": t1},
                                headers={"x-api-key": self.st_key},
                                cache_dir=self.cache_dir if t1 < time.time() - 300 else None)
            for c in data.get("oclhv", []):
                if c.get("close") is not None:
                    out[int(c["time"])] = [float(c["open"]), float(c["high"]), float(c["low"]), float(c["close"])]
            t0 = t1
        return out

    def load(self, mint: str, start_ts: int, end_ts: int, max_pools: int = 2) -> None:
        """Charge les bougies USD [start, end] : Solana Tracker si clé, sinon GeckoTerminal (pagination)."""
        ts_all: dict[int, list[float]] = {}
        if self.st_key:
            try:
                ts_all = self._load_solanatracker(mint, start_ts, end_ts)
            except RuntimeError:
                ts_all = {}
        for addr, side in ([] if ts_all else self.pools(mint)[:max_pools]):
            before = end_ts + 60
            while before > start_ts:
                data = net.get_json(
                    f"{GECKO_URL}/networks/solana/pools/{addr}/ohlcv/minute",
                    {"aggregate": 1, "before_timestamp": before, "limit": 1000, "currency": "usd",
                     "token": side},
                    headers=GECKO_HEADERS, cache_dir=self.cache_dir)
                rows = data.get("data", {}).get("attributes", {}).get("ohlcv_list", [])
                if not rows:
                    break
                for t, o, h, l, c, *_ in rows:
                    ts_all.setdefault(int(t), [float(o), float(h), float(l), float(c)])
                oldest = min(int(r[0]) for r in rows)
                if oldest >= before:
                    break
                before = oldest
            if ts_all:
                break  # le pool le plus liquide suffit ; le suivant seulement s'il n'a rien
        if mint in self._usd:  # fusion avec une fenêtre déjà chargée
            for k, v in zip(*self._usd[mint]):
                ts_all.setdefault(k, v)
        keys = sorted(ts_all)
        self._usd[mint] = (keys, [ts_all[k] for k in keys])

    def set_candles(self, mint: str, candles: dict[int, list[float]]) -> None:
        """Tests : bougies directement en SOL."""
        keys = sorted(candles)
        self._sol_unit[mint] = (keys, [candles[k] for k in keys])

    @staticmethod
    def _find(series, ts: float, max_gap_s: int):
        keys, vals = series
        i = bisect.bisect_right(keys, int(ts)) - 1
        if i < 0:
            return None
        if ts - keys[i] < 60:
            return vals[i], True
        if ts - keys[i] <= max_gap_s:
            c = vals[i][3]
            return [c, c, c, c], False  # pas de trade dans la minute : prix figé
        return None

    def sol_usd_at(self, ts: float) -> float | None:
        k = self._find(self._usd.get(WSOL, ([], [])), ts, 3600)
        return k[0][3] if k else None

    def at(self, mint: str, ts: float, max_gap_s: int = 600) -> tuple[list[float], bool] | None:
        """-> (o,h,l,c en SOL de la minute contenant ts, exact?) ; repli sur la dernière bougie < 10 min."""
        if mint in self._sol_unit:
            return self._find(self._sol_unit[mint], ts, max_gap_s)
        k = self._find(self._usd.get(mint, ([], [])), ts, max_gap_s)
        sol = self.sol_usd_at(ts)
        if not k or not sol:
            return None
        return [x / sol for x in k[0]], k[1]


class BacktestPrices:
    def __init__(self, candles: GeckoCandles, mode: str, slippage_bps: float):
        assert mode in ("neutral", "pessimistic")
        self.c, self.mode, self.slip = candles, mode, slippage_bps / 10_000

    def buy(self, ev: SwapEvent, sol_in: float, ts: float) -> Fill | None:
        k = self.c.at(ev.mint, ts)
        if not k:
            return None
        (o, h, l, c), _ = k
        px = c if self.mode == "neutral" else max(h, ev.price_sol)
        px *= 1 + self.slip
        return Fill(sol_in / px, px) if px > 0 else None

    def sell(self, mint: str, decimals: int, tokens: float, ts: float, ref_price: float | None) -> Fill | None:
        k = self.c.at(mint, ts)
        if not k:
            return None
        (o, h, l, c), _ = k
        px = c if self.mode == "neutral" else (min(l, ref_price) if ref_price else l)
        px *= 1 - self.slip
        return Fill(tokens * px, px)

    def mark(self, mint: str, decimals: int, tokens: float, ts: float) -> float | None:
        k = self.c.at(mint, ts, max_gap_s=10 ** 9)
        return tokens * k[0][3] if k else None


class JupiterPrices:
    """Cotations réelles (lecture seule) : GET /quote. Aucune transaction n'est construite."""

    def __init__(self, quote_url: str, slippage_bps: float):
        self.url, self.slip_bps = quote_url, int(slippage_bps)

    def _quote(self, inp: str, out: str, amount_raw: int) -> dict | None:
        if amount_raw <= 0:
            return None
        try:
            return net.get_json(self.url, {"inputMint": inp, "outputMint": out, "amount": amount_raw,
                                           "slippageBps": self.slip_bps})
        except RuntimeError:
            return None

    def buy(self, ev: SwapEvent, sol_in: float, ts: float) -> Fill | None:
        q = self._quote(WSOL, ev.mint, int(sol_in * LAMPORTS))
        if not q:
            return None
        # Pire cas garanti par la cotation : otherAmountThreshold (= out après slippage max).
        out = int(q.get("otherAmountThreshold") or q["outAmount"]) / 10 ** ev.decimals
        return Fill(out, sol_in / out if out else 0.0, f"impact={q.get('priceImpactPct')}") if out else None

    def sell(self, mint: str, decimals: int, tokens: float, ts: float, ref_price: float | None) -> Fill | None:
        q = self._quote(mint, WSOL, int(tokens * 10 ** decimals))
        if not q:
            return Fill(0.0, 0.0, "aucune route : position invendable")
        sol = int(q.get("otherAmountThreshold") or q["outAmount"]) / LAMPORTS
        return Fill(sol, sol / tokens if tokens else 0.0, f"impact={q.get('priceImpactPct')}")

    def mark(self, mint: str, decimals: int, tokens: float, ts: float) -> float | None:
        f = self.sell(mint, decimals, tokens, ts, None)
        return f.amount_out if f else None

    def sol_usd(self) -> float | None:
        """Cours SOL/USD actuel (cotation 1 SOL -> USDC), pour convertir les swaps des leaders en USDC."""
        q = self._quote(WSOL, USDC, LAMPORTS)
        return int(q["outAmount"]) / 1e6 if q else None
