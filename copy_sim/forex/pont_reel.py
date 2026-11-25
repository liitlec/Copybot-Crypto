#!/usr/bin/env python3
"""Mode RÉEL du pont (compte STARTRADER cent) : `python pont_mt5.py --reel --terminal "<chemin\\terminal64.exe>"`.

Préparé le 25/11/2026 à la demande écrite de Baptiste (PRIORITES « 25/11 23 h »). Le pont démo (`pont_mt5.py` sans
`--reel`) ne change pas : ce module n'est chargé QUE par `--reel`, dans un processus à part, depuis une copie figée à
part (`%USERPROFILE%\\pont_mt5_reel`, voir `installer_tache_reel.ps1`) et un clone du dépôt à part.

Il reprend les fonctions du pont démo et remplace, dans CE processus seulement, ce qui doit l'être :
- compte : aucun ordre tant que le fichier local `AUTORISATION_REEL.json` (à côté du script, écrit par Baptiste sur
  son PC, jamais dans le dépôt) n'existe pas, ne contient pas exactement
    {"compte": <numéro du compte cent>, "phrase": "J'autorise le robot a trader en reel sur ce compte cent",
     "robot": <version du robot réel autorisée>}
  ou ne correspond pas au compte connecté ; le compte doit aussi être en mode RÉEL et en devise cent (USC / EUC).
  Sinon : aucun ordre, statut affiché, rien du compte publié. Le numéro n'est jamais écrit ailleurs que dans ce fichier.
- numéros magiques distincts de la démo ; plafonds 10 positions et 0,10 lot par position ; stop obligatoire sur toute
  ouverture ; spread maximal par ordre ; garde-fou −5 % par jour (celui du pont) ;
- ARRÊT AUTOMATIQUE à −34 % du plus haut de la valeur du compte : plus aucun ordre (positions laissées à leurs stops
  chez le courtier), alerte dans l'état ; il ne se lève que si Baptiste supprime `sommet_reel.json` sur son PC ;
- `STOP_PONT` (à côté du script réel) : plus aucun ordre, robot arrêté ;
- pas de consigne écrite par une IA, pas de demandes d'historique, pas d'export des autres robots : seul le robot réel
  (`copy_sim/labo/mt5_reel/robot/`) trade ; sorties publiées dans `copy_sim/labo/mt5_reel/` seulement.
- une version du robot réel ne s'installe que si elle est égale au champ "robot" de ce fichier (aucune nouvelle
  version sans le geste de Baptiste sur son PC, PLAN_REEL point 7) ;
- le terminal utilisé est celui donné par `--terminal` (le 2e MT5) : `initialize(path=...)` à chaque connexion.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

PHRASE = "J'autorise le robot a trader en reel sur ce compte cent"
FICHIER_AUTORISATION = "AUTORISATION_REEL.json"
FICHIER_SOMMET = "sommet_reel.json"
DEVISES_CENT = ("USC", "EUC")
REL_MT5_REEL = "copy_sim/labo/mt5_reel"
MAGIQUE_REEL, MAGIQUE_ROBOT_REEL = 20261125, 20261126
MAX_POSITIONS_REEL, MAX_LOTS_REEL = 10, 0.10
ARRET_SOMMET = 0.34                 # arrêt automatique à −34 % du plus haut de la valeur du compte
SPREAD_MAX_REL = 0.0003             # 3 pb du prix : au-delà, ouverture refusée (or ≈ 1,2 $ à 4 000 $)
PORTS_REEL = range(8766, 8772)      # tableau de bord réel (la démo est sur 8765)

_ETAT = {"pont": None, "dossier": None, "envoyer": None, "construire": None}


def lire_autorisation(dossier: Path):
    """Renvoie (numéro du compte autorisé, None) ou (None, raison). Le numéro n'est jamais publié."""
    f = Path(dossier) / FICHIER_AUTORISATION
    if not f.exists():
        return None, "pas d'autorisation (AUTORISATION_REEL.json absent) : aucun ordre"
    try:
        a = json.loads(f.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None, "AUTORISATION_REEL.json illisible : aucun ordre"
    if not isinstance(a, dict) or a.get("phrase") != PHRASE:
        return None, "AUTORISATION_REEL.json : phrase absente ou differente : aucun ordre"
    n = a.get("compte")
    if isinstance(n, str) and n.strip().isdigit():
        n = int(n.strip())
    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        return None, "AUTORISATION_REEL.json : numero de compte invalide : aucun ordre"
    return n, None


def version_robot_autorisee(dossier: Path):
    """Version du robot réel autorisée par Baptiste (champ "robot" du fichier d'autorisation), ou None."""
    n, raison = lire_autorisation(dossier)
    if raison:
        return None
    try:
        a = json.loads((Path(dossier) / FICHIER_AUTORISATION).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    v = a.get("robot")
    return v if isinstance(v, int) and not isinstance(v, bool) and v > 0 else None


def sommet(dossier: Path, valeur: float) -> dict:
    """Plus haut de la valeur du compte et arrêt à −34 % (définitif jusqu'à suppression du fichier par Baptiste)."""
    pont = _ETAT["pont"]
    f = Path(dossier) / FICHIER_SOMMET
    s = pont.lire_json(f, {})
    if not isinstance(s, dict) or not pont.nombre(s.get("plus_haut")):
        s = {"plus_haut": valeur, "arret": False}
    if not s.get("arret") and valeur > s["plus_haut"]:
        s["plus_haut"] = valeur
    s["valeur"] = valeur
    s["recul"] = round(valeur / s["plus_haut"] - 1, 4) if s["plus_haut"] > 0 else 0.0
    if not s.get("arret") and s["plus_haut"] > 0 and valeur <= (1 - ARRET_SOMMET) * s["plus_haut"]:
        s["arret"] = True
        s["heure_arret"] = pont.maintenant()
        pont.log.error("ARRET AUTOMATIQUE : valeur %.2f a -%d %% du plus haut %.2f", valeur, ARRET_SOMMET * 100,
                       s["plus_haut"])
    pont.ecrire_json(f, s)
    return s


def compte_reel(mt5, simuler_reel: bool = False):
    """Remplace compte_demo en mode réel. Renvoie (info publiable ou None, raison d'arrêt ou None)."""
    dossier = _ETAT["dossier"]
    info = mt5.account_info()
    if info is None:
        return None, "terminal MT5 non connecte a un compte : aucun ordre"
    n, raison = lire_autorisation(dossier)
    if raison:
        return None, raison
    if int(info.login) != n:
        return None, "compte connecte different du compte autorise : aucun ordre"
    if info.trade_mode != mt5.ACCOUNT_TRADE_MODE_REAL:
        return None, "compte autorise mais pas en mode reel : aucun ordre"
    if str(info.currency).upper() not in DEVISES_CENT:
        return None, "compte autorise mais pas un compte cent (devise attendue USC ou EUC) : aucun ordre"
    s = sommet(dossier, float(info.equity))
    if s.get("arret"):
        return info, (f"ARRET AUTOMATIQUE : valeur a -{ARRET_SOMMET:.0%} du plus haut : plus aucun ordre "
                      "(positions laissees a leurs stops) ; decision de Baptiste")
    return info, None


def envoyer_reel(mt5, demande: dict, simuler_reel: bool = False):
    """Avant l'envoyer du pont : stop obligatoire et spread maximal sur toute ouverture."""
    pont = _ETAT["pont"]
    if "position" not in demande and demande.get("action") == mt5.TRADE_ACTION_DEAL:
        if not (pont.nombre(demande.get("sl")) and demande["sl"] > 0):
            raise pont.Refus("ouverture sans stop refusee")
        t = mt5.symbol_info_tick(demande.get("symbol"))
        if t is None or t.bid <= 0 or t.ask <= 0:
            raise pont.Refus("pas de prix : ouverture refusee")
        if (t.ask - t.bid) / t.bid > SPREAD_MAX_REL:
            raise pont.Refus(f"spread trop large ({(t.ask - t.bid) / t.bid * 1e4:.1f} pb > "
                             f"{SPREAD_MAX_REL * 1e4:.0f} pb) : ouverture refusee")
    return _ETAT["envoyer"](mt5, demande, simuler_reel)


def symbole_or(mt5):
    """Nom du symbole or chez le courtier (XAUUSD, éventuellement avec un suffixe), jamais supposé."""
    if mt5.symbol_info("XAUUSD") is not None:
        return "XAUUSD"
    noms = sorted((s.name for s in (getattr(mt5, "symbols_get", lambda *a: None)() or [])
                   if str(s.name).upper().startswith("XAUUSD")), key=len)
    return noms[0] if noms else None


def construire_etat_reel(mt5, info, arret, statut, local, symboles):
    pont = _ETAT["pont"]
    sym = symbole_or(mt5) if info is not None else None
    if sym:
        symboles.add(sym)
    e = _ETAT["construire"](mt5, info, arret, statut, local, symboles)
    e["mode"] = "reel"
    e["securites"] = {"arret_depuis_plus_haut": -ARRET_SOMMET, "perte_max_jour": -pont.PERTE_MAX_JOUR,
                      "spread_max_pb": SPREAD_MAX_REL * 1e4, "stop_obligatoire": True}
    if info is not None:
        s = pont.lire_json(Path(_ETAT["dossier"]) / FICHIER_SOMMET, {})
        e["sommet"] = {k: s.get(k) for k in ("plus_haut", "recul", "arret", "heure_arret")}
        e["symbole_or"] = sym
    return e


def activer(pont, dossier: Path | None = None, acces_robot=None, lanceur_robot=None):
    """Met CE processus en mode réel (le module pont_mt5 importé ici, pas le fichier ni l'autre processus)."""
    _ETAT.update(pont=pont, dossier=Path(dossier or pont.ICI))
    if _ETAT["envoyer"] is None:
        _ETAT["envoyer"], _ETAT["construire"] = pont.envoyer, pont.construire_etat
    pont.MAGIQUE, pont.MAGIQUE_ROBOT = MAGIQUE_REEL, MAGIQUE_ROBOT_REEL
    pont.MAGIQUES = (MAGIQUE_REEL, MAGIQUE_ROBOT_REEL)
    pont.MAX_POSITIONS, pont.MAX_LOTS = MAX_POSITIONS_REEL, MAX_LOTS_REEL
    pont.REL_MT5 = REL_MT5_REEL
    pont.compte_demo = compte_reel
    pont.envoyer = envoyer_reel
    pont.construire_etat = construire_etat_reel
    pont.MODE_REEL = True
    if acces_robot is not None:                       # le robot réel apprend le nom du symbole or par compte()
        if not hasattr(acces_robot.AccesRobot, "_compte_demo"):
            acces_robot.AccesRobot._compte_demo = acces_robot.AccesRobot.compte

        def compte(self):
            c = acces_robot.AccesRobot._compte_demo(self)
            if c.get("ordres_autorises") or "solde" in c:
                with pont.VERROU:
                    c["symbole_or"] = symbole_or(self.mt5)
            c["mode"] = "reel"
            return c
        acces_robot.AccesRobot.compte = compte
    if lanceur_robot is not None:
        lanceur_robot.REL_ROBOT = REL_MT5_REEL + "/robot"
        L = lanceur_robot.Lanceur
        if not hasattr(L, "_version_distante_demo"):
            L._version_distante_demo = L.version_distante

            def version_distante(self):
                """En réel : une version ne s'installe que si Baptiste l'a autorisée (champ "robot" du fichier)."""
                v = L._version_distante_demo(self)
                ok = version_robot_autorisee(_ETAT["dossier"])
                if v is not None and v != ok:
                    if self.e.get("attente_accord") != v:
                        self.e["attente_accord"] = v
                        self._noter(evenement="attente", version=v,
                                    raison="version non autorisee dans AUTORISATION_REEL.json (champ robot)")
                    return None
                return v
            L.version_distante = version_distante
        if "pont_reel.py" not in lanceur_robot.COMMUNS:
            lanceur_robot.COMMUNS = tuple(lanceur_robot.COMMUNS) + ("pont_reel.py",)


def activer_essais(dossier: Path, faux_mt5=None, compte: int | None = None):
    """Pour les essais du robot réel (bac à sable) : mode réel sur le faux terminal, autorisation écrite dans le
    dossier d'essai (jamais ailleurs)."""
    import pont_mt5 as pont
    import acces_robot
    activer(pont, Path(dossier), acces_robot)
    if faux_mt5 is not None:
        faux_mt5.mode_compte = faux_mt5.ACCOUNT_TRADE_MODE_REAL
        faux_mt5.devise = "USC"
        n = compte or faux_mt5.FAUX_LOGIN
        (Path(dossier) / FICHIER_AUTORISATION).write_text(json.dumps({"compte": n, "phrase": PHRASE}), encoding="utf-8")
    return pont


def main(args) -> None:
    """Boucle du pont réel (appelée par pont_mt5.main si --reel)."""
    import logging
    import sys
    import time
    from logging.handlers import RotatingFileHandler
    import pont_mt5 as pont           # pont_mt5.main a deja enregistre ce module sous ce nom (une seule copie)
    import acces_robot
    import lanceur_robot
    activer(pont, pont.ICI, acces_robot, lanceur_robot)
    if args.depot:
        pont.DEPOT = Path(args.depot).resolve()
    pont.log.setLevel(logging.INFO)
    for h in (RotatingFileHandler(pont.ICI / "pont.log", maxBytes=2_000_000, backupCount=2, encoding="utf-8"),
              logging.StreamHandler()):
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s REEL %(message)s"))
        pont.log.addHandler(h)
    garde = pont.verrou()  # noqa: F841
    branche = pont.git("rev-parse", "--abbrev-ref", "HEAD")[1].strip()
    if branche != pont.BRANCHE:
        sys.exit(f"Le depot doit etre sur la branche {pont.BRANCHE} (actuellement : {branche or 'inconnue'}).")
    if not args.terminal:
        sys.exit("--terminal obligatoire en mode reel (chemin du terminal64.exe du 2e MT5, celui du compte cent).")
    import MetaTrader5
    mt5 = pont.TerminalChemin(MetaTrader5, args.terminal)
    with pont.VERROU:
        mt5.initialize()
    sortie, fichier_local = pont.DEPOT / pont.REL_MT5, pont.ICI / "pont_local.json"
    lanceur = lanceur_robot.Lanceur(mt5, sortie)
    try:
        import tableau_bord
        tableau_bord.PORTS = PORTS_REEL
        with pont.VERROU:
            tableau_bord.SYMBOLE = symbole_or(mt5) or tableau_bord.SYMBOLE
        tableau_bord.demarrer(mt5, lanceur)
    except Exception:
        pont.log.exception("tableau de bord (le pont continue sans)")
    dernier_push = 0.0
    pont.log.info("pont REEL demarre")
    while True:
        debut = time.time()
        try:
            code, _, err = pont.git("fetch", "origin", pont.BRANCHE)
            if code != 0:
                pont.log.warning("git fetch : %s", err)
            with pont.VERROU:
                if mt5.terminal_info() is None:
                    mt5.initialize()
            try:
                if not args.une_fois:
                    lanceur.tour()
            except Exception:
                pont.log.exception("lanceur du robot (le pont continue)")
            with pont.VERROU:       # pas de consigne ni de demandes en réel : seul le robot réel trade
                etat = pont.passage(mt5, sortie, None, None, fichier_local, robot=lanceur.etat())
            pont.log.info("tour : %s", etat["arret"] or "ordres autorises")
            if not args.sans_push and time.time() - dernier_push >= pont.PERIODE_PUSH and pont.publier():
                dernier_push = time.time()
        except Exception:
            pont.log.exception("tour en erreur (le pont continue)")
        if args.une_fois:
            lanceur.arreter("fin du tour unique")
            break
        while time.time() - debut < pont.PERIODE_BOUCLE:
            time.sleep(5)
            try:
                lanceur.surveiller()
            except Exception:
                pont.log.exception("surveillance du robot")
