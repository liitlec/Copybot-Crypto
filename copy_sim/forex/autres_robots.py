"""Export en LECTURE SEULE des positions et de l'historique des autres robots du compte démo (pas ceux du pont).

Toutes les 5 minutes, dans `copy_sim/labo/mt5/autres/` :
- `ouvertes.json` : positions ouvertes hors pont, avec un total par robot ;
- `historique.csv.gz` : positions fermées (une ligne par position), en entier la première fois, puis seulement les
  nouvelles (ajoutées en fin de fichier comme un nouveau bloc gzip, lisible d'un trait par gzip ou pandas).
Seules des fonctions de lecture du terminal sont appelées (positions_get, history_deals_get) : aucun ordre.
Rien d'identifiant : pas de numéro de compte, de serveur ni de nom ; à la place des tickets, un numéro relatif
stable (`n`), gardé hors dépôt dans `autres_numeros.json`. Heures = heure du serveur du courtier (secondes).
"""
from __future__ import annotations

import csv
import gzip
import io
import time
from datetime import datetime, timedelta
from pathlib import Path

import pont_mt5 as pont

PERIODE = 300
DEBUT = datetime(2020, 1, 1)
# numéro magique de base -> robot (lu dans les EA de Baptiste ; +1 par marché à partir de la base)
ROBOTS = [(701100, 701100, "BlockFIFO"), (702100, 702199, "BlockTrend"), (703100, 703199, "BlockRange"),
          (704100, 704199, "BlockGrille"), (705100, 705199, "BlockFinMois"), (712100, 712199, "BlockTrend_pari"),
          (715100, 715199, "BlockFinMois_pari"), (0, 0, "manuel")]
CHAMPS = ["n", "robot", "panier", "magique", "symbole", "sens", "lots", "ouverture_heure_serveur", "prix_entree",
          "fermeture_heure_serveur", "prix_sortie", "stop", "objectif", "fin", "commission", "swap", "resultat"]


def robot(magique: int) -> str:
    for bas, haut, nom in ROBOTS:
        if bas <= magique <= haut:
            return nom
    return f"inconnu_{magique}"


def panier(commentaire: str) -> str:
    """Préfixe du commentaire (ex. BT, BTS, BTI, BG) : le panier ou la variante du robot."""
    mot = (commentaire or "").split(" ")[0]
    return mot if mot.isalnum() and len(mot) <= 8 else ""


