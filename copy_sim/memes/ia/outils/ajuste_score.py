"""Ajuste un score pondéré (06/11) : régression ridge du résultat simulé de chaque signal sur quelques champs, apprise
sur la partie ANCIENNE seulement, puis jugée sur la partie RÉCENTE. Sort directement le bloc « score » à mettre dans
entree.score d'une règle (poids × champ, ou × log10(1 + champ), comparé à un seuil).

Le seuil est choisi sur l'ancien pour ne garder que la meilleure part (--part, 20 % par défaut) des signaux.
Le résultat de chaque signal est borné à [−100 %, +300 %] pour qu'un seul gros trade ne fasse pas le modèle.

Usage : python3 ajuste_score.py /tmp/d --champs rotation_h1,log:liquidite,c_flux [--composes c.json]
        [--sortie sortie.json] [--test-heures 24] [--part 0.2] [--ridge 1.0] [--delai 6] [--essais N]
« log:champ » : le champ entre en log10(1 + champ), comme dans le score de la règle.
Ici le score filtre le premier signal de chaque token ; dans une règle, il filtre avant (un token qui ne passe pas
peut passer plus tard). Les chiffres diffèrent donc un peu : c'est toujours le banc qui juge le bloc obtenu."""
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
from criblage import moy_t  # noqa: E402


def resout(m, v):
    """Système linéaire m x = v (élimination de Gauss avec pivot partiel)."""
    n = len(v)
    a = [row[:] + [v[i]] for i, row in enumerate(m)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(a[r][c]))
        a[c], a[p] = a[p], a[c]
        if abs(a[c][c]) < 1e-12:
            return None
        for r in range(n):
            if r != c:
                f = a[r][c] / a[c][c]
                a[r] = [x - f * y for x, y in zip(a[r], a[c])]
    return [a[i][n] / a[i][i] for i in range(n)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--champs", required=True)
    ap.add_argument("--composes", default=None)
    ap.add_argument("--sortie", default=None)
    ap.add_argument("--test-heures", type=float, default=24)
    ap.add_argument("--part", type=float, default=0.2)
    ap.add_argument("--ridge", type=float, default=1.0)
    ap.add_argument("--delai", type=float, default=6)
    ap.add_argument("--essais", type=int, default=0)
    ap.add_argument("--depuis", default=None)
    a = ap.parse_args()
    termes = []
    for c in a.champs.split(","):
        c = c.strip()
        if c:
            termes.append({"champ": c[4:], "log": True} if c.startswith("log:") else {"champ": c, "log": False})
    if not 0 < len(termes) <= A.TERMES_MAX:
        sys.exit(f"1 à {A.TERMES_MAX} champs")
    sortie = json.loads(Path(a.sortie).read_text()) if a.sortie else {"stop": -0.25, "objectif": 0.4, "duree_max_h": 4}
    composes = json.loads(Path(a.composes).read_text()) if a.composes else []
    rule = A.regle_ia({"entree": {"conditions": [], "composes": composes}, "sortie": sortie, "delai_rachat_h": a.delai})
    if rule is None:
        sys.exit("sortie ou composés invalides")
    rows, paths, rugs = banc.donnees(Path(a.data), a.depuis)
    tr = banc.simule(rule, rows, paths, rugs, avec_ligne=True)
    split = max(t for t, *_ in tr) - a.test_heures * 3600
    pts = []
    for t, x, _, _, r in tr:
        rr = A.avec_composes(rule, r)
        v = []
        for te in termes:
            z = A.champ(rr, te["champ"])
            if z is None:
                break
            v.append(math.log10(1 + max(z, 0.0)) if te["log"] else float(z))
        else:
            pts.append((t, v, max(-1.0, min(3.0, x)), x))
    old = [p for p in pts if p[0] < split]
    new = [p for p in pts if p[0] >= split]
    k = len(termes)
    if len(old) < 10 * k:
        sys.exit(f"trop peu de signaux complets sur l'ancien ({len(old)} pour {k} champs)")
    mu = [sum(p[1][j] for p in old) / len(old) for j in range(k)]
    sd = [max((sum((p[1][j] - mu[j]) ** 2 for p in old) / len(old)) ** 0.5, 1e-12) for j in range(k)]
    z = [[(p[1][j] - mu[j]) / sd[j] for j in range(k)] for p in old]
    y = [p[2] for p in old]
    ym = sum(y) / len(y)
    xtx = [[sum(r[i] * r[j] for r in z) + (a.ridge * len(z) / 100 if i == j else 0) for j in range(k)] for i in range(k)]
    xty = [sum(r[i] * (yy - ym) for r, yy in zip(z, y)) for i in range(k)]
    beta = resout(xtx, xty)
    if beta is None:
        sys.exit("champs trop liés entre eux : en retirer un")
    poids = [b / s for b, s in zip(beta, sd)]
    score = lambda v: sum(w * x for w, x in zip(poids, v))  # noqa: E731
    s_old = sorted((score(p[1]) for p in old), reverse=True)
    seuil = s_old[max(0, int(len(s_old) * a.part) - 1)]
    sel_old = [p[3] for p in old if score(p[1]) >= seuil]
    sel_new = [p[3] for p in new if score(p[1]) >= seuil]
    m_o, t_o = moy_t(sel_old)
    m_n, t_n = moy_t(sel_new)
    n_ess = max(2, a.essais + 1)
    seuil_t = max(2.0, math.sqrt(2 * math.log(n_ess)))
    print(f"{len(pts)} signaux complets (ancien {len(old)}, récent {len(new)})")
    print(f"tous : ancien {moy_t([p[3] for p in old])[0]:+.1%}, récent "
          f"{(moy_t([p[3] for p in new])[0] or float('nan')):+.1%}")
    print(f"meilleurs {a.part:.0%} selon le score : ancien n={len(sel_old)} {m_o:+.1%} t={t_o:.2f} (appris dessus, optimiste) ; "
          f"récent n={len(sel_new)} {(m_n if m_n is not None else float('nan')):+.1%} t={t_n:.2f}  <- le chiffre qui compte")
    print(f"seuil des essais multiples : t ≥ {seuil_t:.2f} sur le récent ; "
          + ("PASSE" if m_n is not None and t_n >= seuil_t else "ne passe pas (pas assez de preuve)"))
    bloc = {"termes": [{"champ": te["champ"], "poids": round(w, 8), "log": te["log"]} for te, w in zip(termes, poids)],
            "seuil": round(seuil, 8)}
    print("\nbloc à mettre dans entree.score (puis banc, puis tournoi) :")
    print(json.dumps(bloc, ensure_ascii=False))


if __name__ == "__main__":
    main()
