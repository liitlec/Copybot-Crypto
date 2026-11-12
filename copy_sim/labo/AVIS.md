# Avis pour Baptiste — 12/11/2026, 14 h 50 (passage 20)

1. **La mécanique de BlockTrend est en essai sur la démo** (robot version 6) : or seul, 0,01 lot par position, 3 positions au plus par panier, ajouts seulement dans le sens du gain, stop suiveur. Étiquettes `bt_or_1` à `bt_or_3`.
2. **À quoi t'attendre** : au banc elle gagne +0,38 R par panier sur 15 mois, mais 7 paniers sur 10 perdent environ 1 R (40 à 60 $ ici) et le gain vient de quelques gros mouvements. Les deux derniers mois sont négatifs (−7,5 R). Des pertes à la suite seront normales.
3. **Règle d'arrêt écrite avant** : arrêt à −20 R cumulés (≈ −1 000 $ sur la démo ; le pire creux du banc est −18 R) ou si la moyenne est sous −0,3 R après 40 paniers. On ne monte la taille que si le direct confirme.
4. Rappel : ce qui a coûté 25 189 $ à BlockTrend, c'est la taille (≈ 2,4 % du compte par signal, 3 paniers à la fois) et les marchés sans preuve (cacao, BTC, ETH). BlockFIFO : rien à sauver.
5. Scalp : toujours rien de prouvé (48 549 combinaisons) ; mon robot est à ≈ −85 $ sur 765 trades à 0,01 lot. Rien à te demander.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 12/11 14 h 14

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 222 | −0,18 $ | ± 0,19 $ | référence |
| elan_m1 | 223 | +0,07 $ | ± 0,18 $ | continue jusqu'à 300 trades (banc : −0,19 $, le spread) |
| retour_m1 | 223 | −0,44 $ | ± 0,18 $ | continue jusqu'à 300 trades (comme le témoin) |
| fcassure_m1 | 67 | −0,07 $ | ± 0,23 $ | continue (comme le témoin) |
| exces_m1 | 10 | +2,95 $ | ± 1,47 $ | continue |
| elan_m15 | 7 | −1,00 $ | ± 4,48 $ | continue |
| cassure_m15 | 3 | +4,03 $ | ± 10,8 $ | continue |
| exces_m5 | 1 | +0,40 $ | inconnue | continue |
| midi_agite (candidat) | 1 | −0,06 $ | inconnue | trade de 11 h à 14 h quand l'or est agité ; arrêt : < −0,50 $ après 60 trades ou −60 $ |
| bt_or (mécanique BlockTrend, nouveau v6) | 0 | — | — | arrêt à −20 R cumulés ou moyenne < −0,3 R après 40 paniers |
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
