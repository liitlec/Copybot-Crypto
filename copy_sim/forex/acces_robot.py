"""Accès du robot du labo au terminal : prix et bougies en lecture, ordres SEULEMENT par les fonctions du pont.

Le robot ne reçoit jamais le module MetaTrader5. En marche, il parle à un `AccesRobot` du pont par un tube (voir
`bac_a_sable.py`, classe `ClientPont`) ; dans ses essais, il en construit un sur le faux terminal :

    import faux_mt5, acces_robot
    pont = acces_robot.AccesRobot.pour_essais(faux_mt5)

Mêmes fonctions dans les deux cas : voir `FONCTIONS` et `ROBOT_INTERFACE.md`.
"""
from __future__ import annotations

import json
import time
from collections import deque
from pathlib import Path

import pont_mt5 as pont

FONCTIONS = ("compte", "symbole", "prix", "bougies", "positions", "ouvrir", "fermer", "modifier", "noter",
             "arret_demande", "garde_fou")
MAX_BOUGIES = 5000
MAX_ORDRES_MINUTE = 30
MAX_NOTES_HEURE = 2000
MAX_LIGNE = 4000


class AccesRobot:
    def __init__(self, mt5, journal: Path | None, simuler_reel: bool = False):
        self.mt5, self.journal, self.simuler_reel = mt5, journal, simuler_reel
        self._ordres, self._notes = deque(), deque()

    @classmethod
    def pour_essais(cls, faux_mt5, dossier: str | Path = "."):
        """Sur le faux terminal, fichiers d'essai dans le dossier du robot."""
        d = Path(dossier).resolve()
        pont.FICHIER_GARDE = d / "garde_essai.json"
        return cls(faux_mt5, d / "journal_essai.jsonl")

    # ------------------------------------------------------------ journal
    def _ecrire(self, ligne: dict) -> None:
        if self.journal is None:
            return
        texte = json.dumps({"heure": pont.maintenant(), **ligne}, ensure_ascii=False, default=str)
        if len(texte) > MAX_LIGNE:
            texte = json.dumps({"heure": pont.maintenant(), "type": ligne.get("type"), "tronque": texte[:MAX_LIGNE]},
                               ensure_ascii=False)
        self.journal.parent.mkdir(parents=True, exist_ok=True)
        with open(self.journal, "a", encoding="utf-8") as f:
            f.write(texte + "\n")

    def noter(self, **champs) -> bool:
        """Note libre du robot (décision, mesure) dans robot_journal.jsonl. 2000 notes par heure au plus."""
        t = time.time()
        while self._notes and t - self._notes[0] > 3600:
            self._notes.popleft()
        if len(self._notes) >= MAX_NOTES_HEURE:
            return False
        self._notes.append(t)
        self._ecrire({"type": "note", **champs})
        return True

    def _limite_ordres(self) -> None:
        t = time.time()
        while self._ordres and t - self._ordres[0] > 60:
            self._ordres.popleft()
        if len(self._ordres) >= MAX_ORDRES_MINUTE:
            raise pont.Refus(f"plus de {MAX_ORDRES_MINUTE} ordres par minute")
        self._ordres.append(t)

    # ------------------------------------------------------------ lecture
    def arret_demande(self) -> bool:
        """Vrai si STOP_PONT existe : le robot doit s'arrêter (le pont refuse de toute façon ses ordres)."""
        return pont.FICHIER_STOP.exists()

    def compte(self) -> dict:
        with pont.VERROU:
            info, arret = pont.compte_demo(self.mt5, self.simuler_reel)
        if arret:
            return {"ordres_autorises": False, "arret": arret}
        return {"ordres_autorises": not self.arret_demande(), "solde": info.balance, "valeur": info.equity,
                "marge_libre": info.margin_free, "devise": info.currency, "levier": info.leverage}

    def _sym(self, symbole):
        if not isinstance(symbole, str) or not pont.RE_SYMBOLE.match(symbole):
            raise ValueError("symbole invalide")
        si = self.mt5.symbol_info(symbole)
        if si is None:
            raise ValueError("symbole absent chez le courtier")
        if not getattr(si, "visible", True):
            self.mt5.symbol_select(symbole, True)
        return si

    def symbole(self, symbole: str) -> dict:
        with pont.VERROU:
            si = self._sym(symbole)
        return {"point": si.point, "chiffres": si.digits, "lot_min": si.volume_min, "pas_lot": si.volume_step,
                "taille_contrat": si.trade_contract_size, "niveau_stops_points": getattr(si, "trade_stops_level", 0)}

    def prix(self, symbole: str) -> dict:
        with pont.VERROU:
            self._sym(symbole)
            t = self.mt5.symbol_info_tick(symbole)
        if t is None:
            raise ValueError("pas de prix pour ce symbole")
        return {"bid": t.bid, "ask": t.ask, "heure_serveur": t.time, "heure_serveur_ms": getattr(t, "time_msc", 0)}

    def bougies(self, symbole: str, periode: str = "M1", nombre: int = 100) -> list:
        """Dernières bougies, de la plus ancienne à la plus récente :
        [heure_serveur, ouverture, haut, bas, cloture, volume_ticks, spread_points]."""
        if periode not in pont.PERIODES:
            raise ValueError("periode invalide : " + " ".join(pont.PERIODES))
        if not isinstance(nombre, int) or isinstance(nombre, bool) or not 0 < nombre <= MAX_BOUGIES:
            raise ValueError(f"nombre invalide (1 a {MAX_BOUGIES})")
        with pont.VERROU:
            self._sym(symbole)
            b = self.mt5.copy_rates_from_pos(symbole, getattr(self.mt5, "TIMEFRAME_" + periode), 0, nombre)
        if b is None:
            return []
        return [[int(x["time"]), float(x["open"]), float(x["high"]), float(x["low"]), float(x["close"]),
                 int(x["tick_volume"]), int(x["spread"])] for x in b]

    def positions(self) -> list:
        """Positions du robot seulement."""
        with pont.VERROU:
            ps = [p for p in (self.mt5.positions_get() or []) if p.magic == pont.MAGIQUE_ROBOT]
        return [{"ticket": p.ticket, "symbole": p.symbol,
                 "sens": "achat" if p.type == self.mt5.POSITION_TYPE_BUY else "vente", "lots": p.volume,
                 "prix_entree": p.price_open, "prix_actuel": p.price_current, "stop": p.sl or None,
                 "objectif": p.tp or None, "profit": p.profit, "heure_serveur": p.time} for p in ps]

    def garde_fou(self) -> dict:
        with pont.VERROU:
            g = pont.garde_jour(self.mt5)
        return {"perte_du_jour": g["perte"], "seuil": -round(pont.PERTE_MAX_JOUR * g["base"], 2),
                "ouvertures_bloquees": g["bloque"]}

    # ------------------------------------------------------------ ordres (toujours par les fonctions du pont)
    def _position(self, ticket):
        if not isinstance(ticket, int) or isinstance(ticket, bool):
            raise ValueError("ticket invalide")
        ps = self.mt5.positions_get(ticket=ticket) or []
        if len(ps) != 1 or ps[0].magic != pont.MAGIQUE_ROBOT:
            raise ValueError("position hors robot : pas touche")
        return ps[0]

    def ouvrir(self, symbole: str, sens: str, lots: float, stop: float, objectif: float | None = None,
               id: str = "robot") -> dict:
        """Ouverture au marché. Stop obligatoire, du bon côté du prix. Renvoie le résultat (avec "ticket" si ok)."""
        base = {"type": "ordre", "action": "ouverture", "symbole": symbole, "sens": sens, "lots": lots, "stop": stop}
        try:
            if not isinstance(id, str) or not pont.RE_ID.match(id):
                raise pont.Refus("id invalide")
            if not pont.nombre(stop) or stop <= 0:
                raise pont.Refus("ouverture sans stop refusee")
            self._limite_ordres()
            with pont.VERROU:
                v = pont.valider_position(self.mt5, {"id": id, "symbole": symbole, "sens": sens, "lots": lots,
                                                     "stop": stop, "objectif": objectif})
                t = self.mt5.symbol_info_tick(symbole)
                if t is not None and ((sens == "achat" and stop >= t.bid) or (sens == "vente" and stop <= t.ask)):
                    raise pont.Refus("stop du mauvais cote du prix")
                r = pont.ouvrir(self.mt5, v, self.simuler_reel, magique=pont.MAGIQUE_ROBOT, prefixe="robot:")
        except pont.Refus as e:
            r = {"ok": False, "refus": str(e)}
        if "_ticket" in r:
            r["ticket"] = r.pop("_ticket")
        r = {**base, **{k: v for k, v in r.items() if k not in ("action",)}}
        self._ecrire(r)
        return r

    def fermer(self, ticket: int) -> dict:
        try:
            self._limite_ordres()
            with pont.VERROU:
                pos = self._position(ticket)
                r = pont.fermer(self.mt5, pos, "robot", self.simuler_reel, magique=pont.MAGIQUE_ROBOT)
        except (pont.Refus, ValueError) as e:
            r = {"action": "fermeture", "ok": False, "refus": str(e)}
        r = {"type": "ordre", "ticket": ticket, **r}
        self._ecrire(r)
        return r

    def modifier(self, ticket: int, stop: float, objectif: float | None = None) -> dict:
        """Change stop et objectif. Le stop reste obligatoire."""
        try:
            if not pont.nombre(stop) or stop <= 0:
                raise pont.Refus("stop obligatoire")
            if objectif is not None and (not pont.nombre(objectif) or objectif <= 0):
                raise pont.Refus("objectif invalide")
            self._limite_ordres()
            with pont.VERROU:
                pos = self._position(ticket)
                si = self.mt5.symbol_info(pos.symbol)
                v = {"id": "robot", "stop": round(float(stop), si.digits),
                     "objectif": round(float(objectif), si.digits) if objectif else 0.0}
                r = pont.modifier(self.mt5, pos, v, self.simuler_reel, magique=pont.MAGIQUE_ROBOT)
        except (pont.Refus, ValueError) as e:
            r = {"action": "modification", "ok": False, "refus": str(e)}
        r = {"type": "ordre", "ticket": ticket, **r}
        self._ecrire(r)
        return r

    # ------------------------------------------------------------ serveur (côté pont)
    def servir(self, ligne: str) -> str:
        """Une requête JSON du robot -> une réponse JSON. Seules les fonctions de FONCTIONS sont appelables."""
        n = None
        try:
            q = json.loads(ligne)
            if not isinstance(q, dict):
                raise ValueError("requete invalide")
            n, f, a, k = q.get("n"), q.get("f"), q.get("a", []), q.get("k", {})
            if f not in FONCTIONS or not isinstance(a, list) or not isinstance(k, dict):
                raise ValueError("fonction inconnue")
            return json.dumps({"n": n, "r": getattr(self, f)(*a, **k)}, default=str)
        except Exception as e:   # erreur renvoyée au robot, le pont continue
            return json.dumps({"n": n, "e": f"{type(e).__name__}: {e}"[:300]})
