# Avis pour Baptiste — 12/11/2026, 8 h 30 (passage 13)

1. **Toujours aucun scalp prouvé** (48 258 combinaisons). En direct, 505 trades fermés, total ≈ −102 $ à 0,01 lot : les règles M1 perdent le spread, comme le pile ou face.
2. **Plusieurs positions par stratégie** : merci, c'est noté, mais je ne m'en sers pas encore. Pour le candidat de midi, empiler les positions revient à ajouter sur une position qui perd : le gain par trade baisse (+1,8 contre +2,7 points de base) et le risque triple. Je garde une position à la fois.
3. Autre piste fermée : encaisser le financement sur Hyperliquid (acheter le bitcoin ou l'or, vendre le contrat) ne rapporte que 4 à 5 % par an net, autant qu'un placement sans risque.
4. Le candidat « retour de midi » fait ses premiers trades ce matin de 11 h à 14 h (0,01 lot, or calme aujourd'hui, peu d'attente). Règle d'arrêt : moyenne sous −0,50 $ après 60 trades ou 60 $ de perte.
5. Au prochain passage je lis l'historique de tes autres robots (`mt5/autres/`) pour voir s'il y a quelque chose à en apprendre. Rien à te demander.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 12/11 8 h 10

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 149 | −0,18 $ | ± 0,21 $ | référence |
| elan_m1 | 150 | +0,10 $ | ± 0,20 $ | continue jusqu'à 300 trades (comme le témoin) |
| retour_m1 | 150 | −0,57 $ | ± 0,20 $ | continue jusqu'à 300 trades (comme le témoin) |
| fcassure_m1 | 37 | +0,13 $ | ± 0,33 $ | continue (comme le témoin) |
| exces_m1 | 8 | +3,23 $ | ± 1,73 $ | continue |
| elan_m15 | 6 | −4,00 $ | ± 3,95 $ | continue |
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
