"""Faut-il emprunter pour agrandir l'arbitrage ? Compare le financement encaisse au cout de l'emprunt.

Emprunter X $ pour agrandir la position rapporte (taux de financement - taux d'emprunt) x X par an.
Ca ne vaut le coup que si l'ecart couvre largement le risque en plus (liquidation, taux qui changent).

    python -m funding.levier                         # etat du jour
    python -m funding.levier --every 360             # verifier toutes les 6 h, alerte Telegram si l'etat change
    python -m funding.levier --exchanges hyperliquid okx --coins BTC ETH --days 7

Taux d'emprunt : Aave v3 (USDC/USDT, Ethereum et Arbitrum) et OKX (taux de base USDT/USDC).
"""
import argparse
import time

import requests

from common.notify import telegram
from funding.exchanges import HISTORY

AAVE = "https://api.v3.aave.com/graphql"
AAVE_MARKETS = {"AaveV3Ethereum", "AaveV3Arbitrum"}
OKX_QUOTA = "https://www.okx.com/api/v5/public/interest-rate-loan-quota"
STABLES = {"USDC", "USDT"}


def aave_borrow_rates():
    q = "{ markets(request:{chainIds:[1,42161]}) { name reserves { underlyingToken { symbol } borrowInfo { apy { value } } } } }"
    data = requests.post(AAVE, json={"query": q}, timeout=30).json()["data"]["markets"]
    out = {}
    for m in data:
        if m["name"] not in AAVE_MARKETS:
            continue
        for r in m["reserves"]:
            sym = r["underlyingToken"]["symbol"]
            if sym in STABLES and r["borrowInfo"]:
                key = f"Aave {m['name'].replace('AaveV3', '')} {sym}"
                out[key] = min(out.get(key, 9), float(r["borrowInfo"]["apy"]["value"]))  # USDC natif plutot que bridge
    return out


def okx_borrow_rates():
    basic = requests.get(OKX_QUOTA, timeout=30).json()["data"][0]["basic"]
    return {f"OKX {d['ccy']}": float(d["rate"]) * 365 for d in basic if d["ccy"] in STABLES}  # taux journalier


def borrow_rates():
    out = {}
    for fn in (aave_borrow_rates, okx_borrow_rates):
        try:
            out.update(fn())
        except Exception as e:
            print(f"{fn.__name__} : echec ({e})")
    return out


def funding_rates(exchanges, coins, days):
    """Taux de financement moyen annualise sur `days` jours, par plateforme et par crypto."""
    end = int(time.time() * 1000)
    start = end - days * 86400 * 1000
    out = {}
    for ex in exchanges:
        for c in coins:
            try:
                rows = HISTORY[ex](c, start, end)
                if len(rows) < 2:
                    continue
                span = (rows[-1][0] - rows[0][0]) / 86400000 + (rows[1][0] - rows[0][0]) / 86400000
                out[(ex, c)] = sum(r for _, r in rows) / span * 365
            except Exception as e:
                print(f"{ex} {c} : echec ({e})")
    return out


def verdict(spread, margin):
    if spread >= 2 * margin:
        return "EMPRUNT INTERESSANT : jusqu'a 2x le capital", 2
    if spread >= margin:
        return "emprunt possible : 1,5x le capital", 1
    if spread >= 0:
        return "pas la peine : l'ecart ne paie pas le risque", 0
    return "REMBOURSER : l'emprunt coute plus que le financement", -1


def check(a):
    fr = funding_rates(a.exchanges, a.coins, a.days)
    br = borrow_rates()
    if not fr or not br:
        return None, "donnees indisponibles"
    best_ex = max(a.exchanges, key=lambda ex: sum(v for (e, _), v in fr.items() if e == ex) or -9)
    fund = sum(v for (e, _), v in fr.items() if e == best_ex) / max(1, sum(1 for e, _ in fr if e == best_ex))
    cheapest = min(br, key=br.get)
    spread = fund - br[cheapest]
    text, level = verdict(spread, a.margin)
    lines = [f"Levier de l'arbitrage, {time.strftime('%d/%m/%Y %H:%M')}",
             f"Financement moyen {a.days} j ({'+'.join(a.coins)}) :"]
    lines += [f"  {e} {c} : {v:+.1%}/an" for (e, c), v in sorted(fr.items())]
    lines.append("Cout de l'emprunt :")
    lines += [f"  {k} : {v:.1%}/an" for k, v in sorted(br.items(), key=lambda kv: kv[1])]
    lines.append(f"Ecart ({best_ex} - {cheapest}) : {spread:+.1%}/an -> {text}")
    if level > 0:
        lines.append(f"Gain en plus pour 1 000 $ empruntes : environ {spread * 1000:,.0f} $/an")
    return level, "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exchanges", nargs="+", default=["hyperliquid", "binance", "okx"])
    ap.add_argument("--coins", nargs="+", default=["BTC", "ETH"])
    ap.add_argument("--days", type=int, default=7, help="moyenne du financement sur N jours")
    ap.add_argument("--margin", type=float, default=0.05, help="ecart minimum pour emprunter (0.05 = 5 points)")
    ap.add_argument("--every", type=float, help="relancer toutes les N minutes, alerte Telegram si l'etat change")
    a = ap.parse_args()
    last = None
    while True:
        level, msg = check(a)
        print("\n" + msg)
        if level is not None and level != last:
            if last is not None or level != 0:
                telegram(msg)
            last = level
        if not a.every:
            break
        time.sleep(a.every * 60)


if __name__ == "__main__":
    main()
