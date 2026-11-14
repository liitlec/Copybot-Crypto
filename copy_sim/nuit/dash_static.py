"""Page de suivi simple (HTML statique, sans script ni capacité) des règles de scalp A à F, pour les téléphones dont
le navigateur ne lit pas la page interactive. Écrit reports/suivi_scalp.html à partir de data_grpc/dash_trades.json
(produit par nuit/dash_export.py). Lecture seule."""
import json
import math
import time
from collections import defaultdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PARIS = ZoneInfo("Europe/Paris")
RULES = [  # règle, description, objectif du verdict, référence sur les mêmes lancements, nom de la référence
    ("G", "F seulement pendant les vagues", 200, "F_G", "F même période"),
    ("H", "E seulement pendant les vagues", 600, "E_H", "E même période"),
    ("F", "Score + sortie E", 300, "D_F", "D"),
    ("E", "Entrée B, moitié vendue à ×2", 1000, "B_E", "B"),
    ("D", "Score + sortie C", 300, "TOUS_C", "tous, sortie C"),
    ("C", "Entrée B, gardé si ≥ +20 % à 60 s", 1000, "B_C", "B"),
    ("B", "+5 s, 1 autre acheteur, vente à 60 s", 1000, None, ""),
    ("A", "+1 s, vente à 60 s", 1000, None, ""),
]
COLORS = {"G": "var(--c7)", "H": "var(--c8)", "F": "var(--c1)", "E": "var(--c2)", "D": "var(--c3)", "C": "var(--c4)", "B": "var(--c5)", "A": "var(--c6)"}


def pct(x, sign=True):
    if x is None:
        return "—"
    s = f"{x * 100:+.1f}" if sign else f"{x * 100:.1f}"
    return s.replace(".", ",") + " %"


def sol(x):
    return f"{x:+.2f}".replace(".", ",")


def paris(iso, fmt="%H:%M"):
    return datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(PARIS).strftime(fmt)


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def stats(by):
    out = []
    for r, nom, obj, ref, ref_nom in RULES:
        xs = [x for _, x in by.get(r, [])]
        n = len(xs)
        m = mean(xs)
        se = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1)) / math.sqrt(n) if n > 1 else None
        sans = mean(sorted(xs, reverse=True)[3:])
        rxs = [x for _, x in by.get(ref, [])] if ref else []
        rm = mean(rxs) if ref else None
        tot_ok = r not in ("G", "H") or sum(xs) >= sum(rxs)  # G / H : le filtre ne doit pas coûter de gains au total
        if n < obj:
            verdict = "En cours"
        else:
            verdict = "Validé" if m > 2 * se and sans > 0 and (rm is None or m > rm) and tot_ok else "Pas validé"
        out.append({"r": r, "nom": nom, "n": n, "obj": obj, "m": m, "se": se, "win": sum(x > 0 for x in xs) / n if n else None,
                    "tot": sum(xs) * 0.1, "sans": sans, "ref": ref_nom, "rm": rm, "verdict": verdict})
    return out


