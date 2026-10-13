"""Recherche de leaders « copiables » : ce qu'un COPIEUR aurait gagné, pas ce que le leader a gagné.

1. candidats : classement KOL 7 jours (Solana Tracker)
2. stats du leader sur ses allers-retours : durée de détention, part < 30 s, PnL, nombre de tokens
3. on écarte les scalpeurs (détention médiane < seuil) : la copie y perd tout (voir test live 515vh1)
4. backtest copieur sur la 1re et la 2e moitié de la fenêtre séparément (choix sur l'une, contrôle
   sur l'autre) + taux de « crash » des tokens (-90 % dans les 15 min après l'achat du leader)
"""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import replace
from statistics import median

from . import net
from .config import WSOL, Settings
from .engine import CopyEngine
from .history import helius_key, wallet_swaps_helius
from .leaders import from_solanatracker
from .prices import BacktestPrices, GeckoCandles
from .report import short, stats
from .swaps import SwapEvent, convert_usd


def round_trips(events: list[SwapEvent]) -> list[dict]:
    """Allers-retours complets (≥ 98 % revendus) par (wallet, token)."""
    agg: dict[tuple, dict] = {}
    for e in events:
        k = (e.wallet, e.mint)
        a = agg.setdefault(k, {"mint": e.mint, "first_buy": None, "last_sell": None, "in": 0.0, "out": 0.0,
                               "bought": 0.0, "sold": 0.0, "first_buy_price": None})
        if e.side == "BUY":
            if a["first_buy"] is None:
                a["first_buy"], a["first_buy_price"] = e.block_time, e.price_sol
            a["in"] += e.sol_amount
            a["bought"] += e.token_amount
        elif a["bought"] > 0:
            a["out"] += e.sol_amount
            a["sold"] += e.token_amount
            a["last_sell"] = e.block_time
    out = []
    for a in agg.values():
        if a["bought"] > 0 and a["sold"] >= 0.98 * a["bought"] and a["last_sell"]:
            a["hold_s"] = a["last_sell"] - a["first_buy"]
            a["pnl"] = a["out"] - a["in"]
            out.append(a)
    return out


def leader_profile(events: list[SwapEvent]) -> dict:
    rts = round_trips(events)
    holds = [r["hold_s"] for r in rts]
    buys = [e.sol_amount for e in events if e.side == "BUY"]
    return {
        "n_swaps": len(events), "n_round_trips": len(rts), "n_tokens": len({e.mint for e in events}),
        "median_hold_s": median(holds) if holds else None,
        "share_under_30s": sum(h < 30 for h in holds) / len(holds) if holds else None,
        "leader_pnl": sum(r["pnl"] for r in rts),
        "leader_win_rate": sum(r["pnl"] > 0 for r in rts) / len(rts) if rts else None,
        "median_buy_sol": median(buys) if buys else None,
    }


def crash_rate(events: list[SwapEvent], candles: GeckoCandles, window_s: int = 900) -> float | None:
    """Part des premiers achats suivis d'une chute de 90 % sous le prix du leader dans les 15 min."""
    firsts: dict[str, SwapEvent] = {}
    for e in events:
        if e.side == "BUY" and e.mint not in firsts:
            firsts[e.mint] = e
    n = crashed = 0
    for e in firsts.values():
        lows = []
        for t in range(int(e.block_time), int(e.block_time) + window_s, 60):
            k = candles.at(e.mint, t, max_gap_s=120)
            if k:
                lows.append(k[0][2])
        if not lows or not e.price_sol:
            continue
        n += 1
        crashed += min(lows) <= 0.1 * e.price_sol
    return crashed / n if n else None


def copier_backtest(events: list[SwapEvent], wallet: str, candles: GeckoCandles, s: Settings) -> dict:
    out = {}
    for mode in ("neutral", "pessimistic"):
        eng = CopyEngine(s, BacktestPrices(candles, mode, s.slippage_bps), [wallet])
        for e in events:
            eng.on_event(e)
        eng.finalize(max(e.block_time for e in events) + 60 if events else time.time())
        out[mode] = stats(eng.st, s.bankroll_sol)
    return out


