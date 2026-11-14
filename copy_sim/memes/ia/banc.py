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
# coût en plus du papier par aller-retour : 2 % de glissement + 0,1 % de frais réseau par côté, remplacé par l'écart
# mesuré sur le test réel dès A.REEL_MIN ventes réelles s'il est plus élevé (06/11)
SURCOUT = [2 * GLISSEMENT + 2 * FRAIS_RESEAU]
GAIN_MAX = 10.0  # +1000 % : au-delà, le VPS tient le prix pour aberrant (05/11, Impeach et BUNNY)


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


def entrees(rule, rows, paths, realiste=True):
    """Achats d'une règle : [(ligne, bougies après l'achat)], un par token et par délai de rachat. La sortie n'y joue
    pas (le délai compte depuis le signal) : les outils peuvent donc essayer plusieurs sorties sur les mêmes achats."""
    out, last = [], {}
    for r in rows:
        if r["t"] - last.get(r["token"], -1e18) < rule.get("delai_rachat_h", 24) * 3600 or not A.entre_ia(rule, r):
            continue
        c = nettoie([(ts, px) for ts, px in paths.get(r["pool"], []) if ts > r["t"]])
        if realiste:
            c = [x for x in c if x[0] >= r["t"] + 300]  # achat à la bougie suivante
        if not c:
            continue
        last[r["token"]] = r["t"]
        out.append((r, c))
    return out


def detail(rule, r, c, rugs, realiste=True):
    """(rendement net de coûts, rug ?, heure de sortie) d'un achat avec la sortie de `rule`, ou None si le trade
    n'est pas terminé. Avec un palier (07/11) : sa part est vendue au premier relevé au-dessus de son objectif, le
    reste suit la sortie normale ; un rug après le palier ne touche que le reste."""
    t0, p0 = (c[0][0], c[0][1]) if realiste else (r["t"], r["prix"])
    pal, x_pal = rule.get("palier"), None
    pic, x, why, t_fin = 0.0, 0.0, None, c[-1][0]
    for ts, px in c[1:] if realiste else c:
        if px / p0 - 1 > GAIN_MAX:  # prix aberrant (pool vidé, bougie fausse) : ignoré, comme sur le VPS
            continue
        x = px / p0 - 1
        pic = max(pic, x)
        if pal and x_pal is None and x >= pal["objectif"]:
            x_pal = x
        why = A.sortir_ia(rule, x, pic, (ts - t0) / 3600, False)
        if why:
            t_fin = ts
            break
    fin_prevue = t0 + rule["duree_max_h"] * 3600
    t_rug = rugs.get(r["pool"])
    rug = realiste and t_rug is not None and t0 <= t_rug <= (t_fin if why else fin_prevue)
    if rug:
        x, t_fin = PERTE_RUG, t_rug
    elif not why and (c[-1][0] - t0) / 3600 < rule["duree_max_h"]:
        return None  # trade pas encore terminé
    if x_pal is not None:
        x = pal["part"] * x_pal + (1 - pal["part"]) * x
    return x - (A.couts(r.get("liquidite")) + (SURCOUT[0] if realiste else 0)), rug, t_fin


def resultat(rule, r, c, rugs, realiste=True):
    """(rendement net de coûts, rug ?) d'un achat avec la sortie de `rule`, ou None si le trade n'est pas terminé."""
    d = detail(rule, r, c, rugs, realiste)
    return None if d is None else d[:2]