class Export:
    def __init__(self, mt5, sortie: Path, local: Path | None = None, avec_manuel: bool = True):
        self.mt5, self.sortie = mt5, Path(sortie)
        self.fichier_local = local or pont.ICI / "autres_numeros.json"
        self.avec_manuel = avec_manuel
        self.dernier = 0.0
        e = pont.lire_json(self.fichier_local, {})
        self.numeros = e.get("numeros", {}) if isinstance(e, dict) else {}
        self.exportees = set(e.get("exportees", [])) if isinstance(e, dict) else set()

    def _n(self, position_id: int) -> int:
        cle = str(position_id)
        if cle not in self.numeros:
            self.numeros[cle] = len(self.numeros) + 1
        return self.numeros[cle]

    def _garder(self, magique: int) -> bool:
        return magique not in pont.MAGIQUES and (self.avec_manuel or magique != 0)

    def ouvertes(self) -> dict:
        with pont.VERROU:
            ps = [p for p in (self.mt5.positions_get() or []) if self._garder(p.magic)]
        lignes, totaux = [], {}
        for p in sorted(ps, key=lambda p: p.time):
            r = robot(p.magic)
            lignes.append({"n": self._n(p.identifier if hasattr(p, "identifier") else p.ticket), "robot": r,
                           "panier": panier(p.comment), "magique": p.magic, "symbole": p.symbol,
                           "sens": "achat" if p.type == 0 else "vente", "lots": p.volume,
                           "ouverture_heure_serveur": p.time, "prix_entree": p.price_open,
                           "prix_actuel": p.price_current, "stop": p.sl or None, "objectif": p.tp or None,
                           "resultat": round(p.profit, 2), "swap": round(p.swap, 2)})
            t = totaux.setdefault(r, {"positions": 0, "resultat_en_cours": 0.0})
            t["positions"] += 1
            t["resultat_en_cours"] = round(t["resultat_en_cours"] + p.profit + p.swap, 2)
        return {"ecrit": pont.maintenant(), "heures": "heure du serveur du courtier, en secondes",
                "par_robot": totaux, "positions": lignes}

    def fermees(self) -> list:
        """Positions fermées pas encore exportées, une ligne chacune."""
        with pont.VERROU:
            deals = self.mt5.history_deals_get(DEBUT, datetime.now() + timedelta(days=2)) or ()
            ouvertes = {getattr(p, "identifier", p.ticket) for p in (self.mt5.positions_get() or [])}
        par_pos = {}
        for d in deals:
            if d.type in (0, 1) and d.position_id:            # achats et ventes seulement (pas les dépôts)
                par_pos.setdefault(d.position_id, []).append(d)
        lignes = []
        for pid, ds in par_pos.items():
            entrees = [d for d in ds if d.entry == 0]
            sorties = [d for d in ds if d.entry in (1, 3)]
            if pid in ouvertes or not entrees or not sorties or str(pid) in self.exportees:
                continue
            e = entrees[0]
            if not self._garder(e.magic):
                continue
            vol = sum(d.volume for d in sorties) or 1.0
            derniere = max(sorties, key=lambda d: d.time_msc)
            fin = (derniere.comment or "").lower()
            lignes.append({
                "n": self._n(pid), "robot": robot(e.magic), "panier": panier(e.comment), "magique": e.magic,
                "symbole": e.symbol, "sens": "achat" if e.type == 0 else "vente", "lots": e.volume,
                "ouverture_heure_serveur": e.time, "prix_entree": e.price, "fermeture_heure_serveur": derniere.time,
                "prix_sortie": round(sum(d.price * d.volume for d in sorties) / vol, 6),
                "stop": None, "objectif": None,
                "fin": "stop" if fin.startswith("[sl") else ("objectif" if fin.startswith("[tp") else
                       ("stop_out" if fin.startswith("[so") else "robot")),
                "commission": round(sum(d.commission + getattr(d, "fee", 0.0) for d in ds), 2),
                "swap": round(sum(d.swap for d in ds), 2),
                "resultat": round(sum(d.profit + d.swap + d.commission + getattr(d, "fee", 0.0) for d in ds), 2)})
            self.exportees.add(str(pid))
        lignes.sort(key=lambda x: x["fermeture_heure_serveur"])
        return lignes

    def exporter(self, force: bool = False) -> dict:
        if not force and time.time() - self.dernier < PERIODE:
            return {}
        self.dernier = time.time()
        dossier = self.sortie / "autres"
        dossier.mkdir(parents=True, exist_ok=True)
        ouv = self.ouvertes()
        nouvelles = self.fermees()
        fichier = dossier / "historique.csv.gz"
        if nouvelles:
            tampon = io.StringIO()
            w = csv.DictWriter(tampon, fieldnames=CHAMPS, lineterminator="\n")
            if not fichier.exists():
                w.writeheader()
            w.writerows(nouvelles)
            with open(fichier, "ab") as f:                   # nouveau bloc gzip à la suite (lisible d'un trait)
                f.write(gzip.compress(tampon.getvalue().encode(), mtime=0))
        ouv["historique"] = {"positions_fermees_exportees": len(self.exportees), "nouvelles_ce_tour": len(nouvelles)}
        pont.ecrire_json(dossier / "ouvertes.json", ouv)
        pont.ecrire_json(self.fichier_local, {"numeros": self.numeros, "exportees": sorted(self.exportees)})
        return {"ouvertes": len(ouv["positions"]), "nouvelles_fermees": len(nouvelles)}
