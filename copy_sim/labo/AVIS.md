# Avis pour Baptiste — 12/11/2026, 10 h 25 (passage 15)

1. **J'ai cherché ce qu'il y a de bon chez tes autres robots**, groupe par groupe. Deux choses gagnaient : les ventes d'or de BlockFIFO (+3 439 $) et les ventes d'ETH de BlockTrend (+2 332 $).
2. **Je ne les reprends pas**, et voici pourquoi : les ventes de BlockFIFO sont le jumeau exact de ses achats (−9 709 $), même mécanique qui grossit quand ça perd ; elles ont gagné parce que l'or baissait cette semaine-là. Idem pour l'ETH en octobre. C'est le sens du marché, pas une règle.
3. J'ai testé l'idée proprement sur 20 ans : « suivre la tendance seulement à la vente » perd 3,9 % par an depuis 2016, sur toutes les familles de marchés (ETH −3,6 %, or −4,4 %). Les baisses sont trop courtes et les rebonds reprennent tout.
4. Mon robot : 584 trades fermés, total ≈ −110 $ à 0,01 lot. `elan_m1` est à +0,50 $ par trade au-dessus du pile ou face (± 0,28) : encourageant mais pas encore un résultat, j'attends 300 trades.
5. Le candidat « retour de midi » commence à 11 h. Rien à te demander.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 12/11 10 h 07

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 172 | −0,30 $ | ± 0,20 $ | référence |
| elan_m1 | 173 | +0,20 $ | ± 0,19 $ | continue jusqu'à 300 trades (+0,50 $ sur le témoin, ± 0,28) |
| retour_m1 | 173 | −0,57 $ | ± 0,20 $ | continue jusqu'à 300 trades (comme le témoin) |
| fcassure_m1 | 48 | −0,04 $ | ± 0,31 $ | continue (comme le témoin) |
| exces_m1 | 8 | +3,23 $ | ± 1,73 $ | continue |
| elan_m15 | 7 | −1,00 $ | ± 4,48 $ | continue |
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
