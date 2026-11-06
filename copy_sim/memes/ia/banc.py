"""Banc d'essai de l'IA chercheuse : rejoue une règle au format memes/ia/regle.json sur les données du VPS, avec la
même entrée, la même sortie (vérifiée sur la clôture de chaque bougie de 5 min, comme le VPS) et les mêmes frais.

Mode réaliste (par défaut depuis le 02/11, parce que le banc annonçait +27 % par trade quand la caisse réelle
perdait −4 %) :
- achat à la clôture de la bougie suivante (au moins 5 min après le signal), pas au prix exact du signal ;
- rugs : un pool qui a été vidé ou s'est effondré d'au moins 80 % pendant un trade réel (trades.jsonl, toutes
  caisses) compte −95 % pour tout trade simulé encore ouvert à ce moment-là, même si ses bougies n'en gardent pas
  la trace ; les pics isolés aberrants (×5 puis retour) sont retirés des bougies ;
- coûts pessimistes : frais et impact habituels + 2 % de glissement par côté + frais Solana/Jito (0,1 %).
Le mode optimiste d'avant reste affiché à côté (--optimiste pour ne voir que lui).

Usage : python3 banc.py DOSSIER_DONNEES regle.json [regle2.json ...] [--test-heures 24]
DOSSIER_DONNEES doit contenir univers.jsonl et ohlcv/<pool>.json (copiés depuis http://140.82.38.41:8787/).
Affiche, pour chaque règle : nombre de trades, moyenne nette, borne basse (moyenne − 2 marges d'erreur), part de
gagnants, sur la période ancienne et sur les dernières heures (test), puis jour par jour."""
import argparse
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import apprend as A  # noqa: E402


GLISSEMENT, FRAIS_RESEAU, PERTE_RUG = 0.02, 0.001, -0.95


def nettoie(c):
    """Retire les bougies aberrantes : pics isolés (×5 ou ÷5 par rapport à deux voisines qui s'accordent) et toute
    hausse de plus de ×20 d'une bougie à l'autre (erreur de données ; les chutes brutales, elles, sont gardées :
    ce sont souvent de vrais rugs)."""
    out = []
    for i, (ts, px) in enumerate(c):
        if not px or px <= 0:
            continue
        if 0 < i < len(c) - 1:
            a, b = c[i - 1][1], c[i + 1][1]
            if a and b and 0.5 < a / b < 2 and (px > 5 * max(a, b) or px < min(a, b) / 5):
                continue
        if out and px > 20 * out[-1][1]:
            continue
        out.append((ts, px))
    return out


def rugs_connus(d):
    """Pool -> premier instant où un trade réel l'a vu vidé ou effondré d'au moins 80 %, confirmé par les bougies
    (voir apprend.rugs_connus : depuis le 04/11, les faux « pools vidés » ne comptent plus)."""
    return A.rugs_connus(d / "trades.jsonl", d / "ohlcv")


