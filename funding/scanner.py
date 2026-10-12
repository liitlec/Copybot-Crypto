"""Scanner d'arbitrage des taux de financement (lecture seule, aucun ordre).

Deux montages, sans pari sur le prix :
  - « comptant + perpetuel » (cash and carry) : acheter au comptant ET vendre le perpetuel sur la meme
    plateforme quand le taux est positif -> on encaisse le financement.
  - « entre plateformes » : vendre le perpetuel la ou le taux est le plus haut, l'acheter la ou il est le
    plus bas -> on encaisse l'ecart.
Le rendement affiche est NET des frais d'entree et de sortie, etales sur la duree de detention prevue.

    python -m funding.scanner                       # tableau des meilleures occasions
    python -m funding.scanner --confirm             # + moyenne 7 jours et part de periodes positives
    python -m funding.scanner --alert 0.25 --every 60   # alerte Telegram au-dessus de 25 %/an, toutes les 60 min
"""
import argparse
import time
from collections import defaultdict

import pandas as pd

from common.notify import telegram
from funding.exchanges import EXCHANGES, HISTORY, snapshot


def carry_table(rates, min_vol, hold_days, spot_fee, perp_fee):
    drag = 2 * (spot_fee + perp_fee) * 365 / hold_days  # entree + sortie, sur les deux jambes
    rows = [{"montage": "comptant+perp", "crypto": r.coin, "vendre_perp": r.exchange, "couverture": f"comptant {r.exchange}",
             "taux_an": r.apr, "net_an": r.apr - drag, "volume_M": r.volume_usd / 1e6, "_short": (r.exchange, r.base)}
            for r in rates if r.has_spot and r.apr > 0 and r.volume_usd >= min_vol]
    return pd.DataFrame(rows)


def cross_table(rates, min_vol, hold_days, perp_fee):
    drag = 4 * perp_fee * 365 / hold_days  # deux perpetuels, entree + sortie
    by_coin = defaultdict(list)
    for r in rates:
        if r.volume_usd >= min_vol:
            by_coin[r.coin].append(r)
    rows = []
    for coin, rs in by_coin.items():
        if len({r.exchange for r in rs}) < 2:
            continue
        hi, lo = max(rs, key=lambda r: r.apr), min(rs, key=lambda r: r.apr)
        if hi.exchange == lo.exchange:
            continue
        spread = hi.apr - lo.apr
        rows.append({"montage": "entre plateformes", "crypto": coin, "vendre_perp": hi.exchange,
                     "couverture": f"perp {lo.exchange}", "taux_an": spread, "net_an": spread - drag,
                     "volume_M": min(hi.volume_usd, lo.volume_usd) / 1e6, "_short": (hi.exchange, hi.base),
                     "_long": (lo.exchange, lo.base)})
    return pd.DataFrame(rows)


def confirm(df, days=7):
    """Ajoute la moyenne des `days` derniers jours : un taux eleve un seul instant ne suffit pas."""
    end = int(time.time() * 1000)
    start = end - days * 86400 * 1000
    avg, pos = [], []
    for _, row in df.iterrows():
        try:
            ex, base = row["_short"]
            hist = HISTORY[ex](base, start, end)
            per_year = _periods_per_year(hist)
            s_avg = sum(r for _, r in hist) / len(hist) * per_year if hist else float("nan")
            s_pos = sum(r > 0 for _, r in hist) / len(hist) if hist else float("nan")
            if "_long" in row and isinstance(row["_long"], tuple):
                ex2, base2 = row["_long"]
                h2 = HISTORY[ex2](base2, start, end)
                if h2:
                    s_avg -= sum(r for _, r in h2) / len(h2) * _periods_per_year(h2)
            avg.append(s_avg)
            pos.append(s_pos)
        except Exception:
            avg.append(float("nan"))
            pos.append(float("nan"))
    df = df.copy()
    df["moy7j_an"] = avg
    df["periodes_pos"] = pos
    return df


def _periods_per_year(hist):
    if len(hist) < 2:
        return 3 * 365
    step_h = (hist[-1][0] - hist[0][0]) / (len(hist) - 1) / 3.6e6
    return 24 / max(step_h, 1e-9) * 365


def scan(args):
    rates = snapshot(args.exchanges)
    df = pd.concat([carry_table(rates, args.min_vol, args.hold_days, args.spot_fee, args.perp_fee),
                    cross_table(rates, args.min_vol, args.hold_days, args.perp_fee)], ignore_index=True)
    if df.empty:
        return df
    df = df.sort_values("net_an", ascending=False).head(args.top)
    if args.confirm:
        df = confirm(df)
    return df


def fmt(df):
    show = [c for c in df.columns if not c.startswith("_")]
    pct = {c: "{:+.1%}".format for c in ("taux_an", "net_an", "moy7j_an")} | {"periodes_pos": "{:.0%}".format,
                                                                             "volume_M": "{:,.0f}".format}
    return df[show].to_string(index=False, formatters={k: v for k, v in pct.items() if k in show})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exchanges", nargs="+", default=list(EXCHANGES))
    ap.add_argument("--min-vol", type=float, default=20e6, help="volume 24 h minimum du perpetuel (USD)")
    ap.add_argument("--hold-days", type=float, default=14, help="duree de detention prevue (etale les frais)")
    ap.add_argument("--spot-fee", type=float, default=0.001)
    ap.add_argument("--perp-fee", type=float, default=0.0005)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--confirm", action="store_true", help="verifier la moyenne 7 jours (plus lent)")
    ap.add_argument("--alert", type=float, help="alerte Telegram si net annualise >= ce seuil (ex. 0.25)")
    ap.add_argument("--every", type=float, help="relancer toutes les N minutes")
    a = ap.parse_args()
    while True:
        df = scan(a)
        stamp = time.strftime("%Y-%m-%d %H:%M")
        print(f"\n=== Arbitrage des taux de financement, {stamp} ===")
        print(fmt(df) if not df.empty else "aucune occasion")
        if a.alert is not None and not df.empty:
            key = "moy7j_an" if "moy7j_an" in df else "net_an"
            hits = df[df[key] >= a.alert]
            if not hits.empty:
                telegram(f"Arbitrage financement {stamp}\n" + fmt(hits))
        if not a.every:
            break
        time.sleep(a.every * 60)


if __name__ == "__main__":
    main()
