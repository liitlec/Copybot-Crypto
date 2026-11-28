"""Configuration (env / .env). Lecture seule : aucune clé privée n'est jamais lue ni utilisée."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

WSOL = "So11111111111111111111111111111111111111112"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
USD_MINTS = {USDC, USDT}
LAMPORTS = 1_000_000_000
GECKO_URL = "https://api.geckoterminal.com/api/v2"


def _f(name: str, default: float) -> float:
    return float(os.getenv(name, default))


@dataclass
class Settings:
    rpc_url: str = field(default_factory=lambda: os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com"))
    jup_quote_url: str = field(default_factory=lambda: os.getenv("JUP_QUOTE_URL", "https://api.jup.ag/swap/v1/quote"))
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("CS_DATA_DIR", "data")))
    bankroll_sol: float = field(default_factory=lambda: _f("CS_BANKROLL_SOL", 1.0))
    size_mode: str = field(default_factory=lambda: os.getenv("CS_SIZE_MODE", "fraction"))
    size: float = field(default_factory=lambda: _f("CS_SIZE", 0.2))
    max_open: int = field(default_factory=lambda: int(_f("CS_MAX_OPEN", 5)))
    max_leader_buy_sol: float = field(default_factory=lambda: _f("CS_MAX_LEADER_BUY_SOL", 0))
    latency_s: float = field(default_factory=lambda: _f("CS_LATENCY_S", 2))
    slippage_bps: float = field(default_factory=lambda: _f("CS_SLIPPAGE_BPS", 100))
    bot_fee_pct: float = field(default_factory=lambda: _f("CS_BOT_FEE_PCT", 1.0))
    tx_fee_sol: float = field(default_factory=lambda: _f("CS_TX_FEE_SOL", 0.0005))
    rotate_after_losses: int = field(default_factory=lambda: int(_f("CS_ROTATE_AFTER_LOSSES", 2)))
    poll_s: float = field(default_factory=lambda: _f("CS_POLL_S", 3))
    min_trade_sol: float = 0.01

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"
