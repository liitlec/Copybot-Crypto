"""HTTP + JSON-RPC Solana (lecture seule), retries, cache disque optionnel."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import requests

_S = requests.Session()
_S.headers["User-Agent"] = "copysim-paper/1.0 (read-only research)"


def _retry(fn, retries: int = 5):
    delay = 1.0
    for attempt in range(retries):
        try:
            return fn()
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            resp = getattr(exc, "response", None)
            if resp is not None and 400 <= resp.status_code < 500 and resp.status_code != 429:
                raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}") from exc
            if attempt == retries - 1:
                raise RuntimeError(str(exc)) from exc
            time.sleep(delay)
            delay = min(delay * 2, 30)


def _cache_path(cache_dir: Path | None, key: str) -> Path | None:
    if cache_dir is None:
        return None
    return Path(cache_dir) / f"{hashlib.sha256(key.encode()).hexdigest()}.json"


def get_json(url: str, params: dict | None = None, *, headers: dict | None = None,
             cache_dir: Path | None = None, timeout: float = 30) -> Any:
    cp = _cache_path(cache_dir, url + json.dumps(params, sort_keys=True))
    if cp and cp.exists():
        return json.loads(cp.read_text())

    def call():
        r = _S.get(url, params=params, headers=headers, timeout=timeout)
        if r.status_code == 429 or r.status_code >= 500:
            raise requests.HTTPError(f"HTTP {r.status_code}", response=None)
        r.raise_for_status()
        return r.json()

    data = _retry(call)
    if cp:
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps(data))
    return data


class SolanaRPC:
    """Uniquement des méthodes de lecture : getSignaturesForAddress, getTransaction."""

    def __init__(self, url: str, cache_dir: Path | None = None):
        self.url = url
        self.cache_dir = cache_dir
        self._id = 0

    def _post(self, payload):
        def call():
            r = _S.post(self.url, json=payload, timeout=60)
            if r.status_code == 429 or r.status_code >= 500:
                raise requests.HTTPError(f"HTTP {r.status_code}", response=None)
            r.raise_for_status()
            return r.json()
        return _retry(call)

    def call(self, method: str, params: list) -> Any:
        self._id += 1
        res = self._post({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params})
        if "error" in res:
            raise RuntimeError(f"RPC {method}: {res['error']}")
        return res["result"]

    def signatures(self, address: str, before: str | None = None, until: str | None = None,
                   limit: int = 1000) -> list[dict]:
        opts: dict = {"limit": limit}
        if before:
            opts["before"] = before
        if until:
            opts["until"] = until
        return self.call("getSignaturesForAddress", [address, opts])

    def transactions(self, sigs: list[str], batch: int = 20) -> list[dict | None]:
        """getTransaction en batch JSON-RPC (repli unitaire si le fournisseur refuse le batch).
        Les transactions finalisées sont immuables : mises en cache disque."""
        out: dict[str, dict | None] = {}
        todo = []
        for s in sigs:
            cp = _cache_path(self.cache_dir, "tx:" + s)
            if cp and cp.exists():
                out[s] = json.loads(cp.read_text())
            else:
                todo.append(s)
        opts = {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0, "commitment": "confirmed"}
        for i in range(0, len(todo), batch):
            chunk = todo[i:i + batch]
            try:
                payload = [{"jsonrpc": "2.0", "id": j, "method": "getTransaction", "params": [s, opts]}
                           for j, s in enumerate(chunk)]
                res = self._post(payload)
                if not isinstance(res, list):
                    raise RuntimeError("batch non supporté")
                by_id = {r.get("id"): r.get("result") for r in res}
                results = [by_id.get(j) for j in range(len(chunk))]
            except RuntimeError:
                results = [self.call("getTransaction", [s, opts]) for s in chunk]
            for s, tx in zip(chunk, results):
                out[s] = tx
                cp = _cache_path(self.cache_dir, "tx:" + s)
                if cp and tx is not None:
                    cp.parent.mkdir(parents=True, exist_ok=True)
                    cp.write_text(json.dumps(tx))
        return [out.get(s) for s in sigs]
