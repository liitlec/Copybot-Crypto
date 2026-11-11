# Journal du laboratoire (le plus récent en bas ; on n'efface rien)

## Passage 1 — 11/11/2026 (≈ 17 h Paris) — base neuve, trois bancs, registre ouvert

**Données.** Yahoo (`query2`, User-Agent de navigateur ; `range=max` rend du mensuel → demander `period1/period2`).
17 séries journalières (7 devises, or, argent, 5 indices, BTC, ETH, taux US 3 mois), 9 séries 1 h sur ~2 ans.
stooq.com est bloqué (vérification JavaScript). Pétrole écarté (prix négatif d'avril 2020 dans la série continue).

**Coûts retenus (compte CFD standard, prudents).** Par sens : devises 1 bp, métaux 2, indices 1,5, crypto 8.
Financement : indices/métaux = taux US + 2,5 %/an à l'achat (dividendes rendus), 2,5 % − taux à la vente ;
devises 1 %/an des deux côtés (écart de taux ignoré, faute de données) ; crypto 15 %/an long, 5 % court.
À vérifier un jour sur les vraies conditions STARTRADER (swaps affichés dans MT5).

**Banc A — suivi de tendance journalier, 16 actifs, règle fixée d'avance** (`banc_tendance.py`, 5 essais : 1 principal
+ 4 horizons seuls). Rendement/an, Sharpe, pire baisse :

| | 2001-2015 | 2016-2026 | 2023-2026 |
|---|---|---|---|
| Tendance brut | +7,4 % / 0,68 / −20 % | +2,7 % / 0,33 / −19 % | +2,2 % / 0,29 / −12 % |
| **Tendance net** | +3,7 % / 0,37 / −24 % | **−1,8 % / −0,15 / −27 %** | −3,6 % / −0,38 / −15 % |
| Tout acheter, même risque, net | +0,1 % / 0,07 / −46 % | +5,0 % / 0,47 / −36 % | +9,4 % / 0,80 / −16 % |

Coûts : 0,9 %/an d'échanges + 3,0 %/an de financement. Contre 300 tirages « mêmes signaux décalés au hasard » : la
tendance battait tout le hasard en 2001-2015, mais 44 % du hasard fait mieux en 2016-2026 et 77 % en 2023-2026.
Les devises sont la partie qui perd (Sharpe −0,57 depuis 2016). **Conclusion : réfuté en CFD sur cet univers.**

**Banc B — scalp simple à l'heure** (`banc_scalp_h1.py`, 18 règles × 9 actifs = 162 essais). Le coût d'un
aller-retour mange 27 à 39 % du mouvement médian d'une heure sur les devises, 30 % sur BTC/ETH, 6 à 12 % sur or et
indices. Tenue 1 h ou 4 h : toutes les règles sont à ≈ 0 bp brut, donc −2 à −3 bp net par trade. Meilleure règle par
actif choisie sur la 1re année puis jugée sur la 2e : +1,2 bp net par trade, t = +0,6 → rien de distinguable de zéro
(les seuls plus viennent de tenues de 24 barres sur indices et crypto, c'est-à-dire de la hausse générale).
Entrées au hasard : exactement moins le coût. **Conclusion : aucun avantage de scalp simple ; 1 %/jour est hors de
portée par ces moyens** (il faudrait ≈ 100 bp nets par jour ; on mesure 0 avant coûts).

**Banc C — acheter seulement (prime de risque), sans devises** (`banc_prime.py`, 3 variantes × 2 modes = 6 essais).
Univers choisi APRÈS avoir vu le banc A → en partie contaminé, d'où le registre papier.

| | 2001-2015 | 2016-2026 | 2023-2026 |
|---|---|---|---|
| CFD ×3, toujours acheté (expo ≈ 1,7) | +4,6 % / 0,33 / −48 % | +13,4 % / 0,79 / −39 % | +19,4 % / 1,05 / −24 % |
| CFD ×3, acheté si > moyenne 200 j | +5,9 % / 0,47 / −23 % | +8,9 % / 0,69 / −28 % | +11,1 % / 0,76 / −17 % |
| Comptant sans levier (expo ≈ 0,55) | +4,2 % / 0,69 / −16 % | +7,6 % / 1,27 / −12 % | +10,8 % / 1,70 / −8 % |
| Réf. 100 % S&P 500 comptant | +4,2 % / 0,31 / −56 % | +13,9 % / 0,83 / −34 % | +20,1 % / 1,34 / −19 % |

Le filtre 200 j ne bat pas un filtre décalé au hasard depuis 2016 (52 % du hasard fait mieux) ; il n'a servi qu'en
2001-2015 (2 %). Les Sharpe ne sont pas retranchés du taux sans risque et 2016-2026 est une période de hausse :
ce « montage » est surtout la prime de risque des actions, de l'or et du bitcoin, pas un talent de trading.
Le panier CFD ×3 ne fait pas mieux que le S&P 500 seul ; le comptant diversifié a la baisse la plus faible.

**Total des essais à ce jour : 5 + 162 + 6 = 173.**

**Registre papier ouvert** (`registre.py` → `registre.csv`, ajout seulement) : P1 panier CFD ×3, P2 idem + filtre
200 j, P3 panier comptant, T0 tendance (témoin réfuté). Départ 10 000 le 11/11/2026, premier jour compté le 12/11.
