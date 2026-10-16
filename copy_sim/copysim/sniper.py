"""Paper test « sniper » Pump.fun : acheter un token dans les premières secondes de sa création.

Enregistrement (snipe-record) : flux public PumpPortal (nouveaux tokens) + abonnement RPC au compte de
la courbe de chaque token. On garde la fiche de création et l'état de la courbe (réserves virtuelles
SOL/token) à chaque trade pendant HORIZON secondes. Fichiers data_sniper/snipes-AAAA-MM-JJ.jsonl.gz (1 ligne par token).

Analyse (snipe-report) : la courbe Pump.fun est un produit constant sur réserves virtuelles, donc le
prix d'un achat/vente de n'importe quelle taille à n'importe quel instant se recalcule exactement.
On rejoue un sniper entrant L secondes après la création, avec des règles de sortie, les frais de
Pump.fun et une priority fee par transaction. Règles choisies sur la 1re moitié, vérifiées sur la 2e.
Aucune transaction n'est envoyée.
"""
from __future__ import annotations

import base64
import gzip
import json
import struct
import os
import threading
import time
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from statistics import mean, median
from urllib.parse import urlparse

PUMPPORTAL_WS = "wss://pumpportal.fun/api/data"


# ---------------------------------------------------------------- courbe Pump.fun

def buy_tokens(sol_in: float, v_sol: float, v_tok: float, fee: float) -> float:
    net = sol_in * (1 - fee)
    return v_tok - v_sol * v_tok / (v_sol + net)


def sell_sol(tokens: float, v_sol: float, v_tok: float, fee: float) -> float:
    gross = v_sol - v_sol * v_tok / (v_tok + tokens)
    return gross * (1 - fee)


# ---------------------------------------------------------------- enregistrement

