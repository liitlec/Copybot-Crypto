# Avis pour Baptiste — 12/11/2026, 12 h 30 (passage 17)

1. **`elan_m1` découpé sur 3 mois (17 991 trades) : il ne gagne dans aucune condition.** Aucune des 14 semaines n'est positive, aucune heure (de −0,38 à +0,01 $ par trade), ni or calme ni or agité (−0,16 à −0,22 $), ni dans le sens de la tendance (−0,16 $) ni contre (−0,22 $). Avant spread il fait zéro partout ; après spread il perd le spread.
2. **`exces_m1` (922 trades) : rien de net non plus.** Moyenne −0,15 $ (± 0,23). Il est à +0,11 $ (± 0,40) les jours agités et à −0,32 $ les jours calmes : trop petit pour être distingué du hasard. Quelques heures ressortent (15 h : +2,22 $ ± 1,48) mais sur 50 trades et parmi 92 cases examinées.
3. Leurs bons chiffres en direct (+0,11 $ sur 198 trades, +3,23 $ sur 8 trades) sont donc de la chance pour l'instant. Je n'en tire aucune nouvelle hypothèse.
4. Mon robot : 672 trades fermés, total ≈ −110 $ à 0,01 lot, 0 refus. Rien de prouvé (48 362 combinaisons testées).
5. Le candidat de midi est dans sa fenêtre (11 h – 14 h) sans signal pour l'instant. Rien à te demander.

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
