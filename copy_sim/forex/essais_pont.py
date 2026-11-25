#!/usr/bin/env python3
"""Essais des sécurités du pont, un par un. À lancer AVANT de laisser tourner le pont.

  python essais_pont.py                  essais réels sur le compte DÉMO du terminal ouvert (0,01 lot, EURUSD)
  python essais_pont.py --symbole XAUUSD autre symbole
  python essais_pont.py --faux           sans terminal, sur un faux MT5 en mémoire (vérifie la logique seulement)

Les essais écrivent dans `essai_mt5/` à côté du script (hors dépôt), jamais dans `copy_sim/labo/mt5/`.
Ils refusent de démarrer si le compte n'est pas une démo, si `STOP_PONT` existe déjà, ou si le pont a déjà des
positions ouvertes (une consigne d'essai vide les fermerait).
"""
import argparse
import json
import shutil
import sys

import pont_mt5 as pont

ap = argparse.ArgumentParser()
ap.add_argument("--faux", action="store_true")
ap.add_argument("--symbole", default="EURUSD")
args = ap.parse_args()

if args.faux:
    import faux_mt5 as mt5
    mt5.positions.append(mt5.Position(77, 0, 0, 4242, 1.0, 1.09, 1.08, 1.12, 1.1, 0.0, 5.0, "EURUSD", "robot perso"))
else:
    import MetaTrader5 as mt5
    if not mt5.initialize():
        sys.exit("MT5 injoignable : ouvrir le terminal, connecte au compte demo.")

SYM = args.symbole
SORTIE = pont.ICI / "essai_mt5"
LOCAL = SORTIE / "local.json"
bilan = []


def du_pont():
    return pont.positions_pont(mt5)


def autres():
    return sorted((p.ticket, p.volume, p.sl, p.tp) for p in (mt5.positions_get() or []) if p.magic != pont.MAGIQUE)


def executions():
    f = SORTIE / "executions.jsonl"
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines()] if f.exists() else []


def tour(version, positions, **k):
    avant = len(executions())
    texte = json.dumps({"version": version, "ecrit": pont.maintenant(), "positions": positions})
    etat = pont.passage(mt5, SORTIE, texte, None, LOCAL, **k)
    for e in executions()[avant:]:
        print("     ", json.dumps(e, ensure_ascii=False))
    return etat


def verdict(nom, ok):
    bilan.append(ok)
    print(f"  => {'REUSSI' if ok else 'ECHEC '} : {nom}\n")


def une(lots=0.01, ident="essai"):
    return {"id": ident, "symbole": SYM, "sens": "achat", "lots": lots, "stop": None, "objectif": None}


info, arret = pont.compte_demo(mt5)
if arret:
    sys.exit("Essais refuses : " + arret)
if pont.FICHIER_STOP.exists():
    sys.exit("STOP_PONT existe deja : le retirer avant les essais.")
if du_pont():
    sys.exit("Le pont a deja des positions ouvertes : essais refuses.")
if mt5.symbol_info(SYM) is None:
    sys.exit(f"Symbole {SYM} absent chez le courtier : essayer --symbole avec le nom exact.")
shutil.rmtree(SORTIE, ignore_errors=True)
autres_avant = autres()
print(f"Compte demo confirme. Positions hors pont au depart : {len(autres_avant)}\n")

print(f"1. Ouverture puis fermeture de 0,01 lot {SYM} par consigne")
tour(1, [une()])
ouverte = len(du_pont()) == 1 and abs(du_pont()[0].volume - 0.01) < 1e-9
tour(1, [une()])
pas_de_double = len(du_pont()) == 1
tour(2, [])
verdict("position ouverte, pas doublee au tour suivant, puis fermee", ouverte and pas_de_double and not du_pont())

