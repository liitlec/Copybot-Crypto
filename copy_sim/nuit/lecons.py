"""« Leçon du jour » (à la demande) : ce que le score et le bot auraient pu mieux faire, sur les lancements enregistrés
par le hub gRPC (data_grpc/). Lecture seule.

1. Qualité du score : appris sur les 2/3 les plus anciens, jugé sur le dernier tiers (part de runs et résultat par
   tranche de score, évolution dans le temps, critères qui pèsent le plus).
2. Bilan des trades : pumps ratés par le score (et pourquoi), pièges choisis (et pourquoi), part du pump captée à la
   sortie, sensibilité des réglages de sortie (seuil à 60 s, stop suiveur, durée max).
Tout ce qui est « meilleur réglage » ici est observé sur des données déjà vues : piste à figer puis tester, pas un résultat.
Rapport : reports/lecons.md"""
import os
import sys
import time
from collections import Counter
from pathlib import Path
from statistics import mean

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
os.environ["TZ"] = "Europe/Paris"  # heures du rapport en heure de Paris
time.tzset()
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
import scalp_score as S  # noqa: E402
from copysim.scalpgrpc import (BASE_COST, SIZE, entry_state, evaluate_c, sol_for, tokens_for)  # noqa: E402

TOP_Q = 0.8  # « sélection » = 20 % meilleurs scores de l'apprentissage (comme la règle D)


def pct(x):
    return "—" if x is None else f"{x:+.1%}"


def best_possible(c, rs, entry_s=5.0, max_s=540.0):
    """Meilleur rendement atteignable (revente au plus haut) entre l'entrée et max_s."""
    t_in = c["bt"] + entry_s
    v_in = entry_state(c, rs, t_in)
    tok = tokens_for(v_in, SIZE)
    vals = [(sol_for(r["v_tok"], tok) - BASE_COST) / (SIZE + BASE_COST) - 1 for r in rs if t_in < r["bt"] <= t_in + max_s]
    return max(vals) if vals else (sol_for(v_in, tok) - BASE_COST) / (SIZE + BASE_COST) - 1


