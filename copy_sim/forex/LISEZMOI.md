# Pont MT5 (démo) : mise en route sur le PC

État au 11/11/2026 : le code est écrit et sa logique est vérifiée sur un faux MT5 (`python essais_pont.py --faux`,
8 essais sur 8). **Les essais réels sur la démo et l'installation sur le PC restent à faire** : la session qui a
écrit le pont tournait dans le cloud, sans accès au PC.

Sur le PC, MT5 ouvert sur le compte démo, bouton « Algo Trading » activé, dépôt sur la branche du labo :
1. `pip install MetaTrader5`
2. `python essais_pont.py` : les essais réels (0,01 lot ouvert puis fermé, refus de plafond, `STOP_PONT`, compte
   non démo simulé, positions des autres robots intactes). Tout doit être « REUSSI ».
3. `python pont_mt5.py --une-fois` puis vérifier que `copy_sim/labo/mt5/etat.json` arrive sur la branche.
4. `.\installer_tache.ps1` : lancement à chaque ouverture de session Windows (tâche « PontMT5 »).

Arrêter : créer un fichier vide `STOP_PONT` dans ce dossier (plus aucun ordre, l'état continue d'être publié), ou
`Stop-ScheduledTask -TaskName PontMT5` pour tout couper. Journal local : `pont.log`.
