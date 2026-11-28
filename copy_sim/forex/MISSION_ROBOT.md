# Lanceur du robot du laboratoire : suite de la mission du pont (11/11/2026), pour la session du PC de Baptiste

Baptiste veut que l'IA autonome du cloud trade **en continu sur la démo MT5** avec un programme qu'elle écrit
elle-même (`copy_sim/labo/mt5/robot/`, règles dans `copy_sim/labo/PRIORITES.md`). À toi d'ajouter au pont le
**lanceur** qui fait tourner ce programme sans laisser passer n'importe quoi. Réponds à Baptiste en français.

## Ce que fait le lanceur (dans le pont ou à côté, lancé au démarrage de Windows comme lui)
1. À chaque `git pull`, si `copy_sim/labo/mt5/robot/VERSION` est plus grand que la version installée : copie le
   dossier `robot/` hors du dépôt (copie figée, comme le pont), lance `essais_robot.py` sur le faux terminal
   (`copy_sim/forex/faux_mt5.py`, sans MT5 réel, délai maximal 2 minutes). « ESSAIS OK » → arrête l'ancien robot,
   démarre le nouveau ; sinon garde l'ancien et note le refus.
2. Fait tourner `robot.py` comme un processus à part ; s'il plante 3 fois en 10 minutes, revient à la version
   d'avant (ou reste arrêté s'il n'y en a pas) et le note.
3. Écrit dans `etat.json` un champ `robot` (version installée, en marche ou non, dernier refus, dernière erreur) et
   pousse `copy_sim/labo/mt5/robot_journal.jsonl` (ce que le robot note : décisions, ordres, prix obtenus).

## Sécurités (à tester une par une sur le faux terminal, puis en vrai à 0,01 lot)
- Le robot ne reçoit **pas** le module `MetaTrader5` pour ses ordres : il reçoit un objet du pont qui lui donne les
  prix et les bougies en lecture, et dont les seules fonctions d'ordre sont celles du pont (démo vérifiée à chaque
  ordre, 10 positions, 0,50 lot, numéro magique, positions du pont seulement). Refuse d'installer un `robot.py` qui
  importe `MetaTrader5`, `subprocess`, `socket`, `urllib`, `requests`, `os.system`, `ctypes`, ou qui ouvre un fichier
  hors de son dossier et de `copy_sim/labo/mt5/` (contrôle simple du texte source avant les essais, et répertoire de
  travail limité).
- Chaque ouverture doit porter un stop ; sans stop, l'ordre est refusé.
- Garde-fou de compte : si la valeur du compte démo baisse de plus de 5 % dans la journée (heure de Paris) par les
  positions du pont, plus d'ouverture jusqu'au lendemain (les fermetures restent permises).
- `STOP_PONT` arrête aussi le robot. Les robots de Baptiste déjà en démo ne sont pas touchés.
- Toujours rien d'identifiant dans le dépôt (public).

## Essais à montrer à Baptiste
Un robot d'essai minimal (ouvre 0,01 lot XAUUSD avec stop, ferme après une minute) installé par VERSION, un robot
refusé pour import interdit, un robot refusé pour essais ratés, un retour arrière après plantages, le garde-fou des
5 %, et `STOP_PONT`. Puis 3 lignes : ce qui tourne, comment l'arrêter.