def rejoue(rule, rows, paths, rugs, debut, fin=None):
    """Rejoue une règle comme le VPS la joue (07/11, demande D4) : un achat au plus par cycle (le premier selon son
    classement), au plus max_positions positions ouvertes, pas de rachat d'un token vendu depuis moins de
    delai_rachat_h heures (compté depuis la VENTE), achat au prix de la bougie suivante. Renvoie
    [(heure d'achat, token, nom, rendement ou None si pas fini, heure de sortie)]."""
    cycles = defaultdict(list)
    for r in rows:
        if r["t"] >= debut and (fin is None or r["t"] <= fin):
            cycles[r["t"]].append(r)
    ouvertes, vendus, out = {}, {}, []
    delai = rule.get("delai_rachat_h", 24) * 3600
    for t in sorted(cycles):
        for tok in [k for k, v in ouvertes.items() if v[3] is not None and v[3] <= t]:
            vendus[tok] = ouvertes.pop(tok)[3]
        if len(ouvertes) >= rule["max_positions"]:
            continue
        ok = [r for r in cycles[t] if A.entre_ia(rule, r) and r["token"] not in ouvertes
              and t - vendus.get(r["token"], -1e18) >= delai]
        ok.sort(key=lambda r: A.valeur_tri(rule, r) * (-1 if rule["tri_desc"] else 1))
        for r in ok:
            c = nettoie([(ts, px) for ts, px in paths.get(r["pool"], []) if ts >= r["t"] + 300])
            if not c:
                continue
            d = detail(rule, r, c, rugs)
            ouvertes[r["token"]] = (r["t"], r.get("nom"), None if d is None else d[0], None if d is None else d[2])
            out.append((r["t"], r["token"], r.get("nom"), None if d is None else d[0], None if d is None else d[2]))
            break
    return out


def compare_direct(d, slot, rows, paths, rugs):
    """--direct defi_N (ou ia) : rejoue la règle en place depuis son début et la compare trade par trade au direct."""
    state = json.loads((d / "state.json").read_text())
    if slot == "ia":
        rule, debut = state.get("ia"), 0
        for ln in (d / "ia_regles.jsonl").read_text().splitlines() if (d / "ia_regles.jsonl").exists() else []:
            try:
                x = json.loads(ln)
            except ValueError:
                continue
            if rule and x.get("version") == rule.get("version"):
                debut = x.get("t", 0)
    else:
        dfi = (state.get("defis") or {}).get(slot)
        if not dfi:
            sys.exit(f"{slot} : aucune règle en place")
        rule, debut = dfi["regle"], dfi["debut"]
    b = (state.get("books") or {}).get(slot) or {}
    direct = [(r["t_in"], r["token"], r.get("name"), r["ret"]) for r in b.get("closed", []) if r["t_in"] >= debut]
    direct += [(q["t"], tok, q.get("name"), None) for tok, q in (b.get("open") or {}).items() if q["t"] >= debut]
    direct.sort()
    sim = rejoue(rule, rows, paths, rugs, debut)
    print(f"{slot} : règle en place depuis {time.strftime('%d/%m %H:%M', time.gmtime(debut))} UTC ; "
          f"{len(direct)} trades en direct, {len(sim)} rejoués")
    pris = set()
    f = lambda v: "en cours" if v is None else f"{v:+.1%}"  # noqa: E731
    for t, tok, nom, ret in direct:
        m = next((i for i, x in enumerate(sim) if i not in pris and x[1] == tok and abs(x[0] - t) <= 900), None)
        if m is None:
            print(f"  {time.strftime('%d/%m %H:%M', time.gmtime(t))}  {str(nom)[:18]:18}  direct {f(ret):>8}   "
                  f"rejoué : ABSENT")
        else:
            pris.add(m)
            print(f"  {time.strftime('%d/%m %H:%M', time.gmtime(t))}  {str(nom)[:18]:18}  direct {f(ret):>8}   "
                  f"rejoué {f(sim[m][3]):>8}")
    for i, (t, tok, nom, ret, _) in enumerate(sim):
        if i not in pris:
            print(f"  {time.strftime('%d/%m %H:%M', time.gmtime(t))}  {str(nom)[:18]:18}  direct   ABSENT   "
                  f"rejoué {f(ret):>8}")
    print(f"  accord : {len(pris)} trades communs sur {len(direct)} directs et {len(sim)} rejoués. Un trade absent du"
          " rejeu vient le plus souvent d'un relevé manquant ou d'un prix différent à la seconde près (le direct"
          " vérifie la sortie toutes les secondes à 15 s, le rejeu sur des bougies de 5 min).")


def simule(rule, rows, paths, rugs=None, realiste=True, avec_ligne=False):
    out, rugs = [], rugs or {}
    for r, c in entrees(rule, rows, paths, realiste):
        res = resultat(rule, r, c, rugs, realiste)
        if res is not None:
            out.append((r["t"], res[0], r["token"], res[1], r) if avec_ligne else (r["t"], res[0], r["token"], res[1]))
    return out


