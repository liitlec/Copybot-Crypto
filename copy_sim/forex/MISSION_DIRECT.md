# Tableau de bord en direct sur le PC (demandé par Baptiste le 11/11/2026), pour la session du PC

Baptiste veut voir **en direct** ce que fait le robot du laboratoire : prix de l'or, positions et résultats qui
bougent à la seconde. La page claude.ai (https://claude.ai/artifact/S18Y8qgC8cRRBoVMM8p7kj) ne peut se mettre à jour
qu'une fois par heure ; le direct ne peut venir que du PC, où tourne MT5. Réponds-lui en français, court et clair.

## Ce qu'il faut construire
Un petit serveur web **en lecture seule**, lancé avec le pont (même démarrage Windows), qui écoute seulement sur
`127.0.0.1` (port 8765, ou un autre libre) et sert une page qui se rafraîchit toute seule chaque seconde :
1. **Prix XAUUSD en direct** : bid, ask, spread en points, variation du jour, et un petit graphique des 60 dernières
   minutes (bougies M1 lues dans MT5), avec les entrées et sorties du robot marquées dessus.
2. **Positions ouvertes du robot** (numéro magique du pont seulement) : hypothèse, sens, lots, entrée, prix actuel,
   stop, résultat en cours, temps restant avant sortie si le robot l'indique.
3. **Aujourd'hui** (heure de Paris) : trades fermés, total, % de gagnants, résultat en cours, garde-fou (perte du jour
   et seuil), état du robot (version, en marche, dernière erreur).
4. **Par hypothèse** : trades, total, moyenne, % de gagnants, pour aujourd'hui et depuis le début (lu dans
   `robot_journal.jsonl` local, en comptant aussi les sorties au stop et les fermetures au changement de version).
5. Les 20 derniers trades fermés, les plus récents en haut.

## Règles
- **Aucun bouton d'ordre** ni aucune action : la page ne fait que lire. Pas d'accès depuis un autre appareil
  (seulement `127.0.0.1`), pas de mot de passe, pas de numéro de compte affiché.
- Elle ne doit pas ralentir le pont ni le robot : lectures MT5 légères (un tick et quelques bougies par seconde).
- Rien de nouveau ne part dans le dépôt public, à part le code du serveur (sans identifiant).
- Teste-la, puis dis à Baptiste en 3 lignes l'adresse à ouvrir dans son navigateur et comment l'arrêter. Mets un
  raccourci sur son bureau si c'est simple.
