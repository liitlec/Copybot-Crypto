"""Score de qualité des lancements pump.fun, calculé AU MOMENT DE DÉCIDER (+DECIDE_S après la création).

Ingrédients (tous connus à l'instant de décision, rien de l'avenir) :
- flux des premières secondes : acheteurs distincts, SOL achetés / vendus, plus gros achat, bundle du créateur…
- métadonnées (hub/pump_enrich.jsonl) : compte X, Telegram, site, description, outil de lancement (hôte des métadonnées)
- créateur : nombre de transactions, âge et solde du wallet au lancement, ses lancements PRÉCÉDENTS et leur issue
- premiers acheteurs : leur historique sur les lancements déjà TERMINÉS (étaient-ils tôt sur des runs ?)
- régime : part de runs parmi les lancements terminés dans la dernière heure, rythme des créations

Cible : « run » = le prix atteint ≥ RUN_X fois le prix d'entrée dans les 10 minutes.
Modèle : grille de points (log-cotes par tranche de chaque caractéristique, lissées), apprise sur le passé.
Validation chronologique : on apprend sur les blocs 1..k−1 et on teste sur le bloc k ; jugement en SOL
(achat 0.1 SOL à la décision, revente à HOLD_S), seuil de score choisi sur l'apprentissage uniquement."""
import json
import math
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, pstdev

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import scalp as s  # noqa: E402
import scalp_regle as R  # noqa: E402

DECIDE_S = 5.0
HOLD_S = 60.0
RUN_X = 2.0
EARLY_S = 10.0  # « premier acheteur » = achat dans les 10 premières secondes d'un lancement
FOLDS = 4


def price_mult(v_in, v):
    return (v_in / v) ** 2  # prix ∝ K / v_tok²


# ------------------------------------------------------------------ données
def load():
    L = R.launches()
    enrich = {}
    p = ROOT / "data_grpc" / "pump_enrich.jsonl"
    if p.exists():
        for l in p.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(l)
            except ValueError:
                continue
            if "tx_err" not in r:
                enrich[r["sig"]] = r
    t_end = max(max([c["bt"]] + [r["bt"] for r in rs]) for c, rs in L)
    return [(c, rs) for c, rs in L if t_end - c["bt"] > 600 + 30], enrich


def outcome(c, rs):
    """Issue d'un lancement vue depuis la décision : multiple max sur 10 min, résultat du trade."""
    t_d = c["bt"] + DECIDE_S
    pre = [r for r in rs if r["bt"] <= t_d]
    post = [r for r in rs if t_d < r["bt"] <= c["bt"] + 600]
    if pre:
        v_in = pre[-1]["v_tok"]
    elif post:
        v_in = post[0]["v_tok"] + post[0]["curve_tok"]
    else:
        v_in = s.V_TOK0
    mx = max([price_mult(v_in, r["v_tok"]) for r in post] + [1.0])
    ret = R.evaluate(c, rs, DECIDE_S, HOLD_S, 1e9)
    return {"mult": mx, "run": mx >= RUN_X, "ret": ret}


def host(uri):
    if not uri:
        return "aucun"
    h = uri.split("/")[2] if uri.count("/") >= 2 else uri
    if "ipfs" in h:
        return "ipfs"
    return h if h in ("meta.uxento.io", "metadata.j7tracker.io", "gg.sc") else "autre"