print(f"2. Plafonds : 0,60 lot, puis {pont.MAX_POSITIONS + 1} positions")
tour(3, [une(0.60)])
a = not du_pont()
tour(4, [une(0.01, f"p{i}") for i in range(pont.MAX_POSITIONS + 1)])
b = not du_pont()
refus = [e for e in executions() if e.get("action") == "refus" and "plafond" in e.get("refus", "")]
verdict("aucun ordre, deux refus de plafond notes", a and b and len(refus) == 2)

print("3. Arret d'urgence STOP_PONT")
pont.FICHIER_STOP.write_text("essai\n")
try:
    etat = tour(5, [une()])
finally:
    pont.FICHIER_STOP.unlink()
verdict("aucun ordre avec STOP_PONT, etat = " + str(etat["arret"]),
        not du_pont() and not etat["ordres_autorises"] and etat["version_appliquee"] < 5)

print("4. Compte non demo (simule)")
etat = tour(6, [une()], simuler_reel=True)
garde_directe = False
try:
    pont.envoyer(mt5, {"action": mt5.TRADE_ACTION_DEAL, "magic": pont.MAGIQUE, "volume": 0.01}, simuler_reel=True)
except pont.Refus:
    garde_directe = True
verdict("aucun ordre, rien du compte publie, etat = " + str(etat["arret"]),
        not du_pont() and not etat["ordres_autorises"] and "solde" not in etat and garde_directe)

print("5. Version plus ancienne ignoree, consigne illisible ignoree")
tour(7, [])
etat = tour(2, [une()])
etat2 = pont.passage(mt5, SORTIE, "{pas du json", None, LOCAL)
verdict("rien ne change", not du_pont() and "ignoree" in etat["consigne"] and "refusee" in etat2["consigne"])

print("6. Positions hors pont intactes, garde directe sur une position etrangere")
garde = True
for p in (mt5.positions_get() or []):
    if p.magic != pont.MAGIQUE:
        try:
            pont.envoyer(mt5, {"action": mt5.TRADE_ACTION_SLTP, "position": p.ticket, "symbol": p.symbol,
                               "sl": 0.0, "tp": 0.0, "magic": pont.MAGIQUE})
            garde = False
        except pont.Refus:
            pass
        break
verdict("les autres positions n'ont pas bouge", autres() == autres_avant and garde)

print("7. Rien d'identifiant dans les fichiers ecrits")
ecrit = "".join(f.read_text(encoding="utf-8", errors="replace") for f in SORTIE.rglob("*") if f.suffix in (".json", ".jsonl"))
c = mt5.account_info()
secrets = [str(c.login), str(c.server), str(c.name)]
verdict("ni numero de compte, ni serveur, ni nom", not any(s and s in ecrit for s in secrets))

if args.faux:
    print("8. (faux) Stop et objectif ajustes, changement de lots, demande d'historique")
    tour(8, [dict(une(), stop=1.09, objectif=1.12)])
    tour(9, [dict(une(), stop=1.095, objectif=1.12)])
    ajuste = len(du_pont()) == 1 and abs(du_pont()[0].sl - 1.095) < 1e-9
    tour(10, [dict(une(0.02), stop=1.095, objectif=1.12)])
    change = len(du_pont()) == 1 and abs(du_pont()[0].volume - 0.02) < 1e-9
    dem = json.dumps({"demandes": [{"id": "h1", "symbole": SYM, "periode": "M1", "nombre": 1000},
                                   {"id": "../x", "symbole": SYM, "periode": "M1", "nombre": 10},
                                   {"id": "h2", "symbole": "INCONNU", "periode": "M1", "nombre": 10}]})
    pont.passage(mt5, SORTIE, json.dumps({"version": 11, "positions": []}), dem, LOCAL)
    index = json.loads((SORTIE / "donnees" / "index.json").read_text())
    histo = index["h1"].get("lignes") == 1000 and "erreur" in index["h2"] and len(index) == 2 \
        and (SORTIE / "donnees" / "h1.csv.gz").exists()
    trop = [o for o in mt5.ordres_recus if o.get("magic") != pont.MAGIQUE or o.get("volume", 0) > pont.MAX_LOTS]
    verdict("ajustement, changement de taille, historique, aucun ordre hors regles",
            ajuste and change and histo and not du_pont() and not trop)

