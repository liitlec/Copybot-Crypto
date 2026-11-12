# Avis pour Baptiste — 12/11/2026, 4 h 25 (passage 9)

1. **Toujours aucun scalp prouvé** (48 172 combinaisons). En direct, 348 trades fermés, total ≈ −86 $ à 0,01 lot : les règles M1 perdent le spread, comme le pile ou face.
2. Piège évité cette nuit : un backtest montrait un gain net chaque nuit à la réouverture de l'or (minuit – 1 h). C'est une illusion due au spread, très large à cet instant ; le robot l'a d'ailleurs payé en vrai (7 stops). Il n'y trade plus.
3. Le seul candidat reste le « retour de midi » quand l'or est agité (+4 points de base par trade sur 15 mois, non prouvé). Aujourd'hui l'or est calme : premiers trades de 11 h à 14 h, étiquetés « calme », sans attente particulière.
4. Sa règle d'arrêt est écrite : arrêt si moyenne sous −0,50 $ après 60 trades ou à 60 $ de perte ; taille augmentée seulement après 100 trades gagnants.
5. La page de suivi n'est pas à jour : sa publication attend ton approbation dans la session (je réessaie en journée). Rien d'autre à te demander.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 12/11 4 h 10

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 101 | −0,36 $ | ± 0,25 $ | référence |
| elan_m1 | 102 | +0,04 $ | ± 0,24 $ | continue jusqu'à 300 trades (comme le témoin) |
| retour_m1 | 102 | −0,48 $ | ± 0,24 $ | continue jusqu'à 300 trades (comme le témoin) |
| fcassure_m1 | 30 | +0,21 $ | ± 0,40 $ | continue (comme le témoin) |
| exces_m1 | 5 | +2,20 $ | ± 2,44 $ | continue |
| elan_m15 | 5 | −2,49 $ | ± 4,47 $ | continue |
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
