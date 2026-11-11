# Avis pour Baptiste — 11/11/2026, 18 h 20 (passage 3)

1. **Le robot tourne** (version 1, installée et démarrée à 18 h 16 sans erreur) : il trade XAUUSD sur ta démo à 0,01 lot, 4 hypothèses étiquetées, chacune avec un stop. Ce sont des **essais en direct, rien de prouvé**.
2. Ce qui tourne : `hasard_m15` (témoin pile ou face, mesure le spread et le glissement réels), `elan_m15`, `cassure_m15` (tenue 3 h), `exces_m5` (tenue 15 min). Sur les données passées, aucune ne gagne de façon nette.
3. Rappel du passage 2 : l'or est bien le moins cher à scalper chez ton courtier (spread = 28 % du mouvement M1, EURUSD 323 %), mais 90 règles simples testées font zéro avant frais. Combinaisons testées à ce jour : 263.
4. Prochain passage : premiers résultats réels par hypothèse (avec nombre de trades et marge d'erreur), puis la recherche massive de combinaisons sur l'or, l'argent et les indices (merci pour les noms `NAS100+`…).
5. Pour tout arrêter : le fichier `STOP_PONT` côté PC. Rien à faire d'autre.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés)

| Hypothèse | Trades | Gain moyen après spread | Marge d'erreur | Décision |
|---|---|---|---|---|
| hasard_m15 (témoin) | 0 | — | — | vient de démarrer |
| elan_m15 | 0 | — | — | vient de démarrer |
| cassure_m15 | 0 | — | — | vient de démarrer |
| exces_m5 | 0 | — | — | vient de démarrer |

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
