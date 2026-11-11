# Avis pour Baptiste — 11/11/2026, 19 h (passage 4)

1. **Le robot version 2 tourne depuis 18 h 46** : scalp presque continu sur XAUUSD en démo, 0,01 lot, 8 hypothèses étiquetées, environ 800 à 900 trades par jour (3 hypothèses M1 ouvrent toutes les 5 minutes, dont le témoin au hasard).
2. **Ce sont des essais, rien n'est prouvé** : sur 3 mois de bougies M1 de ton courtier, ces règles font zéro avant frais. Si le direct confirme, la démo perdra environ 0,20 $ par trade, soit ≈ 160 $ par jour : c'est le prix de la mesure.
3. Exécution réelle sur 14 ouvertures : aucun refus, spread 0,20 $ comme prévu, glissement moyen 0,007 $ (pire cas 0,15 $). Les gains du tableau ci-dessous portent sur 1 ou 2 trades : **ils ne veulent encore rien dire**.
4. Prochain passage : tableau par hypothèse et par heure sur des centaines de trades, coupe de ce qui fait pire que le témoin, puis la recherche massive (or, argent, `NAS100+`, `SP500+`, `GER40+` : données reçues).
5. À signaler côté PC (pas urgent) : une erreur passagère du pont à 18 h 53 (« Accès refusé » en remplaçant `garde_jour.json`, le robot a continué), et ce message a écrit le chemin `C:\Users\…` avec ton nom d'utilisateur Windows dans `robot_journal.jsonl`, qui est public. Je masquerai les chemins dans la prochaine version du robot.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 11/11 18 h 58

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 2 | −2,84 $ | ± 0,72 $ | continue |
| elan_m1 | 2 | +2,45 $ | ± 0,71 $ | continue (2 trades : rien à conclure) |
| retour_m1 | 2 | −2,95 $ | ± 0,63 $ | continue |
| fcassure_m1 | 1 | −0,28 $ | inconnue | continue |
| elan_m15 | 1 | +3,07 $ | inconnue | continue |
| hasard_m15 (témoin v1, retiré) | 2 | −0,68 $ | ± 0,59 $ | remplacé par hasard_m1 |
| exces_m1, exces_m5, cassure_m15 | 0 | — | — | attendent leur signal |

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