# ------------------------------------------------------------------ variables à l'instant de décision
def build(L, enrich):
    L = sorted(L, key=lambda x: x[0]["bt"])
    outs = [outcome(c, rs) for c, rs in L]
    done_order = sorted(range(len(L)), key=lambda i: L[i][0]["bt"] + 600)  # ordre de fin d'observation
    wallet = defaultdict(lambda: [0, 0])     # wallet -> [lancements où il était tôt, dont runs]
    creator = defaultdict(lambda: [0, 0, 0.0])  # créateur -> [lancements terminés, runs, meilleur multiple]
    creator_seen = Counter()                 # lancements déjà créés (même non terminés)
    regime = []                              # (heure de fin, run)
    j = 0
    rows = []
    for i, (c, rs) in enumerate(L):
        t_d = c["bt"] + DECIDE_S
        while j < len(done_order) and L[done_order[j]][0]["bt"] + 600 <= t_d:  # historique strictement passé
            k = done_order[j]
            ck, rk = L[k]
            run = outs[k]["run"]
            for w in {r["signer"] for r in rk if r["kind"] == "buy" and r["bt"] <= ck["bt"] + EARLY_S}:
                wallet[w][0] += 1
                wallet[w][1] += run
            cr = creator[ck["signer"]]
            cr[0] += 1
            cr[1] += run
            cr[2] = max(cr[2], outs[k]["mult"])
            regime.append((ck["bt"] + 600, run))
            j += 1
        pre = [r for r in rs if r["bt"] <= t_d]
        buys = [r for r in pre if r["kind"] == "buy" and r["signer"] != c["signer"]]
        sells = [r for r in pre if r["kind"] == "sell"]
        after = [r for r in rs if r["bt"] > t_d]
        v_in = pre[-1]["v_tok"] if pre else (after[0]["v_tok"] + after[0]["curve_tok"] if after else s.V_TOK0)
        e = enrich.get(c["sig"], {})
        m = e.get("meta") or {}
        cs = e.get("creator_state") or {}
        bq = [wallet[r["signer"]] for r in buys]
        smooth = [(w[1] + 0.2) / (w[0] + 2.0) for w in bq]  # taux de runs lissé (prior ~10 %)
        last_h = [run for t, run in regime if t > t_d - 3600]
        cr = creator[c["signer"]]
        f = {
            "acheteurs distincts": len({r["signer"] for r in buys}),
            "SOL achetés": sum(r["sol"] for r in buys),
            "plus gros achat": max([r["sol"] for r in buys] + [0.0]),
            "ventes avant décision": len(sells),
            "SOL vendus": -sum(r["sol"] for r in sells),
            "SOL dans la courbe": s.K / v_in - s.V_SOL0,
            "achats dans le slot de création": sum(1 for r in rs if r["slot"] == c["slot"] and r["kind"] == "buy"),
            "achat du créateur": max(-c.get("signer_sol", 0.0) - R.CREATE_RENT, 0.0),
            "créateur a vendu": float(any(r["kind"] == "sell" and r["signer"] == c["signer"] for r in pre)),
            "compte X": float(bool(m.get("twitter"))) if m.get("ok") else -1.0,
            "Telegram": float(bool(m.get("telegram"))) if m.get("ok") else -1.0,
            "site": float(bool(m.get("website"))) if m.get("ok") else -1.0,
            "longueur description": float(m.get("desc_len", -1)) if m.get("ok") else -1.0,
            "outil de lancement": host(e.get("uri")) if e else "inconnu",
            "transactions du créateur": float(cs.get("n_tx", -1)),
            "âge du wallet créateur (h)": float(cs["age_h"]) if cs.get("age_h") is not None else (1e4 if cs.get("n_tx") == 1000 else -1.0),
            "solde du créateur": float(cs.get("sol", -1)),
            "lancements passés du créateur": float(creator_seen[c["signer"]]),
            "runs passés du créateur": float(cr[1]),
            "meilleur acheteur précoce (taux de runs)": max(smooth + [0.0]),
            "acheteurs précoces expérimentés": float(sum(1 for w in bq if w[0] >= 3)),
            "runs passés des acheteurs précoces": float(sum(w[1] for w in bq)),
            "part de runs dernière heure": (sum(last_h) / len(last_h)) if len(last_h) >= 20 else -1.0,
            "créations dernière heure": float(len(last_h)),
        }
        creator_seen[c["signer"]] += 1
        rows.append({"bt": c["bt"], "mint": c["mint"], "f": f, "enriched": bool(e), **outs[i]})
    return rows


# ------------------------------------------------------------------ grille de points
class Scorecard:
    def __init__(self, bins=5, alpha=2.0):
        self.bins, self.alpha = bins, alpha

    def fit(self, rows):
        y = [r["run"] for r in rows]
        p0 = (sum(y) + 1) / (len(y) + 2)
        self.base = math.log(p0 / (1 - p0))
        self.tables = {}
        for k in rows[0]["f"]:
            vals = [r["f"][k] for r in rows]
            if isinstance(vals[0], str):
                cuts = None
                keyf = lambda v: v
            else:
                uniq = sorted(set(vals))
                if len(uniq) <= self.bins:
                    cuts = uniq
                else:
                    srt = sorted(vals)
                    cuts = sorted({srt[int(q * (len(srt) - 1))] for q in [b / self.bins for b in range(1, self.bins)]})
                keyf = (lambda v, cuts=cuts: sum(v > x for x in cuts)) if cuts and len(uniq) > self.bins else (lambda v: v)
            cnt = defaultdict(lambda: [0, 0])
            for v, t in zip(vals, y):
                cnt[keyf(v)][0] += 1
                cnt[keyf(v)][1] += t
            tab = {}
            for b, (n, pos) in cnt.items():
                p = (pos + self.alpha * p0) / (n + self.alpha)
                tab[b] = math.log(p / (1 - p)) - self.base
            self.tables[k] = (keyf, tab)
        return self

    def points(self, f):
        return {k: tab.get(keyf(f[k]), 0.0) for k, (keyf, tab) in self.tables.items()}

    def score(self, f):
        return sum(self.points(f).values())


