"""Page de suivi (HTML statique) du test papier memecoins qui tourne sur le VPS. Lit en lecture seule les fichiers
publiés par le VPS (http://IP:8787/state.json, status.md, ia_regles.jsonl, choix des juges, erreurs.log), via le
tunnel HTTPS du proxy si la machine en a un, et le prix actuel des positions ouvertes sur GeckoTerminal.

Vue d'ensemble (03/11) : état du VPS, classement des caisses (total, jour, 24 h), courbe de chaque caisse, positions
ouvertes avec leur résultat en direct, historique de l'IA chercheuse par version, journal des juges, derniers trades.

Usage : python3 memes_page.py [--base http://140.82.38.41:8787] [--out reports/memes_paper.html]"""
import argparse
import json
import os
import re
import subprocess
import time
from collections import defaultdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

PARIS, NY = ZoneInfo("Europe/Paris"), ZoneInfo("America/New_York")
ROOT = Path(__file__).resolve().parents[1]
LABELS = {"juge": "IA juge v1", "juge2": "IA juge v2", "ia": "IA chercheuse", "ia_filtre": "IA chercheuse + filtre",
          "auto": "Règle qui apprend", "un_par_jour": "Sans IA, 1 toutes les 4 h", "classement": "Règles du post",
          "sans_cadran": "Post, sans cadran", "temoin": "Témoin au hasard"}
DETAIL = {"juge": "1 choix toutes les 4 h", "juge2": "jusqu'à 2 choix chaque heure",
          "ia": "règle réécrite par l'IA", "ia_filtre": "même règle + filtre anti-pièges",
          "auto": "meilleure règle simple, en cash si elle perd", "un_par_jour": "témoin des juges",
          "classement": "avec cadran", "sans_cadran": "mêmes choix", "temoin": "tiré dans le filtre"}
# courbes : 6 caisses au plus (palette catégorielle validée, ordre fixe) ; les autres sont dans le classement
COURBES = ("ia", "ia_filtre", "juge", "juge2", "un_par_jour", "classement")
POST = ("classement", "sans_cadran", "temoin")
# XTEN et PREDICT (05/11) : deux tokens jumeaux à volume de robots qui ont fait la plupart des gains ; la colonne
# « hors XTEN/PREDICT » montre si une caisse gagne aussi sur les autres tokens
JUMEAUX = ("XTEN", "PREDICT")


def fetch(url, timeout=30):
    cmd = ["curl", "-sS", "--max-time", str(timeout), "-f", url]
    if os.environ.get("HTTPS_PROXY"):
        cmd[1:1] = ["-p", "-x", os.environ["HTTPS_PROXY"]]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def essai(url, timeout=30):
    try:
        return fetch(url, timeout)
    except Exception:
        return None


def pct(x, signe=True):
    if x is None:
        return "—"
    return (f"{x * 100:+.1f}" if signe else f"{x * 100:.0f}").replace(".", ",").replace("-", "−") + "\u202f%"


def usd(x, signe=False):
    s = f"{abs(x):,.0f}".replace(",", "\u202f") + "\u202f$"
    return ("+" if x >= 0 else "−") + s if signe else ("−" if x < 0 else "") + s


def heure(t, fmt="%d/%m %H:%M"):
    return datetime.fromtimestamp(t, PARIS).strftime(fmt)


def cls(x):
    return "" if x is None or abs(x) < 1e-9 else ("pos" if x > 0 else "neg")


def pnl(rs):
    return sum(r["proceeds"] - r["dollars"] for r in rs)


def version_ia(r):
    m = re.match(r"IA v(\d+)", r.get("reason", ""))
    if m:
        return int(m.group(1))
    w = r.get("why")
    return w.get("ia_version") if isinstance(w, dict) else None


def prix_actuels(pools):
    """Prix GeckoTerminal des pools (30 par appel, un seul appel ici) ; {} si l'API refuse."""
    pools = sorted(set(pools))[:30]
    if not pools:
        return {}
    raw = essai("https://api.geckoterminal.com/api/v2/networks/solana/pools/multi/" + ",".join(pools), 30)
    try:
        return {d["attributes"]["address"]: float(d["attributes"]["base_token_price_usd"] or 0)
                for d in json.loads(raw)["data"]}
    except Exception:
        return {}


