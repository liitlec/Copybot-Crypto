"""Détection des swaps d'un wallet à partir des variations de soldes d'une transaction.

Indépendant du DEX (Pump.fun, PumpSwap, Raydium, Jupiter, Meteora...) : on regarde seulement ce
que le wallet a gagné/perdu en SOL (natif + WSOL), en USDC/USDT et en tokens. Seules les transactions
SIGNÉES par le wallet comptent (les distributions/airdrops envoyés par d'autres sont du bruit).
Les swaps contre USDC/USDT sont convertis en SOL plus tard (cours SOL/USD de la minute).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from .config import LAMPORTS, USD_MINTS, WSOL

EPS_SOL = 1e-6
EPS_USD = 0.01


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
    quote: str = "SOL"        # SOL | USD (USDC/USDT)
    quote_amount: float = 0.0  # montant dans la devise de cotation

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
    raw_key = msg["accountKeys"][i]
    if isinstance(raw_key, dict) and "signer" in raw_key and not raw_key["signer"]:
        return None  # le wallet n'a pas signé : pas un trade à lui
    sol_delta = (meta["postBalances"][i] - meta["preBalances"][i]) / LAMPORTS
    if i == 0:
        sol_delta += meta.get("fee", 0) / LAMPORTS  # on exclut les frais réseau du prix

    pre = _token_sums(meta.get("preTokenBalances"), wallet)
    post = _token_sums(meta.get("postTokenBalances"), wallet)
    usd_delta = 0.0
    deltas: dict[str, tuple[float, float, int]] = {}
    for mint in set(pre) | set(post):
        p0, dec = pre.get(mint, (0.0, post.get(mint, (0, 0))[1]))
        p1 = post.get(mint, (0.0, dec))[0]
        if mint == WSOL:
            sol_delta += p1 - p0
        elif mint in USD_MINTS:
            usd_delta += p1 - p0
        elif abs(p1 - p0) > 0:
            deltas[mint] = (p1 - p0, p0, dec)

    if len(deltas) != 1:
        return None  # transfert, airdrop, swap token-token, route multi-tokens : ignorés
    mint, (d, p0, dec) = next(iter(deltas.items()))
    sig = signature or tx["transaction"].get("signatures", [""])[0]
    base = dict(signature=sig, slot=tx.get("slot", 0), block_time=tx.get("blockTime") or 0, wallet=wallet,
                mint=mint, decimals=dec, leader_pre_tokens=p0)
    # Jambe USD prioritaire si elle bouge dans le sens opposé au token (le SOL ne bouge alors que des frais).
    if d > 0 and usd_delta < -EPS_USD:
        return SwapEvent(side="BUY", sol_amount=0.0, token_amount=d, quote="USD", quote_amount=-usd_delta, **base)
    if d < 0 and usd_delta > EPS_USD:
        return SwapEvent(side="SELL", sol_amount=0.0, token_amount=-d, quote="USD", quote_amount=usd_delta, **base)
    if d > 0 and sol_delta < -EPS_SOL:
        return SwapEvent(side="BUY", sol_amount=-sol_delta, token_amount=d, quote_amount=-sol_delta, **base)
    if d < 0 and sol_delta > EPS_SOL:
        return SwapEvent(side="SELL", sol_amount=sol_delta, token_amount=-d, quote_amount=sol_delta, **base)
    return None


def convert_usd(events: list[SwapEvent], sol_usd_at) -> list[SwapEvent]:
    """Convertit les swaps cotés en USD en équivalent SOL ; écarte ceux sans cours disponible."""
    out = []
    for e in events:
        if e.quote == "USD":
            px = sol_usd_at(e.block_time)
            if not px:
                continue
            e.sol_amount = e.quote_amount / px
        out.append(e)
    return out


def parse_enhanced(t: dict, wallet: str) -> SwapEvent | None:
    """Même logique que parse_swap, sur le format « Enhanced Transactions » de Helius
    (accountData : variations natives et tokens par compte). Le solde de tokens avant la tx n'y figure
    pas : il est reconstitué ensuite par `fill_pre_balances`."""
    if not t or t.get("transactionError"):
        return None
    sol_delta, usd_delta = 0.0, 0.0
    deltas: dict[str, list] = {}
    for a in t.get("accountData", []):
        if a.get("account") == wallet:
            sol_delta += (a.get("nativeBalanceChange") or 0) / LAMPORTS
        for c in a.get("tokenBalanceChanges", []):
            if c.get("userAccount") != wallet:
                continue
            raw = c.get("rawTokenAmount", {})
            dec = int(raw.get("decimals", 0))
            amt = int(raw.get("tokenAmount", "0")) / 10 ** dec
            mint = c.get("mint")
            if mint == WSOL:
                sol_delta += amt
            elif mint in USD_MINTS:
                usd_delta += amt
            else:
                deltas.setdefault(mint, [0.0, dec])[0] += amt
    if t.get("feePayer") == wallet:
        sol_delta += (t.get("fee") or 0) / LAMPORTS
    deltas = {m: v for m, v in deltas.items() if abs(v[0]) > 0}
    if len(deltas) != 1:
        return None
    mint, (d, dec) = next(iter(deltas.items()))
    base = dict(signature=t.get("signature", ""), slot=t.get("slot", 0), block_time=t.get("timestamp") or 0,
                wallet=wallet, mint=mint, decimals=dec, leader_pre_tokens=-1.0)
    if d > 0 and usd_delta < -EPS_USD:
        return SwapEvent(side="BUY", sol_amount=0.0, token_amount=d, quote="USD", quote_amount=-usd_delta, **base)
    if d < 0 and usd_delta > EPS_USD:
        return SwapEvent(side="SELL", sol_amount=0.0, token_amount=-d, quote="USD", quote_amount=usd_delta, **base)
    if d > 0 and sol_delta < -EPS_SOL:
        return SwapEvent(side="BUY", sol_amount=-sol_delta, token_amount=d, quote_amount=-sol_delta, **base)
    if d < 0 and sol_delta > EPS_SOL:
        return SwapEvent(side="SELL", sol_amount=sol_delta, token_amount=-d, quote_amount=sol_delta, **base)
    return None


def fill_pre_balances(events: list[SwapEvent]) -> list[SwapEvent]:
    """Reconstitue le solde du leader avant chaque vente à partir de ses achats observés dans la fenêtre
    (événements triés). Inconnu ou incohérent -> on suppose qu'il vend toute sa ligne."""
    hold: dict[tuple[str, str], float] = {}
    for e in events:
        k = (e.wallet, e.mint)
        h = hold.get(k, 0.0)
        if e.side == "BUY":
            hold[k] = h + e.token_amount
        else:
            if e.leader_pre_tokens < 0:
                e.leader_pre_tokens = h if h >= e.token_amount else e.token_amount
            hold[k] = max(h - e.token_amount, 0.0)
    return events
