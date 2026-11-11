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

print("2. Plafonds : 0,60 lot, puis 11 positions")
tour(3, [une(0.60)])
a = not du_pont()
tour(4, [une(0.01, f"p{i}") for i in range(11)])
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

print(f"BILAN : {sum(bilan)} essais reussis sur {len(bilan)}")
sys.exit(0 if all(bilan) else 1)
