"""Constitution automatique de la liste des leaders (classement hebdo).

Sources, par ordre de préférence :
  1. solanatracker : classement KOL sur 7 jours (le même que Kolscan), clé API gratuite
     SOLANATRACKER_API_KEY. Wallets publics, identifiés (nom, Twitter).
  2. gecko : sans aucune clé. Reconstitue un classement à partir des derniers trades des pools Solana en
     tendance sur GeckoTerminal (gains réalisés par wallet). Fenêtre courte : classement grossier.
Puis filtrage on-chain : on garde les wallets actifs sur 24 h et on écarte les bots (trop de tx).
"""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass

from . import net
from .config import GECKO_URL
from .net import SolanaRPC
from .prices import GECKO_HEADERS

ST_URL = "https://data.solanatracker.io/v2/pnl/leaderboard/kols/period"
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def is_solana_address(s: str) -> bool:
    """Décodage base58 complet : 32 octets exactement (évite toute adresse mal copiée)."""
    if not isinstance(s, str) or not 32 <= len(s) <= 44 or any(c not in B58 for c in s):
        return False
    n = 0
    for c in s:
        n = n * 58 + B58.index(c)
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    raw = b"\0" * (len(s) - len(s.lstrip("1"))) + raw
    return len(raw) == 32


@dataclass
class Candidate:
    wallet: str
    label: str
    pnl: float
    trades: int | None = None
    source: str = ""


def _first(d: dict, *paths, default=None):
    for p in paths:
        cur = d
        for k in p.split("."):
            cur = cur.get(k) if isinstance(cur, dict) else None
        if cur not in (None, ""):
            return cur
    return default


def from_solanatracker(api_key: str, period: str = "7d", limit: int = 30) -> list[Candidate]:
    data = net.get_json(ST_URL, {"period": period, "sort": "realized", "limit": limit},
                        headers={"x-api-key": api_key})
    rows = data.get("traders") or data.get("data") or (data if isinstance(data, list) else [])
    out = []
    for r in rows:
        w = _first(r, "wallet", "address", "walletAddress", "wallet.address")
        if not is_solana_address(w):
            continue
        name = _first(r, "identity.name", "identity.twitter", "name", default="?")
        pnl = float(_first(r, "period.realized", "period.realizedPnl", "realized", "pnl.realized", default=0) or 0)
        out.append(Candidate(w, str(name), pnl, None, f"KOL {period}"))
    return out


ST_TOP = "https://data.solanatracker.io/top-traders/all/{}"


def from_st_top_traders(api_key: str, pages: int = 3) -> list[Candidate]:
    """Meilleurs traders toutes catégories (pas seulement les KOL, donc moins copiés)."""
    out = []
    for page in range(1, pages + 1):
        data = net.get_json(ST_TOP.format(page), {"expandPnl": "false", "sortBy": "total"},
                            headers={"x-api-key": api_key})
        for r in data.get("wallets") or []:
            w = r.get("wallet")
            if is_solana_address(w):
                out.append(Candidate(w, "top " + w[:6], float((r.get("summary") or {}).get("realized") or 0),
                                     None, "top traders"))
        if not data.get("hasNext"):
            break
    return out


def from_gecko(n_pools: int = 20, sleep_s: float = 2.1, log=print) -> list[Candidate]:
    pools = net.get_json(f"{GECKO_URL}/networks/solana/trending_pools", {"page": 1},
                         headers=GECKO_HEADERS).get("data", [])[:n_pools]
    agg: dict[str, dict] = defaultdict(lambda: {"buy": 0.0, "sell": 0.0, "tokens": set(), "n": 0})
    for p in pools:
        addr = p.get("attributes", {}).get("address")
        if not addr:
            continue
        try:
            trades = net.get_json(f"{GECKO_URL}/networks/solana/pools/{addr}/trades", None,
                                  headers=GECKO_HEADERS).get("data", [])
        except RuntimeError as exc:
            log(f"  pool {addr[:6]}…: {exc}")
            continue
        for t in trades:
            a = t.get("attributes", {})
            w = a.get("tx_from_address")
            if not is_solana_address(w):
                continue
            usd = float(a.get("volume_in_usd") or 0)
            g = agg[w]
            g["n"] += 1
            g["tokens"].add(addr)
            g["buy" if a.get("kind") == "buy" else "sell"] += usd
        time.sleep(sleep_s)
    out = []
    for w, g in agg.items():
        if g["buy"] > 0 and g["sell"] > 0 and len(g["tokens"]) >= 2:
            out.append(Candidate(w, "trending-pools", g["sell"] - g["buy"], g["n"], "gecko (USD, fenêtre courte)"))
    return sorted(out, key=lambda c: -c.pnl)


def filter_active(rpc: SolanaRPC, cands: list[Candidate], max_tx_24h: int = 1500, log=print) -> list[Candidate]:
    """Garde les wallets qui ont tradé dans les 24 h, écarte bots/MEV (> max_tx_24h tx)."""
    now = time.time()
    keep = []
    for c in cands:
        try:
            sigs = rpc.signatures(c.wallet, limit=1000)
        except RuntimeError as exc:
            log(f"  {c.wallet[:6]}…: RPC {exc}")
            continue
        recent = [s for s in sigs if (s.get("blockTime") or 0) > now - 86400]
        if not recent:
            log(f"  {c.label} {c.wallet[:6]}…: inactif depuis 24 h, écarté")
        elif len(recent) >= min(max_tx_24h, 1000) and len(sigs) == 1000:
            log(f"  {c.label} {c.wallet[:6]}…: ≥ {len(recent)} tx/24 h, probable bot, écarté")
        else:
            c.trades = len(recent)
            keep.append(c)
    return keep


def write_leaders(path, cands: list[Candidate]) -> None:
    lines = [f"# classement généré le {time.strftime('%Y-%m-%d %H:%M')} — ordre = rang",
             "# adresse                                      # nom | PnL | tx 24h | source"]
    for i, c in enumerate(cands, 1):
        lines.append(f"{c.wallet}  # n°{i} {c.label} | PnL {c.pnl:+,.0f} | {c.trades} tx/24h | {c.source}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
