"""Hub gRPC Yellowstone (Chainstack) en lecture seule : abonnement à toutes les transactions pump.fun, comme
le hub du PC (start_grpc_hub.bat --pumpfun hub/pumpfun.jsonl). Aucune transaction n'est envoyée.

Heure de chaque slot (bt) : heure du premier message reçu pour ce slot (mises à jour de slots du même flux),
sinon l'horodatage serveur du message (created_at), comme le repli du hub du PC."""
from __future__ import annotations

import os
import threading
import time

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58encode(b: bytes) -> str:
    n = int.from_bytes(b, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = B58[r] + out
    return "1" * (len(b) - len(b.lstrip(b"\0"))) + out


def to_tx_dict(info, slot: int, bt: float) -> dict:
    """Transaction gRPC -> dict au format JSON RPC « jsonParsed » (ce qu'attend pumprec.parse)."""
    msg, meta = info.transaction.message, info.meta
    nsig = msg.header.num_required_signatures
    keys = [{"pubkey": b58encode(k), "signer": i < nsig} for i, k in enumerate(msg.account_keys)]

    def tb(lst):
        return [{"accountIndex": b.account_index, "mint": b.mint, "owner": b.owner,
                 "uiTokenAmount": {"amount": b.ui_token_amount.amount, "decimals": b.ui_token_amount.decimals}}
                for b in lst]

    return {"slot": slot, "blockTime": bt,
            "transaction": {"message": {"accountKeys": keys}},
            "meta": {"fee": meta.fee, "preBalances": list(meta.pre_balances), "postBalances": list(meta.post_balances),
                     "preTokenBalances": tb(meta.pre_token_balances), "postTokenBalances": tb(meta.post_token_balances),
                     "loadedAddresses": {"writable": [b58encode(a) for a in meta.loaded_writable_addresses],
                                         "readonly": [b58encode(a) for a in meta.loaded_readonly_addresses]}}}


class GrpcHub:
    """Flux unique : transactions des comptes `accounts` (programme pump.fun) + mises à jour de slots.
    Chaque transaction est passée brute à sink(t, heure_slot, reçu, créé), sans conversion dans ce fil."""

    def __init__(self, endpoint: str, token: str, accounts: list[str], sink, log=print):
        self.endpoint = endpoint.replace("https://", "").replace("http://", "")
        self.token, self.accounts, self.sink, self.log = token, accounts, sink, log
        self.slot_time: dict[int, float] = {}
        self._stop = threading.Event()

    def start(self) -> "GrpcHub":
        threading.Thread(target=self._run, daemon=True).start()
        return self

    def _channel(self):
        import grpc
        ca = os.getenv("SSL_CERT_FILE") or os.getenv("REQUESTS_CA_BUNDLE")
        roots = open(ca, "rb").read() if ca else None
        creds = grpc.composite_channel_credentials(
            grpc.ssl_channel_credentials(roots),
            grpc.metadata_call_credentials(lambda ctx, cb: cb((("x-token", self.token),), None)))
        return grpc.secure_channel(self.endpoint, creds, options=[
            ("grpc.max_receive_message_length", 64 * 1024 * 1024), ("grpc.keepalive_time_ms", 30_000)])

    def _requests(self, pb):
        req = pb.SubscribeRequest(commitment=pb.CommitmentLevel.CONFIRMED)
        req.transactions["pumpfun"].CopyFrom(pb.SubscribeRequestFilterTransactions(
            vote=False, failed=False, account_include=self.accounts))
        req.slots["slots"].CopyFrom(pb.SubscribeRequestFilterSlots())
        yield req
        n = 0
        while not self._stop.is_set():  # ping régulier : certains fournisseurs coupent les flux muets
            time.sleep(10)
            n += 1
            yield pb.SubscribeRequest(ping=pb.SubscribeRequestPing(id=n))

    def _run(self) -> None:
        import grpc
        from .yproto import geyser_pb2 as pb, geyser_pb2_grpc as pbg
        while not self._stop.is_set():
            try:
                stub = pbg.GeyserStub(self._channel())
                self.log("  gRPC : abonnement pump.fun actif")
                for upd in stub.Subscribe(self._requests(pb)):
                    now = time.time()
                    created = upd.created_at.seconds + upd.created_at.nanos / 1e9 if upd.HasField("created_at") else None
                    kind = upd.WhichOneof("update_oneof")
                    if kind == "slot":
                        self.slot_time.setdefault(upd.slot.slot, min(created, now) if created else now)
                        if len(self.slot_time) > 5000:
                            for s in sorted(self.slot_time)[:2500]:
                                del self.slot_time[s]
                    elif kind == "transaction":
                        t = upd.transaction
                        bt = self.slot_time.get(t.slot)
                        if bt is None:
                            bt = min(created, now) if created else now
                        self.sink(t, bt, now, created)
            except grpc.RpcError as exc:
                self.log(f"  gRPC : {exc.code()} {(exc.details() or '')[:120]} ; reconnexion dans 5 s")
            except Exception as exc:  # noqa: BLE001 - on reconnecte quoi qu'il arrive
                self.log(f"  gRPC : {type(exc).__name__}: {str(exc)[:120]} ; reconnexion dans 5 s")
            time.sleep(5)
