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

## Passage 8 — 12/11/2026 (≈ 3 h 10 – 3 h 30 Paris) — filtre de régime du candidat, robot v5

Registre papier : rien à ajouter. Robot v4 installé (2 h 45 env.), en marche, 0 refus, aucune nouvelle erreur.
La page de suivi n'a pas pu être publiée au passage 7 (la publication attendait une approbation, personne la nuit).

**Robot en direct, cumul 11/11 18 h 16 → 12/11 3 h 08** : hasard_m1 88 trades −0,22 $ (± 0,26) ; elan_m1 89, −0,07 $
(± 0,24) ; retour_m1 89, −0,40 $ (± 0,25) ; fcassure_m1 28, +0,36 $ (± 0,41) ; exces_m1 5, +2,20 $ ; elan_m15 4,
−0,58 $ (± 5,2) ; cassure_m15 2, −4,58 $ ; exces_m5 1, +0,40 $. Total de mes trades fermés ≈ −52 $ pour 312
ouvertures. Rien ne se distingue du témoin. **Correction** : la « valeur du compte » démo (66 847 $) contient aussi
≈ +226 $ de positions qui ne sont pas les miennes (autres robots de Baptiste sur la même démo) : pour juger mon
robot, lire le total de ses trades, pas le solde du compte.

**Filtre de régime du candidat de midi (4 essais).** Idée du passage 7 mise à l'épreuve sans regarder le futur :
« agité » = mouvement moyen des 24 dernières heures au-dessus de sa médiane des ≈ 60 jours précédents.
Or M5, 12-15 h serveur, règle figée (20, 2, 3 bougies), 5 tranches de 3 mois depuis août 2025 :

| | Trades | Net par trade | t | Par tranche (bp) |
|---|---|---|---|---|
| tous | 1 224 | +2,24 bp | 2,7 | +0,6 / +4,1 / +3,9 / +1,2 / +1,4 |
| **agité** (mesure M5) | 596 | **+4,21 bp** | 3,1 | +2,0 / +5,8 / +6,7 / +5,6 / +0,4 |
| calme (mesure M5) | 548 | +0,65 bp | 0,6 | −1,2 / +1,9 / +0,9 / −1,4 / +2,1 |
| agité (mesure H1, celle du robot) | 574 | +3,80 bp | 2,7 | +1,5 / +5,8 / +6,6 / +3,2 / +1,2 |
| calme (mesure H1) | 650 | +0,87 bp | 1,0 | −0,7 / +2,0 / +1,5 / −0,0 / +1,5 |

Même règle sur `NAS100+` M5 : +1,36 bp (t = 1,4) en agité, −0,15 en calme → pas un candidat. Hors de 12-15 h, le
filtre n'apporte rien sur l'or. Réserve : le filtre vient d'une observation faite sur ce même échantillon, donc t
est flatté ; la vraie épreuve est le direct. **État actuel : calme** (mouvement H1 moyen 12 bp, médiane 19 bp).

**Robot version 5** : le candidat de midi est noté `midi_agite` ou `midi_calme` selon le régime au moment de
l'ouverture (calculé sur 1 500 bougies H1 du courtier) ; il trade dans les deux cas à 0,01 lot pour comparer.
Règles d'arrêt, écrites avant ses premiers trades : `midi_agite` (attendu ≈ +1,5 $ par trade, ≈ 2 par jour agité) :
arrêt si moyenne < −0,50 $ après 60 trades ou perte cumulée de 60 $ ; `midi_calme` (attendu ≈ 0) : coupé si moyenne
négative après 40 trades. Taille > 0,01 lot seulement après 100 trades `midi_agite` à moyenne positive (t > 1,5).
Essais « ESSAIS OK » dans le bac à sable ; avec les vraies bougies H1 la fonction donne bien « calme » aujourd'hui.

**Total des essais : 48 087 + 4 = 48 091.**

## Passage 9 — 12/11/2026 (≈ 4 h 10 – 4 h 25 Paris) — effets d'heure purs : un faux ami à la réouverture

Registre papier : rien à ajouter. Robot v5 installé et en marche (0 refus, aucune nouvelle erreur).
Page de suivi : non publiée (au passage 8 la demande d'approbation est restée sans réponse et la session a
redémarré) ; je ne réessaie plus la nuit, seulement en journée.

**Robot en direct, cumul 11/11 18 h 16 → 12/11 4 h 10** : hasard_m1 101 trades −0,36 $ (± 0,25) ; elan_m1 102,
+0,04 $ (± 0,24) ; retour_m1 102, −0,48 $ (± 0,24) ; fcassure_m1 30, +0,21 $ (± 0,40) ; exces_m1 5, +2,20 $ ;
elan_m15 5, −2,49 $ (± 4,5) ; cassure_m15 2, −4,58 $ ; exces_m5 1. 354 ouvertures, 0 refus, glissement moyen
+0,003 $. Total ≈ −86 $. Toujours rien qui se distingue du témoin (écart elan_m1 − témoin = +0,40 $ ± 0,34).

**Banc G — effet d'heure pur** (acheter à l'ouverture d'une heure, vendre à sa clôture ; 23 heures × 3 fichiers = 69
essais ; première moitié pour repérer, seconde pour juger). Or H1 (4,5 ans) : une seule heure tient, **1 h serveur
(minuit – 1 h Paris), +2,8 bp puis +4,3 bp brut (t = 4,2 puis 3,4)**, confirmée sur le fichier M15. Nasdaq : rien.
Vérification en M5 (12 essais de plus) : tout le gain est dans la **première bougie de 5 minutes après la
réouverture** (+3,3 bp, t = 3,3) et dans le trou de nuit (+3,5 bp, t = 6,8) ; en entrant à 1 h 05, 1 h 10 ou 1 h 15,
il ne reste rien de net (2e moitié : −0,2 à +0,8 bp, t < 0,5). C'est un **artefact du spread** : les bougies sont en
prix vendeur, et à la réouverture le spread réel est large puis se resserre, ce qui fait « monter » le prix vendeur
sans que l'on puisse l'acheter à ce prix (le spread enregistré dans la bougie, 0,5 bp, est faux à cet instant).
Le direct l'a confirmé cette nuit : glissement de 0,63 $ et 7 stops autour de la réouverture.
**Conclusion : pas d'effet d'heure exploitable ; ne jamais croire un gain de backtest situé à la réouverture.**

**Total des essais : 48 091 + 69 + 12 = 48 172.**

## Passage 10 — 12/11/2026 (≈ 5 h 10 – 5 h 20 Paris) — sorties et tendance de fond du candidat de midi

Registre papier : rien à ajouter. Robot v5 en marche, 0 refus, aucune nouvelle erreur. Page de suivi : pas tentée (nuit).

**Robot en direct, cumul → 5 h 07** : hasard_m1 112 trades −0,25 $ (± 0,23) ; elan_m1 113, +0,08 $ (± 0,22) ;
retour_m1 113, −0,49 $ (± 0,22) ; fcassure_m1 30, +0,21 $ (± 0,40) ; exces_m1 6, +2,76 $ (± 2,1) ; elan_m15 5,
−2,49 $ ; cassure_m15 2, −4,58 $ ; exces_m5 1. 388 ouvertures, 0 refus. Total ≈ −74 $. Rien de distinguable du témoin.

