"""Tableau de bord en direct du robot du labo, sur le PC de Baptiste. LECTURE SEULE.

Serveur web sur 127.0.0.1 seulement (port 8765, ou le suivant libre), lancé dans le processus du pont : il partage
sa connexion au terminal et son verrou. Aucune route n'agit : pas d'ordre, pas de réglage ; GET seulement.
Rien d'identifiant n'est servi (ni compte, ni serveur, ni nom).

Seul pour essayer (sans le pont) :  python tableau_bord.py   puis http://127.0.0.1:8765/
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

import pont_mt5 as pont

SYMBOLE = "XAUUSD"
PORTS = range(8765, 8771)
DEBUT_HISTO = datetime(2026, 11, 10)
PARIS = ZoneInfo("Europe/Paris")
ICI = Path(__file__).resolve().parent


class Lecteur:
    """Construit l'instantané JSON, avec des caches pour rester léger (au plus une lecture MT5 par seconde)."""

    def __init__(self, mt5, lanceur=None, racine_robot: Path | None = None):
        self.mt5, self.lanceur = mt5, lanceur
        self.racine = racine_robot or (lanceur.racine if lanceur else pont.ICI / "robot")
        self.decalage = 7200            # heure du serveur - UTC, en secondes (recalculé quand le prix est frais)
        self._cache, self._t_cache = None, 0.0
        self._deals, self._t_deals = [], 0.0
        self._garde, self._t_garde = None, 0.0
        self._verrou = threading.Lock()

    # ------------------------------------------------------------ outils
    def _serveur_vers_utc(self, t: float) -> float:
        return t - self.decalage

    def _debut_jour_serveur(self) -> float:
        debut = datetime.now(PARIS).replace(hour=0, minute=0, second=0, microsecond=0)
        return debut.timestamp() + self.decalage

    def _etat_robot(self) -> dict:
        if self.lanceur is not None:
            return self.lanceur.etat()
        e = pont.lire_json(self.racine / "lanceur.json", {})
        return {"version_installee": e.get("installee"), "en_marche": None, "dernier_refus": e.get("dernier_refus"),
                "derniere_erreur": e.get("derniere_erreur")}

    def _sorties_prevues(self, version) -> dict:
        """ticket -> heure de sortie prévue (heure du serveur), si le robot la note dans son fichier d'état."""
        prevues = {}
        if version is None:
            return prevues
        for f in (self.racine / f"v{version}").glob("*.json"):
            d = pont.lire_json(f, {})
            ouvert = d.get("ouvert") if isinstance(d, dict) else None
            if isinstance(ouvert, dict):
                for o in ouvert.values():
                    if isinstance(o, dict) and isinstance(o.get("ticket"), int) and pont.nombre(o.get("sortie")):
                        prevues[o["ticket"]] = o["sortie"]
        return prevues

    # ------------------------------------------------------------ lectures MT5 (sous le verrou du pont)
    def _deals_robot(self) -> list:
        if time.time() - self._t_deals < 5:
            return self._deals
        with pont.VERROU:
            deals = self.mt5.history_deals_get(DEBUT_HISTO, datetime.now() + timedelta(days=2)) or ()
        ids = {d.position_id for d in deals if d.magic == pont.MAGIQUE_ROBOT}
        self._deals = [d for d in deals if d.position_id in ids]
        self._t_deals = time.time()
        return self._deals

    def _garde_fou(self):
        if time.time() - self._t_garde >= 10 or self._garde is None:
            with pont.VERROU:
                g = pont.garde_jour(self.mt5)
            self._garde = {"perte_du_jour": g["perte"], "seuil": -round(pont.PERTE_MAX_JOUR * g["base"], 2),
                           "ouvertures_bloquees": g["bloque"]}
            self._t_garde = time.time()
        return self._garde

    def _trades(self, ouvertes: set) -> list:
        par_pos = {}
        for d in self._deals_robot():
            par_pos.setdefault(d.position_id, []).append(d)
        trades = []
        for pid, ds in par_pos.items():
            if pid in ouvertes:
                continue
            entrees = [d for d in ds if d.entry == 0]
            sorties = [d for d in ds if d.entry in (1, 3)]
            if not entrees or not sorties:
                continue
            e, s = entrees[0], max(sorties, key=lambda d: d.time_msc)
            commentaire = e.comment or ""
            fin = (s.comment or "").lower()
            raison = "stop" if "sl" in fin else ("objectif" if "tp" in fin else "robot")
            trades.append({
                "hypothese": commentaire[6:] if commentaire.startswith("robot:") else "?",
                "sens": "achat" if e.type == 0 else "vente", "lots": e.volume, "entree": e.price, "sortie": s.price,
                "ouverture": e.time, "fermeture": s.time, "raison": raison,
                "resultat": round(sum(d.profit + d.swap + d.commission + getattr(d, "fee", 0.0) for d in ds), 2)})
        trades.sort(key=lambda t: t["fermeture"], reverse=True)
        return trades

    @staticmethod
    def _stats(trades: list) -> dict:
        n = len(trades)
        total = round(sum(t["resultat"] for t in trades), 2)
        gagnants = sum(1 for t in trades if t["resultat"] > 0)
        return {"trades": n, "total": total, "moyenne": round(total / n, 2) if n else None,
                "gagnants_pct": round(100 * gagnants / n) if n else None}

    def _construire(self) -> dict:
        m = self.mt5
        with pont.VERROU:
            info, arret = pont.compte_demo(m)
            t = m.symbol_info_tick(SYMBOLE)
            si = m.symbol_info(SYMBOLE)
            barres = m.copy_rates_from_pos(SYMBOLE, m.TIMEFRAME_M1, 0, 60)
            jour = m.copy_rates_from_pos(SYMBOLE, m.TIMEFRAME_D1, 0, 1)
            positions = [p for p in (m.positions_get() or []) if p.magic == pont.MAGIQUE_ROBOT]
        if t is None or si is None:
            raise RuntimeError(f"pas de prix pour {SYMBOLE}")
        age = time.time() - (t.time - self.decalage)
        brut = t.time - time.time()
        if abs(brut - round(brut / 900) * 900) < 60:           # prix frais : on recale le décalage du serveur
            self.decalage = int(round(brut / 900) * 900)
            age = time.time() - (t.time - self.decalage)
        ouverture_jour = float(jour[0]["open"]) if jour is not None and len(jour) else None
        robot = self._etat_robot()
        prevues = self._sorties_prevues(robot.get("version_installee"))
        trades = self._trades({p.ticket for p in positions})
        debut = self._debut_jour_serveur()
        aujourd_hui = [x for x in trades if x["fermeture"] >= debut]
        en_cours = round(sum(p.profit + p.swap for p in positions), 2)
        hyps = sorted({x["hypothese"] for x in trades} | {p.comment[6:] for p in positions
                                                          if (p.comment or "").startswith("robot:")})
        par_hyp = [{"hypothese": h, "jour": self._stats([x for x in aujourd_hui if x["hypothese"] == h]),
                    "debut": self._stats([x for x in trades if x["hypothese"] == h])} for h in hyps]
        bornes = (barres[0]["time"], barres[-1]["time"] + 60) if barres is not None and len(barres) else (0, 0)
        marques = []
        for d in self._deals_robot():
            if bornes[0] <= d.time < bornes[1] and d.symbol == SYMBOLE:
                marques.append({"heure": d.time, "prix": d.price, "type": "entree" if d.entry == 0 else "sortie",
                                "sens": "achat" if d.type == 0 else "vente"})
        return {
            "ecrit": time.time(), "symbole": SYMBOLE, "decalage_serveur": self.decalage,
            "compte_demo": arret is None, "arret": arret, "stop_pont": pont.FICHIER_STOP.exists(),
            "prix": {"bid": t.bid, "ask": t.ask, "spread_points": round((t.ask - t.bid) / si.point),
                     "heure_serveur": t.time, "age_s": round(age), "chiffres": si.digits,
                     "ouverture_jour": ouverture_jour,
                     "variation": round(t.bid - ouverture_jour, si.digits) if ouverture_jour else None,
                     "variation_pct": round(100 * (t.bid / ouverture_jour - 1), 3) if ouverture_jour else None},
            "bougies": [[int(b["time"]), float(b["open"]), float(b["high"]), float(b["low"]), float(b["close"])]
                        for b in (barres if barres is not None else [])],
            "marques": marques,
            "positions": [{
                "hypothese": p.comment[6:] if (p.comment or "").startswith("robot:") else "?",
                "sens": "achat" if p.type == m.POSITION_TYPE_BUY else "vente", "lots": p.volume,
                "entree": p.price_open, "prix": p.price_current, "stop": p.sl or None, "objectif": p.tp or None,
                "resultat": round(p.profit + p.swap, 2), "ouverture": p.time,
                "reste_s": round(prevues[p.ticket] - t.time) if p.ticket in prevues else None}
                for p in sorted(positions, key=lambda p: p.time)],
            "jour": {"date": datetime.now(PARIS).strftime("%d/%m/%Y"), **self._stats(aujourd_hui),
                     "en_cours": en_cours, "garde_fou": self._garde_fou() if info is not None else None},
            "robot": {k: robot.get(k) for k in ("version_installee", "en_marche", "dernier_refus", "derniere_erreur")},
            "par_hypothese": par_hyp,
            "derniers": trades[:20],
        }

    def instantane(self) -> bytes:
        with self._verrou:
            if self._cache is None or time.time() - self._t_cache >= 0.9:
                try:
                    d = self._construire()
                except Exception as e:   # le tableau de bord ne doit jamais gêner le pont
                    d = {"erreur": f"{type(e).__name__}: {e}"[:200], "ecrit": time.time()}
                self._cache, self._t_cache = json.dumps(d, default=str).encode(), time.time()
            return self._cache