def scout(s: Settings, st_key: str, days: float = 7, top: int = 40, min_hold_s: float = 120,
          shortlist: int = 12, log=print) -> dict:
    # Bridage : ne pas gêner les tests live qui partagent les mêmes clés.
    net.MIN_INTERVAL.update({"api.helius.xyz": 1.0, "data.solanatracker.io": 1.0})
    hkey = helius_key(s.rpc_url)
    if not hkey:
        raise RuntimeError("scout utilise l'API Enhanced de Helius : SOLANA_RPC_URL doit être une URL Helius")
    now = int(time.time())
    since, mid = now - int(days * 86400), now - int(days * 86400 / 2)
    cands = from_solanatracker(st_key, "7d", limit=top)
    log(f"{len(cands)} candidats (classement 7 j)")
    candles = GeckoCandles(s.cache_dir, st_key)
    candles.load(WSOL, since - 3600, now + 60)

    profiles = []
    for i, c in enumerate(cands, 1):
        try:
            ev = wallet_swaps_helius(hkey, c.wallet, since, now, max_pages=60, cache_dir=s.cache_dir,
                                     log=lambda *_: None)
        except RuntimeError as exc:
            log(f"  {i}/{len(cands)} {c.label}: échec ({exc})")
            continue
        ev = convert_usd(ev, candles.sol_usd_at)
        p = {"wallet": c.wallet, "label": c.label, "rank_pnl_7d": c.pnl, **leader_profile(ev), "_events": ev}
        profiles.append(p)
        mh = p["median_hold_s"]
        log(f"  {i}/{len(cands)} {c.label[:18]:18s} {p['n_round_trips']:4d} A/R, détention médiane "
            f"{'-' if mh is None else f'{mh:.0f}s'}")

    eligible = [p for p in profiles if p["median_hold_s"] and p["median_hold_s"] >= min_hold_s
                and p["n_round_trips"] >= 8]
    eligible.sort(key=lambda p: -p["leader_pnl"])
    chosen = eligible[:shortlist]
    log(f"{len(eligible)} leaders non scalpeurs (détention médiane ≥ {min_hold_s:.0f} s) ; backtest copieur sur {len(chosen)}")

    cfg = replace(s, rotate_after_losses=0, size_mode="fraction", size=0.1)
    for j, p in enumerate(chosen, 1):
        ev = p["_events"]
        span: dict[str, list[int]] = defaultdict(list)
        for e in ev:
            span[e.mint].append(e.block_time)
        for mint, ts in span.items():
            try:
                candles.load(mint, min(ts) - 300, max(ts) + 1800)
            except RuntimeError:
                pass
        first = [e for e in ev if e.block_time < mid]
        second = [e for e in ev if e.block_time >= mid]
        p["copier_h1"] = copier_backtest(first, p["wallet"], candles, cfg) if first else None
        p["copier_h2"] = copier_backtest(second, p["wallet"], candles, cfg) if second else None
        p["crash_rate"] = crash_rate(ev, candles)
        r1 = (p["copier_h1"] or {}).get("neutral", {}).get("return")
        r2 = (p["copier_h2"] or {}).get("neutral", {}).get("return")
        log(f"  [{j}/{len(chosen)}] {p['label'][:18]:18s} copieur 1re moitié {r1 if r1 is None else f'{r1:+.1%}'}"
            f" | 2e moitié {r2 if r2 is None else f'{r2:+.1%}'} | crash {p['crash_rate']}")
    for p in profiles:
        p.pop("_events", None)
    return {"generated": now, "days": days, "min_hold_s": min_hold_s, "profiles": profiles,
            "chosen": [p["wallet"] for p in chosen]}


def verdict(p: dict) -> str:
    h1, h2 = p.get("copier_h1"), p.get("copier_h2")
    if not h1 or not h2:
        return "données insuffisantes"
    n1, n2 = h1["neutral"], h2["neutral"]
    pe2 = h2["pessimistic"]
    if n1["return"] > 0 and n2["return"] > 0 and pe2["return"] > -0.05 and (p.get("crash_rate") or 0) < 0.15:
        return "✅ candidat"
    if n1["return"] > 0 and n2["return"] <= 0:
        return "❌ ne tient pas hors échantillon"
    return "❌ copieur perdant"


def render_scout(res: dict) -> str:
    f = lambda x, fmt: "-" if x is None else format(x, fmt)
    md = [f"# Scout — leaders copiables ({res['days']:.0f} derniers jours)", "",
          f"Critères : détention médiane ≥ {res['min_hold_s']:.0f} s, ≥ 8 allers-retours ; copieur simulé à 10 % "
          "par trade, 1 % de commission, 2 s de retard ; choix sur la 1re moitié, contrôle sur la 2e.", "",
          "## Tous les candidats", "",
          "| leader | A/R | tokens | détention médiane | trades < 30 s | PnL leader (SOL) | win rate leader |",
          "|---|---|---|---|---|---|---|"]
    for p in sorted(res["profiles"], key=lambda p: -(p["median_hold_s"] or 0)):
        md.append(f"| {p['label'][:20]} `{short(p['wallet'])}` | {p['n_round_trips']} | {p['n_tokens']} | "
                  f"{f(p['median_hold_s'], '.0f')} s | {f(p['share_under_30s'], '.0%')} | {p['leader_pnl']:+.1f} | "
                  f"{f(p['leader_win_rate'], '.0%')} |")
    md += ["", "## Backtest copieur (non scalpeurs)", "",
           "| leader | copieur 1re moitié | copieur 2e moitié (neutre / pessimiste) | profit factor 2e moitié | "
           "crash des tokens | verdict |", "|---|---|---|---|---|---|"]
    for p in res["profiles"]:
        if p["wallet"] not in res["chosen"]:
            continue
        h1, h2 = p.get("copier_h1") or {}, p.get("copier_h2") or {}
        r = lambda h, m: f(h.get(m, {}).get("return"), "+.1%") if h else "-"
        pf = h2.get("neutral", {}).get("profit_factor") if h2 else None
        md.append(f"| {p['label'][:20]} `{short(p['wallet'])}` | {r(h1, 'neutral')} | {r(h2, 'neutral')} / "
                  f"{r(h2, 'pessimistic')} | {f(pf, '.2f')} | {f(p.get('crash_rate'), '.0%')} | {verdict(p)} |")
    md += ["", "Un ✅ ne garantit rien : il faut encore un test live (cotations réelles) avant tout argent réel.", ""]
    return "\n".join(md)