class SnipeRecorder:
    """Deux websockets : PumpPortal (créations de tokens, gratuit) et le RPC Helius (accountSubscribe sur
    la courbe de chaque token suivi : l'état est poussé à chaque trade). Côté et montant d'un trade sont
    déduits de la variation des réserves SOL."""

    def __init__(self, out_dir: Path, rpc_url: str, horizon_s: float = 120, max_tracked: int = 120, log=print):
        self.out_dir, self.horizon, self.max_tracked, self.log = Path(out_dir), horizon_s, max_tracked, log
        self.ws_url = rpc_url.replace("https://", "wss://", 1)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.tracked: dict[str, dict] = {}     # mint -> enregistrement
        self.sub_of: dict[int, str] = {}       # subscription id -> mint
        self.req_of: dict[int, str] = {}       # id de requête -> mint
        self.lock = threading.Lock()
        self.n_done = 0
        self._req = 0
        self.rpc_ws = None

    def _write(self, rec: dict) -> None:
        rec.pop("_bc", None)
        rec.pop("_sub", None)
        path = self.out_dir / f"snipes-{time.strftime('%Y-%m-%d', time.gmtime(rec['t0']))}.jsonl.gz"
        with gzip.open(path, "at", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, separators=(",", ":")) + "\n")

    def _subscribe(self, mint: str, bc: str) -> None:
        if not self.rpc_ws:
            return
        with self.lock:
            self._req += 1
            rid = self._req
            self.req_of[rid] = mint
        try:
            self.rpc_ws.send(json.dumps({"jsonrpc": "2.0", "id": rid, "method": "accountSubscribe",
                                         "params": [bc, {"encoding": "base64", "commitment": "processed"}]}))
        except Exception:  # noqa: BLE001
            pass

    # --- flux PumpPortal : créations
    def on_create(self, ws, msg: str) -> None:
        try:
            m = json.loads(msg)
        except ValueError:
            return
        if m.get("txType") != "create" or not m.get("bondingCurveKey") or m.get("pool") not in (None, "pump"):
            return
        if len(self.tracked) >= self.max_tracked:
            return
        mint = m["mint"]
        rec = {"mint": mint, "t0": round(time.time(), 3), "name": (m.get("name") or "")[:40],
               "symbol": (m.get("symbol") or "")[:15], "creator": m.get("traderPublicKey"),
               "dev_buy_sol": m.get("solAmount"), "dev_buy_tokens": m.get("initialBuy"),
               "mcap_sol": m.get("marketCapSol"), "has_uri": bool(m.get("uri")), "_bc": m["bondingCurveKey"],
               # états : [dt, v_sol, v_tok, côté b/s/c, |Δ SOL|, courbe terminée]
               "states": [[0.0, m.get("vSolInBondingCurve"), m.get("vTokensInBondingCurve"), "c",
                           m.get("solAmount") or 0, 0]]}
        with self.lock:
            self.tracked[mint] = rec
        self._subscribe(mint, m["bondingCurveKey"])

    # --- flux RPC : états de courbe
    def on_rpc(self, ws, msg: str) -> None:
        try:
            m = json.loads(msg)
        except ValueError:
            return
        if "id" in m and "result" in m:  # accusé d'abonnement
            with self.lock:
                mint = self.req_of.pop(m["id"], None)
                if mint and mint in self.tracked:
                    self.sub_of[m["result"]] = mint
                    self.tracked[mint]["_sub"] = m["result"]
            return
        params = m.get("params") or {}
        with self.lock:
            mint = self.sub_of.get(params.get("subscription"))
            rec = self.tracked.get(mint) if mint else None
        if rec is None:
            return
        try:
            data = base64.b64decode(params["result"]["value"]["data"][0])
            v_tok, v_sol = struct.unpack_from("<2Q", data, 8)
            complete = data[48]
        except (KeyError, IndexError, ValueError, struct.error):
            return
        v_sol, v_tok = v_sol / 1e9, v_tok / 1e6
        prev = rec["states"][-1][1] or v_sol
        rec["states"].append([round(time.time() - rec["t0"], 2), round(v_sol, 6), round(v_tok, 3),
                              "b" if v_sol >= prev else "s", round(abs(v_sol - prev), 4), int(complete)])

    def flush_expired(self) -> None:
        now = time.time()
        with self.lock:
            done = [k for k, r in self.tracked.items() if now - r["t0"] >= self.horizon]
            recs = [self.tracked.pop(k) for k in done]
            subs = [r.get("_sub") for r in recs if r.get("_sub") is not None]
            for sid in subs:
                self.sub_of.pop(sid, None)
        for sid in subs:
            try:
                self.rpc_ws.send(json.dumps({"jsonrpc": "2.0", "id": 0, "method": "accountUnsubscribe",
                                             "params": [sid]}))
            except Exception:  # noqa: BLE001
                pass
        for r in recs:
            self._write(r)
            self.n_done += 1
        if recs and self.n_done % 100 < len(recs):
            self.log(f"{time.strftime('%H:%M:%S')} {self.n_done} tokens enregistrés")

    def _run_ws(self, url: str, on_message, on_open, set_ref=None) -> None:
        import websocket
        p = urlparse(os.getenv("HTTPS_PROXY") or os.getenv("https_proxy") or "")
        proxy = {"http_proxy_host": p.hostname, "http_proxy_port": p.port, "proxy_type": "http"} if p.hostname else {}
        ca = os.getenv("SSL_CERT_FILE") or os.getenv("REQUESTS_CA_BUNDLE")
        while True:
            app = websocket.WebSocketApp(url, on_message=on_message, on_open=on_open)
            if set_ref:
                set_ref(app)
            try:
                app.run_forever(ping_interval=30, ping_timeout=10, sslopt={"ca_certs": ca} if ca else None, **proxy)
            except Exception as exc:  # noqa: BLE001
                self.log(f"websocket {url[:30]} : {exc}")
            time.sleep(5)

    def run_forever(self) -> None:
        def rpc_open(ws):  # (ré)abonnement des tokens encore suivis
            with self.lock:
                self.sub_of.clear()
                todo = [(k, r["_bc"]) for k, r in self.tracked.items()]
            for mint, bc in todo:
                self._subscribe(mint, bc)

        threading.Thread(target=self._run_ws, daemon=True,
                         args=(self.ws_url, self.on_rpc, rpc_open, lambda a: setattr(self, "rpc_ws", a))).start()
        threading.Thread(target=self._run_ws, daemon=True,
                         args=(PUMPPORTAL_WS, self.on_create,
                               lambda ws: ws.send(json.dumps({"method": "subscribeNewToken"})))).start()
        while True:
            time.sleep(2)
            self.flush_expired()


