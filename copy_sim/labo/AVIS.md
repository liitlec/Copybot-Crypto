# Avis pour Baptiste — 13/11/2026, 10 h 35 (passage 27)

1. **Le pont ne répond plus depuis 1 h 07 cette nuit** (9 heures) : le robot ne trade pas. Il faut rallumer le PC (ou relancer le pont).
2. **Ton BlockFinMois refait sur 25 ans.** Sur les indices : +125 bp par trade depuis 2016 (258 trades), mais presque rien avant 2016 : c'est une règle du marché récent, pas un effet stable, et elle ressemble beaucoup au repli d'indices déjà en démo.
3. **Sur les devises** (fin de mois, achat après une baisse courte) : petit mais régulier, +12 à +14 bp par trade sur les deux périodes, ≈ 45 trades par an, 3 à 4 fois mieux que le même achat un autre jour. À vérifier avec le vrai spread du courtier avant d'y croire.
4. Rappel d'hier : le repli d'indices ne s'améliore pas par le réglage ; plafond réaliste +8 à +15 % par an pour −24 à −44 % de pire baisse.
5. Ensuite : vérifier la piste « devises de fin de mois » sur les données du courtier et la mettre en démo avant le 30/11 si elle tient.

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
