"""Prix en direct par gRPC Yellowstone (Chainstack), en lecture seule, pour les positions à règle du test papier.

Abonnement aux transactions qui touchent les pools suivis (account_include). Pour chaque swap, le prix est lu dans la
transaction elle-même : variation des soldes des coffres du pool (comptes de jetons détenus par le pool ou par
l'autorité Raydium) en jeton de base et en jeton de cotation, prix = |Δcotation| / |Δbase|. Ce calcul ne dépend pas
du type de pool (produit constant ou concentré) ; c'est le prix d'exécution du swap, à ±1-2 % du prix moyen.
Le prix en dollars = prix en cotation × prix en dollars de la cotation (relevé par GeckoTerminal à chaque cycle).

Aucune transaction n'est envoyée. Sans grpcio, sans fichier grpc.env ou en cas de coupure, rien ne casse : les
positions restent suivies par GeckoTerminal toutes les 15 s."""
from __future__ import annotations

import os
import queue
import sys
import threading
import time
from pathlib import Path

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
# autorités qui détiennent les coffres de plusieurs pools (Raydium AMM v4, Raydium CPMM, Meteora DAMM v2) ; ailleurs
# (PumpSwap, Meteora DLMM, Orca, Raydium CLMM) les coffres appartiennent au compte du pool lui-même
AUTORITES = {"5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1", "GpMZbSM2GgvTKHJirzeGfMFoaZ8UR2X7F4v8vHTvxFbL",
             "HLnpSz9h2S4hiLQ43rnSD9XkcUThA7B8hQMKmDaiTLcC"}


def b58encode(b: bytes) -> str:
    n = int.from_bytes(b, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = B58[r] + out
    return "1" * (len(b) - len(b.lstrip(b"\0"))) + out


def lire_env(path):
    env = {}
    if Path(path).exists():
        for ln in Path(path).read_text().splitlines():
            if "=" in ln and not ln.lstrip().startswith("#"):
                k, v = ln.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def prix_swap(pre, post, pool, base):
    """pre/post : [(index, mint, owner, montant_ui)] ; prix du jeton `base` en jeton de cotation pour ce pool, ou None.
    Seuls les comptes détenus par le pool (ou une autorité de pools connue) comptent."""
    owners = {pool} | AUTORITES
    before = {i: (m, o, a) for i, m, o, a in pre}
    d = {}
    for i, m, o, a in post:
        if o not in owners:
            continue
        a0 = before.get(i, (m, o, 0.0))[2]
        d.setdefault(m, 0.0)
        d[m] += a - a0
    db = d.pop(base, 0.0)
    if not db or not d:
        return None
    quote, dq = max(d.items(), key=lambda kv: abs(kv[1]))
    if not dq or (db > 0) == (dq > 0):  # un swap fait entrer l'un et sortir l'autre
        return None
    return quote, abs(dq) / abs(db)


class Flux:
    def __init__(self, endpoint: str, token: str, log=print):
        self.endpoint = endpoint.replace("https://", "").replace("http://", "").rstrip("/")
        self.token, self.log = token, log
        self.pools: dict[str, str] = {}          # pool -> jeton de base suivi
        self.prix: dict[str, tuple] = {}         # pool -> (heure, prix en cotation, jeton de cotation)
        self._q: queue.Queue = queue.Queue()
        self.actif = False

    @classmethod
    def depuis_fichier(cls, path, log=print):
        env = lire_env(path)
        ep, tok = env.get("GRPC_ENDPOINT"), env.get("GRPC_TOKEN")
        if not ep or not tok:
            return None
        try:
            import grpc  # noqa: F401
        except ImportError:
            log("gRPC : module grpcio absent, suivi par GeckoTerminal seulement")
            return None
        return cls(ep, tok, log).start()

    def start(self) -> "Flux":
        threading.Thread(target=self._run, daemon=True).start()
        return self

    def suivre(self, pools: dict[str, str]) -> None:
        """Remplace l'ensemble des pools suivis (pool -> jeton de base) ; l'abonnement est mis à jour sans coupure."""
        if pools != self.pools:
            self.pools = dict(pools)
            self._q.put(dict(pools))

    def _channel(self):
        import grpc
        creds = grpc.composite_channel_credentials(
            grpc.ssl_channel_credentials(),
            grpc.metadata_call_credentials(lambda ctx, cb: cb((("x-token", self.token),), None)))
        return grpc.secure_channel(self.endpoint, creds, options=[
            ("grpc.max_receive_message_length", 64 * 1024 * 1024), ("grpc.keepalive_time_ms", 30_000)])

    def _requests(self, pb):
        def req(pools):
            r = pb.SubscribeRequest(commitment=pb.CommitmentLevel.PROCESSED)
            if pools:
                r.transactions["pools"].CopyFrom(pb.SubscribeRequestFilterTransactions(
                    vote=False, failed=False, account_include=sorted(pools)))
            return r
        yield req(self.pools)
        n = 0
        while True:
            try:
                pools = self._q.get(timeout=10)
                yield req(pools)
            except queue.Empty:  # ping régulier : certains fournisseurs coupent les flux muets
                n += 1
                yield pb.SubscribeRequest(ping=pb.SubscribeRequestPing(id=n))

    def _sink(self, info):
        meta = info.transaction.meta
        msg = info.transaction.transaction.message
        keys = {b58encode(k) for k in msg.account_keys}
        keys |= {b58encode(a) for a in meta.loaded_writable_addresses}
        pre = [(b.account_index, b.mint, b.owner, b.ui_token_amount.ui_amount) for b in meta.pre_token_balances]
        post = [(b.account_index, b.mint, b.owner, b.ui_token_amount.ui_amount) for b in meta.post_token_balances]
        now = time.time()
        for pool, base in list(self.pools.items()):
            if pool in keys:
                r = prix_swap(pre, post, pool, base)
                if r:
                    self.prix[pool] = (now, r[1], r[0])

    def _run(self) -> None:
        import grpc
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from yproto import geyser_pb2 as pb, geyser_pb2_grpc as pbg
        while True:
            try:
                stub = pbg.GeyserStub(self._channel())
                self.log("gRPC : abonnement actif")
                self.actif = True
                for upd in stub.Subscribe(self._requests(pb)):
                    if upd.WhichOneof("update_oneof") == "transaction":
                        self._sink(upd.transaction)
            except grpc.RpcError as exc:
                self.log(f"gRPC : {exc.code()} {(exc.details() or '')[:120]} ; reconnexion dans 15 s")
            except Exception as exc:  # noqa: BLE001 - on reconnecte quoi qu'il arrive
                self.log(f"gRPC : {type(exc).__name__}: {str(exc)[:120]} ; reconnexion dans 15 s")
            self.actif = False
            time.sleep(15)
