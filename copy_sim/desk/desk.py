"""Bureau papier façon @savipww (post du 13/10/2026), parties testables gratuitement :
- CRYPTO : momentum 12-1 mois sur BTC, ETH, SOL (rendement de J-365 à J-30), les 2 meilleurs s'ils sont positifs, à
  parts égales, sinon cash ; taille × « cadran crypto » = part de feux verts parmi : liquidité nette de la Fed en hausse
  sur 4 semaines, écart de crédit high yield en baisse ou stable sur 4 semaines, BTC au-dessus de sa moyenne 200 jours ;
  cadran < 0,5 -> cash. Revu chaque jour, 10 pb de frais par côté sur ce qui change.
- TENDANCE (« Runner ») : Nasdaq 100 à 3× (synthétique, quotidien : 3 × rendement − 2 × taux court − 0,95 %/an) quand
  l'indice clôture 1 % au-dessus de sa moyenne 200 jours, sortie quand il clôture 3 % en dessous ; dehors, bons du
  Trésor (taux 3 mois). 10 pb par côté à chaque changement.
- CADRAN MEMES (vérification de son « équipe de nuit ») : rendement de SOL et BTC sur les 5 jours suivants selon le
  cadran (liquidité, VIX < 22, BTC > moyenne 200 j, SOL > moyenne 50 j).
Verdict comme dans le post, sur des années que la règle n'a pas vues : VALIDÉ si elle bat la référence (acheter et
garder) en croissance ET en Sharpe sur la période d'apprentissage ET sur la période de test ; COMPROMIS si une seule
des deux mesures ; PAS D'AVANTAGE sinon.

Usage :
  python3 desk.py backtest            -> reports/desk_backtest.md
  python3 desk.py paper --since 2026-10-30   -> reports/desk_paper.md (+ .json), rejoue les règles figées depuis la date
  option --refresh pour retélécharger les données (sinon cache data_desk/ de moins de 12 h)"""
import json
import math
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data_desk"
FRED = ("NASDAQ100", "DTB3", "WALCL", "WTREGEN", "RRPONTSYD", "BAMLH0A0HYM2", "VIXCLS")
COST = 0.0010  # par côté
LETF_FEE = 0.0095


# ------------------------------------------------------------------ données
def _fresh(p, hours=12):
    return p.exists() and time.time() - p.stat().st_mtime < hours * 3600


def fetch(refresh=False):
    DATA.mkdir(parents=True, exist_ok=True)
    for sid in FRED:
        p = DATA / f"fred_{sid}.csv"
        if refresh or not _fresh(p):
            for k in range(3):
                try:
                    req = urllib.request.Request(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}",
                                                 headers={"User-Agent": "curl/8.5.0"})
                    p.write_bytes(urllib.request.urlopen(req, timeout=90).read())
                    break
                except Exception:
                    time.sleep(10)
    for coin in ("BTC", "ETH", "SOL"):
        p = DATA / f"hl_{coin}_1d.json"
        if refresh or not _fresh(p):
            now = int(time.time() * 1000)
            body = json.dumps({"type": "candleSnapshot", "req": {"coin": coin, "interval": "1d",
                                                                   "startTime": now - 5000 * 86_400_000, "endTime": now}})
            req = urllib.request.Request("https://api.hyperliquid.xyz/info", data=body.encode(),
                                         headers={"Content-Type": "application/json"})
            p.write_text(urllib.request.urlopen(req, timeout=60).read().decode())
            time.sleep(2)


def fred(sid):
    out = {}
    for ln in (DATA / f"fred_{sid}.csv").read_text().splitlines()[1:]:
        d, v = ln.split(",")
        if v not in ("", "."):
            out[date.fromisoformat(d)] = float(v)
    return out


