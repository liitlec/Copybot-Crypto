# Avis pour Baptiste — 13/11/2026, 7 h (passage 25, court)

0. **Le pont ne répond plus depuis 1 h 07 cette nuit** (PC éteint ou en veille ?) : le robot ne trade plus tant qu'il n'est pas rallumé. Les 3 petites positions ouvertes ont leur stop chez le courtier.
1. **Le repli d'indices (ton BlockRange corrigé) est sur la démo** : robot version 9, étiquette `repli_ind`, sur NAS100+, SP500+, DJ30+, GER40+ (pas le FTSE), à la taille minimale du courtier. Les bougies du courtier confirment le banc : +25 bp par trade sur le Nasdaq (62 trades), +40 bp sur le S&P (54 trades, 80 % de gagnants).
2. **Il tradera peu** : ≈ 35 à 40 trades par an sur 4 indices (aucun signal aujourd'hui). Règle d'arrêt écrite avant : somme des trades sous −1 500 bp, ou moyenne sous −20 bp après 60 trades. Ses positions survivent maintenant aux mises à jour du robot.
3. **Mécanique BlockTrend ailleurs que sur l'or : non.** Argent +0,07 R par panier (t = 0,4), BTC +0,06 R, ETH +0,01 R, Nasdaq zéro. Elle ne tient que sur l'or, et tout son gain vient des ajouts pendant quelques grands mouvements. Rien d'autre mis en essai.
4. `elan_m1` est éteint depuis 22 h 17 (version 8) ; les scalps M1 restent au niveau du hasard ; `bt_or` attend son premier panier valable.
5. Prochains passages : comment tirer plus du repli d'indices (plus d'indices, sorties, taille, filtres), avec le tableau « base / améliorée » et le chiffrage « 1 % par jour ». Rien à faire de ton côté.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 12/11 23 h 08 (Paris 22 h 08)

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 317 | −0,31 $ | ± 0,18 $ | référence |
| elan_m1 | 319 | −0,03 $ | ± 0,18 $ | **éteint** en version 8 (dans la marge du témoin à 300 trades) |
| retour_m1 | 279 | −0,55 $ | ± 0,20 $ | éteint depuis la version 7 |
| fcassure_m1 | 95 | +0,10 $ | ± 0,25 $ | continue jusqu'à 300 trades (comme le témoin pour l'instant) |
| exces_m1 | 15 | +1,38 $ | ± 1,94 $ | continue |
| elan_m15 | 12 | +4,95 $ | ± 4,23 $ | continue (banc 15 mois : −0,16 $) |
| cassure_m15 | 5 | +8,63 $ | ± 9,04 $ | continue |
| exces_m5 | 4 | +4,16 $ | ± 4,79 $ | continue |
| midi_agite (candidat) | 1 | −0,06 $ | inconnue | 11 h – 14 h quand l'or est agité ; arrêt : < −0,50 $ après 60 trades ou −60 $ |
| repli_ind (repli d'indices, v9) | 0 | — | — | arrêt : somme < −1 500 bp, ou moyenne < −20 bp après 60 trades |
| bt_or (mécanique BlockTrend) | 0 panier valable (le 1er, −0,94 $, coupé par la mise à jour v7) | — | — | arrêt à −20 R cumulés ou moyenne < −0,3 R après 40 paniers |

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
