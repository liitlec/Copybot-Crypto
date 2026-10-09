"""Backtest du bot momentum altcoins (bougies journalieres).

Regles (signal a la cloture du jour J, execution a l'ouverture de J+1) :
  - Regime : BTC cloture au-dessus de sa moyenne `regime_len` jours, sinon aucune nouvelle entree
    (et, si `regime_exit`, on sort de tout a l'ouverture suivante).
  - Univers : volume moyen 30 j >= `min_liq` USDT, cotee depuis >= `min_age` jours.
  - Entree : cloture > plus haut des `breakout` jours precedents ET volume du jour >= `vol_mult` x moyenne 20 j.
    Classement des candidats par performance 30 j, au plus `max_pos` positions.
  - Stop initial : entree - `stop_atr` x ATR14. Taille : `risk` x capital / (entree - stop),
    plafonnee a `lev` x capital / `max_pos` de notionnel par position (levier total <= `lev`).
  - Sortie partielle : `partial_frac` de la position a +`partial_r` R.
  - Stop suiveur : plus haute cloture depuis l'entree - `trail_atr` x ATR14 (ne redescend jamais).
  - Couts : frais + glissement a chaque ordre (plus fort sur les stops), financement journalier sur le notionnel
    (perpetuels). Hypothese prudente : si stop et objectif sont touches le meme jour, le stop passe en premier.

    python -m momentum.backtest                      # parametres par defaut, 2020 -> fin des donnees
    python -m momentum.backtest --start 2021-01-01 --risk 0.03 --lev 3
    python -m momentum.backtest --grid               # robustesse : petite grille de parametres
"""
import argparse
import glob
import itertools
import os
from dataclasses import dataclass, field, replace

import numpy as np
import pandas as pd

from momentum.data import DATA_DIR


@dataclass
class Params:
    breakout: int = 20
    vol_mult: float = 2.0
    regime_len: int = 50
    regime_exit: bool = True
    min_liq: float = 5e6
    min_age: int = 60
    max_pos: int = 5
    risk: float = 0.02
    lev: float = 3.0
    stop_atr: float = 2.5
    trail_atr: float = 3.0
    partial_r: float = 3.0
    partial_frac: float = 0.5
    fee: float = 0.0005          # frais taker par ordre
    slip: float = 0.0005         # glissement par ordre
    stop_slip: float = 0.003     # glissement supplementaire sur les stops (marche qui chute, carnet mince)
    funding_year: float = 0.11   # cout de financement annuel des positions acheteuses (~0,01 % / 8 h)
    btc: str = "BTCUSDT"


@dataclass
class Panel:
    dates: pd.DatetimeIndex
    syms: list
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    qv: np.ndarray


def load_panel(interval="1d", start=None, end=None, folder=None):
    folder = folder or os.path.join(DATA_DIR, interval)
    frames = {}
    for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        df = pd.read_csv(path, parse_dates=["date"]).set_index("date")
        if not df.empty:
            frames[os.path.basename(path)[:-4]] = df
    if not frames:
        raise SystemExit(f"Aucune donnee dans {folder} : lancer d'abord  python -m momentum.data")
    return panel_from_frames(frames, start, end)


def panel_from_frames(frames, start=None, end=None):
    syms = sorted(frames)
    fld = {k: pd.DataFrame({s: frames[s][k] for s in syms}).sort_index() for k in ("open", "high", "low", "close", "quote_volume")}
    idx = fld["close"].index
    keep = np.ones(len(idx), bool)
    if start:
        keep &= idx >= pd.Timestamp(start)
    if end:
        keep &= idx <= pd.Timestamp(end)
    # Les indicateurs ont besoin d'historique avant `start` : on garde tout, et on ne trade qu'a partir de `start`.
    p = Panel(idx, syms, *(fld[k].to_numpy(float) for k in ("open", "high", "low", "close", "quote_volume")))
    p.first_trade = int(np.argmax(keep)) if keep.any() else len(idx)
    p.last_trade = int(len(keep) - np.argmax(keep[::-1]) - 1) if keep.any() else -1
    return p


def indicators(p, prm):
    c, h, l = (pd.DataFrame(x) for x in (p.c, p.h, p.l))
    qv = pd.DataFrame(p.qv)
    prev_c = c.shift(1)
    tr = np.maximum(h - l, np.maximum((h - prev_c).abs(), (l - prev_c).abs()))
    ind = {
        "hh": h.rolling(prm.breakout).max().shift(1).to_numpy(),
        "atr": tr.rolling(14).mean().to_numpy(),
        "vavg": qv.rolling(20).mean().shift(1).to_numpy(),
        "liq": qv.rolling(30).mean().to_numpy(),
        "age": c.notna().cumsum().to_numpy(),
        "mom": (c / c.shift(30) - 1).to_numpy(),
    }
    if prm.btc in p.syms:
        b = c[p.syms.index(prm.btc)]
        ind["regime"] = (b > b.rolling(prm.regime_len).mean()).to_numpy()
    else:
        ind["regime"] = np.ones(len(p.dates), bool)
    return ind