def crypto_closes(coin):
    """Clôture journalière (bougie 00:00 UTC) indexée par la date du jour de la bougie. La bougie du jour en cours
    (pas encore close) est exclue."""
    today = datetime.now(timezone.utc).date()
    out = {}
    for c in json.loads((DATA / f"hl_{coin}_1d.json").read_text()):
        d = datetime.fromtimestamp(c["t"] / 1000, timezone.utc).date()
        if d < today:
            out[d] = float(c["c"])
    return out


def asof(series, d):
    """Dernière valeur connue au jour d (séries hebdomadaires ou avec trous)."""
    best = None
    for k in series:
        if k <= d and (best is None or k > best):
            best = k
    return series[best] if best else None


class AsOf:
    def __init__(self, series):
        self.keys = sorted(series)
        self.s = series

    def __call__(self, d, lag_days=0):
        import bisect
        i = bisect.bisect_right(self.keys, d - timedelta(days=lag_days)) - 1
        return self.s[self.keys[i]] if i >= 0 else None


def sma(vals, n):
    return sum(vals[-n:]) / n if len(vals) >= n else None


# ------------------------------------------------------------------ feux verts
def macro_greens(d, liq, hy, vix):
    """Liquidité nette (WALCL − TGA − RRP, en milliards) en hausse sur 4 semaines ; crédit HY en baisse/stable sur
    4 semaines ; VIX < 22. Données décalées d'un jour (publiées après la séance). None = donnée absente."""
    g = {}
    a, b = liq(d, 1), liq(d, 29)
    g["liquidite"] = None if a is None or b is None else a > b
    a, b = hy(d, 1), hy(d, 29)
    g["credit"] = None if a is None or b is None else a <= b
    v = vix(d, 1)
    g["vix"] = None if v is None else v < 22
    return g


def build_liq():
    walcl, tga, rrp = fred("WALCL"), fred("WTREGEN"), fred("RRPONTSYD")
    rr = AsOf(rrp)
    net = {d: walcl[d] / 1000 - tga[d] / 1000 - (rr(d) or 0) for d in walcl if d in tga}
    return AsOf(net)


# ------------------------------------------------------------------ partie CRYPTO
def crypto_sleeve(start, end, need_all_inputs=False):
    """Rejoue la partie crypto jour par jour ; retourne la liste (jour, rendement net, poids, cadran)."""
    cl = {c: crypto_closes(c) for c in ("BTC", "ETH", "SOL")}
    liq, hy, vix = build_liq(), AsOf(fred("BAMLH0A0HYM2")), AsOf(fred("VIXCLS"))
    days = sorted(d for d in cl["BTC"] if start <= d <= end)
    btc_hist = sorted(cl["BTC"])
    w_prev, out = {}, []
    for i, d in enumerate(days):
        nxt = days[i + 1] if i + 1 < len(days) else None  # dernier jour : décision prise, rendement pas encore connu
        # décision à la clôture de d
        past = [cl["BTC"][k] for k in btc_hist if k <= d]
        btc_ok = None if len(past) < 200 else past[-1] > sma(past, 200)
        g = macro_greens(d, liq, hy, vix)
        inputs = {"liquidite": g["liquidite"], "credit": g["credit"], "btc": btc_ok}
        avail = [v for v in inputs.values() if v is not None]
        if need_all_inputs and len(avail) < 3:
            dial = sum(bool(v) for v in inputs.values()) / 3  # en direct : donnée absente = rouge
        else:
            dial = sum(avail) / len(avail) if avail else 0.0
        mom = {}
        for c in cl:
            a, b = cl[c].get(d - timedelta(days=30)), cl[c].get(d - timedelta(days=365))
            if a and b:
                mom[c] = a / b - 1
        top = [c for c, m in sorted(mom.items(), key=lambda x: -x[1]) if m > 0][:2]
        scale = dial if dial >= 0.5 else 0.0
        w = {c: scale / len(top) for c in top} if top else {}
        turn = sum(abs(w.get(c, 0) - w_prev.get(c, 0)) for c in set(w) | set(w_prev))
        if nxt is None:
            out.append((d, None, w, dial, inputs))  # décision du jour, appliquée à la prochaine bougie
            break
        r = sum(wt * (cl[c][nxt] / cl[c][d] - 1) for c, wt in w.items() if nxt in cl[c] and d in cl[c])
        out.append((nxt, r - turn * COST, w, dial, inputs))
        w_prev = w
    return out


