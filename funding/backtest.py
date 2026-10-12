"""Backtest « comptant + perpetuel » sur l'historique des taux de financement.

Regle : tous les `rebalance` jours, garder les `top_n` cryptos dont le financement moyen des `lookback`
derniers jours est le plus haut (et au-dessus de `min_apr`), a poids egaux. Pour chacune : achat au comptant
+ vente du perpetuel, on encaisse le financement (et on le paie s'il devient negatif).
Capital : le comptant est paye en entier et le perpetuel demande 1/`lev` de marge, donc le notionnel
couvert vaut lev / (1 + lev) du capital.

    python -m funding.backtest download --exchange binance --top 40 --start 2022-01-01
    python -m funding.backtest run --exchange binance
    python -m funding.backtest grid --exchange binance

Limites : l'ecart de prix entre comptant et perpetuel (base) a l'entree et a la sortie n'est pas modelise ;
la liste des cryptos est celle des plus gros volumes AUJOURD'HUI (biais : les cryptos disparues manquent).
"""
import argparse
import glob
import itertools
import os
import time
from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

from funding.exchanges import HISTORY, SNAPSHOT, binance_archive_symbols, binance_spot_volumes

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "funding")


@dataclass
class Params:
    top_n: int = 5
    lookback: int = 7
    rebalance: int = 7
    min_apr: float = 0.05
    lev: float = 3.0
    spot_fee: float = 0.001
    perp_fee: float = 0.0005
    slip: float = 0.0005          # par jambe, a chaque ordre


def download(exchange, top, start):
    folder = os.path.join(DATA, exchange)
    os.makedirs(folder, exist_ok=True)
    if exchange == "binance":
        # Archives publiques data.binance.vision : marche meme la ou l'API futures est bloquee.
        vol = binance_spot_volumes()
        bases = sorted((s[:-4] for s in binance_archive_symbols() if s[:-4] in vol), key=lambda b: -vol[b])[:top]
        fetch = HISTORY["binance_archive"]
    else:
        rates = [r for r in SNAPSHOT[exchange]() if exchange == "hyperliquid" or r.has_spot]
        bases = [r.base for r in sorted(rates, key=lambda r: -r.volume_usd)[:top]]
        fetch = HISTORY[exchange]
    start_ms = int(pd.Timestamp(start).timestamp() * 1000)
    end_ms = int(time.time() * 1000)
    for n, base in enumerate(bases, 1):
        path = os.path.join(folder, f"{base}.csv")
        old = pd.read_csv(path) if os.path.exists(path) else pd.DataFrame(columns=["time", "rate"])
        since = int(old["time"].max()) + 1 if len(old) else start_ms
        rows = fetch(base, since, end_ms)
        df = pd.concat([old, pd.DataFrame(rows, columns=["time", "rate"])]).drop_duplicates("time").sort_values("time")
        df.to_csv(path, index=False)
        print(f"[{n}/{len(bases)}] {base} : {len(df)} reglements")


def load_daily(exchange, start=None, end=None, folder=None):
    """Financement encaisse par jour et par unite de notionnel vendu (somme des reglements du jour)."""
    folder = folder or os.path.join(DATA, exchange)
    cols = {}
    for path in glob.glob(os.path.join(folder, "*.csv")):
        df = pd.read_csv(path)
        if df.empty:
            continue
        s = pd.Series(df["rate"].to_numpy(float), index=pd.to_datetime(df["time"], unit="ms"))
        cols[os.path.basename(path)[:-4]] = s.resample("D").sum(min_count=1)
    if not cols:
        raise SystemExit(f"Aucune donnee dans {folder} : lancer d'abord  python -m funding.backtest download")
    daily = pd.DataFrame(cols).sort_index()
    if start:
        daily = daily[daily.index >= pd.Timestamp(start) - pd.Timedelta(days=60)]  # historique pour la moyenne
    if end:
        daily = daily[daily.index <= pd.Timestamp(end)]
    daily.attrs["start"] = pd.Timestamp(start) if start else daily.index[0]
    return daily


