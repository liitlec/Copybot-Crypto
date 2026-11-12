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

## Passage 3 — 11/11/2026 (≈ 18 h 12 – 18 h 20 Paris) — premier robot sur la démo MT5

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

Suite : le lanceur a installé la version 1 et démarré le robot à 18 h 16 (Paris), sans refus ni erreur ; premiers trades attendus à la bougie M15 de 18 h 30.

## Passage 4 — 11/11/2026 (≈ 18 h 45 – 19 h Paris) — robot version 2, scalp presque continu

Priorité de Baptiste (`PRIORITES.md`, entrée de 18 h 45, commit d6f3124) : le robot v1 trade trop peu ; il veut au
moins 100 à 200 trades par jour, hypothèses M1, tenues courtes, témoin au hasard à la même cadence, 0,01 lot.

**Premiers résultats réels du robot v1** (18 h 16 → 18 h 43) : 2 ouvertures, 0 refus, spread à l'entrée 0,19-0,20 $
(conforme aux bougies), glissement nul (−0,005 $ en moyenne, donc légèrement favorable). 1 trade fermé : `hasard_m15`
−1,27 $. `elan_m15` vendeur ouvert à 4003,75, à +2,97 $ latent. Deux trades : aucune conclusion possible.

**Robot version 2** (`mt5/robot/`, `VERSION` = 2). XAUUSD, 0,01 lot, 8 hypothèses, une position au plus chacune,
stop chez le courtier, sortie au temps, lecture des bougies toutes les secondes :

| Étiquette | Règle | Tenue | Cadence attendue | Banc D (net/trade, réglage → verdict) |
|---|---|---|---|---|
| `hasard_m1` | pile ou face (témoin, même cadence) | 5 min | ≈ 12 par heure | attendu = −spread (≈ −0,19 $) |
| `elan_m1` | sens des 3 dernières minutes | 5 min | ≈ 12 par heure | élan k3 h3 : −0,55 → −0,51 bp (brut ≈ 0) |
| `retour_m1` | contre la dernière minute | 5 min | ≈ 12 par heure | retour k1 h3 : −0,45 → −0,48 bp (brut ≈ 0) |
| `exces_m1` | bougie M1 > 3 écarts-types, on la contre | 12 min | quelques-uns par jour | +0,03 → −1,01 bp |
| `fcassure_m1` | sortie de la fourchette de 48 min, on la contre | 3 min | ≈ 30-60 par jour | −0,17 → −0,33 bp |
| `exces_m5` | bougie M5 > 3 écarts-types, on la suit | 15 min | quelques-uns par jour | +0,81 → +0,47 bp |
| `cassure_m15` | sortie de la fourchette de 12 h, on la suit | 3 h | rare | −0,12 → +2,86 bp |
| `elan_m15` | sens des 3 dernières heures | 3 h | 8 par jour | +0,42 → +0,17 bp |

Soit ≈ 800 à 900 trades par jour de marché ouvert. Coût attendu si rien n'a d'avantage (ce que dit le banc) :
≈ 0,19 $ × 850 ≈ **160 $ par jour** sur la démo (0,25 % du compte), loin du garde-fou de 5 %.
`hasard_m15` est retiré (remplacé par `hasard_m1`). Au changement de version, la position `elan_m15` de la v1
sera fermée comme « orpheline » par la v2 (la mémoire du robot ne suit pas d'une version à l'autre).
Essais : « ESSAIS OK » dans le bac à sable (signaux des 8 hypothèses, 8 ouvertures avec stop à 0,01 lot, pas de
double ouverture, reprise, sorties à 3 min / 5 min / plus tard, stop touché, orpheline, spread large).

