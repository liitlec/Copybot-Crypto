# Avis pour Baptiste — 12/11/2026, 19 h 40 (passage 22)

1. **Ton mélange, vérifié sur 15 mois de bougies du courtier** (à 0,01 lot) : `bt_or` +5 365 $, `exces_m5` +340 $, `cassure_m15` +285 $, `elan_m15` **−398 $**, `exces_m1` −136 $ (sur 3 mois). **96 % du gain vient de `bt_or` seul.**
2. **Ils ne se compensent pas** : tous gagnent les jours où l'or file dans un sens et perdent les jours calmes (mélange : +48 $ par jour de tendance, −14 $ par jour calme). Les +150 $ du direct viennent de la chute de 3 % de l'or aujourd'hui, pas d'un équilibre entre stratégies. Rien à optimiser tant que les pièces ne gagnent pas seules.
3. **Stratégie à critères multiples** (7 conditions réunies, fixées d'avance) : les critères font passer de « perd le spread » à « à peu près zéro », avec un trade tous les 3 jours. Pas de gain prouvé.
4. Rappel « 1 % par jour » : avec `bt_or`, il faudrait risquer 3,1 % du compte par position, soit 41 % de chances de perdre la moitié du compte dans l'année ; à 0,5 %, ≈ 0,16 % par jour si son avantage est réel.
5. **À savoir** : chaque nouvelle version du robot ferme tout ce qui est ouvert (la v7 de 18 h 46 a coupé le premier panier `bt_or`, −0,94 $, non compté). Pour des paniers de plusieurs jours, il faudrait côté PC que le pont rende l'étiquette de chaque position, et éviter de changer de version quand un panier est ouvert.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 12/11 19 h 08

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 281 | −0,39 $ | ± 0,20 $ | référence |
| elan_m1 | 283 | +0,03 $ | ± 0,20 $ | continue jusqu'à 300 trades (banc : −0,19 $, le spread) |
| retour_m1 | 259 | −0,55 $ | ± 0,20 $ | **éteint** en version 7 (12/11 18 h 46) |
| fcassure_m1 | 84 | +0,00 $ | ± 0,27 $ | continue (comme le témoin) |
| exces_m1 | 14 | +1,27 $ | ± 2,08 $ | continue |
| elan_m15 | 11 | +5,37 $ | ± 4,61 $ | continue |
| cassure_m15 | 5 | +8,63 $ | ± 9,04 $ | continue |
| exces_m5 | 1 | +0,40 $ | inconnue | continue |
| midi_agite (candidat) | 1 | −0,06 $ | inconnue | trade de 11 h à 14 h quand l'or est agité ; arrêt : < −0,50 $ après 60 trades ou −60 $ |
| bt_or (mécanique BlockTrend) | 0 panier valable (le 1er, −0,94 $, a été fermé par la mise à jour v7) | — | — | arrêt à −20 R cumulés ou moyenne < −0,3 R après 40 paniers |
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