**Banc H — sorties et tendance de fond du candidat** (`banc_sorties.py`, 20 essais ; or M5, 12-15 h serveur, depuis
août 2025, 1 224 trades ; objectif et stop simulés dans la bougie, stop compté d'abord en cas de doute) :
- les 18 variantes de sortie sont **toutes positives** (+0,4 à +2,2 bp net par trade) : le candidat ne dépend pas
  d'un réglage de sortie précis (bon signe de plateau) ;
- la **sortie simple au bout de 15 minutes reste la meilleure** (+2,24 bp, 59 % de gagnants, 5 tranches sur 5) ;
  objectif « retour à la moyenne » : pareil (+2,09) ; un stop serré (2 ou 3 écarts-types) enlève 0,3 à 0,5 bp ;
  tenir plus longtemps (30 min, 1 h) dégrade nettement (+1,7 puis +0,4 bp, tranches négatives) ;
- **tendance de fond** (cours contre sa moyenne de 20 h) : dans le sens du fond (acheter un creux quand l'or monte,
  vendre un pic quand il baisse) +3,53 bp sur 370 trades, 5 tranches sur 5 ; contre le fond +1,70 bp sur 850 trades.
Rien à changer dans le robot : il sort déjà au temps (15 min) avec un stop de secours large.
Réserve inchangée : tout cela est mesuré sur le même échantillon de 15 mois ; seul le direct tranchera.

**Total des essais : 48 172 + 20 = 48 192.**

## Passage 11 — 12/11/2026 (≈ 6 h 10 – 6 h 20 Paris) — passage court de nuit

Registre papier : rien à ajouter. Robot v5 en marche, 0 refus, aucune nouvelle erreur. Page de suivi : pas tentée (nuit).
**Robot en direct, cumul → 6 h 08** : hasard_m1 125 trades −0,22 $ (± 0,22) ; elan_m1 125, +0,06 $ (± 0,20) ;
retour_m1 126, −0,47 $ (± 0,21) ; fcassure_m1 32, +0,18 $ (± 0,38) ; exces_m1 6, +2,76 $ (± 2,1) ; elan_m15 5,
−2,49 $ ; cassure_m15 2 ; exces_m5 1. 428 ouvertures, 0 refus. Total ≈ −81 $. Rien de distinguable du témoin.

**La règle du candidat aux autres heures, avec tendance de fond** (or M5 et `NAS100+` M5, 8 tranches de 3 h × 3
variantes × 2 marchés = 48 essais, réglage 60 % → verdict 40 %) : sur l'or, **12-15 h serveur est la seule tranche
positive au réglage et au verdict** (+2,9 → +1,3 bp ; dans le sens du fond +4,5 → +2,0 bp) ; ailleurs les signes
changent entre réglage et verdict. Sur le Nasdaq rien de stable (12-15 h : −0,1 → +1,8 bp). Aucun nouveau candidat.

**Total des essais : 48 192 + 48 = 48 240.**

## Passage 12 — 12/11/2026 (≈ 7 h 10 – 7 h 20 Paris) — passage court : cassure d'ouverture de Wall Street

Registre papier : rien à ajouter. Robot v5 en marche, 0 refus, aucune nouvelle erreur. Page de suivi : pas tentée
(avant 8 h).
**Robot en direct, cumul → 7 h 10** : hasard_m1 137 trades −0,17 $ (± 0,21) ; elan_m1 138, +0,04 $ (± 0,20) ;
retour_m1 138, −0,52 $ (± 0,21) ; fcassure_m1 34, +0,11 $ (± 0,36) ; exces_m1 7, +2,43 $ (± 1,8) ; elan_m15 6,
−4,00 $ (± 3,9) ; cassure_m15 2 ; exces_m5 1. 469 ouvertures, 0 refus. Total ≈ −103 $. `retour_m1` est 0,34 $ sous le
témoin (± 0,30) : pas encore 2 erreurs types, on continue jusqu'à 300 trades.

**Cassure de la première demi-heure de Wall Street** (16 h 30 – 17 h serveur, puis on suit ou on contre la sortie de
fourchette, sortie à 18 h, 20 h ou 22 h 55 ; `NAS100+` et or, 12 essais, deux moitiés de ≈ 8 mois) : rien. Nasdaq
suivi jusqu'à 18 h : +4,8 bp puis −4,1 bp ; toutes les autres variantes à |t| < 1. **Réfuté.**

**Total des essais : 48 240 + 12 = 48 252.**

## Passage 13 — 12/11/2026 (≈ 8 h 12 – 8 h 30 Paris) — portage mesuré, positions multiples examinées

Registre papier : rien à ajouter. Robot v5 en marche, 0 refus, aucune nouvelle erreur.
Priorité lue (`PRIORITES.md`, 8 h 15, commit dcc7bc5) : plusieurs positions par hypothèse autorisées (plafond par
hypothèse dans le code, pas de moyenne à la baisse), plafond du pont bientôt 30 (encore 10 dans `etat.json`).
Nouveau : `mt5/autres/` (historique des autres robots de Baptiste, des données) → à lire au prochain passage.

**Robot en direct, cumul → 8 h 10** : hasard_m1 149 trades −0,18 $ (± 0,21) ; elan_m1 150, +0,10 $ (± 0,20) ;
retour_m1 150, −0,57 $ (± 0,20) ; fcassure_m1 37, +0,13 $ (± 0,33) ; exces_m1 8, +3,23 $ (± 1,7) ; elan_m15 6,
−4,00 $ ; cassure_m15 2 ; exces_m5 1. 510 ouvertures, 0 refus. Total ≈ −102 $. `retour_m1` − témoin = −0,39 $
(± 0,29) ; `elan_m1` − témoin = +0,27 $ (± 0,28) : rien au-delà de 2 erreurs types.

**Positions multiples pour le candidat de midi ? Non, pas utile** (2 essais). Sur 15 mois : premier signal (aucun
dans les 15 minutes précédentes) +2,69 bp, 584 trades, 5 tranches sur 5 positives ; signal répété pendant qu'une
position est déjà ouverte (donc ajout sur une position qui perd) +1,83 bp, 640 trades, une tranche négative. Une
seule position à la fois (ce que fait le robot) : +2,27 bp sur 722 trades. Empiler n'ajoute que du risque (jusqu'à
3 stops d'un coup) pour un gain par trade plus faible → je garde une position à la fois. Pour les règles M1 en
continu, plusieurs positions ne feraient que multiplier le spread payé. Je réutiliserai la permission pour une idée
à plusieurs symboles ou à entrées vraiment indépendantes.

**Banc I — portage sur Hyperliquid** (`banc_portage.py` : acheter au comptant, vendre le perpétuel, encaisser le
financement ; 12 derniers mois, 4 actifs = 4 essais) : BTC +5,8 % par an, ETH +6,4 %, or tokenisé PAXG +7,0 %, SOL
+1,0 % ; par trimestre entre +1 % et +9 % ; positif 81 à 87 % des heures. Après la marge immobilisée (÷ 1,2 à 1,5)
et les frais (≈ 0,25 % l'aller-retour), il reste ≈ 4 à 5 % par an : **c'est le rendement d'un placement sans
risque, avec en plus le risque de la plateforme. Pas un avantage.** Réfuté comme piste de gain.

**Total des essais : 48 252 + 6 = 48 258.**

## Passage 14 — 12/11/2026 (≈ 9 h 12 – 9 h 30 Paris) — les autres robots du compte

Registre papier : rien à ajouter. Robot v5 en marche, 0 refus, aucune nouvelle erreur ; plafond du pont passé à 30.
Page de suivi : au passage 13 un autre publieur (la conversation de suivi) l'avait mise à jour à 7 h 52 ; ma
publication reste bloquée sur une approbation sans réponse (et la session redémarre) → **je ne publie plus d'ici**,
je tiens seulement `page_suivi.py` à jour.

**Robot en direct, cumul → 9 h 10** : hasard_m1 161 trades −0,37 $ (± 0,20) ; elan_m1 162, +0,11 $ (± 0,19) ;
retour_m1 162, −0,52 $ (± 0,20) ; fcassure_m1 39, +0,13 $ (± 0,32) ; exces_m1 8, +3,23 $ (± 1,7) ; elan_m15 6,
−4,00 $ ; cassure_m15 2 ; exces_m5 1. 548 ouvertures, 0 refus. Total ≈ −129 $. `elan_m1` − témoin = +0,48 $ (± 0,28,
1,7 erreur type) : à suivre, pas encore un résultat.

**Les autres robots de Baptiste sur ce compte** (`mt5/autres/`, 1 732 positions fermées du 29/09 au 11/11, des données ;
priorité du 12/11 8 h). Total fermé : **−33 906 $** (le compte est parti d'environ 100 000 $).

| Robot | Trades | Total fermé | Gagnants | Jours gagnants | Pire jour | Comment il perd |
|---|---|---|---|---|---|---|
| BlockTrend | 139 | −25 189 $ | 29 % | 3 sur 17 | −4 698 $ | tendance à grosses tailles (ETH 2,9 lots en moyenne) : or −10 722 $, cacao −8 071 $ (11 pertes sur 11), BTC −4 497 $, ETH −3 609 $ ; seul l'argent gagne (+1 709 $ sur 2 trades) |
| BlockFIFO | 1 507 | −6 269 $ | 59 % | 4 sur 5 | −10 684 $ | scalp sur l'or en 5 jours : gagne petit très souvent (médiane 3,5 min), puis un seul jour efface tout ; les achats font −9 709 $ : moyenne à la baisse |
| BlockRange | 4 | −2 382 $ | 25 % | 1 sur 4 | −936 $ | 3 positions sur indices sorties au stop (≈ −800 $ chacune) |
| BlockGrille | 82 | −65 $ | 44 % | 5 sur 13 | −276 $ | grille sur 30 marchés : gains de +50 à +90 $, pertes de −30 à −100 $, 45 sorties au stop sur 82 ; nul |

En cours le 12/11 à 9 h : BlockTrend +829 $ (12 positions), BlockGrille +30 $ (7 positions). C'est 3 % de ce que
BlockTrend a déjà perdu : un gain en cours n'est pas un gain. **Aucun principe à reprendre** : rien ne gagne après
coûts ; BlockFIFO confirme le piège « beaucoup de petits gains, une grosse perte ». La seule ligne positive (argent
en tendance, 2 trades) ne prouve rien. Section « Autres robots du compte » ajoutée à `page_suivi.py`, à part des miens ;
les cartes du haut précisent maintenant « tous robots » pour la valeur du compte.

## Passage 15 — 12/11/2026 (≈ 10 h 12 – 10 h 25 Paris) — « prendre ce qu'il y a de bon chez les autres robots »

Priorité lue (`PRIORITES.md`, 9 h 20, commit 0e4b11c). Registre papier : rien à ajouter. Robot v5 en marche, 0 refus.
**Robot en direct, cumul → 10 h 07** : hasard_m1 172 trades −0,30 $ (± 0,20) ; elan_m1 173, +0,20 $ (± 0,19) ;
retour_m1 173, −0,57 $ (± 0,20) ; fcassure_m1 48, −0,04 $ (± 0,31) ; exces_m1 8, +3,23 $ (± 1,7) ; elan_m15 7,
−1,00 $ ; cassure_m15 2 ; exces_m5 1. 591 ouvertures, 0 refus. Total ≈ −110 $. `elan_m1` − témoin = +0,50 $
(± 0,28, 1,8 erreur type) ; `retour_m1` − témoin = −0,27 $ (± 0,28).

**Les sous-ensembles gagnants des autres robots, vérifiés** (groupes d'au moins 5 trades) :
- BlockFIFO, panier vendeur sur l'or : 661 trades, +3 439 $ (59 % de gagnants). Mais c'est le jumeau du panier
  acheteur (846 trades, −9 709 $) : même mécanique des deux côtés (tailles qui montent de 0,02 à 0,06 lot quand la
  position perd : 0,02 lot → −1,2 $ par trade, 0,06 lot → −25 $), 5 jours seulement, et l'or a baissé cette
  semaine-là. Le côté vendeur a gagné parce qu'il n'a pas rencontré son mauvais jour ; le côté acheteur l'a
  rencontré le 02/10 (−10 684 $). **Écarté : c'est le sens du marché sur 5 jours, pas une règle.**
- BlockTrend, ventes d'ETH : 21 trades, +2 332 $ (t ≈ 1 à 1,6) ; l'ETH a baissé en octobre. Ventes de BTC +176 $,
  ventes d'or −204 $. Achats US2000 de BlockGrille : 6 trades, +328 $. Trop peu et expliqué par la direction.
- **Principe testé sur 20 ans, coûts CFD compris : « suivre la tendance seulement à la vente »** (9 essais,
  `banc_tendance`) : depuis 2016, −3,9 % par an (Sharpe −0,67), négatif dans chaque classe (devises −1,6 %,
  indices −1,2 %, métaux −0,7 %, crypto −0,3 %) ; ETH seul −3,6 % par an, BTC −3,2 %, or −4,4 %, argent −7,7 %.
  L'achat seul fait +2,1 %. **Réfuté** : les baisses sont courtes et violentes, la vente paie le financement
  et se fait reprendre dans les rebonds.
Rien de repris dans mon robot. Le gain en cours de BlockTrend vient de 6 ventes d'or empilées : c'est une
exposition, pas une preuve.

**Total des essais : 48 258 + 9 = 48 267.**

## Passage 16 — 12/11/2026 (≈ 11 h 12 – 11 h 20 Paris) — passage court, direct contre banc

Priorité lue (`PRIORITES.md`, 10 h 45) : combiner filtres et stratégies quand il y a quelques centaines de trades par
hypothèse ; mélange fixé avant d'être jugé, jugé sur les trades suivants ; pas de mélange de pièces sans avantage.
Registre papier : rien à ajouter. Robot v5 en marche, 0 refus (deux redémarrages du robot vers 8 h 04 et 8 h 13,
sans erreur notée : sans doute le PC). Fenêtre du candidat de midi ouverte depuis 11 h : pas encore de trade.

**Robot en direct, cumul → 11 h 08** : hasard_m1 185 trades −0,25 $ (± 0,20) ; elan_m1 186, +0,13 $ (± 0,19) ;
retour_m1 186, −0,55 $ (± 0,20) ; fcassure_m1 51, −0,02 $ (± 0,30) ; exces_m1 8, +3,23 $ (± 1,7) ; elan_m15 7,
−1,00 $ ; cassure_m15 3, +4,03 $ (± 10,8) ; exces_m5 1. 633 ouvertures, 0 refus. Total ≈ −94 $.

**Direct contre banc** (mêmes règles, bougies M1 du courtier, 3 mois, ≈ 18 000 trades chacune, 0,01 lot) :
`elan_m1` −0,19 $ par trade (± 0,02), `retour_m1` −0,14 $ (± 0,02), soit le spread et rien d'autre. Le direct
(+0,13 $ et −0,55 $, ± 0,20) est à moins de 2 erreurs types de ces valeurs : les écarts actuels entre les deux règles
sont du bruit, et il n'y a pas de matière à combiner de ce côté. Elles continuent jusqu'à 300 trades (règle fixée),
puis seront coupées si elles restent dans la marge du témoin.

**Mélange fixé d'avance** (compte pour 1 essai, jugé seulement sur les trades à venir) : candidat de midi × or agité
× sens de la tendance de 20 h. Banc : agité +3,8 bp, sens du fond +3,5 bp. À étiqueter dans le robot (v6) après la
fenêtre de midi, pour ne pas fermer des positions en cours.

**Total des essais : 48 267 + 2 + 1 = 48 270.**

## Passage 17 — 12/11/2026 (≈ 12 h 13 – 12 h 30 Paris) — elan_m1 et exces_m1 découpés par régime

Priorité lue (`PRIORITES.md`, 12 h 10) : dire dans quelles conditions `elan_m1` et `exces_m1` gagnent.
Registre papier : rien à ajouter. Robot v5 en marche, 0 refus. Candidat de midi : fenêtre ouverte, aucun signal encore.
**Robot en direct, cumul → 12 h 10** : hasard_m1 197 trades −0,28 $ (± 0,19) ; elan_m1 198, +0,11 $ (± 0,19) ;
retour_m1 198, −0,51 $ (± 0,19) ; fcassure_m1 58, −0,09 $ (± 0,26) ; exces_m1 8, +3,23 $ (± 1,7) ; elan_m15 7 ;
cassure_m15 3 ; exces_m5 1. 676 ouvertures, 0 refus. Total ≈ −110 $.

**Banc J — découpes** (`banc_decoupes.py`, or M1 du courtier, 12/08 → 11/11, spread réel, $ par trade à 0,01 lot ;
92 cases = 92 essais ; une case ne compte que si elle gagne dans les deux moitiés de la période).

`elan_m1` (17 991 trades) : net −0,19 $ (± 0,02), brut −0,00 $.
| Découpe | Résultat net par trade |
|---|---|
| 14 semaines | de −0,33 à −0,05 $ : **aucune semaine positive** |
| 23 heures de Paris | de −0,38 à +0,01 $ : une seule à zéro (10 h, +0,01 ± 0,09) |
| agitation sur 1 h : calme / moyen / agité | −0,18 / −0,16 / −0,22 $ |
| agitation sur 1 jour : calme / moyen / agité | −0,22 / −0,18 / −0,17 $ |
| dans le sens de la tendance de 20 h / contre | −0,16 / −0,22 $ (brut +0,03 / −0,03) |
→ **Aucune condition où `elan_m1` gagne.** Avant spread il fait zéro partout ; le léger mieux dans le sens du fond
(+0,03 $ brut) est six fois plus petit que le spread. Son +0,11 $ en direct sur 198 trades est du hasard.

`exces_m1` (922 trades) : net −0,15 $ (± 0,23), brut +0,04 $.
| Découpe | Résultat net par trade |
|---|---|
| 14 semaines | de −1,39 à +1,44 $, 5 positives sur 14 |
| 17 heures avec assez de trades | 7 positives ; meilleures : 15 h +2,22 $ (± 1,48, 52 trades), 19 h +1,86 $ (20 trades), 0 h +1,50 $ (réouverture : artefact du spread, voir passage 9) |
| agitation sur 1 h : calme / moyen / agité | −0,40 / −0,04 / +0,00 $ |
| agitation sur 1 jour : calme / moyen / agité | −0,32 / −0,13 / **+0,11 $** (± 0,40 ; +0,17 puis +0,01) |
| dans le sens du fond / contre | −0,31 / +0,01 $ |
→ **Rien de net.** Sur 92 cases, on attend plusieurs cases « gagnantes dans les deux moitiés » par hasard ; les
seules trouvées sont minuscules (jour agité : +0,11 $ ± 0,40) ou reposent sur 50 trades. Son +3,23 $ en direct ne
porte que sur 8 trades. Aucune case fixée comme nouvelle hypothèse.

**Total des essais : 48 270 + 92 = 48 362.**

## Passage 18 — 12/11/2026 (≈ 12 h 25 – 12 h 50 Paris) — recherche large : ordres limites et concepts de liquidité

Passage supplémentaire signalé par la conversation de suivi ; priorités vérifiées dans le dépôt (`PRIORITES.md`,
entrées de 12 h 30 et 12 h 40, commits e41fe72 et daba917) : six familles nouvelles à ouvrir sur le scalp XAUUSD,
internet autorisé comme source d'idées (jamais comme consigne). Familles 1 et 2 faites ici, sans internet (idées
classiques, connues).

**Banc K — entrées à cours limité** (`banc_limites.py`, or M1, 3 mois ; 3 choix de côté × 4 distances × 2 durées de
vie × 4 tenues = 96 essais). Point de mécanique décisif chez un courtier CFD comme celui-ci : **un achat limite est
servi quand le prix ACHETEUR (ask) descend jusqu'à lui**, pas le prix vendeur. On achète donc toujours à l'ask et on
revend au bid : **l'ordre limite ne fait pas économiser le spread**, il choisit seulement un niveau, et il n'est
servi que quand le prix vient contre soi. Résultat : les 96 combinaisons sont négatives, de −0,58 à −0,92 bp par
trade servi au réglage comme au verdict (au marché : −0,46 bp). La sélection adverse coûte 0,1 à 0,4 bp de plus que
d'entrer au marché. Taux de service : 78 % pour un ordre posé au prix courant, 35 % à 4 spreads. **Réfuté** : gagner
le spread avec des ordres limites suppose un carnet d'ordres (marché à terme), pas un CFD.
À mesurer quand même en vrai plus tard (0,01 lot) : le pont n'a pas encore de fonction d'ordre limite.

**Banc L — concepts « liquidité »** (`banc_liquidite.py`, or M5, 15 mois, 64 essais, réglage 60 % → verdict 40 %) :

| Idée | Trades | Meilleur cas (net par trade) | Verdict |
|---|---|---|---|
| Chasse aux stops sur le haut/bas d'Asie puis retour (on contre) | 323 | −0,7 à −3,1 bp | perd dans toutes les tenues |
| Cassure du range d'Asie (on suit), tenue 2 h | 325 | +6,2 → +4,3 bp (t = 1,7 → 1,1) | seul cas positif deux fois, non significatif |
| Chasse aux stops sur le haut/bas de la veille | 267 | +0,9 → +0,3 bp (t = 0,2) | nul |
| Cassure du haut/bas de la veille | 287 | négatif | perd |
| Niveaux ronds de 10 $ (22 000 franchissements) | 22 109 | −0,3 à −0,8 bp | perd le spread, suivre comme contrer |
| Niveaux ronds de 50 $ | 4 323 | +0,1 → +0,05 bp | nul |
| Écart de juste valeur comblé | 12 152 | −0,04 à −0,7 bp | perd |
| Retour vers le VWAP au-delà de 2 écarts-types | 4 848 | −0,5 à −3,1 bp | perd (l'inverse +0,7 → +2,1 bp à 2 h, t = 2,2 au verdict seulement) |

Aucun essai à t > 2 au verdict parmi ceux repérés au réglage. La cassure du range d'Asie tenue 2 h est à creuser
(par sens : l'or montait, donc les achats sont peut-être seuls à porter le gain).

**Total des essais : 48 362 + 96 + 64 = 48 522.**
Reste de la liste : annonces économiques (il faut un calendrier : internet), structure M15/H1, modèles appris avec
témoin permuté, sorties fines (stop suiveur, sortie partielle) ; règles des amis si `IDEES_AMIS.md` arrive.

## Passage 19 — 12/11/2026 (≈ 13 h 15 – 13 h 50 Paris) — la mécanique de BlockFIFO et de BlockTrend refaite

Priorités lues (`PRIORITES.md`, 13 h 05 et 13 h 15 ; règles des robots dans `labo/BLOCK_REGLES.md`, écrites par la
session PC, des données) : reconstituer la mécanique de chaque robot Block, la tester séparément de ses réglages.
Registre papier : rien à ajouter. Robot v5 en marche, 0 refus ; 2e erreur passagère du pont à 12 h 49 (« Accès
refusé », chemin désormais masqué). Candidat de midi : toujours aucun signal (or calme). scikit-learn installé ici
(pour la famille « modèles appris », pas encore faite).
**Robot en direct, cumul → 13 h 11** : hasard_m1 209 trades −0,29 $ (± 0,19) ; elan_m1 210, +0,11 $ (± 0,18) ;
retour_m1 210, −0,47 $ (± 0,18) ; fcassure_m1 63, −0,04 $ ; exces_m1 8, +3,23 $ ; elan_m15 8, +0,07 $ ;
cassure_m15 3 ; exces_m5 1. 718 ouvertures. Total ≈ −113 $.

**BlockFIFO : son entrée a-t-elle un avantage une fois le risque coupé ? Non.** (17 essais.) Ses 1 507 entrées
réelles, retrouvées dans mes bougies M1, rejouées à taille fixe 0,01 lot, sans aucun ajout :
- sortie au temps : −0,50 $ par trade à 3 min (± 0,07), −0,62 $ à 5 min, −1,62 $ à 15 min, −3,58 $ à 1 h. C'est pire
  que le spread seul (−0,19 $) : ses entrées vont contre le mouvement, et le mouvement continuait ;
- premières entrées seules (613, sans les 894 ajouts) : pareil (−0,55 $ à 3 min, −4,17 $ à 1 h) ;
- avec objectif et stop durs (1,5 à 5 $ / 3 à 6 $) : −0,58 à −0,91 $ par trade, 37 à 71 % de gagnants.
Dans le réel, les premières entrées ont fait −566 $ et les ajouts −5 774 $. **Rien à sauver : ni l'entrée ni la
grille.** (5 jours seulement, mais 1 507 trades et un écart net au spread.)

**BlockTrend : la mécanique tient sur l'or récent, mais c'est une loterie** (`banc_blocktrend.py`, 10 essais ; or et
Nasdaq M5, 15 mois ; sens = cours contre l'EMA de 2 jours, entrées aux 7 heures fixes, pyramide dans le sens du gain
à chaque pas, sortie de tout le panier sur recul depuis le meilleur prix ; 1 R = perte d'une position au stop initial).

| Variante | Paniers | Total | Moyenne | Gagnants | Pire creux | Par tranche de 3 mois |
|---|---|---|---|---|---|---|
| Or, réglage serré (pas 0,25, stop 0,667 ATR jour) | 269 | **+166 R** | +0,62 R (t = 2,2) | 22 % | −27 R | +57 / +54 / +30 / +18 / +8 |
| Or, serré, pyramide limitée à 3 positions | 269 | +102 R | +0,38 R (t = 2,2) | 28 % | −18 R | +36 / +42 / +8 / +16 / 0 |
| Or, serré, sans pyramide | 269 | +33 R | +0,12 R (t = 1,7) | 39 % | −10 R | +11 / +14 / +4 / +7 / −2 |
| Or, très large (pas 0,5, stop 1,5 ATR) | 78 | +40 R | +0,51 R (t = 0,9) | 24 % | −22 R | +8 / +41 / −5 / +1 / −4 |
| Nasdaq, serré | 260 | +5 R | +0,02 R (t = 0,1) | 19 % | −52 R | −4 / −22 / +10 / −6 / +27 |
| Nasdaq, serré, sans pyramide | 260 | +14 R | +0,05 R (t = 0,9) | 41 % | −10 R | |

Lecture honnête :
- sur l'or, achats (+105 R) et ventes (+61 R) gagnent, 5 tranches sur 5 positives, 9 mois sur 15 ; **mais** 75 % du
  gain vient de 5 paniers sur 269 (+43, +23, +23, +18, +16 R), le gain baisse de tranche en tranche (+57 → +8 R),
  et sur le Nasdaq la même mécanique fait zéro avec un creux de −52 R. Le t = 2,2 est flatté par ces queues épaisses ;
- la simulation colle au réel : du 05/10 au 16/10 elle enchaîne 10 paniers perdants (≈ −1 R chacun) comme le vrai
  robot, puis prend une vente à +9,9 R le 19/10 que le vrai robot n'a pas prise (aucun trade d'or après le 20/10) ;
- **pourquoi BlockTrend a perdu 25 189 $** : (1) la taille : 0,53 % × 1,5 du solde par panier et **trois paniers par
  signal**, soit ≈ 2,4 % du compte risqué à chaque signal sur l'or ; dix signaux perdants de suite = −24 % ;
  (2) les marchés : cacao (11 pertes sur 11, −8 071 $), BTC et ETH n'ont aucune preuve derrière eux (sur le Nasdaq la
  mécanique ne vaut rien) ; (3) la période : octobre 2026 a été haché sur l'or (11 paniers, +0,3 R en simulation).
- la pyramide est ce qui fait le gain (+166 R contre +33 R sans) et aussi le creux (−27 R contre −10 R).
C'est du suivi de tendance (tenue : heures à jours), pas du scalp, et cela dépend d'un or qui fait de grands
mouvements : stratégie de régime. **Candidat sérieux n° 2**, à mettre en essai sur la démo à 0,01 lot dans la version
« pyramide de 3 au plus » (creux plus petit), avec règle d'arrêt écrite avant (prochain passage).
Non couvert : swap de quelques jours, trous de réouverture sur le stop, autres marchés du robot (argent, BTC, ETH,
cacao : pas de bougies demandées), BlockGrille / BlockRange / BlockFinMois (règles lues, pas encore refaites).

**Total des essais : 48 522 + 17 + 10 = 48 549.**

## Passage 20 — 12/11/2026 (≈ 14 h 15 – 14 h 50 Paris) — robot v6 : la mécanique de BlockTrend en essai

Registre papier : rien à ajouter. Robot v5 en marche, 0 refus. Premier trade du candidat de midi : `midi_agite`
−0,06 $ (1 trade : l'or est repassé « agité » en fin de matinée).
**Robot en direct, cumul → 14 h 14** : hasard_m1 222 trades −0,18 $ (± 0,19) ; elan_m1 223, +0,07 $ (± 0,18) ;
retour_m1 223, −0,44 $ (± 0,18) ; fcassure_m1 67, −0,07 $ ; exces_m1 10, +2,95 $ (± 1,5) ; elan_m15 8 ;
cassure_m15 3 ; exces_m5 1 ; midi_agite 1. 765 ouvertures, 0 refus. Total ≈ −85 $.

**Robot version 6** (`mt5/robot/` : `robot.py`, nouveau `bt_or.py`, `essais_robot.py`, `VERSION` = 6) :
- **`bt_or`** : la mécanique de BlockTrend sur l'or, réglage serré, **3 positions au plus par panier**, 0,01 lot par
  position, un panier par côté. Sens = clôture M5 contre son EMA de 2 jours ; entrée à la clôture des bougies M5 de
  03:05, 08:00, 08:30, 12:00, 15:45, 16:00, 16:30 (serveur) ; ajout dans le sens du gain à chaque pas de 0,25 ATR jour
  (sauté si la clôture est déjà à plus d'un demi-pas au-delà) ; sortie de tout le panier sur un recul de 0,667 ATR
  depuis le meilleur prix (tenu par le robot à chaque seconde) ; stop de secours chez le courtier 25 % plus loin,
  remonté à chaque bougie M5. Étiquettes `bt_or_1`, `bt_or_2`, `bt_or_3`.
- **Règle d'arrêt écrite avant le premier trade** : arrêt à **−20 R cumulés** (le pire creux du banc sur 15 mois est
  −18 R), ou si la moyenne est sous −0,3 R après 40 paniers. 1 R = 0,667 × ATR jour × 1 once, soit ≈ 40 à 60 $ à
  0,01 lot ; −20 R ≈ −1 000 $ sur la démo. Attendu au banc : +0,38 R par panier, 28 % de gagnants, donc de longues
  séries de pertes d'environ 1 R sont **normales** (les 2 derniers mois : 40 paniers, −7,5 R).
- Vérification : le module du robot rejoué sur les 12 000 dernières bougies M5 réelles (`rejeu_bt.py`) prend
  exactement les mêmes 40 paniers que le banc (−12,1 R contre −7,5 R : le rejeu sort au pire prix de la bougie).
- Candidat de midi : étiquette complétée par le sens de la tendance de 20 h (`midi_agite_f`, `_c`, `midi_calme_f`,
  `_c`) : le mélange fixé au passage 16 (agité × sens du fond = `midi_agite_f`) est jugé sur les trades à venir.
- Essais « ESSAIS OK » dans le bac à sable (faux pont à prix pilotés : entrée aux heures fixes seulement, spread,
  achat/vente selon l'EMA, stop de secours, ajout au pas, niveau sauté, 3 positions au plus, stop remonté, sortie sur
  recul, reprise après redémarrage, stop touché chez le courtier, règle d'arrêt, positions du panier non traitées
  comme orphelines).
Limites connues : le cumul en R repart de zéro à chaque nouvelle version du robot (le suivre par les notes « sortie
panier » du journal) ; un changement de version ferme les paniers ouverts.
Positions multiples : c'est le premier usage de la permission du 12/11 8 h 15 (pyramide dans le sens du gain, jamais
contre ; perte maximale d'un panier ≈ −1,6 R si les 3 positions sont stoppées au plus mauvais moment).

**Total des essais : 48 549 (inchangé).**

## Passage 21 — 12/11/2026 (commencé 15 h 15, repris 17 h 15 – 17 h 35 Paris après un redémarrage) — modèles appris, « 1 % par jour »

Passages de 16 h 10 et 17 h 10 rattrapés ici (limite d'usage atteinte à 15 h 10, puis redémarrage de la session).
Priorités lues (`PRIORITES.md`, 16 h 40 et 16 h 55) : rythme toutes les 2 heures, sous-agents autorisés (pas utilisés
ici), objectif de Baptiste « environ 1 % par jour en moyenne », stratégies à critères multiples, et pour chaque
candidat le risque chiffré de le pousser vers 1 % par jour. Registre papier : rien à ajouter.

**Robot v6 en direct** (installé à 14 h 19, 0 refus, 3 erreurs passagères du pont en tout) — cumul → 17 h 11 :
hasard_m1 257 trades −0,29 $ (± 0,21) ; elan_m1 259, +0,04 $ (± 0,20) ; retour_m1 259, −0,55 $ (± 0,20) ;
fcassure_m1 81, +0,00 $ ; exces_m1 14, +1,27 $ (± 2,1) ; exces_m5 4, +4,16 $ (± 4,8) ; elan_m15 9, +2,56 $ ;
cassure_m15 4 ; midi_agite 1 (−0,06 $). 898 ouvertures, 0 refus. Total ≈ −145 $.
**`bt_or` : premier panier**, vendeur, ouvert à 14 h 50 à 3 895,66 (stop à 55 $), ajouts à 3 869,63 (16 h) et
3 854,03 (16 h 15) pendant la chute de l'or (4 000 → 3 854 dans la journée) ; à 17 h 11 l'or est remonté à 3 875 :
panier à ≈ −6 $, encore ouvert, stop suiveur à 3 909 environ. Exactement le comportement attendu.

**Banc N — modèles appris** (`banc_modele.py`, gradient boosting, 26 variables : rendements de 1 à 240 min,
amplitudes, agitation, écarts aux moyennes, position dans la fourchette, mèches, volume de ticks, spread, heure,
séries, distance aux extrêmes du jour ; or M1, 3 mois ; 4 tours de validation glissante ; 4 essais) :

| Horizon | Prévisions gardées | Trades | Brut | Net | Témoin (cibles mélangées), brut |
|---|---|---|---|---|---|
| 5 min | les 10 % les plus fortes | 4 616 | −0,23 bp | −0,72 bp | −0,08 / +0,13 / +0,11 |
| 5 min | les 2 % les plus fortes | 954 | −0,03 bp | −0,53 bp | +0,51 / +0,09 / +0,53 |
| 15 min | 10 % | 6 283 | −0,75 bp | −1,24 bp | +0,30 / −0,89 / +0,48 |
| 15 min | 2 % | 1 067 | −1,72 bp | −2,22 bp | −0,16 / −1,14 / −0,02 |

Le lien entre prévision et réalité est nul hors échantillon (corrélations de −0,07 à +0,05 selon les tours) : le
modèle ne fait pas mieux que le témoin mélangé. **Réfuté : 26 variables de prix à la fois ne prévoient pas les 5 ou
15 prochaines minutes de l'or mieux que le hasard.**

**Banc O — ce qu'il faudrait pour « 1 % par jour »** (`banc_objectif.py` ; 5 000 années simulées en tirant des blocs
de trades du banc ; hypothèse généreuse : le futur ressemble aux 15 mois du banc, qui ont eux-mêmes été choisis
parmi 48 000 essais).

Mécanique BlockTrend sur l'or (3 positions au plus ; 212 paniers par an, +0,38 R par panier) :
| Risque par R | Par jour en moyenne | Gain médian sur un an | Pire baisse médiane | Chances de perdre 50 % dans l'année |
|---|---|---|---|---|
| 0,25 % | 0,08 % | +21 % | −5 % | 0 % |
| 0,5 % | 0,16 % | +45 % | −9 % | 0 % |
| 1 % | 0,32 % | +103 % | −18 % | 0 % |
| 2 % | 0,64 % | +255 % | −33 % | 6 % |
| **3,1 %** | **1 %** | +463 % | −47 % | **41 %** |

Retour de midi sur l'or (une position à la fois, 570 trades par an, 1 R = 20 bp contre soi) : 1 % par jour demande
3,9 % du compte par R, soit un **levier d'environ 20** ; au banc cela donne −28 % de pire baisse médiane et 2 % de
chances de perdre la moitié, mais ce candidat a échoué sur juin-août 2025 et un écart de 5 % de l'or pendant une
position à levier 20 efface le compte : ces chiffres-là sont le meilleur cas.
Lecture : **si** ces deux avantages sont réels et durent, 0,1 à 0,3 % par jour est atteignable à risque raisonnable
(pire baisse de 5 à 18 %) ; 1 % par jour revient à jouer le compte à pile ou face sur l'année pour BlockTrend. Et si
l'avantage n'existe pas (ce que le direct doit encore dire), plus de taille = plus de pertes, rien d'autre.

**Total des essais : 48 549 + 4 = 48 553.**

Suite du passage 21 (18 h 46 Paris) — information de la conversation de suivi, vérifiée dans le dépôt (commits
5041adc, c2bb1e7) : robot **version 7** publié par elle à la demande de Baptiste, seul changement `ETEINTES =
{"retour_m1"}` (plus d'ouverture de `retour_m1` : −0,55 $ par trade sur 277 trades). Installée à 18 h 46, 0 refus.
**Effet de bord** : le changement de version a fermé comme « orphelines » les 7 positions ouvertes, dont le premier
panier `bt_or` (3 ventes : +22,24 $, −3,79 $, −19,39 $ = **−0,94 $, soit −0,02 R**). Ce panier n'est donc **pas un
résultat de la stratégie** (ni stop ni recul : coupé par la mise à jour) ; à ne pas compter dans sa moyenne.
À corriger : que les paniers survivent à un changement de version (il faut que `pont.positions()` rende l'étiquette
de chaque position, ou un dossier d'état qui ne change pas avec la version : demande côté PC).

## Passage 22 — 12/11/2026 (≈ 19 h 11 – 19 h 40 Paris) — critères multiples, le mélange de Baptiste sur l'historique

Priorité lue (`PRIORITES.md`, 19 h, commit 0e3b7d4) : suivre le mélange `elan_m15` + `cassure_m15` + `exces_m1` +
`exces_m5` + `bt_or`, vérifier sur l'historique que ses membres se compensent, optimisation en avance glissante.
Registre papier : rien à ajouter. Robot **v7** en marche depuis 18 h 46 (0 refus). Mon message d'information à la
conversation de suivi (fermeture du panier par la mise à jour) n'est pas parti : l'envoi demande une approbation
restée sans réponse, puis la session redémarre → je ne l'utilise plus ; l'information est dans AVIS.md.
**Robot en direct, cumul → 19 h 08** : hasard_m1 281 trades −0,39 $ (± 0,20) ; elan_m1 283, +0,03 $ (± 0,20) ;
retour_m1 279, −0,55 $ (éteint) ; fcassure_m1 84, +0,00 $ ; exces_m1 14, +1,27 $ (± 2,1) ; exces_m5 4, +4,16 $ ;
elan_m15 11, +5,37 $ (± 4,6) ; cassure_m15 5, +8,63 $ (± 9,0) ; midi_agite 1 ; `bt_or` : 1 panier coupé par la mise
à jour (+22,24 −3,79 −19,39 = −0,94 $, non compté). 970 ouvertures, 0 refus.

**Banc P — stratégie à critères multiples, fixée d'avance** (`banc_criteres.py`, or M5, 15 mois, 27 essais) : acheter
un repli (écart > 1,5 écart-type) dans une tendance établie, seulement si 7 conditions sont réunies (séance active,
tendance de 20 h, pente de la moyenne, structure M15 ascendante, or agité, spread normal, bougie de confirmation).
| Tenue | Trades (15 mois) | Réglage | Verdict |
|---|---|---|---|
| 15 min | 106 (0,3 par jour) | −0,3 bp (t = −0,2) | +1,9 bp (t = 0,8) |
| 30 min | 102 | −1,9 bp | +1,3 bp (t = 0,4) |
| 60 min | 97 | +0,7 bp | +2,0 bp (t = 0,4) |
| repli seul, aucun critère (15 min) | 11 616 | −0,6 bp | −0,2 bp |
En retirant un critère à la fois, rien ne change nettement (verdicts de −0,2 à +3,3 bp, tous à t < 2) ; seul le
filtre de séance compte un peu. **Les critères font passer de « perd le spread » à « à peu près zéro », pas à un
gain prouvé**, et il ne reste qu'un trade tous les trois jours : impossible à juger vite en direct. Non retenu.

**Banc Q — le mélange de Baptiste sur l'historique** (`banc_melange.py`, or, 06/08/2025 → 11/11/2026, 328 jours,
$ à 0,01 lot par position, une position à la fois comme le robot ; 5 essais) :

| Membre | Trades | $ par trade | Total 15 mois | Jours de tendance ($/jour) | Jours calmes ($/jour) |
|---|---|---|---|---|---|
| elan_m15 | 2 499 | −0,16 | **−398 $** | +10,2 | −12,7 |
| cassure_m15 | 780 | +0,37 | +285 $ (t = 0,4) | +11,4 | −9,7 |
| exces_m5 | 1 339 | +0,25 | +340 $ (t = 0,9) | +4,5 | −2,4 |
| bt_or | 269 paniers | +19,94 | **+5 365 $** (t = 1,8) | +21,6 | +11,1 |
| exces_m1 (3 mois seulement) | 922 | −0,15 | −136 $ | | |
| **Mélange (4 premiers)** | | | +5 592 $ | **+47,8** | **−13,7** |

- **96 % du gain du mélange vient de `bt_or` seul.** `elan_m15` perd sur 15 mois, `cassure_m15` et `exces_m5` sont à
  zéro près, `exces_m1` aussi.
- **Ils ne se compensent pas** : tous gagnent les jours de tendance et perdent les jours calmes (mélange : +48 $ par
  jour de tendance, −14 $ par jour calme). Corrélations quotidiennes faibles (0,0 à 0,35) ; seule `exces_m1` va à
  l'inverse d'`elan_m15` (−0,43), mais les deux valent zéro en moyenne.
- Par tranche de 3 mois le mélange fait +1 606 / +2 834 / +1 226 / +551 / **−624 $** ; pire creux −2 016 $.
- Les +150 $ du direct depuis hier viennent d'une seule journée de forte tendance (l'or a perdu 3 %) : c'est le
  régime, pas une compensation. Rien à optimiser tant que les pièces n'ont pas d'avantage seules ; la seule pièce
  qui en a un (au banc) est `bt_or`.

**Total des essais : 48 553 + 27 + 5 = 48 585.**

## Passage 23 — 12/11/2026 (≈ 22 h 15 – 22 h 45 Paris) — session neuve ; BlockRange refait ; robot v8 (`elan_m1` coupé)

Session neuve (l'ancienne était trop lourde ; passages de 21 h 10 manqués pour limite d'usage, rattrapés ici).
Budget : normal. Registre papier : `donnees.py` + `registre.py` relancés (il faut `mkdir data` dans un clone neuf),
0 ligne ajoutée (la clôture du 12/11 n'est pas encore comptée).
**Robot v7 en direct, cumul → 23 h 08 serveur (21 h 08 UTC)** : hasard_m1 317 trades −0,31 $ (± 0,18) ; elan_m1 319,
−0,03 $ (± 0,18) ; retour_m1 279, −0,55 $ (éteint) ; fcassure_m1 95, +0,10 $ (± 0,25) ; exces_m1 15, +1,38 $
(± 1,9) ; elan_m15 12, +4,95 $ (± 4,2) ; cassure_m15 5, +8,63 $ (± 9,0) ; exces_m5 4, +4,16 $ ; hasard_m15 2 ;
midi_agite 1. 1 056 ouvertures, 0 refus, spread moyen 0,204 $, glissement nul. `bt_or` : aucun panier depuis la v7
(prochaine heure d'entrée : 03:05 serveur).

**Banc R — la mécanique de BlockRange refaite** (`banc_blockrange.py`, clôtures seules, 8 essais ;
`banc_blockrange_ohlc.py`, vraies bougies jour Yahoo, entrée à l'ouverture du lendemain comme le robot, stop dur
2 × ATR 20 j dans la bougie, 3 essais). 5 indices (S&P 500, Nasdaq 100, DAX, Nikkei, FTSE), 2000-2026, coûts : 2 bp
+ financement CFD (taux 3 mois + 2,5 %) par nuit.

| RSI 2 j < | Réglage 2000-2015 | Verdict 2016-2026 | Récent (08/2025 →) |
|---|---|---|---|
| 5 | 235 trades, +27,6 bp net (t = 2,2) | 230, +36,8 bp (t = 2,8) | 37, +51,9 bp |
| **10 (réglage de Baptiste)** | 519, +20,3 bp (t = 2,5) | 454, **+20,0 bp (t = 2,3 ; par semaine 2,1)** | 78, +23,6 bp (t = 1,2) |
| 25 | 1 168, +12,4 bp (t = 2,5) | 970, +17,1 bp (t = 3,3) | 151, +17,9 bp |

- **Premier montage du labo qui passe réglage ET verdict, avec un plateau** (les 11 variantes sont positives sur les
  deux périodes, avec ou sans filtre 200 j, entrée à la clôture ou à l'ouverture suivante). 66 % de gagnants, 3,8
  nuits de tenue, pire trade −5 % (verdict). C'est l'effet connu « acheter le repli court d'un indice en hausse ».
- Témoin (mêmes durées prises au hasard dans les jours au-dessus de la moyenne 200 j) : +9 bp brut, soit ≈ +1 bp
  net : le repli apporte ≈ +16 à +19 bp par trade au-delà de la simple prime des indices.
- Par indice (verdict) : Nikkei +36, Nasdaq +31, S&P +26, DAX +12, **FTSE −8 bp**. Années perdantes : 2018, 2019,
  2022 (−5 à −11 % en somme de trades).
- **Mais c'est petit** : ≈ 45 trades par an sur 5 indices. À 20 % du compte par trade (levier 1 au plus) :
  **+1,6 % par an, pire baisse −6,5 %** ; à 100 % du compte par trade (levier 5 au plus) ≈ +8 % par an pour une pire
  baisse ≈ −30 %. Très loin de 1 % par jour. Le t par semaine (2,1) tient compte du fait que les indices entrent
  souvent ensemble.
- Pourquoi BlockRange a perdu 2 307 $ en 4 trades sur la démo : 4 trades ne disent rien (un trade sur trois perd,
  le pire fait −5 %) ; c'est la taille par trade qui a fait la somme, pas la règle.
- Suite : demandé au pont les bougies D1 de `NAS100+` et `SP500+` (spread et écart avec Yahoo), et les M5 de
  XAGUSD, BTCUSD, ETHUSD (mécanique BlockTrend ailleurs que sur l'or). Mise en essai dans le robot à étudier : la
  position dure plusieurs jours, donc même problème que `bt_or` (un changement de version la ferme).

**Robot version 8** : seul changement `ETEINTES = {"retour_m1", "elan_m1"}`. Règle écrite d'avance (« couper
`elan_m1` à 300 trades s'il reste dans la marge du témoin ») : 319 trades, −0,03 $ (± 0,18) contre témoin −0,31 $
(± 0,18), écart 0,28 ± 0,25 (t ≈ 1,1), et banc de 18 000 trades à −0,19 $ = le spread. Coupé. « ESSAIS OK ».
Vérifié avant de publier : aucun panier `bt_or` ouvert (4 petites positions M1/M15 seront fermées par la mise à
jour, dont un `elan_m15` : ce trade-là sera une sortie « orpheline », à ne pas compter).
Effet : ≈ 40 % de trades en moins (il reste `hasard_m1`, `fcassure_m1`, `exces_*`, `elan_m15`, `cassure_m15`,
`midi_*`, `bt_or`).

**Total des essais : 48 585 + 11 = 48 596.**

## Passage 24 — 12/11/2026 (≈ 22 h 41 – 23 h 15 Paris) — repli d'indices mis sur la démo (robot v9) ; BlockTrend ailleurs

Priorités lues (`PRIORITES.md`, deux entrées de 22 h 40) : rythme toutes les 2 h 30 ; mettre le repli d'indices en
essai sur la démo dès ce passage ; tester la mécanique BlockTrend sur argent, BTC, ETH, indices ; l'amélioration du
rendement de BlockRange (plus d'indices, sorties, taille, filtres, tableau base / améliorée) aux passages suivants.
Robot **v8 installé à 23 h 17 serveur**, 0 refus. Direct inchangé à quelques trades près (hasard_m1 323 trades
−0,31 $ ; fcassure_m1 97, +0,11 $ ; elan_m15 13, +4,46 $ ± 3,9) ; aucun panier `bt_or`.

**Le repli d'indices sur les bougies jour du courtier** (reçues : `nas_d1_5k` depuis 09/2018, `sp_d1_5k` depuis
09/2020 ; même programme que le banc R bis, 6 essais) :
| | RSI 2 j < 5 | **< 10 (règle de base)** | < 25 |
|---|---|---|---|
| `NAS100+` | 36 trades, +72 bp (t = 2,0) | 62 trades, **+25 bp** (t = 0,9), 68 % gagnants, pire −5,1 % | 147, +34 bp (t = 2,0) |
| `SP500+` | 25, +69 bp (t = 2,6) | 54 trades, **+40 bp** (t = 2,4), 80 % gagnants, pire −3,2 % | 108, +12 bp (t = 0,9) |
Spread réel : 0,3 bp (Nasdaq) et 0,5 bp (S&P) : négligeable. Les bougies du courtier confirment Yahoo. Aujourd'hui :
pas de signal (RSI 2 j à 78 et 64).

**Robot version 9** : nouveau module `mt5/robot/repli_ind.py` (étiquette `repli_ind`), sur `NAS100+`, `SP500+`,
`DJ30+`, `GER40+` (pas de FTSE ; un indice absent ou fermé est noté une fois et ignoré).
- Règle = celle du banc, sans réglage ajouté : RSI 2 jours < 10 et clôture au-dessus de la moyenne 200 jours (bougies
  D1 fermées du courtier) → achat dans les 180 premières minutes de la journée suivante dès que le spread est normal
  (≤ 3 bp) ; stop chez le courtier à 2 × ATR 20 jours ; sortie dès qu'une clôture repasse au-dessus de la moyenne
  5 jours, ou après 10 jours ; une position par indice ; pas de rachat le jour d'une sortie.
- Taille : le lot minimal du courtier (refusé si cela dépasse 30 000 $ de marché ; le montant est noté à chaque
  ouverture, je saurai au premier trade ce que vaut un lot minimal).
- **Règle d'arrêt écrite avant le premier trade** : arrêt si la somme des trades passe sous **−1 500 bp**, ou si la
  moyenne est sous **−20 bp après 60 trades** (banc : +20 bp par trade, pires années −500 à −1 100 bp en somme).
  Attendu : ≈ 35 à 40 trades par an sur 4 indices → verdict du direct en mois, pas en jours.
- **Survit aux changements de version** : toute position du robot sur un indice est reprise (note « reprise ») au
  lieu d'être fermée comme orpheline (le compte de jours repart alors de la reprise). Ce n'est pas encore le cas
  de `bt_or`.
- Essais « ESSAIS OK » (signal, fenêtre de 180 min, spread anormal, ouvertures bloquées, stop à 2 ATR, une position
  par indice, reprise après redémarrage, sorties moyenne 5 j / 10 jours / stop, pas de rachat le jour de la sortie,
  indice absent, position reprise et non fermée par le robot complet) ; contrôle du texte du lanceur : rien.
- Vérifié avant de publier : aucun panier `bt_or` ouvert (l'or est en fermeture nocturne ; 2 petites positions,
  dont un `elan_m15`, seront fermées par la mise à jour : à ne pas compter).

**Banc M bis — mécanique BlockTrend sur argent, BTC, ETH** (`banc_blocktrend.py`, bougies M5 du courtier, spread
réel ; 15 essais ; le Nasdaq était déjà à zéro au passage 19) :
| Marché (période) | Serré, 3 positions au plus (= `bt_or`) | Serré, 10 positions | Très large, 10 positions |
|---|---|---|---|
| Argent (08/2025 → 11/2026) | 291 paniers, +0,07 R (t = 0,4) | +0,20 R (t = 0,8), creux −49 R | +1,08 R (t = 1,5), 78 paniers |
| BTC (01 → 11/2026) | 278, +0,06 R (t = 0,4) | +0,10 R (t = 0,4) | +0,09 R (t = 0,2) |
| ETH (01 → 11/2026) | 268, +0,01 R (t = 0,1) | −0,07 R | −0,01 R |
Sur l'argent, presque tout le gain vient d'une seule tranche de 3 mois (+66 R sur +59) ; BTC et ETH : zéro.
**La mécanique ne tient que sur l'or** (et encore à t = 2,2, dans un marché qui a beaucoup tendu) : aucun autre
marché mis en essai. Sans pyramide, elle vaut zéro partout : tout le gain vient des ajouts pendant quelques grands
mouvements.

**Total des essais : 48 596 + 6 + 15 = 48 617.**

## Passage 25 — 13/11/2026 (≈ 7 h Paris) — passage court : pont arrêté depuis 1 h 07, bilan demandé par Baptiste

Passages de 0 h 10, 2 h 40 et 5 h 10 non faits (la session a redémarré plusieurs fois) ; rattrapés ici en un seul.
Aucune nouvelle priorité. Robot **v9 installé le 12/11 à 22 h 44 (Paris)**, 0 refus, aucune note d'erreur de
`repli_ind` (les 4 indices répondent), aucun signal d'achat, aucun panier `bt_or`.
**Le pont n'écrit plus depuis le 13/11 à 1 h 07 (Paris)** (dernier `etat.json` : 0 h 06 UTC) : PC éteint ou en
veille. 3 positions de 0,01 lot étaient ouvertes, chacune avec son stop chez le courtier. Les bougies D1 demandées
(`DJ30+`, `GER40+`, `JPN225+`, `FRA40+`, `EU50+`, XAUUSD) ne sont pas arrivées.
Direct, cumul → 1 h 05 : hasard_m1 338 trades −0,28 $ (± 0,17) ; fcassure_m1 99, +0,12 $ (± 0,24) ; elan_m15 14,
+3,94 $ (± 3,7) ; exces_m1 16, +1,32 $ (± 1,8) ; cassure_m15 5 ; exces_m5 4. 1 086 ouvertures, 0 refus.
Aucun banc lancé (essais : 48 617, inchangé). Reste à faire : amélioration du repli d'indices (PRIORITES 22 h 40).

## Passage 26 — 13/11/2026 (≈ 7 h 41 – 8 h 10 Paris) — comment tirer plus du repli d'indices (banc S)

Aucune nouvelle priorité. **Pont toujours arrêté** (dernier `etat.json` : 13/11 1 h 07 Paris) : rien de neuf en
direct, données D1 demandées non arrivées. Robot v9 inchangé.

**Banc S** (`banc_repli_plus.py`, bougies jour Yahoo 2000-2026, portefeuille simulé jour par jour avec positions
qui se chevauchent, coûts : 2 bp + financement CFD par nuit ; ≈ 70 essais).

1. **Par marché, règle de base, 2016-2026** (bp par trade) : Dow +32 (t = 2,5), Nikkei +36, Nasdaq +31, Russell
   +30, S&P +26, EuroStoxx +23, DAX +12 ; **perdants : CAC −22, FTSE −8** ; **or +10 (t = 0,4), argent −22 : la
   logique ne tient pas sur les métaux.**
2. **Plus d'indices** (4 → 8 : + Nikkei, CAC, EuroStoxx, Russell) : 35 → 65 trades par an, même gain par trade
   (+21 bp, t = 3,3 sur chaque moitié), mais les indices replient ensemble : à 50 % du compte par position, +4,4 %
   → +6,5 % par an et pire baisse −12,5 % → −26,8 %. **Sharpe identique (0,64 contre 0,62) : plus gros, pas meilleur.**
3. **Sorties, durée, stop, seuil** : grille de 54 réglages, **54 sur 54 positifs** en 2016-2026 (Sharpe de 0,18 à
   0,82, médiane 0,49, base 0,62) : la règle est robuste. Mais **le réglage ne rapporte rien** : en avance glissante
   (meilleur réglage du passé, jugé sur les 3 ans suivants, 2010-2026) Sharpe 0,52, exactement celui de la base,
   avec une pire baisse plus forte (−39 % contre −27 %). Ce qui était le mieux avant 2016 (sortie lente, seuil 15)
   est le moins bon après. Seul résultat stable : **garder le stop à 2 ATR** (sans stop : Sharpe 0,45 puis 0,38).
4. **Filtre 100 j au lieu de 200 j** : mieux avant 2016 (0,62), moins bien après (0,43). **Taille au risque**
   (stop = 2 % du compte) : pas mieux (0,52). Rien à retenir.
5. **Tableau base (4 indices du robot, 2016-2026, 35 trades par an, exposé 27 % des jours)** :

| Part du compte par position | Gain par an | Par jour | Pire baisse | Chances de perdre 50 % dans l'année |
|---|---|---|---|---|
| 20 % | +1,8 % | 0,007 % | −5 % | 0 % |
| 50 % | +4,4 % | 0,018 % | −12,5 % | 0 % |
| 100 % | +8,4 % | 0,036 % | −24 % | 0 % |
| 200 % | +15,2 % | 0,07 % | −44 % | 0,1 % |
| 500 % | +22 % | 0,18 % | −83 % | 21 % |
| **2 760 % (ce qu'il faut pour 1 % par jour)** | compte perdu | 1 % « en moyenne » | −100 % | **96 %** |

   Avec 8 indices : 100 % par position → +12 % par an, pire baisse −48 % ; 200 % → +19 %, −77 %.
   **Le plafond réaliste est ≈ +8 à +15 % par an** pour −24 à −44 % de pire baisse ; au-delà le levier détruit le
   gain (à 500 % avec 8 indices : +1,7 % par an). 1 % par jour est hors de portée de cette règle.

Décision : **la règle du robot reste telle quelle** (aucune « version améliorée » ne passe l'avance glissante ; la
seule amélioration honnête est le nombre d'indices, qui augmente gain et risque ensemble). À étudier ensuite :
ajouter Nikkei, EuroStoxx, Russell au robot quand leurs noms chez le courtier seront connus (pas le CAC).
Limite : les indices Yahoo sont au comptant (clôture de bourse), le CFD cote presque 24 h ; vérifié seulement sur
`NAS100+` et `SP500+` (passage 24).

**Total des essais : 48 617 + 70 = 48 687.**

## Passage 27 — 13/11/2026 (≈ 10 h 12 – 10 h 35 Paris) — la mécanique de BlockFinMois refaite (banc T)

Aucune nouvelle priorité. **Pont toujours arrêté** (dernier `etat.json` : 13/11 1 h 07 Paris, soit 9 h) : rien de
neuf en direct, robot v9 inchangé, données D1 demandées non arrivées.

**Banc T** (`banc_finmois.py`, bougies jour Yahoo 2001-2026, 13 essais ; t calculé avec un point par mois car les
marchés entrent tous le même jour ; témoin = la même règle lancée un autre jour du mois).

| Règle | 2001-2015 | 2016-2026 |
|---|---|---|
| **Piste B, 9 indices** : fin de mois, mois négatif, au-dessus de la moyenne 200 j, 10 jours | 315 trades, +27 bp (t = 0,8) | 258 trades, **+125 bp (t = 2,0)**, 68 % gagnants |
| témoin : même règle un autre jour | +19 bp | +13 bp |
| fin de mois sans condition, 5 jours | −2 bp | +33 bp (t = 1,7) |
| mois négatif seul, 10 jours | −50 bp | +80 bp |
| **Piste A, 7 devises** : fin de mois, RSI 2 j < 30, sortie au-dessus de la moyenne 5 j | 345 trades, **+13,6 bp** (t = 1,2), 68 % gagnants | 289 trades, **+12,1 bp** (t = 2,3), 69 % gagnants |
| témoin : même règle un autre jour | +3,7 bp | +0,6 bp |
| devises, RSI 2 j < 10 | +17 bp (t = 1,6) | +11 bp (t = 1,2) |

- **Indices (piste B)** : très bon depuis 2016, **nul avant** (à peine au-dessus du témoin, et « mois négatif seul »
  perdait 50 bp). Ce n'est pas un effet stable sur 25 ans : c'est une règle du régime récent (marchés qui rachètent
  chaque baisse), ≈ 25 trades par an groupés sur 4 à 5 fins de mois. Elle recoupe largement le repli d'indices déjà
  en démo (acheter une baisse dans une tendance haussière).
- **Devises (piste A)** : petit mais **du même signe et de la même taille sur les deux périodes** (+12 à +14 bp par
  trade, ≈ 45 trades par an, 3 à 4 fois le témoin). Réserves : clôtures seules (stop jugé à la clôture), coût
  supposé 2 bp alors que le spread des devises s'élargit en fin de journée, portage ignoré, t modeste (1,2 et 2,3).
  À ≈ +12 bp × 45 trades, cela fait ≈ +5 % par an pour 100 % du compte par position : modeste.
- Décision : rien de publié (pont arrêté, et la prochaine fin de mois est le 30/11). **Avant le 30/11** : vérifier
  la piste A sur les bougies du courtier (spread réel à 21 h serveur le dernier jour du mois), puis l'ajouter au
  robot à taille minimale si elle tient ; la piste B seulement comme essai de régime, avec règle d'arrêt.

**Total des essais : 48 687 + 13 = 48 700.**