# ------------------------------------------------------------------ serveur web (GET seulement)

FICHIERS = {"/": ("tableau_bord.html", "text/html; charset=utf-8"),
            "/app.js": ("tableau_bord.js", "application/javascript; charset=utf-8")}

# ------------------------------------------------------------------ copie publique, pour le téléphone (hors de chez soi)
# Chaque minute, l'instantané (déjà sans identifiant) part sur la branche `mt5-direct` du dépôt : UN seul commit sans
# parent, remplacé à chaque fois (la branche ne grossit pas, la branche de travail n'est pas touchée). La même page
# (index.html + app.js) y est jointe ; elle lit direct.json depuis GitHub.
BRANCHE_DIRECT = "mt5-direct"
PERIODE_DIRECT = 60


def _publier_direct(lecteur: Lecteur) -> None:
    dossier = ICI / "direct"
    dossier.mkdir(exist_ok=True)
    (dossier / "direct.json").write_bytes(lecteur.instantane())
    lignes = []
    for nom, source in (("direct.json", dossier / "direct.json"), ("index.html", ICI / "tableau_bord.html"),
                        ("app.js", ICI / "tableau_bord.js")):
        code, sha, err = pont.git("hash-object", "-w", str(source))
        if code != 0:
            raise RuntimeError("git hash-object : " + err)
        lignes.append(f"100644 blob {sha.strip()}\t{nom}")
    # séparateur nul (-z) : Windows ne transforme pas les fins de ligne envoyées à git
    (dossier / "arbre.txt").write_text("\0".join(lignes) + "\0", encoding="utf-8", newline="")
    code, arbre, err = pont.git("mktree", "-z", "--missing", entree=dossier / "arbre.txt")
    if code != 0:
        raise RuntimeError("git mktree : " + err)
    code, commit, err = pont.git("commit-tree", arbre.strip(), "-m", "tableau de bord : instantane")
    if code != 0:
        raise RuntimeError("git commit-tree : " + err)
    code, _, err = pont.git("push", "-q", "-f", "origin", f"{commit.strip()}:refs/heads/{BRANCHE_DIRECT}", timeout=60)
    if code != 0:
        raise RuntimeError("git push : " + err)


