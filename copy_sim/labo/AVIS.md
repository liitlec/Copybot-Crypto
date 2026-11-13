# Avis pour Baptiste — 14/11/2026, 0 h 25 (passage 33)

1. **Robot version 10 installée** (22 h 42) : le repli d'indices suit 5 indices (Nasdaq, S&P 500, Dow, DAX, Russell 2000). Marché fermé jusqu'à lundi vers 0 h.
2. **Repli d'indices en H4 au lieu du jour : non.** Sur le Nasdaq du courtier, la même règle en H4 fait zéro (−5 à +10 bp par trade) contre +25 bp en jour. On ne peut pas multiplier les trades en descendant d'unité de temps.
3. Rappel : l'effet est américain (S&P et Dow +40 bp, Nasdaq et Russell +25 bp ; indices européens ≈ zéro) et son plafond réaliste est +8 à +15 % par an.
4. Direct : scalps M1 au niveau du hasard ; aucun trade encore pour le repli d'indices ni pour `bt_or`.
5. Week-end : passages courts. Reste à étudier : les annonces économiques sur l'or.

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
