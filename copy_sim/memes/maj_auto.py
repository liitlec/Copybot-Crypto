"""Mise à jour automatique du code de RECHERCHE du test papier (06/11, demandée par l'utilisateur : « que je n'aie pas
besoin de valider »). Lancé toutes les 10 min par memes-maj.timer, sous l'utilisateur « memes » (aucun droit root).

1. Lit copy_sim/memes/AUTO_VERSION sur la branche (« <numéro> <commit> » ; le numéro doit dépasser celui en place).
2. Si c'est nouveau : télécharge À CE COMMIT seulement les fichiers de AUTO_FICHIERS (jamais reel.py, serveur.py,
   installer.sh ni ce script, qui restent sous la validation de l'utilisateur), les compile, puis lance le test hors
   ligne du même commit (tests/test_cycle.py : 14 cycles simulés, sans réseau). Un échec = version refusée, rien ne
   change.
3. Sinon, garde une copie de la version en place, installe la nouvelle et demande au papier de redémarrer entre deux
   cycles (data/REDEMARRER) ; le serveur web est relancé.
4. Aux passages suivants : si le papier relancé n'a pas fini un cycle (status.md) ou si le serveur web ne répond pas
   dans les 20 min, ou si erreurs.log a pris plus de 20 lignes,
   retour automatique à la version précédente, et ce commit n'est plus jamais réessayé.

Le portefeuille du test réel n'est pas accessible d'ici (autre utilisateur, autre dossier). Journal : data/maj_auto.log."""
import json
import os
import py_compile
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

D = Path(os.environ.get("MEMES_DIR", "/opt/memes_paper"))
DATA = D / "data"
MAJ = D / "maj"
DEPOT = os.environ.get("MEMES_DEPOT", "https://raw.githubusercontent.com/liitlec/Copybot-Crypto")  # autre adresse : tests seulement
BRANCHE = "claude/polymarket-weather-sigma-resolution-olv0bs"
AUTO_FICHIERS = ("memes_paper.py", "apprend.py", "memes_page.py", "flux.py")
TEST = "tests/test_cycle.py"
DELAI_SANTE_S, ERREURS_MAX = 20 * 60, 20
UA = {"User-Agent": "memes-maj/1.0"}


def journal(msg):
    with (DATA / "maj_auto.log").open("a") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}\n")


def lire(url, timeout=30):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def etat():
    try:
        return json.loads((MAJ / "etat.json").read_text())
    except (OSError, ValueError):
        return {}


def sauver(e):
    MAJ.mkdir(exist_ok=True)
    tmp = MAJ / "etat.tmp"
    tmp.write_text(json.dumps(e, indent=1))
    tmp.replace(MAJ / "etat.json")


def relancer():
    (DATA / "REDEMARRER").write_text(str(time.time()))  # le papier s'arrête proprement entre deux cycles
    try:  # le serveur web n'a pas d'état : relancé tout de suite (systemd le redémarre)
        out = subprocess.run(["pgrep", "-u", str(os.getuid()), "-f", f"{D}/serveur.py"], capture_output=True, text=True)
        for pid in out.stdout.split():
            os.kill(int(pid), signal.SIGTERM)
    except Exception as exc:
        journal(f"relance du serveur web impossible : {exc!r}")


def lignes(p):
    try:
        with open(p, "rb") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def verifier_sante(e):
    """Après une installation : santé du papier, retour en arrière si besoin."""
    c = e.get("en_cours")
    if not c:
        return
    def mtime(p):
        try:
            return p.stat().st_mtime
        except OSError:
            return 0
    dem = mtime(DATA / "demarrage")  # écrit par memes_paper.py à chaque lancement
    try:
        lire("http://127.0.0.1:8787/status.md", timeout=10)
        web = True
    except Exception:
        web = False
    trop_erreurs = lignes(DATA / "erreurs.log") - c["erreurs"] > ERREURS_MAX
    if dem > c["t"] and mtime(DATA / "status.md") > dem and web and not trop_erreurs:
        journal(f"{c['version'][:7]} en service, cycle sain")
        e.pop("en_cours")
        sauver(e)
        return
    if time.time() - c["t"] < DELAI_SANTE_S and not trop_erreurs:
        return
    prec = MAJ / "precedent"
    for f in AUTO_FICHIERS:
        if (prec / f).exists():
            shutil.copy2(prec / f, D / f)
    e.setdefault("refusees", []).append(c["version"])
    e["version"] = c.get("ancienne")
    e.pop("en_cours")
    sauver(e)
    relancer()
    journal(f"{c['version'][:7]} RETIRÉE ({'trop d’erreurs' if trop_erreurs else 'aucun cycle en 20 min'}) : "
            f"retour à {str(c.get('ancienne'))[:7]}")


