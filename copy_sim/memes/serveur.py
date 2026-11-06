"""Serveur web du test papier memecoins sur le VPS : sert le dossier de données en lecture (comme http.server) et
accepte en écriture, avec le jeton secret (en-tête X-Jeton, fichier « jeton » à côté de ce script), seulement les
fichiers des IA listés dans ECRITURE. Chaque fichier écrit est vérifié (taille, JSON valide, règle de l'IA bornée) ;
rien d'autre ne peut être écrit, et rien n'est exécuté.

Usage : python3 serveur.py --dir /opt/memes_paper/data --port 8787"""
import argparse
import hmac
import json
import math
import re
import sys
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import apprend  # noqa: E402

ECRITURE = re.compile(r"^(ia_regle\.json|ia_challengeuses\.json|ia_registre\.json|ia_demandes\.md|ia_carnet\.md|juge_lecons\.md|juge_idees\.json|juge_\d{4}-\d{2}-\d{2}(_\d{2})?\.json|juge2_\d{4}-\d{2}-\d{2}_\d{2}\.json|juge2_lecons\.md)$")
TAILLE_MAX = 64 * 1024
TAILLE_MAX_PAR_FICHIER = {"ia_registre.json": 512 * 1024}  # registre des hypothèses de la chercheuse (06/11)
# tableau commun des IA (01-02/11) : chacune y ajoute des observations, sans pouvoir effacer celles des autres
COMMUN, COMMUN_AJOUT_MAX, COMMUN_LIGNES_MAX = "commun.md", 2048, 400
AUTEURS = ("chercheuse", "juge", "juge2")
_verrou = threading.Lock()


PROMO_MIN_TRADES = 15  # tournoi (04/11) : trades fermés en direct exigés d'une challengeuse pour devenir la règle active


