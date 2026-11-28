"""Flux temps réel des transactions des leaders (websocket `logsSubscribe`, lecture seule).

Le RPC pousse la signature dès que la transaction est confirmée (~0,5-1 s après le leader), au lieu
d'attendre l'indexation de getSignaturesForAddress (plusieurs secondes). Un thread par leader,
reconnexion automatique.
"""
from __future__ import annotations

import json
import os
import queue
import threading
import time
from urllib.parse import urlparse

try:
    import websocket  # websocket-client
except ImportError:  # pragma: no cover
    websocket = None


def ws_url(rpc_url: str) -> str:
    u = urlparse(rpc_url)
    return rpc_url.replace(f"{u.scheme}://", "wss://" if u.scheme == "https" else "ws://", 1)


def _proxy_kwargs() -> dict:
    p = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    if not p:
        return {}
    u = urlparse(p)
    return {"http_proxy_host": u.hostname, "http_proxy_port": u.port, "proxy_type": "http"}


class SignatureStream:
    def __init__(self, rpc_url: str, wallets: list[str], log=print):
        if websocket is None:
            raise RuntimeError("module websocket-client absent (pip install websocket-client)")
        self.url, self.wallets, self.log = ws_url(rpc_url), wallets, log
        self.q: queue.Queue[tuple[str, str, float]] = queue.Queue()
        self._stop = threading.Event()

    def start(self) -> "SignatureStream":
        # une seule connexion, un abonnement par wallet : Helius limite le nombre de connexions simultanées
        threading.Thread(target=self._run, daemon=True).start()
        return self

    def stop(self) -> None:
        self._stop.set()

    def handle(self, msg: str, subs: dict[int, str], pending: dict[int, str]) -> None:
        """Accusé d'abonnement (id -> n° d'abonnement) ou notification de transaction."""
        try:
            d = json.loads(msg)
        except ValueError:
            return
        if "id" in d and d.get("id") in pending and "result" in d:
            subs[d["result"]] = pending.pop(d["id"])
            if not pending:
                self.log(f"  websocket : {len(subs)} abonnement(s) actif(s)")
            return
        try:
            params = d["params"]
            v = params["result"]["value"]
        except (KeyError, TypeError):
            return  # ping, erreur…
        wallet = subs.get(params.get("subscription"))
        if wallet and v.get("err") is None:
            self.q.put((wallet, v["signature"], time.time()))

    def _run(self) -> None:
        ca = os.getenv("SSL_CERT_FILE") or os.getenv("REQUESTS_CA_BUNDLE")
        while not self._stop.is_set():
            subs: dict[int, str] = {}
            pending = {i: w for i, w in enumerate(self.wallets, 1)}

            def on_open(ws):
                for i, w in list(pending.items()):
                    ws.send(json.dumps({"jsonrpc": "2.0", "id": i, "method": "logsSubscribe",
                                        "params": [{"mentions": [w]}, {"commitment": "confirmed"}]}))

            app = websocket.WebSocketApp(self.url, on_open=on_open,
                                         on_message=lambda ws, m: self.handle(m, subs, pending),
                                         on_error=lambda ws, e: self.log(f"  websocket : {e}"))
            try:
                app.run_forever(ping_interval=30, ping_timeout=10,
                                sslopt={"ca_certs": ca} if ca else None, **_proxy_kwargs())
            except Exception as exc:  # noqa: BLE001 - on reconnecte quoi qu'il arrive
                self.log(f"  websocket : {exc}")
            if pending and not self._stop.is_set():
                self.log(f"  websocket coupé ({len(pending)} abonnement(s) non confirmé(s)), reconnexion")
            if not self._stop.is_set():
                time.sleep(3)
