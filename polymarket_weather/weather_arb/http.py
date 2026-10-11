"""Client HTTP minimal : retries, backoff, cache disque optionnel (pour la calibration)."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import requests

_SESSION = requests.Session()
_SESSION.headers["User-Agent"] = "weather-arb-paper/1.0 (research, paper trading only)"


def get(url: str, params: dict | list | None = None, *, timeout: float = 30, retries: int = 4,
        cache_dir: Path | None = None, cache_ttl_s: float | None = None, as_text: bool = False) -> Any:
    """GET avec retries. Si cache_dir est fourni, la réponse est mise en cache (TTL None = permanent)."""
    cache_file = None
    if cache_dir is not None:
        key = hashlib.sha256((url + json.dumps(params, sort_keys=True, default=str)).encode()).hexdigest()
        cache_file = Path(cache_dir) / f"{key}.json"
        if cache_file.exists():
            age = time.time() - cache_file.stat().st_mtime
            if cache_ttl_s is None or age < cache_ttl_s:
                return json.loads(cache_file.read_text(encoding="utf-8"))

    delay = 2.0
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            r = _SESSION.get(url, params=params, timeout=timeout)
            if r.status_code == 429 or r.status_code >= 500:
                raise requests.HTTPError(f"HTTP {r.status_code}", response=r)
            r.raise_for_status()
            data = r.text if as_text else r.json()
            if cache_file is not None:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(json.dumps(data), encoding="utf-8")
            return data
        except (requests.RequestException, ValueError) as exc:
            last_exc = exc
            resp = getattr(exc, "response", None)
            if resp is not None and 400 <= resp.status_code < 500 and resp.status_code != 429:
                break  # erreur client : inutile de réessayer
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
    raise RuntimeError(f"GET {url} échoué : {last_exc}") from last_exc