def buy_hold(coin, start, end):
    cl = crypto_closes(coin)
    days = sorted(d for d in cl if start <= d <= end)
    return [(days[i + 1], cl[days[i + 1]] / cl[days[i]] - 1) for i in range(len(days) - 1)]


# ------------------------------------------------------------------ partie TENDANCE
def trend_sleeve(start, end, n=200, band_in=1.01, band_out=0.97, lev=3.0):
    ndx, tb = fred("NASDAQ100"), AsOf(fred("DTB3"))
    days = sorted(ndx)
    out, inside = [], False
    for i in range(n, len(days) - 1):
        d, nxt = days[i], days[i + 1]
        if nxt < start or d > end:
            continue
        ma = sum(ndx[k] for k in days[i - n + 1:i + 1]) / n
        was = inside
        inside = ndx[d] > ma * (band_out if inside else band_in)
        rf = (tb(d) or 0) / 100 / 252
        r_ndx = ndx[nxt] / ndx[d] - 1
        r = lev * r_ndx - (lev - 1) * rf - LETF_FEE / 252 if inside else rf
        if inside != was:
            r -= COST * 2  # vendre l'un, acheter l'autre
        out.append((nxt, r, inside))
    return out


def ndx_series(start, end, lev=1.0):
    ndx, tb = fred("NASDAQ100"), AsOf(fred("DTB3"))
    days = sorted(ndx)
    res = []
    for i in range(len(days) - 1):
        d, nxt = days[i], days[i + 1]
        if start <= nxt <= end:
            rf = (tb(d) or 0) / 100 / 252
            res.append((nxt, lev * (ndx[nxt] / ndx[d] - 1) - (lev - 1) * rf - (LETF_FEE / 252 if lev > 1 else 0)))
    return res


# ------------------------------------------------------------------ mesures
def perf(rets, per_year):
    if len(rets) < 20:
        return None
    eq, peak, dd = 1.0, 1.0, 0.0
    for r in rets:
        eq *= 1 + r
        peak = max(peak, eq)
        dd = min(dd, eq / peak - 1)
    yrs = len(rets) / per_year
    m = sum(rets) / len(rets)
    sd = (sum((r - m) ** 2 for r in rets) / (len(rets) - 1)) ** 0.5
    return {"croissance": eq ** (1 / yrs) - 1 if eq > 0 else -1.0, "total": eq - 1, "pire_baisse": dd,
            "sharpe": m / sd * math.sqrt(per_year) if sd else 0.0, "annees": yrs}


def verdict(s_tr, b_tr, s_te, b_te):
    def beats(s, b):
        return (s["croissance"] > b["croissance"], s["sharpe"] > b["sharpe"])
    a, c = beats(s_tr, b_tr), beats(s_te, b_te)
    if all(a) and all(c):
        return "VALIDÉ"
    if any(a) and any(c):
        return "COMPROMIS"
    return "PAS D'AVANTAGE"


def fmt(p):
    return (f"{p['croissance']:+.1%}/an, total {p['total']:+.0%}, pire baisse {p['pire_baisse']:.0%}, "
            f"Sharpe {p['sharpe']:.2f} ({p['annees']:.1f} ans)")


