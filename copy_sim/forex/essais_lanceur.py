#!/usr/bin/env python3
"""Essais du lanceur du robot, un par un. Robots lancés pour de vrai dans le bac à sable (processus à part).

  python essais_lanceur.py          sur le faux terminal (aucun ordre réel)
  python essais_lanceur.py --reel   un seul essai sur le compte DÉMO : robot d'exemple, 0,01 lot XAUUSD avec stop,
                                    fermé après une minute (environ 90 s)
Tout est écrit dans `essai_lanceur/` à côté du script (hors dépôt).
"""
import argparse
import json
import shutil
import sys
import time
from pathlib import Path

import pont_mt5 as pont

ap = argparse.ArgumentParser()
ap.add_argument("--reel", action="store_true")
args = ap.parse_args()

ICI = Path(__file__).resolve().parent
TMP = ICI / "essai_lanceur"
shutil.rmtree(TMP, ignore_errors=True)
(TMP / "mt5").mkdir(parents=True)
pont.FICHIER_GARDE = TMP / "garde.json"
import lanceur_robot as lr   # noqa: E402

EXEMPLE = {p.name: p.read_text(encoding="utf-8") for p in (ICI / "robot_exemple").iterdir() if p.is_file()}
bilan = []


def verdict(nom, ok, detail=""):
    bilan.append(bool(ok))
    print(f"  => {'REUSSI' if ok else 'ECHEC '} : {nom} {detail}\n", flush=True)


def journal():
    f = TMP / "mt5" / "robot_journal.jsonl"
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines()] if f.exists() else []


def attendre(cond, delai):
    fin = time.time() + delai
    while time.time() < fin:
        if cond():
            return True
        time.sleep(1)
    return cond()


def robot_variante(code_robot, essais=None):
    d = dict(EXEMPLE)
    d["robot.py"] = code_robot
    if essais is not None:
        d["essais_robot.py"] = essais
    return d


if pont.FICHIER_STOP.exists():
    sys.exit("STOP_PONT existe deja : le retirer avant les essais.")

if args.reel:
    import MetaTrader5 as mt5
    if not mt5.initialize():
        sys.exit("MT5 injoignable.")
    info, arret = pont.compte_demo(mt5)
    if arret:
        sys.exit("Essai refuse : " + arret)
    autres = sorted(p.ticket for p in (mt5.positions_get() or []) if p.magic != pont.MAGIQUE_ROBOT)
    L = lr.Lanceur(mt5, TMP / "mt5", TMP / "robot")
    print("Essai reel (demo) : robot d'exemple installe par VERSION, 0,01 lot XAUUSD avec stop, ferme apres 60 s")
    L.installer(1, EXEMPLE)
    ouvert = attendre(lambda: any(e.get("action") == "ouverture" for e in journal()), 30)
    ferme = attendre(lambda: any(e.get("action") == "fermeture" for e in journal()), 100)
    L.arreter("fin de l'essai")
    for e in journal():
        print("     ", json.dumps(e, ensure_ascii=False))
    o = [e for e in journal() if e.get("action") == "ouverture"]
    f = [e for e in journal() if e.get("action") == "fermeture"]
    restantes = [p for p in (mt5.positions_get() or []) if p.magic == pont.MAGIQUE_ROBOT]
    intactes = sorted(p.ticket for p in (mt5.positions_get() or []) if p.magic != pont.MAGIQUE_ROBOT) == autres
    verdict("ouverte avec stop puis fermee, aucune position du robot restante, autres positions intactes",
            o and o[0]["ok"] and o[0]["stop"] and f and f[0]["ok"] and not restantes and intactes)
    print(f"BILAN : {sum(bilan)} sur {len(bilan)}")
    sys.exit(0 if all(bilan) else 1)

import faux_mt5 as mt5   # noqa: E402
L = lr.Lanceur(mt5, TMP / "mt5", TMP / "robot")
lr.FENETRE_PLANTAGES = 600

print("1. Robot minimal installe par VERSION (ouvre 0,01 lot XAUUSD avec stop, ferme apres 3 s)")
ok = L.installer(1, robot_variante(EXEMPLE["robot.py"].replace("5.0, 60", "5.0, 3")))
ouvert = attendre(lambda: any(e.get("action") == "ouverture" and e.get("ok") for e in journal()), 20)
ferme = attendre(lambda: any(e.get("action") == "fermeture" and e.get("ok") for e in journal()), 20)
o = [x for x in mt5.ordres_recus if "position" not in x and x["action"] == mt5.TRADE_ACTION_DEAL]
verdict("installe, en marche, ouvert avec stop puis ferme",
        ok and L.en_marche() and ouvert and ferme and o and o[0]["sl"] > 0 and o[0]["magic"] == pont.MAGIQUE_ROBOT
        and L.etat()["version_installee"] == 1)

print("2. Robot refuse pour import interdit (version 2)")
ok = L.installer(2, robot_variante("import socket\n" + EXEMPLE["robot.py"]))
verdict("refuse, version 1 toujours en marche", not ok and L.en_marche() and L.e["installee"] == 1,
        "| " + str(L.e["dernier_refus"]["raison"]))

