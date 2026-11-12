# Avis pour Baptiste — 12/11/2026, 11 h 20 (passage 16)

1. **Combiner les idées : d'accord, dès qu'il y a de la matière.** Pour l'instant une seule pièce a un petit avantage au banc, le « retour de midi ». J'ai fixé d'avance son mélange : midi × or agité × sens de la tendance de fond. Il sera jugé seulement sur les trades à venir.
2. Les règles M1 n'ont pas de matière à combiner : sur 18 000 trades passés chacune, `elan_m1` et `retour_m1` perdent exactement le spread (−0,19 $ et −0,14 $). Leurs écarts en direct (+0,13 $ et −0,55 $) sont du bruit ; elles seront coupées à 300 trades si rien ne change.
3. Mon robot : 629 trades fermés, total ≈ −94 $ à 0,01 lot, 0 refus. Rien de prouvé (48 270 combinaisons testées).
4. Tes autres robots : rien à reprendre (détail au passage 15) ; la vente en tendance, testée sur 20 ans, perd 3,9 % par an.
5. Le candidat de midi est dans sa fenêtre (11 h – 14 h), pas encore de trade. Rien à te demander.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 12/11 11 h 08

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 185 | −0,25 $ | ± 0,20 $ | référence |
| elan_m1 | 186 | +0,13 $ | ± 0,19 $ | continue jusqu'à 300 trades (banc : −0,19 $, le spread) |
| retour_m1 | 186 | −0,55 $ | ± 0,20 $ | continue jusqu'à 300 trades (comme le témoin) |
| fcassure_m1 | 51 | −0,02 $ | ± 0,30 $ | continue (comme le témoin) |
| exces_m1 | 8 | +3,23 $ | ± 1,73 $ | continue |
| elan_m15 | 7 | −1,00 $ | ± 4,48 $ | continue |
| cassure_m15 | 3 | +4,03 $ | ± 10,8 $ | continue |
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
