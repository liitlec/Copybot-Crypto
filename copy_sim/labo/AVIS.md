# Avis pour Baptiste — 12/11/2026, 2 h 40 (passage 7)

1. **Toujours aucun scalp prouvé** (48 087 combinaisons testées). En direct, 266 trades fermés : les règles M1 font exactement comme le pile ou face (−0,20 $ par trade = le spread). Solde démo : 66 664 $ (départ 66 675 $).
2. **Le candidat « retour de midi » est une stratégie de régime** : il gagne quand l'or est agité (+5,6 points de base par trade dans le tiers le plus agité des 15 derniers mois), rien quand l'or est calme (il perdait en juin-août 2025). Aujourd'hui l'agitation est moyenne.
3. **Sa règle d'arrêt est écrite avant ses premiers trades** (ce matin 11 h, 0,01 lot) : arrêt si la moyenne est sous −0,50 $ après 60 trades, ou dès 60 $ de perte cumulée ; on ne monte la taille qu'après 100 trades gagnants en moyenne.
4. Robot version 4 : il ne prend plus de position autour de la fermeture nocturne de l'or (22 h 50 – 0 h 10), où 7 stops ont sauté sur des trous de prix.
5. Honnêtement : si le candidat tient, c'est environ +0,9 $ par trade à 0,01 lot, 4 trades par jour, et cela peut s'arrêter du jour au lendemain. Rien à te demander.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 12/11 2 h 12

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 77 | −0,25 $ | ± 0,28 $ | référence |
| elan_m1 | 77 | −0,17 $ | ± 0,26 $ | continue jusqu'à 300 trades (comme le témoin) |
| retour_m1 | 77 | −0,24 $ | ± 0,27 $ | continue jusqu'à 300 trades (comme le témoin) |
| fcassure_m1 | 25 | +0,45 $ | ± 0,42 $ | continue (trop peu pour conclure) |
| exces_m1 | 5 | +2,20 $ | ± 2,44 $ | continue |
| elan_m15 | 3 | +4,56 $ | ± 1,17 $ | continue (3 trades : rien à conclure) |
| cassure_m15 | 1 | +6,86 $ | inconnue | continue |
| exces_m5 | 1 | +0,40 $ | inconnue | continue |
| ecart_midi_m5 (candidat) | 0 | — | — | commence ce 12/11 à 11 h ; arrêt : < −0,50 $ après 60 trades ou −60 $ cumulés |

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