# ---------------------------------------------------------------- simulation

@dataclass(frozen=True)
class Rule:
    latency_s: float
    tp: float | None      # take profit (+0.3 = +30 %)
    sl: float | None      # stop loss (-0.3 = -30 %)
    max_hold_s: float

    def label(self) -> str:
        f = lambda x: "-" if x is None else f"{x:+.0%}"
        return f"entrée {self.latency_s:g}s, TP {f(self.tp)}, SL {f(self.sl)}, max {self.max_hold_s:g}s"


def simulate(rec: dict, rule: Rule, size_sol: float, fee: float, tx_fee_sol: float) -> float | None:
    """Rendement net d'un snipe (None si aucun état exploitable). Frais : % Pump.fun à l'achat et à la
    vente + priority fee fixe par transaction."""
    st = [s for s in rec["states"] if s[1] and s[2]]
    if not st:
        return None
    i = 0  # état courant = dernier trade avant l'instant considéré
    while i + 1 < len(st) and st[i + 1][0] <= rule.latency_s:
        i += 1
    t_in = max(rule.latency_s, st[i][0])
    tokens = buy_tokens(size_sol, st[i][1], st[i][2], fee)
    cost = size_sol + tx_fee_sol
    exit_sol = None
    for s in st[i + 1:]:
        if s[0] - t_in > rule.max_hold_s:
            break
        val = sell_sol(tokens, s[1], s[2], fee) - tx_fee_sol
        ret = val / cost - 1
        if (rule.tp is not None and ret >= rule.tp) or (rule.sl is not None and ret <= rule.sl):
            exit_sol = val
            break
    if exit_sol is None:  # sortie à la durée max, sur le dernier état connu avant
        last = st[i]
        for s in st[i + 1:]:
            if s[0] - t_in > rule.max_hold_s:
                break
            last = s
        exit_sol = sell_sol(tokens, last[1], last[2], fee) - tx_fee_sol
    return exit_sol / cost - 1


MAX_VIRTUAL_SOL = 1000.0  # une courbe Pump.fun migre vers ~115 SOL virtuels : au-delà, mauvais décodage


def valid_curve(rec: dict) -> bool:
    """Écarte les comptes dont le format ne correspond pas à la courbe standard (états absurdes)."""
    return all(s[1] <= MAX_VIRTUAL_SOL for s in rec.get("states", []) if s[1])


def load_snipes(data_dir: Path) -> list[dict]:
    recs = []
    for p in sorted(Path(data_dir).glob("snipes-*.jsonl.gz")):
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            recs += [json.loads(l) for l in fh if l.strip()]
    recs = [r for r in recs if valid_curve(r)]
    recs.sort(key=lambda r: r["t0"])
    return recs


GRID = dict(latency_s=(0.5, 1, 2, 5), tp=(None, 0.2, 0.5, 1.0), sl=(None, -0.2, -0.4),
            max_hold_s=(10, 30, 60, 120))


def evaluate(recs: list[dict], rule: Rule, size: float, fee: float, tx: float) -> dict:
    rs = [r for r in (simulate(x, rule, size, fee, tx) for x in recs) if r is not None]
    if not rs:
        return {"n": 0}
    wins = [r for r in rs if r > 0]
    loss = [r for r in rs if r <= 0]
    pf = sum(wins) / -sum(loss) if loss and sum(loss) else None
    return {"n": len(rs), "mean": mean(rs), "median": median(rs), "win_rate": len(wins) / len(rs), "pf": pf}


