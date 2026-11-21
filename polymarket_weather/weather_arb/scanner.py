"""Scan : marchés Gamma -> station -> prévision au point station -> probabilités -> paper trades.

PAPER TRADING UNIQUEMENT : aucun ordre n'est envoyé, aucun appel CLOB authentifié.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from . import forecast as fcmod
from . import markets as mk
from .config import Settings
from .observations import observed_so_far, round_half_up
from .probability import (SigmaTable, bucket_prob_ensemble, bucket_prob_normal, clip,
                          condition_on_observed, dress_sigma, event_distribution, recenter_members)
from .stations import Station, StationRegistry
from .store import append_jsonl, read_json, read_jsonl, write_json


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def lead_days(target: date, st: Station, now: datetime) -> int:
    return (target - now.astimezone(ZoneInfo(st.tz)).date()).days


@dataclass
class EventForecast:
    det_c: float                  # prévision déterministe brute (°C)
    members_c: list[float] | None  # membres d'ensemble (°C) si mode ensemble
    obs_so_far: float | None = None  # extrême observé depuis minuit local (unité du marché), J0


def costs(price: float | None, s: Settings) -> float | None:
    """Coût effectif d'une part : prix + slippage, frais proportionnels au notionnel."""
    if price is None:
        return None
    return min(price + s.slippage, 0.999) * (1 + s.fee_rate)


def evaluate_event(ev: mk.EventSpec, st: Station, f: EventForecast, sigmas: SigmaTable,
                   s: Settings, now: datetime) -> list[dict]:
    """Calcule probabilités + edges pour toutes les tranches d'un événement (fonction pure)."""
    lead = lead_days(ev.target_date, st, now)
    err = sigmas.get(st.icao, lead)
    unit = ev.unit
    center_c = f.det_c + err.bias_c
    mean_u = fcmod.c_to_unit(center_c, unit)
    sigma_u = fcmod.delta_c_to_unit(err.sigma_c, unit)

    markets = [m for m in ev.markets if m.bucket is not None]
    buckets = [m.bucket for m in markets]
    complete = not mk.check_partition(buckets)

    if s.prob_model == "ensemble" and f.members_c:
        members_u = [fcmod.c_to_unit(x, unit) for x in recenter_members(f.members_c, center_c)]
        d_sigma = dress_sigma(sigma_u, members_u, fcmod.delta_c_to_unit(s.sigma_floor_c, unit))
        probs = event_distribution(buckets, lambda b: bucket_prob_ensemble(b, members_u, d_sigma), complete)
        model_name, eff_sigma = "ensemble", d_sigma
    else:
        probs = event_distribution(buckets, lambda b: bucket_prob_normal(b, mean_u, sigma_u), complete)
        model_name, eff_sigma = "normal", sigma_u

    obs_rep = None
    if lead == 0 and f.obs_so_far is not None:
        obs_rep = round_half_up(f.obs_so_far)
        probs = condition_on_observed(buckets, probs, obs_rep, ev.kind)

    rows = []
    ts = now.isoformat(timespec="seconds")
    for m, p_raw in zip(markets, probs):
        p = clip(p_raw, s.prob_clip)
        cost_yes = costs(m.best_ask, s)
        cost_no = costs(1 - m.best_bid, s) if m.best_bid is not None else None
        edge_yes = p - cost_yes if cost_yes is not None else None
        edge_no = (1 - p) - cost_no if cost_no is not None else None
        rows.append({
            "ts": ts, "event_slug": ev.slug, "event_title": ev.title, "market_id": m.market_id,
            "condition_id": m.condition_id, "market_slug": m.slug, "question": m.question,
            "city": ev.city, "kind": ev.kind, "target_date": ev.target_date.isoformat(),
            "unit": unit, "bucket_lo": m.bucket.lo, "bucket_hi": m.bucket.hi, "bucket": m.bucket.label(unit),
            "station_icao": st.icao, "station_name": st.name, "station_src": st.source,
            "station_lat": st.lat, "station_lon": st.lon, "station_tz": st.tz, "resolution_source": ev.resolution_source,
            "lead_days": lead, "model": model_name, "nwp_model": s.model,
            "forecast_raw": round(fcmod.c_to_unit(f.det_c, unit), 2), "forecast_mean": round(mean_u, 2),
            "bias_applied": round(fcmod.delta_c_to_unit(err.bias_c, unit), 2),
            "sigma": round(eff_sigma, 3), "sigma_source": err.source, "obs_so_far": obs_rep,
            "partition_complete": complete, "p_model": round(p, 4),
            "best_bid": m.best_bid, "best_ask": m.best_ask, "mid": m.mid, "spread": m.spread,
            "liquidity": m.liquidity, "accepting_orders": m.accepting_orders,
            "edge_yes": None if edge_yes is None else round(edge_yes, 4),
            "edge_no": None if edge_no is None else round(edge_no, 4),
            "warnings": ev.warnings,
        })
    return rows