def _boucle_direct(lecteur: Lecteur) -> None:
    erreurs = 0
    while True:
        debut = time.time()
        try:
            _publier_direct(lecteur)
            erreurs = 0
        except Exception as e:
            erreurs += 1
            if erreurs in (1, 10) or erreurs % 60 == 0:      # pas un message par minute si GitHub est injoignable
                pont.log.warning("tableau de bord, copie publique : %s", str(e)[:200])
        time.sleep(max(5.0, PERIODE_DIRECT - (time.time() - debut)))


def _gestionnaire(lecteur: Lecteur, port: int):
    hotes = {f"127.0.0.1:{port}", f"localhost:{port}"}

    class G(BaseHTTPRequestHandler):
        server_version = "TableauBord"
        sys_version = ""

        def log_message(self, *a):
            pass

        def _envoyer(self, code, corps: bytes, type_="text/plain; charset=utf-8"):
            self.send_response(code)
            self.send_header("Content-Type", type_)
            self.send_header("Content-Length", str(len(corps)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'")
            self.end_headers()
            self.wfile.write(corps)

        def do_GET(self):
            if self.headers.get("Host") not in hotes:          # contre les sites qui viseraient 127.0.0.1
                return self._envoyer(403, b"interdit")
            chemin = self.path.split("?")[0]
            if chemin == "/donnees":
                return self._envoyer(200, lecteur.instantane(), "application/json")
            if chemin in FICHIERS:
                nom, type_ = FICHIERS[chemin]
                return self._envoyer(200, (ICI / nom).read_bytes(), type_)
            return self._envoyer(404, b"introuvable")

        def _refus(self):
            self._envoyer(405, b"lecture seule")

        do_POST = do_PUT = do_DELETE = do_PATCH = _refus

    return G


def demarrer(mt5, lanceur=None, racine_robot: Path | None = None, direct: bool = True) -> int | None:
    """Lance le serveur dans un fil à part (et la copie publique pour le téléphone). Renvoie le port."""
    lecteur = Lecteur(mt5, lanceur, racine_robot)
    if direct:
        threading.Thread(target=_boucle_direct, args=(lecteur,), daemon=True, name="tableau_bord_direct").start()
    for port in PORTS:
        try:
            serveur = ThreadingHTTPServer(("127.0.0.1", port), _gestionnaire(lecteur, port))
        except OSError:
            continue
        serveur.daemon_threads = True
        threading.Thread(target=serveur.serve_forever, daemon=True, name="tableau_bord").start()
        (ICI / "tableau_bord.adresse").write_text(f"http://127.0.0.1:{port}/\n", encoding="utf-8")
        pont.log.info("tableau de bord : http://127.0.0.1:%d/", port)
        return port
    pont.log.error("tableau de bord : aucun port libre entre %d et %d", PORTS[0], PORTS[-1])
    return None


if __name__ == "__main__":
    import MetaTrader5 as mt5_reel
    if not mt5_reel.initialize():
        raise SystemExit("MT5 injoignable")
    p = demarrer(mt5_reel, None, Path.home() / "pont_mt5" / "robot", direct=False)
    print(f"Tableau de bord : http://127.0.0.1:{p}/  (Ctrl+C pour arreter)")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
