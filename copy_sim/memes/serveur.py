"""Serveur web du test papier memecoins sur le VPS : sert le dossier de données en lecture (comme http.server) et
accepte en écriture, avec le jeton secret (en-tête X-Jeton, fichier « jeton » à côté de ce script), seulement les
fichiers des IA listés dans ECRITURE. Chaque fichier écrit est vérifié (taille, JSON valide, règle de l'IA bornée) ;
rien d'autre ne peut être écrit, et rien n'est exécuté.

Usage : python3 serveur.py --dir /opt/memes_paper/data --port 8787"""
import argparse
import hmac
import json
import re
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import apprend  # noqa: E402

ECRITURE = re.compile(r"^(ia_regle\.json|ia_carnet\.md|juge_lecons\.md|juge_idees\.json|juge_\d{4}-\d{2}-\d{2}(_\d{2})?\.json)$")
TAILLE_MAX = 64 * 1024


def verifier(name, body):
    """Renvoie le contenu à écrire, ou lève ValueError."""
    text = body.decode("utf-8")
    if name.endswith(".md"):
        return text
    data = json.loads(text)
    if name == "ia_regle.json" and apprend.regle_ia(data) is None:
        raise ValueError("règle invalide (voir memes/ia/MISSION.md)")
    if name.startswith("juge_2") and not (isinstance(data, dict) and "creneau" in data and "choix" in data):
        raise ValueError("choix du juge invalide")
    return json.dumps(data, ensure_ascii=False, indent=1)


class Handler(SimpleHTTPRequestHandler):
    jeton = ""

    def do_POST(self):
        m = re.match(r"^/ecrire/([^/?#]+)$", self.path)
        if not m or not ECRITURE.match(m.group(1)):
            return self.send_error(404, "fichier non autorisé")
        if not self.jeton or not hmac.compare_digest(self.headers.get("X-Jeton", ""), self.jeton):
            return self.send_error(403, "jeton invalide")
        n = int(self.headers.get("Content-Length") or 0)
        if not 0 < n <= TAILLE_MAX:
            return self.send_error(413, "taille invalide")
        try:
            content = verifier(m.group(1), self.rfile.read(n))
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