def donnees(d, depuis=None, avec_interdits=False):
    """(lignes d'univers.jsonl, bougies par pool, pools vidés) comme le banc les utilise ; règle aussi le surcoût
    mesuré par le test réel. Partagé avec les outils de ia/outils/."""
    rows = A.charger(d / "univers.jsonl", 0)
    if not avec_interdits:  # 06/11 : interdits pour toutes les caisses, donc hors du banc aussi
        rows = [r for r in rows if not A.nom_interdit(r.get("nom"))]
    if depuis:
        from datetime import datetime, timezone
        t_dep = float(depuis) if str(depuis).replace(".", "").isdigit() else \
            datetime.fromisoformat(depuis).replace(tzinfo=timezone.utc).timestamp()
        rows = [r for r in rows if r["t"] >= t_dep]
        print(f"hors échantillon : signaux après {datetime.fromtimestamp(t_dep, timezone.utc):%d/%m %H:%M} UTC seulement")
    paths = {}
    for f in (d / "ohlcv").glob("*.json"):
        try:  # un fichier mal téléchargé (page d'erreur, coupure) est ignoré
            paths[f.stem] = [tuple(x) for x in json.loads(f.read_text())["c"]]
        except (ValueError, KeyError, TypeError):
            continue
    rugs = rugs_connus(d)
    # champs de fourchette (07/11) : bougies d'avant chaque relevé + relevés plus récents, comme le VPS
    propres = {pool: A.nettoie(sorted(c)) for pool, c in paths.items()}
    releves = defaultdict(list)
    for r in rows:
        for k in A.FOURCHETTES:
            r.pop(k, None)
        r.update(A.fourchettes_bougies(r["t"], r.get("prix"), propres.get(r["pool"], []), releves[r["token"]]))
        releves[r["token"]].append((r["t"], r.get("prix")))
        if len(releves[r["token"]]) > 200:
            del releves[r["token"]][:-150]
    n_reel, ec = A.ecart_reel(d / "reel.jsonl")
    if ec is not None:
        print(f"test réel : {n_reel} ventes, le papier surestime de {ec:+.1%} par aller-retour"
              + (f" ; coût du banc porté à {max(ec, SURCOUT[0]):.1%}" if n_reel >= A.REEL_MIN and ec > SURCOUT[0]
                 else f" (le banc compte {SURCOUT[0]:.1%} ; remplacé à partir de {A.REEL_MIN} ventes si plus élevé)"))
        if n_reel >= A.REEL_MIN:
            SURCOUT[0] = max(SURCOUT[0], ec)
    return rows, paths, rugs


def resume(xs):
    s = A.stats(xs)
    win = sum(x > 0 for x in xs) / len(xs) if xs else 0
    m = "—" if s["m"] is None else f"{s['m']:+.1%}"
    bas = "—" if s["bas"] is None else f"{s['bas']:+.1%}"
    return f"n={s['n']:4d}  moyenne={m:>7}  borne basse={bas:>7}  gagnants={win:.0%}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("regles", nargs="*")
    ap.add_argument("--test-heures", type=float, default=24)
    ap.add_argument("--optimiste", action="store_true", help="seulement l'ancien mode (prix du signal, sans rugs ni glissement)")
    ap.add_argument("--depuis", default=None,
                    help="ne garder que les signaux après cette date (AAAA-MM-JJTHH:MM, heure UTC, ou secondes Unix) : "
                         "test vraiment hors échantillon d'une règle écrite à cette date")
    ap.add_argument("--avec-interdits", action="store_true", help="garder XTEN et PREDICT (exclus par défaut)")
    ap.add_argument("--direct", default=None,
                    help="defi_N ou ia : rejoue la règle en place comme le VPS (un achat par cycle, positions max, "
                         "rachat compté depuis la vente) et compare trade par trade au direct (07/11)")
    ap.add_argument("--essais", type=int, default=0,
                    help="nombre total de variantes testées pendant ce passage (toi et tes agents) : relève le seuil")
    a = ap.parse_args()
    d = Path(a.data)
    rows, paths, rugs = donnees(d, a.depuis, a.avec_interdits)
    if a.direct:
        return compare_direct(d, a.direct, rows, paths, rugs)
    now = max(r["t"] for r in rows)
    split = now - a.test_heures * 3600
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
