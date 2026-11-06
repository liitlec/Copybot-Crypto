"""Validation glissante (06/11) : au lieu d'un seul découpage ancien / récent, la règle est jugée sur --fenetres
périodes successives de même durée. Une règle solide gagne sur la plupart d'entre elles ; une règle qui ne gagne que
sur une période a eu de la chance (un token, un jour de marché).

Verdict « SOLIDE » si au moins 2/3 des fenêtres avec assez de trades sont positives, qu'aucune ne perd plus de
--pire (20 %) en moyenne, et que la moyenne reste positive sans la meilleure fenêtre.

Usage : python3 glissante.py /tmp/d regle.json [regle2.json ...] [--fenetres 6] [--min 3] [--pire 0.2] [--depuis ...]"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import apprend as A  # noqa: E402
import banc  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("regles", nargs="+")
    ap.add_argument("--fenetres", type=int, default=6)
    ap.add_argument("--min", type=int, default=3, help="trades minimum pour juger une fenêtre")
    ap.add_argument("--pire", type=float, default=0.2)
    ap.add_argument("--depuis", default=None)
    a = ap.parse_args()
    rows, paths, rugs = banc.donnees(Path(a.data), a.depuis)
    t_min, t_max = min(r["t"] for r in rows), max(r["t"] for r in rows)
    pas = (t_max - t_min) / a.fenetres
    for path in a.regles:
        rule = A.regle_ia(json.loads(Path(path).read_text()))
        if rule is None:
            print(f"\n{path} : règle invalide")
            continue
        tr = banc.simule(rule, rows, paths, rugs)
        print(f"\n{path} : {len(tr)} trades sur {a.fenetres} fenêtres de {pas / 3600:.0f} h")
        moys = []
        for k in range(a.fenetres):
            lo, hi = t_min + k * pas, t_min + (k + 1) * pas
            xs = [x for t, x, *_ in tr if lo <= t < hi or (k == a.fenetres - 1 and t == hi)]
            debut = time.strftime("%d/%m %Hh", time.gmtime(lo))
            if len(xs) >= a.min:
                m = sum(xs) / len(xs)
                moys.append((m, len(xs)))
                print(f"  {debut} : n={len(xs):3d} moyenne {m:+.1%}")
            else:
                print(f"  {debut} : n={len(xs):3d} (trop peu)")
        if len(moys) < 3:
            print("  verdict : pas assez de fenêtres jugées (au moins 3)")
            continue
        pos = sum(1 for m, _ in moys if m > 0)
        pire = min(m for m, _ in moys)
        sans_best = sorted(moys, key=lambda x: -x[0])[1:]
        m_sans = sum(m * n for m, n in sans_best) / sum(n for _, n in sans_best)
        ok = pos >= 2 * len(moys) / 3 and pire > -a.pire and m_sans > 0
        print(f"  {pos}/{len(moys)} fenêtres positives, pire {pire:+.1%}, sans la meilleure {m_sans:+.1%} -> "
              + ("SOLIDE" if ok else "FRAGILE"))


if __name__ == "__main__":
    main()