def courbe(books, now):
    """Ligne SVG : résultat de chaque caisse depuis le départ (réalisé à chaque vente, valeur actuelle au bout)."""
    W, H, L, R, T, B = 720, 260, 46, 12, 12, 26
    series = {}
    t0 = min((r["t_in"] for k in COURBES for r in books[k]["b"]["closed"]), default=now - 86400)
    for k in COURBES:
        b = books[k]["b"]
        pts, cum = [(t0, 0.0)], 0.0
        for r in sorted(b["closed"], key=lambda r: r["t_out"]):
            cum += r["proceeds"] - r["dollars"]
            pts.append((r["t_out"], cum / b["start"]))
        pts.append((now, books[k]["val"] / b["start"] - 1))
        series[k] = pts
    ys = [y for p in series.values() for _, y in p] + [0.0]
    lo, hi = min(ys), max(ys)
    pad = (hi - lo) * 0.08 or 0.05
    lo, hi = lo - pad, hi + pad
    X = lambda t: L + (t - t0) / max(now - t0, 1) * (W - L - R)
    Y = lambda y: T + (hi - y) / (hi - lo) * (H - T - B)
    grid = []
    step = 0.1 if hi - lo < 0.8 else 0.25
    v = (int(lo / step) - 1) * step
    while v <= hi:
        if v >= lo:
            grid.append(f'<line x1="{L}" x2="{W - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="{"zero" if abs(v) < 1e-9 else "grid"}"/>'
                        f'<text x="{L - 6}" y="{Y(v) + 4:.1f}" class="ax" text-anchor="end">{pct(v)}</text>')
        v += step
    jour = datetime.fromtimestamp(t0, PARIS).replace(hour=0, minute=0, second=0, microsecond=0).timestamp() + 86400
    while jour < now:
        grid.append(f'<line x1="{X(jour):.1f}" x2="{X(jour):.1f}" y1="{T}" y2="{H - B}" class="grid"/>'
                    f'<text x="{X(jour):.1f}" y="{H - 8}" class="ax" text-anchor="middle">{heure(jour, "%d/%m")}</text>')
        jour += 86400
    lines = []
    for i, k in enumerate(COURBES):
        d = " ".join(f"{'M' if j == 0 else 'L'}{X(t):.1f},{Y(y):.1f}" for j, (t, y) in enumerate(series[k]))
        lines.append(f'<path d="{d}" class="s s{i + 1}" fill="none"><title>{escape(LABELS[k])}</title></path>')
        t, y = series[k][-1]
        lines.append(f'<circle cx="{X(t):.1f}" cy="{Y(y):.1f}" r="4" class="d{i + 1}"/>')
    data = {k: [[round(t), round(y, 4)] for t, y in series[k]] for k in COURBES}
    legend = "".join(f'<span class="lg"><i class="sw sw{i + 1}"></i>{escape(LABELS[k])}</span>' for i, k in enumerate(COURBES))
    return (f'<div class="legend">{legend}</div><div class="chart" data-t0="{t0}" data-now="{now}" data-lo="{lo}" data-hi="{hi}">'
            f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Résultat de chaque caisse depuis le départ">'
            f'{"".join(grid)}{"".join(lines)}<line class="cross" x1="0" x2="0" y1="{T}" y2="{H - B}" visibility="hidden"/></svg>'
            f'<div class="tip" hidden></div></div><script type="application/json" id="series">{json.dumps(data)}</script>')


def calib_html(calib):
    """Note de calibration des juges (04/11) : probabilité annoncée face à la fréquence réelle de gain."""
    if not calib or not calib.get("juges"):
        return ""
    out = []
    for j, nom in (("juge", "v1"), ("juge2", "v2")):
        c = calib["juges"].get(j) or {}
        if not c.get("n"):
            continue
        tr = " · ".join(f"annoncé {t['proba_moyenne']:.2f} → réel {t['frequence_reelle']:.2f} ({t['n']})".replace(".", ",")
                        for t in c.get("tranches", []))
        out.append(f"<p><b>Calibration juge {nom}</b> ({c['n']} probabilités, gain = plus de "
                   f"{calib['seuil_gain'] * 100:.0f} % après {calib['horizon']}) : score de Brier {c['brier']:.3f} contre "
                   f"{c['brier_reference']:.3f} pour un juge qui dirait toujours la moyenne → "
                   f"{'<span class=pos>utile</span>' if c['utile'] else '<span class=neg>pas encore mieux que la moyenne</span>'}"
                   f".</p><p class='sub'>{tr}</p>".replace(".3f", ""))
    return "".join(out)


