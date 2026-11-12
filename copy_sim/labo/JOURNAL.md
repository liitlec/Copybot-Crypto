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