def simule(rule, rows, paths, rugs=None, realiste=True):
    out, last = [], {}
    rugs = rugs or {}
    for r in rows:
        if r["t"] - last.get(r["token"], -1e18) < rule.get("delai_rachat_h", 24) * 3600 or not A.entre_ia(rule, r):
            continue
        c = nettoie([(ts, px) for ts, px in paths.get(r["pool"], []) if ts > r["t"]])
        if realiste:
            c = [x for x in c if x[0] >= r["t"] + 300]  # achat à la bougie suivante
        if not c:
            continue
        last[r["token"]] = r["t"]
        t0, p0 = (c[0][0], c[0][1]) if realiste else (r["t"], r["prix"])
        pic, x, why, t_fin = 0.0, 0.0, None, c[-1][0]
        for ts, px in c[1:] if realiste else c:
            x = px / p0 - 1
            pic = max(pic, x)
            why = A.sortir_ia(rule, x, pic, (ts - t0) / 3600, False)
            if why:
                t_fin = ts
                break
        fin_prevue = t0 + rule["duree_max_h"] * 3600
        t_rug = rugs.get(r["pool"])
        rug = realiste and t_rug is not None and t0 <= t_rug <= (t_fin if why else fin_prevue)
        if rug:
            x = PERTE_RUG
        elif not why and (c[-1][0] - t0) / 3600 < rule["duree_max_h"]:
            continue  # trade pas encore terminé
        cout = A.couts(r.get("liquidite")) + ((2 * GLISSEMENT + 2 * FRAIS_RESEAU) if realiste else 0)
        out.append((r["t"], x - cout, r["token"], rug))
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
    ap.add_argument("--optimiste", action="store_true", help="seulement l'ancien mode (prix du signal, sans rugs ni glissement)")
    ap.add_argument("--depuis", default=None,
                    help="ne garder que les signaux après cette date (AAAA-MM-JJTHH:MM, heure UTC, ou secondes Unix) : "
                         "test vraiment hors échantillon d'une règle écrite à cette date")
    ap.add_argument("--avec-interdits", action="store_true", help="garder XTEN et PREDICT (exclus par défaut)")
    ap.add_argument("--essais", type=int, default=0,
                    help="nombre total de variantes testées pendant ce passage (toi et tes agents) : relève le seuil")
    a = ap.parse_args()
    d = Path(a.data)
    rows = A.charger(d / "univers.jsonl", 0)
    if not a.avec_interdits:  # 06/11 : interdits pour toutes les caisses, donc hors du banc aussi
        rows = [r for r in rows if not A.nom_interdit(r.get("nom"))]
    if a.depuis:
        from datetime import datetime, timezone
        t_dep = float(a.depuis) if a.depuis.replace(".", "").isdigit() else \
            datetime.fromisoformat(a.depuis).replace(tzinfo=timezone.utc).timestamp()
        rows = [r for r in rows if r["t"] >= t_dep]
        print(f"hors échantillon : signaux après {datetime.fromtimestamp(t_dep, timezone.utc):%d/%m %H:%M} UTC seulement")
    paths = {}
    for f in (d / "ohlcv").glob("*.json"):
        try:  # un fichier mal téléchargé (page d'erreur, coupure) est ignoré
            paths[f.stem] = [tuple(x) for x in json.loads(f.read_text())["c"]]
        except (ValueError, KeyError, TypeError):
            continue
    now = max(r["t"] for r in rows)
    split = now - a.test_heures * 3600
    rugs = rugs_connus(d)
    print(f"{len(rows)} lignes, {len(paths)} pools avec prix, {len(rugs)} pools vidés connus, "
          f"test = dernières {a.test_heures:g} h ; mode {'optimiste' if a.optimiste else 'réaliste'}")
    for path in a.regles:
        raw = json.loads(Path(path).read_text())
        rule = A.regle_ia(raw)
        if rule is None:
            n = len((raw.get("entree") or {}).get("conditions") or [])
            print(f"\n{path} : règle invalide" + (f" ({n} conditions, {A.CONDITIONS_MAX} au plus)"
                                                 if n > A.CONDITIONS_MAX else ""))
            continue
        tr = simule(rule, rows, paths, rugs, realiste=not a.optimiste)
        old = [x for t, x, *_ in tr if t < split]
        new = [x for t, x, *_ in tr if t >= split]
        xs = [x for _, x, *_ in tr]
        srt = sorted(xs, reverse=True)
        print(f"\n{path} (v{rule['version']})\n  ancien : {resume(old)}\n  test   : {resume(new)}"
              f"\n  total  : {resume(xs)}  dont rugs={sum(1 for *_, g in tr if g)}"
              f"  sans les 3 meilleurs={(sum(srt[3:]) / len(srt[3:])) if len(srt) > 3 else float('nan'):+.1%}")
        if len(xs) > 1:  # essais multiples (04/11) : sur N variantes, la meilleure gagne souvent par hasard
            m = sum(xs) / len(xs)
            se = (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5 / len(xs) ** 0.5
            t = m / se if se > 0 else float("inf")
            n_ess = max(a.essais, len(a.regles))
            seuil = max(2.0, (2 * math.log(n_ess)) ** 0.5) if n_ess > 1 else 2.0
            print(f"  solidité : t = {t:.2f} (moyenne / marge), seuil {seuil:.2f} pour {n_ess} essais "
                  f"-> {'PASSE' if t >= seuil else 'trop faible, probablement du hasard'}")
        if not a.optimiste:
            opt = [x for _, x, *_ in simule(rule, rows, paths, realiste=False)]
            print(f"  (ancien banc optimiste, pour comparaison : {resume(opt)})")
        days = defaultdict(list)
        for t, x, *_ in tr:
            days[time.strftime("%Y-%m-%d", time.gmtime(t))].append(x)
        for k in sorted(days):
            print(f"  {k} : {resume(days[k])}")


if __name__ == "__main__":
    main()
