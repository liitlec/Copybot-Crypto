"""Règle « lancement propre » du PC (nuit/scalp_regle.py), même code : copysim/scalpgrpc.py."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from copysim import scalpgrpc as _g  # noqa: E402
from copysim.scalpgrpc import CREATE_RENT, ENTRY_S, HOLD_S, MAX_SOL, evaluate  # noqa: E402,F401


def launches(path=ROOT / "data_grpc" / "pumpfun.jsonl", since=0.0):
    return _g.launches(Path(path), since)