def main():
    if os.geteuid() == 0:
        sys.exit("à lancer sous l'utilisateur memes, jamais en root")
    MAJ.mkdir(exist_ok=True)
    e = etat()
    verifier_sante(e)
    if e.get("en_cours"):
        return
    try:  # « <numéro> <commit> » : le numéro ne fait que monter, pour ne jamais revenir sous l'installation manuelle
        brut = lire(f"{DEPOT}/{BRANCHE}/copy_sim/memes/AUTO_VERSION").decode().split()
        seq, v = int(brut[0]), brut[1]
    except Exception as exc:
        return journal(f"AUTO_VERSION illisible : {exc!r}")
    if len(v) != 40 or not all(ch in "0123456789abcdef" for ch in v):
        return journal(f"AUTO_VERSION invalide : {v[:60]!r}")
    if seq <= e.get("seq", 0) or v == e.get("version") or v in e.get("refusees", []):
        return
    neuf = MAJ / v
    shutil.rmtree(neuf, ignore_errors=True)
    (neuf / "tests").mkdir(parents=True)
    try:
        for f in AUTO_FICHIERS + (TEST,):
            (neuf / f).write_bytes(lire(f"{DEPOT}/{v}/copy_sim/memes/{f}"))
        for f in AUTO_FICHIERS:
            py_compile.compile(str(neuf / f), doraise=True)
    except Exception as exc:
        shutil.rmtree(neuf, ignore_errors=True)
        return journal(f"{v[:7]} non téléchargée ou ne compile pas : {exc!r}"[:400])
    # le test du commit, sur les fichiers du commit, sans réseau ; les autres modules (reel, serveur…) n'y sont pas
    sortie = neuf / "essai"
    try:
        r = subprocess.run([sys.executable, str(neuf / TEST), str(sortie)], cwd=str(neuf), capture_output=True,
                           text=True, timeout=600, env={"PATH": "/usr/bin:/bin", "MEMES_SRC": str(neuf)})
        ok = r.returncode == 0 and "TEST OK" in r.stdout
        detail = (r.stdout + r.stderr)[-300:]
    except subprocess.TimeoutExpired:
        ok, detail = False, "test trop long (10 min)"
    if not ok:
        e.setdefault("refusees", []).append(v)
        sauver(e)
        shutil.rmtree(neuf, ignore_errors=True)
        return journal(f"{v[:7]} REFUSÉE par son test : {detail!r}")
    prec = MAJ / "precedent"
    shutil.rmtree(prec, ignore_errors=True)
    prec.mkdir()
    for f in AUTO_FICHIERS:
        if (D / f).exists():
            shutil.copy2(D / f, prec / f)
    for f in AUTO_FICHIERS:
        tmp = D / f"{f}.maj"
        shutil.copy2(neuf / f, tmp)
        tmp.replace(D / f)
    e["en_cours"] = {"version": v, "ancienne": e.get("version"), "t": time.time(), "erreurs": lignes(DATA / "erreurs.log")}
    e["version"], e["seq"] = v, seq
    sauver(e)
    shutil.rmtree(neuf, ignore_errors=True)
    relancer()
    journal(f"{v[:7]} installée (test hors ligne réussi), redémarrage du papier entre deux cycles")


if __name__ == "__main__":
    main()