if args.faux:
    # ---------------------------------------------------------------- mode REEL (compte cent), sur le faux terminal
    # (en dernier : ce processus passe en mode reel ; le pont demo d'un autre processus n'est pas touche)
    import subprocess
    demo = subprocess.run([sys.executable, "-c", "import pont_mt5 as p; print(p.MAGIQUE, p.MAX_POSITIONS, p.MAX_LOTS, "
                           "p.REL_MT5, p.compte_demo.__name__)"], capture_output=True, text=True, cwd=str(pont.ICI)).stdout
    import pont_reel
    import acces_robot
    AUT = pont.ICI / "essai_reel_aut"          # tient lieu du dossier de la copie reelle (ou Baptiste ecrit le fichier)
    SR = pont.ICI / "essai_mt5_reel"
    shutil.rmtree(AUT, ignore_errors=True); shutil.rmtree(SR, ignore_errors=True); AUT.mkdir()
    LR = SR / "local.json"
    pont_reel.activer(pont, AUT, acces_robot)
    for p in list(mt5.positions):
        mt5.positions.remove(p)
    mt5.mode_compte, mt5.devise, mt5.valeur = mt5.ACCOUNT_TRADE_MODE_REAL, "USC", 20000.0
    ORX = "XAUUSD"

    def ouvre_robot(lots=0.02, stop=2640.0):
        try:
            v = pont.valider_position(mt5, {"id": "r", "symbole": ORX, "sens": "achat", "lots": lots, "stop": stop})
        except pont.Refus as x:
            return {"ok": False, "refus": str(x)}
        return pont.ouvrir(mt5, v, False, magique=pont.MAGIQUE_ROBOT, prefixe="robot:")

    def aut(compte, phrase=pont_reel.PHRASE):
        (AUT / pont_reel.FICHIER_AUTORISATION).write_text(json.dumps({"compte": compte, "phrase": phrase}),
                                                          encoding="utf-8")

    print("9. (reel) sans fichier d'autorisation : aucun ordre, rien du compte publie")
    e = pont.passage(mt5, SR, None, None, LR)
    r = ouvre_robot()
    verdict("refus : " + str(e["arret"]), not e["ordres_autorises"] and "solde" not in e and "autorisation" in e["arret"]
            and not r["ok"] and not mt5.positions)

    print("10. (reel) autorisation d'un autre compte, puis phrase fausse")
    aut(mt5.FAUX_LOGIN + 1)
    e1 = pont.passage(mt5, SR, None, None, LR)
    aut(mt5.FAUX_LOGIN, "oui")
    e2 = pont.passage(mt5, SR, None, None, LR)
    verdict("refus : " + str(e1["arret"]) + " / " + str(e2["arret"]),
            "different" in e1["arret"] and "phrase" in e2["arret"] and not ouvre_robot()["ok"] and not mt5.positions)

    print("11. (reel) bon numero mais compte demo, puis compte reel non cent (USD)")
    aut(mt5.FAUX_LOGIN)
    mt5.mode_compte = mt5.ACCOUNT_TRADE_MODE_DEMO
    e1 = pont.passage(mt5, SR, None, None, LR)
    mt5.mode_compte, mt5.devise = mt5.ACCOUNT_TRADE_MODE_REAL, "USD"
    e2 = pont.passage(mt5, SR, None, None, LR)
    mt5.devise = "USC"
    verdict("refus : " + str(e1["arret"]) + " / " + str(e2["arret"]),
            "pas en mode reel" in e1["arret"] and "cent" in e2["arret"] and not mt5.positions)

    print("12. (reel) tout bon : ouverture permise, plafonds 0,10 lot et stop obligatoire, spread maximal")
    e = pont.passage(mt5, SR, None, None, LR)
    ok1 = ouvre_robot()["ok"]
    trop = ouvre_robot(lots=0.20)
    sans = None
    try:
        pont.envoyer(mt5, {"action": mt5.TRADE_ACTION_DEAL, "symbol": ORX, "volume": 0.01, "magic": pont.MAGIQUE_ROBOT,
                           "sl": 0.0})
    except pont.Refus as x:
        sans = str(x)
    ancien = mt5._prix[ORX]
    mt5._prix[ORX] = (2650.10, 2652.10)
    large = ouvre_robot()
    mt5._prix[ORX] = ancien
    verdict(f"ouverture ok ; refus : {trop.get('refus')} / {sans} / {large.get('refus')}",
            e["ordres_autorises"] and e.get("mode") == "reel" and ok1 and not trop["ok"] and "plafond" in trop["refus"]
            and sans and "stop" in sans and not large["ok"] and "spread" in large["refus"] and len(mt5.positions) == 1
            and mt5.positions[0].magic == pont_reel.MAGIQUE_ROBOT_REEL and e.get("symbole_or") == ORX)

    print("13. (reel) arret automatique a -34 % du plus haut, qui ne se leve pas tout seul")
    mt5.valeur = 30000.0
    pont.passage(mt5, SR, None, None, LR)                     # nouveau plus haut
    mt5.valeur = 30000.0 * 0.67
    e1 = pont.passage(mt5, SR, None, None, LR)
    mt5.valeur = 30000.0 * 0.65
    e2 = pont.passage(mt5, SR, None, None, LR)
    r = ouvre_robot()
    mt5.valeur = 31000.0
    e3 = pont.passage(mt5, SR, None, None, LR)
    pos_gardee = len(mt5.positions) == 1                      # positions laissees a leurs stops
    verdict("a -33 % : " + str(e1["arret"]) + " ; a -35 % : " + str(e2["arret"])[:40] + "...",
            e1["ordres_autorises"] and not e2["ordres_autorises"] and "ARRET AUTOMATIQUE" in e2["arret"]
            and e2["sommet"]["arret"] and "solde" in e2 and not r["ok"] and not e3["ordres_autorises"] and pos_gardee)

    print("14. (reel) STOP_PONT, rien d'identifiant publie, pont demo d'un autre processus inchange")
    pont.FICHIER_STOP.write_text("essai\n")
    try:
        (AUT / pont_reel.FICHIER_SOMMET).unlink()
        e = pont.passage(mt5, SR, None, None, LR)
    finally:
        pont.FICHIER_STOP.unlink()
    ecrit = "".join(f.read_text(encoding="utf-8", errors="replace") for f in SR.rglob("*") if f.suffix in (".json", ".jsonl"))
    secrets = [str(mt5.FAUX_LOGIN), mt5.FAUX_SERVEUR, mt5.FAUX_NOM]
    verdict("STOP_PONT : " + str(e["arret"]) + " ; demo : " + demo.strip(),
            not e["ordres_autorises"] and "STOP_PONT" in e["arret"] and not any(x in ecrit for x in secrets)
            and demo.split() == ["20261111", "30", "0.5", "copy_sim/labo/mt5", "compte_demo"])
    print("15. (reel) une version du robot ne s'installe que si Baptiste l'a autorisee (champ robot)")
    import lanceur_robot
    pont_reel.activer(pont, AUT, acces_robot, lanceur_robot)
    lire = pont.lire_distant
    pont.lire_distant = lambda nom: "3\n" if nom == "robot/VERSION" else None
    try:
        la = lanceur_robot.Lanceur(mt5, SR, racine=SR / "rob")
        aut(mt5.FAUX_LOGIN)
        v0 = la.version_distante()
        (AUT / pont_reel.FICHIER_AUTORISATION).write_text(json.dumps(
            {"compte": mt5.FAUX_LOGIN, "phrase": pont_reel.PHRASE, "robot": 2}), encoding="utf-8")
        v2 = la.version_distante()
        (AUT / pont_reel.FICHIER_AUTORISATION).write_text(json.dumps(
            {"compte": mt5.FAUX_LOGIN, "phrase": pont_reel.PHRASE, "robot": 3}), encoding="utf-8")
        v3 = la.version_distante()
    finally:
        pont.lire_distant = lire
    verdict(f"sans champ : {v0} ; autorisee 2 : {v2} ; autorisee 3 : {v3} ; dossier robot : {lanceur_robot.REL_ROBOT}",
            v0 is None and v2 is None and v3 == 3 and lanceur_robot.REL_ROBOT == "copy_sim/labo/mt5_reel/robot"
            and "pont_reel.py" in lanceur_robot.COMMUNS)
    print("16. (reel) arret a distance : arret, fermer_tout limite aux magiques reels, une seule fois ; absent / false /"
          " illisible = normal ; ne peut jamais autoriser")
    for p in list(mt5.positions):
        mt5.positions.remove(p)
    mt5.valeur = 20000.0
    (AUT / pont_reel.FICHIER_SOMMET).unlink(missing_ok=True)
    aut(mt5.FAUX_LOGIN)
    ouvre_robot(); ouvre_robot()
    etr = mt5.Position(91, 0, 0, 20261112, 0.01, 2650.0, 2640.0, 0.0, 2650.0, 0.0, 1.0, ORX, "demo")
    mt5.positions.append(etr)
    acc = acces_robot.AccesRobot(mt5, None)
    n0 = pont_reel.appliquer_arret_distant(mt5, None, SR)
    e0 = pont.passage(mt5, SR, None, None, LR)
    m1 = pont_reel.appliquer_arret_distant(mt5, json.dumps({"arret": True, "fermer_tout": True}), SR)
    reste = [p.magic for p in mt5.positions]
    e1 = pont.passage(mt5, SR, None, None, LR)
    r1 = ouvre_robot()
    stop_robot = acc.arret_demande()
    ouvre_ok = None
    pont_reel._ETAT["distant"] = None                      # une position rouverte a la main pendant l'arret...
    ouvre_ok = ouvre_robot()["ok"]
    pont_reel.appliquer_arret_distant(mt5, json.dumps({"arret": True, "fermer_tout": True}), SR)
    une_fois = sum(p.magic == pont_reel.MAGIQUE_ROBOT_REEL for p in mt5.positions) == 1   # ...n'est pas refermee
    pont_reel.appliquer_arret_distant(mt5, json.dumps({"arret": False}), SR)
    e2 = pont.passage(mt5, SR, None, None, LR)
    pont_reel.appliquer_arret_distant(mt5, "{pas du json", SR)
    e3 = pont.passage(mt5, SR, None, None, LR)
    (AUT / pont_reel.FICHIER_AUTORISATION).unlink()
    pont_reel.appliquer_arret_distant(mt5, json.dumps({"arret": False, "autoriser": True, "compte": mt5.FAUX_LOGIN,
                                                       "phrase": pont_reel.PHRASE, "robot": 1}), SR)
    e4 = pont.passage(mt5, SR, None, None, LR)
    verdict("arret : " + str(e1["arret"])[:45] + "... ; restent : " + str(reste),
            n0 is None and e0["ordres_autorises"] and m1["fermeture_faite"] and reste == [20261112]
            and not e1["ordres_autorises"] and "ARRET A DISTANCE" in e1["arret"] and e1["arret_distant"]["actif"]
            and not r1["ok"] and stop_robot and ouvre_ok and une_fois
            and e2["ordres_autorises"] and e2["arret_distant"] is None and e3["ordres_autorises"]
            and not e4["ordres_autorises"] and "autorisation" in e4["arret"] and not acc.arret_demande())
    shutil.rmtree(AUT, ignore_errors=True); shutil.rmtree(SR, ignore_errors=True)

print(f"BILAN : {sum(bilan)} essais reussis sur {len(bilan)}")
sys.exit(0 if all(bilan) else 1)