def snipe_report(recs: list[dict], size: float, fee: float, tx: float) -> str:
    half = len(recs) // 2
    a, b = recs[:half], recs[half:]
    rules = [Rule(*v) for v in product(*GRID.values())]
    scored = sorted(((evaluate(a, r, size, fee, tx), r) for r in rules), key=lambda x: -(x[0].get("mean") or -9))
    lines = [f"# Paper test sniper Pump.fun — {len(recs)} tokens", "",
             f"Taille {size} SOL, frais Pump.fun {fee:.2%} par côté, priority fee {tx} SOL par transaction. "
             f"Règles classées sur la 1re moitié ({len(a)} tokens), vérifiées sur la 2e ({len(b)} tokens).", "",
             "| règle | 1re moitié : moyenne / médiane / gagnants | 2e moitié (contrôle) : moyenne / médiane / gagnants / PF |",
             "|---|---|---|"]
    for ev_a, r in scored[:12]:
        ev_b = evaluate(b, r, size, fee, tx)
        g = lambda e: (f"{e['mean']:+.1%} / {e['median']:+.1%} / {e['win_rate']:.0%}" if e.get("n") else "-")
        pf = ev_b.get("pf")
        lines.append(f"| {r.label()} | {g(ev_a)} | {g(ev_b)} / {'-' if pf is None else f'{pf:.2f}'} |")
    # Sensibilité à la vitesse et à quelques filtres simples, avec la meilleure règle de la 1re moitié.
    best = scored[0][1]
    lines += ["", f"## Meilleure règle ({best.label()}) selon la vitesse d'entrée (2e moitié)", "",
              "| entrée après | moyenne | gagnants |", "|---|---|---|"]
    for lat in GRID["latency_s"]:
        e = evaluate(b, Rule(lat, best.tp, best.sl, best.max_hold_s), size, fee, tx)
        if e.get("n"):
            lines.append(f"| {lat:g} s | {e['mean']:+.1%} | {e['win_rate']:.0%} |")
    filt = {"dev achète 0 SOL": lambda r: not r.get("dev_buy_sol"),
            "dev achète > 1 SOL": lambda r: (r.get("dev_buy_sol") or 0) > 1,
            "≥ 5 achats dans les 5 premières s": lambda r: sum(1 for s in r["states"] if s[3] == "b" and s[0] <= 5) >= 5,
            "vente ≥ 1 SOL dans les 30 s": lambda r: any(s[3] == "s" and s[4] >= 1 for s in r["states"] if s[0] <= 30)}
    lines += ["", "## Filtres simples (meilleure règle, 2e moitié)", "", "| filtre | tokens | moyenne | gagnants |",
              "|---|---|---|---|"]
    for name, fn in filt.items():
        sub = [r for r in b if fn(r)]
        e = evaluate(sub, best, size, fee, tx)
        if e.get("n"):
            lines.append(f"| {name} | {e['n']} | {e['mean']:+.1%} | {e['win_rate']:.0%} |")
    lines += ["", "Lecture : si même la meilleure règle est négative sur la 2e moitié, le sniping amateur ne paie pas. "
              "« vente ≥ 1 SOL dans les 30 s » utilise une info future : c'est un diagnostic, pas un filtre utilisable.", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------- scalp A / B (règles figées sur le PC le 15/10)

BUNDLE_S = 0.4  # trades vus dans les 0,4 s de la création ~ même bloc que la création (bundle du créateur)


def scalp_entry_ok(rec: dict, entry_s: float, need_other_buyer: bool) -> bool:
    """B : au moins un achat d'un autre que le créateur avant l'entrée, et pas d'achat groupé dans le bloc de
    création. On ne connaît pas le signataire de chaque trade ici : tout achat après la création compte comme
    « autre acheteur », et le bloc de création est approché par les 0,4 premières secondes."""
    if not need_other_buyer:
        return True
    st = rec.get("states", [])
    if any(s[3] == "b" and s[0] <= BUNDLE_S for s in st):
        return False
    return any(s[3] == "b" and BUNDLE_S < s[0] <= entry_s for s in st)


# règles figées sur le PC (prereg/scalp_rule.json du 15/10, 20:17) : entrée (s), confirmation, plafond de SOL dans la courbe
SCALP_RULES = {"B confirmé : +5 s, au moins 1 autre acheteur": (5.0, True, 2.5),
               "A brut : +1 s, sans confirmation": (1.0, False, 0.5)}
V_SOL0 = 30.0  # SOL virtuels d'une courbe neuve
# t0 = réception du message PumpPortal, ~0,5 s après le bloc de création (mesuré le 16/10 : 0,1 à 0,9 s) ;
# les délais des règles (comptés depuis le bloc sur le PC) sont donc décalés d'autant ici
CLOCK_OFFSET_S = 0.5


def sol_in_curve_at(rec: dict, t: float) -> float | None:
    """SOL réels dans la courbe à l'instant t (dernier état connu, achat du créateur compris)."""
    st = [s for s in rec.get("states", []) if s[1] and s[2]]
    if not st:
        return None
    cur = st[0]
    for s in st[1:]:
        if s[0] > t:
            break
        cur = s
    return cur[1] - V_SOL0


def scalp_report(recs: list[dict], size: float = 0.1, fee: float = 0.0125, tx: float = 0.000105,
                 hold_s: float = 60.0) -> str:
    md = ["# Scalp Pump.fun A / B (cloud)", "",
          f"{len(recs)} lancements enregistrés. Achat {size} SOL, revente {hold_s:.0f} s après l'entrée, frais Pump.fun "
          f"{fee:.2%} par côté + {tx} SOL par transaction (mêmes valeurs que le PC). Plafond de SOL dans la courbe à "
          "l'entrée : B 2,5 SOL, A 0,5 SOL. Prix exacts de la courbe (états enregistrés).", "",
          "| règle | trades | total | par trade | sans les 3 meilleurs | gagnants | > +100 % |", "|---|---|---|---|---|---|---|"]
    for name, (entry_bloc, confirm, max_sol) in SCALP_RULES.items():
        entry = max(entry_bloc - CLOCK_OFFSET_S, 0.0)
        rule = Rule(entry, None, None, hold_s)
        ok = [x for x in recs if scalp_entry_ok(x, entry, confirm)
              and (sol_in_curve_at(x, entry) is not None and sol_in_curve_at(x, entry) < max_sol)]
        rs = [r for r in (simulate(x, rule, size, fee, tx) for x in ok) if r is not None]
        if not rs:
            md.append(f"| {name} | 0 | - | - | - | - | - |")
            continue
        srt = sorted(rs, reverse=True)
        se = (sum((r - mean(rs)) ** 2 for r in rs) / len(rs)) ** .5 / len(rs) ** .5
        rest = mean(srt[3:]) if len(srt) > 3 else float("nan")
        md.append(f"| {name} | {len(rs)} | {sum(rs) * size:+.2f} SOL | {mean(rs):+.2%} ± {se:.2%} | {rest:+.2%} | "
                  f"{sum(r > 0 for r in rs) / len(rs):.0%} | {sum(r > 1 for r in rs)} |")
    md += ["", "Signataires non connus ici (pas de gRPC) : « autre acheteur » = tout achat après la création ; bloc de "
           "création approché par les 0,4 premières secondes ; délais corrigés de 0,5 s (retard mesuré de PumpPortal "
           "sur le bloc). Résultats comparables mais pas identiques à ceux du PC.", ""]
    return "\n".join(md)
