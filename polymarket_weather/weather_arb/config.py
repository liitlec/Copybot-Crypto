"""Configuration lue dans l'environnement (.env optionnel). Aucune clé en dur."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:  # python-dotenv est optionnel
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass


def _f(name: str, default: float) -> float:
    return float(os.getenv(name, default))


def _i(name: str, default: int) -> int:
    return int(os.getenv(name, default))


GAMMA_URL = "https://gamma-api.polymarket.com"
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_ENSEMBLE = "https://ensemble-api.open-meteo.com/v1/ensemble"
OPEN_METEO_PREVIOUS_RUNS = "https://previous-runs-api.open-meteo.com/v1/forecast"
OPEN_METEO_HISTORICAL_FC = "https://historical-forecast-api.open-meteo.com/v1/forecast"
OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
IEM_ASOS = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"

# Tag Gamma : "temperature" seul ne renvoie rien.
TAG_SLUG = "daily-temperature"

# Sigma a priori (°C) par horizon, AVANT calibration. Volontairement plus large que
# l'ancien 0.7/1.5 : erreur typique d'ECMWF brut sur Tmax à une station d'aéroport.
DEFAULT_SIGMA_C = {0: 1.3, 1: 1.8, 2: 2.0, 3: 2.3, 4: 2.6, 5: 2.9, 6: 3.2, 7: 3.5}
SIGMA_GROWTH_AFTER_7 = 0.3  # °C par jour au-delà de J+7


@dataclass
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("WX_DATA_DIR", "data")))
    model: str = field(default_factory=lambda: os.getenv("WX_MODEL", "ecmwf_ifs025"))
    prob_model: str = field(default_factory=lambda: os.getenv("WX_PROB_MODEL", "normal"))
    min_edge: float = field(default_factory=lambda: _f("WX_MIN_EDGE", 0.08))
    max_spread: float = field(default_factory=lambda: _f("WX_MAX_SPREAD", 0.10))
    min_liquidity: float = field(default_factory=lambda: _f("WX_MIN_LIQUIDITY", 200))
    fee_rate: float = field(default_factory=lambda: _f("WX_FEE_RATE", 0.01))
    slippage: float = field(default_factory=lambda: _f("WX_SLIPPAGE", 0.01))
    stake_usd: float = field(default_factory=lambda: _f("WX_STAKE_USD", 10))
    max_trades_per_event: int = field(default_factory=lambda: _i("WX_MAX_TRADES_PER_EVENT", 1))
    prob_clip: float = field(default_factory=lambda: _f("WX_PROB_CLIP", 0.02))
    require_station: bool = field(default_factory=lambda: os.getenv("WX_REQUIRE_STATION", "1") == "1")
    scan_interval_min: int = field(default_factory=lambda: _i("WX_SCAN_INTERVAL_MIN", 30))
    # Shrinkage de la calibration station vers la calibration globale (pseudo-observations).
    shrink_k: int = 20
    sigma_floor_c: float = 0.6

    @property
    def trades_path(self) -> Path:
        return self.data_dir / "paper_trades.json"

    @property
    def predictions_path(self) -> Path:
        return self.data_dir / "predictions.jsonl"

    def sigma_table_path(self, kind: str = "high") -> Path:
        return self.data_dir / f"sigma_table_{kind}.json"

    @property
    def stations_override_path(self) -> Path:
        return self.data_dir / "stations.json"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"
