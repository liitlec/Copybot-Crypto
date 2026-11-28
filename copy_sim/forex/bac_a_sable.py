"""Démarre le robot du labo (ou ses essais) dans un processus à part, sous surveillance (crochet d'audit Python).

    python -I bac_a_sable.py robot  <dossier du robot> <dossier commun> <dossier mt5 du dépôt>
    python -I bac_a_sable.py essais <dossier du robot> <dossier commun> <dossier mt5 du dépôt>

Interdit, une fois le crochet posé (il ne peut pas être retiré) : importer MetaTrader5, subprocess, socket, urllib,
http, requests, ctypes, multiprocessing, asyncio, ssl… ; lancer un programme ; ouvrir une connexion ; lire un fichier
hors de son dossier, du dossier commun, de `copy_sim/labo/mt5/` et de Python ; écrire hors de son dossier.
Le lanceur lui donne aussi un environnement vide (aucune variable de Baptiste, aucune clé).

Ce n'est PAS un bac à sable étanche (la doc Python le dit des crochets d'audit) : c'est une barrière contre les
erreurs et les tentatives simples, en plus du contrôle du texte source et des essais. En mode robot, le robot reçoit
`ClientPont`, qui ne fait qu'envoyer des requêtes au pont ; les ordres sont validés de l'autre côté du tube.
"""
import json
import os
import sys

MODULES_INTERDITS = frozenset((
    "MetaTrader5", "subprocess", "_posixsubprocess", "socket", "_socket", "urllib", "urllib3", "http", "requests",
    "httpx", "aiohttp", "ctypes", "_ctypes", "multiprocessing", "_multiprocessing", "asyncio", "concurrent", "ssl",
    "_ssl", "ftplib", "smtplib", "poplib", "imaplib", "telnetlib", "webbrowser", "winreg", "xmlrpc", "socketserver",
    "mmap", "select", "selectors", "pip", "ensurepip", "venv", "_overlapped", "pty", "importlib.metadata",
))
EVENEMENTS_INTERDITS = (
    "subprocess.", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.startfile", "os.fork", "os.kill",
    "os.putenv", "os.unsetenv", "os.symlink", "os.link", "os.chmod", "os.chown", "ctypes.", "socket.", "winreg.",
    "_winapi.", "msvcrt.", "mmap.", "sys.settrace", "sys.setprofile", "sys.monitoring", "sys.remote_exec",
    "cpython.remote_debugger_script", "gc.get_referrers", "gc.get_referents", "gc.get_objects", "urllib.",
    "http.client.", "ftplib.", "smtplib.", "webbrowser.", "pdb.",
)
ECRITURE_PAR_CHEMIN = ("os.remove", "os.rename", "os.replace", "os.rmdir", "os.mkdir", "os.truncate", "shutil.",
                       "os.utime")
LECTURE_PAR_CHEMIN = ("os.listdir", "os.scandir", "os.chdir", "glob.glob", "os.add_dll_directory")


def _norm(p) -> str:
    return os.path.normcase(os.path.abspath(os.fsdecode(os.fspath(p))))


def _sous(chemin: str, racines) -> bool:
    return any(chemin == r or chemin.startswith(r.rstrip("\\/") + os.sep) for r in racines)


def poser_crochet(dossier: str, lecture: tuple) -> None:
    ecriture = (_norm(dossier),)
    lecture = tuple(_norm(x) for x in lecture) + ecriture
    ecrire_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC

    def crochet(ev, args):
        if ev == "import":
            nom = args[0] or ""
            if nom in MODULES_INTERDITS or nom.split(".")[0] in MODULES_INTERDITS:
                raise ImportError(f"bac a sable : module interdit ({nom})")
            return
        if ev == "open":
            chemin, mode, flags = (list(args) + [None, None, None])[:3]
            if chemin is None or isinstance(chemin, int):
                return
            c = _norm(chemin)
            ecrit = (isinstance(mode, str) and any(x in mode for x in "wax+")) or \
                    (isinstance(flags, int) and flags & ecrire_flags)
            if not _sous(c, ecriture if ecrit else lecture):
                raise PermissionError(f"bac a sable : fichier hors de ses dossiers ({'ecriture' if ecrit else 'lecture'})")
            return
        if ev.startswith(EVENEMENTS_INTERDITS):
            raise PermissionError(f"bac a sable : interdit ({ev})")
        if ev.startswith(ECRITURE_PAR_CHEMIN) or ev.startswith(LECTURE_PAR_CHEMIN):
            racines = ecriture if ev.startswith(ECRITURE_PAR_CHEMIN) else lecture
            for a in args:
                if isinstance(a, (str, bytes, os.PathLike)) and not _sous(_norm(a), racines):
                    raise PermissionError(f"bac a sable : {ev} hors de ses dossiers")

    sys.addaudithook(crochet)


class ClientPont:
    """Ce que le robot reçoit : chaque appel devient une requête au pont (qui valide tout)."""

    def __init__(self, entree, sortie):
        self._in, self._out, self._n = entree, sortie, 0

    def _appel(self, f, *a, **k):
        self._n += 1
        self._out.write((json.dumps({"n": self._n, "f": f, "a": list(a), "k": k}) + "\n").encode())
        self._out.flush()
        ligne = self._in.readline()
        if not ligne:
            raise SystemExit("pont ferme : arret du robot")
        rep = json.loads(ligne)
        if "e" in rep:
            raise RuntimeError(rep["e"])
        return rep["r"]

    def __getattr__(self, nom):
        if nom.startswith("_"):
            raise AttributeError(nom)
        return lambda *a, **k: self._appel(nom, *a, **k)


def main():
    mode, dossier, commun, mt5dir = sys.argv[1:5]
    entree, sortie = sys.stdin.buffer, sys.stdout.buffer
    racines_python = {sys.prefix, sys.base_prefix, sys.exec_prefix, os.path.dirname(sys.executable)}
    lecture = (commun, mt5dir, *racines_python)
    os.chdir(dossier)
    sys.path[:0] = [dossier, commun]
    if mode == "robot":
        sys.stdout = sys.stderr            # les print du robot vont dans son journal d'erreurs, pas dans le tube
        sys.stdin = None
    poser_crochet(dossier, lecture)
    if mode == "essais":
        import runpy
        runpy.run_path(os.path.join(dossier, "essais_robot.py"), run_name="__main__")
    elif mode == "robot":
        import robot
        robot.lancer(ClientPont(entree, sortie))
    else:
        sys.exit("mode inconnu")


if __name__ == "__main__":
    main()
