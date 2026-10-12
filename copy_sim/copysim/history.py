"""Historique des swaps des leaders sur une fenêtre passée (pour le backtest)."""
from __future__ import annotations

import time

from urllib.parse import parse_qs, urlparse

from . import net
from .net import SolanaRPC
from .swaps import SwapEvent, fill_pre_balances, parse_enhanced, parse_swap

HELIUS_ENHANCED = "https://api.helius.xyz/v0/addresses/{}/transactions"


def helius_key(rpc_url: str) -> str | None:
    u = urlparse(rpc_url)
    if "helius" not in u.netloc:
        return None
    return (parse_qs(u.query).get("api-key") or [None])[0]


def wallet_swaps_helius(api_key: str, wallet: str, since_ts: int, until_ts: int | None = None,
                        max_pages: int = 200, cache_dir=None, log=print) -> list[SwapEvent]:
    """100 transactions déjà décodées par requête (au lieu d'1 avec getTransaction)."""
    events, before, n = [], None, 0
    for _ in range(max_pages):
        params = {"api-key": api_key, "limit": 100}
        if before:
            params["before"] = before
        page = net.get_json(HELIUS_ENHANCED.format(wallet), params, cache_dir=cache_dir if before else None)
        if not page:
            break
        n += len(page)
        for t in page:
            ts = t.get("timestamp") or 0
            if until_ts and ts > until_ts:
                continue
            if ts and ts < since_ts:
                page = []
                break
            e = parse_enhanced(t, wallet)
            if e:
                events.append(e)
        if not page:
            break
        before = page[-1]["signature"]
    events.sort(key=lambda e: (e.block_time, e.slot))
    log(f"  {wallet[:6]}…: {n} tx (Helius), {len(events)} swaps (SOL ou USD)")
    return fill_pre_balances(events)


def wallet_swaps(rpc: SolanaRPC, wallet: str, since_ts: int, until_ts: int | None = None,
                 max_tx: int = 3000, log=print) -> list[SwapEvent]:
    sigs: list[dict] = []
    before = None
    while len(sigs) < max_tx:
        page = rpc.signatures(wallet, before=before, limit=1000)
        if not page:
            break
        for s in page:
            bt = s.get("blockTime") or 0
            if bt and bt < since_ts:
                page = []
                break
            if s.get("err") is None and (until_ts is None or bt <= until_ts):
                sigs.append(s)
        if not page or len(page) < 1000:
            break
        before = page[-1]["signature"]
    sigs = sigs[:max_tx]
    if len(sigs) >= max_tx:
        log(f"  {wallet[:6]}…: plafond de {max_tx} tx atteint, fenêtre tronquée")
    txs = rpc.transactions([s["signature"] for s in sigs])
    events = [e for e in (parse_swap(tx, wallet, s["signature"]) for s, tx in zip(sigs, txs)) if e]
    events.sort(key=lambda e: (e.block_time, e.slot))
    log(f"  {wallet[:6]}…: {len(sigs)} tx, {len(events)} swaps signés (SOL ou USD)")
    return events


def leaders_swaps(rpc: SolanaRPC, wallets: list[str], days: float, log=print) -> list[SwapEvent]:
    now = int(time.time())
    since = now - int(days * 86400)
    key = helius_key(rpc.url)
    out: list[SwapEvent] = []
    for w in wallets:
        try:
            if key:
                out += wallet_swaps_helius(key, w, since, now, cache_dir=rpc.cache_dir, log=log)
            else:
                out += wallet_swaps(rpc, w, since, now, log=log)
        except RuntimeError as exc:
            log(f"  {w[:6]}…: échec RPC ({exc})")
    out.sort(key=lambda e: (e.block_time, e.slot))
    return out
