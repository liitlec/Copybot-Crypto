# Avis pour Baptiste — 11/11/2026, 22 h 25 (passage 6)

1. **Toujours aucun scalp prouvé**, après 48 077 combinaisons testées avec le spread réel de ton courtier.
2. Le seul candidat (« retour de midi » : sur l'or en M5, entre 11 h et 14 h Paris, parier sur le retour après un écart trop fort, 15 min) a gagné dans 5 périodes de 3 mois sur 5 depuis août 2025 (+2,3 points de base par trade, presque significatif), **mais il perd sur la période d'avant** : fragile. Il trade demain dès 11 h à 0,01 lot.
3. Robot en direct (4 heures, 135 trades fermés) : exécution parfaite (0 refus, glissement nul). Les trois règles M1 font comme le pile ou face ; les deux règles M15 ont gagné 17 $ sur 3 trades, ce qui ne prouve rien. Compte démo : 66 673 $ (départ 66 675 $).
4. Ordre de grandeur honnête : même si le candidat était vrai, il rapporterait environ 0,1 % par jour sans levier. 1 % par jour demanderait un fort levier, donc un fort risque.
5. Suite : refaire l'épreuve du candidat sur l'or de 2024 (données demandées au pont), laisser le robot accumuler ≈ 300 trades par règle, puis grille élargie sur le Nasdaq.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 11/11 22 h 07

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 40 | −0,17 $ | ± 0,29 $ | référence |
| elan_m1 | 40 | −0,03 $ | ± 0,28 $ | continue (pas distinguable du témoin) |
| retour_m1 | 40 | −0,12 $ | ± 0,29 $ | continue (idem) |
| fcassure_m1 | 11 | −0,03 $ | ± 0,65 $ | continue |
| elan_m15 | 2 | +4,97 $ | ± 1,90 $ | continue (2 trades : rien à conclure) |
| cassure_m15 | 1 | +6,86 $ | inconnue | continue |
| exces_m1 | 1 (sorti au stop) | ≈ −4,10 $ | inconnue | continue |
| exces_m5 | 0 | — | — | attend son signal |
| ecart_midi_m5 (candidat) | 0 | — | — | commence le 12/11 à 11 h |

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
