# Avis pour Baptiste — 16/11/2026, 10 h 15 (relais)

0. **Pont revenu à 6 h 57, v11 installée et en marche** ; marché calme ce matin, donc la sélection du test est en pause et seul le témoin trade. Le test compte les trades fermés depuis lundi 0 h.
0 a. **Variantes « calme » (v12) écrites et testées, pas encore publiées** : un panier `bt_or` du test est ouvert depuis 7 h 05 et une mise à jour du robot le fermerait (seules les positions d'indices survivent, pas `bt_or`). Je publie dès que le panier est fermé ; idéalement, côté PC, garder `etat_bt.json` d'une version à l'autre.
0 b. **10 h 15** : panier `bt_or` toujours ouvert, v12 toujours en attente. Ta demande « réagir plus vite aux retournements » est notée : une idée à la fois au banc, puis en variantes `_opt` sur la démo, publiées avec la v12.
0 bis. **public-apis (`labo/APIS.md`)** : Helious donne gratuitement, sans clé, le calendrier des annonces (heure, importance, prévu/publié) → on pourra tester « couper le robot autour des annonces fortes ». Goldprice.dev répond aussi ; TradingCalendars demande une clé (inutile pour l'instant).
0 ter. **Anti-secrets** : `labo/verif_secrets.py` vérifie chaque commit (clés, jetons, mots de passe, numéro de compte) ; idée tirée d'ECC, détails dans `labo/ECC.md`.
1. **Robot v11 publié** (pause des petites règles quand l'or est calme) : essais OK, aucun panier ouvert ; ton PC l'installera au rallumage lundi.
2. Le test de la semaine 16-20/11 démarre lundi 0 h avec les critères fixés le 15/11 ; bilan vendredi soir en tête de ce fichier.
3. Jusqu'à mercredi 16 h, passages courts : suivi du test et une petite étape à la fois sur public-apis, ECC et les dépôts de trading.

## Avis précédent (passage 43)

1. **Comment le robot reconnaît le calme** : il mesure de combien l'or bouge en moyenne d'une heure à l'autre sur les 24 dernières heures, et compare à sa valeur habituelle des 60 derniers jours ; en dessous de la médiane = calme. Recalculé chaque heure : il faut quelques heures de mouvement pour repasser en « agité ».
2. **Le calme avant le mouvement (compression puis cassure) : testé, non.** La cassure d'une fourchette très serrée (4 h, 8 h, 24 h) ne vaut pas mieux que celle d'une fourchette normale, plutôt moins : après un long calme, la première sortie est souvent fausse. Vérifié aussi sur le Nasdaq, l'argent, l'EURUSD et le BTC : rien non plus.
3. **Spread heure par heure** : 0,20 $ à toute heure, calme ou pas ; il n'y a pas d'heure moins chère. Un calme dure en moyenne 1 jour (le plus long : 25 jours).
4. **Portage** : je ne vois pas les swaps du courtier. Il faudrait que le pont ajoute `swap_long` et `swap_short` par symbole dans `etat.json` (à demander côté PC).
5. La règle reste « au calme, ne rien faire » ; la version 11 du robot (pause de ses petites règles quand l'or est calme) est écrite et testée, je la publie lundi à la réouverture. J'attends les règles de tes amis pour les tester.

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