print("3. Robot refuse pour essais rates (version 3)")
ok = L.installer(3, robot_variante(EXEMPLE["robot.py"], "print('ECHEC voulu')\n"))
verdict("refuse, version 1 toujours en marche", not ok and L.en_marche() and L.e["installee"] == 1,
        "| " + str(L.e["dernier_refus"]["raison"]))

print("4. Retour arriere apres 3 plantages (version 4 qui plante une fois lancee)")
plante = "import time\n\ndef lancer(pont):\n    time.sleep(1)\n    raise ValueError('plantage voulu')\n"
ok = L.installer(4, robot_variante(plante, "print('ESSAIS OK')\n"))
attendre(lambda: (L.surveiller() or True) and L.e["installee"] == 1, 60)
verdict("version 4 installee puis retiree, retour a la version 1 en marche",
        ok and L.e["installee"] == 1 and "4" in L.e["refusees"] and attendre(L.en_marche, 5),
        "| " + str((L.e["derniere_erreur"] or {}).get("message")))

print("5. Garde-fou des 5 % : perte du jour de 600 sur 10 000")
L.arreter("essai garde-fou")
acces = L.acces
r1 = acces.ouvrir("XAUUSD", "achat", 0.01, stop=2600.0)
i = next(k for k, p in enumerate(mt5.positions) if p.ticket == r1["ticket"])
mt5.positions[i] = mt5.positions[i]._replace(profit=-600.0)
r2 = acces.ouvrir("XAUUSD", "achat", 0.01, stop=2600.0)
r3 = acces.fermer(r1["ticket"])
mt5.transactions.append(mt5.Deal(r1["ticket"], -600.0, 0.0, 0.0, 0.0))
r4 = acces.ouvrir("XAUUSD", "achat", 0.01, stop=2600.0)
verdict("ouverture refusee, fermeture permise, toujours bloque apres la fermeture",
        r1["ok"] and not r2["ok"] and "garde-fou" in r2["refus"] and r3["ok"] and not r4["ok"],
        "| " + r2.get("refus", ""))
pont.FICHIER_GARDE.unlink()

print("6. STOP_PONT arrete le robot et bloque ses ordres")
L.demarrer()
en_marche = attendre(L.en_marche, 5)
pont.FICHIER_STOP.write_text("essai\n")
try:
    L.surveiller()
    arrete = not L.en_marche()
    r = acces.ouvrir("XAUUSD", "achat", 0.01, stop=2600.0)
    L.surveiller()
    pas_relance = not L.en_marche()
finally:
    pont.FICHIER_STOP.unlink()
verdict("robot arrete, pas relance, ordre refuse", en_marche and arrete and pas_relance and not r["ok"],
        "| " + r.get("refus", ""))

print("7. Bac a sable : tentatives d'evasion (texte source deguise pour passer le controle simple)")
evasion = '''import os, time, json

def essai(f):
    try:
        f()
        return "PERMIS"
    except BaseException as e:
        return "bloque : " + type(e).__name__

def lancer(pont):
    imp = getattr(__builtins__, "__imp" + "ort__") if not isinstance(__builtins__, dict) else __builtins__["__imp" + "ort__"]
    hors = "C" + ":" + chr(92) + "Windows" + chr(92) + "win.ini"
    r = {
        "import_socket": essai(lambda: imp("so" + "cket")),
        "import_mt5": essai(lambda: imp("MetaTrader" + "5")),
        "import_ctypes": essai(lambda: imp("c" + "types")),
        "lancer_programme": essai(lambda: getattr(os, "sys" + "tem")("echo x")),
        "lire_hors_dossier": essai(lambda: open(hors).read()),
        "ecrire_hors_dossier": essai(lambda: open(os.path.join(os.path.dirname(os.getcwd()), "x.txt"), "w")),
        "variables": sorted(getattr(os, "envi" + "ron").keys()),
    }
    pont.noter(evasion=r)
    while not pont.arret_demande():
        time.sleep(2)
'''
ok = L.installer(5, robot_variante(evasion, "print('ESSAIS OK')\n"))
attendre(lambda: any("evasion" in e for e in journal()), 20)
ev = next((e["evasion"] for e in journal() if "evasion" in e), {})
print("     ", json.dumps(ev, ensure_ascii=False))
L.arreter("fin des essais")
bloques = all(str(v).startswith("bloque") for k, v in ev.items() if k != "variables")
propres = set(ev.get("variables", [])) <= {"PYTHONIOENCODING", "PYTHONDONTWRITEBYTECODE", "SYSTEMROOT", "WINDIR"}
verdict("tout bloque, aucune variable d'environnement de Baptiste", ok and ev and bloques and propres)

print("8. Rien d'identifiant dans les fichiers publies")
ecrit = "".join(f.read_text(encoding="utf-8", errors="replace") for f in (TMP / "mt5").rglob("*") if f.is_file())
verdict("ni compte, ni serveur, ni nom, ni chemin du PC",
        not any(s in ecrit for s in (str(mt5.FAUX_LOGIN), mt5.FAUX_SERVEUR, mt5.FAUX_NOM, str(Path.home()))))

print(f"BILAN : {sum(bilan)} essais reussis sur {len(bilan)}")
sys.exit(0 if all(bilan) else 1)
