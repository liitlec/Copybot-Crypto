"""Récupération et parsing des marchés de température Polymarket (Gamma API).

Points clés corrigés par rapport à une lecture naïve :
  * station + source de résolution extraites de la description (URL Wunderground -> ICAO)
  * unité (°C/°F) lue dans le marché, jamais supposée
  * tranches en DEGRÉS ENTIERS RAPPORTÉS : "25°C" = valeur affichée 25 = continu [24.5, 25.5[ ;
    "26°C or higher" = [25.5, +inf[ ; "84-85°F" = [83.5, 85.5[
  * date cible = jour LOCAL de la station
  * prix d'entrée = best ask (YES) / 1 - best bid (NO), pas outcomePrices
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Iterator

from . import http
from .config import GAMMA_URL, TAG_SLUG

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], start=1)}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})
MONTHS["sept"] = 9


@dataclass(frozen=True)
class Bucket:
    """Tranche en valeurs entières rapportées, bornes INCLUSIVES. None = ouvert."""
    lo: int | None
    hi: int | None

    @property
    def cont_lo(self) -> float:
        return float("-inf") if self.lo is None else self.lo - 0.5

    @property
    def cont_hi(self) -> float:
        return float("inf") if self.hi is None else self.hi + 0.5

    def contains(self, reported: int) -> bool:
        return (self.lo is None or reported >= self.lo) and (self.hi is None or reported <= self.hi)

    def label(self, unit: str) -> str:
        if self.lo is None:
            return f"<={self.hi}°{unit}"
        if self.hi is None:
            return f">={self.lo}°{unit}"
        return f"{self.lo}°{unit}" if self.lo == self.hi else f"{self.lo}-{self.hi}°{unit}"


@dataclass
class MarketSpec:
    market_id: str
    condition_id: str | None
    slug: str | None
    question: str
    label: str
    bucket: Bucket | None
    best_bid: float | None
    best_ask: float | None
    last_price: float | None
    outcome_yes_price: float | None
    liquidity: float
    closed: bool
    accepting_orders: bool

    @property
    def mid(self) -> float | None:
        if self.best_bid is not None and self.best_ask is not None:
            return (self.best_bid + self.best_ask) / 2
        return self.outcome_yes_price

    @property
    def spread(self) -> float | None:
        if self.best_bid is not None and self.best_ask is not None:
            return self.best_ask - self.best_bid
        return None

    def resolved_yes(self) -> bool | None:
        """Résultat officiel si le marché est clos et réglé (outcomePrices = 1/0)."""
        if not self.closed or self.outcome_yes_price is None:
            return None
        if self.outcome_yes_price >= 0.99:
            return True
        if self.outcome_yes_price <= 0.01:
            return False
        return None


@dataclass
class EventSpec:
    event_id: str
    slug: str
    title: str
    city: str | None
    kind: str | None            # "high" | "low"
    target_date: date | None
    unit: str | None            # "C" | "F"
    station_icao: str | None
    station_name: str | None
    resolution_source: str      # wunderground | noaa | hko | unknown
    resolution_url: str | None
    markets: list[MarketSpec] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all([self.city, self.kind, self.target_date, self.unit]) and bool(self.markets)


# ---------------------------------------------------------------- parsing helpers

_TITLE_RE = re.compile(
    r"(highest|lowest|high|low)\s+temp(?:erature)?\s+in\s+(.+?)\s+on\s+([A-Za-z]+)\.?\s+(\d{1,2})",
    re.I)
_WU_ICAO_RE = re.compile(r"wunderground\.com/[^\s\"'<>]*?/([A-Z]{4})(?=[/?#\s\"'<>.,;)]|$)")
_ICAO_HINT_RE = re.compile(r"\b(?:ICAO|station(?: code| id)?)\s*[:(]?\s*([A-Z]{4})\b")
_STATION_NAME_RE = re.compile(r"recorded (?:at|by) (?:the )?(.+?)\s+(?:weather )?station", re.I)
_URL_RE = re.compile(r"https?://[^\s\"'<>)]+")


def _f(x) -> float | None:
    if x is None or x == "":
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _json_list(x) -> list:
    if isinstance(x, list):
        return x
    if isinstance(x, str) and x.strip().startswith("["):
        try:
            return json.loads(x)
        except ValueError:
            return []
    return []


def parse_unit(*texts: str) -> str | None:
    blob = " ".join(t for t in texts if t)
    has_f = bool(re.search(r"°\s*F\b|fahrenheit", blob, re.I))
    has_c = bool(re.search(r"°\s*C\b|celsius", blob, re.I))
    if has_f and not has_c:
        return "F"
    if has_c and not has_f:
        return "C"
    return None  # ambigu -> le marché sera ignoré


_NUM = r"(-?\d+(?:\.\d+)?)"


def parse_bucket(label: str) -> Bucket | None:
    """Parse '26°C or higher', '17°C or below', '84-85°F', '25°C', 'between 84-85°F'."""
    if not label:
        return None
    s = label.replace("–", "-").replace("—", "-").replace("º", "°").strip()
    m = re.search(_NUM + r"\s*°?\s*[CF]?\s*(?:or|and)\s+(higher|above|more|greater|over)", s, re.I)
    if m:
        return Bucket(_int(m.group(1)), None)
    m = re.search(_NUM + r"\s*°?\s*[CF]?\s*(?:or|and)\s+(lower|below|less|under)", s, re.I)
    if m:
        return Bucket(None, _int(m.group(1)))
    m = re.search(_NUM + r"\s*°?\s*[CF]?\s*(?:-|to)\s*" + _NUM + r"\s*°", s, re.I)
    if m:
        lo, hi = _int(m.group(1)), _int(m.group(2))
        return Bucket(min(lo, hi), max(lo, hi))
    m = re.search(r"(?:^|\s|be\s)" + _NUM + r"\s*°\s*[CF]\b", s, re.I)
    if m:
        v = _int(m.group(1))
        return Bucket(v, v)
    return None


def _int(x: str) -> int:
    v = float(x)
    if v != int(v):
        raise ValueError(f"borne non entière : {x}")
    return int(v)


def parse_title(title: str, end_date: str | None) -> tuple[str | None, str | None, date | None]:
    m = _TITLE_RE.search(title or "")
    if not m:
        return None, None, None
    kind = "high" if m.group(1).lower().startswith("high") else "low"
    city = m.group(2).strip()
    month = MONTHS.get(m.group(3).lower())
    day = int(m.group(4))
    if not month:
        return city, kind, None
    ref = _parse_dt(end_date) or datetime.utcnow()
    # Année : celle qui place la date au plus près de endDate (gère décembre/janvier).
    candidates = []
    for y in (ref.year - 1, ref.year, ref.year + 1):
        try:
            candidates.append(date(y, month, day))
        except ValueError:
            pass
    target = min(candidates, key=lambda d: abs((d - ref.date()).days)) if candidates else None
    return city, kind, target


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def parse_resolution(description: str, resolution_source: str | None = None
                     ) -> tuple[str | None, str | None, str, str | None]:
    """-> (icao, station_name, source_kind, url)."""
    text = f"{description or ''} {resolution_source or ''}"
    urls = [u.rstrip(".,;") for u in _URL_RE.findall(text)]
    icao = None
    m = _WU_ICAO_RE.search(text)
    if m:
        icao = m.group(1)
    else:
        m = _ICAO_HINT_RE.search(text)
        if m:
            icao = m.group(1)
    name_m = _STATION_NAME_RE.search(text)
    name = name_m.group(1).strip() if name_m else None
    low = text.lower()
    if "wunderground" in low:
        kind = "wunderground"
    elif "weather.gov.hk" in low or "hong kong observatory" in low:
        kind = "hko"
    elif "weather.gov" in low or "noaa" in low or "ncei" in low:
        kind = "noaa"
    else:
        kind = "unknown"
    url = next((u for u in urls if "wunderground" in u or "weather" in u or "noaa" in u),
               urls[0] if urls else None)
    return icao, name, kind, url


def parse_market(m: dict) -> MarketSpec:
    label = m.get("groupItemTitle") or m.get("question") or ""
    bucket = None
    try:
        bucket = parse_bucket(label) or parse_bucket(m.get("question") or "")
    except ValueError:
        bucket = None
    prices = _json_list(m.get("outcomePrices"))
    outcomes = [str(o).lower() for o in _json_list(m.get("outcomes"))]
    yes_idx = outcomes.index("yes") if "yes" in outcomes else 0
    yes_price = _f(prices[yes_idx]) if len(prices) > yes_idx else None
    return MarketSpec(
        market_id=str(m.get("id")),
        condition_id=m.get("conditionId"),
        slug=m.get("slug"),
        question=m.get("question") or "",
        label=label,
        bucket=bucket,
        best_bid=_f(m.get("bestBid")),
        best_ask=_f(m.get("bestAsk")),
        last_price=_f(m.get("lastTradePrice")),
        outcome_yes_price=yes_price,
        liquidity=_f(m.get("liquidityNum")) or _f(m.get("liquidity")) or 0.0,
        closed=bool(m.get("closed")),
        accepting_orders=bool(m.get("acceptingOrders", not m.get("closed"))),
    )


def parse_event(ev: dict) -> EventSpec:
    title = ev.get("title") or ""
    raw_markets = ev.get("markets") or []
    description = ev.get("description") or (raw_markets[0].get("description") if raw_markets else "") or ""
    res_src = ev.get("resolutionSource") or (raw_markets[0].get("resolutionSource") if raw_markets else None)
    city, kind, target = parse_title(title, ev.get("endDate"))
    if not city and raw_markets:  # repli sur la question du 1er marché
        city, kind, target = parse_title(raw_markets[0].get("question") or "", ev.get("endDate"))
    icao, st_name, src_kind, url = parse_resolution(description, res_src)
    labels = " ".join((m.get("groupItemTitle") or "") for m in raw_markets)
    unit = parse_unit(description, title, labels)

    spec = EventSpec(
        event_id=str(ev.get("id")), slug=ev.get("slug") or "", title=title, city=city, kind=kind,
        target_date=target, unit=unit, station_icao=icao, station_name=st_name,
        resolution_source=src_kind, resolution_url=url,
        markets=[parse_market(m) for m in raw_markets],
    )
    if not icao:
        spec.warnings.append("station ICAO introuvable dans la description")
    if unit is None:
        spec.warnings.append("unité °C/°F ambiguë")
    if src_kind not in ("wunderground", "noaa"):
        spec.warnings.append(f"source de résolution '{src_kind}' : vérifier la correspondance avec METAR")
    if any(m.bucket is None for m in spec.markets):
        spec.warnings.append("tranche(s) non parsée(s)")
    spec.warnings.extend(check_partition([m.bucket for m in spec.markets if m.bucket]))
    return spec


def check_partition(buckets: list[Bucket]) -> list[str]:
    """Vérifie que les tranches couvrent tout l'axe sans trou ni chevauchement."""
    if not buckets:
        return ["aucune tranche"]
    bs = sorted(buckets, key=lambda b: (float("-inf") if b.lo is None else b.lo))
    warns = []
    if bs[0].lo is not None:
        warns.append("pas de tranche ouverte basse")
    if bs[-1].hi is not None:
        warns.append("pas de tranche ouverte haute")
    for a, b in zip(bs, bs[1:]):
        if a.hi is None or b.lo is None:
            warns.append("tranche ouverte au milieu")
        elif b.lo != a.hi + 1:
            warns.append(f"trou/chevauchement entre {a} et {b}")
    return warns


# ---------------------------------------------------------------- API

def iter_events(closed: bool = False, page_size: int = 100, max_pages: int = 50) -> Iterator[dict]:
    for page in range(max_pages):
        params = {"tag_slug": TAG_SLUG, "closed": str(closed).lower(), "limit": page_size,
                  "offset": page * page_size}
        if not closed:
            params["active"] = "true"
        batch = http.get(f"{GAMMA_URL}/events", params)
        if not batch:
            return
        yield from batch
        if len(batch) < page_size:
            return


def fetch_event_by_slug(slug: str) -> dict | None:
    data = http.get(f"{GAMMA_URL}/events", {"slug": slug})
    return data[0] if data else None


def fetch_market(market_id: str) -> dict | None:
    try:
        return http.get(f"{GAMMA_URL}/markets/{market_id}")
    except RuntimeError:
        return None


def fetch_temperature_events() -> list[EventSpec]:
    return [parse_event(ev) for ev in iter_events()]
