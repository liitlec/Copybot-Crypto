"""Page de suivi du robot du labo sur la démo MT5 (demandée par Baptiste le 11/11) : candidats, trades, taux.
Lit labo/mt5/etat.json, labo/mt5/robot_journal.jsonl et labo/AVIS.md, écrit copy_sim/reports/labo_suivi.html
(page autonome, sans réseau). Usage : python3 copy_sim/labo/page_suivi.py"""
import html
import json
import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ICI = Path(__file__).resolve().parent
SORTIE = ICI.parent / "reports" / "labo_suivi.html"
PARIS = ZoneInfo("Europe/Paris")
TEMOIN = "hasard_m1"
DESC = {  # texte par défaut ; une hypothèse inconnue s'affiche sans description
    "hasard_m1": "Témoin : achète ou vend à pile ou face chaque 5 min. Sert de référence.",
    "hasard_m15": "Ancien témoin (version 1), retiré.",
    "elan_m1": "Suit le mouvement de la dernière minute.",
    "retour_m1": "Parie sur le retour après un mouvement d'une minute.",
    "fcassure_m1": "Fausse cassure : entre contre une cassure qui échoue.",
    "exces_m1": "Retour après un excès, bougies d'une minute.",
    "exces_m5": "Retour après un excès, bougies de 5 minutes, tenue 15 min.",
    "elan_m15": "Suit le mouvement sur 15 minutes.",
    "cassure_m15": "Cassure de fourchette sur 15 minutes, tenue 3 h.",
    "ecart_midi_m5": "Candidat « retour de midi » : entre 11 h et 14 h, retour après un écart de plus de 2 écarts-types.",
}


def e(x):
    return html.escape(str(x))


def usd(x, signe=True):
    s = f"{x:+,.2f}" if signe else f"{x:,.2f}"
    return s.replace(",", " ").replace(".", ",").replace("-", "−") + " $"


def paris(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(PARIS)


def stats(xs):
    n = len(xs)
    m = sum(xs) / n
    se = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1) / n) if n > 1 else None
    return n, m, se


def verdict(nom, xs, temoin):
    n, m, se = stats(xs)
    if nom.startswith("hasard"):
        return "ref", "référence"
    if n < 30 or not se:
        return "attente", f"trop peu ({n} sur 30)"
    if temoin and len(temoin) >= 30:
        nt, mt, st = stats(temoin)
        t = (m - mt) / math.sqrt(se ** 2 + st ** 2)
    else:
        t = m / se
    if t >= 2 and n >= 100:
        return "bon", "en avance sur le hasard"
    if t >= 2:
        return "piste", "piste à confirmer"
    if t <= -2:
        return "mauvais", "pire que le hasard"
    return "neutre", "comme le hasard"


def lire():
    etat = json.loads((ICI / "mt5" / "etat.json").read_text(encoding="utf-8"))
    par_hyp, par_heure, derniers, ouvertures, actives = defaultdict(list), defaultdict(list), [], defaultdict(int), []
    f = ICI / "mt5" / "robot_journal.jsonl"
    for ln in f.read_text(encoding="utf-8").splitlines() if f.exists() else []:
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        ev = d.get("evenement")
        if ev == "demarrage":
            actives = d.get("hypotheses") or actives
        elif ev == "ouverture" and d.get("ok"):
            ouvertures[d.get("hypothese")] += 1
        elif ev == "sortie" and isinstance(d.get("profit"), (int, float)):
            par_hyp[d["hypothese"]].append(d["profit"])
            par_heure[paris(d["heure"]).hour].append(d["profit"])
            derniers.append(d)
    avis = []
    a = ICI / "AVIS.md"
    titre_avis = ""
    if a.exists():
        for ln in a.read_text(encoding="utf-8").splitlines():
            if ln.startswith("# ") and not titre_avis:
                titre_avis = ln[2:].strip()
            m = re.match(r"^\d+\.\s+(.*)", ln)
            if m:
                avis.append(m.group(1))
            elif avis and ln.startswith("## "):
                break
    return etat, par_hyp, par_heure, derniers, actives, titre_avis, avis


def gras(t):
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", re.sub(r"`(.+?)`", r"<code>\1</code>", e(t)))


