"""Bot momentum en simulation (« paper trading ») : aucun ordre reel.

Chaque jour apres la cloture (00:00 UTC) : met a jour les bougies, rejoue exactement les regles du backtest
depuis la date de depart de la simulation, et envoie le point du jour (entrees, sorties, positions, achats
prevus demain). Rejouer depuis le depart garantit que la simulation suit les memes regles que le backtest.

    python -m momentum.live --since 2026-10-13               # depart de la simulation, 10 000 $ fictifs
    python -m momentum.live --since 2026-10-13 --no-update   # sans retelecharger les donnees

A planifier chaque jour vers 00:15 UTC (cron, ou Planificateur de taches Windows).
"""
import argparse
import os

import pandas as pd

from common.notify import telegram
from momentum.backtest import DATA_DIR, Params, load_panel, run, stats
from momentum.data import download

OUT = os.path.join(os.path.dirname(DATA_DIR), "resultats", "live")


def daily_report(res, capital):
    e = res.equity.dropna()
    last = e.index[-1]
    t = res.trades
    closed = t[(t["why"] != "ouverte") & (t["exit_date"] == last)] if len(t) else t
    opened = t[t["entry_date"] == last] if len(t) else t
    lines = [f"Bot momentum (simulation) - cloture du {last:%d/%m/%Y}",
             f"Capital : {e.iloc[-1]:,.0f} $ ({e.iloc[-1] / capital - 1:+.1%} depuis le depart)"]
    if len(e) > 1:
        lines.append(f"Jour : {e.iloc[-1] / e.iloc[-2] - 1:+.2%}")
    for _, r in opened.iterrows():
        lines.append(f"  ACHAT {r['sym']} a {r['entry']:.6g}")
    for _, r in closed.iterrows():
        lines.append(f"  VENTE {r['sym']} a {r['exit']:.6g} ({r['why']}, {r['r']:+.2f} R)")
    if res.open_positions:
        lines.append("Positions ouvertes :")
        for p in res.open_positions:
            lines.append(f"  {p['sym']} : entree {p['entry']:.6g}, stop {p['stop']:.6g}, {p['r_open']:+.2f} R")
    else:
        lines.append("Aucune position ouverte.")
    if res.exit_all:
        lines.append("Bitcoin sous sa moyenne : tout sera vendu a l'ouverture.")
    elif res.pending:
        lines.append("Achats prevus a l'ouverture : " + ", ".join(res.pending))
    s = stats(res)
    if s.get("trades"):
        lines.append(f"Depuis le depart : {s['trades']} trades, pire chute {s['max_dd']:.1%}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True, help="date de depart de la simulation (AAAA-MM-JJ)")
    ap.add_argument("--capital", type=float, default=10_000)
    ap.add_argument("--no-update", action="store_true")
    a = ap.parse_args()
    if not a.no_update:
        download(start="2020-01-01")
    panel = load_panel(start=a.since)
    if panel.first_trade > panel.last_trade:
        raise SystemExit(f"Pas encore de bougie terminee depuis le {a.since}.")
    res = run(panel, Params(), a.capital)
    msg = daily_report(res, a.capital)
    print(msg)
    telegram(msg)
    os.makedirs(OUT, exist_ok=True)
    res.equity.to_csv(os.path.join(OUT, "equity.csv"))
    res.trades.to_csv(os.path.join(OUT, "trades.csv"), index=False)
    pd.DataFrame(res.open_positions).to_csv(os.path.join(OUT, "positions.csv"), index=False)


if __name__ == "__main__":
    main()
