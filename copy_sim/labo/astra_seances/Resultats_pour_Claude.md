# Reconnaître le type de séance sur l’or
**Recherche pour Baptiste • 23 novembre 2026 • XAUUSD**

## Ce qu’on sait distinguer à l’avance
Sur 76 jours de décision monétaire programmée de la Fed (FOMC), seuls 2 ont été calmes entre 9 h et 21 h, contre 22,4 % des séances témoins comparables. De 13 h à 21 h, il y en a eu 0 sur 76, contre 21,4 % chez les témoins. Le signal est connu avant l’ouverture. Sur ces 76 après-midi, le prix a fait 24 tendances, 13 allers-retours et 39 trajets mixtes. Ce calendrier permet de signaler un risque de forte amplitude. Il laisse ouverte la décision d’activer le robot de tendance ou celui de retour à la moyenne.

Le classifieur du matin enrichit aussi la sélection en jours calmes. En revanche, les données ne justifient pas une bascule automatique entre les deux robots. Un signal de cassure mérite une comparaison en démo pour le régime récent.

## Données et définition des résultats
897 séances de juin 2013 à décembre 2016 pour régler les modèles, puis 2 407 séances distinctes hors apprentissage. Décision principale à 9 h, contrôle secondaire à 13 h. Les deux décisions d’un même jour restent deux observations de la même séance. H4 historique en heure de la source, fuseau non confirmé. La deuxième source est en UTC, avec des H1 regroupées en H4. Vérifier ce décalage avant tout rejeu MT5. Les séances incomplètes sont exclues, ce qui limite notamment l’interprétation des jours fériés. La seconde série fournit 108 séances évaluées après les 20 séances nécessaires à l’initialisation, du 27 avril au 25 septembre 2026. Les premiers tests de Baptiste avaient déjà examiné les prix de plusieurs de ces périodes. Il s’agit de contrôles historiques chronologiques.
- **Calme** si l’amplitude future (plus haut moins plus bas, divisé par le cours à la décision) est inférieure à 70 % de la médiane des 20 séances précédentes au même horaire.
- **Tendance** sur les autres séances si le déplacement absolu jusqu’à la clôture vaut au moins 65 % de l’amplitude future, dans un sens ou dans l’autre.
- **Aller-retour** sur les séances restantes si le cours s’écarte de son point de départ d’au moins 40 % de l’amplitude médiane habituelle et finit à moins de 30 % de cette excursion de son point de départ. Cette définition capture un trajet observable au moyen des extrêmes et de la clôture. Une séance avec plusieurs oscillations suivies d’une forte clôture peut recevoir une autre étiquette.
- **Mixte** dans les autres cas. Aucun calcul de signal ne prend en compte l’étiquette future.

## Calendrier de la Fed
Le signal s’applique au dernier jour d’une réunion ordinaire programmée, quand la décision est publiée. Les réunions d’urgence et celle annulée de mars 2020 sont exclues. Pour chaque réunion, le témoin est la moyenne des autres séances disponibles du même mois, de la même année et du même jour de semaine. Le nombre de réunions est limité et les moyennes du dernier bloc sont fragiles.

| Période | Réunions observées | Calmes après 9 h | Calmes après 13 h | Tendances après 13 h | Allers-retours après 13 h |
|---|---:|---:|---:|---:|---:|
| 2017–2021 | 39 | 1 | 0 | 11 | 5 |
| 2022–2023 | 16 | 0 | 0 | 5 | 5 |
| 2024–6 fév. 2026 | 17 | 1 | 0 | 8 | 2 |
| 27 avr.–25 sept. 2026 | 4 | 0 | 0 | 0 | 1 |

Le ratio médian de l’amplitude entre 13 h et 21 h et de l’amplitude moyenne des témoins correspondants atteint 1,62. Zéro séance calme dans l’échantillon laisse ouverte la possibilité d’en observer à l’avenir. À taille unitaire et pour un coût fixe de 4 points de base par aller-retour, les règles simplifiées de tendance et de retour font respectivement −3,22 et −11,90 points de base en moyenne par après-midi de réunion. Le spread réel pourrait s’écarter fortement du forfait au moment des annonces. Ces simulacres ne reproduisent pas les paniers ni les renforts de bt_or.

## Score du matin
Régression logistique à quatre classes, figée fin 2016. Elle combine l’amplitude matinale relative aux 20 séances passées, le niveau récent de volatilité sur trois jours, la taille du déplacement net, la position de clôture dans la plage du matin, le recouvrement des deux dernières bougies, le dépassement de la plage de la veille et le jour de semaine. Pour chaque classe, l’alerte est déclenchée au 80e centile des scores sur l’échantillon d’apprentissage. Pour « calme » à 9 h, ce seuil vaut 0,261655. Réserve temporelle et fichier de paramètres identiques pour tous les blocs.