def page():
    etat, par_hyp, par_heure, derniers, actives, titre_avis, avis = lire()
    rob, gf = etat.get("robot") or {}, etat.get("garde_fou") or {}
    tous = [x for xs in par_hyp.values() for x in xs]
    temoin = par_hyp.get(TEMOIN, [])
    maj = paris(etat["ecrit"])
    retard = (datetime.now(timezone.utc) - maj.astimezone(timezone.utc)).total_seconds() / 60
    noms = sorted(set(par_hyp) | set(actives), key=lambda k: (-(sum(par_hyp[k]) if par_hyp.get(k) else -1e9), k))
    lignes = []
    for nom in noms:
        xs = par_hyp.get(nom, [])
        actif = nom in actives
        if xs:
            n, m, se = stats(xs)
            cl, txt = verdict(nom, xs, temoin)
            cells = (f"<td class='n'>{n}</td><td class='n {'pos' if sum(xs) > 0 else 'neg'}'>{usd(sum(xs))}</td>"
                     f"<td class='n'>{usd(m)}<span class='se'>{' ± ' + usd(se, False) if se else ''}</span></td>"
                     f"<td class='n'>{100 * sum(x > 0 for x in xs) / n:.0f} %</td>")
        else:
            cl, txt = "attente", "attend son signal"
            cells = "<td class='n'>0</td><td class='n'>—</td><td class='n'>—</td><td class='n'>—</td>"
        lignes.append(f"<tr class='{'' if actif else 'retire'}'><td><span class='nom'>{e(nom)}</span>"
                      f"<span class='desc'>{e(DESC.get(nom, ''))}{'' if actif else ' (plus dans le robot)'}</span></td>"
                      f"{cells}<td><span class='pastille {cl}'>{e(txt)}</span></td></tr>")
    heures = "".join(
        f"<tr><td>{h:02d} h – {h + 1:02d} h</td><td class='n'>{len(xs)}</td>"
        f"<td class='n {'pos' if sum(xs) > 0 else 'neg'}'>{usd(sum(xs))}</td><td class='n'>{usd(sum(xs) / len(xs))}</td></tr>"
        for h, xs in sorted(par_heure.items()))
    pos = "".join(
        f"<tr><td>{e(p.get('symbole'))}</td><td>{e(p.get('sens'))}</td><td class='n'>{p.get('lots')}</td>"
        f"<td class='n'>{p.get('prix_entree')}</td><td class='n'>{p.get('prix_actuel')}</td><td class='n'>{p.get('stop')}</td>"
        f"<td class='n {'pos' if (p.get('profit') or 0) > 0 else 'neg'}'>{usd(p.get('profit') or 0)}</td></tr>"
        for p in etat.get("positions_robot") or [])
    recents = "".join(
        f"<tr><td>{paris(d['heure']):%H:%M}</td><td>{e(d['hypothese'])}</td><td>{'achat' if d.get('sens') == 1 else 'vente'}</td>"
        f"<td class='n'>{d.get('entree')}</td><td class='n'>{d.get('prix_sortie')}</td><td>{e(d.get('raison', ''))}</td>"
        f"<td class='n {'pos' if d['profit'] > 0 else 'neg'}'>{usd(d['profit'])}</td></tr>"
        for d in derniers[-20:][::-1])
    etat_robot = ("en marche" if rob.get("en_marche") else "arrêté") if rob else "pas installé"
    alerte = ""
    if retard > 20:
        alerte = (f"<p class='alerte'>Le pont n'a rien envoyé depuis {retard:.0f} minutes : PC éteint, MT5 fermé ou "
                  "marché fermé. Les chiffres ci-dessous datent de son dernier envoi.</p>")
    if gf.get("ouvertures_bloquees"):
        alerte += "<p class='alerte'>Garde-fou atteint : plus aucune ouverture aujourd'hui.</p>"
    n_t = len(tous)
    return f"""<meta name="claude:viewport-fit-sides" content="cover">
<title>Robot or démo MT5</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600&display=swap">
<style>
/* tableau de bord : état du compte, puis les candidats classés, puis le détail */
:root {{ --fond:#f5f6f3; --carte:#ffffff; --texte:#1c211d; --doux:#5d665f; --trait:#dfe3dc; --or:#9a7412;
  --pos:#1d7a4a; --neg:#b3372c; --neutre:#5d665f; --piste:#8a6200; --fond-pos:#e2f2e8; --fond-neg:#f8e4e1;
  --fond-neutre:#eceee9; --fond-piste:#f6ecd0;
  --titre:'Space Grotesk',system-ui,sans-serif; --corps:'Inter',system-ui,sans-serif; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --fond:#141714; --carte:#1c211d; --texte:#e8ebe6;
  --doux:#9aa39b; --trait:#2e352f; --or:#d9b24a; --pos:#5fc48d; --neg:#ef8377; --neutre:#9aa39b; --piste:#e0bb55;
  --fond-pos:#19372a; --fond-neg:#42211d; --fond-neutre:#272d28; --fond-piste:#3a3016; color-scheme:dark }} }}
:root[data-theme="dark"] {{ --fond:#141714; --carte:#1c211d; --texte:#e8ebe6; --doux:#9aa39b; --trait:#2e352f; --or:#d9b24a;
  --pos:#5fc48d; --neg:#ef8377; --neutre:#9aa39b; --piste:#e0bb55; --fond-pos:#19372a; --fond-neg:#42211d;
  --fond-neutre:#272d28; --fond-piste:#3a3016; color-scheme:dark }}
body {{ background:var(--fond); color:var(--texte); font-family:var(--corps); font-size:15px; line-height:1.5;
  padding-block:24px 48px; padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)); }}
main {{ max-width:1040px; margin:0 auto; display:flex; flex-direction:column; gap:28px; }}
h1 {{ font-family:var(--titre); font-size:1.7rem; font-weight:600; margin:0; text-wrap:balance; }}
h1 em {{ font-style:normal; color:var(--or); }}
h2 {{ font-family:var(--titre); font-size:1.1rem; font-weight:600; margin:0 0 10px; }}
.sous {{ color:var(--doux); margin:4px 0 0; }}
.chiffres {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(150px, 1fr)); gap:12px; }}
.chiffre {{ background:var(--carte); border:1px solid var(--trait); border-radius:10px; padding:12px 14px; min-width:0; }}
.chiffre span {{ display:block; color:var(--doux); font-size:.78rem; text-transform:uppercase; letter-spacing:.05em; }}
.chiffre b {{ font-family:var(--titre); font-size:1.35rem; font-weight:600; font-variant-numeric:tabular-nums; }}
.defile {{ overflow-x:auto; background:var(--carte); border:1px solid var(--trait); border-radius:10px; }}
table {{ border-collapse:collapse; width:100%; font-variant-numeric:tabular-nums; }}
th, td {{ padding:9px 12px; text-align:left; border-bottom:1px solid var(--trait); white-space:nowrap; }}
th {{ font-size:.75rem; text-transform:uppercase; letter-spacing:.05em; color:var(--doux); font-weight:500; }}
tr:last-child td {{ border-bottom:0; }}
td.n, th.n {{ text-align:right; }}
td:first-child {{ white-space:normal; min-width:200px; }}
.nom {{ font-weight:600; display:block; font-family:ui-monospace, SFMono-Regular, Menlo, monospace; font-size:.9rem; }}
.desc {{ display:block; color:var(--doux); font-size:.82rem; }}
.se {{ color:var(--doux); font-size:.82rem; }}
.pos {{ color:var(--pos); }} .neg {{ color:var(--neg); }}
tr.retire td {{ opacity:.6; }}
.pastille {{ display:inline-block; padding:2px 10px; border-radius:999px; font-size:.8rem; font-weight:500; }}
.pastille.bon {{ background:var(--fond-pos); color:var(--pos); }}
.pastille.piste {{ background:var(--fond-piste); color:var(--piste); }}
.pastille.mauvais {{ background:var(--fond-neg); color:var(--neg); }}
.pastille.neutre, .pastille.attente, .pastille.ref {{ background:var(--fond-neutre); color:var(--neutre); }}
.avis {{ background:var(--carte); border:1px solid var(--trait); border-radius:10px; padding:14px 18px; }}
.avis ol {{ margin:0; padding-left:20px; display:flex; flex-direction:column; gap:6px; max-width:75ch; }}
.alerte {{ background:var(--fond-neg); color:var(--neg); border-radius:10px; padding:10px 14px; margin:0; font-weight:500; }}
.note {{ color:var(--doux); font-size:.85rem; margin:8px 0 0; max-width:75ch; }}
.deux {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:28px; }}
.deux > div {{ min-width:0; }}
code {{ font-family:ui-monospace, SFMono-Regular, Menlo, monospace; font-size:.88em; }}
</style>
<main>
<header>
  <h1>Robot <em>XAUUSD</em> sur la démo MT5</h1>
  <p class="sous">Dernier envoi du PC : {maj:%d/%m à %H:%M} (Paris) · robot version {e(rob.get('version_installee', '—'))}, {etat_robot} · essais à 0,01 lot, rien de prouvé tant que la colonne « Verdict » ne le dit pas</p>
</header>
{alerte}
<section class="chiffres">
  <div class="chiffre"><span>Valeur du compte démo</span><b>{usd(etat.get('valeur', 0), False)}</b></div>
  <div class="chiffre"><span>Résultat du jour</span><b class="{'pos' if gf.get('perte_du_jour', 0) > 0 else 'neg'}">{usd(gf.get('perte_du_jour', 0))}</b></div>
  <div class="chiffre"><span>Trades fermés</span><b>{n_t}</b></div>
  <div class="chiffre"><span>Total des trades</span><b class="{'pos' if sum(tous) > 0 else 'neg'}">{usd(sum(tous)) if tous else '—'}</b></div>
  <div class="chiffre"><span>Trades gagnants</span><b>{f"{100 * sum(x > 0 for x in tous) / n_t:.0f} %" if tous else '—'}</b></div>
  <div class="chiffre"><span>Positions ouvertes</span><b>{len(etat.get('positions_robot') or [])}</b></div>
</section>
<section>
  <h2>Les candidats</h2>
  <div class="defile"><table>
    <tr><th>Hypothèse</th><th class="n">Trades</th><th class="n">Total</th><th class="n">Moyenne par trade</th><th class="n">Gagnants</th><th>Verdict</th></tr>
    {''.join(lignes)}
  </table></div>
  <p class="note">Le verdict compare chaque hypothèse au témoin à pile ou face. Il faut au moins 30 trades pour un premier avis, et 100 trades avec une nette avance pour « en avance sur le hasard ». Le chiffre après ± est la marge d'erreur de la moyenne.</p>
</section>
<section class="avis">
  <h2>{e(titre_avis) or "Avis de l'IA"}</h2>
  <ol>{''.join(f'<li>{gras(a)}</li>' for a in avis) or "<li>Pas encore d'avis.</li>"}</ol>
</section>
<section class="deux">
  <div>
    <h2>Positions ouvertes</h2>
    <div class="defile"><table>
      <tr><th>Marché</th><th>Sens</th><th class="n">Lots</th><th class="n">Entrée</th><th class="n">Prix</th><th class="n">Stop</th><th class="n">Résultat</th></tr>
      {pos or "<tr><td colspan='7'>Aucune position ouverte.</td></tr>"}
    </table></div>
  </div>
  <div>
    <h2>Par heure de sortie (Paris)</h2>
    <div class="defile"><table>
      <tr><th>Heure</th><th class="n">Trades</th><th class="n">Total</th><th class="n">Moyenne</th></tr>
      {heures or "<tr><td colspan='4'>Pas encore de trade fermé.</td></tr>"}
    </table></div>
  </div>
</section>
<section>
  <h2>Les 20 derniers trades fermés</h2>
  <div class="defile"><table>
    <tr><th>Heure</th><th>Hypothèse</th><th>Sens</th><th class="n">Entrée</th><th class="n">Sortie</th><th>Raison</th><th class="n">Résultat</th></tr>
    {recents or "<tr><td colspan='7'>Pas encore de trade fermé.</td></tr>"}
  </table></div>
  <p class="note">Page refaite à chaque passage de l'IA (environ une fois par heure). Pour l'instant à la seconde, regarde l'onglet « Trading » de MetaTrader 5.</p>
</section>
</main>
"""


if __name__ == "__main__":
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    SORTIE.write_text(page(), encoding="utf-8")
    print(SORTIE)
