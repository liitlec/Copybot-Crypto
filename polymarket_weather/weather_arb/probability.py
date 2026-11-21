"""Probabilités par tranche : loi normale calibrée ou ensemble ECMWF habillé (kernel dressing)."""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean, pstdev

from .config import DEFAULT_SIGMA_C, SIGMA_GROWTH_AFTER_7
from .markets import Bucket
from .store import read_json

SQRT2 = math.sqrt(2)


def norm_cdf(x: float) -> float:
    if x == float("inf"):
        return 1.0
    if x == float("-inf"):
        return 0.0
    return 0.5 * (1 + math.erf(x / SQRT2))


def bucket_prob_normal(b: Bucket, mean: float, sigma: float) -> float:
    """P(valeur rapportée dans [lo, hi]) = P(T continu dans [lo-0.5, hi+0.5[)."""
    return norm_cdf((b.cont_hi - mean) / sigma) - norm_cdf((b.cont_lo - mean) / sigma)


def bucket_prob_ensemble(b: Bucket, members: list[float], dress_sigma: float) -> float:
    """Moyenne sur les membres d'une gaussienne centrée sur chaque membre (kernel dressing).
    Un simple comptage de membres donnerait 0 % / 100 % sur les tranches de 1 °C (51 membres)."""
    return fmean(bucket_prob_normal(b, m, dress_sigma) for m in members)


def recenter_members(members: list[float], center: float) -> list[float]:
    """Garde la forme/dispersion de l'ensemble mais la recentre sur la prévision déterministe
    débiaisée. L'ensemble Open-Meteo est en pas de 3 h interpolés : son max brut est biaisé bas."""
    mu = fmean(members)
    return [center + (m - mu) for m in members]


def dress_sigma(calibrated_sigma: float, members: list[float], floor: float) -> float:
    """Variance totale ≈ max(sigma calibrée², spread²) : on ne descend jamais sous l'erreur
    observée historiquement, mais on garde une dispersion plus large si l'ensemble l'indique."""
    spread = pstdev(members) if len(members) > 1 else 0.0
    return max(math.sqrt(max(calibrated_sigma ** 2 - spread ** 2, 0.0)), floor)


def event_distribution(buckets: list[Bucket], prob_fn, complete: bool) -> list[float]:
    """Probabilités de toutes les tranches d'un événement ; renormalisées si la partition est complète."""
    probs = [prob_fn(b) for b in buckets]
    total = sum(probs)
    if complete and total > 0:
        probs = [p / total for p in probs]
    return probs


def condition_on_observed(buckets: list[Bucket], probs: list[float], obs_reported: int | None,
                          kind: str) -> list[float]:
    """J0 : si le max observé depuis minuit vaut déjà X, toute tranche < X est impossible
    (et inversement pour le min). Les cotes intègrent cette info, le modèle doit aussi."""
    if obs_reported is None:
        return probs
    out = []
    for b, p in zip(buckets, probs):
        impossible = (kind == "high" and b.hi is not None and b.hi < obs_reported) or \
                     (kind == "low" and b.lo is not None and b.lo > obs_reported)
        out.append(0.0 if impossible else p)
    total = sum(out)
    return [p / total for p in out] if total > 0 else probs


def clip(p: float, eps: float) -> float:
    return min(max(p, eps), 1 - eps)


@dataclass
class ErrorModel:
    bias_c: float      # à AJOUTER à la prévision (obs - prévision moyen)
    sigma_c: float
    source: str        # station | global | default


class SigmaTable:
    """Table d'erreurs issue de `calibrate` ; repli sur DEFAULT_SIGMA_C si absente."""

    def __init__(self, path: Path | None, shrink_k: int = 20, floor_c: float = 0.6):
        self.data = read_json(path, {}) if path else {}
        self.k = shrink_k
        self.floor = floor_c

    @staticmethod
    def _lookup(table: dict, lead: int) -> dict | None:
        if not table:
            return None
        if str(lead) in table:
            return table[str(lead)]
        known = sorted(int(k) for k in table)
        last = known[-1]
        if lead > last:
            row = dict(table[str(last)])
            extra = SIGMA_GROWTH_AFTER_7 * (lead - last)
            for key in ("sd", "rmse"):
                if key in row:
                    row[key] = row[key] + extra
            return row
        return table[str(known[0])]

    def get(self, icao: str | None, lead: int) -> ErrorModel:
        lead = max(lead, 0)
        g = self._lookup(self.data.get("global", {}), lead)
        s = self._lookup(self.data.get("stations", {}).get(icao or "", {}), lead)
        if g is None:
            sd = DEFAULT_SIGMA_C.get(lead, DEFAULT_SIGMA_C[7] + SIGMA_GROWTH_AFTER_7 * (lead - 7))
            return ErrorModel(0.0, sd, "default")
        if s is None or s.get("n", 0) == 0:
            # Station inconnue : biais inconnu -> RMSE brut (biais inclus) comme sigma.
            return ErrorModel(0.0, max(g["rmse"], self.floor), "global")
        n = s["n"]
        w = n / (n + self.k)
        bias = w * s["bias"]
        var = (n * s["sd"] ** 2 + self.k * g["sd"] ** 2) / (n + self.k)
        return ErrorModel(bias, max(math.sqrt(var), self.floor), "station")
