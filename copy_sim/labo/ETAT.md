# État du laboratoire (réécrit à chaque passage) — après le passage 7, 12/11/2026 (2 h 40)

## Où j'en suis
- Outils : `donnees.py` (téléchargement Yahoo), `banc_tendance.py` (A), `banc_scalp_h1.py` (B), `banc_prime.py` (C),
  `registre.py` (papier). Tout tourne en moins d'une minute.
- Réfuté : tendance long/court en CFD (devises surtout) ; scalp simple à l'heure (élan / retour).
- Meilleur montage honnête du moment : panier acheté seulement (indices, or, argent, BTC, ETH) à risque égal ;
  ≈ +8 à +13 %/an depuis 2016 selon le levier, mais c'est la prime de risque en période de hausse, pas un avantage.
- Réfuté aussi (passage 2) : 30 règles simples de bougies sur XAUUSD en M1, M5, M15 avec le spread réel.
- Mesuré : l'or est le moins cher (spread 0,46 bp = 28 % du mouvement M1, 11 % en M5 ; EURUSD 323 %).
- Réfuté (passage 5) : grille de 47 628 combinaisons (or, argent, Nasdaq, S&P, DAX) : aucune à t > 2 au verdict.
- 48 087 essais comptés. Banc F : `banc_plateau.py`. Banc D : `banc_or.py` (données dans `mt5/donnees/`, poussées par le pont).

## À chaque passage, d'abord
`python3 donnees.py && python3 registre.py` puis recopier le tableau du registre dans AVIS.md.

## À chaque passage, ensuite (priorité de Baptiste du 11/11 18 h 15)
Lire `mt5/etat.json` (champ `robot` : version installée, en marche, dernier refus), `mt5/robot_journal.jsonl`,
`mt5/executions.jsonl`. Tenir dans AVIS.md le tableau **par hypothèse** : trades, gain moyen après spread, erreur
type. Couper ce qui perd nettement, garder ce qui tient, ne monter la taille que si direct ET banc concordent.
Le robot note `evenement` = ouverture / sortie (avec `hypothese`, `profit` en $ juste avant la fermeture, `raison`).
Pour changer le robot : modifier `mt5/robot/`, relancer les essais (voir JOURNAL passage 3), monter `VERSION` en dernier.

## Pistes suivantes (par ordre)
1. **Résultats du robot** : `python3 analyse_robot.py` ; attendre ≈ 300 trades par hypothèse continue (≈ 30 h de
   marché) avant de couper ; couper alors ce qui est sous le témoin `hasard_m1` de plus de 2 erreurs types.
   Ajouter à `analyse_robot.py` le découpage par heure (`h_serveur` dans les notes ; serveur = Paris + 1 h).
   `ecart_midi_m5` ne trade que de 11 h à 14 h Paris : premiers trades le 12/11.
2. **Candidat `ecart_midi_m5`** (premiers trades le 12/11 de 11 h à 14 h Paris). Règle d'arrêt (JOURNAL passage 7) :
   arrêt si moyenne < −0,50 $ après 60 trades ou perte cumulée de 60 $ ; taille > 0,01 lot seulement après 100 trades
   à moyenne positive (t > 1,5). Régime : gagne quand l'or est agité (mouvement M5 moyen sur 24 h > ≈ 6 bp), rien
   sous ≈ 4,8 bp. **À faire** : coder ce filtre de volatilité dans le robot (v5) après l'avoir vérifié en avance
   glissante dans `banc_plateau.py` ; essayer la même idée sur `NAS100+` M5.
3. **Étendre la grille** (`banc_grille.py`) : stops/objectifs dans la bougie, tendance de fond (M15/H1), deux règles
   qui se confirment, jour de semaine ; `NAS100+` en priorité (spread = 21 % du mouvement M1, moins cher que l'or).
   Demander plus d'historique par tranches (`debut`/`fin`) si le terminal en a.
4. Portage (Hyperliquid), effets de calendrier sur indices : après.

## MT5 démo (section ajoutée à MISSION.md le 11/11, commit 36b30f3)
- Cible : compte démo via le pont (`labo/mt5/consigne.json` → pont ; `etat.json`, `executions.jsonl`, `donnees/` ← pont).
- Le pont tourne depuis le 11/11 17 h 10 ; lanceur de robot présent (champ `robot` de `etat.json`), aucun robot installé.
- Demandes d'historique : 90 000 bougies passent, 200 000 non. Serveur = UTC+2. Bougies en prix vendeur.
- `consigne.json` : rien envoyé. Robot v1 en marche le 11/11 à 18 h 16 ; **v2 poussée ≈ 19 h** (8 hypothèses, ≈ 850 trades/jour, coût attendu ≈ 160 $/jour de démo) : vérifier `etat.json` → `robot.version_installee` = 2 (4 hypothèses XAUUSD, 0,01 lot, non prouvées).
- Indices : `NAS100+`, `SP500+`, `DJ30+`, `GER40+` (et variantes `ft+`).

## Robot
- v4 poussée le 12/11 ≈ 2 h 40 (comme v3 + pas d'ouverture de 23 h 50 à 1 h 10 serveur) : vérifier `version_installee` = 4.
- Le terminal n'a pas de M5 avant juin 2025 pour l'or (demande 2024 : « aucune bougie »).
- La session redémarre souvent en plein passage : committer tôt ; plusieurs déclenchements peuvent arriver d'un coup
  (les traiter en un seul passage).

## Page de suivi (PRIORITES, entrée de 23 h)
Dernière étape de chaque passage, après le push : `git pull --rebase`, `python3 copy_sim/labo/page_suivi.py`, puis
outil Artifact : « read » de https://claude.ai/artifact/S18Y8qgC8cRRBoVMM8p7kj puis publish avec cette `url` et
`file_path` = `copy_sim/reports/labo_suivi.html`. Relire le fichier avant de publier (ni identifiant ni chemin du PC).

## Pièges notés
- Yahoo : `range=max` → mensuel ; utiliser `period1/period2`. `query1` peut répondre « Too Many Requests », `query2` passe.
- Indices en 1 h : 7 barres par jour seulement, « 24 barres » ≈ 3,5 jours.
- Les Sharpe du banc C ne retranchent pas le taux sans risque.