Nouveau : `analyse_robot.py` (tableau par hypothèse : trades, gain moyen en $, erreur type, t ; spread et
glissement à l'entrée). Données reçues pour la recherche massive : `NAS100+`, `SP500+`, `GER40+`, `XAGUSD` en M1
(90 000 bougies chacun), `NAS100+` M5, XAUUSD H1 (26 663). Recherche massive : toujours à faire. Essais : 263.

Suite : v2 installée à 18 h 46 (Paris) sans refus ; orphelines de la v1 fermées (+3,08 $ et −0,11 $). À 18 h 58 : 14 ouvertures, 0 refus, spread moyen 0,199 $, glissement moyen +0,007 $ (max +0,15). Une erreur passagère venue du pont (remplacement de `garde_jour.json` refusé par Windows), le robot a continué ; le message contenait un chemin avec le nom d'utilisateur Windows → à masquer dans la v3.

## Passage 5 — 11/11/2026 (≈ 21 h 10 – 21 h 30 Paris) — résultats du robot, grille de 47 628 combinaisons, robot v3

(Les passages planifiés de 19 h 10 et 20 h 10 n'ont pas abouti : le processus de la session a redémarré. Rien de perdu.)
Registre papier : aucun jour terminé à ajouter. `registre.py` corrigé (positions notées une fois par jour).

**Robot v2 en direct, 18 h 46 → 21 h 03** (0,01 lot, $ par trade après spread ; `analyse_robot.py`) :

| Hypothèse | Trades | Gain moyen | ± 1 erreur type | Total |
|---|---|---|---|---|
| hasard_m1 (témoin) | 27 | −0,66 $ | 0,34 | −17,80 $ |
| elan_m1 | 27 | −0,01 $ | 0,36 | −0,20 $ |
| retour_m1 | 27 | −0,22 $ | 0,35 | −5,86 $ |
| fcassure_m1 | 9 | −0,50 $ | 0,66 | −4,53 $ |
| exces_m1 | 1 (stop) | ≈ −4,10 $ | — | −4,10 $ |
| elan_m15 (v1) | 1 | +3,07 $ | — | +3,07 $ |

99 ouvertures, 0 refus, spread moyen 0,198 $, glissement moyen −0,002 $ (nul). Compte démo 66 674,76 → 66 643,93 $
(−31 $ en ≈ 3 h, conforme au coût attendu). Aucune hypothèse ne se distingue du témoin : les écarts sont de l'ordre
d'une erreur type. Cadence réelle ≈ 10 trades par heure et par hypothèse continue (≈ 700 par jour au total).

**Banc E — grille massive** (`banc_grille.py`). Par fichier : 18 signaux (élan 1 à 60 bougies, cassure de 10 à 240,
excès 2-3-4 écarts-types, écart à la moyenne 20-60-240) × suivre/contrer × 7 tenues (1 à 60 bougies) × 9 filtres
d'heure (tout, 8 tranches de 3 h) × 3 filtres de volatilité = 6 804 combinaisons ; 7 fichiers = **47 628**.
Spread réel payé, réglage 60 % / verdict 40 %, t divisé par √tenue (trades chevauchants), au moins 300 trades.
Référence « hasard » : mêmes entrées, sens tiré à pile ou face, meilleur t de toute la grille (5 tirages).

| Fichier | Spread / mouvement | Positives au réglage | t > 2 au réglage | Meilleur t réglage | Meilleur t du hasard | t > 2 au verdict |
|---|---|---|---|---|---|---|
| XAUUSD M1 | 28 % | 14 % | 0 | 1,48 | 0,9 – 1,2 | 0 |
| XAUUSD M5 | 11 % | 32 % | 13 | 3,25 | 1,5 – 2,3 | 0 |
| XAGUSD M1 | 115 % | 3 % | 0 | 1,47 | 0,1 – 0,5 | 0 |
| NAS100+ M1 | **21 %** | 18 % | 0 | 1,65 | 0,7 – 2,3 | 0 |
| NAS100+ M5 | 10 % | 29 % | 0 | 1,76 | 1,4 – 2,1 | 0 |
| SP500+ M1 | 71 % | 8 % | 0 | 1,65 | 0,3 – 0,6 | 0 |
| GER40+ M1 | 55 % | 5 % | 0 | 1,81 | 0,2 – 0,8 | 0 |

Lecture : **aucune des 47 628 combinaisons ne passe le verdict (t > 2)**. Le Nasdaq (`NAS100+`) est encore moins cher
que l'or à scalper ; l'argent, le S&P et le DAX sont nettement plus chers. Un seul groupe dépasse le hasard au
réglage et forme un petit plateau : **XAUUSD M5, de 12 h à 15 h serveur (11 h – 14 h Paris), contrer un écart de plus
de 2 écarts-types à la moyenne de 20 bougies (ou une cassure de 20 bougies), tenue 15 min** : réglage +2,9 à +3,6 bp
(t = 2,5 à 3,25), verdict +0,4 à +1,3 bp (t = 0,4 à 1,1) → positif mais non prouvé (4 voisins sur 13 à t > 2 ; 6 des
13 restent positifs au verdict). C'est le meilleur candidat du moment, rien de plus.
Non couvert par la grille : stops et objectifs dans la bougie, jour de la semaine, tendance de fond, combinaisons de
deux règles, sens seul (achat/vente : biaisé par la hausse de l'or sur la période).

**Total des essais : 263 + 47 628 = 47 891.**

**Robot version 3** (`VERSION` = 3) : les 8 hypothèses de la v2 sont gardées (aucune n'est encore nettement sous le
témoin : trop peu de trades), plus `ecart_midi_m5` (le candidat de la grille, 12 h – 15 h serveur seulement, tenue
15 min). Les messages d'erreur ne contiennent plus de chemin de fichier. Essais « ESSAIS OK » dans le bac à sable.

## Passage 6 — 11/11/2026 (≈ 22 h 10 – 22 h 25 Paris) — le candidat de midi à l'épreuve

Registre papier : rien à ajouter (premier jour compté le 12/11). Robot v3 en marche depuis 21 h 15, 0 refus, 1 seule
erreur (celle de 18 h 53). Compte démo 66 672,88 $ (départ 66 674,76 $).

**Robot en direct, cumul 18 h 16 → 22 h 07** (0,01 lot, $ par trade après spread) :

| Hypothèse | Trades | Gain moyen | ± 1 erreur type | Total |
|---|---|---|---|---|
| hasard_m1 (témoin) | 40 | −0,17 $ | 0,29 | −6,76 $ |
| elan_m1 | 40 | −0,03 $ | 0,28 | −1,14 $ |
| retour_m1 | 40 | −0,12 $ | 0,29 | −4,95 $ |
| fcassure_m1 | 11 | −0,03 $ | 0,65 | −0,31 $ |
| elan_m15 | 2 | +4,97 $ | 1,90 | +9,93 $ |
| cassure_m15 | 1 | +6,86 $ | — | +6,86 $ |
| exces_m1 | 1 (stop) | ≈ −4,10 $ | — | −4,10 $ |

141 ouvertures, 0 refus, spread 0,198 $, glissement −0,001 $. Rien ne se distingue du témoin ; les deux règles M15
ont gagné sur 3 trades pris dans le même mouvement de baisse (fermés à chaque changement de version) : aucune preuve.

**Banc F — affinage du candidat « retour de midi » sur l'or M5** (`banc_plateau.py`, 180 combinaisons : longueur
15/20/30 × seuil 1,5/2/2,5 × tenue 2/3/4/6 × 5 fenêtres d'heures ; 5 tranches de temps de ≈ 3 mois).
- Combinaison de départ (20, 2, 3 bougies, 12-15 h serveur) : positive dans les 5 tranches (+0,6 / +4,1 / +3,9 /
  +1,2 / +1,4 bp nets par trade, 225 à 270 trades par tranche).
- Fenêtre 12-14 h serveur (11-13 h Paris) : 67 à 100 % des 36 réglages positifs dans chaque tranche = vrai plateau.
  Toutes heures confondues la même règle perd (6 à 39 % de réglages positifs) ; par tranche de 3 h, seule 12-15 h
  est nettement positive (+2,24 bp), 15-18 h et 06-09 h sont négatives.
- Épreuve glissante (choix sur le passé, verdict sur la tranche suivante, 4 fois) : **865 trades, +2,28 bp net par
  trade, t = +1,91**. Proche du seuil, pas dessus. Réserve : la fenêtre d'heures a été repérée sur tout
  l'échantillon dans le banc E, donc ce verdict n'est pas entièrement « jamais vu ».
- **Contre-épreuve sur une période vraiment neuve** (M15 d'octobre 2024 à août 2025, 3 traductions de la règle,
  6 essais) : 12-15 h serveur → −2,65 bp (t = −2,3, 73 trades), −1,40 bp (t = −1,8), +0,34 bp. **Le candidat ne
  tient pas avant août 2025** en M15. La traduction M5 → M15 n'est pas exacte : j'ai demandé au pont l'or M5 de
  2024 et de janvier-août 2025 pour refaire l'épreuve à l'identique.

Conclusion : candidat **fragile** (≈ +2 bp par trade au mieux, soit ≈ 0,8 $ par trade à 0,01 lot, 4 à 5 trades par
jour). Il reste dans le robot à 0,01 lot, à titre d'essai. À +2 bp × 5 trades par jour, même vrai, cela ferait
≈ 0,1 % par jour à levier 1 : loin de 1 % par jour sans fort levier.

**Total des essais : 47 891 + 180 + 6 = 48 077.**

## Passage 7 — 12/11/2026 (≈ 2 h 15 – 2 h 40 Paris) — régime du candidat, règle d'arrêt, robot v4

(Les passages de 23 h 10, 0 h 10, 1 h 10 n'ont pas abouti : redémarrages de la session. Rattrapés ici.)
Priorités lues (`PRIORITES.md`, entrées de 22 h 35 et 23 h) : une stratégie « du régime actuel » est acceptable si
elle a une règle d'arrêt écrite avant ses premiers trades ; page de suivi à refaire en fin de passage.
Registre papier : aucun jour terminé à ajouter (le 12/11 sera le premier).

**Robot en direct, cumul 11/11 18 h 16 → 12/11 2 h 12** (0,01 lot, $ par trade après spread, sorties au stop comprises) :

| Hypothèse | Trades | dont stops | Gain moyen | ± 1 erreur type | Total |
|---|---|---|---|---|---|
| hasard_m1 (témoin) | 77 | 2 | −0,25 $ | 0,28 | −19,22 $ |
| elan_m1 | 77 | 3 | −0,17 $ | 0,26 | −12,84 $ |
| retour_m1 | 77 | 2 | −0,24 $ | 0,27 | −18,60 $ |
| fcassure_m1 | 25 | 0 | +0,45 $ | 0,42 | +11,12 $ |
| exces_m1 | 5 | 1 | +2,20 $ | 2,44 | +10,99 $ |
| elan_m15 | 3 | 0 | +4,56 $ | 1,17 | +13,69 $ |
| cassure_m15 | 1 | 0 | +6,86 $ | — | +6,86 $ |
| exces_m5 | 1 | 0 | +0,40 $ | — | +0,40 $ |

273 ouvertures, 0 refus, spread moyen 0,207 $, glissement moyen +0,004 $ (pire cas 0,63 $ à la réouverture de
1 h serveur). Le témoin perd 0,25 $ par trade = le spread, comme prévu ; `elan_m1` et `retour_m1` font pareil.
Compte démo : 66 664,40 $ de solde (départ 66 674,76 $). Sept sorties au stop, toutes entre minuit et 1 h 20 (Paris),
autour de la fermeture nocturne de l'or (trous de prix à la réouverture, stops serrés après une heure calme).
→ **Robot v4** : plus d'ouverture de 23 h 50 à 1 h 10 serveur (22 h 50 – 0 h 10 Paris). Rien d'autre ne change.

**Candidat « retour de midi » (ecart_midi_m5) : son régime.** Le terminal n'a l'or en M5 que depuis juin 2025
(rien pour 2024). Sur juin-août 2025 (7 semaines, jamais vues) : −0,93 bp par trade (162 trades, t = −1,0).
Explication probable : la règle gagne quand l'or est agité. Depuis août 2025, par tiers de volatilité (mouvement
M5 moyen sur 24 h) : calme +0,9 bp, moyen +0,2 bp, **agité +5,6 bp (t = 2,9)** ; en juin-août 2025 l'or bougeait
2,5 fois moins (écart-type par trade 6,8 bp contre 16,7). Positif chaque jour de la semaine (+0,3 à +4,7 bp).
Sur 15 mois récents : 1 224 trades, +2,24 bp, 59 % de gagnants, ≈ 3,7 trades par jour. (10 essais de plus.)

**Règle d'arrêt, écrite avant ses premiers trades (11 h le 12/11)** — à 0,01 lot, 1 bp ≈ 0,40 $ :
- attendu au banc : ≈ +0,90 $ par trade, écart-type ≈ 6,70 $, ≈ 4 trades par jour ;
- **arrêt** si, après 60 trades, la moyenne est sous −0,50 $ par trade, ou dès que la perte cumulée atteint 60 $ ;
- **régime** : elle vaut quand le mouvement M5 moyen sur 24 h dépasse ≈ 6 bp (tiers agité) ; sous ≈ 4,8 bp (tiers
  calme) elle ne vaut rien. Valeur actuelle : 5,1 bp (tiers moyen) → attente modeste. Filtre à coder dans le robot ;
- **taille** : on ne monte au-dessus de 0,01 lot que si, après 100 trades en direct, la moyenne est positive avec
  t > 1,5 et que le banc glissant reste positif.

**Total des essais : 48 077 + 10 = 48 087.**
