# Avis pour Baptiste — 12/11/2026, 12 h 50 (passage 18)

1. **Recherche large commencée : deux familles testées, aucune ne passe** (160 essais de plus, 48 522 au total).
2. **Ordres à cours limité** : chez un courtier CFD, un achat limite est servi au prix acheteur, donc on paie le spread quand même ; et l'ordre n'est servi que quand le prix part contre nous. Résultat : pire qu'entrer au marché (−0,6 à −0,9 point de base par trade contre −0,46). Les scalpeurs qui « gagnent le spread » le font sur des marchés à carnet d'ordres, pas sur un CFD.
3. **Concepts de liquidité** (chasse aux stops d'Asie et de la veille, niveaux ronds, écart de juste valeur, retour au VWAP) : tous perdent ou font zéro après spread. Seule piste faible : suivre la cassure du range d'Asie 2 heures (+4 à +6 points de base, non significatif), à creuser.
4. `elan_m1` et `exces_m1` découpés sur 3 mois (passage 17) : aucune semaine, heure, agitation ou tendance où ils gagnent. Robot en direct : ≈ 680 trades, ≈ −110 $ à 0,01 lot.
5. Si tes amis ont des règles précises (quand ils entrent, où ils sortent), écris-les dans `labo/IDEES_AMIS.md` : je les teste en premier, telles quelles. Prochaines familles : annonces, structure M15/H1, modèles appris, sorties fines.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 12/11 12 h 10

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 197 | −0,28 $ | ± 0,19 $ | référence |
| elan_m1 | 198 | +0,11 $ | ± 0,19 $ | continue jusqu'à 300 trades (banc : −0,19 $, le spread) |
| retour_m1 | 198 | −0,51 $ | ± 0,19 $ | continue jusqu'à 300 trades (comme le témoin) |
| fcassure_m1 | 58 | −0,09 $ | ± 0,26 $ | continue (comme le témoin) |
| exces_m1 | 8 | +3,23 $ | ± 1,73 $ | continue |
| elan_m15 | 7 | −1,00 $ | ± 4,48 $ | continue |
| cassure_m15 | 3 | +4,03 $ | ± 10,8 $ | continue |
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
