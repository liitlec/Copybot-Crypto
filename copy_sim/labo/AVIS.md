# Avis pour Baptiste — 13/11/2026, 23 h (passage 32)

1. **Le repli d'indices est un effet américain.** Sur les bougies de ton courtier : S&P 500 et Dow +40 bp par trade (75 à 80 % de gagnants), Nasdaq et Russell 2000 +25 bp ; DAX, CAC et EuroStoxx à peu près zéro ; rien de net sur l'or.
2. **Robot version 10** : le Russell 2000 (`US2000+`) est ajouté, soit 5 indices suivis. Je garde le DAX pour l'instant (liste fixée avant le premier trade) et le retirerai s'il déçoit aussi en direct.
3. Direct : rien de neuf, les scalps M1 restent au niveau du hasard (témoin −0,33 $ par trade sur 395 trades). Aucun trade encore pour le repli d'indices ni pour `bt_or`.
4. Le marché ferme pour le week-end ; reprise lundi vers 0 h. Passages courts d'ici là.
5. Ensuite : dernière famille de recherche (annonces économiques) ; entrée en H4 pour le repli d'indices (données reçues).

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 13/11 20 h 13 (Paris)

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 367 | −0,30 $ | ± 0,16 $ | référence |
| fcassure_m1 | 108 | +0,16 $ | ± 0,22 $ | continue jusqu'à 300 trades |
| exces_m1 | 16 | +1,32 $ | ± 1,82 $ | continue |
| elan_m15 | 15 | +3,08 $ | ± 3,52 $ | continue (banc 15 mois : −0,16 $) |
| cassure_m15 | 5 | +8,63 $ | ± 9,04 $ | continue |
| exces_m5 | 4 | +4,16 $ | ± 4,79 $ | continue |
| midi_agite (candidat) | 1 | −0,06 $ | inconnue | arrêt : < −0,50 $ après 60 trades ou −60 $ |
| repli_ind (repli d'indices) | 0 | — | — | arrêt : somme < −1 500 bp, ou moyenne < −20 bp après 60 trades |
| bt_or (mécanique BlockTrend) | 0 panier valable | — | — | arrêt à −20 R cumulés ou moyenne < −0,3 R après 40 paniers |
| elan_m1, retour_m1 | 322 et 279 | −0,03 $ et −0,55 $ | ± 0,18 $ | éteints (versions 8 et 7) |

## Candidat prouvé au banc, en direct depuis la version 9 : repli d'indices (mécanique BlockRange)

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
