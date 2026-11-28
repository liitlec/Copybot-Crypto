"""Résolution des paper trades (et du journal de prédictions) échus : WIN / LOSS.

Source 1 (prioritaire) : résultat officiel Polymarket (Gamma, outcomePrices 1/0 une fois clos).
Source 2 (contrôle / provisoire) : observation METAR de la station + règle de tranche.
Un désaccord entre les deux = bug d'interprétation (station, unité, bornes, fuseau) à investiguer.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from . import markets as mk
from .config import Settings
from .observations import observed_extreme
from .stations import Station
from .store import read_json, read_jsonl, write_json, write_jsonl


def compute_pnl(side: str, yes_won: bool, shares: float, stake: float, fee: float) -> tuple[str, float]:
    win = yes_won if side == "YES" else not yes_won
    return ("WIN" if win else "LOSS"), round((shares if win else 0.0) - stake - fee, 4)


def apply_resolution(rec: dict, official_yes: bool | None, obs: dict | None, official_only: bool,
                     now_iso: str) -> bool:
    """Met à jour `rec` en place. Renvoie True si quelque chose a changé."""
    bucket = mk.Bucket(rec["bucket_lo"], rec["bucket_hi"])
    obs_yes = bucket.contains(obs["reported"]) if obs else None
    if obs:
        rec["observed"] = round(obs["value"], 2)
        rec["observed_reported"] = obs["reported"]
        rec["obs_yes"] = obs_yes
        rec["forecast_error"] = round(obs["value"] - rec["forecast_mean"], 2)
    if official_yes is not None:
        yes, method = official_yes, "polymarket"
    elif obs_yes is not None and not official_only:
        yes, method = obs_yes, "observation"
    else:
        return bool(obs)
    rec["outcome_yes"] = yes
    rec["resolution_method"] = method
    rec["resolved_at"] = now_iso
    rec["obs_mismatch"] = (official_yes is not None and obs_yes is not None and official_yes != obs_yes)
    if "side" in rec:  # trade
        rec["result"], rec["pnl"] = compute_pnl(rec["side"], yes, rec["shares"], rec["stake_usd"],
                                                rec.get("fee_usd", 0.0))
        rec["status"] = "RESOLVED" if method == "polymarket" else "PROVISIONAL"
    return True


def _needs_resolution(rec: dict) -> bool:
    return rec.get("resolution_method") != "polymarket"


def _local_day_over(rec: dict, now: datetime) -> bool:
    tz = ZoneInfo(rec.get("station_tz") or "UTC")
    return now.astimezone(tz).date() > date.fromisoformat(rec["target_date"])


def _station(rec: dict) -> Station | None:
    if not rec.get("station_icao") or rec.get("station_lat") is None:
        return None
    return Station(rec["station_icao"], rec.get("station_name") or "", rec["station_lat"],
                   rec["station_lon"], rec.get("station_tz") or "UTC")


def resolve_records(records: list[dict], s: Settings, official_only: bool = False, log=print) -> int:
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat(timespec="seconds")
    pending = [r for r in records if _needs_resolution(r) and _local_day_over(r, now)]
    official: dict[str, bool | None] = {}
    for slug in sorted({r["event_slug"] for r in pending}):
        try:
            ev = mk.fetch_event_by_slug(slug)
        except RuntimeError as exc:
            log(f"  Gamma indisponible pour {slug}: {exc}")
            continue
        for m in (ev or {}).get("markets", []):
            official[str(m.get("id"))] = mk.parse_market(m).resolved_yes()
    obs_cache: dict[tuple, dict | None] = {}
    changed = 0
    for r in pending:
        off = official.get(r["market_id"])
        if off is None and r["market_id"] not in official:
            raw = mk.fetch_market(r["market_id"])
            off = mk.parse_market(raw).resolved_yes() if raw else None
        key = (r.get("station_icao"), r["target_date"], r["kind"], r["unit"])
        if key not in obs_cache:
            st = _station(r)
            try:
                obs_cache[key] = observed_extreme(st, date.fromisoformat(r["target_date"]), r["kind"],
                                                  r["unit"], s.cache_dir) if st else None
            except RuntimeError as exc:
                log(f"  METAR indisponible {key}: {exc}")
                obs_cache[key] = None
        changed += apply_resolution(r, off, obs_cache[key], official_only, now_iso)
    return changed


def resolve_all(s: Settings, official_only: bool = False, log=print) -> dict:
    trades = read_json(s.trades_path, [])
    n_t = resolve_records(trades, s, official_only, log)
    write_json(s.trades_path, trades)
    preds = read_jsonl(s.predictions_path)
    n_p = resolve_records(preds, s, official_only, log)
    write_jsonl(s.predictions_path, preds)
    mism = [t for t in trades if t.get("obs_mismatch")]
    return {"trades_updated": n_t, "predictions_updated": n_p, "mismatches": len(mism)}