@dataclass
class Pos:
    j: int
    entry_i: int
    entry: float
    qty: float
    stop: float
    risk_unit: float
    peak: float
    r_dist: float
    last: float
    partial_done: bool = False
    pnl: float = 0.0
    last_i: int = 0


@dataclass
class Result:
    equity: pd.Series
    trades: pd.DataFrame
    params: Params = field(default_factory=Params)


def run(p, prm=Params(), capital=10_000.0):
    ind = indicators(p, prm)
    cost = prm.fee + prm.slip
    fund_day = prm.funding_year / 365
    cash, pos, pending, trades = capital, {}, [], []
    exit_all = False
    eq = np.full(len(p.dates), np.nan)

    def close_part(ps, qty, px, i, why, final):
        nonlocal cash
        cash += qty * px * (1 - cost)
        ps.pnl += qty * (px - ps.entry) - qty * px * cost
        ps.qty -= qty
        if final:
            trades.append({"sym": p.syms[ps.j], "entry_date": p.dates[ps.entry_i], "exit_date": p.dates[i],
                           "entry": ps.entry, "exit": px, "why": why, "pnl": ps.pnl,
                           "r": ps.pnl / ps.risk_unit if ps.risk_unit > 0 else 0.0})

    for i in range(p.first_trade, p.last_trade + 1):
        o, h, l, c = p.o[i], p.h[i], p.l[i], p.c[i]
        equity_open = cash + sum(ps.qty * (o[ps.j] if np.isfinite(o[ps.j]) else ps.last) for ps in pos.values())

        # 1. Sorties de regime a l'ouverture.
        if exit_all:
            for j, ps in list(pos.items()):
                if np.isfinite(o[j]):
                    close_part(ps, ps.qty, o[j], i, "regime", True)
                    del pos[j]
            exit_all = False

        # 2. Entrees a l'ouverture (signaux de la veille).
        gross = sum(ps.qty * o[ps.j] for ps in pos.values() if np.isfinite(o[ps.j]))
        for j in pending:
            if j in pos or not np.isfinite(o[j]) or len(pos) >= prm.max_pos:
                continue
            entry = o[j]
            stop = entry - prm.stop_atr * ind["atr"][i - 1, j]
            if not np.isfinite(stop) or stop <= 0 or stop >= entry:
                continue
            qty = prm.risk * equity_open / (entry - stop)
            qty = min(qty, prm.lev * equity_open / prm.max_pos / entry, max(0.0, prm.lev * equity_open - gross) / entry)
            if qty <= 0:
                continue
            cash -= qty * entry * (1 + cost)
            gross += qty * entry
            pos[j] = Pos(j, i, entry, qty, stop, qty * (entry - stop) + qty * entry * cost, entry, entry - stop, entry)
            pos[j].pnl = -qty * entry * cost
            pos[j].last_i = i
        pending = []

        # 3. Gestion des positions sur la bougie du jour (stop teste avant l'objectif : hypothese prudente).
        for j, ps in list(pos.items()):
            if not np.isfinite(c[j]):
                if i - ps.last_i > 5:  # plus de cotation : retrait de la cote, sortie au dernier prix connu
                    close_part(ps, ps.qty, ps.last, i, "retrait", True)
                    del pos[j]
                continue
            ps.last, ps.last_i = c[j], i
            if o[j] <= ps.stop:
                close_part(ps, ps.qty, o[j] * (1 - prm.stop_slip), i, "stop_gap", True)
                del pos[j]
                continue
            if l[j] <= ps.stop:
                close_part(ps, ps.qty, ps.stop * (1 - prm.stop_slip), i, "stop", True)
                del pos[j]
                continue
            target = ps.entry + prm.partial_r * ps.r_dist
            if not ps.partial_done and prm.partial_frac > 0 and h[j] >= target:
                close_part(ps, ps.qty * prm.partial_frac, max(target, o[j]), i, "partiel", False)
                ps.partial_done = True
            cash -= ps.qty * c[j] * fund_day
            ps.pnl -= ps.qty * c[j] * fund_day
            ps.peak = max(ps.peak, c[j])
            if np.isfinite(ind["atr"][i, j]):
                ps.stop = max(ps.stop, ps.peak - prm.trail_atr * ind["atr"][i, j])

        # 4. Valeur du compte a la cloture.
        eq[i] = cash + sum(ps.qty * (c[ps.j] if np.isfinite(c[ps.j]) else ps.last) for ps in pos.values())
        if eq[i] <= 0:
            eq[i:] = 0
            break

        # 5. Signaux pour demain.
        if not ind["regime"][i]:
            exit_all = prm.regime_exit and bool(pos)
            continue
        ok = (np.isfinite(c) & (c > ind["hh"][i]) & (p.qv[i] >= prm.vol_mult * ind["vavg"][i])
              & (ind["liq"][i] >= prm.min_liq) & (ind["age"][i] >= prm.min_age))
        cand = [j for j in np.flatnonzero(ok) if j not in pos]
        cand.sort(key=lambda j: -np.nan_to_num(ind["mom"][i, j], nan=-1e9))
        pending = cand[: max(0, prm.max_pos - len(pos))]

    # Positions encore ouvertes : valorisees a la derniere cloture.
    last = p.last_trade
    for j, ps in list(pos.items()):
        px = p.c[last, j] if np.isfinite(p.c[last, j]) else ps.last
        close_part(ps, ps.qty, px, last, "ouverte", True)

    equity = pd.Series(eq[p.first_trade:p.last_trade + 1], index=p.dates[p.first_trade:p.last_trade + 1]).ffill()
    return Result(equity, pd.DataFrame(trades), prm)


