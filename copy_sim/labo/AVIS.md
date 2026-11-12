# Avis pour Baptiste — 12/11/2026, 17 h 35 (passage 21)

1. **1 % par jour, chiffré honnêtement.** Avec la mécanique de BlockTrend sur l'or, si son avantage du banc est réel : risquer 0,5 % du compte par position donne ≈ 0,16 % par jour (+45 % par an, pire baisse −9 %) ; risquer 1 % donne ≈ 0,32 % par jour (pire baisse −18 %). **Pour 1 % par jour il faudrait risquer 3,1 % par position, avec 41 % de chances de perdre la moitié du compte dans l'année.**
2. Avec le « retour de midi », 1 % par jour demanderait un levier d'environ 20 : au banc cela passe, mais il a déjà perdu sur juin-août 2025, et à ce levier un seul écart de 5 % de l'or efface le compte.
3. Et ces chiffres supposent que l'avantage existe. Aucun n'est encore confirmé en direct ; si l'avantage est nul, grossir la taille ne fait que grossir les pertes. C'est à toi de choisir le niveau de risque, une fois le direct connu.
4. **Premier panier `bt_or` en cours** : vendeur depuis 14 h 50 à 3 896, 2 ajouts pendant la chute (3 870, 3 854), l'or est remonté à 3 875 : ≈ −6 $ pour l'instant, stop suiveur vers 3 909. Reste du robot : 898 trades, ≈ −145 $ à 0,01 lot.
5. Modèle appris sur 26 variables : il ne prévoit rien (pas mieux qu'un témoin mélangé). 48 553 combinaisons testées. Prochain passage : stratégies à critères multiples, annonces, sorties fines.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 12/11 17 h 11

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 257 | −0,29 $ | ± 0,21 $ | référence |
| elan_m1 | 259 | +0,04 $ | ± 0,20 $ | continue jusqu'à 300 trades (banc : −0,19 $, le spread) |
| retour_m1 | 259 | −0,55 $ | ± 0,20 $ | continue jusqu'à 300 trades (comme le témoin) |
| fcassure_m1 | 81 | +0,00 $ | ± 0,28 $ | continue (comme le témoin) |
| exces_m1 | 14 | +1,27 $ | ± 2,08 $ | continue |
| elan_m15 | 7 | −1,00 $ | ± 4,48 $ | continue |
| cassure_m15 | 3 | +4,03 $ | ± 10,8 $ | continue |
| exces_m5 | 1 | +0,40 $ | inconnue | continue |
| midi_agite (candidat) | 1 | −0,06 $ | inconnue | trade de 11 h à 14 h quand l'or est agité ; arrêt : < −0,50 $ après 60 trades ou −60 $ |
| bt_or (mécanique BlockTrend, v6) | 0 fermé, 1 panier de 3 ventes ouvert (≈ −6 $) | — | — | arrêt à −20 R cumulés ou moyenne < −0,3 R après 40 paniers |
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
