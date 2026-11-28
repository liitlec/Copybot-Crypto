"""Lanceur du robot du labo (copy_sim/labo/mt5/robot/), dans le processus du pont.

À chaque tour du pont : si `robot/VERSION` (sur la branche distante) dépasse la version installée, copie figée du
dossier hors du dépôt, contrôle du texte source, essais sur le faux terminal dans le bac à sable (2 minutes au plus).
« ESSAIS OK » -> l'ancien robot s'arrête, le nouveau démarre ; sinon refus noté, l'ancien continue.
Le robot tourne dans un processus à part (`bac_a_sable.py`) et ne passe ses ordres que par `AccesRobot` (fonctions
du pont). 3 plantages en 10 minutes -> retour à la version d'avant (ou arrêt s'il n'y en a pas). `STOP_PONT` l'arrête.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pont_mt5 as pont
from acces_robot import AccesRobot

REL_ROBOT = pont.REL_MT5 + "/robot"
INTERFACE = "copy_sim/forex/ROBOT_INTERFACE.md"
COMMUNS = ("pont_mt5.py", "acces_robot.py", "faux_mt5.py", "bac_a_sable.py")
EXTENSIONS = (".py", ".json", ".txt", ".md", ".csv")
MAX_FICHIERS, MAX_OCTETS = 40, 2_000_000
DELAI_ESSAIS = 120
PLANTAGES_MAX, FENETRE_PLANTAGES = 3, 600
MAX_JOURNAL, GARDE_JOURNAL = 5_000_000, 2_000_000
RE_NOM = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,60}$")
# contrôle simple du texte source (le crochet d'audit du bac à sable reste la vraie barrière)
INTERDITS = [
    (re.compile(r"\bMetaTrader5\b"), "MetaTrader5"), (re.compile(r"\bsubprocess\b"), "subprocess"),
    (re.compile(r"\bsocket\b"), "socket"), (re.compile(r"\burllib\d?\b"), "urllib"),
    (re.compile(r"\brequests\b"), "requests"), (re.compile(r"\bos\s*\.\s*system\b"), "os.system"),
    (re.compile(r"\bctypes\b"), "ctypes"), (re.compile(r"\b__import__\b"), "__import__"),
    (re.compile(r"\bimportlib\b"), "importlib"), (re.compile(r"\b(exec|eval|compile)\s*\("), "exec/eval/compile"),
    (re.compile(r"\b(multiprocessing|asyncio|http|ssl|winreg|webbrowser|mmap)\b"), "module reseau ou systeme"),
    (re.compile(r"\bos\s*\.\s*(popen|exec\w*|spawn\w*|startfile|environ)\b"), "fonction os interdite"),
    (re.compile(r"""["'][A-Za-z]:[\\/]|["'](\\\\|/)|\.\.[\\/]"""), "chemin hors de son dossier"),
    (re.compile(r"\bsys\s*\.\s*(addaudithook|settrace|setprofile|_getframe|modules)\b"), "sys interdit"),
]


def controle_source(nom: str, texte: str) -> str | None:
    for motif, raison in INTERDITS:
        m = motif.search(texte)
        if m:
            ligne = texte[:m.start()].count("\n") + 1
            return f"{nom} ligne {ligne} : {raison} interdit"
    return None


def anonymiser(texte: str) -> str:
    for p in sorted({str(Path.home()), str(pont.ICI), str(pont.DEPOT)}, key=len, reverse=True):
        texte = texte.replace(p, "~")
    return texte


