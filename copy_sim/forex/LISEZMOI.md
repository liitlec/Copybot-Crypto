# Pont MT5 (démo) : mise en route sur le PC

État au 11/11/2026 : installé sur le PC de Baptiste.
- Essais sur faux MT5 (`python essais_pont.py --faux`) : 8 sur 8.
- Essais réels sur le compte démo (`python essais_pont.py`) : 7 sur 7 (0,01 lot EURUSD ouvert puis fermé par
  consigne, deux refus de plafond, `STOP_PONT`, compte non démo simulé, version ancienne / consigne illisible
  ignorées, rien d'identifiant écrit). Il n'y avait aucune position d'autres robots pendant l'essai 6.

Le pont **tourne depuis une copie figée hors du dépôt** (`%USERPROFILE%\pont_mt5\pont_mt5.py`, lancé avec
`--depot <chemin du dépôt>`) : le `git pull` qu'il fait chaque minute ne peut donc pas modifier son propre code.
Une nouvelle version du pont n'est installée que si Baptiste relance `.\installer_tache.ps1` sur son PC.

Installation (MT5 ouvert sur le compte démo, bouton « Algo Trading » activé, dépôt sur la branche du labo) :
1. `pip install MetaTrader5`
2. `python essais_pont.py` : tout doit être « REUSSI ».
3. `.\installer_tache.ps1` : copie le pont dans `%USERPROFILE%\pont_mt5` et le lance à chaque ouverture de session
   Windows (tâche « PontMT5 »).

**Robot du labo (lanceur, depuis le 11/11/2026)** : le pont installe aussi `copy_sim/labo/mt5/robot/` quand son
`VERSION` augmente, après contrôle du texte et essais sur le faux terminal, et le fait tourner dans un bac à sable
(`bac_a_sable.py`) ; ses ordres passent par `acces_robot.py` (fonctions du pont). Interface : `ROBOT_INTERFACE.md`.
Essais : `python essais_lanceur.py` (faux terminal, 8 sur 8) et `python essais_lanceur.py --reel` (démo, 1 sur 1 :
0,01 lot XAUUSD avec stop, fermé après une minute).

**Tableau de bord en direct (depuis le 11/11/2026)** : `tableau_bord.py` (+ `.html`, `.js`), lancé dans le pont,
sert http://127.0.0.1:8765/ (raccourci « Robot du labo en direct » sur le bureau) : prix de l'or, graphique M1 avec
les trades du robot, positions, résultats du jour et par hypothèse (historique MT5, stops compris), 20 derniers
trades. Lecture seule : GET seulement, 127.0.0.1 seulement, aucun identifiant affiché. Essai seul :
`python tableau_bord.py`.
Depuis le téléphone (hors de chez soi, rien à installer) : chaque minute, le pont envoie l'instantané (sans
identifiant) et la page sur la branche `mt5-direct` (un seul commit, remplacé à chaque fois) ; ouvrir
https://htmlpreview.github.io/?https://github.com/liitlec/Copybot-Crypto/blob/mt5-direct/index.html (copie de 1 à 2 min).

Arrêter : créer un fichier vide `%USERPROFILE%\pont_mt5\STOP_PONT` (plus aucun ordre, robot arrêté, l'état continue
d'être publié), ou `Stop-ScheduledTask -TaskName PontMT5` pour tout couper. Journal : `%USERPROFILE%\pont_mt5\pont.log`.
