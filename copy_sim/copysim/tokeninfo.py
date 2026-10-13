"""Fiche de chaque token au moment où un achat est copié (data/token_info.jsonl), pour tester plus tard
des filtres anti-rug : âge du token et du pool, liquidité, LP brûlée, autorités mint/freeze, répartition
des holders (top 10, dev, bundlers, snipers, insiders) et score de risque Solana Tracker.

Tourne dans un thread à part : la copie n'attend jamais la fiche. Lecture seule."""
from __future__ import annotations

import json
import queue
import threading
import time
from pathlib import Path

import requests

ST_TOKEN = "https://data.solanatracker.io/tokens/{}"


def summarize(d: dict, now: float) -> dict:
    """Extrait les champs utiles d'une réponse /tokens/{mint} de Solana Tracker."""
    tok = d.get("token") or {}
    created = (tok.get("creation") or {}).get("created_time")
    pools = d.get("pools") or []
    main = max(pools, key=lambda p: (p.get("liquidity") or {}).get("usd") or 0, default={})
    risk = d.get("risk") or {}
    pct = lambda k: (risk.get(k) or {}).get("totalPercentage")
    sec = main.get("security") or {}
    pool_created = main.get("createdAt")
    return {
        "token_age_s": round(now - created, 1) if created else None,
        "creator": (tok.get("creation") or {}).get("creator"),
        "pool_market": main.get("market"),
        "pool_age_s": round(now - pool_created / 1000, 1) if pool_created else None,
        "liquidity_usd": (main.get("liquidity") or {}).get("usd"),
        "liquidity_usd_all_pools": sum((p.get("liquidity") or {}).get("usd") or 0 for p in pools),
        "n_pools": len(pools),
        "lp_burn_pct": main.get("lpBurn"),
        "mint_authority": sec.get("mintAuthority"),
        "freeze_authority": sec.get("freezeAuthority"),
        "deployer": main.get("deployer"),
        "pool_buys": (main.get("txns") or {}).get("buys"),
        "pool_sells": (main.get("txns") or {}).get("sells"),
        "risk_score": risk.get("score"),
        "rugged_flag": risk.get("rugged"),
        "top10_pct": risk.get("top10"),
        "dev_pct": (risk.get("dev") or {}).get("percentage"),
        "bundlers_pct": pct("bundlers"),
        "snipers_pct": pct("snipers"),
        "insiders_pct": pct("insiders"),
        "risks": [r.get("name") for r in risk.get("risks", [])],
    }


class TokenInfoRecorder(threading.Thread):
    def __init__(self, api_key: str | None, out_path: Path):
        super().__init__(daemon=True)
        self.key, self.out = api_key, Path(out_path)
        self.q: queue.Queue = queue.Queue()
        self._session = requests.Session()

    def submit(self, ev, res: dict) -> None:
        self.q.put((ev, res, time.time()))

    def _fetch(self, mint: str) -> dict | None:
        if not self.key:
            return None
        for _ in range(3):
            try:
                r = self._session.get(ST_TOKEN.format(mint), headers={"x-api-key": self.key}, timeout=10)
                if r.status_code == 200:
                    return r.json()
                if r.status_code != 429:
                    return None
            except (requests.RequestException, ValueError):
                pass
            time.sleep(1)
        return None

    def run(self) -> None:
        while True:
            ev, res, t = self.q.get()
            d = self._fetch(ev.mint)
            row = {"ts": round(t, 2), "fetched_ts": round(time.time(), 2), "mint": ev.mint, "leader": ev.wallet,
                   "leader_buy_sol": round(ev.sol_amount, 4), "our_sol": res.get("sol"),
                   "our_impact": res.get("note", "").removeprefix("impact="),
                   "entry_vs_leader": (res["price"] / res["leader_price"] - 1) if res.get("leader_price") else None,
                   "ok": d is not None}
            if d is not None:
                row.update(summarize(d, time.time()))
            with self.out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
