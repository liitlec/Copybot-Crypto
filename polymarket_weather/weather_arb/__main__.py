"""CLI : python -m weather_arb {scan,loop,resolve,calibrate,report,explain}

PAPER TRADING UNIQUEMENT. Aucun ordre réel n'est jamais envoyé.
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone

from . import forecast as fcmod
from . import markets as mk
from .calibration import calibrate, format_table
from .config import OPEN_METEO_GEOCODING, Settings
from .probability import SigmaTable, bucket_prob_normal
from .resolution import resolve_all
from .scanner import EventForecast, evaluate_event, lead_days, now_utc, scan_once
from .stations import BUILTIN, Station, StationRegistry
from .store import write_json


def cmd_scan(s: Settings, args) -> None:
    res = scan_once(s)
    print(f"{datetime.now():%Y-%m-%d %H:%M} | événements {res['events']} | marchés évalués "
          f"{res['markets_evaluated']} | opportunités (après coûts/filtres) {res['opportunities']} | "
          f"nouveaux trades {len(res['new_trades'])}")
    for reason, n in sorted(res["skipped"].items(), key=lambda kv: -kv[1]):
        print(f"   ignorés : {n:4d}  {reason}")
    for t in res["new_trades"]:
        print(f"   + {t['side']:3s} {t['city']} {t['target_date']} {t['bucket']:>8s} @ {t['entry_price']:.3f} "
              f"p={t['p_side']:.2f} edge={t['edge']:+.2f} J+{t['lead_days']} [{t['station_icao']}]")


def cmd_loop(s: Settings, args) -> None:
    while True:
        try:
            cmd_scan(s, args)
            if args.with_resolve:
                print("   résolution :", resolve_all(s, log=lambda *_: None))
        except Exception as exc:  # le loop ne doit pas mourir sur une erreur réseau
            print(f"   ERREUR scan : {exc}", file=sys.stderr)
        time.sleep(s.scan_interval_min * 60)


def cmd_resolve(s: Settings, args) -> None:
    print(resolve_all(s, official_only=args.official_only))


def cmd_report(s: Settings, args) -> None:
    from .report import write_report
    print(f"Rapport écrit : {write_report(s)}")


def cmd_calibrate(s: Settings, args) -> None:
    reg = StationRegistry(s.stations_override_path, allow_geocoding=False)
    if args.stations:
        icaos = [x.strip().upper() for x in args.stations.split(",")]
    elif args.from_markets:
        icaos = sorted({e.station_icao for e in mk.fetch_temperature_events() if e.station_icao})
    else:
        icaos = sorted(BUILTIN)
    stations = [st for st in (reg.get(i) for i in icaos) if st]
    print(f"Calibration {args.kind} sur {len(stations)} stations, {args.days} jours, modèle {s.model}")
    table = calibrate(stations, s.model, args.days, args.kind, cache_dir=s.cache_dir)
    write_json(s.sigma_table_path(args.kind), table)
    print(format_table(table))
    print(f"-> {s.sigma_table_path(args.kind)}")


def cmd_explain(s: Settings, args) -> None:
    """Déroule toute la chaîne pour un événement : utile pour comprendre un écart de 50 points."""
    from . import http
    raw = mk.fetch_event_by_slug(args.slug)
    if not raw:
        sys.exit(f"événement introuvable : {args.slug}")
    ev = mk.parse_event(raw)
    print(f"{ev.title}\n  ville={ev.city} type={ev.kind} date={ev.target_date} unité={ev.unit}")
    print(f"  station={ev.station_icao} ({ev.station_name}) source={ev.resolution_source}\n  url={ev.resolution_url}")
    for w in ev.warnings:
        print(f"  ! {w}")
    st = StationRegistry(s.stations_override_path).get(ev.station_icao, ev.station_name)
    if not st or not ev.ok:
        sys.exit("  -> station ou parsing incomplet, arrêt")
    now = now_utc()
    lead = lead_days(ev.target_date, st, now)
    det = fcmod.fetch_deterministic(st, s.model, ev.kind).get(ev.target_date)
    print(f"  coords station {st.lat},{st.lon} tz={st.tz} ({st.source}) horizon J+{lead}")
    print(f"  prévision {s.model} au point station : {fcmod.c_to_unit(det, ev.unit):.1f}°{ev.unit}")
    geo = http.get(OPEN_METEO_GEOCODING, {"name": ev.city, "count": 1}).get("results") or []
    if geo:
        city_st = Station("CITY", ev.city, geo[0]["latitude"], geo[0]["longitude"], st.tz)
        det_city = fcmod.fetch_deterministic(city_st, s.model, ev.kind).get(ev.target_date)
        if det_city is not None:
            print(f"  prévision au centre-ville ({city_st.lat:.2f},{city_st.lon:.2f}) : "
                  f"{fcmod.c_to_unit(det_city, ev.unit):.1f}°{ev.unit}  "
                  f"(écart station-ville {fcmod.delta_c_to_unit(det - det_city, ev.unit):+.1f})")
    sig = SigmaTable(s.sigma_table_path(ev.kind), s.shrink_k, s.sigma_floor_c)
    rows = evaluate_event(ev, st, EventForecast(det, None), sig, s, now)
    old_sigma = fcmod.delta_c_to_unit(0.7 if lead == 0 else 1.5 if lead == 1 else 1.5 + 0.5 * (lead - 1), ev.unit)
    old_mean = fcmod.c_to_unit(det, ev.unit)
    print(f"  sigma utilisé {rows[0]['sigma']:.2f} ({rows[0]['sigma_source']}), biais {rows[0]['bias_applied']:+.2f}"
          f" ; ancien sigma ≈ {old_sigma:.2f}")
    print(f"\n  {'tranche':>10s} {'bid':>6s} {'ask':>6s} {'p_new':>6s} {'p_old':>6s} {'edgeYES':>8s} {'edgeNO':>7s}")
    for r in rows:
        b = mk.Bucket(r["bucket_lo"], r["bucket_hi"])
        p_old = bucket_prob_normal(b, old_mean, old_sigma)
        f = lambda x: "  -   " if x is None else f"{x:6.2f}"
        print(f"  {r['bucket']:>10s} {f(r['best_bid'])} {f(r['best_ask'])} {r['p_model']:6.2f} {p_old:6.2f} "
              f"{f(r['edge_yes']):>8s} {f(r['edge_no']):>7s}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="weather_arb", description=__doc__)
    ap.add_argument("--model", help="modèle Open-Meteo (défaut WX_MODEL)")
    ap.add_argument("--prob-model", choices=["normal", "ensemble"], help="défaut WX_PROB_MODEL")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan", help="un scan, log des paper trades")
    p = sub.add_parser("loop", help="scan toutes les WX_SCAN_INTERVAL_MIN minutes")
    p.add_argument("--with-resolve", action="store_true")
    p = sub.add_parser("resolve", help="résout les trades/prédictions échus (WIN/LOSS)")
    p.add_argument("--official-only", action="store_true", help="ignorer la résolution provisoire METAR")
    p = sub.add_parser("calibrate", help="calibre biais/sigma par station et horizon")
    p.add_argument("--days", type=int, default=180)
    p.add_argument("--kind", choices=["high", "low"], default="high")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--stations", help="liste ICAO séparés par des virgules")
    g.add_argument("--from-markets", action="store_true", help="stations des marchés actifs")
    sub.add_parser("report", help="génère reports/report.md + report.json")
    p = sub.add_parser("explain", help="diagnostic détaillé d'un événement")
    p.add_argument("slug", help="slug Gamma de l'événement")
    args = ap.parse_args(argv)

    s = Settings()
    if args.model:
        s.model = args.model
    if args.prob_model:
        s.prob_model = args.prob_model
    {"scan": cmd_scan, "loop": cmd_loop, "resolve": cmd_resolve, "calibrate": cmd_calibrate,
     "report": cmd_report, "explain": cmd_explain}[args.cmd](s, args)


if __name__ == "__main__":
    main()
