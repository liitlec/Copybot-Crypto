"""Constantes et formules de courbe du scalp pump.fun (copie de nuit/scalp.py du PC, partie utilisée par les règles
et le score). Les données viennent du hub gRPC du cloud : data_grpc/pumpfun.jsonl."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from copysim.scalpgrpc import (BASE_COST, FEE, K, SIZE, V_SOL0, V_TOK0, V_TOK_OFFSET,  # noqa: E402,F401
                               sol_for, tokens_for)
