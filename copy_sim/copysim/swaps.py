"""Détection des swaps d'un wallet à partir des variations de soldes d'une transaction.

Indépendant du DEX (Pump.fun, PumpSwap, Raydium, Jupiter, Meteora...) : on regarde seulement ce
que le wallet a gagné/perdu en SOL (natif + WSOL) et en tokens. Seuls les swaps contre SOL sont gérés.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .config import LAMPORTS, WSOL

EPS_SOL = 1e-6


@dataclass
class SwapEvent:
    signature: str
    slot: int
    block_time: int
    wallet: str
    side: str            # BUY | SELL
    mint: str
    sol_amount: float    # SOL dépensés (BUY) ou reçus (SELL), hors frais réseau
    token_amount: float  # tokens reçus (BUY) ou vendus (SELL), unités décimales
    decimals: int
    leader_pre_tokens: float  # solde de tokens du leader avant la tx (pour la fraction vendue)

    @property
    def price_sol(self) -> float:
        return self.sol_amount / self.token_amount if self.token_amount else 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "SwapEvent":
        return cls(**d)


def _key(k) -> str:
    return k["pubkey"] if isinstance(k, dict) else k


def _token_sums(balances: list[dict], wallet: str) -> dict[str, tuple[float, int]]:
    out: dict[str, tuple[float, int]] = {}
    for b in balances or []:
        if b.get("owner") != wallet:
            continue
        ui = b.get("uiTokenAmount") or {}
        dec = int(ui.get("decimals", 0))
        amt = int(ui.get("amount", "0")) / 10 ** dec
        prev = out.get(b["mint"], (0.0, dec))[0]
        out[b["mint"]] = (prev + amt, dec)
    return out


def parse_swap(tx: dict | None, wallet: str, signature: str | None = None) -> SwapEvent | None:
    if not tx or not tx.get("meta") or tx["meta"].get("err") is not None:
        return None
    meta = tx["meta"]
    msg = tx["transaction"]["message"]
    keys = [_key(k) for k in msg["accountKeys"]]
    loaded = meta.get("loadedAddresses") or {}
    if len(keys) < len(meta["preBalances"]):  # encodage non "jsonParsed" : clés de lookup tables à part
        keys += loaded.get("writable", []) + loaded.get("readonly", [])
    if wallet not in keys:
        return None
    i = keys.index(wallet)
    sol_delta = (meta["postBalances"][i] - meta["preBalances"][i]) / LAMPORTS
    if i == 0:
        sol_delta += meta.get("fee", 0) / LAMPORTS  # on exclut les frais réseau du prix

    pre = _token_sums(meta.get("preTokenBalances"), wallet)
    post = _token_sums(meta.get("postTokenBalances"), wallet)
    deltas: dict[str, tuple[float, float, int]] = {}
    for mint in set(pre) | set(post):
        p0, dec = pre.get(mint, (0.0, post.get(mint, (0, 0))[1]))
        p1 = post.get(mint, (0.0, dec))[0]
        if mint == WSOL:
            sol_delta += p1 - p0
        elif abs(p1 - p0) > 0:
            deltas[mint] = (p1 - p0, p0, dec)

    if len(deltas) != 1:
        return None  # transfert, airdrop, swap token-token, route multi-tokens : ignorés
    mint, (d, p0, dec) = next(iter(deltas.items()))
    sig = signature or tx["transaction"].get("signatures", [""])[0]
    base = dict(signature=sig, slot=tx.get("slot", 0), block_time=tx.get("blockTime") or 0, wallet=wallet,
                mint=mint, decimals=dec, leader_pre_tokens=p0)
    if d > 0 and sol_delta < -EPS_SOL:
        return SwapEvent(side="BUY", sol_amount=-sol_delta, token_amount=d, **base)
    if d < 0 and sol_delta > EPS_SOL:
        return SwapEvent(side="SELL", sol_amount=sol_delta, token_amount=-d, **base)
    return None
