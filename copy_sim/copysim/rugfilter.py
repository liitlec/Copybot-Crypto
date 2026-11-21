"""Filtre anti-rug appliqué au moment de copier un achat (seuils réglables dans .env, à recalibrer
avec data/token_info.jsonl). La fiche du token vient de Solana Tracker ; si elle n'arrive pas à temps,
l'achat est refusé (prudence).

Si Solana Tracker ne répond pas (crédits épuisés, panne), repli gratuit : DexScreener pour la liquidité et
l'âge du pool, RPC Solana pour les autorités mint/freeze. La répartition des holders n'est alors pas connue
et n'est pas contrôlée."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

from .tokeninfo import ST_TOKEN, summarize

DEXSCREENER = "https://api.dexscreener.com/latest/dex/tokens/{}"


def _f(name: str, default: float) -> float:
    return float(os.getenv(name, default))


class RugFilter:
    def __init__(self, api_key: str | None, log_path: Path | None = None, timeout_s: float = 2.0,
                 rpc_url: str | None = None):
        self.key, self.log_path, self.timeout = api_key, Path(log_path) if log_path else None, timeout_s
        self.rpc_url = rpc_url or os.getenv("SOLANA_RPC_URL")
        self.st_down_until = 0.0  # après un refus de Solana Tracker, on passe au repli pendant 10 min
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
        if not info.get("liquidity_unknown") and (liq is None or liq < self.min_liq_usd):
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
        if self.key and time.time() >= self.st_down_until:
            try:
                resp = self._session.get(ST_TOKEN.format(mint), headers={"x-api-key": self.key}, timeout=self.timeout)
                if resp.status_code == 200:
                    return {**summarize(resp.json(), time.time()), "source": "solanatracker"}
                if resp.status_code in (401, 402, 403, 429):
                    self.st_down_until = time.time() + 600
            except (requests.RequestException, ValueError):
                pass
        return self.fetch_free(mint)

    def fetch_free(self, mint: str) -> dict | None:
        """Repli sans clé : DexScreener (liquidité, âge du pool) + RPC (autorités mint/freeze)."""
        try:
            pairs = self._session.get(DEXSCREENER.format(mint), timeout=self.timeout).json().get("pairs") or []
        except (requests.RequestException, ValueError):
            return None
        if not pairs:
            return None
        liq = lambda p: (p.get("liquidity") or {}).get("usd")
        main = max(pairs, key=lambda p: liq(p) or 0)
        created = [p["pairCreatedAt"] for p in pairs if p.get("pairCreatedAt")]
        info = {"source": "dexscreener", "pool_market": main.get("dexId"), "n_pools": len(pairs),
                # pool en courbe de lancement : liquidité virtuelle non publiée -> critère non applicable
                "liquidity_usd": liq(main) if any(liq(p) for p in pairs) else None,
                "liquidity_unknown": not any(liq(p) for p in pairs),
                "pool_age_s": round(time.time() - min(created) / 1000, 1) if created else None}
        auth = self._authorities(mint)
        if auth is None:
            return None
        return {**info, **auth}

    def _authorities(self, mint: str) -> dict | None:
        if not self.rpc_url:
            return None
        try:
            r = self._session.post(self.rpc_url, json={"jsonrpc": "2.0", "id": 1, "method": "getAccountInfo",
                                                       "params": [mint, {"encoding": "jsonParsed"}]}, timeout=self.timeout)
            parsed = r.json()["result"]["value"]["data"]["parsed"]["info"]
            return {"mint_authority": parsed.get("mintAuthority"), "freeze_authority": parsed.get("freezeAuthority")}
        except (requests.RequestException, ValueError, KeyError, TypeError):
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
