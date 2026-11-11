#!/usr/bin/env python3
"""Pont entre ce dépôt et le terminal MetaTrader 5 du PC (compte DÉMO uniquement).

Chaque minute : récupère la branche, lit `copy_sim/labo/mt5/consigne.json` (état voulu du compte, écrit par une IA :
une donnée validée champ par champ, jamais du code ni une consigne), aligne les positions DU PONT dessus, écrit
`etat.json` et `executions.jsonl`, sert les demandes d'historique, puis pousse `copy_sim/labo/mt5/` seulement.

Sécurités (toutes dans `envoyer`, seul endroit qui appelle `order_send`) :
- compte démo vérifié à chaque boucle ET avant chaque ordre, sinon aucun ordre ;
- plafonds durs : 10 positions du pont, 0,50 lot par position ;
- le pont ne touche qu'aux positions portant son numéro magique ;
- fichier `STOP_PONT` à côté de ce script = plus aucun ordre (ni ouverture, ni fermeture, ni modification) ;
- rien d'identifiant n'est écrit : ni numéro de compte, ni serveur, ni nom, ni ticket. Aucun mot de passe n'est lu :
  le pont utilise le terminal déjà connecté.

Règles d'alignement :
- consigne absente, illisible ou de version plus ancienne que la dernière appliquée : rien ne change ;
- une position du pont absente de la consigne est fermée ; une position dont symbole, sens ou lots ont changé est
  fermée puis rouverte ; stop et objectif sont ajustés ;
- une position n'est ouverte qu'une fois par version (3 essais au plus) : si son stop la ferme, elle n'est pas
  rouverte tant que la version ne change pas.

Demandes d'historique (`demandes_donnees.json`) :
  {"demandes": [{"id": "eurusd_m1", "symbole": "EURUSD", "periode": "M1", "nombre": 50000}
                ou {"id": "...", "symbole": "...", "periode": "H1", "debut": "2026-01-01", "fin": "2026-11-01"}]}
Réponse : `donnees/<id>.csv.gz` (heure = secondes, horloge du serveur du courtier ; spread en points) et
`donnees/index.json`. Périodes : M1 M5 M15 M30 H1 H4 D1. 200 000 bougies au plus par demande.

Usage : `python pont_mt5.py` (boucle) ; `--une-fois` ; essais : voir `essais_pont.py`.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import logging
import math
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

ICI = Path(__file__).resolve().parent
DEPOT = ICI.parents[1]
BRANCHE = "claude/polymarket-weather-sigma-resolution-olv0bs"
REL_MT5 = "copy_sim/labo/mt5"
FICHIER_STOP = ICI / "STOP_PONT"

VERSION_PONT = 1
MAGIQUE = 20261111          # numéro magique du pont : il ne touche à rien d'autre
MAX_POSITIONS = 10          # plafond dur
MAX_LOTS = 0.50             # plafond dur, par position
MAX_ESSAIS = 3              # essais d'ouverture ou de modification par version
PERIODE_BOUCLE = 60         # secondes
PERIODE_PUSH = 300          # secondes
MAX_BARRES = 200_000
MAX_DEMANDES = 20
MAX_DEMANDES_PAR_TOUR = 2
MAX_DOSSIER_DONNEES = 60 * 1024 * 1024
MAX_TAILLE_JSON = 100_000
PERIODES = ("M1", "M5", "M15", "M30", "H1", "H4", "D1")
RE_ID = re.compile(r"^[A-Za-z0-9_-]{1,20}$")
RE_SYMBOLE = re.compile(r"^[A-Za-z0-9._#+-]{1,32}$")
RETCODES_OK = (10008, 10009, 10010)   # placé, exécuté, exécuté en partie
RETCODE_REMPLISSAGE = 10030
RETCODE_MARCHE_FERME = 10018

log = logging.getLogger("pont")


class Refus(Exception):
    """Ordre ou donnée refusés par une sécurité du pont."""


def maintenant() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ecrire_json(chemin: Path, objet) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    tmp = chemin.with_suffix(chemin.suffix + ".tmp")
    tmp.write_text(json.dumps(objet, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, chemin)


def lire_json(chemin: Path, defaut):
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defaut


def noter(sortie: Path, **champs) -> None:
    """Ajoute une ligne à executions.jsonl."""
    sortie.mkdir(parents=True, exist_ok=True)
    ligne = {"heure": maintenant(), **champs}
    with open(sortie / "executions.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
    log.info("execution %s", ligne)


def nombre(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


# ------------------------------------------------------------------ sécurités

def compte_demo(mt5, simuler_reel: bool = False):
    """Renvoie (info du compte, raison d'arrêt ou None). Sans démo confirmée : aucun ordre."""
    info = mt5.account_info()
    if info is None:
        return None, "terminal MT5 non connecte a un compte : aucun ordre"
    mode = mt5.ACCOUNT_TRADE_MODE_REAL if simuler_reel else info.trade_mode
    if mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
        return None, "compte non demo : aucun ordre"   # et rien de ce compte n'est publié
    return info, None


def positions_pont(mt5) -> list:
    return [p for p in (mt5.positions_get() or []) if p.magic == MAGIQUE]


def envoyer(mt5, demande: dict, simuler_reel: bool = False):
    """SEUL endroit qui appelle order_send. Revérifie toutes les sécurités juste avant l'ordre."""
    if FICHIER_STOP.exists():
        raise Refus("STOP_PONT present")
    _, arret = compte_demo(mt5, simuler_reel)
    if arret:
        raise Refus(arret)
    if demande.get("magic") != MAGIQUE:
        raise Refus("numero magique absent")
    action = demande.get("action")
    if "position" in demande:                      # fermeture ou modification : une position du pont seulement
        if action not in (mt5.TRADE_ACTION_DEAL, mt5.TRADE_ACTION_SLTP):
            raise Refus("action non permise")
        pos = mt5.positions_get(ticket=demande["position"]) or []
        if len(pos) != 1 or pos[0].magic != MAGIQUE:
            raise Refus("position hors pont : pas touche")
        if action == mt5.TRADE_ACTION_DEAL and demande.get("volume", 0) > pos[0].volume + 1e-9:
            raise Refus("volume de fermeture superieur a la position")
    elif action == mt5.TRADE_ACTION_DEAL:          # ouverture
        vol = demande.get("volume")
        if not nombre(vol) or not 0 < vol <= MAX_LOTS + 1e-9:
            raise Refus(f"plafond : {MAX_LOTS} lot par position")
        if len(positions_pont(mt5)) >= MAX_POSITIONS:
            raise Refus(f"plafond : {MAX_POSITIONS} positions")
    else:
        raise Refus("action non permise")
    return mt5.order_send(demande)


# ------------------------------------------------------------------ validation de la consigne

def lire_consigne(texte: str):
    """Renvoie (version, liste brute des positions). Lève Refus si la consigne entière est inacceptable."""
    if len(texte) > MAX_TAILLE_JSON:
        raise Refus("consigne trop grosse")
    try:
        c = json.loads(texte)
    except ValueError:
        raise Refus("consigne illisible (JSON)")
    if not isinstance(c, dict):
        raise Refus("consigne illisible (pas un objet)")
    version = c.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or not 0 < version < 10**12:
        raise Refus("version invalide")
    brutes = c.get("positions")
    if not isinstance(brutes, list):
        raise Refus("positions invalide")
    if len(brutes) > MAX_POSITIONS:
        raise Refus(f"plafond : {len(brutes)} positions demandees, {MAX_POSITIONS} au plus ; consigne refusee en entier")
    ids = []
    for b in brutes:
        if not isinstance(b, dict) or not isinstance(b.get("id"), str) or not RE_ID.match(b["id"]):
            raise Refus("id de position invalide (lettres, chiffres, _ et -, 20 caracteres au plus)")
        ids.append(b["id"])
    if len(set(ids)) != len(ids):
        raise Refus("id en double")
    return version, brutes


def valider_position(mt5, b: dict) -> dict:
    """Valide une position champ par champ. Lève Refus avec la raison."""
    sym = b.get("symbole")
    if not isinstance(sym, str) or not RE_SYMBOLE.match(sym):
        raise Refus("symbole invalide")
    si = mt5.symbol_info(sym)
    if si is None:
        raise Refus("symbole absent chez le courtier")
    if not getattr(si, "visible", True):
        mt5.symbol_select(sym, True)
    sens = b.get("sens")
    if sens not in ("achat", "vente"):
        raise Refus("sens invalide (achat ou vente)")
    lots = b.get("lots")
    if not nombre(lots) or lots <= 0:
        raise Refus("lots invalide")
    if lots > MAX_LOTS + 1e-9:
        raise Refus(f"plafond : {lots} lot demande, {MAX_LOTS} au plus par position")
    pas = si.volume_step or 0.01
    if lots < si.volume_min - 1e-9 or abs(lots / pas - round(lots / pas)) > 1e-6:
        raise Refus(f"lots hors grille du courtier (minimum {si.volume_min}, pas {pas})")
    prix = {}
    for champ in ("stop", "objectif"):
        v = b.get(champ)
        if v is not None and (not nombre(v) or v <= 0):
            raise Refus(f"{champ} invalide")
        prix[champ] = round(float(v), si.digits) if v is not None else 0.0
    return {"id": b["id"], "symbole": sym, "sens": sens, "lots": round(round(lots / pas) * pas, 8), **prix}


# ------------------------------------------------------------------ ordres

def _spread(mt5, sym):
    t, si = mt5.symbol_info_tick(sym), mt5.symbol_info(sym)
    if t is None or si is None or not si.point or t.ask <= 0 or t.bid <= 0:
        return None, None, None
    return t, si, round((t.ask - t.bid) / si.point, 1)


def _ordre_marche(mt5, demande: dict, si, simuler_reel: bool):
    """Envoie un ordre au marché en essayant les modes de remplissage acceptés par le courtier."""
    modes = [mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_RETURN]
    permis = getattr(si, "filling_mode", 0)
    modes.sort(key=lambda m: 0 if (m == mt5.ORDER_FILLING_FOK and permis & 1)
               or (m == mt5.ORDER_FILLING_IOC and permis & 2) else 1)
    res = None
    for m in modes:
        res = envoyer(mt5, {**demande, "type_filling": m}, simuler_reel)
        if res is None or res.retcode != RETCODE_REMPLISSAGE:
            break
    return res


def _resultat(mt5, res) -> dict:
    if res is None:
        return {"ok": False, "retcode": None, "refus": "pas de reponse du terminal " + str(mt5.last_error())[:80]}
    ok = res.retcode in RETCODES_OK
    d = {"ok": ok, "retcode": res.retcode, "prix_obtenu": res.price or None}
    if not ok:
        d["refus"] = "courtier : " + str(res.comment)[:60]
    return d


def ouvrir(mt5, v: dict, simuler_reel: bool) -> dict:
    t, si, spread = _spread(mt5, v["symbole"])
    base = {"action": "ouverture", "id": v["id"], "symbole": v["symbole"], "sens": v["sens"], "lots": v["lots"]}
    if t is None:
        return {**base, "ok": False, "refus": "pas de prix pour ce symbole"}
    achat = v["sens"] == "achat"
    prix = t.ask if achat else t.bid
    demande = {"action": mt5.TRADE_ACTION_DEAL, "symbol": v["symbole"], "volume": v["lots"],
               "type": mt5.ORDER_TYPE_BUY if achat else mt5.ORDER_TYPE_SELL, "price": prix,
               "sl": v["stop"], "tp": v["objectif"], "deviation": 20, "magic": MAGIQUE,
               "comment": "pont:" + v["id"], "type_time": mt5.ORDER_TIME_GTC}
    base.update(prix_demande=prix, spread_points=spread, stop=v["stop"] or None, objectif=v["objectif"] or None)
    try:
        res = _ordre_marche(mt5, demande, si, simuler_reel)
    except Refus as e:
        return {**base, "ok": False, "refus": str(e)}
    r = {**base, **_resultat(mt5, res)}
    if r["ok"]:
        r["_ticket"] = res.order
    return r


def fermer(mt5, pos, ident: str, simuler_reel: bool) -> dict:
    t, si, spread = _spread(mt5, pos.symbol)
    achat = pos.type == mt5.POSITION_TYPE_BUY
    base = {"action": "fermeture", "id": ident, "symbole": pos.symbol, "sens": "achat" if achat else "vente",
            "lots": pos.volume}
    if t is None:
        return {**base, "ok": False, "refus": "pas de prix pour ce symbole"}
    prix = t.bid if achat else t.ask
    demande = {"action": mt5.TRADE_ACTION_DEAL, "position": pos.ticket, "symbol": pos.symbol, "volume": pos.volume,
               "type": mt5.ORDER_TYPE_SELL if achat else mt5.ORDER_TYPE_BUY, "price": prix, "deviation": 20,
               "magic": MAGIQUE, "comment": "pont:fin", "type_time": mt5.ORDER_TIME_GTC}
    base.update(prix_demande=prix, spread_points=spread, prix_entree=pos.price_open)
    try:
        res = _ordre_marche(mt5, demande, si, simuler_reel)
    except Refus as e:
        return {**base, "ok": False, "refus": str(e)}
    return {**base, **_resultat(mt5, res)}


def modifier(mt5, pos, v: dict, simuler_reel: bool) -> dict:
    base = {"action": "modification", "id": v["id"], "symbole": pos.symbol, "stop": v["stop"] or None,
            "objectif": v["objectif"] or None}
    demande = {"action": mt5.TRADE_ACTION_SLTP, "position": pos.ticket, "symbol": pos.symbol,
               "sl": v["stop"], "tp": v["objectif"], "magic": MAGIQUE}
    try:
        res = envoyer(mt5, demande, simuler_reel)
    except Refus as e:
        return {**base, "ok": False, "refus": str(e)}
    r = {**base, **_resultat(mt5, res)}
    r.pop("prix_obtenu", None)
    return r


def identite(pos, local: dict) -> str:
    ident = local.get("tickets", {}).get(str(pos.ticket))
    if ident:
        return ident
    c = getattr(pos, "comment", "") or ""
    if c.startswith("pont:") and RE_ID.match(c[5:]):
        return c[5:]
    return "?"


def aligner(mt5, version: int, brutes: list, local: dict, sortie: Path, simuler_reel: bool) -> None:
    nouvelle = version > local.get("version", 0)
    if nouvelle:
        local.update(version=version, essais={}, ouvertes=[], sltp={}, attente=[])
    voulues, refusees = {}, set()
    for b in brutes:
        try:
            voulues[b["id"]] = valider_position(mt5, b)
        except Refus as e:
            refusees.add(b["id"])
            if nouvelle:
                noter(sortie, version=version, action="refus", id=b["id"], refus=str(e))

    def journal(r: dict):
        r.pop("_ticket", None)
        noter(sortie, version=version, **r)

    # 1. positions du pont existantes : fermer, garder, ajuster
    presentes = set()
    for pos in positions_pont(mt5):
        ident = identite(pos, local)
        v = voulues.get(ident)
        if ident in refusees:
            presentes.add(ident)
            continue
        sens = "achat" if pos.type == mt5.POSITION_TYPE_BUY else "vente"
        if v is None or v["symbole"] != pos.symbol or v["sens"] != sens or abs(v["lots"] - pos.volume) > 1e-9:
            r = fermer(mt5, pos, ident, simuler_reel)
            cle = f"{r.get('retcode')}|{r.get('refus')}"
            if r["ok"]:
                local.get("tickets", {}).pop(str(pos.ticket), None)
                local.get("echecs", {}).pop(str(pos.ticket), None)
                journal(r)
            else:
                presentes.add(ident)
                if local.setdefault("echecs", {}).get(str(pos.ticket)) != cle:   # même échec : noté une seule fois
                    local["echecs"][str(pos.ticket)] = cle
                    journal(r)
            continue
        presentes.add(ident)
        if ident not in local["ouvertes"]:
            local["ouvertes"].append(ident)
        si = mt5.symbol_info(pos.symbol)
        tol = (si.point if si else 1e-5) / 2
        if abs(pos.sl - v["stop"]) > tol or abs(pos.tp - v["objectif"]) > tol:
            if local["sltp"].get(ident, 0) < MAX_ESSAIS:
                r = modifier(mt5, pos, v, simuler_reel)
                local["sltp"][ident] = 0 if r["ok"] else local["sltp"].get(ident, 0) + 1
                journal(r)

    # 2. ouvrir ce qui manque (une fois par version)
    for ident, v in voulues.items():
        if ident in presentes or ident in local["ouvertes"] or local["essais"].get(ident, 0) >= MAX_ESSAIS:
            continue
        r = ouvrir(mt5, v, simuler_reel)
        if r.get("retcode") == RETCODE_MARCHE_FERME:      # marché fermé : on réessaiera, noté une seule fois
            if ident not in local["attente"]:
                local["attente"].append(ident)
                journal(r)
            continue
        local["essais"][ident] = local["essais"].get(ident, 0) + 1
        if r["ok"]:
            local["ouvertes"].append(ident)
            local.setdefault("tickets", {})[str(r["_ticket"])] = ident
        journal(r)


# ------------------------------------------------------------------ état publié

def construire_etat(mt5, info, arret, statut: str, local: dict, symboles: set) -> dict:
    e = {"ecrit": maintenant(), "pont": VERSION_PONT, "ordres_autorises": arret is None, "arret": arret,
         "consigne": statut, "version_appliquee": local.get("version", 0),
         "plafonds": {"positions": MAX_POSITIONS, "lots_par_position": MAX_LOTS}}
    if info is None:               # pas de compte démo confirmé : on ne publie rien du compte
        return e
    e.update(solde=info.balance, valeur=info.equity, marge_libre=info.margin_free, devise=info.currency,
             levier=info.leverage, positions=[], symboles={})
    for pos in positions_pont(mt5):
        symboles.add(pos.symbol)
        e["positions"].append({
            "id": identite(pos, local), "symbole": pos.symbol,
            "sens": "achat" if pos.type == mt5.POSITION_TYPE_BUY else "vente", "lots": pos.volume,
            "prix_entree": pos.price_open, "prix_actuel": pos.price_current, "stop": pos.sl or None,
            "objectif": pos.tp or None, "profit": pos.profit, "swap": pos.swap, "ouverte_heure_serveur": pos.time})
    for sym in sorted(symboles):
        t, si, spread = _spread(mt5, sym)
        if t is None:
            continue
        e["symboles"][sym] = {"bid": t.bid, "ask": t.ask, "spread_points": spread, "point": si.point,
                              "chiffres": si.digits, "lot_min": si.volume_min, "pas_lot": si.volume_step,
                              "taille_contrat": si.trade_contract_size, "heure_serveur": t.time}
    return e


# ------------------------------------------------------------------ historiques

def _date(s):
    if not isinstance(s, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        raise Refus("date invalide (AAAA-MM-JJ)")
    try:
        return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise Refus("date invalide (AAAA-MM-JJ)")


def servir_demandes(mt5, texte: str | None, sortie: Path, symboles: set) -> None:
    if not texte or len(texte) > MAX_TAILLE_JSON:
        return
    try:
        demandes = json.loads(texte).get("demandes")
    except (ValueError, AttributeError):
        return
    if not isinstance(demandes, list):
        return
    dossier = sortie / "donnees"
    index = lire_json(dossier / "index.json", {})
    if not isinstance(index, dict):
        index = {}
    servies = 0
    for d in demandes[:MAX_DEMANDES]:
        if not isinstance(d, dict) or not isinstance(d.get("id"), str) or not RE_ID.match(d["id"]):
            continue
        ident = d["id"]
        cle = hashlib.sha1(json.dumps(d, sort_keys=True).encode()).hexdigest()[:12]
        if isinstance(index.get(ident), dict) and index[ident].get("cle") == cle:
            continue                                   # déjà servie (ou déjà refusée) telle quelle
        if servies >= MAX_DEMANDES_PAR_TOUR:
            break
        servies += 1
        fiche = {"cle": cle, "ecrit": maintenant()}
        try:
            sym, per = d.get("symbole"), d.get("periode")
            if not isinstance(sym, str) or not RE_SYMBOLE.match(sym) or mt5.symbol_info(sym) is None:
                raise Refus("symbole absent chez le courtier")
            if per not in PERIODES:
                raise Refus("periode invalide : " + " ".join(PERIODES))
            mt5.symbol_select(sym, True)
            symboles.add(sym)
            tf = getattr(mt5, "TIMEFRAME_" + per)
            if "nombre" in d:
                n = d["nombre"]
                if not isinstance(n, int) or isinstance(n, bool) or not 0 < n <= MAX_BARRES:
                    raise Refus(f"nombre invalide (1 a {MAX_BARRES})")
                barres = mt5.copy_rates_from_pos(sym, tf, 0, n)
            else:
                debut, fin = _date(d.get("debut")), _date(d.get("fin"))
                if fin <= debut:
                    raise Refus("fin avant debut")
                barres = mt5.copy_rates_range(sym, tf, debut, fin)
            if barres is None or len(barres) == 0:
                raise Refus("aucune bougie renvoyee par le terminal")
            if len(barres) > MAX_BARRES:
                barres, fiche["tronque"] = barres[-MAX_BARRES:], True
            if sum(f.stat().st_size for f in dossier.glob("*.csv.gz")) > MAX_DOSSIER_DONNEES:
                raise Refus("dossier donnees plein : retirer d'anciennes demandes")
            tampon = io.StringIO()
            w = csv.writer(tampon, lineterminator="\n")
            w.writerow(["heure", "ouverture", "haut", "bas", "cloture", "volume_ticks", "spread_points"])
            for b in barres:
                w.writerow([int(b["time"]), float(b["open"]), float(b["high"]), float(b["low"]), float(b["close"]),
                            int(b["tick_volume"]), int(b["spread"])])
            dossier.mkdir(parents=True, exist_ok=True)
            with gzip.GzipFile(dossier / f"{ident}.csv.gz", "wb", mtime=0) as f:
                f.write(tampon.getvalue().encode())
            fiche.update(symbole=sym, periode=per, lignes=len(barres), premiere=int(barres[0]["time"]),
                         derniere=int(barres[-1]["time"]), fichier=f"{ident}.csv.gz")
        except Refus as e:
            fiche["erreur"] = str(e)
        index[ident] = fiche
        log.info("demande %s : %s", ident, fiche)
    if servies:
        ecrire_json(dossier / "index.json", index)


# ------------------------------------------------------------------ un passage complet

def passage(mt5, sortie: Path, texte_consigne: str | None, texte_demandes: str | None, fichier_local: Path,
            simuler_reel: bool = False) -> dict:
    """Un tour : sécurités, alignement, historiques, etat.json. Renvoie l'état écrit."""
    local = lire_json(fichier_local, {})
    if not isinstance(local, dict):
        local = {}
    for cle, vide in (("essais", {}), ("ouvertes", []), ("sltp", {}), ("attente", []), ("tickets", {}),
                      ("echecs", {})):
        local.setdefault(cle, vide)

    info, arret = None, None
    if mt5.terminal_info() is None and not mt5.initialize():
        arret = "terminal MT5 injoignable : aucun ordre"
    else:
        info, arret = compte_demo(mt5, simuler_reel)
        ti = mt5.terminal_info()
        if arret is None and ti is not None and not ti.trade_allowed:
            arret = "trading algorithmique desactive dans le terminal : aucun ordre"
    if FICHIER_STOP.exists():
        arret = "STOP_PONT present : aucun ordre"

    symboles: set = set()
    version, brutes = None, None
    if texte_consigne is None:
        statut = "consigne absente : rien ne change"
    else:
        try:
            version, brutes = lire_consigne(texte_consigne)
            if version < local.get("version", 0):
                statut = f"version {version} plus ancienne que {local['version']} : ignoree"
                version = None
            else:
                statut = f"version {version} lue"
        except Refus as e:
            statut = f"consigne refusee : {e}"
            empreinte = hashlib.sha1(texte_consigne.encode()).hexdigest()[:12]
            if local.get("dernier_rejet") != empreinte:        # noté une seule fois par consigne fautive
                local["dernier_rejet"] = empreinte
                noter(sortie, action="refus", refus=str(e))

    if version is not None and arret is None:
        aligner(mt5, version, brutes, local, sortie, simuler_reel)
        statut = f"version {version} appliquee"
    elif version is not None:
        statut = f"version {version} en attente : {arret}"
    if brutes and info is not None:
        symboles.update(b["symbole"] for b in brutes if isinstance(b.get("symbole"), str)
                        and RE_SYMBOLE.match(b["symbole"]) and mt5.symbol_info(b["symbole"]) is not None)

    if info is not None:
        try:
            servir_demandes(mt5, texte_demandes, sortie, symboles)
        except Exception:
            log.exception("demandes d'historique")
    etat = construire_etat(mt5, info, arret, statut, local, symboles)
    ecrire_json(sortie / "etat.json", etat)
    ecrire_json(fichier_local, local)
    return etat


# ------------------------------------------------------------------ git

def git(*args, timeout=120):
    drapeaux = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        r = subprocess.run(["git", "-C", str(DEPOT), *args], capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace", creationflags=drapeaux)
        return r.returncode, r.stdout, r.stderr.strip()[-300:]
    except (OSError, subprocess.TimeoutExpired) as e:
        return 99, "", str(e)[:300]


def lire_distant(nom: str) -> str | None:
    code, sortie, _ = git("show", f"origin/{BRANCHE}:{REL_MT5}/{nom}")
    return sortie if code == 0 else None


def publier() -> bool:
    """Commit et push de copy_sim/labo/mt5/ seulement. Jamais de push forcé."""
    git("add", "--", REL_MT5)
    if git("diff", "--cached", "--quiet", "--", REL_MT5)[0] == 1:
        code, _, err = git("commit", "-q", "-m", "pont mt5 : etat et executions", "--", REL_MT5)
        if code != 0:
            log.error("git commit : %s", err)
            return False
    code, _, err = git("pull", "--rebase", "--autostash", "origin", BRANCHE)
    if code != 0:
        git("rebase", "--abort")
        log.error("git pull : %s", err)
        return False
    code, _, err = git("push", "origin", f"HEAD:{BRANCHE}")
    if code != 0:
        log.error("git push : %s", err)
    return code == 0


# ------------------------------------------------------------------ boucle

def verrou():
    """Une seule instance du pont (Windows)."""
    if os.name != "nt":
        return None
    import msvcrt
    f = open(ICI / "pont.verrou", "w")
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        sys.exit("Le pont tourne deja.")
    return f


def main() -> None:
    ap = argparse.ArgumentParser(description="Pont MT5 (demo uniquement)")
    ap.add_argument("--une-fois", action="store_true", help="un seul tour puis arret")
    ap.add_argument("--sans-push", action="store_true", help="ne pousse rien (essais)")
    args = ap.parse_args()

    log.setLevel(logging.INFO)
    for h in (RotatingFileHandler(ICI / "pont.log", maxBytes=2_000_000, backupCount=2, encoding="utf-8"),
              logging.StreamHandler()):
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(h)

    garde = verrou()  # noqa: F841 (garde le verrou ouvert)
    branche = git("rev-parse", "--abbrev-ref", "HEAD")[1].strip()
    if branche != BRANCHE:
        sys.exit(f"Le depot doit etre sur la branche {BRANCHE} (actuellement : {branche or 'inconnue'}).")
    import MetaTrader5 as mt5   # terminal déjà connecté : aucun identifiant, aucun mot de passe ici

    sortie, fichier_local = DEPOT / REL_MT5, ICI / "pont_local.json"
    dernier_push = 0.0
    log.info("pont demarre")
    while True:
        debut = time.time()
        try:
            code, _, err = git("fetch", "origin", BRANCHE)
            if code != 0:
                log.warning("git fetch : %s", err)
            etat = passage(mt5, sortie, lire_distant("consigne.json"), lire_distant("demandes_donnees.json"),
                           fichier_local)
            log.info("tour : %s%s", etat["consigne"], " | " + etat["arret"] if etat["arret"] else "")
            if not args.sans_push and time.time() - dernier_push >= PERIODE_PUSH and publier():
                dernier_push = time.time()
        except Exception:
            log.exception("tour en erreur (le pont continue)")
        if args.une_fois:
            break
        time.sleep(max(5.0, PERIODE_BOUCLE - (time.time() - debut)))


if __name__ == "__main__":
    main()
