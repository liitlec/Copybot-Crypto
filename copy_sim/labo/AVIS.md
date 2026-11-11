# Avis pour Baptiste — 11/11/2026, 21 h 30 (passage 5)

1. **Recherche massive faite : 47 628 combinaisons** (or M1 et M5, argent, Nasdaq, S&P, DAX ; règles × tenues × heures × volatilité, spread réel). **Aucune ne gagne de façon prouvée** sur la période jamais vue.
2. Le seul groupe au-dessus du hasard : sur l'or en M5, entre 11 h et 14 h (Paris), parier sur le retour après un écart trop fort, tenue 15 min. Gain passé faible (+0,4 à +1,3 point de base par trade) et non prouvé : je l'ai ajouté au robot (version 3) pour le voir en vrai dès demain 11 h.
3. Le robot en direct (3 heures, 92 trades fermés) : exécution parfaite (0 refus, spread 0,20 $, glissement nul), mais aucune règle ne fait mieux que le pile ou face. La démo a perdu 31 $, comme prévu par le coût du spread.
4. Découverte utile : le **Nasdaq (`NAS100+`) est encore moins cher à scalper que l'or** chez ton courtier (spread = 21 % du mouvement d'une minute contre 28 %) ; l'argent, le S&P et le DAX sont bien plus chers.
5. Suite : laisser tourner jusqu'à ≈ 300 trades par règle avant de couper, affiner autour du seul candidat, étendre la grille (stops/objectifs, tendance de fond, Nasdaq). Rien à te demander.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 11/11 21 h 03

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 27 | −0,66 $ | ± 0,34 $ | référence |
| elan_m1 | 27 | −0,01 $ | ± 0,36 $ | continue (pas distinguable du témoin) |
| retour_m1 | 27 | −0,22 $ | ± 0,35 $ | continue (idem) |
| fcassure_m1 | 9 | −0,50 $ | ± 0,66 $ | continue |
| exces_m1 | 1 (sorti au stop) | ≈ −4,10 $ | inconnue | continue |
| elan_m15 | 1 | +3,07 $ | inconnue | continue |
| exces_m5, cassure_m15 | 0 | — | — | attendent leur signal |
| ecart_midi_m5 (nouveau, v3) | 0 | — | — | commence le 12/11 à 11 h |

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
