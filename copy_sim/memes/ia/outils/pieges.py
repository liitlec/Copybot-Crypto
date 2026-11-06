"""Détecteur de pièges (06/11) : quels champs annoncent un rug AU MOMENT DE L'ACHAT ?

Pour chaque achat possible (tous les tokens du filtre, un par token et par --delai heures), un « piège » = pool vidé
connu pendant les --horizon heures qui suivent, ou chute d'au moins --chute (80 % par défaut) sous le prix d'achat
dans ce délai. Pour chaque champ, on cherche sur la partie ANCIENNE le quintile à exclure (le plus haut ou le plus
bas) qui concentre le plus de pièges, puis on vérifie sur la partie RÉCENTE que l'exclure retire bien des pièges
sans retirer les gagnants. Résultat : des conditions « anti-piège » à ajouter à n'importe quelle règle.

Usage : python3 pieges.py /tmp/d [--horizon 24] [--chute 0.8] [--delai 6] [--test-heures 24] [--composes c.json]"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import apprend as A  # noqa: E402
import banc  # noqa: E402
from criblage import champs_connus  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--horizon", type=float, default=24)
    ap.add_argument("--chute", type=float, default=0.8)
    ap.add_argument("--delai", type=float, default=6)
    ap.add_argument("--test-heures", type=float, default=24)
    ap.add_argument("--composes", default=None)
    ap.add_argument("--depuis", default=None)
    a = ap.parse_args()
    composes = json.loads(Path(a.composes).read_text()) if a.composes else []
    rule = A.regle_ia({"entree": {"conditions": [], "composes": composes}, "delai_rachat_h": a.delai,
                       "sortie": {"stop": -0.9, "duree_max_h": a.horizon}})
    if rule is None:
        sys.exit("composés invalides")
    rows, paths, rugs = banc.donnees(Path(a.data), a.depuis)
    pts = []
    for r, c in banc.entrees(rule, rows, paths):
        t0, p0 = c[0]
        fin = t0 + a.horizon * 3600
        if c[-1][0] < fin and not (r["pool"] in rugs and t0 <= rugs[r["pool"]] <= fin):
            continue  # pas encore assez de recul
        bas = min(px for ts, px in c if ts <= fin) / p0 - 1
        piege = bas <= -a.chute or (r["pool"] in rugs and t0 <= rugs[r["pool"]] <= fin)
        pts.append((r["t"], A.avec_composes(rule, r), piege))
    if len(pts) < 50:
        sys.exit(f"trop peu d'achats avec assez de recul ({len(pts)})")
    split = max(t for t, *_ in pts) - a.test_heures * 3600
    old = [p for p in pts if p[0] < split]
    new = [p for p in pts if p[0] >= split]
    taux = lambda xs: sum(1 for x in xs if x[2]) / len(xs) if xs else float("nan")  # noqa: E731
    print(f"{len(pts)} achats possibles ; pièges : ancien {taux(old):.0%} de {len(old)}, récent {taux(new):.0%} de {len(new)}")
    res = []
    for ch in champs_connus() + [c["nom"] for c in rule["composes"]]:
        vo = sorted((A.champ(r, ch), p) for _, r, p in [(t, r, p) for t, r, p in old] if A.champ(r, ch) is not None)
        if len(vo) < 50:
            continue
        q1, q4 = vo[len(vo) // 5][0], vo[4 * len(vo) // 5][0]
        best = None
        for op_garde, val in ((">", q1), ("<", q4)):  # garder au-dessus du 1er quintile, ou sous le 4e
            exclus = [(v, p) for v, p in vo if not A.OPS[op_garde](v, val)]
            if len(exclus) < 10:
                continue
            gain = sum(1 for _, p in exclus if p) / len(exclus) - taux(old)
            if best is None or gain > best[2]:
                best = (op_garde, val, gain, len(exclus))
        if not best or best[2] <= 0:
            continue
        op_garde, val, gain, n_ex = best
        nv = [(A.champ(r, ch), p) for _, r, p in new if A.champ(r, ch) is not None]
        ex_new = [p for v, p in nv if not A.OPS[op_garde](v, val)]
        garde_new = [p for v, p in nv if A.OPS[op_garde](v, val)]
        t_ex = sum(ex_new) / len(ex_new) if ex_new else None
        t_ga = sum(garde_new) / len(garde_new) if garde_new else None
        res.append((t_ex is not None and t_ga is not None and t_ex > 2 * max(t_ga, 0.01) and len(ex_new) >= 5,
                    gain, ch, op_garde, val, n_ex, t_ex, t_ga, len(ex_new)))
    res.sort(key=lambda x: (not x[0], -x[1]))
    print(f"\n{'champ':30} garder si       ancien : pièges chez les exclus   récent : exclus / gardés")
    for ok, gain, ch, op, val, n_ex, t_ex, t_ga, n_exn in res[:30]:
        f = lambda v: "—" if v is None else f"{v:.0%}"  # noqa: E731
        print(f"{'RETENU ' if ok else '       '}{ch:23} {op} {val:<12.4g} {taux(old) + gain:.0%} (n={n_ex})"
              f"                 {f(t_ex)} (n={n_exn}) / {f(t_ga)}")
    gard = [x for x in res if x[0]]
    if gard:
        print("\nconditions anti-piège candidates (à ajouter à une règle, puis banc et tournoi) :")
        for _, _, ch, op, val, *_ in gard[:5]:
            print(json.dumps({"champ": ch, "op": op, "val": round(val, 6)}, ensure_ascii=False))
    else:
        print("\naucun champ ne sépare les pièges de façon stable sur le récent")


if __name__ == "__main__":
    main()
