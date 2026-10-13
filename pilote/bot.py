"""Bot unique sur Hyperliquid : arbitrage des taux + emprunt quand ca paie + tendance BTC/ETH. Simulation seulement.

Chaque jour, il calcule les positions a tenir, met a jour un portefeuille fictif (prix, financement encaisse,
staking, cout d'emprunt, frais) et envoie le point du jour.
  - Part arbitrage (1 - w_trend) : BTC + ETH en permanence (comptant + vente du perpetuel), plus au maximum
    2 altcoins dont le financement moyen 14 j depasse 20 %/an. Revue chaque semaine.
  - Emprunt : la part arbitrage passe a 1,5x le capital si le financement moyen 14 j de BTC/ETH depasse le cout
    d'emprunt + 5 points, a 2x au-dela de + 10 points. Revue chaque semaine.
  - Part tendance (w_trend) : BTC et ETH detenus sans couverture selon l'ensemble de 6 signaux de tendance
    (taille reduite si la volatilite depasse 40 %/an), le reste en arbitrage sur la meme crypto.

    python -m pilote.bot replay --since 2026-01-01       # rejoue la periode jour par jour avec les donnees locales
    python -m pilote.bot run --capital 10000             # simulation en direct (etat dans resultats/pilote/)
    python -m pilote.bot run --reset --capital 10000     # repartir de zero
    python -m pilote.bot run --profil agressif           # profil agressif (etat separe)

Profils : « equilibre » = 70 % arbitrage / 30 % tendance, emprunt 1,5x/2x, tendance sans levier.
« agressif » = 50/50, emprunt 2x/3x, tendance jusqu'a 1,5x (volatilite cible 60 %).

A planifier chaque jour vers 00:15 UTC.
"""
import argparse
import glob
import json
import os
import time
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
import requests

from common.notify import telegram
from funding.exchanges import HL, hyperliquid_history, norm_base
from momentum.data import BASE as BINANCE_SPOT
from momentum.data import DATA_DIR
from tendance.algo import ENSEMBLE, trend_up

CORE = ("BTC", "ETH")
DAY = pd.Timedelta(days=1)
STATE = os.path.join(os.path.dirname(DATA_DIR), "resultats", "pilote", "state_{}.json")


@dataclass
class Config:
    capital: float = 10_000.0
    w_trend: float = 0.3
    sat_apr: float = 0.20
    max_sats: int = 2
    lookback: int = 14
    min_volume: float = 20e6     # volume 24 h minimum d'une altcoin (mode direct)
    notional: float = 0.95       # part couverte quand le comptant sert de marge
    spot_fee: float = 0.00075
    perp_fee: float = 0.0002
    eth_stake: float = 0.03
    default_borrow: float = 0.06
    vol_target: float = 0.4
    trend_cap: float = 1.0                      # exposition max de la part tendance (1,5 = levier 1,5x)
    borrow_steps: tuple = ((0.10, 2.0), (0.05, 1.5))  # (ecart financement - emprunt, taille de la part arbitrage)


PROFILS = {
    "equilibre": {},
    "agressif": {"w_trend": 0.5, "vol_target": 0.6, "trend_cap": 1.5, "borrow_steps": ((0.10, 3.0), (0.05, 2.0))},
}


# ---------- sources de donnees ----------