def env_vide() -> dict:
    """Environnement du robot : rien de Baptiste (ni clé, ni profil)."""
    e = {"PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
    for k in ("SYSTEMROOT", "WINDIR"):
        if os.environ.get(k):
            e[k] = os.environ[k]
    return e


def python_console() -> str:
    exe = Path(sys.executable)
    cons = exe.with_name("python.exe")
    return str(cons if cons.exists() else exe)


class Lanceur:
    def __init__(self, mt5, sortie: Path, racine: Path | None = None, source=None, simuler_reel=False):
        """sortie = copy_sim/labo/mt5 du dépôt ; racine = dossier des copies figées (hors dépôt) ;
        source = fonction (version) -> {nom: texte} ou None (par défaut : la branche distante, par git)."""
        self.mt5, self.sortie = mt5, Path(sortie)
        self.racine = Path(racine) if racine else pont.ICI / "robot"
        self.commun = self.racine / "commun"
        self.fichier = self.racine / "lanceur.json"
        self.source = source or self._source_git
        self.acces = AccesRobot(mt5, self.sortie / "robot_journal.jsonl", simuler_reel)
        self.proc, self.fil, self.plantages, self.voulu_arret = None, None, [], False
        self.e = pont.lire_json(self.fichier, {})
        if not isinstance(self.e, dict):
            self.e = {}
        for k, v in (("installee", None), ("precedente", None), ("refusees", {}), ("dernier_refus", None),
                     ("derniere_erreur", None)):
            self.e.setdefault(k, v)

    # ------------------------------------------------------------ état
    def _sauver(self):
        pont.ecrire_json(self.fichier, self.e)

    def _noter(self, **champs):
        self.acces._ecrire({"type": "lanceur", **champs})
        pont.log.info("robot : %s", champs)

    def etat(self) -> dict:
        return {"version_installee": self.e["installee"], "version_precedente": self.e["precedente"],
                "en_marche": self.en_marche(), "dernier_refus": self.e["dernier_refus"],
                "derniere_erreur": self.e["derniere_erreur"], "plantages_10_min": len(self.plantages),
                "interface": INTERFACE}

    def en_marche(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    # ------------------------------------------------------------ source
    def _source_git(self, version: int) -> dict:
        code, sortie, err = pont.git("ls-tree", "-r", "-l", f"origin/{pont.BRANCHE}", "--", REL_ROBOT + "/")
        if code != 0:
            raise pont.Refus("lecture du dossier robot impossible : " + err[:100])
        fichiers = {}
        for ligne in sortie.splitlines():
            meta, _, chemin = ligne.partition("\t")
            nom = chemin[len(REL_ROBOT) + 1:]
            fichiers[nom] = int(meta.split()[3]) if meta.split()[3].isdigit() else MAX_OCTETS
        if len(fichiers) > MAX_FICHIERS or sum(fichiers.values()) > MAX_OCTETS:
            raise pont.Refus(f"robot trop gros ({MAX_FICHIERS} fichiers, {MAX_OCTETS} octets au plus)")
        textes = {}
        for nom in fichiers:
            texte = pont.lire_distant(f"robot/{nom}")
            if texte is None:
                raise pont.Refus(f"lecture de {nom} impossible")
            textes[nom] = texte
        return textes

    def version_distante(self) -> int | None:
        t = pont.lire_distant("robot/VERSION")
        if t is None:
            return None
        t = t.strip()
        return int(t) if t.isdigit() and len(t) < 12 else None

    # ------------------------------------------------------------ installation
    def _preparer_commun(self):
        self.commun.mkdir(parents=True, exist_ok=True)
        for nom in COMMUNS:
            shutil.copy2(pont.ICI / nom, self.commun / nom)

    def _args(self, mode: str, dossier: Path) -> list:
        return [python_console(), "-I", "-B", str(self.commun / "bac_a_sable.py"), mode, str(dossier),
                str(self.commun), str(self.sortie)]

    def installer(self, version: int, fichiers: dict | None = None) -> bool:
        """Installe la version si le contrôle et les essais passent. Renvoie vrai si installée."""
        try:
            if fichiers is None:
                fichiers = self.source(version)
            for nom in fichiers:
                if "/" in nom or "\\" in nom or not RE_NOM.match(nom) or not nom.endswith(EXTENSIONS + ("VERSION",)):
                    raise pont.Refus(f"fichier non permis dans robot/ : {nom[:60]} (pas de sous-dossier)")
            for nom in ("robot.py", "essais_robot.py"):
                if nom not in fichiers:
                    raise pont.Refus(f"{nom} manquant")
            for nom, texte in fichiers.items():
                if nom.endswith(".py"):
                    raison = controle_source(nom, texte)
                    if raison:
                        raise pont.Refus(raison)
            dossier = self.racine / f"v{version}"
            shutil.rmtree(dossier, ignore_errors=True)
            dossier.mkdir(parents=True)
            for nom, texte in fichiers.items():
                (dossier / nom).write_text(texte, encoding="utf-8")
            self._preparer_commun()
            try:
                r = subprocess.run(self._args("essais", dossier), cwd=dossier, env=env_vide(), capture_output=True,
                                   text=True, encoding="utf-8", errors="replace", timeout=DELAI_ESSAIS,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                sortie = (r.stdout or "") + (r.stderr or "")
                ok = r.returncode == 0 and "ESSAIS OK" in "\n".join((r.stdout or "").strip().splitlines()[-3:])
            except subprocess.TimeoutExpired:
                sortie, ok = "", False
                raise pont.Refus(f"essais trop longs (plus de {DELAI_ESSAIS} s)")
            finally:
                (self.racine / f"essais_v{version}.log").write_text(locals().get("sortie", ""), encoding="utf-8")
            if not ok:
                derniere = [x for x in sortie.strip().splitlines() if x.strip()][-1:] or ["(rien)"]
                raise pont.Refus("essais rates : " + anonymiser(derniere[0])[:200])
        except pont.Refus as e:
            self.e["refusees"][str(version)] = str(e)
            self.e["dernier_refus"] = {"version": version, "raison": str(e), "heure": pont.maintenant()}
            self._sauver()
            self._noter(evenement="refus", version=version, raison=str(e))
            return False
        self.arreter("nouvelle version")
        if self.e["installee"] is not None:
            self.e["precedente"] = self.e["installee"]
        self.e["installee"] = version
        self.plantages = []
        self._sauver()
        self._noter(evenement="installee", version=version)
        self.demarrer()
        return True

    # ------------------------------------------------------------ marche
    def demarrer(self):
        if self.e["installee"] is None or self.en_marche() or pont.FICHIER_STOP.exists():
            return
        dossier = self.racine / f"v{self.e['installee']}"
        self._preparer_commun()
        erreurs = open(self.racine / "robot_erreurs.log", "ab")
        self.proc = subprocess.Popen(self._args("robot", dossier), cwd=dossier, env=env_vide(),
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=erreurs,
                                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        erreurs.close()
        self.voulu_arret = False
        self.fil = threading.Thread(target=self._servir, args=(self.proc,), daemon=True)
        self.fil.start()
        self._noter(evenement="demarre", version=self.e["installee"])

    def _servir(self, proc):
        try:
            for ligne in proc.stdout:
                if len(ligne) > 100_000:
                    rep = json.dumps({"n": None, "e": "requete trop longue"})
                else:
                    rep = self.acces.servir(ligne.decode("utf-8", "replace"))
                proc.stdin.write((rep + "\n").encode())
                proc.stdin.flush()
        except (OSError, ValueError):
            pass

    def arreter(self, raison: str):
        if self.proc is None:
            return
        self.voulu_arret = True
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
            self._noter(evenement="arrete", version=self.e["installee"], raison=raison)
        self.proc = None

    def _derniere_erreur(self) -> str:
        try:
            lignes = (self.racine / "robot_erreurs.log").read_bytes()[-4000:].decode("utf-8", "replace")
        except OSError:
            return "(aucune)"
        lignes = [x for x in lignes.strip().splitlines() if x.strip()]
        return anonymiser(lignes[-1])[:300] if lignes else "(aucune)"

    def surveiller(self):
        """Toutes les quelques secondes : STOP_PONT, plantages, redémarrage."""
        if pont.FICHIER_STOP.exists():
            self.arreter("STOP_PONT present")
            return
        if self.proc is not None and self.proc.poll() is not None and not self.voulu_arret:
            code = self.proc.returncode
            self.proc = None
            maintenant = time.time()
            self.plantages = [t for t in self.plantages if maintenant - t < FENETRE_PLANTAGES] + [maintenant]
            self.e["derniere_erreur"] = {"version": self.e["installee"], "code_sortie": code,
                                         "message": self._derniere_erreur(), "heure": pont.maintenant()}
            self._noter(evenement="plantage", version=self.e["installee"], code_sortie=code,
                        message=self.e["derniere_erreur"]["message"])
            if len(self.plantages) >= PLANTAGES_MAX:
                fautive = self.e["installee"]
                self.e["refusees"][str(fautive)] = f"{PLANTAGES_MAX} plantages en {FENETRE_PLANTAGES // 60} min"
                self.e["installee"], self.e["precedente"] = self.e["precedente"], None
                self.plantages = []
                self._noter(evenement="retour_arriere", depuis=fautive, vers=self.e["installee"])
            self._sauver()
        if self.proc is None and self.e["installee"] is not None:
            self.demarrer()

    def tour(self):
        """Une fois par tour du pont : nouvelle version ? surveillance ; journal borné."""
        if not pont.FICHIER_STOP.exists():
            v = self.version_distante()
            if v is not None and v > (self.e["installee"] or 0) and str(v) not in self.e["refusees"]:
                self.installer(v)
        self.surveiller()
        j = self.sortie / "robot_journal.jsonl"
        if j.exists() and j.stat().st_size > MAX_JOURNAL:
            reste = j.read_bytes()[-GARDE_JOURNAL:]
            j.write_bytes(reste[reste.find(b"\n") + 1:])
