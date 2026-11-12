// Tableau de bord en direct : lit /donnees chaque seconde. Aucune action possible.
"use strict";
let decalage = 7200, chiffres = 2;

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const nb = (x, d = 2) => (x === null || x === undefined) ? "–" : Number(x).toLocaleString("fr-FR", { minimumFractionDigits: d, maximumFractionDigits: d });
const usd = (x) => (x === null || x === undefined) ? "–" : (x > 0 ? "+" : "") + nb(x) + " $";
const cls = (x) => x > 0 ? "pos" : (x < 0 ? "neg" : "");
const heure = (tServeur, sec = false) => new Date((tServeur - decalage) * 1000).toLocaleTimeString("fr-FR",
  { timeZone: "Europe/Paris", hour: "2-digit", minute: "2-digit", second: sec ? "2-digit" : undefined });
const jourHeure = (tServeur) => new Date((tServeur - decalage) * 1000).toLocaleString("fr-FR",
  { timeZone: "Europe/Paris", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
const duree = (s) => s === null || s === undefined ? "–" : (s < 0 ? "dépassée" :
  (s >= 3600 ? Math.floor(s / 3600) + " h " + String(Math.floor(s % 3600 / 60)).padStart(2, "0") :
  Math.floor(s / 60) + " min " + String(s % 60).padStart(2, "0")));

function table(el, entetes, lignes, vide) {
  if (!lignes.length) { el.innerHTML = `<tr><td class="vide">${esc(vide)}</td></tr>`; return; }
  el.innerHTML = "<tr>" + entetes.map((h) => `<th>${esc(h)}</th>`).join("") + "</tr>" +
    lignes.map((l) => "<tr>" + l.join("") + "</tr>").join("");
}
const td = (v, c = "") => `<td class="${c}">${v}</td>`;

function graphique(bougies, marques) {
  const svg = $("graphique");
  const L = svg.clientWidth || 700, H = 280, g = 8, d = 58, bas = 22;
  if (!bougies.length) { svg.innerHTML = ""; return; }
  let lo = Math.min(...bougies.map((b) => b[3])), hi = Math.max(...bougies.map((b) => b[2]));
  marques.forEach((m) => { lo = Math.min(lo, m.prix); hi = Math.max(hi, m.prix); });
  const marge = (hi - lo) * 0.06 || 1; lo -= marge; hi += marge;
  const n = bougies.length, pas = (L - g - d) / n, t0 = bougies[0][0];
  const y = (p) => g + (hi - p) / (hi - lo) * (H - g - bas);
  const x = (t) => g + ((t - t0) / 60 + 0.5) * pas;
  const css = getComputedStyle(document.documentElement);
  const C = (v) => css.getPropertyValue(v).trim();
  let s = "";
  for (let i = 0; i <= 4; i++) {
    const p = lo + (hi - lo) * i / 4, yy = y(p);
    s += `<line x1="${g}" x2="${L - d}" y1="${yy}" y2="${yy}" stroke="${C("--grille")}"/>` +
         `<text x="${L - d + 6}" y="${yy + 4}" font-size="11" fill="${C("--doux")}">${nb(p, chiffres)}</text>`;
  }
  bougies.forEach((b, i) => {
    const [t, o, h, l, c] = b, xx = x(t), coul = c >= o ? C("--vert") : C("--rouge");
    const w = Math.max(1, pas * 0.6);
    s += `<line x1="${xx}" x2="${xx}" y1="${y(h)}" y2="${y(l)}" stroke="${coul}"/>` +
         `<rect x="${xx - w / 2}" y="${Math.min(y(o), y(c))}" width="${w}" height="${Math.max(1, Math.abs(y(o) - y(c)))}" fill="${coul}"/>`;
    if (i % 10 === 0) s += `<text x="${xx}" y="${H - 6}" font-size="11" text-anchor="middle" fill="${C("--doux")}">${heure(t)}</text>`;
  });
  marques.forEach((m) => {
    const xx = x(Math.floor(m.heure / 60) * 60), yy = y(m.prix);
    if (m.type === "entree") {
      const haut = m.sens === "achat";
      const pts = haut ? `${xx},${yy - 7} ${xx - 6},${yy + 4} ${xx + 6},${yy + 4}` : `${xx},${yy + 7} ${xx - 6},${yy - 4} ${xx + 6},${yy - 4}`;
      s += `<polygon points="${pts}" fill="${haut ? C("--vert") : C("--rouge")}" stroke="${C("--carte")}" stroke-width="1"/>`;
    } else {
      s += `<circle cx="${xx}" cy="${yy}" r="4.5" fill="${C("--accent")}" stroke="${C("--carte")}" stroke-width="1"/>`;
    }
  });
  svg.setAttribute("viewBox", `0 0 ${L} ${H}`);
  svg.innerHTML = s;
}

function afficher(D) {
  decalage = D.decalage_serveur ?? decalage;
  const P = D.prix; chiffres = P.chiffres ?? 2;
  $("bid").textContent = nb(P.bid, chiffres);
  $("ask").textContent = nb(P.ask, chiffres);
  $("spread").textContent = P.spread_points + " points";
  $("variation").innerHTML = P.variation === null ? "–" :
    `<span class="${cls(P.variation)}">${P.variation > 0 ? "+" : ""}${nb(P.variation, chiffres)} (${P.variation_pct > 0 ? "+" : ""}${nb(P.variation_pct, 2)} %)</span>`;
  P.age_s = Math.max(0, Math.round(Date.now() / 1000 - (P.heure_serveur - decalage)));   // âge réel, même sur la copie
  $("age").textContent = P.age_s <= 5 ? "à l'instant" : (P.age_s < 120 ? `il y a ${P.age_s} s` : `il y a ${Math.round(P.age_s / 60)} min (marché fermé ?)`);
  graphique(D.bougies, D.marques);

  const J = D.jour;
  $("date").textContent = J.date;
  $("j-trades").textContent = J.trades;
  $("j-total").innerHTML = `<span class="${cls(J.total)}">${usd(J.total)}</span>`;
  $("j-gagnants").textContent = J.gagnants_pct === null ? "–" : J.gagnants_pct + " %";
  $("j-encours").innerHTML = `<span class="${cls(J.en_cours)}">${usd(J.en_cours)}</span>`;
  $("j-garde").innerHTML = J.garde_fou ? `<span class="${cls(J.garde_fou.perte_du_jour)}">${usd(J.garde_fou.perte_du_jour)}</span> / ${usd(J.garde_fou.seuil)}` +
    (J.garde_fou.ouvertures_bloquees ? ' <b class="neg">bloqué</b>' : "") : "–";

  table($("positions"), ["Hypothèse", "Sens", "Lots", "Entrée", "Prix", "Stop", "En cours", "Ouverte", "Sortie dans"],
    D.positions.map((p) => [td(esc(p.hypothese)), td(p.sens), td(nb(p.lots)), td(nb(p.entree, chiffres)),
      td(nb(p.prix, chiffres)), td(nb(p.stop, chiffres)), td(usd(p.resultat), cls(p.resultat)),
      td(heure(p.ouverture)), td(duree(p.reste_s))]), "Aucune position ouverte.");

  const R = D.robot;
  $("r-version").textContent = R.version_installee ?? "aucune";
  $("r-marche").innerHTML = R.en_marche === null ? "–" : (R.en_marche ? '<span class="pos">oui</span>' : '<span class="neg">non</span>');
  $("r-erreur").textContent = R.derniere_erreur ? R.derniere_erreur.message || "oui" : "aucune";
  $("r-refus").textContent = R.dernier_refus ? `v${R.dernier_refus.version} : ${R.dernier_refus.raison}` : "aucun";

  table($("hypotheses"), ["Hypothèse", "Auj. trades", "Auj. total", "Auj. moy.", "Auj. gagn.", "Total trades", "Total", "Moyenne", "Gagnants"],
    D.par_hypothese.map((h) => [td(esc(h.hypothese)), td(h.jour.trades), td(usd(h.jour.total), cls(h.jour.total)),
      td(usd(h.jour.moyenne), cls(h.jour.moyenne)), td(h.jour.gagnants_pct === null ? "–" : h.jour.gagnants_pct + " %"),
      td(h.debut.trades), td(usd(h.debut.total), cls(h.debut.total)), td(usd(h.debut.moyenne), cls(h.debut.moyenne)),
      td(h.debut.gagnants_pct === null ? "–" : h.debut.gagnants_pct + " %")]), "Aucun trade pour l'instant.");

  table($("derniers"), ["Hypothèse", "Sens", "Lots", "Entrée", "Sortie", "Ouvert", "Fermé", "Fin", "Résultat"],
    D.derniers.map((t) => [td(esc(t.hypothese)), td(t.sens), td(nb(t.lots)), td(nb(t.entree, chiffres)),
      td(nb(t.sortie, chiffres)), td(jourHeure(t.ouverture)), td(jourHeure(t.fermeture)), td(t.raison),
      td(usd(t.resultat), cls(t.resultat))]), "Aucun trade fermé pour l'instant.");

  const alertes = [];
  if (!D.compte_demo) alertes.push("Compte non démo ou terminal déconnecté : " + (D.arret || ""));
  if (D.stop_pont) alertes.push("STOP_PONT présent : plus aucun ordre, robot arrêté.");
  $("alerte").style.display = alertes.length ? "block" : "none";
  $("alerte").textContent = alertes.join(" ");
}

// En local (PC) : /donnees chaque seconde. Ailleurs (téléphone) : l'instantané publié chaque minute sur GitHub.
const LOCAL = ["127.0.0.1", "localhost"].includes(location.hostname);
const DEPOT = "liitlec/Copybot-Crypto", BRANCHE = "mt5-direct";
const API = `https://api.github.com/repos/${DEPOT}/contents/direct.json?ref=${BRANCHE}`;
const BRUT = `https://raw.githubusercontent.com/${DEPOT}/${BRANCHE}/direct.json`;
let dernier = null;

async function lire() {
  if (LOCAL) return (await fetch("/donnees", { cache: "no-store" })).json();
  try {   // l'API de GitHub n'a pas de cache (60 lectures par heure et par adresse)
    const r = await fetch(API, { cache: "no-store", headers: { Accept: "application/vnd.github.raw+json" } });
    if (r.ok) return r.json();
  } catch (e) { /* on tente la copie brute */ }
  const r = await fetch(BRUT + "?t=" + Date.now(), { cache: "no-store" });   // peut avoir jusqu'à 5 min de retard
  if (!r.ok) throw new Error("GitHub " + r.status);
  return r.json();
}

function etat() {
  if (!dernier) return;
  const age = Math.max(0, Math.round(Date.now() / 1000 - dernier));
  const txt = LOCAL ? `en direct · ${heure(Date.now() / 1000 + decalage, true)}`
    : `mis à jour il y a ${age < 120 ? age + " s" : Math.round(age / 60) + " min"}`;
  $("etat").innerHTML = `<span class="pastille${age > 300 ? " off" : ""}"></span>${txt}`;
}

async function boucle() {
  try {
    const D = await lire();
    if (D.erreur) throw new Error(D.erreur);
    afficher(D);
    dernier = D.ecrit;
    etat();
  } catch (e) {
    $("etat").innerHTML = `<span class="pastille off"></span>pas de données (${esc(e.message).slice(0, 80)})`;
  }
  setTimeout(boucle, LOCAL ? 1000 : 65000);
}
if (!LOCAL) {
  $("mode").textContent = "Lecture seule · démo · copie mise à jour chaque minute";
  setInterval(etat, 1000);
}
boucle();
