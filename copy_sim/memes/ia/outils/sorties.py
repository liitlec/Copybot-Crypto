"""Optimiseur de sorties (06/11) : garde l'ENTRÉE d'une règle et essaie une grille de sorties (stop, objectif, stop
suiveur, durée), sur les mêmes achats, avec le banc réaliste. Chaque sortie est classée sur la partie ANCIENNE ;
les meilleures sont ensuite jugées sur la partie RÉCENTE, qu'elles n'ont pas vue.

Usage : python3 sorties.py /tmp/d regle.json [--test-heures 24] [--essais N] [--top 10]
        [--stops -0.1,-0.2,-0.3] [--objectifs 0,0.3,0.6,1.5] [--suiveurs 0,0.2,0.35] [--durees 1,4,12]
(0 = pas d'objectif ou pas de stop suiveur). Le seuil des essais compte toutes les sorties de la grille.
Une sortie n'est retenue que si elle bat la sortie actuelle de la règle sur le récent aussi."""
import argparse
import itertools
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import apprend as A  # noqa: E402
import banc  # noqa: E402
from criblage import moy_t  # noqa: E402


def nombres(s):
    return [float(x) for x in s.split(",") if x.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("regle")
    ap.add_argument("--test-heures", type=float, default=24)
    ap.add_argument("--essais", type=int, default=0)
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--stops", default="-0.1,-0.15,-0.2,-0.3,-0.45")
    ap.add_argument("--objectifs", default="0,0.2,0.4,0.8,1.5")
    ap.add_argument("--suiveurs", default="0,0.15,0.25,0.4")
    ap.add_argument("--durees", default="1,4,12,24")
    ap.add_argument("--depuis", default=None)
    a = ap.parse_args()
    raw = json.loads(Path(a.regle).read_text())
    base = A.regle_ia(raw)
    if base is None:
        sys.exit("règle invalide")
    rows, paths, rugs = banc.donnees(Path(a.data), a.depuis)
    achats = banc.entrees(base, rows, paths)
    if len(achats) < 10:
        sys.exit(f"trop peu d'achats pour cette entrée ({len(achats)})")
    split = max(r["t"] for r, _ in achats) - a.test_heures * 3600
    grille = list(itertools.product(nombres(a.stops), nombres(a.objectifs), nombres(a.suiveurs), nombres(a.durees)))
    n_ess = max(2, len(grille) + a.essais)
    seuil = max(2.0, math.sqrt(2 * math.log(n_ess)))

    def juge(rule):
        old, new = [], []
        for r, c in achats:
            res = banc.resultat(rule, r, c, rugs)
            if res is not None:
                (old if r["t"] < split else new).append(res[0])
        return old, new

    res = []
    for stop, obj, suiv, duree in grille:
        sx = {"stop": stop, "objectif": obj or None, "suiveur": suiv or None, "duree_max_h": duree,
              "sortie_volume": base["sortie_volume"]}
        rule = A.regle_ia(dict(raw, sortie=sx))
        old, new = juge(rule)
        if len(old) >= 10:
            m_o, t_o = moy_t(old)
            res.append((m_o, t_o, len(old), new, sx))
    old0, new0 = juge(base)
    m0o, t0o = moy_t(old0)
    m0n, _ = moy_t(new0)
    print(f"{len(achats)} achats (ancien {sum(1 for r, _ in achats if r['t'] < split)}) ; {len(grille)} sorties essayées ; "
          f"seuil t {seuil:.2f}")
    print(f"sortie actuelle : ancien n={len(old0)} {m0o:+.1%} t={t0o:.2f} ; récent n={len(new0)} "
          f"{(m0n if m0n is not None else float('nan')):+.1%}")
    res.sort(key=lambda x: -x[0])
    print(f"\n{'stop':>6} {'objectif':>8} {'suiveur':>8} {'durée':>6}   ancien (n, moy, t)       récent (n, moy)")
    meilleure = None
    for m_o, t_o, n_o, new, sx in res[:a.top]:
        m_n, _ = moy_t(new)
        ok = t_o >= seuil and m_n is not None and (m0n is None or m_n > m0n) and len(new) >= 5
        if ok and meilleure is None:
            meilleure = sx
        f = lambda v: "—" if v is None else f"{v:+.0%}"  # noqa: E731
        print(f"{'RETENUE ' if ok else '        '}{sx['stop']:+.0%} {f(sx['objectif']):>8} {f(sx['suiveur']):>8} "
              f"{sx['duree_max_h']:>5g}h   n={n_o:4d} {m_o:+7.1%} t={t_o:+5.2f}   n={len(new):4d} "
              f"{(m_n if m_n is not None else float('nan')):+7.1%}")
    if meilleure:
        print("\nsortie candidate (à mettre en challengeuse avec la même entrée) :")
        print(json.dumps({k: v for k, v in meilleure.items() if v is not None}, ensure_ascii=False))
    else:
        print("\naucune sortie ne passe à la fois le seuil sur l'ancien et la sortie actuelle sur le récent")


if __name__ == "__main__":
    main()
