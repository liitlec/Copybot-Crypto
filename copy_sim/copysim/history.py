"""Historique des swaps des leaders sur une fenêtre passée (pour le backtest)."""
from __future__ import annotations

import time

from .net import SolanaRPC
from .swaps import SwapEvent, parse_swap


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
    log(f"  {wallet[:6]}…: {len(sigs)} tx, {len(events)} swaps contre SOL")
    return events


def leaders_swaps(rpc: SolanaRPC, wallets: list[str], days: float, log=print) -> list[SwapEvent]:
    now = int(time.time())
    since = now - int(days * 86400)
    out: list[SwapEvent] = []
    for w in wallets:
        try:
            out += wallet_swaps(rpc, w, since, now, log=log)
        except RuntimeError as exc:
            log(f"  {w[:6]}…: échec RPC ({exc})")
    out.sort(key=lambda e: (e.block_time, e.slot))
    return out
