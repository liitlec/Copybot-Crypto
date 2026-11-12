# Avis pour Baptiste — 12/11/2026, 13 h 50 (passage 19)

1. **BlockTrend : j'ai refait sa mécanique, et sur l'or elle tient** (15 mois de bougies du courtier, spread compris) : +166 R sur 269 paniers, positive dans les 5 périodes de 3 mois, à l'achat comme à la vente. C'est le résultat le plus solide trouvé jusqu'ici, après le « retour de midi ».
2. **Mais c'est une loterie, pas du scalp** : 22 % de paniers gagnants seulement, 75 % du gain vient de 5 paniers sur 269, le gain baisse de trimestre en trimestre, et la même mécanique fait zéro sur le Nasdaq. Elle vit des grands mouvements de l'or : stratégie de régime.
3. **Pourquoi il a perdu 25 189 $** : la taille (≈ 2,4 % du compte risqué à chaque signal, avec 3 paniers à la fois ; dix signaux perdants de suite en octobre), et des marchés sans preuve (cacao : 11 pertes sur 11, BTC, ETH).
4. **BlockFIFO : rien à sauver.** Ses 1 507 entrées rejouées à taille fixe, sans ajout, perdent 0,50 $ par trade en 3 minutes (le spread seul coûte 0,19 $) ; avec stop dur et objectif, −0,58 à −0,91 $.
5. Prochain passage : je mets la mécanique de BlockTrend en essai sur la démo à 0,01 lot, or seul, 3 positions au plus, avec sa règle d'arrêt écrite avant. Rien à te demander.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 12/11 12 h 10

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 197 | −0,28 $ | ± 0,19 $ | référence |
| elan_m1 | 198 | +0,11 $ | ± 0,19 $ | continue jusqu'à 300 trades (banc : −0,19 $, le spread) |
| retour_m1 | 198 | −0,51 $ | ± 0,19 $ | continue jusqu'à 300 trades (comme le témoin) |
| fcassure_m1 | 58 | −0,09 $ | ± 0,26 $ | continue (comme le témoin) |
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
