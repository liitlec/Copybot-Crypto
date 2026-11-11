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

## Passage 2 — 11/11/2026 (≈ 17 h 15 – 17 h 45 Paris) — priorité de Baptiste : scalp sur l'or, données du courtier

Passage supplémentaire signalé par la conversation de suivi ; vérifié dans le dépôt (`PRIORITES.md`, commits 10c7bd4
et 7ef96c9, référencé par `MISSION.md`). Le pont MT5 démo tourne (solde démo 66 674 $, aucune position).

**Données du courtier** (`mt5/demandes_donnees.json` → `mt5/donnees/`). 200 000 bougies : refusé par le terminal
(« aucune bougie ») ; 90 000 passe. Reçu : XAUUSD M1 (91 jours), M5 (462 jours), M15 (771 jours), EURUSD M1 et M5,
USDJPY M1. Aucun indice trouvé sous les noms NAS100, US500, USTEC, US100, SP500, US30, GER40 → demander à Baptiste
le nom exact d'un indice dans sa fenêtre « Observation du marché ». Horloge du serveur = UTC+2 = Paris + 1 h.

**Banc D, partie 1 — l'or est-il le moins cher à scalper ? Oui, nettement** (`banc_or.py`).

| | Spread médian | Mouvement médian de la bougie | Spread / mouvement |
|---|---|---|---|
| XAUUSD M1 | 0,46 bp (≈ 19 points, 0,19 $) | 1,66 bp | **28 %** |
| XAUUSD M5 | 0,46 bp | 4,07 bp | **11 %** |
| XAUUSD M15 | 0,50 bp | 6,04 bp | **8 %** |
| EURUSD M1 | 1,15 bp | 0,36 bp | 323 % |
| EURUSD M5 | 1,12 bp | 0,96 bp | 117 % |
| USDJPY M1 | 1,13 bp | 0,51 bp | 222 % |

Meilleures heures pour l'or (heure de Paris) : 14 h – 17 h (ouverture de New York, ratio 16 à 18 % en M1, 6,6 % en
M5) et 2 h – 4 h (Asie, ≈ 18-21 %). Pires : 22 h – 1 h (45 à 50 %). EURUSD et USDJPY : spread à minuit serveur ×3 à ×5.
Réserve : le spread d'une bougie MT5 est quasi constant (p95 = 0,51 bp), il ne montre sans doute pas les
élargissements pendant les annonces ; commission et glissement réels inconnus → à mesurer en vrai à 0,01 lot.

**Banc D, partie 2 — scalp sur l'or, 30 règles × 3 périodes = 90 essais.** Élan, retour, cassure de fourchette
(12 et 48 bougies), fausse cassure, excès > 3 écarts-types suivi ou contré ; tenue 1, 3, 12 bougies ; entrée à
l'ouverture suivante, spread réel payé ; réglage sur les 60 % premiers, verdict sur les 40 % derniers.

| Période | Règles gagnantes nettes au réglage | … encore gagnantes au verdict | Meilleure au réglage → verdict | Hasard même fréquence |
|---|---|---|---|---|
| M1 (91 j) | 2 / 30 (à +0,03 bp) | 0 | excès contré h12 : −1,01 bp/trade (t = −1,2) | −0,56 bp |
| M5 (462 j) | 3 / 30 | 1 | cassure n48 h12 : −1,29 bp (t = −1,2) | −0,42 bp |
| M15 (771 j) | 4 / 30 | 2 | excès suivi h12 : −5,99 bp (t = −1,1) | −0,93 bp |

Partout le gain brut est à ≈ 0 ± 0,2 bp par trade : les règles ne prévoient rien, on perd donc le spread
(−0,45 à −0,5 bp par trade ; à 100 trades par jour ≈ −0,5 % par jour à levier 1). Aucun t positif > 1,3 au verdict.
**Conclusion : l'or est bien le marché le moins cher (Baptiste a raison), mais aucune règle simple de bougies n'y
gagne.** Le faible coût ouvre quand même la porte : il suffit d'un avantage brut de 0,5 bp par trade.

**Total des essais : 173 + 90 = 263.**

Le lanceur du robot est apparu dans `etat.json` (champ `robot`, interface `copy_sim/forex/ROBOT_INTERFACE.md`) en fin
de passage : pas encore de robot écrit. Registre papier : pas de jour terminé depuis l'ouverture.

## Passage 3 — 11/11/2026 (≈ 18 h 15 – 18 h 45 Paris) — premier robot sur la démo MT5

Priorités de Baptiste relues dans `PRIORITES.md` (entrées de 18 h, 18 h 05, 18 h 10, 18 h 15 ; commit 19f76a7) :
trader sur la démo dès maintenant, petite taille, hypothèses étiquetées, apprendre des résultats ; recherche massive
de combinaisons avec garde-fous. Indices chez le courtier : `NAS100+`, `SP500+`, `DJ30+`, `GER40+`.

**Robot version 1** (`mt5/robot/robot.py`, essais `essais_robot.py`, `VERSION` = 1). XAUUSD, **0,01 lot** par
hypothèse, une position au plus par hypothèse (4 au maximum), stop de secours chez le courtier (4 × amplitude moyenne
de 48 bougies, 3 $ au moins), sortie au temps, pas d'ouverture si spread > 0,60 $. Toutes sont des **essais non
prouvés** (le banc D ne trouve d'avantage pour aucune) :

| Étiquette | Règle | Tenue | Ce que dit le banc D (net par trade, réglage → verdict) |
|---|---|---|---|
| `hasard_m15` | pile ou face à chaque bougie M15 | 5 min | témoin : attendu ≈ −0,5 bp ; sert à mesurer spread et glissement réels |
| `elan_m15` | sens du rendement de 12 bougies M15 | 3 h | +0,42 → +0,17 bp (t = 0,1) |
| `cassure_m15` | clôture au-delà du haut/bas de 48 bougies M15, on suit | 3 h | −0,12 → +2,86 bp (t = 1,0) |
| `exces_m5` | bougie M5 > 3 écarts-types, on suit | 15 min | +0,81 → +0,47 bp (t = 0,5) |

Essais hors ligne : signaux, premier tour sans ordre, ouvertures à 0,01 lot avec stop, pas de double ouverture,
reprise après redémarrage, sorties au temps, stop touché, position orpheline fermée, spread trop large, ouverture
sans stop refusée → « ESSAIS OK », y compris dans le bac à sable du lanceur (ici il faut lui laisser lire le dossier
des fuseaux horaires de Linux ; sur le PC Windows l'exemple passe sans cela). Contrôle du texte source : rien d'interdit.

Risque en jeu : démo seulement ; 0,01 lot d'or = 1 once, soit 1 $ par dollar de mouvement ; le témoin coûte environ
0,19 $ de spread par trade, ≈ 18 $ par jour sur un compte démo de 66 674 $.

Demandes d'historique ajoutées : `NAS100+`, `SP500+`, `GER40+`, `XAGUSD` en M1, `NAS100+` M5, XAUUSD H1.
Pas encore fait : la recherche massive de combinaisons (prochain passage). Total des essais inchangé : 263.
