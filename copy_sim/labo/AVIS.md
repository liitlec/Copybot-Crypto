# Avis pour Baptiste — 11/11/2026, 19 h (passage 4)

1. **Robot version 2 poussé : scalp presque continu** sur XAUUSD en démo, 0,01 lot, 8 hypothèses étiquetées, environ **800 à 900 trades par jour** (3 hypothèses M1 ouvrent toutes les 5 minutes, dont le témoin au hasard).
2. **Ce sont des essais, rien n'est prouvé** : sur 3 mois de bougies M1 de ton courtier, ces règles font zéro avant frais. Si le direct confirme, la démo perdra environ 0,19 $ par trade, soit ≈ 160 $ par jour : c'est le prix de la mesure.
3. Premiers chiffres réels (v1, 27 minutes) : 2 ouvertures, spread 0,19-0,20 $ comme prévu, **glissement nul**, aucun refus. 1 trade fermé (−1,27 $) : trop peu pour conclure quoi que ce soit.
4. Prochain passage : tableau par hypothèse et par heure avec marge d'erreur, coupe de ce qui fait pire que le témoin, puis la recherche massive (or, argent, `NAS100+`, `SP500+`, `GER40+` : données reçues).
5. Aucune limite du pont ne gêne la cadence pour l'instant. Pour tout arrêter : `STOP_PONT` côté PC.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés)

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur | Décision |
|---|---|---|---|---|
| hasard_m15 (témoin v1, retiré) | 1 | −1,27 $ | inconnue (1 trade) | remplacé par hasard_m1 |
| elan_m15 | 0 (1 ouvert, +2,97 $ latent) | — | — | continue |
| hasard_m1, elan_m1, retour_m1, exces_m1, fcassure_m1, exces_m5, cassure_m15 | 0 | — | — | démarrent avec la v2 |

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
