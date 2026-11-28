"""Enregistreur Pump.fun (lecture seule) pour mesurer le scalp de quelques secondes.

Chaque création de token vue par le gRPC, puis toutes les transactions de sa courbe pendant WINDOW_S secondes,
avec leur ordre EXACT dans le bloc (slot + index), l'état de la courbe, et ce que chaque acheteur a payé pour
passer (priority fee, tip Jito). Une ligne JSON compacte par transaction dans hub/pumpfun.jsonl :
  slot, idx, bt (heure du slot), seen, sig, signer, kind (create / buy / sell), mint, curve_acc, quote (sol ou
  wsol), sol (SOL entrés (+) ou sortis (−) de la courbe), curve (SOL de la courbe après, loyer compris en
  « sol »), vault_tok (tokens dans la courbe après), curve_tok (tokens sortis de la courbe), tok (tokens du
  signataire), px (prix côté courbe), signer_sol, fee, prio, jito (tip Jito), cu.
"""
from __future__ import annotations

import json
import queue
import threading
import time
from collections import Counter, defaultdict
from pathlib import Path

from .grpchub import b58encode, to_tx_dict

PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
WSOL = "So11111111111111111111111111111111111111112"
JITO_TIPS = {
    "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5", "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",
    "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY", "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
    "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh", "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
    "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL", "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT",
}
WINDOW_S = 600  # on suit chaque token 10 min après sa création
CREATE_LOGS = ("Program log: Instruction: Create", "Program log: Instruction: CreateV2")


def pump_instructions(logs: list[str]) -> list[str]:
    """Instructions exécutées PAR le programme pump.fun (pile d'appels reconstituée depuis les logs : le
    « CreateIdempotent » du programme des comptes de tokens ne doit pas passer pour une création)."""
    stack, out = [], []
    for l in logs:
        if l.startswith("Program ") and " invoke [" in l:
            stack.append(l.split()[1])
        elif l.startswith("Program ") and (l.endswith(" success") or " failed" in l):
            if stack:
                stack.pop()
        elif l.startswith("Program log: Instruction: ") and stack and stack[-1] == PUMP_PROGRAM:
            out.append(l[len("Program log: Instruction: "):].strip())
    return out


def _kind(logs: list[str]) -> str | None:
    ins = pump_instructions(logs)
    if any(i in ("Create", "CreateV2") for i in ins):
        return "create"
    if any(i.startswith("Buy") for i in ins):
        return "buy"
    if any(i.startswith("Sell") for i in ins):
        return "sell"
    return None