def stats(res):
    e = res.equity.dropna()
    t = res.trades
    if e.empty:
        return {}
    years = max((e.index[-1] - e.index[0]).days / 365.25, 1e-9)
    dd = (e / e.cummax() - 1).min()
    monthly = e.resample("ME").last().pct_change().dropna()
    cagr = (e.iloc[-1] / e.iloc[0]) ** (1 / years) - 1 if e.iloc[-1] > 0 else -1.0
    return {
        "final": e.iloc[-1], "cagr": cagr, "max_dd": dd, "calmar": cagr / abs(dd) if dd < 0 else np.nan,
        "trades": len(t), "win_rate": (t["pnl"] > 0).mean() if len(t) else np.nan,
        "avg_r": t["r"].mean() if len(t) else np.nan, "best_r": t["r"].max() if len(t) else np.nan,
        "neg_months": f"{(monthly < 0).sum()}/{len(monthly)}",
    }


def yearly(res):
    e = res.equity.dropna()
    y = e.resample("YE").last()
    first = pd.Series([e.iloc[0]], index=[e.index[0]])
    return (pd.concat([first, y]).pct_change().dropna()).rename(lambda d: d.year)


def benchmark(p, sym="BTCUSDT"):
    if sym not in p.syms:
        return None
    s = pd.Series(p.c[:, p.syms.index(sym)], index=p.dates).iloc[p.first_trade:p.last_trade + 1].dropna()
    return s / s.iloc[0] * 10_000


def fmt_stats(s):
    return (f"capital final {s['final']:,.0f} $ | CAGR {s['cagr']:+.1%} | pire chute {s['max_dd']:.1%} | "
            f"Calmar {s['calmar']:.2f} | {s['trades']} trades | gagnants {s['win_rate']:.0%} | "
            f"moyenne {s['avg_r']:+.2f} R | meilleur {s['best_r']:+.1f} R | mois negatifs {s['neg_months']}")


def report(p, prm, out_dir=None):
    res = run(p, prm)
    s = stats(res)
    print("=== Bot momentum altcoins ===")
    print(prm)
    print(fmt_stats(s))
    print("\nPar annee :")
    bench = benchmark(p)
    by = yearly(res)
    bb = yearly(Result(bench, pd.DataFrame())) if bench is not None else None
    for y, r in by.items():
        extra = f"   (BTC achete et garde : {bb[y]:+.0%})" if bb is not None and y in bb else ""
        print(f"  {y} : {r:+.0%}{extra}")
    if bench is not None:
        bdd = (bench / bench.cummax() - 1).min()
        print(f"\nBTC achete et garde : {bench.iloc[-1]:,.0f} $, pire chute {bdd:.0%}")
    if len(res.trades):
        t = res.trades
        print("\nSorties :", t["why"].value_counts().to_dict())
        print("Meilleurs trades :")
        print(t.nlargest(5, "r")[["sym", "entry_date", "exit_date", "r"]].to_string(index=False))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        res.equity.to_csv(os.path.join(out_dir, "equity.csv"))
        res.trades.to_csv(os.path.join(out_dir, "trades.csv"), index=False)
    return res


def grid(p, base):
    rows = []
    for brk, trail, regime, risk in itertools.product((20, 55), (2.0, 3.0, 4.0), (50, 100), (0.01, 0.02, 0.03)):
        prm = replace(base, breakout=brk, trail_atr=trail, regime_len=regime, risk=risk)
        s = stats(run(p, prm))
        rows.append({"breakout": brk, "trail": trail, "regime": regime, "risk": risk, **s})
    df = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(df.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print(f"\nCombinaisons rentables : {(df['cagr'] > 0).sum()}/{len(df)} | CAGR median {df['cagr'].median():+.1%} "
          f"| pire chute mediane {df['max_dd'].median():.1%}")
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2020-06-01")
    ap.add_argument("--end")
    ap.add_argument("--grid", action="store_true")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(DATA_DIR), "resultats"))
    for f in Params.__dataclass_fields__.values():
        if f.type in (int, float, str):
            ap.add_argument("--" + f.name.replace("_", "-"), type=f.type, default=f.default)
    ap.add_argument("--no-regime-exit", action="store_true")
    a = ap.parse_args()
    prm = Params(**{k: getattr(a, k) for k in Params.__dataclass_fields__ if k != "regime_exit"},
                 regime_exit=not a.no_regime_exit)
    panel = load_panel(start=a.start, end=a.end)
    if a.grid:
        grid(panel, prm)
    else:
        report(panel, prm, a.out)
