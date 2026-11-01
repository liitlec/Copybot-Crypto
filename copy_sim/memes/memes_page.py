"""Page de suivi (HTML statique) du test papier memecoins qui tourne sur le VPS. Lit en lecture seule les fichiers
publiés par le VPS (http://IP:8787/state.json, status.md), via le tunnel HTTPS du proxy si la machine en a un.
Usage : python3 memes_page.py [--base http://140.82.38.41:8787] [--out reports/memes_paper.html]"""
import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
ROOT = Path(__file__).resolve().parents[1]


def fetch(url):
    cmd = ["curl", "-sS", "--max-time", "30", "-f", url]
    if os.environ.get("HTTPS_PROXY"):
        cmd[1:1] = ["-p", "-x", os.environ["HTTPS_PROXY"]]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def pct(x):
    return "—" if x is None else f"{x * 100:+.1f}".replace(".", ",") + "\u202f%"


def usd(x):
    return f"{x:,.2f}".replace(",", "\u202f").replace(".", ",") + "\u202f$"


def stats(rs):
    xs = [r["ret"] for r in rs]
    if not xs:
        return None
    n, m = len(xs), sum(xs) / len(xs)
    se = ((sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5 / n ** 0.5) if n > 1 else None
    srt = sorted(xs, reverse=True)
    return {"n": n, "m": m, "se": se, "win": sum(x > 0 for x in xs) / n,
            "no3": (sum(srt[3:]) / len(srt[3:])) if n > 3 else None,
            "rug": sum(r["reason"].startswith("pool vidé") for r in rs),
            "pnl": sum(r["proceeds"] - r["dollars"] for r in rs)}


def page(state, status_md):
    values = dict(re.findall(r"## (\w+)\n- caisse [\d.]+ \$, valeur ([\d.]+) \$", status_md))
    upd = re.search(r"— (\d\d/\d\d \d\d:\d\d) UTC", status_md)
    when = "—"
    if upd:
        d = datetime.strptime(f"{datetime.now().year}/{upd.group(1)}", "%Y/%d/%m %H:%M").replace(tzinfo=timezone.utc)
        when = d.astimezone(PARIS).strftime("%d/%m %H:%M")
    dial = state.get("dial", {})
    labels = {"classement": "Ses règles (avec cadran)", "sans_cadran": "Mêmes choix, sans cadran", "temoin": "Témoin tiré au hasard",
              "juge": "IA juge (1 choix toutes les 4 h)", "un_par_jour": "Sans IA, 1 toutes les 4 h (témoin de l'IA juge)",
              "auto": "Règle qui apprend (réajustée chaque heure)", "ia": "IA chercheuse (réécrit sa règle elle-même)"}
    cards, rows_open, closed_all = [], [], []
    for key in [k for k in labels if k in state["books"]]:
        b = state["books"][key]
        val = float(values.get(key, b["cash"]))
        st = stats(b["closed"])
        line = "aucun trade fermé" if not st else (
            f"{st['n']} trades fermés · moyenne {pct(st['m'])}" + (f" ± {pct(st['se'])[1:]}" if st['se'] else "") +
            f" · gagnants {st['win'] * 100:.0f}\u202f% · sans les 3 meilleurs {pct(st['no3'])} · vidés {st['rug']}")
        cls = "pos" if val >= b["start"] else "neg"
        cards.append(f'<article class="card"><div class="lab">{labels[key]}</div><div class="big {cls}">{pct(val / b["start"] - 1)}</div>'
                     f'<div class="small">valeur {usd(val)} · départ {usd(b["start"])} · {len(b["open"])} positions ouvertes</div>'
                     f'<div class="small">{line}</div></article>')
        for tok, p in b["open"].items():
            rows_open.append((p["t"], key, p.get("name") or tok[:6], p["dollars"]))
        closed_all += [dict(r, book=key) for r in b["closed"]]
    rows_open.sort(reverse=True)
    closed_all.sort(key=lambda r: -r["t_out"])
    t_open = "".join(f"<tr><td>{datetime.fromtimestamp(t, PARIS):%d/%m %H:%M}</td><td class='txt'>{escape(labels[k].split(' (')[0])}</td>"
                     f"<td class='txt'>{escape(str(n))}</td><td>{usd(d)}</td></tr>" for t, k, n, d in rows_open[:30]) \
        or "<tr><td colspan='4' class='txt'>Aucune position ouverte.</td></tr>"
    t_closed = "".join(
        f"<tr><td>{datetime.fromtimestamp(r['t_out'], PARIS):%d/%m %H:%M}</td><td class='txt'>{escape(labels[r['book']].split(' (')[0])}</td>"
        f"<td class='txt'>{escape(str(r.get('name') or r['token'][:6]))}</td><td>{r['minutes']}\u202fmin</td>"
        f"<td class='{'pos' if r['ret'] > 0 else 'neg'}'>{pct(r['ret'])}</td><td class='txt'>{escape(r['reason'])}</td></tr>"
        for r in closed_all[:40]) or "<tr><td colspan='6' class='txt'>Pas encore de trade fermé.</td></tr>"
    au = state.get("auto") or {}
    rg = au.get("regle")
    auto_txt = ("Règle qui apprend : " + (
        f"âge ≤ {rg['age_max_h']} h, prix 1 h {rg['prix_1h']}, acheteurs {rg['acheteurs_1h']}, classement {rg['classe']}, "
        f"stop {rg['stop']:+.0%}, objectif {rg['objectif']:+.0%}, max {rg['duree_max_h']} h"
        + (f", idée de l'IA « {json.loads(rg['idee'])['nom']} »" if rg.get("idee") else "") if rg else "en cash")
        + (f" ({au.get('raison')})" if au.get("raison") else "")) if au else \
        "Règle qui apprend : pas encore d'apprentissage (il faut au moins 3 jours de collecte)."
    ia = state.get("ia")
    ia_txt = ("IA chercheuse : " + (f"règle v{ia['version']}" + (" en pause" if ia.get("pause") else "") +
              (f" — {ia['pourquoi']}" if ia.get("pourquoi") else "")) if ia else
              "IA chercheuse : pas encore de règle (elle passe toutes les heures).")
    verts = " · ".join(f"{k} {'vert' if v else 'rouge'}" for k, v in dial.get("verts", {}).items())
    cad = dial.get("cadran")
    return f"""<title>Suivi memecoins papier</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
:root {{ --bg: #f6f5f2; --panel: #ffffff; --fg: #1d1c19; --muted: #66625a; --line: #e2ded6; --ok: #1f7a4a; --bad: #b3372f; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg: #141311; --panel: #1d1c19; --fg: #ecebe7; --muted: #a29d93; --line: #2f2d29; --ok: #5cc48a; --bad: #ef7a70; color-scheme: dark; }} }}
:root[data-theme="dark"] {{ --bg: #141311; --panel: #1d1c19; --fg: #ecebe7; --muted: #a29d93; --line: #2f2d29; --ok: #5cc48a; --bad: #ef7a70; color-scheme: dark; }}
body {{ background: var(--bg); color: var(--fg); font-family: system-ui, -apple-system, sans-serif; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 20px 32px; }}
.wrap {{ max-width: 60rem; margin-inline: auto; display: grid; gap: 16px; }}
h1 {{ font-size: 1.5rem; margin: 0; }} h2 {{ font-size: 1rem; margin: 0; }}
p {{ margin: 0; color: var(--muted); font-size: .9rem; max-width: 70ch; }}
.cards {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr)); }}
.card, .box {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 16px; display: grid; gap: 6px; min-width: 0; }}
.lab {{ font-weight: 600; }} .big {{ font-size: 2rem; font-variant-numeric: tabular-nums; }} .small {{ font-size: .82rem; color: var(--muted); }}
.pos {{ color: var(--ok); }} .neg {{ color: var(--bad); }}
.scroll {{ overflow-x: auto; }} table {{ width: 100%; border-collapse: collapse; font-size: .88rem; font-variant-numeric: tabular-nums; }}
th, td {{ text-align: right; padding: .4rem .5rem; border-bottom: 1px solid var(--line); white-space: nowrap; }}
th {{ color: var(--muted); font-size: .75rem; font-weight: 600; }} th:first-child, td:first-child, .txt {{ text-align: left; }}
</style>
<div class="wrap">
<header><h1>Suivi memecoins papier</h1>
<p>Stratégie memecoins du post @savipww, en simulation sur le VPS (Solana, toutes les 5 min). Sept caisses fictives de 10 000 $ : trois achètent à chaque cycle selon le post, deux une fois par jour à 06:00 New York comme le post (l'une choisie par une IA, l'autre le premier du classement), une suit une règle réapprise chaque heure sur les données collectées, et une suit la règle qu'une IA chercheuse réécrit elle-même toutes les heures. Dernier cycle du VPS : {when} (heure de Paris). Cadran du jour : {"—" if cad is None else f"{cad:.2f}".replace(".", ",")} ({escape(verts)}).</p></header>
<section class="cards">{"".join(cards)}</section>
<p>{escape(auto_txt)}</p>
<p>{escape(ia_txt)}</p>
<section class="box"><h2>Positions ouvertes</h2><div class="scroll"><table><thead><tr><th>Achat</th><th class="txt">Caisse</th><th class="txt">Token</th><th>Mise</th></tr></thead><tbody>{t_open}</tbody></table></div></section>
<section class="box"><h2>Derniers trades fermés</h2><div class="scroll"><table><thead><tr><th>Vente</th><th class="txt">Caisse</th><th class="txt">Token</th><th>Durée</th><th>Résultat</th><th class="txt">Raison</th></tr></thead><tbody>{t_closed}</tbody></table></div></section>
<p>Verdict prévu : après au moins 100 trades fermés, gagnant seulement si la moyenne dépasse 2 fois sa marge d'erreur, reste positive sans les 3 meilleurs trades et bat le témoin tiré au hasard. Le cadran n'est utile que si « ses règles » battent « sans cadran » ; l'IA n'est utile que si « IA juge » bat « 1 par jour sans IA ». Frais 0,45 % par côté (min. 0,95 $) et impact sur le prix compris ; aucune clé, aucun ordre réel.</p>
</div>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://140.82.38.41:8787")
    ap.add_argument("--out", default=str(ROOT / "reports" / "memes_paper.html"))
    a = ap.parse_args()
    state = json.loads(fetch(a.base + "/state.json"))
    status_md = fetch(a.base + "/status.md")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(page(state, status_md), encoding="utf-8")
    print(a.out)


if __name__ == "__main__":
    main()