# ------------------------------------------------------------------ rapports
def backtest():
    md = [f"# Bureau papier façon @savipww : test sur le passé — {datetime.now(timezone.utc):%d/%m/%Y %H:%M} UTC", ""]
    # CRYPTO
    cs = [x for x in crypto_sleeve(date(2021, 9, 20), date.today()) if x[1] is not None]
    split = date(2023, 1, 1)
    md += ["## Partie CRYPTO (momentum 12-1 sur BTC/ETH/SOL × cadran crypto)",
           "Apprentissage : sept. 2021 → 2022 (premier jour avec 12 mois d'historique) ; test : 2023 → aujourd'hui. "
           "Avant fin 2023 l'écart de crédit n'existe pas en accès libre : le cadran utilise alors les 2 autres feux.", ""]
    for name, rng in (("apprentissage", (date(2021, 9, 20), split)), ("test", (split, date.today()))):
        s = perf([r for d, r, *_ in cs if rng[0] <= d < rng[1]], 365)
        b = perf([r for d, r in buy_hold("BTC", *rng)], 365)
        md.append(f"- {name} : règle {fmt(s)} | BTC acheté et gardé {fmt(b)}")
    s_tr = perf([r for d, r, *_ in cs if d < split], 365)
    s_te = perf([r for d, r, *_ in cs if d >= split], 365)
    b_tr = perf([r for d, r in buy_hold("BTC", date(2021, 9, 20), split)], 365)
    b_te = perf([r for d, r in buy_hold("BTC", split, date.today())], 365)
    exposure = sum(1 for _, _, w, *_ in cs if w) / len(cs)
    md += [f"- exposée au marché {exposure:.0%} des jours", f"- **verdict : {verdict(s_tr, b_tr, s_te, b_te)}**", ""]
    # TENDANCE
    t0, t1, t2 = date(1999, 1, 4), date(2015, 1, 1), date.today()
    md += ["## Partie TENDANCE (Nasdaq 100 ×3 au-dessus de la moyenne 200 jours, sinon bons du Trésor)",
           "Apprentissage : 1999 → 2014 (bulle internet et 2008 compris) ; test : 2015 → aujourd'hui (comme dans le post).", ""]
    for name, a, b in (("apprentissage", t0, t1), ("test", t1, t2)):
        md.append(f"- {name} : règle {fmt(perf([r for _, r, _ in trend_sleeve(a, b)], 252))}")
        md.append(f"  - Nasdaq acheté et gardé {fmt(perf([r for _, r in ndx_series(a, b)], 252))}")
        md.append(f"  - Nasdaq ×3 acheté et gardé {fmt(perf([r for _, r in ndx_series(a, b, 3.0)], 252))}")
    v = verdict(perf([r for _, r, _ in trend_sleeve(t0, t1)], 252), perf([r for _, r in ndx_series(t0, t1)], 252),
                perf([r for _, r, _ in trend_sleeve(t1, t2)], 252), perf([r for _, r in ndx_series(t1, t2)], 252))
    md += [f"- **verdict (contre le Nasdaq acheté et gardé) : {v}**", "",
           "Robustesse (moyenne N jours × bande de sortie, test 2015 → aujourd'hui, croissance/an et pire baisse) :", ""]
    md += ["| N \\ sortie | −1 % | −2 % | −3 % | −4 % | −5 % |", "|---|---|---|---|---|---|"]
    for n in (100, 150, 175, 200, 225, 250, 300):
        cells = []
        for bo in (0.99, 0.98, 0.97, 0.96, 0.95):
            p = perf([r for _, r, _ in trend_sleeve(t1, t2, n=n, band_out=bo)], 252)
            cells.append(f"{p['croissance']:+.0%} / {p['pire_baisse']:.0%}")
        md.append(f"| {n} | " + " | ".join(cells) + " |")
    md.append("")
    # CADRAN MEMES
    md += ["## Cadran memecoins : sépare-t-il les bons et les mauvais jours ?",
           "Rendement moyen sur les 5 jours suivants selon le cadran du jour (liquidité, VIX < 22, BTC > moy. 200 j, "
           "SOL > moy. 50 j). Sans frais.", ""]
    cl = {c: crypto_closes(c) for c in ("BTC", "SOL")}
    liq, hy, vix = build_liq(), AsOf(fred("BAMLH0A0HYM2")), AsOf(fred("VIXCLS"))
    days = sorted(d for d in cl["SOL"] if d in cl["BTC"])
    rows = []
    for i in range(200, len(days) - 5):
        d = days[i]
        b = [cl["BTC"][k] for k in days[:i + 1]]
        s = [cl["SOL"][k] for k in days[:i + 1]]
        g = macro_greens(d, liq, hy, vix)
        greens = [g["liquidite"], g["vix"], b[-1] > sma(b, 200), s[-1] > sma(s, 50)]
        dial = sum(bool(x) for x in greens) / 4
        rows.append((d, dial, cl["SOL"][days[i + 5]] / cl["SOL"][d] - 1, cl["BTC"][days[i + 5]] / cl["BTC"][d] - 1))
    for per, (a, z) in (("2021-2023", (date(2021, 1, 1), date(2024, 1, 1))), ("2024 → aujourd'hui", (date(2024, 1, 1), date.today()))):
        md.append(f"**{per}**")
        md += ["", "| cadran | jours | SOL 5 j | BTC 5 j |", "|---|---|---|---|"]
        for lv in (0.0, 0.25, 0.5, 0.75, 1.0):
            sel = [r for r in rows if a <= r[0] < z and r[1] == lv]
            if sel:
                md.append(f"| {lv:.2f} | {len(sel)} | {sum(r[2] for r in sel) / len(sel):+.2%} | {sum(r[3] for r in sel) / len(sel):+.2%} |")
        md.append("")
    rep = "\n".join(md)
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "desk_backtest.md").write_text(rep, encoding="utf-8")
    print(rep)