def promotion(rule, d):
    """Une nouvelle règle active n'est acceptée que si c'est la même stratégie que la règle active (simple changement
    de texte), ou une challengeuse (caisse defi_N du VPS) qui a au moins PROMO_MIN_TRADES trades fermés en direct, une
    moyenne positive et une moyenne meilleure que la règle active sur la même période. Renvoie None ou la raison du
    refus. C'est ce qui empêche de choisir une règle sur le passé seulement."""
    try:
        state = json.loads((Path(d) / "state.json").read_text())
    except (OSError, ValueError):
        return "état du VPS illisible, réessaie au prochain passage"
    cle = apprend.cle_regle(rule)
    active = state.get("ia")
    if active and apprend.cle_regle(active) == cle:
        return None
    for slot, defi in (state.get("defis") or {}).items():
        if defi.get("cle") != cle:
            continue
        b = (state.get("books") or {}).get(slot) or {}
        xs = [r["ret"] for r in b.get("closed", [])]
        if len(xs) < PROMO_MIN_TRADES:
            return f"{slot} n'a que {len(xs)} trades fermés en direct ({PROMO_MIN_TRADES} exigés)"
        m = sum(xs) / len(xs)
        if m <= 0:
            return f"{slot} perd en direct (moyenne {m:+.1%})"
        # 06/11 : avec jusqu'à 12 places, la meilleure gagne souvent par chance ; sa moyenne doit dépasser
        # sqrt(2 ln N) erreurs types (N = places en jeu), comme le seuil du banc
        n_places = max(1, len(state.get("defis") or {}))
        sd = (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5
        t = m / (sd / len(xs) ** 0.5) if sd > 0 else float("inf")
        seuil = max(1.0, math.sqrt(2 * math.log(n_places))) if n_places > 1 else 1.0
        if t < seuil:
            return (f"{slot} : moyenne {m:+.1%} à {t:.2f} erreurs types, il en faut {seuil:.2f} avec {n_places} places "
                    "en jeu (attends plus de trades)")
        champ_xs = [r["ret"] for r in (state.get("books") or {}).get("ia", {}).get("closed", [])
                    if r.get("t_in", 0) >= defi.get("debut", 0)]
        if len(champ_xs) >= 5 and m <= sum(champ_xs) / len(champ_xs):
            return f"{slot} ({m:+.1%}) ne bat pas la règle active sur la même période ({sum(champ_xs) / len(champ_xs):+.1%})"
        return None
    return "cette règle n'est pas une challengeuse en jeu : mets-la d'abord dans ia_challengeuses.json (voir MISSION.md)"


def verifier(name, body, d=None):
    """Renvoie le contenu à écrire, ou lève ValueError."""
    text = body.decode("utf-8")
    if name.endswith(".md"):
        return text
    data = json.loads(text)
    if name == "ia_regle.json":
        rule = apprend.regle_ia(data)
        if rule is None:
            raise ValueError("règle invalide (voir memes/ia/MISSION.md)")
        why = promotion(rule, d) if d is not None else None
        if why:
            raise ValueError(f"promotion refusée : {why}")
    if name == "ia_registre.json":
        if not isinstance(data, dict) or not isinstance(data.get("hypotheses"), list):
            raise ValueError('il faut {"hypotheses": [...]} (voir MISSION.md)')
    if name == "ia_challengeuses.json":
        cs = data.get("challengeuses") if isinstance(data, dict) else None
        if not isinstance(cs, list) or not 0 < len(cs) <= apprend.DEFIS_MAX:
            raise ValueError(f"il faut {{\"challengeuses\": [...]}} avec 1 à {apprend.DEFIS_MAX} entrées")
        for i, c in enumerate(cs):
            if not isinstance(c, dict) or apprend.regle_ia(c.get("regle")) is None:
                raise ValueError(f"challengeuse {i + 1} invalide (même format que ia_regle.json, dans \"regle\")")
    if name.startswith(("juge_2", "juge2_2")) and not (isinstance(data, dict) and "creneau" in data and "choix" in data):
        raise ValueError("choix du juge invalide")
    return json.dumps(data, ensure_ascii=False, indent=1)


class Handler(SimpleHTTPRequestHandler):
    jeton = ""

    def _ajouter_commun(self):
        """POST /ajouter/commun.md?auteur=<chercheuse|juge|juge2> : ajoute le texte (2 Ko au plus) en fin de tableau,
        daté et signé ; le tableau garde ses 400 dernières lignes. Personne ne peut réécrire ce qu'un autre a écrit."""
        auteur = (re.search(r"[?&]auteur=([a-z0-9]+)", self.path) or [None, ""])[1]
        if auteur not in AUTEURS:
            return self.send_error(400, "auteur inconnu")
        n = int(self.headers.get("Content-Length") or 0)
        if not 0 < n <= COMMUN_AJOUT_MAX:
            return self.send_error(413, "taille invalide (2 Ko au plus)")
        try:
            texte = self.rfile.read(n).decode("utf-8").strip()
        except UnicodeDecodeError:
            return self.send_error(400, "texte invalide")
        path = Path(self.directory) / COMMUN
        entete = f"### {time.strftime('%d/%m %H:%M', time.gmtime())} UTC — {auteur}"
        with _verrou:
            old = path.read_text(encoding="utf-8").splitlines() if path.exists() else ["# Tableau commun des IA"]
            lignes = (old + ["", entete] + texte.splitlines())[-COMMUN_LIGNES_MAX:]
            tmp = path.with_suffix(".tmp")
            tmp.write_text("\n".join(lignes) + "\n", encoding="utf-8")
            tmp.replace(path)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok\n")

    def do_POST(self):
        if self.path.startswith("/ajouter/"):
            if not self.jeton or not hmac.compare_digest(self.headers.get("X-Jeton", ""), self.jeton):
                return self.send_error(403, "jeton invalide")
            if not re.match(r"^/ajouter/commun\.md(\?|$)", self.path):
                return self.send_error(404, "fichier non autorisé")
            return self._ajouter_commun()
        m = re.match(r"^/ecrire/([^/?#]+)$", self.path)
        if not m or not ECRITURE.match(m.group(1)):
            return self.send_error(404, "fichier non autorisé")
        if not self.jeton or not hmac.compare_digest(self.headers.get("X-Jeton", ""), self.jeton):
            return self.send_error(403, "jeton invalide")
        n = int(self.headers.get("Content-Length") or 0)
        if not 0 < n <= TAILLE_MAX_PAR_FICHIER.get(m.group(1), TAILLE_MAX):
            return self.send_error(413, "taille invalide")
        try:
            content = verifier(m.group(1), self.rfile.read(n), self.directory)
        except (ValueError, UnicodeDecodeError) as exc:
            return self.send_error(400, str(exc)[:200])
        path = Path(self.directory) / m.group(1)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--port", type=int, default=8787)
    a = ap.parse_args()
    jf = Path(__file__).resolve().parent / "jeton"
    Handler.jeton = jf.read_text().strip() if jf.exists() else ""
    ThreadingHTTPServer(("", a.port), partial(Handler, directory=a.dir)).serve_forever()


if __name__ == "__main__":
    main()
