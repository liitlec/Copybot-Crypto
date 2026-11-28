"""Autopsie des trades fermés d'une caisse (04/11) : pour chaque trade, ce que le token montrait à l'achat (dossier
d'univers.jsonl le plus proche avant l'achat), puis ce que les bougies 5 min ont fait pendant et après le trade
(plus haut, plus bas, temps jusqu'au plus haut, prix 1 h et 4 h après la vente).

Sert à comprendre pourquoi un trade a gagné ou perdu, et si le signal existait au moment de l'achat. Signale aussi un
« ÉCART » quand le résultat enregistré ne ressemble pas du tout aux bougies (erreur de simulation possible : ne tire
alors aucune leçon de ce trade).

Usage : python3 autopsie.py /tmp/d [--caisse ia] [--dernier 30] [--champs liquidite,rotation_h1,...]"""
import argparse
import bisect
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import apprend as A  # noqa: E402

DEFAUT = ("age_h", "liquidite", "liq_sur_mcap", "rotation_h1", "volume_par_trader_h1", "part_vendeurs_h1",
          "transactions.h1.buyers", "transactions.m5.buyers", "acceleration_volume", "variation_prix_pct.h1",
          "variation_prix_pct.h6", "top10_pct")


def charger_univers(path, tokens):
    par_token = defaultdict(list)
    with open(path) as f:
        for ln in f:
            if not any(t in ln for t in tokens):
                continue
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if r.get("token") in tokens:
                par_token[r["token"]].append(r)
    for v in par_token.values():
        v.sort(key=lambda r: r["t"])
    return par_token


def bougies(d, pool):
    f = d / "ohlcv" / f"{pool}.json"
    try:
        return [tuple(x) for x in json.loads(f.read_text())["c"]] if f.exists() else []
    except ValueError:
        return []


def fmt(v):
    if v is None:
        return "—"
    if isinstance(v, float) and abs(v) < 10:
        return f"{v:.2f}"
    return f"{v:,.0f}".replace(",", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--caisse", default="ia")
    ap.add_argument("--dernier", type=int, default=30)
    ap.add_argument("--champs", default=",".join(DEFAUT))
    a = ap.parse_args()
    d = Path(a.data)
    champs = [c for c in a.champs.split(",") if c]
    trades = []
    for ln in (d / "trades.jsonl").read_text().splitlines():
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if r.get("book") == a.caisse and "ret" in r:
            trades.append(r)
    trades = trades[-a.dernier:]
    if not trades:
        print(f"aucun trade fermé pour la caisse {a.caisse}")
        return
    uni = charger_univers(d / "univers.jsonl", {r["token"] for r in trades})
    gagnants, perdants = defaultdict(list), defaultdict(list)
    for r in trades:
        rows = uni.get(r["token"], [])
        i = bisect.bisect_right([x["t"] for x in rows], r["t_in"]) - 1
        rec = rows[i] if i >= 0 and r["t_in"] - rows[i]["t"] < 900 else None
        c = bougies(d, r["pool"])
        avant = [px for ts, px in c if ts <= r["t_in"]]
        pendant = [(ts, px) for ts, px in c if r["t_in"] < ts <= r["t_out"]]
        apres = [(ts, px) for ts, px in c if ts > r["t_out"]]
        p0 = avant[-1] if avant else None
        ligne = [f"{r.get('name', r['token'][:6])[:16]:16}", f"{r['ret'] * 100:+7.1f} %", f"{r['minutes']:4d} min",
                 r["reason"][:34]]
        if p0 and pendant:
            hi = max(pendant, key=lambda x: x[1])
            lo = min(px for _, px in pendant)
            ligne += [f"plus haut {hi[1] / p0 - 1:+.0%} à {round((hi[0] - r['t_in']) / 60)} min", f"plus bas {lo / p0 - 1:+.0%}"]
            fin = pendant[-1][1] / p0 - 1
            if abs(fin - r["ret"]) > 0.25 and not r["reason"].startswith(("pool vidé", "pool disparu")):
                ligne.append(f"ÉCART : bougies {fin:+.0%} à la vente, enregistré {r['ret']:+.0%}")
        else:
            ligne.append("pas de bougies pendant le trade")
        if p0:
            for h in (1, 4):
                xs = [px for ts, px in apres if ts <= r["t_out"] + h * 3600]
                if xs:
                    ligne.append(f"{h} h après la vente {xs[-1] / p0 - 1:+.0%}")
        print(" | ".join(ligne))
        if rec:
            vals = {k: A.champ(rec, k) for k in champs}
            print("    à l'achat : " + ", ".join(f"{k}={fmt(v)}" for k, v in vals.items()))
            cible = gagnants if r["ret"] > 0 else perdants
            for k, v in vals.items():
                if v is not None:
                    cible[k].append(v)
        else:
            print("    à l'achat : dossier introuvable dans univers.jsonl")
    print(f"\nMédianes à l'achat ({sum(r['ret'] > 0 for r in trades)} gagnants / {sum(r['ret'] <= 0 for r in trades)} perdants) :")
    med = lambda xs: sorted(xs)[len(xs) // 2] if xs else None
    for k in champs:
        print(f"  {k:28} gagnants {fmt(med(gagnants[k])):>10}   perdants {fmt(med(perdants[k])):>10}")


if __name__ == "__main__":
    main()
