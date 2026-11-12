# Avis pour Baptiste — 12/11/2026, 3 h 30 (passage 8)

1. **Toujours aucun scalp prouvé** (48 091 combinaisons). En direct, 308 trades fermés, total ≈ −52 $ à 0,01 lot : les règles M1 font comme le pile ou face, elles perdent le spread.
2. **Le candidat « retour de midi » se précise** : quand l'or est agité, il a gagné +4 points de base par trade (≈ +1,5 $ à 0,01 lot) dans 5 périodes de 3 mois sur 5 ; quand l'or est calme, presque rien. Aujourd'hui l'or est **calme** : n'attends pas grand-chose de lui ce midi.
3. Robot version 5 : il note chaque trade de midi « agité » ou « calme » pour vérifier cela en vrai. Règle d'arrêt écrite : arrêt si la moyenne est sous −0,50 $ après 60 trades ou à 60 $ de perte ; taille augmentée seulement après 100 trades gagnants.
4. Attention : la valeur du compte démo inclut tes autres robots (≈ +226 $ de positions qui ne sont pas les miennes). Pour juger le mien, regarde le tableau ci-dessous.
5. La page de suivi n'a pas pu être mise à jour cette nuit : la publication attend ton approbation dans la session. Rien d'autre à te demander.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 12/11 3 h 08

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 88 | −0,22 $ | ± 0,26 $ | référence |
| elan_m1 | 89 | −0,07 $ | ± 0,24 $ | continue jusqu'à 300 trades (comme le témoin) |
| retour_m1 | 89 | −0,40 $ | ± 0,25 $ | continue jusqu'à 300 trades (comme le témoin) |
| fcassure_m1 | 28 | +0,36 $ | ± 0,41 $ | continue (trop peu pour conclure) |
| exces_m1 | 5 | +2,20 $ | ± 2,44 $ | continue |
| elan_m15 | 4 | −0,58 $ | ± 5,21 $ | continue |
| cassure_m15 | 2 | −4,58 $ | ± 11,4 $ | continue |
| exces_m5 | 1 | +0,40 $ | inconnue | continue |
| midi_agite (candidat) | 0 | — | — | trade de 11 h à 14 h quand l'or est agité ; arrêt : < −0,50 $ après 60 trades ou −60 $ |
| midi_calme (comparaison) | 0 | — | — | même règle quand l'or est calme ; coupé si négatif après 40 trades |

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