def main():
    t0 = time.time()
    L, enrich = S.load()
    # lancements enrichis ET achetables (le bundle du créateur dans le slot de création exclut l'achat)
    rows = [r for r in S.build(L, enrich) if r["enriched"] and r["ret"] is not None]
    byk = {(c["bt"], c["mint"]): (c, rs) for c, rs in L}
    md = [f"# Leçon du jour — {time.strftime('%d/%m %H:%M')}", ""]
    if len(rows) < 600:
        md.append(f"Pas assez de lancements enrichis et terminés ({len(rows)}) : il en faut au moins 600.")
        return "\n".join(md)
    h0, h1 = rows[0]["bt"], rows[-1]["bt"]
    cut = len(rows) * 2 // 3
    train, test = rows[:cut], rows[cut:]
    sc = S.Scorecard().fit(train)
    tr_scores = sorted(sc.score(r["f"]) for r in train)
    thr = tr_scores[int(TOP_Q * (len(tr_scores) - 1))]
    for r in test:
        r["score"] = sc.score(r["f"])
        r["sel"] = r["score"] >= thr
    md += [f"{len(rows)} lancements enrichis, achetables et terminés, de {time.strftime('%H:%M', time.localtime(h0))} à "
           f"{time.strftime('%H:%M', time.localtime(h1))}. Score appris sur les {len(train)} premiers, jugé sur les "
           f"{len(test)} suivants (jamais vus). Run = prix ×2 en 10 min après la décision (+5 s).", ""]

    # ---------------------------------------------------------------- 1. qualité du score
    md += ["## 1. Qualité du score", "", "| tranche de score (test) | lancements | runs | résultat à 60 s |",
           "|---|---|---|---|"]
    srt = sorted(test, key=lambda r: -r["score"])
    n = len(srt)
    for a, b, lab in ((0, .1, "10 % meilleurs"), (.1, .2, "10-20 %"), (.2, .5, "20-50 %"), (.5, .8, "50-80 %"),
                      (.8, 1.0, "20 % pires")):
        part = srt[int(a * n):int(b * n)]
        rets = [r["ret"] for r in part if r["ret"] is not None]
        md.append(f"| {lab} | {len(part)} | {sum(r['run'] for r in part) / max(len(part), 1):.0%} | "
                  f"{pct(mean(rets)) if rets else '—'} |")
    base = sum(r["run"] for r in test) / len(test)
    md += ["", f"Sans score : {base:.0%} de runs. Évolution dans le temps (test coupé en 3) :", ""]
    for i in range(3):
        part = test[i * len(test) // 3:(i + 1) * len(test) // 3]
        sel = [r for r in part if r["sel"]]
        md.append(f"- {time.strftime('%H:%M', time.localtime(part[0]['bt']))} : runs {sum(r['run'] for r in sel) / max(len(sel), 1):.0%} "
                  f"chez les sélectionnés ({len(sel)}) contre {sum(r['run'] for r in part) / len(part):.0%} pour tous")
    spread = sorted(((max(t.values()) - min(t.values()), k) for k, (_, t) in sc.tables.items() if t), reverse=True)
    md += ["", "Critères qui pèsent le plus : " + ", ".join(f"{k} ({d:.1f})" for d, k in spread[:8]), ""]

    # ---------------------------------------------------------------- 2. pumps ratés / pièges
    missed = [r for r in test if r["run"] and not r["sel"]]
    caught = [r for r in test if r["run"] and r["sel"]]
    traps = [r for r in test if r["sel"] and r["ret"] is not None and r["ret"] < -0.15]

    def blame(group, worst=True):
        c = Counter()
        for r in group:
            pts = sc.points(r["f"])
            k = min(pts, key=pts.get) if worst else max(pts, key=pts.get)
            c[k] += 1
        return ", ".join(f"{k} ({v})" for k, v in c.most_common(4)) or "—"

    md += ["## 2. Bilan des choix", "",
           f"- **Pumps captés** par la sélection : {len(caught)} ; **pumps ratés** : {len(missed)} "
           f"(sur {len(caught) + len(missed)} runs du test).",
           f"- Ce qui a fait rater les pumps (critère le plus pénalisant) : {blame(missed, True)}.",
           f"- **Pièges choisis** (sélectionnés, ≤ −15 % à 60 s) : {len(traps)} sur {sum(r['sel'] for r in test)} "
           f"sélectionnés ; ce qui les a fait choisir : {blame(traps, False)}.", ""]

    # ---------------------------------------------------------------- 3. sortie
    sel = [r for r in test if r["sel"]]
    md += ["## 3. La sortie", ""]
    cap = []
    for r in sel:
        c, rs = byk[(r["bt"], r["mint"])]
        bp = best_possible(c, rs)
        xc = evaluate_c(c, rs, 5.0, 1e9, 60.0, 0.20, 0.30, 540.0)
        if xc is not None and bp > 0.5:
            cap.append((bp, xc, r["ret"]))
    if cap:
        md += [f"Sur les {len(cap)} sélectionnés qui ont atteint au moins +50 % : meilleur possible moyen "
               f"{pct(mean(b for b, _, _ in cap))}, sortie C {pct(mean(x for _, x, _ in cap))}, revente à 60 s "
               f"{pct(mean(y for *_, y in cap if y is not None))}.", ""]
    md += ["Réglages de sortie (sélectionnés du test, entrée +5 s) — **observé, pas validé** :", "",
           "| à 60 s, garder si ≥ | stop suiveur | durée max | résultat moyen | total SOL |", "|---|---|---|---|---|"]
    grid = []
    for keep in (0.10, 0.20, 0.30):
        for trail in (0.20, 0.30, 0.40):
            for mx in (180.0, 360.0, 540.0):
                xs = []
                for r in sel:
                    c, rs = byk[(r["bt"], r["mint"])]
                    x = evaluate_c(c, rs, 5.0, 1e9, 60.0, keep, trail, mx)
                    if x is not None:
                        xs.append(x)
                if xs:
                    grid.append((mean(xs), keep, trail, mx, sum(xs) * SIZE))
    grid.sort(reverse=True)
    for m, keep, trail, mx, tot in grid[:5] + [g for g in grid if (g[1], g[2], g[3]) == (0.2, 0.3, 540.0)]:
        tag = " ← règle actuelle (C / D)" if (keep, trail, mx) == (0.2, 0.3, 540.0) else ""
        md.append(f"| +{keep:.0%} | −{trail:.0%} | {mx / 60:.0f} min | {pct(m)} | {tot:+.3f}{tag} |")
    md += ["", f"_Calcul {time.time() - t0:.0f} s. Toute amélioration repérée ici doit être figée dans une nouvelle "
           "règle puis jugée sur des lancements futurs._", ""]
    return "\n".join(md)


if __name__ == "__main__":
    out = main()
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "lecons.md").write_text(out, encoding="utf-8")
    print(out)
