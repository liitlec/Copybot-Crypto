"""Banc d'essai de l'IA chercheuse : rejoue une règle au format memes/ia/regle.json sur les données du VPS, avec la
même entrée, la même sortie (vérifiée sur la clôture de chaque bougie de 5 min, comme le VPS) et les mêmes frais.

Usage : python3 banc.py DOSSIER_DONNEES regle.json [regle2.json ...] [--test-heures 24]
DOSSIER_DONNEES doit contenir univers.jsonl et ohlcv/<pool>.json (copiés depuis http://140.82.38.41:8787/).
Affiche, pour chaque règle : nombre de trades, moyenne nette, borne basse (moyenne − 2 marges d'erreur), part de
gagnants, sur la période ancienne et sur les dernières heures (test), puis jour par jour."""
import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import apprend as A  # noqa: E402


def simule(rule, rows, paths):
    out, last = [], {}
    for r in rows:
        if r["t"] - last.get(r["token"], -1e18) < 24 * 3600 or not A.entre_ia(rule, r):
            continue
        c = [(ts, px) for ts, px in paths.get(r["pool"], []) if ts > r["t"]]
        if not c:
            continue
        last[r["token"]] = r["t"]
        pic, x, why = 0.0, 0.0, None
        for ts, px in c:
            x = px / r["prix"] - 1
            pic = max(pic, x)
            why = A.sortir_ia(rule, x, pic, (ts - r["t"]) / 3600, False)
            if why:
                break
        if not why and (c[-1][0] - r["t"]) / 3600 < rule["duree_max_h"]:
            continue  # trade pas encore terminé
        out.append((r["t"], x - A.couts(r.get("liquidite")), r["token"]))
    return out


def resume(xs):
    s = A.stats(xs)
    win = sum(x > 0 for x in xs) / len(xs) if xs else 0
    m = "—" if s["m"] is None else f"{s['m']:+.1%}"
    bas = "—" if s["bas"] is None else f"{s['bas']:+.1%}"
    return f"n={s['n']:4d}  moyenne={m:>7}  borne basse={bas:>7}  gagnants={win:.0%}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("regles", nargs="+")
    ap.add_argument("--test-heures", type=float, default=24)
    a = ap.parse_args()
    d = Path(a.data)
    rows = A.charger(d / "univers.jsonl", 0)
    paths = {}
    for f in (d / "ohlcv").glob("*.json"):
        paths[f.stem] = [tuple(x) for x in json.loads(f.read_text())["c"]]
    now = max(r["t"] for r in rows)
    split = now - a.test_heures * 3600
    print(f"{len(rows)} lignes, {len(paths)} pools avec prix, test = dernières {a.test_heures:g} h")
    for path in a.regles:
        rule = A.regle_ia(json.loads(Path(path).read_text()))
        if rule is None:
            print(f"\n{path} : règle invalide")
            continue
        tr = simule(rule, rows, paths)
        old = [x for t, x, _ in tr if t < split]
        new = [x for t, x, _ in tr if t >= split]
        print(f"\n{path} (v{rule['version']})\n  ancien : {resume(old)}\n  test   : {resume(new)}")
        days = defaultdict(list)
        for t, x, _ in tr:
            days[time.strftime("%Y-%m-%d", time.gmtime(t))].append(x)
        for k in sorted(days):
            print(f"  {k} : {resume(days[k])}")


if __name__ == "__main__":
    main()