def reel_html(lignes):
    """Test réel à petites sommes (05/11) : ventes faites, comparées à leur jumeau papier, et derniers événements."""
    ev = []
    for ln in (lignes or "").splitlines():
        try:
            ev.append(json.loads(ln))
        except ValueError:
            pass
    if not ev:
        return "<p>Pas encore de test réel (le portefeuille dédié n'est pas créé ou n'a encore rien fait).</p>"
    dep = next((e for e in ev if e.get("event") == "depart"), {})
    ventes = [e for e in ev if e.get("event") == "vente"]
    achats = [e for e in ev if e.get("event") == "achat"]
    gain = sum(e["usd_recu"] - e["usd_mise"] for e in ventes)
    ec = [e["ecart_achat"] for e in achats if e.get("ecart_achat") is not None]
    ecr = [e["ret_reel"] - e["ret_papier"] for e in ventes if e.get("ret_papier") is not None]
    tete = (f"<p><b>Test réel</b> (portefeuille dédié, {usd(dep.get('valeur_usd', 0))} au départ) : {len(achats)} achats, "
            f"{len(ventes)} ventes, résultat réalisé <span class='{cls(gain)}'>{usd(gain, True)}</span>"
            + (f" · prix d'achat réel {pct(sum(ec) / len(ec))} par rapport au papier" if ec else "")
            + (f" · résultat réel {pct(sum(ecr) / len(ecr))} par rapport au papier, par trade" if ecr else "") + ".</p>")
    rows = "".join(
        f"<tr><td>{heure(e['t'])}</td><td class='txt'>{escape(e.get('event', ''))}</td>"
        f"<td class='txt'>{escape(str(e.get('nom') or e.get('token', '')[:6]))}</td>"
        f"<td class='txt sub wrap'>{escape(', '.join(f'{k} {v}' for k, v in e.items() if k in ('usd', 'usd_recu', 'ret_reel', 'ret_papier', 'ecart_achat', 'raison', 'erreur', 'secondes')))}</td></tr>"
        for e in reversed(ev[-12:]))
    return tete + ("<div class='scroll'><table><thead><tr><th>Heure</th><th class='txt'>Événement</th><th class='txt'>Token</th>"
                   "<th class='txt'>Détail</th></tr></thead><tbody>" + rows + "</tbody></table></div>")


def diversite_html(state):
    """Diversité du tournoi (06/11) : places qui achètent les mêmes tokens (même calcul que ia/outils/diversite.py)."""
    books, acs = state.get("books") or {}, {}
    for slot, debut in [("ia", 0)] + [(k, v.get("debut", 0)) for k, v in (state.get("defis") or {}).items()]:
        b = books.get(slot) or {}
        acs[slot] = ({r["token"] for r in b.get("closed", []) if r.get("t_in", 0) >= debut}
                     | {t for t, q in (b.get("open") or {}).items() if q.get("t", 0) >= debut})
    tous = [t for ts in acs.values() for t in ts]
    if not tous:
        return ""
    cles, proches = sorted(acs, key=lambda k: (k != "ia", int(k.split("_")[1]) if "_" in k else 0)), []
    for i, a in enumerate(cles):
        for b in cles[i + 1:]:
            if len(acs[a]) >= 3 and len(acs[b]) >= 3:
                part = len(acs[a] & acs[b]) / min(len(acs[a]), len(acs[b]))
                if part >= 0.5:
                    proches.append(f"{'championne' if a == 'ia' else a.replace('_', ' ')} et {b.replace('_', ' ')} "
                                   f"({part:.0%})")
    return (f"<p class='sub'><b>Diversité :</b> {len(set(tous))} tokens distincts sur {len(tous)} achats"
            + (" ; places qui achètent surtout les mêmes tokens : " + ", ".join(proches) if proches else
               " ; aucune paire de places trop proche") + ".</p>")