| Bloc | Séances | Calmes parmi les alertes | Fréquence de base | Témoin ajusté au mois et au jour de semaine |
|---|---:|---:|---:|---:|
| 2017–2021 | 1 248 | 71/229 (31,0 %) | 18,4 % | 26,5 % |
| 2022–2023 | 515 | 28/89 (31,5 %) | 19,8 % | 28,8 % |
| 2024–6 fév. 2026 | 536 | 29/94 (30,9 %) | 19,4 % | 29,2 % |
| 27 avr.–25 sept. 2026 | 108 | 7/19 (36,8 %) | 18,5 % | 35,3 % |

Le témoin ajusté utilise la fréquence observée dans chaque groupe mois × jour de semaine, pondérée selon les dates d’alerte. C’est un diagnostic rétrospectif de l’effet du calendrier. Un lundi est calme dans environ 28 à 31 % des cas selon le bloc. Ensemble, le score attrape 135 journées calmes sur 456 et produit 296 fausses alertes sur 431. Parmi les alertes, 93 séances basculent en tendance. L’alerte « tendance » classe juste 107/406 fois (26,4 %, contre 24,7 % habituellement), et l’alerte « retour » 86/500 fois (17,2 %, contre 15,9 %). Ces dernières fréquences motivent la décision de conserver « indéterminé » en démo.

## Cassure à 9 h et comparaison économique
Prendre le plus haut et le plus bas de la bougie 1 h–5 h. Si la bougie 5 h–9 h dépasse **un seul** côté de cette plage et clôture au-delà, entrer dans ce sens à la première cotation de la bougie de 9 h. Sortie vers 21 h. Un seul aller-retour, 0,04 % de coût forfaitaire, 0 % de retenue sur gains, exposition unitaire sans pyramide. Les coûts, les cotations bid/ask, les renforts et le risque du robot STARTRADER restent à rejouer. Il s’agit d’une vérification exploratoire complémentaire. L’intervalle par semaines mesure la variabilité historique et ne corrige pas la sélection parmi toutes les pistes du projet.

| Bloc | Occasions | Bon sens | Gain net moyen par occasion | Achat systématique aux mêmes instants | IC 95 % du gain net |
|---|---:|---:|---:|---:|---:|
| 2017–2021 | 590 | 51,2 % | −0,008 % | −0,053 % | [−0,061 %, +0,044 %] |
| 2022–2023 | 242 | 48,3 % | −0,008 % | −0,085 % | [−0,117 %, +0,095 %] |
| 2024–6 fév. 2026 | 251 | 54,6 % | +0,078 % | +0,043 % | [−0,033 %, +0,189 %] |
| 27 avr.–25 sept. 2026 | 48 | 60,4 % | +0,167 % | −0,018 % | [−0,015 %, +0,376 %] |

Sur les deux blocs récents, l’intervalle à 95 % du surplus sur l’achat simple contient aussi zéro. Après une cassure rejetée à 9 h, entrer en sens inverse rapporte −0,553 % en moyenne sur les 34 cas du dernier bloc. À 13 h, suivre la cassure acceptée donne −0,168 % sur les 48 derniers cas. La conclusion dépend donc de l’horaire et de la définition exacte.

## Vérification utile pour Claude
1. Aligner les bougies avec les horodatages UTC de STARTRADER, en contrôlant heures d’été et d’hiver. Pour le FOMC, marquer uniquement la date de décision annoncée au calendrier avant la séance.
2. Sur les deux robots en simulation continue à risque égal, écrire à 9 h le drapeau FOMC, le score calme, le signal de cassure et l’état « indéterminé » si applicable. Garder les mêmes règles et horaires sur tout le bloc réservé.
3. Comparer les paniers engagés après la décision sur la même séance et aux mêmes budgets : bt_or seul, retour seul, 50/50, et suspension d’une seule famille à la fois. Conserver le P&L flottant, le spread, le glissement et tout panier engagé avant la décision dans un suivi séparé. Inclure les jours sans intervention.
4. Avant toute adoption, comparer les euros nets à une coupure aléatoire de même fréquence, avec calendrier et risque comparables. Rapporter le nombre de signaux, la pire baisse, les semaines perdantes, l’espérance et son incertitude. Un gain moyen par signal ne fournit pas un minimum hebdomadaire.

## Reproduction et sources
Les fichiers ancien.csv, h4.csv et h1.csv sont les données d’entrée. Avec Python, pandas, numpy et scikit-learn, exécuter dans l’ordre detecter.py, cassure.py, verifier.py, calendrier.py puis figer.py. Le journal complet offre les décisions des deux horaires. Pour évaluer une journée à 9 h hors ligne, exécuter par exemple python score_matin.py h4.csv 2025-03-19. Le calcul coupe automatiquement les bougies postérieures à la décision. Le drapeau Fed se lit dans fed.csv.
- Données H4 : https://raw.githubusercontent.com/tohaitrieu/market-history/master/data/commodities/GOLD/GOLD-H4.csv
- Contrôle H1 : https://raw.githubusercontent.com/getdata-finance/xauusd-1h-ohlcv-metals-historical-data/main/XAUUSD_1h.csv
- Calendrier FOMC : https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
- Archives Fed 2017 à 2020 : https://www.federalreserve.gov/monetarypolicy/fomchistorical2017.htm (remplacer l’année dans le lien pour les autres années).