def money(sel):
    r = [x["ret"] for x in sel if x["ret"] is not None]
    if not r:
        return None
    srt = sorted(r, reverse=True)
    return {"n": len(r), "moy": mean(r), "se": pstdev(r) / len(r) ** .5 if len(r) > 1 else 0.0,
            "sans3": mean(srt[3:]) if len(srt) > 3 else 0.0, "gagn": sum(x > 0 for x in r) / len(r), "sol": sum(r) * s.SIZE}


if __name__ == "__main__":
    t0 = time.time()
    L, enrich = load()
    rows = build(L, enrich)
    if "--tous" not in sys.argv:  # évaluation sur les lancements avec métadonnées + créateur
        rows = [r for r in rows if r["enriched"]]
    if not rows:
        sys.exit("aucun lancement enrichi terminé pour l'instant")
    print(f"{len(rows)} lancements enrichis et terminés ({(rows[-1]['bt'] - rows[0]['bt']) / 3600:.1f} h), "
          f"runs ≥ {RUN_X}× : {sum(r['run'] for r in rows) / len(rows):.1%} ; calcul {time.time() - t0:.0f} s\n")
    if len(rows) < 400:
        sys.exit("pas encore assez de lancements enrichis pour une validation honnête (il en faut plusieurs milliers)")
    size = len(rows) // FOLDS
    allsel, allbase = [], []

    def rolling_select(sc, seq, q, window=500):
        """Garde un lancement si son score est dans les (1 − q) meilleurs des `window` lancements PRÉCÉDENTS :
        seuil glissant calculable en direct (l'historique des wallets grossit, les scores montent avec le temps)."""
        out, hist = [], []
        for r in seq:
            sco = sc.score(r["f"])
            if len(hist) >= 100:
                srt = sorted(hist[-window:])
                if sco >= srt[int(q * (len(srt) - 1))]:
                    out.append(r)
            hist.append(sco)
        return out

    for k in range(1, FOLDS):
        train, test = rows[:k * size], rows[k * size:(k + 1) * size]
        sc = Scorecard().fit(train)
        best = None
        for q in (0.5, 0.7, 0.8, 0.9, 0.95):  # sévérité choisie sur l'apprentissage seulement
            m = money(rolling_select(sc, train, q))
            if m and m["n"] >= 30 and (best is None or m["moy"] > best[0]):
                best = (m["moy"], q)
        _, q = best
        sel = rolling_select(sc, rows[max(0, k * size - 500):(k + 1) * size], q)
        sel = [r for r in sel if r["bt"] >= test[0]["bt"]]
        mt, mb = money(sel), money(test)
        allsel += sel
        allbase += test
        runs_sel = sum(r["run"] for r in sel) / max(len(sel), 1)
        runs_all = sum(r["run"] for r in test) / len(test)
        print(f"bloc {k + 1} : appris sur {len(train)}, testé sur {len(test)} | seuil = meilleurs {1 - q:.0%} des scores | "
              f"runs {runs_sel:.0%} (vs {runs_all:.0%} sans score) | sélection : {mt['n']} trades, {mt['moy']:+.2%} ± {mt['se']:.2%}, "
              f"sans les 3 meilleurs {mt['sans3']:+.2%}, {mt['sol']:+.2f} SOL | tout acheter : {mb['moy']:+.2%}" if mt else f"bloc {k + 1} : rien de sélectionné")
    m, b = money(allsel), money(allbase)
    if m:
        print(f"\nTOTAL hors apprentissage : {m['n']} trades sélectionnés, {m['moy']:+.2%} ± {m['se']:.2%} par trade, "
              f"sans les 3 meilleurs {m['sans3']:+.2%}, gagnants {m['gagn']:.0%}, {m['sol']:+.2f} SOL "
              f"(tout acheter : {b['moy']:+.2%}, {b['sol']:+.2f} SOL)")
    sc = Scorecard().fit(rows[:3 * size])
    print("\nce qui pèse le plus dans le score (écart de points entre la meilleure et la pire tranche, appris sur 3/4) :")
    spread = sorted(((max(t.values()) - min(t.values()), k) for k, (_, t) in sc.tables.items() if t), reverse=True)
    for d, k in spread[:12]:
        print(f"  {k:42} {d:5.2f}")