def page(state, status_md, regles, juges, erreurs, prix, now, calib=None, reel=None):
    values = dict(re.findall(r"## (\w+)\n- caisse [\d.]+ \$, valeur ([\d.]+) \$", status_md))
    upd = re.search(r"— (\d\d/\d\d \d\d:\d\d) UTC", status_md)
    grpc = re.search(r"Prix en direct \(gRPC\) : ([^\n]+)", status_md)
    minuit = datetime.fromtimestamp(now, PARIS).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    for slot, dfi in sorted((state.get("defis") or {}).items(), key=lambda kv: int(kv[0].split("_")[1])):  # tournoi (04/11) : challengeuses de la chercheuse
        LABELS[slot] = f"Défi {slot.split('_')[1]} : {dfi.get('nom') or 'sans nom'}"
        DETAIL[slot] = f"challengeuse de la chercheuse, depuis le {heure(dfi.get('debut', now))}"
    books = {}
    for k in LABELS:
        b = state["books"].get(k)
        if not b:
            continue
        val = float(values.get(k, b["cash"]))
        xs = [r["ret"] for r in b["closed"]]
        books[k] = {"b": b, "val": val, "n": len(xs), "win": (sum(x > 0 for x in xs) / len(xs)) if xs else None,
                    "moy": (sum(xs) / len(xs)) if xs else None,
                    "hors": [r["ret"] for r in b["closed"] if not str(r.get("name") or "").upper().startswith(JUMEAUX)],
                    "rugs": sum(r["reason"].startswith("pool vidé") or r["ret"] <= -0.8 for r in b["closed"]),
                    "jour": pnl([r for r in b["closed"] if r["t_out"] >= minuit]),
                    "h24": pnl([r for r in b["closed"] if r["t_out"] >= now - 86400])}

    # 1. état du VPS
    last = state.get("last_cycle") or 0
    age = (now - last) / 60
    err = [ln for ln in (erreurs or "").splitlines() if ln.strip()][-1:] if erreurs else []
    err_t = None
    if err:
        try:
            err_t = datetime.fromisoformat(err[0].split()[0]).timestamp()
        except Exception:
            pass
    ok = age <= 15
    etat = (f'<span class="badge {"ok" if ok else "ko"}">{"✓ VPS à jour" if ok else "⚠ VPS en retard"}</span> '
            f'dernier cycle {heure(last, "%H:%M")} (il y a {age:.0f} min)'
            + (f' · gRPC {escape(grpc.group(1).split(",")[0])}' if grpc else "")
            + (f' · dernière erreur {heure(err_t)}' + (" (<b>moins de 2 h</b>)" if now - err_t < 7200 else "") if err_t else " · aucune erreur")
            + f' · cadran du jour {str(state.get("dial", {}).get("cadran", "—")).replace(".", ",")}')

    # 2. classement
    rows = []
    for k, x in sorted(books.items(), key=lambda kv: -kv[1]["val"] / kv[1]["b"]["start"]):
        tot = x["val"] / x["b"]["start"] - 1
        rows.append(
            f"<tr><td class='txt'><b>{escape(LABELS[k])}</b><div class='sub'>{escape(DETAIL[k])}</div></td>"
            f"<td class='{cls(tot)}'><b>{pct(tot)}</b></td><td>{usd(x['val'])}</td>"
            f"<td class='{cls(x['jour'])}'>{usd(x['jour'], True) if x['jour'] else '—'}</td>"
            f"<td class='{cls(x['h24'])}'>{usd(x['h24'], True) if x['h24'] else '—'}</td>"
            f"<td>{x['n']}</td><td>{pct(x['win'], False)}</td><td class='{cls(x['moy'])}'>{pct(x['moy'])}</td>"
            f"<td class='{cls(sum(x['hors']) if x['hors'] else None)}'>{pct(sum(x['hors']) / len(x['hors'])) if x['hors'] else '—'}"
            f"<div class='sub'>{len(x['hors'])} trades</div></td>"
            f"<td>{x['rugs']}</td><td>{len(x['b']['open'])}</td></tr>")
    classement = ("<div class='scroll'><table><thead><tr><th class='txt'>Caisse</th><th>Total</th><th>Valeur</th>"
                  "<th>Aujourd'hui</th><th>24 h</th><th>Trades</th><th>Gagnants</th><th>Moyenne</th><th>Hors XTEN/PREDICT</th><th>Rugs</th>"
                  "<th>Ouvertes</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>")

    # 3. positions ouvertes (caisses des IA et témoins des juges en détail ; règles du post en résumé)
    op = []
    for k in LABELS:
        if k not in books or k in POST:
            continue
        for tok, p in books[k]["b"]["open"].items():
            px = prix.get(p["pool"])
            x = px / p["px_in"] - 1 if px and p.get("px_in") else None
            sx = p.get("sortie_ia") or p.get("sortie") or {}
            sortie = " · ".join(s for s in (
                f"stop {pct(sx['stop'])}" if sx.get("stop") is not None else "",
                f"objectif {pct(sx['objectif'])}" if sx.get("objectif") is not None else "",
                f"max {sx['duree_max_h']:g} h".replace(".", ",") if sx.get("duree_max_h") else "") if s) or "sortie du post (volume)"
            op.append((p["t"], f"<tr><td>{heure(p['t'])}</td><td class='txt'>{escape(LABELS[k])}</td>"
                               f"<td class='txt'>{escape(str(p.get('name') or tok[:6]))}</td><td>{usd(p['dollars'])}</td>"
                               f"<td class='{cls(x)}'><b>{pct(x)}</b></td><td class='txt sub'>{escape(sortie)}</td></tr>"))
    op.sort(reverse=True)
    post = [f"{escape(LABELS[k])} : {len(books[k]['b']['open'])}" for k in POST if k in books]
    positions = ("<div class='scroll'><table><thead><tr><th>Achat</th><th class='txt'>Caisse</th><th class='txt'>Token</th>"
                 "<th>Mise</th><th>Maintenant</th><th class='txt'>Sortie prévue</th></tr></thead><tbody>"
                 + ("".join(r for _, r in op) or "<tr><td colspan='6' class='txt'>Aucune position ouverte dans les caisses des IA.</td></tr>")
                 + "</tbody></table></div>"
                 + f"<p class='sub'>Positions des règles du post (souvent anciennes) : {' · '.join(post)}."
                 + ("" if prix else " Prix en direct indisponibles (GeckoTerminal a refusé l'appel).") + "</p>")

    # 4. chercheuse par version
    par_v = defaultdict(list)
    for r in books.get("ia", {}).get("b", {}).get("closed", []):
        par_v[version_ia(r)].append(r)
    debut = {}
    for r in regles:
        debut.setdefault(r.get("version"), r.get("t"))
    vrows = []
    for v in sorted((v for v in par_v if v is not None), reverse=True):
        rs = par_v[v]
        xs = [r["ret"] for r in rs]
        vrows.append(f"<tr><td class='txt'>v{v}</td><td>{heure(debut[v]) if debut.get(v) else '—'}</td><td>{len(xs)}</td>"
                     f"<td>{sum(x > 0 for x in xs)}</td><td class='{cls(sum(xs))}'>{pct(sum(xs) / len(xs))}</td>"
                     f"<td class='{cls(pnl(rs))}'>{usd(pnl(rs), True)}</td>"
                     f"<td>{sum(r['reason'].startswith('pool vidé') or r['ret'] <= -0.8 for r in rs)}</td></tr>")
    ia = state.get("ia") or {}
    regle_ia = (f"<p><b>Règle active : v{ia.get('version')}</b>" + (" (en pause)" if ia.get("pause") else "")
                + (f" — {escape(ia.get('pourquoi', '')[:400])}" if ia.get("pourquoi") else "") + "</p>") if ia else ""
    chercheuse = (regle_ia + "<div class='scroll'><table><thead><tr><th class='txt'>Version</th><th>Depuis</th><th>Trades</th>"
                  "<th>Gagnés</th><th>Moyenne</th><th>Résultat</th><th>Rugs</th></tr></thead><tbody>"
                  + "".join(vrows) + "</tbody></table></div>")
    finis = (state.get("defis_finis") or [])[-6:]
    if state.get("defis") or finis:
        chercheuse += ("<p><b>Tournoi :</b> une challengeuse ne remplace la règle active qu'après au moins 15 trades "
                       "fermés en direct, avec une moyenne positive, meilleure que la règle active sur la même période, "
                       "et assez nette pour ne pas être de la chance (seuil qui monte avec le nombre de places).</p>")
        chercheuse += diversite_html(state)
        if finis:
            chercheuse += "<p class='sub'>Challengeuses terminées : " + " · ".join(
                f"{escape(x['nom'] or x['place'])} ({x['trades']} trades, {pct(x['moyenne'])})" for x in reversed(finis)) + "</p>"
    au = state.get("auto") or {}
    auto_txt = ("<p><b>Règle qui apprend :</b> " + ("<span class='pos'>en jeu</span>" if au.get("regle") else "en cash")
                + (f" — {escape(au.get('raison', ''))}" if au.get("raison") else "") + "</p>") if au else ""

    # 5. journal des juges (24 dernières heures)
    noms = {}
    for b in state["books"].values():
        for r in b["closed"]:
            noms[r["token"]] = r.get("name")
        for tok, p in b["open"].items():
            noms[tok] = p.get("name")
    jr = []
    for nom, d in juges:
        try:
            t = datetime.strptime(d["creneau"], "%Y-%m-%d_%H").replace(tzinfo=NY).timestamp()
        except Exception:
            continue
        ch = d.get("choix")
        ch = [c for c in (ch if isinstance(ch, list) else [ch]) if c]
        quoi = ", ".join(escape(str(noms.get(c) or c[:6])) for c in ch) or "aucun"
        jr.append((t, f"<tr><td>{heure(t)}</td><td class='txt'>{'v2' if nom.startswith('juge2') else 'v1'}</td>"
                      f"<td class='txt'>{'<b>' + quoi + '</b>' if ch else quoi}</td>"
                      f"<td>{str(d.get('proba', '—')).replace('.', ',')}</td>"
                      f"<td class='txt sub wrap'>{escape(str(d.get('raison', ''))[:220])}</td></tr>"))
    jr.sort(reverse=True)
    n_choix = sum("<b>" in r for _, r in jr)
    journal = calib_html(calib) + (f"<p class='sub'>{len(jr)} décisions sur 24 h, dont {n_choix} achat{'s' if n_choix > 1 else ''}. "
               "Seuil d'achat : probabilité 0,55.</p><div class='scroll'><table><thead><tr><th>Créneau</th><th class='txt'>Juge</th>"
               "<th class='txt'>Choix</th><th>Proba</th><th class='txt'>Raison</th></tr></thead><tbody>"
               + ("".join(r for _, r in jr) or "<tr><td colspan='5' class='txt'>Aucune décision sur 24 h.</td></tr>")
               + "</tbody></table></div>")

    # 6. derniers trades
    closed = sorted((dict(r, book=k) for k, x in books.items() for r in x["b"]["closed"]), key=lambda r: -r["t_out"])
    t_closed = "".join(
        f"<tr><td>{heure(r['t_out'])}</td><td class='txt'>{escape(LABELS[r['book']])}</td>"
        f"<td class='txt'>{escape(str(r.get('name') or r['token'][:6]))}</td><td>{r['minutes']}\u202fmin</td>"
        f"<td class='{cls(r['ret'])}'>{pct(r['ret'])}</td><td class='{cls(r['ret'])}'>{usd(r['proceeds'] - r['dollars'], True)}</td>"
        f"<td class='txt sub'>{escape(r['reason'])}</td></tr>" for r in closed[:30])

    maj = heure(now)
    return f"""<title>Suivi memecoins papier</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
:root {{ --bg: #f6f5f2; --panel: #ffffff; --fg: #1d1c19; --muted: #66625a; --line: #e2ded6; --grid: #ebe8e1; --ok: #1f7a4a; --bad: #b3372f;
  --s1: #2a78d6; --s2: #eb6834; --s3: #1baf7a; --s4: #eda100; --s5: #e87ba4; --s6: #008300; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg: #141311; --panel: #1d1c19; --fg: #ecebe7; --muted: #a29d93; --line: #2f2d29; --grid: #2a2825; --ok: #5cc48a; --bad: #ef7a70; color-scheme: dark;
  --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500; --s5: #d55181; --s6: #008300; }} }}
:root[data-theme="dark"] {{ --bg: #141311; --panel: #1d1c19; --fg: #ecebe7; --muted: #a29d93; --line: #2f2d29; --grid: #2a2825; --ok: #5cc48a; --bad: #ef7a70; color-scheme: dark;
  --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500; --s5: #d55181; --s6: #008300; }}
body {{ background: var(--bg); color: var(--fg); font-family: system-ui, -apple-system, sans-serif; margin: 0; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 20px 32px; }}
.wrap {{ max-width: 64rem; margin-inline: auto; display: grid; gap: 16px; }}
h1 {{ font-size: 1.5rem; margin: 0; }} h2 {{ font-size: 1.05rem; margin: 0; }}
p {{ margin: 0; color: var(--muted); font-size: .9rem; max-width: 80ch; }} p b {{ color: var(--fg); }}
.box {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 16px; display: grid; gap: 10px; min-width: 0; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-weight: 600; font-size: .82rem; }}
.badge.ok {{ background: color-mix(in srgb, var(--ok) 15%, transparent); color: var(--ok); }}
.badge.ko {{ background: color-mix(in srgb, var(--bad) 15%, transparent); color: var(--bad); }}
.pos {{ color: var(--ok); }} .neg {{ color: var(--bad); }} .sub {{ font-size: .78rem; color: var(--muted); font-weight: 400; }}
.scroll {{ overflow-x: auto; }} table {{ width: 100%; border-collapse: collapse; font-size: .86rem; font-variant-numeric: tabular-nums; }}
th, td {{ text-align: right; padding: .4rem .5rem; border-bottom: 1px solid var(--line); white-space: nowrap; vertical-align: top; }}
th {{ color: var(--muted); font-size: .74rem; font-weight: 600; }} th:first-child, td:first-child, .txt {{ text-align: left; }}
td.wrap {{ white-space: normal; min-width: 18rem; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: .8rem; color: var(--muted); }}
.lg {{ display: inline-flex; align-items: center; gap: 6px; }} .sw {{ width: 14px; height: 3px; border-radius: 2px; display: inline-block; }}
.chart {{ position: relative; }} svg {{ width: 100%; height: auto; display: block; }}
.grid {{ stroke: var(--grid); stroke-width: 1; }} .zero {{ stroke: var(--muted); stroke-width: 1; }}
.ax {{ fill: var(--muted); font-size: 11px; }} .cross {{ stroke: var(--muted); stroke-width: 1; stroke-dasharray: 3 3; }}
.s {{ stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }}
{"".join(f".s{i} {{ stroke: var(--s{i}); }} .d{i} {{ fill: var(--s{i}); stroke: var(--panel); stroke-width: 2; }} .sw{i} {{ background: var(--s{i}); }} " for i in range(1, 7))}
.tip {{ position: absolute; top: 4px; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 6px 8px; font-size: .78rem; pointer-events: none; box-shadow: 0 2px 8px rgb(0 0 0 / .12); min-width: 11rem; }}
.tip div {{ display: flex; justify-content: space-between; gap: 10px; }} .tip i {{ width: 10px; height: 3px; border-radius: 2px; display: inline-block; margin-right: 5px; vertical-align: middle; }}
</style>
<div class="wrap">
<header style="display:grid;gap:6px"><h1>Suivi memecoins papier</h1>
<p>Test papier sur le VPS (Solana), 10 000 $ fictifs par caisse, aucun ordre réel. Page mise à jour le {maj} (heure de Paris).</p>
<p>{etat}</p></header>
<section class="box"><h2>Classement des caisses</h2>{classement}
<p class="sub">« Aujourd'hui » et « 24 h » : gains et pertes des trades fermés sur la période. Moyenne : par trade, frais et glissement compris ; « hors XTEN/PREDICT » : la même moyenne sans ces deux tokens. Rugs : pool vidé ou chute de plus de 80 %.</p></section>
<section class="box"><h2>Résultat depuis le départ</h2>{courbe(books, now)}
<p class="sub">Chaque point est une vente ; le dernier point est la valeur actuelle (positions ouvertes comprises). Les deux autres caisses du post et la règle qui apprend sont dans le classement.</p></section>
<section class="box"><h2>Test réel (petites sommes)</h2>{reel_html(reel)}</section>
<section class="box"><h2>Positions ouvertes</h2>{positions}</section>
<section class="box"><h2>IA chercheuse : résultats réels par version</h2>{chercheuse}{auto_txt}</section>
<section class="box"><h2>Journal des juges (24 h)</h2>{journal}</section>
<section class="box"><h2>Derniers trades fermés</h2><div class="scroll"><table><thead><tr><th>Vente</th><th class="txt">Caisse</th><th class="txt">Token</th><th>Durée</th><th>Résultat</th><th>Gain</th><th class="txt">Raison</th></tr></thead><tbody>{t_closed}</tbody></table></div></section>
<p class="sub">Verdict prévu : après au moins 100 trades fermés, une caisse ne gagne que si sa moyenne dépasse 2 fois sa marge d'erreur, reste positive sans ses 3 meilleurs trades et bat le témoin tiré au hasard.</p>
</div>
<script>
(() => {{
  const box = document.querySelector('.chart'); if (!box) return;
  const data = JSON.parse(document.getElementById('series').textContent);
  const names = {json.dumps({k: LABELS[k] for k in COURBES}, ensure_ascii=False)};
  const keys = Object.keys(data), svg = box.querySelector('svg'), tip = box.querySelector('.tip'), cross = svg.querySelector('.cross');
  const t0 = +box.dataset.t0, now = +box.dataset.now, W = 720, L = 46, R = 12;
  const fmt = v => (v >= 0 ? '+' : '−') + Math.abs(v * 100).toFixed(1).replace('.', ',') + ' %';
  const at = (pts, t) => {{ let y = 0; for (const [ti, yi] of pts) {{ if (ti <= t) y = yi; else break; }} return y; }};
  svg.addEventListener('pointermove', e => {{
    const r = svg.getBoundingClientRect(), x = (e.clientX - r.left) / r.width * W;
    if (x < L || x > W - R) {{ tip.hidden = true; cross.setAttribute('visibility', 'hidden'); return; }}
    const t = t0 + (x - L) / (W - L - R) * (now - t0);
    cross.setAttribute('x1', x); cross.setAttribute('x2', x); cross.setAttribute('visibility', 'visible');
    const d = new Date(t * 1000).toLocaleString('fr-FR', {{ timeZone: 'Europe/Paris', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }});
    const rows = keys.map((k, i) => [k, i, at(data[k], t)]).sort((a, b) => b[2] - a[2]);
    tip.innerHTML = '<b>' + d + '</b>' + rows.map(([k, i, y]) => `<div><span><i style="background:var(--s${{i + 1}})"></i>${{names[k]}}</span><span>${{fmt(y)}}</span></div>`).join('');
    tip.hidden = false;
    const left = (e.clientX - r.left) > r.width / 2 ? (e.clientX - r.left) - tip.offsetWidth - 12 : (e.clientX - r.left) + 12;
    tip.style.left = Math.max(0, left) + 'px';
  }});
  svg.addEventListener('pointerleave', () => {{ tip.hidden = true; cross.setAttribute('visibility', 'hidden'); }});
}})();
</script>
"""


