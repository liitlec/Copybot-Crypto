"""CLI : python -m copysim {backtest,live,report}

SIMULATION UNIQUEMENT : lecture seule de la blockchain, aucune clé privée, aucun ordre envoyé.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from dataclasses import asdict, replace
from pathlib import Path

from .config import Settings
from .engine import CopyEngine, EngineState
from .history import leaders_swaps
from .net import SolanaRPC
from .prices import BacktestPrices, GeckoCandles, JupiterPrices
from .report import leader_baseline, render, stats
from .swaps import SwapEvent, parse_swap


def read_leaders(path: str) -> list[str]:
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line:
            out.append(line.split()[0])
    if not out:
        sys.exit(f"aucune adresse dans {path}")
    return out


def assumptions(s: Settings) -> dict:
    return {"capital": f"{s.bankroll_sol} SOL", "taille": f"{s.size} ({s.size_mode})",
            "retard": f"{s.latency_s}s", "slippage": f"{s.slippage_bps:.0f}bps", "frais bot": f"{s.bot_fee_pct}%",
            "frais tx": f"{s.tx_fee_sol} SOL", "rotation": f"après {s.rotate_after_losses} pertes",
            "max positions": s.max_open}


def cmd_backtest(s: Settings, args) -> None:
    leaders = read_leaders(args.leaders)
    rpc = SolanaRPC(s.rpc_url, s.cache_dir)
    print(f"Historique de {len(leaders)} leaders sur {args.days} j…")
    events = leaders_swaps(rpc, leaders, args.days)
    if not events:
        sys.exit("aucun swap trouvé (RPC limité ? adresses correctes ?)")
    candles = GeckoCandles(s.cache_dir)
    span: dict[str, list[int]] = defaultdict(list)
    for e in events:
        span[e.mint].append(e.block_time)
    end_ts = max(e.block_time for e in events) + 60
    print(f"Bougies GeckoTerminal pour {len(span)} tokens (≈30 req/min, mis en cache)…")
    for i, (mint, ts) in enumerate(span.items(), 1):
        try:
            candles.load(mint, min(ts) - 300, end_ts + 600)
        except RuntimeError as exc:
            print(f"  {mint[:6]}…: pas de bougies ({exc})")
        if i % 25 == 0:
            print(f"  {i}/{len(span)}")
        time.sleep(args.gecko_sleep)

    scenarios = {
        "neutral": (s, "neutral"),
        "pessimistic": (s, "pessimistic"),
        "neutral, sans rotation": (replace(s, rotate_after_losses=0), "neutral"),
    }
    results, states = {}, {}
    for name, (cfg, mode) in scenarios.items():
        eng = CopyEngine(cfg, BacktestPrices(candles, mode, cfg.slippage_bps), leaders)
        for e in events:
            eng.on_event(e)
        eng.finalize(end_ts)
        results[name] = stats(eng.st, cfg.bankroll_sol)
        states[name] = asdict(eng.st)
    md = render(results, leader_baseline(events),
                {"title": f"backtest {args.days} j, {len(leaders)} leaders, {len(events)} swaps",
                 "assumptions": assumptions(s)})
    out = Path("reports")
    out.mkdir(exist_ok=True)
    (out / "backtest.md").write_text(md, encoding="utf-8")
    (out / "backtest.json").write_text(json.dumps({"results": results, "states": states}, default=str, indent=1))
    print(md)
    print(f"-> {out / 'backtest.md'}")


def _load_state(path: Path, s: Settings) -> EngineState:
    if path.exists():
        d = json.loads(path.read_text())
        d["equity_curve"] = [tuple(x) for x in d.get("equity_curve", [])]
        return EngineState(**d)
    return EngineState(cash=s.bankroll_sol)


def cmd_live(s: Settings, args) -> None:
    leaders = read_leaders(args.leaders)
    rpc = SolanaRPC(s.rpc_url)
    s.data_dir.mkdir(parents=True, exist_ok=True)
    state_path, log_path = s.data_dir / "live_state.json", s.data_dir / "live_events.jsonl"
    eng = CopyEngine(s, JupiterPrices(s.jup_quote_url, s.slippage_bps), leaders,
                     _load_state(state_path, s), live=True)
    last_sig: dict[str, str | None] = {}
    for w in leaders:  # on part de maintenant : pas de rattrapage de l'historique
        page = rpc.signatures(w, limit=1)
        last_sig[w] = page[0]["signature"] if page else None
    print(f"Paper trading live sur {len(leaders)} leaders (Ctrl+C pour arrêter). Leader actif : "
          f"{eng.active_leader or 'tous'}")
    while True:
        for w in leaders:
            try:
                new = rpc.signatures(w, until=last_sig[w], limit=50)
            except RuntimeError as exc:
                print(f"  RPC {w[:6]}…: {exc}", file=sys.stderr)
                continue
            if not new:
                continue
            last_sig[w] = new[0]["signature"]
            ok = [x["signature"] for x in reversed(new) if x.get("err") is None]
            for sig, tx in zip(ok, rpc.transactions(ok)):
                ev = parse_swap(tx, w, sig)
                if not ev:
                    continue
                res = eng.on_event(ev, now_ts=time.time())
                if res:
                    res["ts"] = time.time()
                    with log_path.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(res) + "\n")
                    print(f"  {res['type']:4s} {w[:6]}… {ev.mint[:6]}… {res['sol']:+.4f} SOL "
                          f"retard {res['delay_s']}s  capital≈{eng.equity_at_cost():.3f}")
        state_path.write_text(json.dumps(asdict(eng.st), default=str))
        time.sleep(s.poll_s)


def cmd_report(s: Settings, args) -> None:
    state_path = s.data_dir / "live_state.json"
    if not state_path.exists():
        sys.exit("pas d'état live (lance d'abord `live`)")
    st = _load_state(state_path, s)
    md = render({"live (cotations Jupiter réelles)": stats(st, s.bankroll_sol)}, None,
                {"title": "paper trading live", "assumptions": assumptions(s)})
    Path("reports").mkdir(exist_ok=True)
    Path("reports/live.md").write_text(md, encoding="utf-8")
    print(md)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="copysim", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("backtest", help="rejoue les N derniers jours des leaders")
    p.add_argument("--leaders", default="leaders.txt", help="1 adresse par ligne, dans l'ordre du classement")
    p.add_argument("--days", type=float, default=3)
    p.add_argument("--gecko-sleep", type=float, default=2.1, help="pause entre tokens (limite GeckoTerminal)")
    p = sub.add_parser("live", help="paper trading en temps réel (cotations Jupiter)")
    p.add_argument("--leaders", default="leaders.txt")
    sub.add_parser("report", help="rapport du paper trading live")
    args = ap.parse_args(argv)
    s = Settings()
    {"backtest": cmd_backtest, "live": cmd_live, "report": cmd_report}[args.cmd](s, args)


if __name__ == "__main__":
    main()