def parse(tx: dict, logs: list[str], ixs: list[list[str]] | None = None) -> dict | None:
    """ixs : comptes de chaque instruction du programme pump.fun (niveau 1 ou appelée par un autre programme).
    Buy/Sell classiques : token = 3e compte, courbe = 4e, SOL de la courbe en lamports. Versions récentes
    (V2/V3, cotées en WSOL) : la courbe est le propriétaire qui détient à la fois le token et du WSOL."""
    kind = _kind(logs)
    if kind is None:
        return None
    meta = tx["meta"]
    keys = [k["pubkey"] for k in tx["transaction"]["message"]["accountKeys"]]
    keys += meta["loadedAddresses"]["writable"] + meta["loadedAddresses"]["readonly"]
    signer = keys[0]
    bal: dict = defaultdict(lambda: [0.0, 0.0])  # (propriétaire, mint) -> [avant, après]
    for side, j in (("preTokenBalances", 0), ("postTokenBalances", 1)):
        for b in meta.get(side) or []:
            if b.get("owner"):
                bal[(b["owner"], b["mint"])][j] += int(b["uiTokenAmount"]["amount"]) / 10 ** int(b["uiTokenAmount"]["decimals"])
    pre, post = meta["preBalances"], meta["postBalances"]

    def lam(k):
        i = keys.index(k) if k in keys else None
        return (pre[i] / 1e9, post[i] / 1e9) if i is not None and i < len(post) else (0.0, 0.0)

    ixs = ixs or []
    mints = {m for (_, m) in bal}
    mint = curve = None
    quote = "sol"
    for a in ixs:
        if len(a) < 12:
            continue
        if a[2] == WSOL or (a[1] in mints and a[2] in mints):  # V2 (cotée SOL) / V3 (cotée dans un autre token)
            m, q, idx = a[1], a[2], 10 if len(a) >= 27 else 5
        else:  # Buy / Sell / BuyExactSolIn classiques
            m, q, idx = a[2], WSOL, 3

        def moved(o):
            return (o, m) in bal and bal[(o, m)][1] != bal[(o, m)][0]

        def quote_delta(o):
            if q != WSOL:
                x = bal.get((o, q))
                return x[1] - x[0] if x else 0.0
            w = bal.get((o, WSOL))
            return w[1] - w[0] if w and w[0] != w[1] else lam(o)[1] - lam(o)[0]

        def coherent(o):  # la courbe reçoit la monnaie quand elle donne des tokens, et inversement
            dt = bal[(o, m)][1] - bal[(o, m)][0]
            return quote_delta(o) * dt < 0

        # la courbe : à sa place connue dans l'instruction, sinon le compte cohérent qui bouge le plus de tokens
        if idx < len(a) and moved(a[idx]) and coherent(a[idx]):
            curve = a[idx]
        else:
            owners = [(abs(bal[(o, m)][1] - bal[(o, m)][0]), o) for o in a if o != signer and moved(o) and coherent(o)]
            curve = max(owners)[1] if owners else None
        if curve:
            mint, quote = m, ("sol" if q == WSOL else q)
            break
    if mint is None and kind == "create":  # création sans achat du créateur : courbe encore vide
        accs = [x for a in ixs for x in a]
        mint = next((x for x in accs if x.endswith("pump")), accs[0] if accs else None)
    if mint is None:
        return None
    if curve is None:
        c_pre = c_post = 0.0
    elif quote == "sol":
        w = bal.get((curve, WSOL))
        c_pre, c_post = w if w and w[0] != w[1] else lam(curve)
    else:
        c_pre, c_post = bal.get((curve, quote), [0.0, 0.0])
    v = bal.get((curve, mint)) if curve else None
    c_tok = (v[1] - v[0]) if v else 0.0
    d_sol = c_post - c_pre
    s = bal.get((signer, mint))
    sx, sy = lam(signer)
    nsig = sum(1 for k in tx["transaction"]["message"]["accountKeys"] if k["signer"])
    return {"kind": kind, "signer": signer, "mint": mint, "curve_acc": curve, "quote": quote,
            "sol": round(d_sol, 9), "curve": c_post, "vault_tok": v[1] if v else None,
            "curve_tok": round(-c_tok, 6), "tok": round((s[1] - s[0]) if s else 0.0, 6),
            "px": abs(d_sol / c_tok) if c_tok and d_sol else None,
            "signer_sol": round(sy - sx, 9), "fee": meta["fee"] / 1e9,
            "prio": max(meta["fee"] - 5000 * nsig, 0) / 1e9,
            "jito": round(sum(lam(k)[1] - lam(k)[0] for k in JITO_TIPS if k in keys), 9)}


def pump_ix_accounts(info) -> list[list[str]]:
    """Comptes des instructions pump.fun d'une transaction gRPC (niveau 1 puis instructions internes)."""
    msg, meta = info.transaction.message, info.meta
    keys = [b58encode(k) for k in msg.account_keys]
    keys += [b58encode(a) for a in meta.loaded_writable_addresses] + [b58encode(a) for a in meta.loaded_readonly_addresses]
    if PUMP_PROGRAM not in keys:
        return []
    pi = keys.index(PUMP_PROGRAM)
    out = [[keys[i] for i in ix.accounts if i < len(keys)] for ix in msg.instructions if ix.program_id_index == pi]
    for g in meta.inner_instructions:
        out += [[keys[i] for i in ix.accounts if i < len(keys)] for ix in g.instructions if ix.program_id_index == pi]
    return out