def chart(by):
    W, H, ml, mr, mt, mb = 720, 300, 52, 92, 12, 28
    series = {}
    for r, *_ in RULES:
        tot, pts = 0.0, []
        for t, x in by.get(r, []):
            tot += x * 0.1
            pts.append((t, tot))
        if pts:
            series[r] = pts
    if not series:
        return "<p class='note'>Pas encore de trades.</p>"
    ts = [t for p in series.values() for t, _ in p]
    vs = [v for p in series.values() for _, v in p] + [0.0]
    t0, t1 = min(ts), max(ts)
    lo, hi = min(vs), max(vs)
    step = max(0.5, round((hi - lo) / 5 * 2) / 2)
    lo, hi = math.floor(lo / step) * step, math.ceil(hi / step) * step
    X = lambda t: ml + (t - t0) / max(t1 - t0, 1) * (W - ml - mr)  # noqa: E731
    Y = lambda v: mt + (hi - v) / max(hi - lo, 1e-9) * (H - mt - mb)  # noqa: E731
    g = []
    v = lo
    while v <= hi + 1e-9:
        g.append(f"<line x1='{ml}' x2='{W - mr}' y1='{Y(v):.1f}' y2='{Y(v):.1f}' class='{'zero' if abs(v) < 1e-9 else 'grid'}'/>"
                 f"<text x='{ml - 6}' y='{Y(v):.1f}' dy='0.32em' text-anchor='end' class='tick'>{sol(v)}</text>")
        v += step
    h = datetime.fromtimestamp(t0, PARIS).replace(minute=0, second=0) .timestamp() + 3600
    every = 3600 if t1 - t0 < 8 * 3600 else 7200
    while h < t1:
        g.append(f"<text x='{X(h):.1f}' y='{H - 8}' text-anchor='middle' class='tick'>"
                 f"{datetime.fromtimestamp(h, PARIS).strftime('%H h')}</text>")
        h += every
    ends = []
    for r, pts in series.items():
        keep = pts[:: max(1, len(pts) // 400)] + [pts[-1]]
        d = "M" + " L".join(f"{X(t):.1f},{Y(v):.1f}" for t, v in keep)
        wide = r in ("F", "E")
        g.append(f"<path d='{d}' fill='none' stroke='{COLORS[r]}' stroke-width='{2.5 if wide else 1.5}' "
                 f"stroke-linejoin='round' stroke-linecap='round' opacity='{1 if wide else 0.75}'/>")
        ends.append([Y(pts[-1][1]), r, pts[-1]])
    ends.sort()
    for i in range(1, len(ends)):
        ends[i][0] = max(ends[i][0], ends[i - 1][0] + 14)
    for y, r, (t, v) in ends:
        g.append(f"<circle cx='{X(t):.1f}' cy='{Y(v):.1f}' r='3' fill='{COLORS[r]}'/>"
                 f"<text x='{W - mr + 8}' y='{y:.1f}' dy='0.32em' class='end' fill='{COLORS[r]}'>{r} {sol(v)}</text>")
    return f"<svg viewBox='0 0 {W} {H}' width='100%' role='img' aria-label='Total cumulé par règle'>{''.join(g)}</svg>"


def main():
    rows = json.loads((ROOT / "data_grpc" / "dash_trades.json").read_text(encoding="utf-8"))
    by = defaultdict(list)
    for x in rows:
        by[x["serie"]].append((datetime.strptime(x["heure"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp(),
                               x["rendement"]))
    st = stats(by)
    main_rows = [x for x in rows if x["serie"] in COLORS]
    last = max((x["heure"] for x in main_rows), default=None)
    tiles = []
    for s in st:
        if s["r"] not in ("G", "H", "F", "E"):
            continue
        cls = {"Validé": "ok", "Pas validé": "bad"}.get(s["verdict"], "wait")
        sg = "pos" if (s["m"] or 0) > 0 else "neg"
        tiles.append(f"""<article class="tile"><div class="top"><span class="letter">{s['r']}</span>
<span class="name">{escape(s['nom'])}</span><span class="pill {cls}">{s['verdict']}</span></div>
<div class="big {sg}">{pct(s['m'])}</div><div class="cap">par trade · total {sol(s['tot'])} SOL</div>
<div class="track"><i style="width:{min(100, 100 * s['n'] / s['obj']):.0f}%"></i></div>
<div class="cap">{s['n']} / {s['obj']} trades pour le verdict</div></article>""")
    trs = []
    for s in st:
        c = lambda v: "pos" if (v or 0) > 0 else "neg" if (v or 0) < 0 else ""  # noqa: E731
        trs.append(f"<tr><td>{s['r']}</td><td class='txt'>{escape(s['nom'])}</td><td>{s['n']} / {s['obj']}</td>"
                   f"<td class='{c(s['m'])}'>{pct(s['m'])}</td><td>{pct(s['se'], False)}</td>"
                   f"<td>{pct(s['win'], False)}</td><td class='{c(s['tot'])}'>{sol(s['tot'])}</td>"
                   f"<td class='{c(s['sans'])}'>{pct(s['sans'])}</td><td class='txt'>{escape(s['ref']) or '—'}</td>"
                   f"<td>{pct(s['rm']) if s['ref'] else '—'}</td><td class='txt'>{s['verdict']}</td></tr>")
    recent = sorted((x for x in rows if x["serie"] in ("G", "H", "F", "E")), key=lambda x: x["heure"], reverse=True)[:25]
    rec = "".join(f"<tr><td>{paris(x['heure'], '%H:%M:%S')}</td><td class='txt'>{x['serie']}</td>"
                  f"<td class='txt'>{escape(x['token'])}…</td><td class='{'pos' if x['rendement'] > 0 else 'neg'}'>"
                  f"{pct(x['rendement'])}</td></tr>" for x in recent)
    best = sorted((x for x in rows if x["serie"] in COLORS), key=lambda x: -x["rendement"])[:8]
    top = "".join(f"<tr><td>{paris(x['heure'], '%H:%M')}</td><td class='txt'>{x['serie']}</td>"
                  f"<td class='txt'>{escape(x['token'])}…</td><td class='pos'>{pct(x['rendement'])}</td></tr>" for x in best)
    gen = datetime.now(PARIS).strftime("%d/%m %H:%M")
    html = PAGE.format(last=paris(last, "%d/%m %H:%M") if last else "—", gen=gen, n=len(main_rows),
                       tiles="".join(tiles), chart=chart(by), rows="".join(trs), recent=rec, top=top)
    out = ROOT / "reports" / "suivi_scalp.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(out, len(html.encode()) // 1024, "Ko")


PAGE = """<title>Suivi scalp Pump.fun</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>
/* Tableau de bord sobre : cartes des règles clés, courbe cumulée, tableaux ; une colonne au téléphone */
:root {{ --bg: #f6f7f5; --panel: #ffffff; --fg: #1d2420; --muted: #5d6862; --line: #dfe4e0; --ok: #1f7a4a; --bad: #b3372f; --warn: #9a6a12;
  --c1: #2a6fdb; --c2: #d9622b; --c3: #7b52c9; --c4: #1f8f8a; --c5: #8a8f2a; --c6: #9c5a7a; --c7: #0b7d3e; --c8: #b8860b;
  --serif: "Fraunces", Georgia, serif; --sans: "IBM Plex Sans", system-ui, -apple-system, sans-serif; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg: #121614; --panel: #1b201d; --fg: #e8ece9; --muted: #9aa59f; --line: #2c332f;
  --ok: #5cc48a; --bad: #ef7a70; --warn: #e2b04f; --c1: #6ea2ff; --c2: #ff9a62; --c3: #b294ff; --c4: #4fc8c1; --c5: #c9cf5a; --c6: #e08fb4; --c7: #5fd68f; --c8: #f0c75e; color-scheme: dark; }} }}
:root[data-theme="dark"] {{ --bg: #121614; --panel: #1b201d; --fg: #e8ece9; --muted: #9aa59f; --line: #2c332f;
  --ok: #5cc48a; --bad: #ef7a70; --warn: #e2b04f; --c1: #6ea2ff; --c2: #ff9a62; --c3: #b294ff; --c4: #4fc8c1; --c5: #c9cf5a; --c6: #e08fb4; --c7: #5fd68f; --c8: #f0c75e; color-scheme: dark; }}
body {{ background: var(--bg); color: var(--fg); font-family: var(--sans); padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 20px 32px; }}
.wrap {{ max-width: 72rem; margin-inline: auto; display: grid; gap: 20px; }}
h1 {{ font-family: var(--serif); font-weight: 400; font-size: 1.9rem; margin: 0; text-wrap: balance; }}
h2 {{ font-size: 1.05rem; font-weight: 600; margin: 0; }}
.sub, .note, .cap {{ color: var(--muted); margin: 0; }}
.note, .cap {{ font-size: 0.8rem; }}
.tiles {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr)); }}
.tile, .card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 16px; min-width: 0; display: grid; gap: 8px; align-content: start; }}
.top {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
.letter {{ font-family: var(--serif); width: 1.8rem; height: 1.8rem; display: inline-grid; place-items: center; border-radius: 50%; border: 1px solid var(--line); }}
.name {{ font-weight: 600; flex: 1; min-width: 0; }}
.pill {{ font-size: 0.75rem; padding: 0.1rem 0.5rem; border-radius: 999px; border: 1px solid currentColor; white-space: nowrap; }}
.pill.ok {{ color: var(--ok); }} .pill.bad {{ color: var(--bad); }} .pill.wait {{ color: var(--warn); }}
.big {{ font-family: var(--serif); font-size: 2.4rem; line-height: 1.1; font-variant-numeric: tabular-nums; }}
.pos {{ color: var(--ok); }} .neg {{ color: var(--bad); }}
.track {{ height: 6px; border-radius: 999px; background: var(--line); overflow: hidden; }}
.track i {{ display: block; height: 100%; background: var(--muted); border-radius: 999px; }}
svg .grid {{ stroke: var(--line); stroke-width: 1; }} svg .zero {{ stroke: var(--muted); stroke-width: 1; stroke-dasharray: 4 3; }}
svg .tick {{ fill: var(--muted); font-size: 12px; }} svg .end {{ font-size: 12px; font-weight: 600; }}
.scroll {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; font-size: 0.9rem; }}
th, td {{ text-align: right; padding: 0.45rem 0.6rem; border-bottom: 1px solid var(--line); white-space: nowrap; }}
th {{ font-size: 0.75rem; color: var(--muted); font-weight: 600; }}
th:first-child, td:first-child, .txt {{ text-align: left; }}
.two {{ display: grid; gap: 20px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 22rem), 1fr)); }}
ul {{ margin: 0; padding-left: 1.2rem; display: grid; gap: 4px; max-width: 70ch; }}
</style>
<div class="wrap">
<header><h1>Suivi scalp Pump.fun</h1>
<p class="sub">Simulation (paper trading), 0,1 SOL par trade. Dernier trade compté : {last} (heure de Paris) · {n} trades · page générée le {gen}.
Mise à jour toutes les 15 minutes : rechargez la page pour voir les derniers chiffres.</p></header>
<section class="tiles">{tiles}</section>
<section class="card"><h2>Total cumulé par règle</h2><p class="note">En SOL depuis le début du test, heure de Paris.</p>{chart}</section>
<section class="card"><h2>Toutes les règles</h2>
<p class="note">« ± » est la marge d’erreur de la moyenne. Validé = assez de trades, moyenne au-dessus de 2 fois la marge, positive sans les 3 meilleurs trades et meilleure que la référence sur les mêmes lancements.</p>
<div class="scroll"><table><thead><tr><th>Règle</th><th class="txt">Description</th><th>Trades</th><th>Moyenne</th><th>±</th><th>Gagnants</th>
<th>Total SOL</th><th>Sans 3 meilleurs</th><th class="txt">Référence</th><th>Référence, moyenne</th><th class="txt">Verdict</th></tr></thead>
<tbody>{rows}</tbody></table></div></section>
<div class="two">
<section class="card"><h2>Derniers trades E, F, G, H</h2><div class="scroll"><table><thead><tr><th>Heure</th><th class="txt">Règle</th><th class="txt">Token</th><th>Résultat</th></tr></thead><tbody>{recent}</tbody></table></div></section>
<section class="card"><h2>Plus gros trades</h2><div class="scroll"><table><thead><tr><th>Heure</th><th class="txt">Règle</th><th class="txt">Token</th><th>Résultat</th></tr></thead><tbody>{top}</tbody></table></div></section>
</div>
<section class="card"><h2>Les règles</h2><ul>
<li><b>A</b> : achat 1 s après la création, revente à 60 s.</li>
<li><b>B</b> (règle du PC) : achat à +5 s si au moins un autre acheteur que le créateur et moins de 2,5 SOL dans la courbe, revente à 60 s.</li>
<li><b>C</b> : entrée de B ; à 60 s, gardé si ≥ +20 % avec un stop suiveur à −30 %, 9 min au plus.</li>
<li><b>D</b> : seulement les 20 % meilleurs lancements selon le score de qualité, sortie de C.</li>
<li><b>E</b> : entrée de B ; moitié vendue dès ×2, le reste avec un stop suiveur à −40 % ; sans ×2 à 60 s, sortie de C ; 9 min au plus.</li>
<li><b>F</b> : sélection du score (comme D), sortie de E.</li>
<li><b>G</b> / <b>H</b> : F / E, mais seulement quand les trades B terminés dans les 30 dernières minutes sont positifs en moyenne (pendant les vagues). Comptées depuis leur fixation à 13:41.</li></ul></section>
</div>
"""

if __name__ == "__main__":
    main()
