"""Filtre anti-rug appliqué au moment de copier un achat (seuils réglables dans .env, à recalibrer
avec data/token_info.jsonl). La fiche du token vient de Solana Tracker ; si elle n'arrive pas à temps,
l'achat est refusé (prudence)."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

from .tokeninfo import ST_TOKEN, summarize


def _f(name: str, default: float) -> float:
    return float(os.getenv(name, default))


class RugFilter:
    def __init__(self, api_key: str | None, log_path: Path | None = None, timeout_s: float = 2.0):
        self.key, self.log_path, self.timeout = api_key, Path(log_path) if log_path else None, timeout_s
        self.min_liq_usd = _f("RF_MIN_LIQUIDITY_USD", 2000)
        self.min_pool_age_s = _f("RF_MIN_POOL_AGE_S", 60)
        self.max_top10 = _f("RF_MAX_TOP10_PCT", 60)
        self.max_dev = _f("RF_MAX_DEV_PCT", 15)
        self.max_bundlers = _f("RF_MAX_BUNDLERS_PCT", 40)
        self.max_insiders = _f("RF_MAX_INSIDERS_PCT", 30)
        self.max_impact = _f("RF_MAX_IMPACT", 0.03)
        self._session = requests.Session()

    def reasons(self, info: dict) -> list[str]:
        """Liste des motifs de refus (vide = acceptable)."""
        r = []
        if info.get("mint_authority"):
            r.append("autorité mint active")
        if info.get("freeze_authority"):
            r.append("autorité freeze active")
        if info.get("rugged_flag"):
            r.append("déjà signalé rugged")
        liq = info.get("liquidity_usd")
        if liq is None or liq < self.min_liq_usd:
            r.append(f"liquidité < {self.min_liq_usd:.0f} $")
        age = info.get("pool_age_s")
        if age is not None and age < self.min_pool_age_s:
            r.append(f"pool de moins de {self.min_pool_age_s:.0f} s")
        for key, lim, label in (("top10_pct", self.max_top10, "top 10"), ("dev_pct", self.max_dev, "dev"),
                                ("bundlers_pct", self.max_bundlers, "bundlers"),
                                ("insiders_pct", self.max_insiders, "insiders")):
            v = info.get(key)
            if v is not None and v > lim:
                r.append(f"{label} > {lim:.0f} %")
        return r

    def fetch(self, mint: str) -> dict | None:
        if not self.key:
            return None
        try:
            resp = self._session.get(ST_TOKEN.format(mint), headers={"x-api-key": self.key}, timeout=self.timeout)
            return summarize(resp.json(), time.time()) if resp.status_code == 200 else None
        except (requests.RequestException, ValueError):
            return None

    def check(self, ev) -> str | None:
        """Appelé avant la cotation d'achat : renvoie un motif de refus ou None."""
        t0 = time.time()
        info = self.fetch(ev.mint)
        reasons = ["fiche token indisponible"] if info is None else self.reasons(info)
        if self.log_path:
            row = {"ts": round(t0, 2), "check_ms": round((time.time() - t0) * 1000), "mint": ev.mint,
                   "leader": ev.wallet, "leader_buy_sol": round(ev.sol_amount, 4), "refused": reasons,
                   **(info or {})}
            with self.log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
        return ("anti-rug : " + reasons[0]) if reasons else None