class PumpRecorder:
    """Branché sur le flux gRPC du hub (filtre brut) : la conversion se fait dans un fil à part pour ne pas
    retarder les transactions des leaders."""

    def __init__(self, out: str, log=print):
        self.out, self.log = Path(out), log
        self.q: queue.Queue = queue.Queue(maxsize=50_000)
        self.created: dict[str, float] = {}
        self.common: Counter = Counter()
        self.n_in = self.n_rec = self.n_create = self.dropped = self.errors = 0

    def sink(self, t, bt: float, now: float, created: float | None) -> None:
        try:
            self.q.put_nowait((t, bt, now))
        except queue.Full:
            self.dropped += 1

    def start(self) -> "PumpRecorder":
        threading.Thread(target=self._run, daemon=True).start()
        return self

    def _run(self) -> None:
        self.out.parent.mkdir(parents=True, exist_ok=True)
        fh = self.out.open("a", encoding="utf-8")
        last = time.time()
        while True:
            try:
                t, bt, now = self.q.get(timeout=1)
            except queue.Empty:
                t = None
            if t is not None:
                try:
                    self._one(t, bt, now, fh)
                except Exception as exc:  # noqa: BLE001 - une transaction bizarre ne doit pas arrêter l'enregistrement
                    self.errors += 1
                    if self.errors <= 5:
                        self.log(f"  pump.fun : erreur de lecture {type(exc).__name__}: {str(exc)[:120]}")
            if time.time() - last > 60:
                last = time.time()
                fh.flush()
                for m in [m for m, c0 in self.created.items() if last - c0 > WINDOW_S + 60]:
                    del self.created[m]
                self.log(f"  pump.fun : {self.n_in} tx reçues, {self.n_create} créations, {self.n_rec} enregistrées, "
                         f"file {self.q.qsize()}, perdues {self.dropped}, erreurs {self.errors}")
                if self.out.stat().st_size > 2 * 1024 ** 3:  # garde-fou disque : 2 Go
                    self.log("  pump.fun : 2 Go atteints, enregistrement arrêté")
                    return

    def _one(self, t, bt, now, fh) -> None:
        self.n_in += 1
        info = t.transaction
        logs = list(info.meta.log_messages)
        # tri rapide avant la conversion (coûteuse) : création, ou token créé pendant l'enregistrement
        useful = (any(l in CREATE_LOGS for l in logs)
                  or any(b.mint in self.created for b in info.meta.post_token_balances))
        if not useful or info.meta.HasField("err"):
            return
        r = parse(to_tx_dict(info, t.slot, bt), logs, pump_ix_accounts(info))
        if not r:
            return
        if r["kind"] == "create":
            # tous les comptes de la création comme mints possibles : la place du mint varie selon la version
            accs = [x for a in pump_ix_accounts(info) for x in a]
            r["accs"] = accs[:24]
            for x in set(accs) | {r["mint"]}:
                self.common[x] += 1
                if self.common[x] <= 3 and x != WSOL:  # comptes communs (programmes, monnaie de cotation) exclus
                    self.created.setdefault(x, bt)
                else:
                    self.created.pop(x, None)
            self.n_create += 1
        c0 = self.created.get(r["mint"])
        if c0 is not None and bt - c0 <= WINDOW_S:
            cu = info.meta.compute_units_consumed if info.meta.HasField("compute_units_consumed") else None
            fh.write(json.dumps({"slot": t.slot, "idx": info.index, "bt": round(bt, 3), "seen": round(now, 3),
                                 "sig": b58encode(info.signature), **r, "cu": cu}) + "\n")
            self.n_rec += 1
