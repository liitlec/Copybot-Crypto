# Interface du robot du labo (lanceur installé sur le PC le 11/11/2026)

Le lanceur (`lanceur_robot.py`, dans le pont) installe `copy_sim/labo/mt5/robot/` quand `VERSION` augmente.
Exemple complet qui marche : `copy_sim/forex/robot_exemple/` (essayé en vrai sur la démo le 11/11).

## Fichiers (`copy_sim/labo/mt5/robot/`, à plat, sans sous-dossier)
- `robot.py` : définit `lancer(pont)`, qui **ne revient jamais** tant que `pont.arret_demande()` est faux (un retour
  ou une exception compte comme un plantage ; 3 en 10 minutes = retour à la version d'avant, version refusée).
- `essais_robot.py` : essais hors ligne sur le faux terminal, exécutés dans le même bac à sable (2 minutes au plus) ;
  dernière ligne affichée : `ESSAIS OK`. Pour un `pont` d'essai :
  `import faux_mt5, acces_robot; pont = acces_robot.AccesRobot.pour_essais(faux_mt5)`.
- `VERSION` : un entier, changé en dernier. Une version refusée ne sera pas réessayée : monter le numéro.
- Autres modules `.py`, `.json`, `.csv`, `.txt`, `.md` permis (40 fichiers, 2 Mo au plus).

## Ce que `pont` offre (les seules façons d'agir)
| Appel | Rend |
|---|---|
| `compte()` | `ordres_autorises`, `solde`, `valeur`, `marge_libre`, `devise`, `levier` |
| `symbole(s)` | `point`, `chiffres`, `lot_min`, `pas_lot`, `taille_contrat`, `niveau_stops_points` |
| `prix(s)` | `bid`, `ask`, `heure_serveur`, `heure_serveur_ms` |
| `bougies(s, periode="M1", nombre=100)` | listes `[heure_serveur, ouverture, haut, bas, cloture, volume_ticks, spread_points]`, 5000 au plus |
| `positions()` | positions **du robot** : `ticket`, `symbole`, `sens`, `lots`, `prix_entree`, `prix_actuel`, `stop`, `objectif`, `profit` |
| `ouvrir(s, sens, lots, stop, objectif=None, id="robot")` | résultat (`ok`, `ticket`, `prix_demande`, `prix_obtenu`, `spread_points`, ou `refus`) |
| `fermer(ticket)` / `modifier(ticket, stop, objectif=None)` | résultat |
| `garde_fou()` | `perte_du_jour`, `seuil`, `ouvertures_bloquees` |
| `noter(**champs)` | écrit une ligne dans `mt5/robot_journal.jsonl` (2000 par heure au plus) |
| `arret_demande()` | vrai si `STOP_PONT` existe : sortir de `lancer` |

Les ordres et leurs résultats sont notés automatiquement dans `robot_journal.jsonl` ; l'état du lanceur est dans
`etat.json`, champ `robot` (version installée, en marche, dernier refus, dernière erreur), et les positions du robot
dans `positions_robot`.

## Règles appliquées par le pont (refus sinon)
- Compte démo vérifié à chaque ordre ; `STOP_PONT` = aucun ordre et robot arrêté.
- Stop obligatoire à l'ouverture, du bon côté du prix ; impossible de le retirer.
- 0,50 lot par position ; 30 positions au plus, pont et robot ensemble ; 30 ordres par minute au plus.
- Garde-fou : perte du jour (heure de Paris) des positions du pont et du robot au-delà de 5 % de la valeur du compte
  au début du jour = plus d'ouverture jusqu'au lendemain (fermetures permises).
- Le robot ne touche qu'à ses positions (numéro magique 20261112) ; celles de la consigne et les robots de Baptiste
  ne lui sont pas accessibles.

## Bac à sable (processus à part, environnement vide)
Refusé avant les essais (contrôle du texte) : `MetaTrader5`, `subprocess`, `socket`, `urllib`, `requests`,
`os.system`, `ctypes`, `__import__`, `importlib`, `exec`/`eval`/`compile`, chemins absolus ou `../`, `os.environ`.
Bloqué en marche : ces imports et `multiprocessing`, `asyncio`, `http`, `ssl`… ; lancer un programme ; le réseau ;
lire hors de son dossier, de `copy_sim/labo/mt5/` et de Python ; écrire hors de son dossier.
Paquets permis : bibliothèque standard (sauf ce qui précède) et `numpy`.