def depuis_dossier(d, now, prix, rafraichir=60):
    """Même page, construite par le VPS à chaque cycle depuis son dossier de données (servie en /suivi.html), avec
    les prix qu'il vient de relever ; la page se recharge toute seule toutes les `rafraichir` secondes."""
    d = Path(d)
    lire = lambda n: (d / n).read_text(encoding="utf-8") if (d / n).exists() else ""
    regles = []
    for ln in lire("ia_regles.jsonl").splitlines():
        try:
            regles.append(json.loads(ln))
        except ValueError:
            pass
    juges = []
    for f in sorted(d.glob("juge*_20*.json")):
        m = re.search(r"^juge2?_(\d{4}-\d{2}-\d{2})(?:_(\d{2}))?\.json$", f.name)
        if not m:
            continue
        t = datetime.strptime(f"{m.group(1)}_{m.group(2) or '06'}", "%Y-%m-%d_%H").replace(tzinfo=NY).timestamp()
        if now - t <= 26 * 3600:
            try:
                juges.append((f.name, json.loads(f.read_text(encoding="utf-8"))))
            except ValueError:
                pass
    err = lire("erreurs.log").splitlines()[-5:]
    try:
        calib = json.loads(lire("calibration_juges.json") or "null")
    except ValueError:
        calib = None
    corps = page(json.loads(lire("state.json")), lire("status.md"), regles, juges, "\n".join(err),
                 {p: x for p, x in prix.items() if x}, now, calib, lire("reel.jsonl"))
    return ('<!doctype html><html lang="fr"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<meta http-equiv="refresh" content="{rafraichir}"></head><body>{corps}</body></html>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://140.82.38.41:8787")
    ap.add_argument("--out", default=str(ROOT / "reports" / "memes_paper.html"))
    a = ap.parse_args()
    now = time.time()
    state = json.loads(fetch(a.base + "/state.json", 60))
    status_md = fetch(a.base + "/status.md")
    regles = []
    for ln in (essai(a.base + "/ia_regles.jsonl") or "").splitlines():
        try:
            regles.append(json.loads(ln))
        except ValueError:
            pass
    liste = sorted(set(re.findall(r'href="(juge2?_\d{4}-\d{2}-\d{2}(?:_\d{2})?\.json)"', essai(a.base + "/") or "")))
    juges = []
    for nom in liste:
        m = re.search(r"_(\d{4}-\d{2}-\d{2})(?:_(\d{2}))?\.json$", nom)  # sans heure : ancien choix de 06:00
        t = datetime.strptime(f"{m.group(1)}_{m.group(2) or '06'}", "%Y-%m-%d_%H").replace(tzinfo=NY).timestamp()
        if now - t > 26 * 3600:
            continue
        raw = essai(a.base + "/" + nom, 20)
        try:
            juges.append((nom, json.loads(raw)))
        except Exception:
            pass
    pools = [p["pool"] for k, b in state["books"].items() if k not in POST for p in b["open"].values()]
    prix = prix_actuels(pools)
    try:
        calib = json.loads(essai(a.base + "/calibration_juges.json") or "null")
    except ValueError:
        calib = None
    page_html = page(state, status_md, regles, juges, essai(a.base + "/erreurs.log"), prix, now, calib,
                     essai(a.base + "/reel.jsonl"))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(page_html, encoding="utf-8")
    print(a.out)


if __name__ == "__main__":
    main()
