# Avis pour Baptiste — 12/11/2026, 22 h 45 (passage 23, session neuve)

1. **Ton BlockRange refait sur 26 ans** (acheter un indice après un repli court, en tendance haussière) : c'est la **première règle du labo qui gagne au réglage ET au verdict** : +20 points de base par trade après coûts (454 trades depuis 2016, t = 2,3 ; 66 % de gagnants), et les réglages voisins gagnent aussi.
2. **Mais c'est petit** : ≈ 45 trades par an. Avec 20 % du compte par trade : **+1,6 % par an**, pire baisse −6,5 % ; poussé à levier 5 : ≈ +8 % par an pour ≈ −30 % de pire baisse. Ses −2 307 $ sur la démo tiennent à 4 trades trop gros, pas à la règle. À éviter : le FTSE (perdant).
3. **Robot version 8** publiée : `elan_m1` éteint (319 trades, −0,03 $ par trade, pareil que le hasard : règle d'arrêt fixée d'avance). Aucun panier `bt_or` n'était ouvert. Il y aura ≈ 40 % de trades en moins.
4. `bt_or` (mécanique BlockTrend sur l'or) reste le seul candidat sérieux en direct : 0 panier valable pour l'instant, prochaine entrée possible cette nuit. Les scalps M1 restent au niveau du hasard.
5. Ensuite : comparer les bougies jour du courtier à Yahoo pour mettre le repli d'indices en essai sur la démo ; tester la mécanique BlockTrend sur argent, BTC, ETH (données demandées au pont). Rien à faire de ton côté.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 12/11 23 h 08 (Paris 22 h 08)

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 317 | −0,31 $ | ± 0,18 $ | référence |
| elan_m1 | 319 | −0,03 $ | ± 0,18 $ | **éteint** en version 8 (dans la marge du témoin à 300 trades) |
| retour_m1 | 279 | −0,55 $ | ± 0,20 $ | éteint depuis la version 7 |
| fcassure_m1 | 95 | +0,10 $ | ± 0,25 $ | continue jusqu'à 300 trades (comme le témoin pour l'instant) |
| exces_m1 | 15 | +1,38 $ | ± 1,94 $ | continue |
| elan_m15 | 12 | +4,95 $ | ± 4,23 $ | continue (banc 15 mois : −0,16 $) |
| cassure_m15 | 5 | +8,63 $ | ± 9,04 $ | continue |
| exces_m5 | 4 | +4,16 $ | ± 4,79 $ | continue |
| midi_agite (candidat) | 1 | −0,06 $ | inconnue | 11 h – 14 h quand l'or est agité ; arrêt : < −0,50 $ après 60 trades ou −60 $ |
| bt_or (mécanique BlockTrend) | 0 panier valable (le 1er, −0,94 $, coupé par la mise à jour v7) | — | — | arrêt à −20 R cumulés ou moyenne < −0,3 R après 40 paniers |

## Candidat prouvé au banc, pas encore en direct : repli d'indices (mécanique BlockRange)

| Réglage | 2000-2015 | 2016-2026 | À 20 % du compte par trade |
|---|---|---|---|
| RSI 2 j < 10, au-dessus de la moyenne 200 j, sortie au-dessus de la moyenne 5 j | +20,3 bp par trade (519 trades) | +20,0 bp (454 trades, t = 2,3) | +1,6 % par an, pire baisse −6,5 % |

## Meilleur montage prouvé du moment (inchangé) : panier acheté seulement, risque égal (indices, or, argent, BTC, ETH)

| Version | 2016-2026 par an | Pire baisse | Remarque |
|---|---|---|---|
| P1 CFD levier ×3 | +13,4 % | −39 % | pas mieux que le S&P 500 seul (+13,9 %, −34 %) |
| P2 CFD ×3 + filtre 200 j | +8,9 % | −28 % | filtre non prouvé depuis 2016 |
| P3 comptant sans levier | +7,6 % | −12 % | le plus régulier |

Aucun scalp n'a encore le droit d'entrer dans ce tableau : ceux du robot sont des essais.

## Registre papier (départ 10 000 le 11/11/2026, premier jour compté : 12/11)

| Montage | Dernier jour | Capital |
|---|---|---|
| P1 panier CFD ×3 | 11/11 | 10 000 |
| P2 panier CFD ×3 + filtre 200 j | 11/11 | 10 000 |
| P3 panier comptant | 11/11 | 10 000 |
| T0 tendance (témoin réfuté) | 11/11 | 10 000 |