def run(daily, prm=Params()):
    f = daily.to_numpy(float)
    score = daily.rolling(prm.lookback, min_periods=prm.lookback).mean().to_numpy() * 365
    first = int(np.searchsorted(daily.index, daily.attrs.get("start", daily.index[0])))
    first = max(first, prm.lookback)
    notional = prm.lev / (1 + prm.lev)
    leg_cost = prm.spot_fee + prm.perp_fee + 2 * prm.slip
    w = np.zeros(f.shape[1])
    held, rets = [], []
    for i in range(first, len(daily)):
        if (i - first) % prm.rebalance == 0:
            sc = np.where(np.isfinite(score[i - 1]), score[i - 1], -np.inf)
            pick = [j for j in np.argsort(-sc)[: prm.top_n] if sc[j] >= prm.min_apr]
            new = np.zeros_like(w)
            if pick:
                new[pick] = notional / len(pick)
            cost = np.abs(new - w).sum() * leg_cost
            w = new
        else:
            cost = 0.0
        # Une crypto sans reglement ce jour-la (retiree, pas encore cotee) rapporte 0.
        r = float(np.nansum(w * np.nan_to_num(f[i], nan=0.0))) - cost
        rets.append(r)
        held.append(int((w > 0).sum()))
    idx = daily.index[first:]
    return pd.Series(np.cumprod(1 + np.array(rets)), index=idx), pd.Series(held, index=idx)


def stats(curve, held):
    if curve.empty:
        return {}
    years = max((curve.index[-1] - curve.index[0]).days / 365.25, 1e-9)
    cagr = curve.iloc[-1] ** (1 / years) - 1
    dd = (curve / curve.cummax() - 1).min()
    weekly = curve.resample("W").last().pct_change().dropna()
    monthly = curve.resample("ME").last().pct_change().dropna()
    return {"rendement_an": cagr, "pire_chute": dd, "pire_mois": monthly.min() if len(monthly) else np.nan,
            "semaines_neg": f"{(weekly < 0).sum()}/{len(weekly)}", "positions_moy": held.mean(),
            "jours_investi": (held > 0).mean()}


def yearly(curve):
    y = curve.resample("YE").last()
    return (y / y.shift(1).fillna(1.0) - 1).rename(lambda d: d.year)


def report(daily, prm):
    curve, held = run(daily, prm)
    s = stats(curve, held)
    print("=== Comptant + perpetuel ===")
    print(prm)
    print(f"rendement {s['rendement_an']:+.1%}/an | pire chute {s['pire_chute']:.1%} | pire mois {s['pire_mois']:+.1%} | "
          f"semaines negatives {s['semaines_neg']} | {s['positions_moy']:.1f} positions en moyenne | "
          f"investi {s['jours_investi']:.0%} du temps")
    for y, r in yearly(curve).items():
        print(f"  {y} : {r:+.1%}")
    for coin in ("BTC", "ETH"):
        if coin in daily:
            c, h = run(_with_start(daily[[coin]].copy(), daily), replace(prm, top_n=1, min_apr=-1e9, rebalance=10 ** 9))
            print(f"Repere : {coin} garde en permanence -> {stats(c, h)['rendement_an']:+.1%}/an")
    return curve


def _with_start(df, ref):
    df.attrs["start"] = ref.attrs.get("start")
    return df


def grid(daily, base):
    rows = []
    for top_n, lookback, rebalance, min_apr in itertools.product((3, 5, 10), (3, 7, 14), (1, 7), (0.0, 0.1)):
        prm = replace(base, top_n=top_n, lookback=lookback, rebalance=rebalance, min_apr=min_apr)
        rows.append({"top_n": top_n, "lookback": lookback, "rebalance": rebalance, "min_apr": min_apr,
                     **stats(*run(daily, prm))})
    df = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(df.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print(f"\nCombinaisons rentables : {(df['rendement_an'] > 0).sum()}/{len(df)} | "
          f"mediane {df['rendement_an'].median():+.1%}/an")
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("download", "run", "grid"))
    ap.add_argument("--exchange", default="binance", choices=("binance", "bybit", "hyperliquid"))
    ap.add_argument("--top", type=int, default=40, help="download : nombre de cryptos (plus gros volumes)")
    ap.add_argument("--start", default="2022-01-01")
    ap.add_argument("--end")
    for k, v in Params.__dataclass_fields__.items():
        ap.add_argument("--" + k.replace("_", "-"), type=v.type, default=v.default)
    a = ap.parse_args()
    if a.action == "download":
        download(a.exchange, a.top, a.start)
        return
    prm = Params(**{k: getattr(a, k) for k in Params.__dataclass_fields__})
    daily = load_daily(a.exchange, a.start, a.end)
    (grid if a.action == "grid" else report)(daily, prm)


if __name__ == "__main__":
    main()