def tradable(row: dict, s: Settings) -> tuple[str, float, float] | None:
    """-> (side, edge, prix d'entrée brut) si le marché passe tous les filtres, sinon None."""
    if not row["accepting_orders"] or row["spread"] is None or row["spread"] > s.max_spread:
        return None
    if row["liquidity"] < s.min_liquidity or not row["partition_complete"]:
        return None
    cands = []
    if row["edge_yes"] is not None and row["edge_yes"] >= s.min_edge:
        cands.append(("YES", row["edge_yes"], min(row["best_ask"] + s.slippage, 0.999)))
    if row["edge_no"] is not None and row["edge_no"] >= s.min_edge:
        cands.append(("NO", row["edge_no"], min(1 - row["best_bid"] + s.slippage, 0.999)))
    return max(cands, key=lambda c: c[1]) if cands else None


def make_trade(row: dict, side: str, edge: float, price: float, s: Settings) -> dict:
    p_side = row["p_model"] if side == "YES" else 1 - row["p_model"]
    fee = s.stake_usd * s.fee_rate
    return {
        **{k: row[k] for k in ("event_slug", "event_title", "market_id", "condition_id", "market_slug",
                               "question", "city", "kind", "target_date", "unit", "bucket_lo",
                               "bucket_hi", "bucket", "station_icao", "station_name", "station_src",
                               "station_lat", "station_lon", "station_tz",
                               "resolution_source", "lead_days", "model", "nwp_model", "forecast_raw",
                               "forecast_mean", "bias_applied", "sigma", "sigma_source", "p_model",
                               "best_bid", "best_ask", "mid", "spread")},
        "trade_id": uuid.uuid4().hex[:12], "created_at": row["ts"], "side": side,
        "entry_price": round(price, 4), "p_side": round(p_side, 4), "edge": edge,
        "stake_usd": s.stake_usd, "fee_usd": round(fee, 4), "shares": round(s.stake_usd / price, 4),
        "status": "OPEN",
    }


def select_trades(rows: list[dict], existing: list[dict], s: Settings) -> list[dict]:
    """Une seule entrée par marché (jamais de re-log à chaque scan) et au plus N par événement :
    les tranches d'un même événement sont mutuellement exclusives et donc corrélées."""
    taken_markets = {t["market_id"] for t in existing}
    per_event: dict[str, int] = {}
    for t in existing:
        per_event[t["event_slug"]] = per_event.get(t["event_slug"], 0) + 1
    cands = []
    for r in rows:
        if r["market_id"] in taken_markets:
            continue
        sig = tradable(r, s)
        if sig:
            cands.append((sig[1], r, sig))
    new = []
    for _, r, (side, edge, price) in sorted(cands, key=lambda c: -c[0]):
        if per_event.get(r["event_slug"], 0) >= s.max_trades_per_event:
            continue
        per_event[r["event_slug"]] = per_event.get(r["event_slug"], 0) + 1
        new.append(make_trade(r, side, edge, price, s))
    return new


def scan_once(s: Settings, log=print) -> dict:
    s.data_dir.mkdir(parents=True, exist_ok=True)
    now = now_utc()
    registry = StationRegistry(s.stations_override_path)
    sigmas = {k: SigmaTable(s.sigma_table_path(k), s.shrink_k, s.sigma_floor_c) for k in ("high", "low")}
    events = mk.fetch_temperature_events()
    skipped: dict[str, int] = {}
    fc_cache: dict[tuple, dict] = {}
    ens_cache: dict[tuple, dict] = {}
    rows: list[dict] = []

    def skip(reason: str):
        skipped[reason] = skipped.get(reason, 0) + 1

    for ev in events:
        if not ev.ok:
            skip("parsing incomplet (ville/date/unité/tranches)")
            continue
        st = registry.get(ev.station_icao, ev.station_name)
        if st is None or (s.require_station and st.source == "geocoded" and not ev.station_icao):
            skip("station de résolution non identifiée")
            continue
        lead = lead_days(ev.target_date, st, now)
        if lead < 0:
            skip("date passée")
            continue
        key = (st.icao, ev.kind)
        try:
            if key not in fc_cache:
                fc_cache[key] = fcmod.fetch_deterministic(st, s.model, ev.kind)
            if s.prob_model == "ensemble" and key not in ens_cache:
                ens_cache[key] = fcmod.fetch_ensemble(st, "ecmwf_ifs025", ev.kind)
        except RuntimeError as exc:
            log(f"  prévision indisponible {st.icao}: {exc}")
            skip("prévision indisponible")
            continue
        det = fc_cache[key].get(ev.target_date)
        if det is None:
            skip("hors horizon de prévision")
            continue
        obs = None
        if lead == 0:
            try:
                obs = observed_so_far(st, ev.target_date, ev.kind, ev.unit)
            except RuntimeError:
                obs = None
        members = ens_cache.get(key, {}).get(ev.target_date)
        rows.extend(evaluate_event(ev, st, EventForecast(det, members, obs), sigmas[ev.kind], s, now))

    # Journal de prédictions : 1 ligne par (marché, horizon) -> calibration sans biais de sélection.
    seen = {(p["market_id"], p["lead_days"]) for p in read_jsonl(s.predictions_path)}
    append_jsonl(s.predictions_path, [r for r in rows if (r["market_id"], r["lead_days"]) not in seen])

    trades = read_json(s.trades_path, [])
    new = select_trades(rows, trades, s)
    if new:
        write_json(s.trades_path, trades + new)
    opps = [r for r in rows if tradable(r, s)]
    return {"events": len(events), "markets_evaluated": len(rows), "opportunities": len(opps),
            "new_trades": new, "skipped": skipped}