class LocalSource:
    """Donnees deja telechargees (data/funding/hyperliquid et data/1d) : pour rejouer le passe."""

    def __init__(self):
        self.rates = {}
        for path in glob.glob(os.path.join(DATA_DIR, "funding", "hyperliquid", "*.csv")):
            df = pd.read_csv(path)
            self.rates[os.path.basename(path)[:-4]] = pd.Series(df["rate"].to_numpy(float),
                                                                index=pd.to_datetime(df["time"], unit="ms")).sort_index()
        self.px = {}

    def closes(self, coin):
        name = norm_base(coin) + "USDT"
        if name not in self.px:
            path = os.path.join(DATA_DIR, "1d", f"{name}.csv")
            self.px[name] = (pd.read_csv(path, parse_dates=["date"]).set_index("date")["close"]
                             if os.path.exists(path) else None)
        return self.px[name]

    def coins(self, t):
        return list(self.rates)

    def funding_apr(self, coin, t, days):
        s = self.rates.get(coin)
        if s is None:
            return np.nan
        w = s[(s.index >= t - days * DAY) & (s.index < t)]
        return w.sum() / days * 365 if len(w) else np.nan

    def funding_sum(self, coin, t0, t1):
        s = self.rates.get(coin)
        return 0.0 if s is None else float(s[(s.index >= t0) & (s.index < t1)].sum())

    def price(self, coin, t):
        c = self.closes(coin)
        if c is None:
            return np.nan
        c = c[c.index < t]  # cloture de la derniere journee terminee avant t
        return float(c.iloc[-1]) if len(c) else np.nan

    def trend_closes(self, coin, t):
        c = self.closes(coin)
        return c[c.index < t]

    def borrow_rate(self, t, default):
        return default  # pas d'historique des taux d'emprunt : taux fixe


class LiveSource:
    """API publiques : Hyperliquid (financement, prix, volumes), miroir Binance (bougies), Aave/OKX (emprunt)."""

    def __init__(self):
        meta, ctxs = requests.post(HL, json={"type": "metaAndAssetCtxs"}, timeout=30).json()
        self.ctx = {a["name"]: c for a, c in zip(meta["universe"], ctxs) if not a.get("isDelisted")}
        self.mids = {k: float(v) for k, v in requests.post(HL, json={"type": "allMids"}, timeout=30).json().items()}
        self.cache = {}

    def coins(self, t):
        # Pre-selection : volume suffisant et financement actuel au-dessus de la moitie du seuil.
        return [n for n, c in self.ctx.items() if float(c.get("dayNtlVlm") or 0) >= self.min_volume
                and float(c.get("funding") or 0) * 24 * 365 >= self.sat_apr / 2] + list(CORE)

    def _hist(self, coin, days):
        key = (coin, days)
        if key not in self.cache:
            end = int(time.time() * 1000)
            self.cache[key] = hyperliquid_history(coin, end - days * 86400000, end)
        return self.cache[key]

    def funding_apr(self, coin, t, days):
        rows = self._hist(coin, days)
        return sum(r for _, r in rows) / days * 365 if rows else np.nan

    def funding_sum(self, coin, t0, t1):
        rows = hyperliquid_history(coin, int(t0.timestamp() * 1000), int(t1.timestamp() * 1000))
        return float(sum(r for _, r in rows))

    def price(self, coin, t):
        return self.mids.get(coin, np.nan)

    def trend_closes(self, coin, t):
        kl = requests.get(BINANCE_SPOT + "/api/v3/klines", params={"symbol": coin + "USDT", "interval": "1d", "limit": 300},
                          timeout=30).json()[:-1]  # bougie du jour non terminee
        return pd.Series([float(k[4]) for k in kl], index=pd.to_datetime([k[0] for k in kl], unit="ms"))

    def borrow_rate(self, t, default):
        from funding.levier import borrow_rates
        rates = borrow_rates()
        return min(rates.values()) if rates else default


# ---------- decisions ----------

def weekly_choices(src, t, cfg):
    borrow = src.borrow_rate(t, cfg.default_borrow)
    core_apr = np.nanmean([src.funding_apr(c, t, cfg.lookback) for c in CORE])
    k = next((m for gap, m in cfg.borrow_steps if core_apr > borrow + gap), 1.0)
    cands = []
    for c in src.coins(t):
        if c in CORE or np.isnan(src.price(c, t)):
            continue
        apr = src.funding_apr(c, t, cfg.lookback)
        if apr >= cfg.sat_apr:
            cands.append((apr, c))
    sats = [c for _, c in sorted(cands, reverse=True)[: cfg.max_sats]]
    return {"k": k, "sats": sats, "borrow": borrow, "core_apr": float(core_apr)}