def paper(since):
    """Rejoue les règles figées depuis `since` (aucun état à garder : tout se recalcule à partir des données publiques)."""
    end = date.today()
    cs = crypto_sleeve(since - timedelta(days=400), end, need_all_inputs=True)  # historique pour le momentum, compte depuis `since`
    ts = trend_sleeve(since - timedelta(days=3), end)
    eq_c = 1.0
    for d, r, *_ in cs:
        if d >= since and r is not None:
            eq_c *= 1 + r
    eq_t = 1.0
    for d, r, _ in ts:
        if d >= since:
            eq_t *= 1 + r
    last_c = cs[-1] if cs else None
    last_t = ts[-1] if ts else None
    out = {"depuis": since.isoformat(), "maj": datetime.now(timezone.utc).isoformat(timespec="minutes"),
           "crypto": {"valeur": eq_c, "cadran": last_c[3] if last_c else None, "feux": last_c[4] if last_c else None,
                      "position": last_c[2] if last_c else None, "dernier_jour": last_c[0].isoformat() if last_c else None},
           "tendance": {"valeur": eq_t, "dans_le_nasdaq_x3": last_t[2] if last_t else None,
                        "dernier_jour": last_t[0].isoformat() if last_t else None}}
    md = [f"# Bureau papier (crypto + tendance) — mis à jour {out['maj']} UTC", "",
          f"Règles figées le {since:%d/%m/%Y} ; tout est rejoué depuis cette date à partir des données publiques.", "",
          f"- **Crypto** : {eq_c - 1:+.2%} depuis le départ ; cadran {out['crypto']['cadran']} ; feux {out['crypto']['feux']} ; "
          f"position {out['crypto']['position'] or 'cash'} (au {out['crypto']['dernier_jour']})",
          f"- **Tendance** : {eq_t - 1:+.2%} depuis le départ ; "
          f"{'Nasdaq ×3' if out['tendance']['dans_le_nasdaq_x3'] else 'bons du Trésor'} (au {out['tendance']['dernier_jour']})"]
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "desk_paper.md").write_text("\n".join(md), encoding="utf-8")
    (ROOT / "reports" / "desk_paper.html").write_text(page(out, since), encoding="utf-8")
    (ROOT / "reports" / "desk_paper.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))
    print("\n".join(md))


def page(o, since):
    """Page de suivi simple (HTML statique, lisible sur téléphone)."""
    def pct(x):
        return f"{x * 100:+.2f}".replace(".", ",") + "\u202f%"
    c, t = o["crypto"], o["tendance"]
    pos = ", ".join(f"{k} {v * 100:.0f}\u202f%" for k, v in (c["position"] or {}).items()) or "cash"
    feux = " · ".join(f"{k} {'vert' if v else ('rouge' if v is False else 'absent')}" for k, v in (c["feux"] or {}).items())
    cad = "—" if c["cadran"] is None else f"{c['cadran']:.2f}".replace(".", ",")
    return f"""<title>Bureau papier crypto</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
:root {{ --bg: #f5f6f8; --panel: #ffffff; --fg: #1b1f24; --muted: #5b6470; --line: #dde1e6; --ok: #1f7a4a; --bad: #b3372f; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg: #111418; --panel: #1a1e24; --fg: #e9ecef; --muted: #9aa3ad; --line: #2b313a; --ok: #5cc48a; --bad: #ef7a70; color-scheme: dark; }} }}
:root[data-theme="dark"] {{ --bg: #111418; --panel: #1a1e24; --fg: #e9ecef; --muted: #9aa3ad; --line: #2b313a; --ok: #5cc48a; --bad: #ef7a70; color-scheme: dark; }}
body {{ background: var(--bg); color: var(--fg); font-family: system-ui, -apple-system, sans-serif; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 20px 32px; }}
.wrap {{ max-width: 46rem; margin-inline: auto; display: grid; gap: 16px; }}
h1 {{ font-size: 1.5rem; margin: 0; }} p {{ margin: 0; color: var(--muted); font-size: .9rem; }}
.card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 16px; display: grid; gap: 6px; }}
.big {{ font-size: 2rem; font-variant-numeric: tabular-nums; }} .pos {{ color: var(--ok); }} .neg {{ color: var(--bad); }}
.lab {{ font-weight: 600; }} .small {{ font-size: .85rem; color: var(--muted); }}
</style>
<div class="wrap">
<h1>Bureau papier crypto</h1>
<p>Simulation des parties « crypto » et « tendance » du post @savipww. Règles figées le {since:%d/%m/%Y}, rejouées chaque matin sur les données publiques. Mis à jour {o['maj'].replace('T', ' ')} UTC.</p>
<section class="card"><span class="lab">Crypto : momentum BTC/ETH/SOL × cadran</span>
<span class="big {'pos' if c['valeur'] >= 1 else 'neg'}">{pct(c['valeur'] - 1)}</span>
<span>Position : {pos} · cadran {cad}</span><span class="small">{feux} · au {c['dernier_jour']}</span>
<span class="small">Sur le passé (2023 → 2026) : +44,8 %/an, pire baisse −33 %, contre +49,8 %/an et −53 % pour BTC gardé. Verdict : COMPROMIS.</span></section>
<section class="card"><span class="lab">Tendance : Nasdaq ×3 au-dessus de la moyenne 200 jours</span>
<span class="big {'pos' if t['valeur'] >= 1 else 'neg'}">{pct(t['valeur'] - 1)}</span>
<span>Position : {'Nasdaq ×3' if t['dans_le_nasdaq_x3'] else 'bons du Trésor'} · au {t['dernier_jour']}</span>
<span class="small">Sur le passé (2015 → 2026) : +31 %/an mais pire baisse −62 % ; 1999-2014 : pire baisse −92 %. Verdict : COMPROMIS.</span></section>
<p>Partie memecoins : test papier sur le VPS (3 caisses : classement, sans cadran, témoin au hasard). Partie actions : non testée (données payantes).</p>
</div>
"""


if __name__ == "__main__":
    fetch(refresh="--refresh" in sys.argv)
    if len(sys.argv) > 1 and sys.argv[1] == "paper":
        i = sys.argv.index("--since") if "--since" in sys.argv else None
        paper(date.fromisoformat(sys.argv[i + 1]) if i else date.today())
    else:
        backtest()
