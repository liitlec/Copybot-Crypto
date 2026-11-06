"""Criblage (06/11) : passe TOUS les champs connus au crible d'un coup, au lieu de les essayer un par un à la main.

Pour chaque signal d'univers.jsonl, le banc réaliste simule la même sortie (par défaut stop −25 %, objectif +40 %,
4 h ; bougie suivante, rugs, glissement, coût mesuré par le test réel). Puis, pour chaque champ, les signaux de la
partie ANCIENNE sont coupés en 5 tranches (quintiles) ; le meilleur côté (≥ 4e quintile ou ≤ 1er) est choisi sur
l'ancien, puis vérifié sur la partie RÉCENTE qu'il n'a pas vue. Un champ n'est retenu que si son côté choisi passe le
seuil des essais multiples sur l'ancien ET reste positif sur le récent.

Usage : python3 criblage.py /tmp/d [--sortie sortie.json] [--test-heures 24] [--delai 6] [--essais N]
        [--champs a,b,...] [--depuis 2026-11-06T12:00] [--composes composes.json]
--composes : liste au format de entree.composes d'une règle, pour cribler aussi ses champs composés.
Ce qui en sort est une piste, pas une preuve : elle doit ensuite passer au banc puis au tournoi."""
import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # outils voisins (criblage…), même sous python3 -I
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import apprend as A  # noqa: E402
import banc  # noqa: E402

FENETRES = ("m5", "m15", "m30", "h1", "h6", "h24")


def champs_connus():
    out = [c for c in A.CHAMPS if not c.endswith(".")]
    out += [f"volume.{f}" for f in ("m5", "h1", "h6", "h24")]
    out += [f"variation_prix_pct.{f}" for f in ("m5", "h1", "h6", "h24")]
    out += [f"transactions.{f}.{k}" for f in FENETRES for k in ("buys", "sells", "buyers", "sellers")]
    return out


def moy_t(xs):
    if len(xs) < 2:
        return (xs[0] if xs else None), 0.0
    m = sum(xs) / len(xs)
    sd = (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5
    return m, (m / (sd / len(xs) ** 0.5) if sd > 0 else 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--sortie", help="fichier JSON {\"stop\":..,\"objectif\":..,\"suiveur\":..,\"duree_max_h\":..}")
    ap.add_argument("--test-heures", type=float, default=24)
    ap.add_argument("--delai", type=float, default=6, help="heures avant de recompter le même token (2 à 48)")
    ap.add_argument("--essais", type=int, default=0, help="essais déjà faits pendant ce passage")
    ap.add_argument("--champs", default="")
    ap.add_argument("--composes", default=None)
    ap.add_argument("--depuis", default=None)
    ap.add_argument("--min", type=int, default=15, help="signaux minimum par côté")
    a = ap.parse_args()
    sortie = json.loads(Path(a.sortie).read_text()) if a.sortie else {"stop": -0.25, "objectif": 0.4, "duree_max_h": 4}
    composes = json.loads(Path(a.composes).read_text()) if a.composes else []
    rule = A.regle_ia({"entree": {"conditions": [], "composes": composes}, "sortie": sortie, "delai_rachat_h": a.delai})
    if rule is None:
        sys.exit("sortie ou composés invalides")
    rows, paths, rugs = banc.donnees(Path(a.data), a.depuis)
    tr = banc.simule(rule, rows, paths, rugs, avec_ligne=True)
    if len(tr) < 4 * a.min:
        sys.exit(f"trop peu de trades simulés ({len(tr)})")
    split = max(t for t, *_ in tr) - a.test_heures * 3600
    champs = [c for c in a.champs.split(",") if c] or champs_connus() + [c["nom"] for c in rule["composes"]]
    seuil = max(2.0, math.sqrt(2 * math.log(max(2, 2 * len(champs) + a.essais))))
    base_old = [x for t, x, *_ in tr if t < split]
    base_new = [x for t, x, *_ in tr if t >= split]
    print(f"{len(tr)} trades simulés (ancien {len(base_old)}, récent {len(base_new)}) ; sans filtre : ancien "
          f"{moy_t(base_old)[0]:+.1%}, récent {moy_t(base_new)[0] if base_new else float('nan'):+.1%} ; "
          f"{len(champs)} champs, seuil t {seuil:.2f}")
    res = []
    for c in champs:
        pts = []
        for t, x, _, _, r in tr:
            v = A.champ(A.avec_composes(rule, r), c)
            if v is not None:
                pts.append((t, v, x))
        old = sorted((v, x) for t, v, x in pts if t < split)
        if len(old) < 5 * a.min:
            continue
        q1, q4 = old[len(old) // 5][0], old[4 * len(old) // 5][0]
        cotes = [(">=", q4), ("<=", q1)]
        best = None
        for op, val in cotes:
            sel = [x for v, x in old if A.OPS[op](v, val)]
            if len(sel) < a.min:
                continue
            m, tt = moy_t(sel)
            if best is None or m > best[2]:
                best = (op, val, m, tt, len(sel))
        if not best:
            continue
        op, val, m_old, t_old, n_old = best
        new = [x for t, v, x in pts if t >= split and A.OPS[op](v, val)]
        m_new, t_new = moy_t(new)
        ok = t_old >= seuil and m_new is not None and m_new > 0 and len(new) >= 5
        res.append((ok, m_new if m_new is not None else -9, c, op, val, m_old, t_old, n_old, m_new, len(new)))
    res.sort(key=lambda x: (not x[0], -x[1]))
    print(f"\n{'champ':34} côté          ancien (n, moy, t)        récent (n, moy)")
    for ok, _, c, op, val, m_old, t_old, n_old, m_new, n_new in res[:40]:
        mn = "—" if m_new is None else f"{m_new:+.1%}"
        print(f"{'RETENU ' if ok else '       '}{c:27} {op} {val:<10.4g} n={n_old:4d} {m_old:+7.1%} t={t_old:+5.2f}   "
              f"n={n_new:4d} {mn:>7}")
    gard = [x for x in res if x[0]]
    if gard:
        print("\nconditions candidates (à passer au banc avec --essais, puis au tournoi) :")
        for _, _, c, op, val, *_ in gard[:5]:
            print(json.dumps({"champ": c, "op": op, "val": round(val, 6)}, ensure_ascii=False))
    else:
        print("\naucun champ ne passe seul : chercher des combinaisons (ajuste_score.py) ou d'autres données (demandes.md)")


if __name__ == "__main__":
    main()