def targets(src, t, cfg, equity, weekly):
    """Positions cibles en dollars : comptant (positif) et perpetuel (negatif = vendu)."""
    spot, perp = {}, {}

    def add(coin, s, p):
        spot[coin] = spot.get(coin, 0.0) + s
        perp[coin] = perp.get(coin, 0.0) + p

    carry_cap = (1 - cfg.w_trend) * equity * weekly["k"]
    picks = list(CORE) + weekly["sats"]
    for c in picks:
        n = carry_cap * cfg.notional / len(picks)
        add(c, n, -n)
    expo = {}
    for c in CORE:
        closes = src.trend_closes(c, t)
        # part des signaux haussiers x taille selon la volatilite, plafonnee a trend_cap (1,5 = levier 1,5x)
        share = sum(float(trend_up(closes, k, n).iloc[-1]) for k, n in ENSEMBLE) / len(ENSEMBLE)
        vol = closes.pct_change().rolling(20).std().iloc[-1] * np.sqrt(365)
        e = share * min(cfg.trend_cap, cfg.vol_target / vol) if vol > 0 else 0.0
        expo[c] = e
        half = cfg.w_trend * equity / len(CORE)
        add(c, e * half, 0.0)
        n = max(0.0, 1 - e) * half * cfg.notional
        add(c, n, -n)
    return spot, perp, expo


# ---------- portefeuille fictif ----------

def new_state(cfg, t):
    return {"time": t.isoformat(), "equity": cfg.capital, "spot": {}, "perp": {}, "prices": {}, "weekly": None,
            "weekly_time": None, "history": [], "config": asdict(cfg)}


def step(src, state, t, cfg):
    """Fait vivre les positions depuis le dernier passage, puis se repositionne. Renvoie le detail du jour."""
    t0 = pd.Timestamp(state["time"])
    pnl = {"prix": 0.0, "financement": 0.0, "staking": 0.0, "emprunt": 0.0, "frais": 0.0}
    days = (t - t0) / DAY
    for c in set(state["spot"]) | set(state["perp"]):
        p0, p1 = state["prices"].get(c), src.price(c, t)
        s, p = state["spot"].get(c, 0.0), state["perp"].get(c, 0.0)
        if p0 and np.isfinite(p1):
            pnl["prix"] += (s + p) * (p1 / p0 - 1)
        pnl["financement"] += -p * src.funding_sum(c, t0, t)
        if c == "ETH":
            pnl["staking"] += s * cfg.eth_stake / 365 * days
    if state["weekly"]:
        # emprunt de la part arbitrage + comptant tendance au-dela de la part (levier tendance)
        borrowed = (state["weekly"]["k"] - 1) * (1 - cfg.w_trend) * state["equity"]
        borrowed += sum(max(0.0, e - 1) for e in state.get("expo", {}).values()) * cfg.w_trend * state["equity"] / len(CORE)
        pnl["emprunt"] = -borrowed * state["weekly"]["borrow"] / 365 * days
    equity = state["equity"] + sum(pnl.values())

    if state["weekly_time"] is None or t - pd.Timestamp(state["weekly_time"]) >= 7 * DAY - pd.Timedelta(hours=1):
        state["weekly"], state["weekly_time"] = weekly_choices(src, t, cfg), t.isoformat()
    spot, perp, expo = targets(src, t, cfg, equity, state["weekly"])
    fees = sum(abs(spot.get(c, 0) - state["spot"].get(c, 0)) for c in set(spot) | set(state["spot"])) * cfg.spot_fee
    fees += sum(abs(perp.get(c, 0) - state["perp"].get(c, 0)) for c in set(perp) | set(state["perp"])) * cfg.perp_fee
    pnl["frais"] = -fees
    equity -= fees
    old_spot = dict(state["spot"])
    state.update(time=t.isoformat(), equity=equity, spot=spot, perp=perp, expo=expo,
                 prices={c: src.price(c, t) for c in spot})
    state["history"].append({"time": t.isoformat(), "equity": equity, **pnl})
    return {"pnl": pnl, "expo": expo, "old_spot": old_spot}


