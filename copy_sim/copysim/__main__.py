"""CLI : python -m copysim {backtest,live,report}

SIMULATION UNIQUEMENT : lecture seule de la blockchain, aucune clé privée, aucun ordre envoyé.
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from dataclasses import asdict, replace
from pathlib import Path

from .config import Settings
from .engine import CopyEngine, EngineState
from .history import leaders_swaps
from .net import SolanaRPC
from .prices import BacktestPrices, GeckoCandles, JupiterPrices
from .report import leader_baseline, render, stats
from .config import WSOL
from .swaps import SwapEvent, convert_usd, parse_swap


def build_leaders(s: Settings, out: str, source: str = "auto", top: int = 10, check: bool = True) -> None:
    from .leaders import filter_active, from_gecko, from_solanatracker, write_leaders
    key = os.getenv("SOLANATRACKER_API_KEY", "")
    if source == "auto":
        source = "solanatracker" if key else "gecko"
    print(f"Recherche des leaders via {source}…")
    if source == "solanatracker":
        if not key:
            sys.exit("SOLANATRACKER_API_KEY manquante dans .env")
        cands = from_solanatracker(key, "7d", limit=max(30, top * 3))
    else:
        cands = from_gecko()
    print(f"  {len(cands)} candidats")
    if check:
        cands = filter_active(SolanaRPC(s.rpc_url), cands[: top * 3])
    cands = cands[:top]
    if not cands:
        sys.exit("aucun leader retenu")
    write_leaders(out, cands)
    print(Path(out).read_text(encoding="utf-8"))


def read_leaders(path: str) -> list[str]:
    if not Path(path).exists():
        print(f"{path} absent : génération automatique du classement.")
        build_leaders(Settings(), path)
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
    end = None
    if args.end:
        end = int(datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()) + 86399
    print(f"Historique de {len(leaders)} leaders sur {args.days} j" + (f" jusqu'au {args.end}" if end else "") + "…")
    events = leaders_swaps(rpc, leaders, args.days, end_ts=end)
    if not events:
        sys.exit("aucun swap trouvé (RPC limité ? adresses correctes ?)")
    candles = GeckoCandles(s.cache_dir, os.getenv("SOLANATRACKER_API_KEY") or None)
    end_ts = max(e.block_time for e in events) + 60
    candles.load(WSOL, min(e.block_time for e in events) - 3600, end_ts + 3600)
    n_usd = sum(e.quote == "USD" for e in events)
    events = convert_usd(events, candles.sol_usd_at)
    print(f"{len(events)} swaps ({n_usd} cotés en USDC/USDT, convertis en SOL)")
    span: dict[str, list[int]] = defaultdict(list)
    for e in events:
        span[e.mint].append(e.block_time)
    print(f"Bougies 1 min pour {len(span)} tokens ({'Solana Tracker' if candles.st_key else 'GeckoTerminal, ≈30 req/min'}, mis en cache)…")
    for i, (mint, ts) in enumerate(span.items(), 1):
        try:  # seulement autour des trades du leader (+15 min)
            candles.load(mint, min(ts) - 300, max(ts) + 900)
        except RuntimeError as exc:
            print(f"  {mint[:6]}…: pas de bougies ({exc})")
        if i % 25 == 0:
            print(f"  {i}/{len(span)}")

    scenarios = {
        "neutral": (s, "neutral"),
        "pessimistic": (s, "pessimistic"),
        "neutral, sans rotation": (replace(s, rotate_after_losses=0), "neutral"),
    }

    def run_all():
        res, sts, still_open = {}, {}, set()
        for name, (cfg, mode) in scenarios.items():
            eng = CopyEngine(cfg, BacktestPrices(candles, mode, cfg.slippage_bps), leaders)
            for e in events:
                eng.on_event(e)
            still_open |= {p["mint"] for p in eng.st.positions.values()}
            eng.finalize(end_ts)
            res[name] = stats(eng.st, cfg.bankroll_sol)
            sts[name] = asdict(eng.st)
        return res, sts, still_open

    results, states, still_open = run_all()
    if still_open:  # positions jamais revendues : prix jusqu'à la fin de la fenêtre pour les valoriser
        print(f"Prolongation des bougies pour {len(still_open)} positions encore ouvertes…")
        for mint in still_open:
            try:
                candles.load(mint, max(span[mint]) + 900, end_ts + 600)
            except RuntimeError as exc:
                print(f"  {mint[:6]}…: {exc}")
        results, states, _ = run_all()
    md = render(results, leader_baseline(events),
                {"title": f"backtest {args.days} j, {len(leaders)} leaders, {len(events)} swaps",
                 "assumptions": assumptions(s)})
    out = Path("reports")
    out.mkdir(exist_ok=True)
    (out / f"{args.out}.md").write_text(md, encoding="utf-8")
    (out / f"{args.out}.json").write_text(json.dumps({"results": results, "states": states}, default=str, indent=1))
    print(md)
    print(f"-> {out / (args.out + '.md')}")


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
    prices = JupiterPrices(s.jup_quote_url, s.slippage_bps)
    check, max_impact = None, None
    if args.rug_filter:
        from .rugfilter import RugFilter
        rf = RugFilter(os.getenv("SOLANATRACKER_API_KEY") or None, s.data_dir / "rug_checks.jsonl")
        check, max_impact = rf.check, rf.max_impact
    eng = CopyEngine(s, prices, leaders, _load_state(state_path, s), live=True,
                     pre_buy_check=check, max_impact=max_impact)
    last_sig: dict[str, str | None] = {}
    for w in leaders:  # on part de maintenant : pas de rattrapage de l'historique
        page = rpc.signatures(w, limit=1)
        last_sig[w] = page[0]["signature"] if page else None
    started, last_report, last_poll = time.time(), 0.0, 0.0
    processed: set[str] = set()

    def handle(w: str, sig: str, tx: dict | None) -> None:
        processed.add(sig)
        ev = parse_swap(tx, w, sig)
        if not ev:
            return
        if ev.quote == "USD":
            px = prices.sol_usd()
            if not px:
                return
            ev.sol_amount = ev.quote_amount / px
        res = eng.on_event(ev, now_ts=time.time())
        if res:
            res["ts"] = time.time()
            if token_rec and res["type"] == "BUY":
                token_rec.submit(ev, res)
            with log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(res) + "\n")
            print(f"  {res['type']:4s} {w[:6]}… {ev.mint[:6]}… {res['sol']:+.4f} SOL "
                  f"retard {res['delay_s']}s  capital≈{eng.equity_at_cost():.3f}", flush=True)
            state_path.write_text(json.dumps(asdict(eng.st), default=str))

    token_rec = None
    if args.record_paths:  # données pour tester plus tard sorties et filtres anti-rug
        from .paths import PathRecorder
        from .tokeninfo import TokenInfoRecorder
        PathRecorder(eng.st, s.jup_quote_url, s.data_dir / "price_paths.jsonl").start()
        token_rec = TokenInfoRecorder(os.getenv("SOLANATRACKER_API_KEY") or None, s.data_dir / "token_info.jsonl")
        token_rec.start()

    stream = None
    if not args.poll:
        try:
            from .stream import SignatureStream
            stream = SignatureStream(s.rpc_url, leaders).start()
        except RuntimeError as exc:
            print(f"  temps réel indisponible ({exc}) : interrogation toutes les {s.poll_s}s")
    # filet de sécurité espacé : chaque contrôle coûte une requête par leader (crédits Helius limités)
    safety_s = float(os.getenv("CS_SAFETY_POLL_S", 120))
    mode = (f"websocket temps réel + contrôle toutes les {safety_s:.0f} s" if stream
            else f"interrogation toutes les {s.poll_s}s")
    print(f"Paper trading live sur {len(leaders)} leaders ({mode}). Ctrl+C pour arrêter. Leader actif : "
          f"{eng.active_leader or 'tous'}", flush=True)
    poll_every = safety_s if stream else s.poll_s
    while True:
        if stream:  # 1) signatures poussées en temps réel
            try:
                w, sig, _ = stream.q.get(timeout=0.5)
            except queue.Empty:
                w = None
            if w and sig not in processed:
                tx = None
                for _ in range(25):  # la tx peut ne pas être encore servie par getTransaction
                    try:
                        tx = rpc.call("getTransaction", [sig, {"encoding": "jsonParsed", "commitment": "confirmed",
                                                               "maxSupportedTransactionVersion": 1}])
                    except RuntimeError:
                        tx = None
                    if tx:
                        break
                    time.sleep(0.2)
                handle(w, sig, tx)
        if time.time() - last_poll >= poll_every:  # 2) filet de sécurité : rien n'est raté
            last_poll = time.time()
            for w in leaders:
                try:
                    new = rpc.signatures(w, until=last_sig[w], limit=50)
                except RuntimeError as exc:
                    print(f"  RPC {w[:6]}…: {exc}", file=sys.stderr)
                    continue
                if not new:
                    continue
                last_sig[w] = new[0]["signature"]
                ok = [x["signature"] for x in reversed(new) if x.get("err") is None and x["signature"] not in processed]
                for sig, tx in zip(ok, rpc.transactions(ok)):
                    handle(w, sig, tx)
            state_path.write_text(json.dumps(asdict(eng.st), default=str))
        if time.time() - last_report > 60:
            write_live_report(s, eng.st, log_path, started, args.report)
            last_report = time.time()
        if not stream:
            time.sleep(s.poll_s)


def cmd_leaders(s: Settings, args) -> None:
    build_leaders(s, args.out, args.source, args.top, not args.no_check)


def write_live_report(s: Settings, st: EngineState, log_path: Path, started: float | None = None,
                      name: str = "live") -> Path:
    """reports/live.md : synthèse + positions ouvertes + derniers trades (rafraîchi chaque minute)."""
    from .report import short
    md = render({"live (cotations Jupiter réelles)": stats(st, s.bankroll_sol)}, None,
                {"title": "paper trading live", "assumptions": assumptions(s)})
    head = [f"_Mis à jour : {time.strftime('%Y-%m-%d %H:%M:%S')} UTC"
            + (f" — en cours depuis {(time.time() - started) / 3600:.1f} h" if started else "") + "_", "",
            f"**Capital ≈ {st.cash + sum(p['cost_sol'] - p['proceeds_sol'] for p in st.positions.values()):.4f} SOL** "
            f"(départ {s.bankroll_sol} SOL, cash {st.cash:.4f}, positions au coût d'achat)", "",
            "## Positions ouvertes", ""]
    if st.positions:
        head += ["| token | depuis | engagé SOL | prix d'entrée vs leader |", "|---|---|---|---|"]
        for p in st.positions.values():
            slip = p["entry_price"] / p["leader_entry_price"] - 1 if p["leader_entry_price"] else 0
            head.append(f"| {short(p['mint'])} | {time.strftime('%H:%M:%S', time.gmtime(p['opened_ts']))} | "
                        f"{p['cost_sol']:.4f} | {slip:+.1%} |")
    else:
        head.append("Aucune.")
    rows = [json.loads(l) for l in log_path.read_text(encoding="utf-8").splitlines()[-15:]] if log_path.exists() else []
    head += ["", "## 15 derniers événements", ""]
    if rows:
        head += ["| heure UTC | type | token | SOL | prix vs leader | retard |", "|---|---|---|---|---|---|"]
        for r in reversed(rows):
            vs = r["price"] / r["leader_price"] - 1 if r.get("leader_price") else 0
            head.append(f"| {time.strftime('%H:%M:%S', time.gmtime(r['ts']))} | {r['type']} | {short(r['mint'])} | "
                        f"{r['sol']:+.4f} | {vs:+.1%} | {r['delay_s']} s |")
    else:
        head.append("Aucun pour l'instant.")
    out = Path("reports") / f"{name}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(head) + "\n\n" + md, encoding="utf-8")
    return out


def cmd_scout(s: Settings, args) -> None:
    from .scout import render_scout, scout, verdict
    key = os.getenv("SOLANATRACKER_API_KEY")
    if not key:
        sys.exit("SOLANATRACKER_API_KEY manquante dans .env")
    exclude: set[str] = set()
    for f in args.exclude or []:
        if Path(f).exists():
            exclude |= {p["wallet"] for p in json.loads(Path(f).read_text(encoding="utf-8"))["profiles"]}
    res = scout(s, key, args.days, args.top, args.min_hold, args.shortlist,
                sources=args.sources.split(","), exclude=exclude)
    Path("reports").mkdir(exist_ok=True)
    Path(f"reports/{args.name}.md").write_text(render_scout(res), encoding="utf-8")
    Path(f"reports/{args.name}.json").write_text(json.dumps(res, default=str, indent=1), encoding="utf-8")
    good = [p for p in res["profiles"] if p["wallet"] in res["chosen"] and verdict(p).startswith("✅")]
    Path(args.out).write_text("".join(f"{p['wallet']}  # {p['label']} (scout)\n" for p in good), encoding="utf-8")
    print(render_scout(res))
    print(f"-> reports/{args.name}.md ; {len(good)} candidat(s) dans {args.out}")


def cmd_snipe_record(s: Settings, args) -> None:
    from .sniper import SnipeRecorder
    print(f"Enregistrement des nouveaux tokens Pump.fun ({args.horizon:.0f} s chacun) dans {args.dir}/", flush=True)
    SnipeRecorder(Path(args.dir), s.rpc_url, args.horizon, log=lambda m: print(m, flush=True)).run_forever()


def cmd_snipe_report(s: Settings, args) -> None:
    from .sniper import load_snipes, snipe_report
    recs = load_snipes(Path(args.dir))
    if len(recs) < 50:
        sys.exit(f"seulement {len(recs)} tokens enregistrés : attendre d'en avoir au moins 50")
    md = snipe_report(recs, args.size, args.fee, args.tx_fee)
    Path("reports").mkdir(exist_ok=True)
    Path("reports/sniper.md").write_text(md, encoding="utf-8")
    print(md)


def cmd_scalp_report(s: Settings, args) -> None:
    from .sniper import load_snipes, scalp_report
    recs = [r for r in load_snipes(Path(args.dir)) if r["t0"] >= args.since]
    md = scalp_report(recs, args.size, args.fee, args.tx_fee, args.hold)
    Path("reports").mkdir(exist_ok=True)
    Path("reports/live_scalp_cloud.md").write_text(md, encoding="utf-8")
    print(md)


def cmd_copy_check(s: Settings, args) -> None:
    """Évalue les règles de copie pré-enregistrées sur chaque dossier de test présent."""
    from .rules import closed_trades, evaluate, load_paths, render
    pre = json.loads(Path(args.rule).read_text(encoding="utf-8"))
    results = {}
    for d in args.dirs:
        st = Path(d) / "live_state.json"
        if st.exists():
            trades = closed_trades(st, pre["fixee_ts"])
            results[d] = evaluate(trades, load_paths(Path(d) / "price_paths.jsonl"), pre, s.bot_fee_pct, s.tx_fee_sol)
    md = render(results, pre)
    Path("reports").mkdir(exist_ok=True)
    Path("reports/copy_rules.md").write_text(md, encoding="utf-8")
    print(md)


def cmd_snipe_check(s: Settings, args) -> None:
    """Évalue la règle pré-enregistrée uniquement sur les tokens postérieurs à son enregistrement."""
    from .sniper import Rule, evaluate, load_snipes
    pre = json.loads(Path(args.rule).read_text(encoding="utf-8"))
    r, c = pre["regle"], pre["hypotheses_de_cout"]
    rule = Rule(0.5, r["take_profit"], r["stop_loss"], r["duree_max_s"])
    recs = [x for x in load_snipes(Path(args.dir)) if x["t0"] > pre["fixee_ts"]]
    sel = [x for x in recs if (x.get("dev_buy_sol") or 0) > 1]
    ev = lambda xs: evaluate(xs, rule, c["taille_sol"], c["frais_pumpfun_par_cote"], c["priority_fee_sol_par_tx"])
    half = len(sel) // 2
    rows = [("règle (dev > 1 SOL)", ev(sel)), ("  1re moitié", ev(sel[:half])), ("  2e moitié", ev(sel[half:])),
            ("témoin : même règle, tous tokens", ev(recs))]
    k = pre["criteres_de_reussite"]
    a, h1, h2 = rows[0][1], rows[1][1], rows[2][1]
    ok = (a.get("n", 0) >= k["tokens_filtres_min"] and (a.get("mean") or -1) > k["rendement_moyen_net_min"]
          and (a.get("pf") or 0) >= k["profit_factor_min"] and (h1.get("mean") or -1) > 0 and (h2.get("mean") or -1) > 0)
    md = [f"# Règle pré-enregistrée : {pre['nom']}", "", f"Fixée le {pre['fixee_le_utc']} UTC. "
          f"Évaluée sur {len(recs)} tokens enregistrés depuis.", "",
          "| | tokens | moyenne nette | médiane | gagnants | profit factor |", "|---|---|---|---|---|---|"]
    for name, e in rows:
        if e.get("n"):
            pf = "-" if e["pf"] is None else f"{e['pf']:.2f}"
            md.append(f"| {name} | {e['n']} | {e['mean']:+.1%} | {e['median']:+.1%} | {e['win_rate']:.0%} | {pf} |")
        else:
            md.append(f"| {name} | 0 | - | - | - | - |")
    verdict = ("✅ critères atteints" if ok else
               f"⏳ pas encore assez de tokens filtrés ({a.get('n', 0)}/{k['tokens_filtres_min']})"
               if a.get("n", 0) < k["tokens_filtres_min"] else "❌ critères non atteints")
    md += ["", f"Critères : ≥ {k['tokens_filtres_min']} tokens filtrés, moyenne > 0, profit factor ≥ "
           f"{k['profit_factor_min']}, positif sur chaque moitié. **Verdict : {verdict}**", ""]
    Path("reports").mkdir(exist_ok=True)
    Path("reports/sniper_prereg.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


def cmd_report(s: Settings, args) -> None:
    state_path = s.data_dir / "live_state.json"
    if not state_path.exists():
        sys.exit("pas d'état live (lance d'abord `live`)")
    st = _load_state(state_path, s)
    print(write_live_report(s, st, s.data_dir / "live_events.jsonl", name=args.report).read_text(encoding="utf-8"))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="copysim", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("backtest", help="rejoue les N derniers jours des leaders")
    p.add_argument("--leaders", default="leaders.txt", help="1 adresse par ligne, dans l'ordre du classement")
    p.add_argument("--days", type=float, default=3)
    p.add_argument("--end", help="date de fin AAAA-MM-JJ (UTC) pour rejouer une période passée")
    p.add_argument("--out", default="backtest", help="nom du rapport dans reports/")
    p = sub.add_parser("live", help="paper trading en temps réel (cotations Jupiter)")
    p.add_argument("--leaders", default="leaders.txt")
    p.add_argument("--poll", action="store_true", help="sans websocket : interrogation toutes les CS_POLL_S s")
    p.add_argument("--report", default="live", help="nom du rapport dans reports/ (plusieurs tests en parallèle)")
    p.add_argument("--rug-filter", action="store_true",
                   help="filtre anti-rug avant chaque achat (seuils RF_* dans .env, journal data/rug_checks.jsonl)")
    p.add_argument("--record-paths", action="store_true",
                   help="enregistre le prix de sortie des positions ouvertes (~1,5 s) et la fiche de chaque token acheté "
                        "(data/price_paths.jsonl, data/token_info.jsonl)")
    p = sub.add_parser("report", help="rapport du paper trading live")
    p.add_argument("--report", default="live")
    p = sub.add_parser("snipe-record", help="enregistre les premières minutes des nouveaux tokens Pump.fun")
    p.add_argument("--dir", default="data_sniper")
    p.add_argument("--horizon", type=float, default=120)
    p = sub.add_parser("snipe-report", help="rejoue un sniper sur les tokens enregistrés")
    p.add_argument("--dir", default="data_sniper")
    p.add_argument("--size", type=float, default=0.5, help="taille d'achat en SOL")
    p.add_argument("--fee", type=float, default=0.0125, help="frais Pump.fun par côté")
    p.add_argument("--tx-fee", type=float, default=0.002, help="priority fee/Jito par transaction (SOL)")
    p = sub.add_parser("scalp-report", help="rejoue les règles de scalp A et B sur les lancements enregistrés")
    p.add_argument("--dir", default="data_scalp_pf")
    p.add_argument("--since", type=float, default=0.0, help="timestamp de début (lancements postérieurs seulement)")
    p.add_argument("--size", type=float, default=0.1)
    p.add_argument("--fee", type=float, default=0.0125)
    p.add_argument("--tx-fee", type=float, default=0.000105)
    p.add_argument("--hold", type=float, default=60.0)
    p = sub.add_parser("snipe-check", help="évalue la règle sniper pré-enregistrée sur les données postérieures")
    p.add_argument("--dir", default="data_sniper")
    p.add_argument("--rule", default="prereg/sniper_rule.json")
    p = sub.add_parser("copy-check", help="évalue les règles de copie pré-enregistrées (prereg/copy_rules.json)")
    p.add_argument("--rule", default="prereg/copy_rules.json")
    p.add_argument("--dirs", nargs="*", default=["data", "data_filtre", "data_raven", "data_cands", "data_scalp"])
    p = sub.add_parser("scout", help="cherche des leaders copiables (backtest copieur, validation hors échantillon)")
    p.add_argument("--days", type=float, default=7)
    p.add_argument("--top", type=int, default=40)
    p.add_argument("--min-hold", type=float, default=120, help="détention médiane minimale (s)")
    p.add_argument("--shortlist", type=int, default=12)
    p.add_argument("--out", default="leaders_scout.txt")
    p.add_argument("--sources", default="kol7d", help="kol7d,kol30d,kol1d,top (séparés par des virgules)")
    p.add_argument("--exclude", nargs="*", help="scout.json précédents : wallets déjà étudiés à sauter")
    p.add_argument("--name", default="scout", help="nom du rapport dans reports/")
    p = sub.add_parser("leaders", help="génère leaders.txt (classement 7 jours) automatiquement")
    p.add_argument("--source", choices=["auto", "solanatracker", "gecko"], default="auto")
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--out", default="leaders.txt")
    p.add_argument("--no-check", action="store_true", help="ne pas vérifier l'activité on-chain")
    args = ap.parse_args(argv)
    s = Settings()
    {"backtest": cmd_backtest, "live": cmd_live, "report": cmd_report, "leaders": cmd_leaders, "scout": cmd_scout, "copy-check": cmd_copy_check,
     "snipe-record": cmd_snipe_record, "snipe-report": cmd_snipe_report, "snipe-check": cmd_snipe_check,
     "scalp-report": cmd_scalp_report}[args.cmd](s, args)


if __name__ == "__main__":
    main()
