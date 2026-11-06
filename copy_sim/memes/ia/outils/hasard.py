"""Test contre le hasard (06/11) : la règle fait-elle mieux que des achats tirés au hasard parmi les mêmes tokens ?

On simule la règle (banc réaliste). Puis, des milliers de fois, on tire au hasard autant d'achats que la règle en a
fait, LE MÊME JOUR que chacun des siens, parmi tous les tokens qui passaient le filtre ce jour-là, avec la MÊME
sortie. La part des tirages qui font au moins aussi bien que la règle est la « chance d'être du hasard » (p) :
sous 5 %, la règle choisit vraiment ses tokens ; au-dessus, son résultat vient du marché du moment ou de la sortie,
pas de son entrée. Avec plusieurs règles testées, divise 5 % par le nombre de règles.

Usage : python3 hasard.py /tmp/d regle.json [--tirages 2000] [--depuis ...] [--graine 1]"""
import argparse
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import apprend as A  # noqa: E402
import banc  # noqa: E402


def jour(t):
    return time.strftime("%Y-%m-%d", time.gmtime(t))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("regle")
    ap.add_argument("--tirages", type=int, default=2000)
    ap.add_argument("--depuis", default=None)
    ap.add_argument("--graine", type=int, default=1)
    a = ap.parse_args()
    raw = json.loads(Path(a.regle).read_text())
    rule = A.regle_ia(raw)
    if rule is None:
        sys.exit("règle invalide")
    rows, paths, rugs = banc.donnees(Path(a.data), a.depuis)
    tr = banc.simule(rule, rows, paths, rugs)
    if len(tr) < 5:
        sys.exit(f"trop peu de trades pour juger ({len(tr)})")
    # référence : même délai de rachat et même sortie, sans aucune condition d'entrée
    libre = A.regle_ia(dict(raw, entree={"conditions": []}, classement={"champ": "score"}))
    pool = defaultdict(list)
    for t, x, *_ in banc.simule(libre, rows, paths, rugs):
        pool[jour(t)].append(x)
    besoin = defaultdict(int)
    for t, *_ in tr:
        besoin[jour(t)] += 1
    jours = [j for j in besoin if pool[j]]
    if not jours:
        sys.exit("aucun achat de référence les mêmes jours")
    m_regle = sum(x for t, x, *_ in tr if jour(t) in jours) / sum(besoin[j] for j in jours)
    rnd = random.Random(a.graine)
    moy = []
    for _ in range(a.tirages):
        xs = [x for j in jours for x in rnd.choices(pool[j], k=besoin[j])]
        moy.append(sum(xs) / len(xs))
    moy.sort()
    p = sum(1 for m in moy if m >= m_regle) / len(moy)
    med = moy[len(moy) // 2]
    print(f"règle : {len(tr)} trades, moyenne {m_regle:+.1%} (sur les {len(jours)} jours comparables)")
    print(f"hasard, mêmes jours et même sortie : médiane {med:+.1%}, 5 % des tirages au-dessus de "
          f"{moy[int(0.95 * len(moy))]:+.1%} ({sum(len(v) for v in pool.values())} achats possibles)")
    print(f"avantage de l'entrée : {m_regle - med:+.1%} par trade ; chance d'être du hasard p = {p:.1%} -> "
          + ("la règle choisit vraiment ses tokens" if p < 0.05 else
             "pas mieux que le hasard : le résultat vient du marché ou de la sortie, pas de l'entrée"))


if __name__ == "__main__":
    main()