def report(state, day, cfg):
    w = state["weekly"]
    eq = state["equity"]
    lines = [f"Pilote crypto (simulation) - {pd.Timestamp(state['time']):%d/%m/%Y %H:%M} UTC",
             f"Capital : {eq:,.0f} $ ({eq / cfg.capital - 1:+.1%} depuis le depart)",
             "Jour : " + ", ".join(f"{k} {v:+,.2f} $" for k, v in day["pnl"].items() if abs(v) >= 0.005),
             f"Emprunt : {'x' + str(w['k']) if w['k'] > 1 else 'aucun'} (financement BTC/ETH {w['core_apr']:+.1%}/an, "
             f"emprunt {w['borrow']:.1%}/an)",
             "Tendance : " + ", ".join(f"{c} {e:.0%} sans couverture" for c, e in day["expo"].items()),
             "Altcoins en arbitrage : " + (", ".join(w["sats"]) if w["sats"] else "aucune au-dessus de 20 %/an"),
             "Positions a tenir :"]
    for c in sorted(state["spot"], key=lambda c: -state["spot"][c]):
        s, p = state["spot"][c], state["perp"].get(c, 0.0)
        lines.append(f"  {c} : comptant {s:,.0f} $, perpetuel {p:,.0f} $ (exposition au prix {s + p:+,.0f} $)")
    return "\n".join(lines)


def summary(hist, cfg):
    h = pd.DataFrame(hist).set_index("time")
    h.index = pd.to_datetime(h.index)
    eq = h["equity"]
    m = eq.resample("ME").last()
    m = m / m.shift(1).fillna(cfg.capital) - 1
    dd = (eq / eq.cummax() - 1).min()
    print(f"\nCapital : {cfg.capital:,.0f} $ -> {eq.iloc[-1]:,.0f} $ ({eq.iloc[-1] / cfg.capital - 1:+.1%}) | pire chute {dd:.1%}")
    print("Detail : " + ", ".join(f"{c} {h[c].sum():+,.0f} $" for c in ("prix", "financement", "staking", "emprunt", "frais")))
    print("Par mois : " + " ".join(f"{d:%b} {v:+.1%}" for d, v in m.items()))


def replay(a, cfg):
    src = LocalSource()
    t = pd.Timestamp(a.since)
    end = pd.Timestamp(a.until) if a.until else min(s.index[-1] for c, s in src.rates.items() if c in CORE).normalize()
    state = new_state(cfg, t)
    step(src, state, t, cfg)                       # positions d'ouverture
    while t + DAY <= end:
        t += DAY
        day = step(src, state, t, cfg)
    print(report(state, day, cfg))
    summary(state["history"], cfg)


def run(a, cfg):
    src = LiveSource()
    src.min_volume, src.sat_apr = cfg.min_volume, cfg.sat_apr
    t = pd.Timestamp.now(tz="UTC").tz_localize(None)
    path = STATE.format(a.profil)
    if a.reset or not os.path.exists(path):
        state = new_state(cfg, t)
    else:
        with open(path) as f:
            state = json.load(f)
        conf = state["config"]
        conf["borrow_steps"] = tuple(tuple(x) for x in conf["borrow_steps"])
        cfg = Config(**conf)
    day = step(src, state, t, cfg)
    msg = f"[profil {a.profil}] " + report(state, day, cfg)
    print(msg)
    telegram(msg)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=1, default=float)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("replay", "run"))
    ap.add_argument("--since", default="2026-01-01")
    ap.add_argument("--until")
    ap.add_argument("--capital", type=float, default=10_000)
    ap.add_argument("--profil", choices=sorted(PROFILS), default="equilibre")
    ap.add_argument("--reset", action="store_true")
    a = ap.parse_args()
    cfg = Config(capital=a.capital, **PROFILS[a.profil])
    (replay if a.action == "replay" else run)(a, cfg)


if __name__ == "__main__":
    main()
