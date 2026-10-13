"""Enregistre le prix de sortie réel de chaque position ouverte (cotation Jupiter de vente de toute la
ligne), toutes les ~1,5 s, pour tester plus tard des règles de sortie (take profit, stop, durée max)
sans relancer de test live. Lecture seule : aucune transaction n'est construite."""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import requests

from .config import LAMPORTS, WSOL


class PathRecorder(threading.Thread):
    def __init__(self, state, quote_url: str, out_path: Path, interval_s: float = 1.5):
        super().__init__(daemon=True)
        self.state, self.url, self.out, self.interval = state, quote_url, Path(out_path), interval_s
        self._session = requests.Session()

    def _quote_sell(self, mint: str, raw_amount: int) -> dict | None:
        try:  # pas de retry : une cotation manquée vaut mieux que retarder les vrais trades
            r = self._session.get(self.url, params={"inputMint": mint, "outputMint": WSOL, "amount": raw_amount,
                                                    "slippageBps": 100}, timeout=5)
            return r.json() if r.status_code == 200 else None
        except (requests.RequestException, ValueError):
            return None

    def run(self) -> None:
        i = 0
        while True:
            try:
                positions = list(self.state.positions.values())
            except RuntimeError:  # dict modifié pendant la lecture
                positions = []
            if positions:
                p = positions[i % len(positions)]  # une cotation par intervalle, à tour de rôle
                i += 1
                raw = int(p["tokens"] * 10 ** p["decimals"])
                q = self._quote_sell(p["mint"], raw) if raw > 0 else None
                if q and q.get("outAmount"):
                    sol = int(q["outAmount"]) / LAMPORTS
                    row = {"ts": round(time.time(), 2), "mint": p["mint"], "leader": p["leader"],
                           "opened_ts": p["opened_ts"], "age_s": round(time.time() - p["opened_ts"], 1),
                           "tokens": p["tokens"], "cost_sol": p["cost_sol"], "sell_value_sol": sol,
                           "ret_vs_cost": round(sol / p["cost_sol"] - 1, 4) if p["cost_sol"] else None,
                           "impact": q.get("priceImpactPct")}
                    with self.out.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(row) + "\n")
            time.sleep(self.interval)
