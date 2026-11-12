# Avis pour Baptiste — 12/11/2026, 9 h 30 (passage 14)

1. **J'ai étudié tes autres robots** (1 732 positions fermées depuis le 29/09) : ensemble ils ont perdu **33 906 $**. BlockTrend −25 189 $ (3 jours gagnants sur 17), BlockFIFO −6 269 $, BlockRange −2 382 $, BlockGrille −65 $. Aucun principe à reprendre.
2. Les +830 $ « en cours » de BlockTrend ce matin ne sont pas un gain : c'est 3 % de ce qu'il a déjà perdu, et ce n'est acquis qu'une fois fermé. BlockFIFO montre le piège classique : 59 % de trades gagnants, 4 jours gagnants sur 5, puis un jour à −10 684 $.
3. Mon robot : 543 trades fermés, total ≈ −129 $ à 0,01 lot, toujours rien de prouvé (48 258 combinaisons testées). `elan_m1` est un peu au-dessus du pile ou face (+0,48 $ ± 0,28), pas assez pour conclure.
4. Le candidat « retour de midi » commence à 11 h (0,01 lot, or calme, peu d'attente ; arrêt si moyenne sous −0,50 $ après 60 trades ou 60 $ de perte).
5. Page de suivi : je ne peux pas la publier d'ici (approbation en attente) ; j'y ai ajouté une section « Autres robots du compte » que ta conversation de suivi publiera. Rien à te demander.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 12/11 9 h 10

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 161 | −0,37 $ | ± 0,20 $ | référence |
| elan_m1 | 162 | +0,11 $ | ± 0,19 $ | continue jusqu'à 300 trades (+0,48 $ sur le témoin, ± 0,28) |
| retour_m1 | 162 | −0,52 $ | ± 0,20 $ | continue jusqu'à 300 trades (comme le témoin) |
| fcassure_m1 | 39 | +0,13 $ | ± 0,32 $ | continue (comme le témoin) |
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
