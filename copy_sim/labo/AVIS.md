# Avis pour Baptiste — 23/11/2026, soir (Lot E : vérification de l'étude d'Astra « type de séance sur l'or », PRIORITES 23/11 12 h)

**Réponse courte : les chiffres d'Astra sont exacts, mais aucun de ses signaux ne rapporte quand on les branche sur nos robots. Chaque gain est dans la marge d'une coupure tirée au hasard (meilleur p 0,22, 1,00 après correction). Sur 12,7 ans de H4, le type de journée se devine un tout petit peu mieux que le hasard (AUC 0,55), mais ça ne se transforme pas en argent. Pas de variante `_opt`, robot inchangé.** Banc `banc_lote.py`, contrat figé et poussé avant les résultats (efcbbf1).

**1. Reproduction et heures**

| Contrôle | Résultat |
|---|---|
| Ses scripts, sans modification | Mêmes chiffres : calme 71/229, 28/89, 29/94, 7/19 ; FOMC 0 sur 76 après 13 h, amplitude ×1,62 ; cassure 590 / 242 / 251 / 48 occasions |
| Fuseau de sa source H4 | Heure **serveur STARTRADER − 3 h**, été comme hiver (écart médian 0,2 pb, contre 7 pb ou plus avec un autre décalage) |
| Son « 9 h » | = 12 h serveur = **11 h à Paris** (pas 9 h) |
| Sa 2e source (H1 en UTC) | Décalée d'1 h en hiver par rapport à la première (petit défaut, sans effet sur ses conclusions) |
| « 20 ans » de H4 | Non : vraies bougies 4 h seulement **depuis 06/2013** (avant, une bougie par jour) → 12,7 ans |

**2-3. Ses drapeaux sur nos robots** (or H1 du courtier 08/2022 → 11/2026, 1 106 jours, décision à 11 h Paris ; spread réel + 50 % de glissement ; unités à risque égal ; positions ouvertes avant 11 h gardées)

Drapeaux : FOMC 34 jours, calme 210, cassure 501, indéterminé 464. Bases : `bt_or` seul −5 / +95 u, retour seul −12 / −52, 50/50 −9 / +22 (2022-24 / 2024-26).

| Règle | Jours | Gain 2022-24 / 2024-26 | Coupure au hasard (médiane) | p hasard | Pire baisse (base) | Spread ×3 |
|---|---|---|---|---|---|---|
| `bt_or` seul, coupé les jours FOMC | 34 | +1,8 / −0,7 | −0,5 | 0,38 | −24,8 (−26,1) | +1,2 |
| `bt_or` seul, coupé les jours calmes | 210 | +12,4 / −8,8 | −4,8 | 0,22 | −21,3 (−26,1) | +4,8 |
| `bt_or` seul, coupé les jours de cassure | 501 | −0,6 / −42,7 | −24,2 | 0,89 | −22,1 | −41,4 |
| Retour seul, coupé les jours FOMC | 34 | +1,7 / +2,7 | +2,7 | 0,37 | −66,7 (−73,6) | +5,2 |
| Retour seul, coupé les jours calmes | 210 | −2,3 / +11,6 | +5,7 | 0,37 | −63,8 | +12,8 |
| Retour seul, coupé les jours de cassure | 501 | +10,8 / +20,1 | +22,3 | 0,30 | −45,9 | +39,4 |
| 50/50, retour coupé les jours de cassure | 501 | +5,4 / +10,0 | +11,1 | 0,29 | −15,3 (−13,9) | +19,7 |
| 50/50, les 5 autres règles | 34-501 | toutes < ±7 | — | 0,23-0,89 | — | — |

1. **FOMC** : il a raison, ces jours bougent plus. Mais sur nos robots, ça ne change rien (34 jours, ±2 u).
2. **Calme** : couper `bt_or` les jours calmes aide en 2022-24 (+12) et coûte en 2024-26 (−9), avec p 0,22.
3. **Cassure** : couper la famille retour semble rapporter (+31 u), mais une coupure au hasard du même nombre de jours rapporte presque autant (+22). Ce n'est pas le signal qui aide : la famille retour perd presque tout le temps. Couper `bt_or` ces jours-là coûte −43 u.
4. Semaines perdantes, espérance par semaine et IC : quasi identiques à la base pour les 12 règles (détails dans `donnees/lote_robots.csv`). Après correction de Holm, p = 1,00 partout.

**4. Le test « jour » du lot D refait sur 12,7 ans de H4** (06/2013 → 02/2026, ≈ 3 000 jours prévus hors échantillon ; décisions à 7 h, 11 h et 15 h Paris, les heures du quadrillage H4)

| Décision | Modèle | AUC (IC 95 %) | Gain/risque par an (toujours 1 : 0,33) | Gain 2014-19 / 2020-26 | Placebo p |
|---|---|---|---|---|---|
| 7 h | logistique | **0,56 (0,54-0,58)** | 0,23 | +66 / −100 R | 0,24 |
| 7 h | arbre | 0,53 (0,51-0,55) | 0,45 | +28 / +14 | 0,26 |
| 11 h | logistique | **0,56 (0,54-0,58)** | 0,10 | −13 / −67 | 0,37 |
| 11 h | arbre | 0,55 (0,53-0,57) | 0,37 | +9 / +8 | 0,17 |
| 15 h | logistique | 0,55 (0,53-0,57) | 0,36 | +15 / −1 | 0,04 |
| 15 h | arbre | 0,53 (0,51-0,55) | 0,33 | 0 / +2 | 0,58 |
| **SPA, 6 règles** | | | | | **p = 0,61** |

1. **Avec 3 000 jours, on voit enfin quelque chose** : le type du reste de la journée se devine un peu mieux que pile ou face (AUC 0,55-0,56, borne basse au-dessus de 0,5). Sur 4 ans (lot D), c'était invisible (AUC 0,47-0,52).
2. **Mais c'est trop faible pour payer.** Une seule règle bat son placebo, et sur une seule période (15 h logistique, p 0,04, +15 puis −1 R). Le test SPA dit p 0,61. Il faudrait environ 56 % de bons jours, et une AUC de 0,55 n'y suffit pas.
3. Le `bt_or` rejoué en H4 suit bien le vrai (corrélation 0,88), mais il gagne +19 R en 2022-24 quand le vrai perd −5 R. Le contrat le déclare donc non validé : la colonne argent est indicative.
4. **Le type de journée se retourne un peu, il ne se prolonge pas** : corrélation avec la veille −0,06 (seuil 0,035). Une journée de tendance est plutôt suivie d'une journée moins tendue, pas d'une autre tendance.

**Conclusion** : l'étude d'Astra est propre et reproductible. Mais ce qu'elle détecte (FOMC agités, matins calmes un peu mieux repérés, AUC 0,55) est réel sans être exploitable par nos robots à risque égal. Il n'y a rien à mettre en démo.

# Avis pour Baptiste — 23/11/2026, soir (Lot D, points 6-8 : deviner la JOURNÉE de tendance à 9 h, 11 h, 14 h)

**Réponse courte : non. À 9 h, 11 h ou 14 h, rien de ce qu'on connaît ne dit si la suite de la journée sera en tendance ou en aller-retour (AUC 0,47 à 0,52, alors que 0,50 = pile ou face). Aucune des 6 règles ne bat « toujours 1 » sur les deux périodes. Pas de variante démo.** Banc `banc_lotd_jour.py`, contrat figé et poussé avant les résultats.

**Limite importante** : l'historique intrajour long (Dukascopy, HistData) est **bloqué par le réseau de l'environnement cloud** (connexions refusées). Il faudrait ajouter `datafeed.dukascopy.com` aux domaines autorisés de l'environnement. Le test est donc fait sur l'or H1 du courtier, 08/2022 → 11/2026 (1 106 jours, dont 825 prévus hors échantillon à partir de 09/2023). Pas sur 15-20 ans.

**Ce qu'on connaît à l'heure de décider** : amplitude, sens et efficacité de la séance depuis minuit (Asie et début d'Europe), écart d'ouverture, type des 1 et 5 jours d'avant, compression d'hier, jour de la semaine, annonces (emploi, inflation, Fed), position dans le mois, VIX et GVZ. Deux modèles simples (logistique, arbre à 2 niveaux), recalculés chaque mois. Mise 0/1/2 sur les paniers `bt_or` ouverts après l'heure de décision.

| Décision | Modèle | AUC (IC 95 %) | Gain/risque par an (toujours 1 : 1,58) | Gain contre « toujours 1 » 2023-24 / 2024-26 | Placebo p |
|---|---|---|---|---|---|
| 9 h | logistique | 0,51 (0,47-0,54) | 1,06 | −16 / −44 R | 0,95 |
| 9 h | arbre | 0,52 (0,48-0,56) | 1,49 | −2 / −8 R | 0,54 |
| 11 h | logistique | 0,47 (0,42-0,51) | 1,62 | −4 / +9 R | 0,28 |
| 11 h | arbre | 0,48 (0,44-0,52) | 1,65 | +14 / −6 R | 0,20 |
| 14 h | logistique | 0,52 (0,48-0,56) | 1,52 | −20 / +13 R | 0,75 |
| 14 h | arbre | 0,52 (0,48-0,56) | 1,54 | +4 / −9 R | 0,66 |
| **SPA, 6 règles** | | | | | **p = 0,83** |

**Ce que vaudrait une bonne prévision** (9 h ; mise 2 si « bon jour » annoncé, 0 sinon ; 263 jours avec un panier après 9 h ; « toujours 1 » = +184 R)

| Précision | 50 % | 52 % | 55 % | 60 % | 65 % | 70 % |
|---|---|---|---|---|---|---|
| Gain contre « toujours 1 » | −34 R | −24 R | −1 R | +27 R | +56 R | +86 R |

1. **Il faut au moins 56 % de jours bien devinés pour gagner quelque chose.** Nos modèles font 40 à 55 % sur les jours où ils osent miser 0 ou 2 : c'est pile ou face, voire moins.
2. **Le type de journée ne se prolonge pas.** Corrélation de l'efficacité du jour avec celle de la veille : −0,08 ; avec la moyenne des 5 jours d'avant : −0,06. « Aujourd'hui ressemble à jeudi dernier » n'apporte donc rien. Exemples : 05/11 efficacité 0,27 (aller-retour), 06/11 0,22, 10/11 0,79 (tendance), 11/11 0,50. Les jours que tu cites (19, 20 et 23/11) sont après la fin de nos bougies H1 (11/11).
3. Les étiquettes H1 et M5 sont identiques sur 2025-26, mais c'est la même source chez le courtier : ce contrôle ne prouve rien de plus.

**Point 8, bilan des deux échelles**

| Échelle | Données | Meilleur résultat | Verdict |
|---|---|---|---|
| Heure (Lot B, Astra) | 15 mois M5, 4 ans H1 | « prolongement » +89 R, p 0,13 | rien |
| **Jour (ce lot)** | 4 ans H1 | AUC 0,52, SPA p 0,83 | rien |
| **Mois (ce lot)** | 22 ans journalier | 19 règles sous « toujours 1 », SPA p 1,00 | rien |

**Conclusion franche** : à aucune échelle on ne devine à l'avance si l'or va tendre. Ce qui marche, c'est d'être **toujours en place** avec une règle de tendance qui coupe vite ses pertes et laisse courir ses gains (c'est ce que fait `bt_or`). Le « détecteur » est en fait déjà dans la sortie au recul. Seule piste qui reste : refaire le test du jour sur 15-20 ans d'or M5. Il faut pour ça autoriser `datafeed.dukascopy.com` dans les réglages réseau de l'environnement cloud. Vu les chiffres de 4 ans (AUC 0,5 partout), je n'en attends pas grand-chose.

# Avis pour Baptiste — 23/11/2026, soir (Lot D : détecter le marché à l'échelle du mois, PRIORITES 23/11 11 h 15)

**Réponse courte : non, pas de détecteur. Le mime journalier de `bt_or` ne passe pas la validation (corrélation 0,48 pour un seuil de 0,6, et il gagne en 2022-24 quand le vrai perd). Le reste est donc seulement indicatif. Mais là aussi, aucun des 18 filtres lents ne bat « toujours 1 » sur 20 ans (SPA p = 1,00). Pas de variante `bt_or_filtre_opt`, robot inchangé.** Banc `banc_lotd.py`, contrat figé et poussé avant les résultats (commit 066e561).

Données : GLD journalier 11/2004 → 11/2026 (vrais haut/bas). GC=F ne sert qu'en contrôle : 45 % de bougies plates avant 2008. FRED : GVZ, taux réel 10 ans, dollar. Jugement sur 01/2007 → 11/2026 (239 mois), à risque égal.

**1. Mime journalier contre vrai `bt_or` H1 (08/2022 → 11/2026, R par mois)**

| Mesure | Mime GLD | Vrai `bt_or` | Seuil |
|---|---|---|---|
| Corrélation mensuelle | 0,48 | — | ≥ 0,6 → **raté** |
| 2022-2024 (B1) | +37 R | −1 R | même signe → **raté** |
| 2024-2026 (B2) | +87 R | +154 R | même signe → ok |
| Paniers par mois | 11 | 18 | — |
| Contrôle GC=F | corr. 0,54 avec le vrai, 0,53 avec le mime GLD | | |

Avec une seule bougie par jour, on ne retrouve pas `bt_or`. Son résultat dépend de ce qui se passe à l'intérieur de la journée (5 entrées par jour, stop de 0,67 ATR). Le mime change même beaucoup selon la source (GLD ou GC=F).

**2-3. Filtres lents (indicatif)** — décidés en fin de mois, mise 0/1/2 par tercile du passé. Référence « toujours 1 » : +563 R. Gains et pertes donnés à risque égal contre la référence.

| Filtre | 2007-2016 | 2017-2026 | Placebo p | Vrai `bt_or` 2022-24 / 2024-26 |
|---|---|---|---|---|
| \|momentum\| 12 mois (le meilleur sur 2022-26) | −14 R | −26 R | 0,08 | **+20 / +34 R** |
| \|momentum\| 3 mois | −10 | −27 | 0,24 | −25 / +15 |
| Kaufman 60 j | −28 | −15 | 0,20 | −41 / 0 |
| Momentum 12 mois (avec le sens) | −114 | +39 | 0,15 | −2 / +23 |
| Dollar sur 3 mois | −86 | +5 | 0,07 | −24 / −38 |
| GVZ (niveau / variation) | −119 / 0 | −182 / −253 | 0,93 / 1,00 | — |
| Taux réel sur 3 mois | −228 | −55 | 1,00 | −26 / −1 |
| Résultat récent de `bt_or` (1 mois, 3 mois, courbe) | −206 / −51 / −161 | −57 / −271 / −177 | 0,76-0,92 | toujours négatif |
| Choix en walk-forward | −117 | −103 | 0,79 | −18 / +10 |
| **Test SPA, 19 règles** | | | **p = 1,00** (White 1,00) | |

Les 19 règles font toutes moins bien que « toujours 1 » sur 20 ans, et aussi avec le coût doublé. Le seul filtre qui aidait `bt_or` sur 2022-26 (|momentum| 12 mois) perd dans les deux décennies : c'est le piège d'un historique court.

**4. Échelle de temps**

| Historique | Mois | Régimes de 3 mois ou plus | Écart détectable (rapport gain/risque annuel) |
|---|---|---|---|
| 2007-2026 | 239 | 27 | 0,45 |
| 2022-2026 (4 ans) | 52 | 6 | 0,96 |
| 15 derniers mois | 15 | 2 | 1,79 |

1. **4 ans ne pouvaient rien prouver.** Il y a seulement 6 régimes, et l'écart détectable (0,96) dépasse tout l'avantage de la stratégie (0,71 par an). 15 mois de M5, c'est 2 régimes.
2. **Le mois d'avant ne dit rien du mois suivant.** Sur 20 ans, l'autocorrélation des résultats mensuels est de −0,05, −0,03 et −0,09 (retards 1 à 3), sous le seuil de 0,13. C'est pour ça que tous les filtres « suivre ce qui marche » échouent, à l'heure, au jour et au mois.
3. **Meilleure piste restante** (hors contrat, sur un mime non validé) : sur 20 ans, la tendance de l'or sans filtre gagne dans les deux décennies (+248 / +316 R). Elle perd 5 années sur 20, et seulement 3 % des fenêtres de 2 ans sont négatives. Une période plate comme 2022-24 fait donc partie du jeu normal. Elle ne se prévoit pas, elle se tient : petite mise (1 % par panier au plus, Lot C) et patience. Pour aller plus loin, il faudrait des bougies intrajour longues (or M5/H1 sur 10 ans ou plus), qu'aucune source publique gratuite n'a fournies ici.

# Avis pour Baptiste — 23/11/2026, après-midi (Lot C : « encaisser plus qu'on ne dépose », PRIORITES 23/11 11 h)

**Réponse courte : oui, on peut finir positif en argent encaissé, mais seulement avec une règle qui gagne déjà (la cassure calme d'Astra ou les rebonds d'indices). Les retraits et la martingale ne créent aucun gain : sur un jeu sans avantage, tout finit à zéro ou en perte. Ils changent seulement la forme : plus de chances d'avoir déjà sorti de l'argent, mais plus de ruines. Robot v26 publié : poche virtuelle `encaisse_calme_opt` (aucun ordre).**

Critère : argent net encaissé = retraits − dépôts (recharges comprises), en fois le dépôt (1 = 500 €). Prudent = avantage ÷ 2. B1 = 08/2022-09/2024, B2 = 10/2024-11/2026. Banc `banc_lotc.py`, contrat figé avant les résultats.

**1. Cassure après séance très calme (Astra), rejeu réel, sans retrait**

| Bloc | 1 % par panier | 12 % (chiffre d'Astra) | ×2 après perte, 1 % | ×2 après perte, 12 % |
|---|---|---|---|---|
| 2022-2024 | +0,25 %/sem., pire baisse −25 % | ×0,71, pire baisse −98 % | −0,34 %/sem., −88 % | ruine |
| 2024-2026 | +0,41 %/sem., −12 % | ruine | +0,67 %/sem., −58 % | ruine |

Les +0,64 et +0,81 %/sem. d'Astra à 12 % ne se retrouvent pas : à 12 %, le compte est ruiné.

**2. `bt_or` en % du compte (rejeu réel)** — Astra, pyramide or à 1 % : +0,39 %/sem.

| Risque par panier | 0,5 % | 1 % | 2 % | 3 % |
|---|---|---|---|---|
| 2022-2024 | −0,03 %/sem. (−18 %) | −0,09 % (−34 %) | −0,34 % (−59 %) | −0,73 % (−75 %) |
| 2024-2026 | +0,66 %/sem. (−9 %) | +1,26 % (−17 %) | +2,29 % (−32 %) | +3,11 % (−45 %) |

**3. Martingale + retraits, 24 mois** (Monte-Carlo par semaines, 2 000 parcours ; net en dépôts)

| Montage | Prudent B1 / B2 : net moyen | P(net > 0) | 1 fois sur 10, pire que | Ruines moyennes | Sans avantage : net moyen |
|---|---|---|---|---|---|
| **Calme, 6 %, ×1,5 après perte, retrait au-dessus de 1,5 dépôt, 2 recharges (retenu)** | +1,6 / +1,5 | 59 / 64 % | −2,4 / −2,1 | 2,5 / 2,0 | +0,2 |
| Calme, même chose à mise fixe 6 % (témoin) | +0,2 / +0,4 | 44 / 52 % | −1,8 / −1,4 | 0,5 / 0,2 | −0,7 |
| Calme, mise fixe 12 % | +1,2 / +1,3 | 58 / 63 % | −2,4 / −1,9 | 2,1 / 1,4 | −0,2 |
| Rebonds d'indices, mise fixe 12 %, même retrait (le plus sûr) | +0,3 / +3,2 | 56 / 87 % | −1,0 / −0,2 | 0 / 0,2 | −0,6 |
| `bt_or`, 1 %, même retrait | −0,9 / −0,5 | 0 / 19 % | −1,0 | 0 | −0,9 |
| `bt_or`, 3 %, ×2 après perte | +0,3 / +2,4 | 44 / 64 % | −2,5 / −2,2 | 3,0 | 0,0 |

1. **Les retraits ne changent pas l'espérance.** Sans avantage, le résultat reste nul ou négatif pour toutes les règles. Quand la règle gagne, ils baissent même le total : `bt_or` à 3 % vaut 6,0 dépôts sans retrait, contre 1,2 à 3,7 avec. Ce qu'ils changent, c'est la part déjà en poche si le compte saute.
2. **La martingale n'exploite rien.** Après une perte, le panier suivant n'est pas meilleur (écarts sous 1 écart-type, de signe changeant). Elle joue juste plus gros : le montage retenu fait comme une mise fixe de 12 %.
3. **`bt_or` échoue** : il n'a rien gagné en 2022-2024, et aucune règle de retrait ne rattrape ça.
4. **Point 4 rempli** : 44 combinaisons sont positives en prudent sur les deux blocs, toutes sur la cassure calme ou les rebonds. Mais même la retenue perd de l'argent 4 fois sur 10 en 2 ans, et 1 fois sur 10 elle perd les 3 dépôts (≈ −1 200 €). Sur 6 mois, elle n'est positive que 1 fois sur 3.
5. **Robot v26** : `encaisse_calme_opt` est une poche virtuelle de 500 € qui rejoue chaque panier fermé de `gpt_pyramide_opt` avec ces règles (mise, retraits, recharges) et note l'argent net encaissé. Aucun ordre en plus, hors totaux, arrêt après 3 ruines ou 24 mois. Aucun argent réel sans ton accord sur ton PC.

# Avis pour Baptiste — 23/11/2026, fin de matinée (réponse d'Astra sur la détection de régime, PRIORITES 23/11 10 h 20)

**Réponse courte : aucune des 3 règles d'Astra ne bat le mélange fixe 50/50 selon le contrat. On arrête la recherche du détecteur de régime sur cet historique. Pas de variante `_opt`, robot inchangé (v25).** Le contrat a été figé et poussé avant tout calcul (commit 11f55ce, docstring de `banc_astra.py`).

Or du courtier M5/M15, 08/2025 → 11/2026 (328 jours), spread réel. Familles du labo : tendance (`elan_m15` + `cassure_m15`) et retour (`fcassure_m5` + `contre_exces_m5`), sans la pause au calme. 1 R = budget de risque d'une entrée. 50/50 = moitié du budget à chaque famille. Témoins : 50/50 **−175 R** ; tendance seule **−5 R** ; retour seul −345 R.

| Essai | Ce qui se passe | Gain contre le 50/50 (spread réel / doublé) | Par décision changée | Placebo | Verdict |
|---|---|---|---|---|---|
| 1. Oracle horaire (meilleur choix connu après coup) | Borne haute +4 632 R (+0,71 R par heure) ; les 10 meilleures heures = 4 % | — | — | Heures mélangées au hasard : +4 622 R (même chose) | la borne ne mesure que le bruit |
| 2. Veto de coût (A/c < 4) | Ne se déclenche jamais : l'heure d'or fait en médiane 51 fois le coût (10 % des heures : 32 fois) | 0 / 0 | — | — | ne tient pas (sans objet sur l'or) |
| 3. Prolongement après retournement | Tendance 1 055 h, retour 892 h ; 1er signal vers 12 h (Paris), 13 % des séances après 18 h | **+89 R** / +92 R | +0,054 R (seuil 0,05) | p 0,13 | **indéterminé** (IC 95 % corrigé : borne basse −0,15 R/jour) |
| 4. Tenue du prix après annonce (CPI, emploi) | 24 annonces : 14 « tendance », 0 « retour », 10 sans signal | −9 R | −0,66 R | 34 faux événements : p 0,51 | ne tient pas |
| Test SPA de Hansen (3 règles contre 50/50) | | | | | p = 0,53 |

1. **Oracle horaire** : choisir après coup, chaque heure, la bonne famille rapporterait +4 632 R sur 15 mois. Mais en mélangeant les heures au hasard, on trouve exactement la même chose (+4 622 R). Cette borne ne dit donc rien d'une structure exploitable. Ce contrôle a été ajouté après le premier lancement ; le seuil du contrat (+0,05 R par heure) était trop facile à dépasser. Contrôle sur 4 ans d'or H1 : même tableau (+2 345 R de borne haute, dont +507 en 2022-24 et +1 838 en 2024-26).
2. **Veto de coût** : sur l'or, une heure parcourt toujours bien plus que le coût d'un aller-retour (médiane ×51 ; jamais sous ×4, ni en M5 sur 15 mois, ni en H1 sur 4 ans). Le filtre ne suspend aucune heure ; il serait utile seulement sur un marché beaucoup plus cher à trader.
3. **Prolongement** : c'est le seul qui gagne (+89 R contre le 50/50, +92 R avec un spread doublé, pire baisse −137 R contre −189). Mais il ne bat pas son placebo (p 0,13), l'intervalle de confiance contient 0, et surtout **« tendance seule » fait mieux sans aucun détecteur** (+170 R contre le 50/50). Son gain vient surtout de couper souvent la famille retour, qui perd. Retard en argent : 441 alertes ; +64 R déjà passés au moment de l'alerte contre +58 R encore accessibles. Il arrive donc en moyenne à mi-parcours.
4. **Annonces** : 14 signaux « le prix tient → tendance » ; le trade direct de 15 h 45 à 16 h 30 fait en moyenne −0,005 ATR (7 gagnants sur 14), pas mieux que de faux événements (−0,016 ATR, p 0,51). Il n'y a jamais eu de signal « retour ». Essai exploratoire : trop peu d'événements.
5. **Décision** (règle d'Astra appliquée) : aucun mécanisme ne bat le mélange fixe selon le contrat, donc on arrête la recherche du détecteur sur cet historique. Le résultat utile est ailleurs : sur ces 15 mois, la famille retour (sans la pause au calme) perd −345 R, et c'est elle qu'il faudrait revoir, pas l'aiguillage.

# Avis pour Baptiste — 23/11/2026 (réponse de GPT Astra, tour 2 : ses 6 points testés)

**Réponse courte : GPT a raison sur la taille (1 % par panier au plus, pas 12 %), et le compte cent est faisable. Mais aucune de ses 3 améliorations ne tient : le filtre « séance calme » n'est pas assez net, la diversification n'aide pas, l'interrupteur de pyramide non plus. Robot inchangé (v25).**

**1. Risque par panier — chance de passer à −30 % sous le sommet en 24 mois** (mesuré / prudent / nul ; Monte-Carlo par semaines entières, risque compté avec les 2 renforts, le glissement et les swaps)

| Risque par panier | Or, 4 ans | Or, M15 | Or + Nasdaq + S&P + EUR/USD |
|---|---|---|---|
| 0,5 % | 0 / 0 / 0 % | 0 / 0 / 0 % | 0,4 / 6 / 27 % |
| **1 %** | 0,1 / **2** / 12 % | 0 / **0,7** / 9 % | 24 / 60 / 87 % |
| 2 % | 13 / 41 / 72 % | 4 / 27 / 65 % | 93 / 99 / 100 % |
| 3 % | 49 / 81 / 95 % | 25 / 67 / 92 % | 100 % |
| 12 % (version GPT) | 100 % ; ruine 18 / 50 / 80 % | 100 % ; ruine 6 / 37 / 77 % | ruine 92 / 98 / 100 % |

**2. Compte cent** (rejeu historique, or 4 ans ; signal ignoré si le lot minimum dépasse le budget)

| Départ | 0,5 % | 1 % | 2 % | 3 % |
|---|---|---|---|---|
| 100 € | 12 % ignorés, ×1,29, pire baisse −12 % | 1,4 % ignorés, ×1,65, −24 % | 0 ignoré, ×2,90, −44 % | 0, ×4,59, −59 % |
| 500 € | 0 ignoré | 0 | 0 | 0 |

**3. Filtre placebo « séance calme / inside day »** (1 000 tirages au hasard, même nombre de séances par mois, même sens, même volatilité)

| Jeu | R total réel | Placebo (médiane) | p | Vaut ? |
|---|---|---|---|---|
| Or 4 ans | +82,5 | +25,4 | 0,042 | oui |
| Or M15 | +48,5 | +20,7 | 0,119 | non |
| Chaque moitié de 2 ans | +33 / +49 | +3 / +22 | 0,10 / 0,12 | non |

**4. Diversification à risque global constant** (période commune 08/2025-11/2026 ; jours où au moins 2 marchés perdent ensemble)

| Mécanique | Portefeuille | Total | Temps sous le sommet | Perte des jours communs (or seul ces jours-là) | Aide ? |
|---|---|---|---|---|---|
| Règle GPT | or seul | +29,5 R | 73 % | — | — |
| Règle GPT | + S&P + EUR/USD | +24,8 R | 79 % | −11,7 (−8,3) | non |
| `bt_or` | or seul | +122 R | 88 % | — | — |
| `bt_or` | + Nasdaq + EUR/USD | +42 R | 89 % | −81 (−46) | non |

**5. Interrupteur de pyramide** (renforts coupés si les 20 derniers paniers montrent qu'ils ont coûté)

| Jeu | Renforts − sans renforts | Toujours sans | Toujours avec | Interrupteur |
|---|---|---|---|---|
| Règle GPT, or 2022-2024 | −1,7 R | +34,8 | +33,1 | **+42,4** |
| Règle GPT, or 2024-2026 | +11,8 R | +37,6 | **+49,4** | +48,0 |
| Règle GPT, or M15 | +12,3 R | +36,3 | **+48,5** | +41,6 |
| `bt_or`, or 2024-2026 | +107,6 R | +46,6 | **+154,2** | +122,2 |

**6. Sens tiré au sort pour `bt_or`** (2 000 tirages, 3 positions) : 4 ans moyenne +108 R (5 % des tirages sous +63, 5 % au-dessus de +151) ; `bt_or` réel +153 R (mieux que 96 % des tirages) mais −1 R en 2022-2024 (mieux que 12 % seulement) ; « toujours acheteur » +244 R, mieux que tous les tirages.

1. Taille : à 12 % par panier, la baisse de −30 % est certaine et la ruine en 2 ans va de 18 à 50 % ; **1 % par panier** est le maximum qui garde moins de 10 % de chances de −30 % en 2 ans (prudent), et seulement 0,5 % par marché si on joue 4 marchés en même temps.
2. Compte cent : 500 € suffisent toujours ; avec 100 €, à 1 % par panier, 1,4 % des signaux sont ignorés (lot minimum trop gros) et le résultat passe de ×1,83 à ×1,65 sur 4 ans.
3. Le filtre « séance calme » fait 3 fois mieux qu'un tirage au hasard en moyenne, mais il ne bat clairement le hasard que sur 4 ans (p 0,04), pas sur 2 ans ni en M15 : pas assez net pour être sûr.
4. Diversifier ne protège pas les jours où tout perd ensemble : avec les autres marchés, ces jours-là coûtent plus que l'or seul, et `bt_or` perd les deux tiers de sa croissance.
5. L'interrupteur de pyramide aide seulement quand l'or fait du surplace (2022-2024) ; pendant la hausse il coûte, donc « toujours renforcer » reste meilleur. Conseil : règle de GPT à 1 % par panier au plus si un jour elle passe en réel, or seul, renforts toujours actifs.

# Avis pour Baptiste — 23/11/2026 (Lot B : deviner le type de marché en direct, 7 pistes, PRIORITES 23/11)

**Réponse courte : aucune des 7 pistes ne devine le type de marché mieux que « tout laisser en marche ». Pas de variante `_regime_opt`, robot inchangé (v25, celle du Lot A).** Trois pistes (3, 5, 6) semblaient passer, mais seulement en grossissant les familles d'indices souvent sans position ; à risque égal, l'écart disparaît (meilleur p corrigé 0,26 ; Holm entre les 7 pistes inutile, aucune sous 0,05).

Socle commun `regime_socle.py` : 6 familles qui tournent depuis 08/2022 (`bt_or` en H1, cassure et retour de fourchette or H1, `repli_ind`, `rebond_nas`, tendance 50/200 S&P). Chaque jour, un poids de 0 à 2 par famille, décidé avec ce qui est connu avant le jour ; walk-forward 6 mois / 1 mois ; spread réel puis doublé ; reality check de White sur toute la grille. Unité u = 1 écart-type journalier d'une famille. **Correction en cours de route** : comparer « à exposition égale » (somme des poids) grossissait à tort les familles souvent sans position (un témoin fixe « indices seuls » passait le critère avec +761 u). Chaque piste est donc aussi jugée **à risque égal** (volatilité mesurée sur les 6 mois d'avant), et doit passer les deux mesures.

Hors échantillon, spread réel. Références : tout en marche **+87 u (2022-24) / +324 u (2024-26)** ; suivre ce qui marche sur 5 jours −96 / +34 (exposition égale), −53 / +121 (risque égal).

| Piste | Banc (réglages) | Exposition égale : 2022-24 / 2024-26 (tout : 87 / 324) | Risque égal : 2022-24 / 2024-26 (tout : 87 / 324) | p corrigé contre « tout » : expo / risque | Spread doublé, 2024-26 risque égal (tout 296) | Verdict |
|---|---|---|---|---|---|---|
| 1. Modèle de régime caché (HMM 2-3 états, hystérésis) | `banc_regime_p1.py` (36) | 128 / 348 | 77 / 250 | 0,091 / 0,887 | 227 | ne tient pas |
| 2. Mesures tendance/bruit (Kaufman, Hurst, ratio de variance, ADX, VWAP…) | `banc_regime_p2.py` (30) | 37 / 271 | 51 / 253 | 0,985 / 0,999 | 229 | ne tient pas |
| 3. Méta-étiquetage (prendre ou non chaque signal, purge + embargo) | `banc_regime_p3.py` (16) | 167 / 549 | 93 / 348 | 0,004 / **0,261** | 336 | ne tient pas (faux positif à exposition égale) |
| 4. Bandit (Hedge, Exp3, Thompson, plancher) | `banc_regime_p4.py` (28) | 90 / 316 | 75 / 297 | 0,085 / 0,808 | 275 | ne tient pas |
| 5. Régime commun or / indices / dollar / taux (VIX, taux réel, pente, ACP glissante) | `banc_regime_p5.py` (26) | 100 / 448 | **30** / 376 | 0,038 / **0,540** | 368 | ne tient pas (faux positif à exposition égale) |
| 6. Infos de début de journée (VIX, volatilité implicite de l'or, annonces, écart d'ouverture, COT) | `banc_regime_p6.py` (21) | 72 / 464 | 69 / 329 | 0,012 / **0,625** | 315 | ne tient pas (perd en 2022-24) |
| 7. Sortie qui s'adapte (stop resserré quand l'efficacité chute…) | `banc_regime_p7.py` (24) | 126 / 298 | — (perd déjà en 2024-26) | 0,476 / — | 252 (expo) | ne tient pas |

Piste 6 (informations de début de journée) :
1. Règles à seuil ou poids appris par case : VIX au-dessus de 20 ou en forte hausse, volatilité implicite de l'or (GVZ) contre sa médiane, jour d'annonce (emploi, inflation, Fed), grand écart d'ouverture la veille, COT extrême.
2. Le réglage le plus choisi est « VIX > 20 → indices en rachat ×2, tendance S&P coupée » ; il perd déjà en 2022-24 (+72 u contre +87).
3. À risque égal : +69 / +329 u contre +87 / +324 ; t −0,32 ; p corrigé 0,63.
4. Annonces, GVZ, écart d'ouverture et COT ne donnent aucun réglage stable ; le grand écart d'ouverture n'arrive que 3 % des jours.
5. Limite : le socle décide le poids à minuit, donc l'écart d'ouverture du jour même n'est pas testé (seulement celui de la veille).

Piste 5 (régime commun des marchés) :
1. L'état commun connu le matin (S&P en hausse et VIX bas ou non, tendance de l'or 20/60 jours, dollar et taux réel, volatilité, ACP glissante sur 16 grandeurs) donne les poids, fixés à la main ou appris par état sur le passé.
2. À exposition égale, il semblait passer (+100 / +448 u contre +87 / +324, p 0,038), mais pour la même raison que la piste 3 : les règles « 2 ou 0 » grossissent des familles souvent sans position.
3. À risque égal, il fait +30 u contre +87 en 2022-24 et +376 contre +324 en 2024-26 ; p corrigé 0,54 : pas de différence réelle.
4. Le réglage choisi change presque chaque trimestre : l'état des marchés ne dit pas de façon stable quelle famille gagnera le mois suivant.
5. Contrôle : retarder toutes les données d'un ou quatre jours de plus ne change rien (pas de fuite) ; le dollar FRED, publié chaque semaine, est pris avec 10 jours de retard.

Piste 3 (méta-étiquetage) — la seule qui passait d'abord :
1. Un classifieur par famille, réentraîné chaque mois sur le passé purgé, dit chaque jour s'il faut prendre les signaux (volatilité de l'or, efficacité, VIX, S&P, gain récent de la famille).
2. À exposition égale, il semblait gagner beaucoup (+167 / +549 u contre +87 / +324, p 0,004) ; mais il coupe surtout l'or (`bt_or` presque toujours à 0) et garde `repli_ind` et `rebond_nas`, qui sont souvent sans position et donc grossis par la mise à exposition égale.
3. À risque égal, il reste à peine devant : +93 / +348 u contre +87 / +324, t 0,27, p corrigé 0,26 ; son rapport gain/risque est même un peu moins bon (1,40 contre 1,47 par an).
4. À l'intérieur d'une famille, le tri ne sert presque à rien : les signaux pris gagnent aussi souvent que ceux écartés (cassure or 50 % contre 48 %).
5. Il coupe `bt_or` parce que l'étiquette « trade gagnant » punit une stratégie qui gagne rarement mais gros ; c'est le piège connu du méta-étiquetage.

Piste 1 (modèle de régime caché) :
1. Un modèle à 2 ou 3 états, réestimé chaque mois sur le passé, met les familles de tendance de l'or ×2 en régime « agité », et les familles de retour ×2 au calme.
2. À exposition égale, il battait « tout en marche » sur les deux périodes (+128 / +348 u contre +87 / +324), mais avec p 0,091.
3. À risque égal, il perd : +77 / +250 u ; p corrigé 0,89.
4. Il sépare surtout les journées agitées des calmes, pas la tendance du va-et-vient, et le sens de l'effet s'est inversé pendant presque un an (06/2023-04/2024).
5. Verdict : ne tient pas.

Piste 7 (sortie qui s'adapte toute seule) :
1. On change la sortie de `bt_or` et de la cassure or : stop resserré de moitié quand l'efficacité de Kaufman passe sous 0,25, sortie après 12 h sans progrès, moitié encaissée à +1 ATR.
2. En 2022-24 (or heurté), le stop resserré aide (+126 u contre +87), mais en 2024-26 (forte tendance) il fait moins bien (+298 contre +324 ; +87 contre +99 sur la période réservée).
3. La sortie au temps et l'objectif partiel coupent les grands paniers gagnants, qui font l'essentiel du gain de `bt_or`.
4. Contrôle sur l'or M5 (06/2025-11/2026) : `bt_or` d'origine +114 R ; avec stop resserré +43 R (2,6 fois plus de paniers) ; les 12 variantes font toutes moins bien.
5. p corrigé 0,476 ; au spread doublé, elle perd aussi en 2024-26 (+252 contre +296 u).

Piste 2 (mesures tendance / bruit) :
1. Six mesures sur l'or H1 et quatre sur les indices, lissées et combinées, donnent les poids.
2. Hors échantillon, c'est nettement moins bien que tout laisser en marche, dans les deux mesures (risque égal : +51 / +253 u contre +87 / +324).
3. Les mesures ne s'accordent pas entre elles, et le « régime » d'hier ne se prolonge pas assez le lendemain ; le réglage choisi change presque chaque trimestre.
4. Au spread doublé, même écart ; p corrigé 0,985 à 0,999.
5. Ne tient pas.

Piste 4 (bandit) :
1. Le réglage choisi est presque toujours Exp3 lent, avec des poids proches de « tout en marche » : +90 / +316 u à exposition égale, +75 / +297 à risque égal.
2. Les versions qui réagissent vite retombent dans le défaut de « suivre 5 jours ».
3. p corrigé 0,085 (exposition égale) et 0,81 (risque égal) contre « tout en marche ».
4. Au spread doublé, même constat.
5. Sur ces familles, le gain récent ne prédit pas le gain suivant.

# Avis pour Baptiste — 23/11/2026 (Lot A : la pyramide sur nos autres stratégies)

**Réponse courte : ajouter des renforts n'améliore aucune de nos autres stratégies. Une seule chose tient, déjà connue : l'or « toujours acheteur » avec la pyramide de `bt_or`. Il est sur la démo en `achat_or_pyr_opt` (robot v25, hors totaux, essais OK).**

Total à risque égal (en points de base), sans renforts / renforts « gagnants » de GPT / pyramide `bt_or` :

| Stratégie | 2022-2024 | 2024-2026 | Hors échantillon : choix contre sans renforts | Verdict |
|---|---|---|---|---|
| repli_ind (indices) | 1 024 / 1 024 / 811 | 6 093 / 6 093 / 4 303 | 7 726 contre 7 784 | non |
| rebond_nas, rebond_sp | identiques (trade d'un jour) | identiques | identique | non |
| fomc_dax | 1 258 / 1 258 / 798 | 25 / 25 / 5 | 528 contre 539 | non |
| elan_m15 | 1 459 / 1 382 / 716 | 50 / 81 / −339 | 411 contre 2 417 | non |
| cassure_m15 | 13 / −122 / 169 | 1 430 / 1 051 / −86 | 1 239 contre 1 848 | non |
| exces_m5 | 805 / 754 / 746 | 658 / 686 / 692 | 1 287 contre 1 256 | non |
| retour_court_ar | −3 852 / −4 011 / −3 949 | −2 361 / −2 509 / −2 481 | −6 616 contre −5 575 | non |
| **or toujours acheteur** | 3 032 / 2 157 / **3 701** | 3 702 / 4 206 / **9 349** | **10 940 contre 5 840** | **tient (pyramide)** |

1. Sur les indices (repli, rebonds, FOMC), les renforts ne servent à rien ou coûtent : ces trades sont courts et leur gain vient du rebond lui-même, pas d'une tendance qui s'étire.
2. Sur les règles courtes de l'or (elan, cassure, excès, retour), les renforts n'aident pas non plus ; elan_m15 perd même beaucoup hors échantillon (411 contre 2 417).
3. Seul l'or « toujours acheteur » gagne vraiment à la pyramide (choisie 13 fois sur 14 en hors échantillon, test de White p 0,001), mais c'est la même mécanique que `bt_or` avec le sens toujours à l'achat : un pari sur la hausse de l'or.
4. Sur la démo : `achat_or_pyr_opt` = `bt_or` en achat seulement, 0,01 lot, 3 positions, mêmes heures et même stop suiveur ; règle d'arrêt de `bt_or` (−20 R ou moyenne < −0,3 R après 40 paniers), écrite avant.
5. Limites : rebond_nas / rebond_sp ne tiennent qu'une bougie journalière (aucun renfort possible), fomc_dax et la tendance 50/200 du S&P ont trop peu de trades (37 et 3) pour juger.

# Avis pour Baptiste — 23/11/2026 (règle « renforts gagnants » de GPT Astra, sur l'or et sur les autres marchés)

**Réponse courte : la règle de GPT gagne un peu sur l'or, mais moins que `bt_or` sur les 2 dernières années, et ses +3,21 %/semaine ne se retrouvent pas avec les vrais prix du courtier (−3,25 %/semaine sur la même fenêtre). À 12 % de risque par panier, elle ruine le compte une fois sur deux à trois. Elle tourne sur la démo pour les données : `gpt_pyramide_opt`, robot v24 (hors totaux, 0,02 lot, arrêt à −15 R).**

| Test (version A : laisser courir) | Paniers | R par panier | Total | Contre `bt_or` au même risque | Ce qu'il faut retenir |
|---|---|---|---|---|---|
| Or 2022-2024 (H1) | 122 | +0,28 | +34 R | **+49 contre +1 R** | meilleure que `bt_or` quand l'or ne monte pas franchement |
| Or 2024-2026 (H1) | 97 | +0,51 | +49 R | +68 contre **+154 R** | nettement moins bien pendant la hausse |
| Or M15 10/2024-11/2026 | 97 | +0,50 | +49 R | +72 contre **+148 R** | même chose ; 2026 T3 et T4 négatifs |
| Fenêtre de GPT 08/06-25/09/2026 | 9 (2 gagnants) | — | −3,9 R | GPT : 7 paniers, +3,21 %/sem. | **−3,25 %/semaine**, pire baisse −46 % à 12 % de risque |
| Ruine 24 mois, 100 €, 12 % par panier (4 ans) | | | | | mesuré 43 % ; prudent 70 % |
| Ruine 24 mois, 100 €, 3 % / 2 % par panier (4 ans) | | | | | prudent 2 % / 0 % ; compte médian ×1,3 / ×1,25 |
| Autres marchés (12 essayés) | 59-135 par marché | | | corrélation mensuelle avec `bt_or` : −0,3 à +0,3 | Nasdaq, S&P, EUR/USD, pétrole « ajoutent » mais sur trop peu de paniers (p 0,33) |
| Portefeuille multi-marchés (parité de risque) | | | | bat `bt_or` dans 1 cas sur 4 | **ne tient pas** |

1. Sur l'or, la règle de GPT est positive dans les deux périodes (+0,28 et +0,51 R par panier, test de White p 0,03), et sans lien avec `bt_or` (corrélation mensuelle 0,04) : c'est une vraie pièce différente, pas une copie.
2. Mais elle fait 2 fois moins que `bt_or` sur 2024-2026 à risque égal, et la fenêtre que GPT montrait (+3,21 %/semaine) donne −3,25 %/semaine avec les vrais prix : 9 paniers et non 7, dont 2 gagnants.
3. À 12 % du compte par panier, c'est un pari : pire baisse de −83 à −99 %, ruine en 2 ans 43 % si l'avantage est vrai, 70 % s'il est moitié moindre. À 2-3 % par panier la ruine disparaît presque, pour un compte médian ×1,3 en 2 ans (prudent).
4. Ailleurs que sur l'or, la mécanique `bt_or` perd presque partout (S&P, Dow, EUR/USD, ETH, DAX, pétrole) ; la règle de GPT est positive sur 4 marchés peu liés à l'or, mais sur 60 paniers environ chacun et sans preuve (p 0,33). Le portefeuille multi-marchés ne bat pas `bt_or` seul.
5. Mon avis : la garder en données sur la démo (v24) à côté de `bt_or`, car elle gagne quand l'or fait du surplace ; ne jamais la jouer à 12 % ; la regarder à nouveau après 30 paniers réels (règle d'arrêt : −15 R ou moyenne < −0,3 R).

# Avis pour Baptiste — 22/11/2026, soir (« bt_or doit mieux entrer en position », PRIORITES 22/11)

**Pont revenu lundi 23/11 vers 7 h (Paris) ; robot v23 (`pari_tendance_opt`) installé à 7 h 01**, positions reprises, aucune fermée ; une erreur isolée à 7 h 02 (Windows refuse l'accès à un fichier, déjà vue), sans suite.

**Réponse courte : aucune des 5 pistes ne fait mieux entrer `bt_or`. Pas de `bt_or_entree_opt`, robot inchangé (v23).** Toutes trient des périodes ou multiplient les paniers ; aucune ne rend l'entrée plus juste, et aucune ne bat hors échantillon la référence « toujours acheteur + pyramide ».

Hors échantillon (walk-forward), à risque égal, sur les mêmes mois :

| Piste | Banc (essais) | 4 ans H1 : choisi / `bt_or` / toujours acheteur + pyramide | 17 mois M5 : choisi / `bt_or` / toujours acheteur | Écart défavorable médian (`bt_or` 0,51 R) | Bat le hasard en 2022-2024 ? | Verdict |
|---|---|---|---|---|---|---|
| 1-2. Repli dans la tendance, cassure | `banc_entree_moment.py` (20) | +246 / +179 / **+320** R | +43 / **+63** / +30 R | 0,42-0,50 | non (sauf 1 réglage) | ne tient pas |
| 3-4. Fond journalier, volatilité, heure | `banc_entree_filtres.py` (17) | +242 / +179 / **+320** R | **+91** / +63 / +30 R | 0,49-0,52 | seulement les versions « acheteur » | ne tient pas |
| 5. Stop initial plus serré (même risque en $) | `banc_entree_stop.py` (29) | **+339** / +179 / +320 R | +28 / **+63** / +30 R | 0,51-0,56 | non | ne tient pas |

1. Attendre un repli de 0,25 ATR donne de meilleurs paniers (+0,29 R par panier au lieu de +0,16) mais 2 fois moins nombreux ; l'écart défavorable médian ne baisse presque pas (0,47 contre 0,51 R) et un panier sur deux touche toujours son stop de départ.
2. Les filtres de fond, de volatilité et d'heure choisissent des moments, pas de meilleures entrées ; le meilleur sur 4 ans est « acheter seulement quand l'or est au-dessus de sa moyenne 50 jours » (+452 R à risque égal contre +425 pour l'achat permanent), une différence trop petite pour compter.
3. Un stop plus serré ne fait pas monter le gain par R : le spread pèse 2 à 2,5 fois plus et le stop est touché 6 fois plus souvent ; le beau chiffre sur 4 ans (+339 R) vient en partie des grandes bougies d'une heure et ne se retrouve pas en M5 (+28 R contre +63 pour `bt_or`).
4. Sur 2022-2024, quand l'or ne montait pas franchement, aucune entrée qui garde le sens « prix contre moyenne de 2 jours » ne fait mieux qu'un sens tiré au sort : le problème de `bt_or` n'est pas le moment d'entrée mais le sens, qui ne vaut que dans une forte tendance.
5. Seule idée qui reste debout : sur 4 ans, l'achat permanent avec pyramide fait mieux que `bt_or` (+320 contre +179 R hors échantillon), mais il perd sur les 17 derniers mois (+30 contre +63 R) et c'est un pari pur sur la hausse de l'or ; je ne le mets pas sur la démo sans ta décision.

# Avis pour Baptiste — 22/11/2026 (contre-expertise externe : 3 travaux, PRIORITES 22/11)

**Réponse courte : l'expert a raison sur l'essentiel.** Le plan −30 % fait environ +1,6 % par mois en prudent (pas +0,3 %), mais seulement grâce au levier ; `bt_or` gagne surtout par la pyramide et la hausse de l'or, pas par un vrai signal de sens ; le momentum de fin de séance ne tient pas. **Robot inchangé (v23), aucune nouvelle variante.**

| Travail | Banc | Résultat principal | Verdict |
|---|---|---|---|
| 1. Réconcilier le plan −30 % | `banc_reconcilie.py` | Mêmes réglages dans les deux bancs (levier 7,5). Prudent : mois typique +0,3 %, moyenne des mois +2,7 %, **rythme du compte sur 12 mois +1,6 %** (compte médian ×1,21) ; 27 % de chances d'une année en perte ; 48 % de mois négatifs | écart = définition, pas erreur |
| 2. Décomposer `bt_or` | `banc_decompose_bt.py` | 4 ans (H1) : `bt_or` +153 R ; sans renforcements +58 R ; sens au hasard +108 R ; **toujours acheteur +244 R** (pire baisse −25 contre −40). 2022-2024 : `bt_or` −1 R | gain = ~½ pyramide + hausse de l'or ; le signal ne bat pas l'achat simple |
| 3. Fin de séance S&P / Nasdaq / Dow | `banc_fin_seance.py` | 12 derniers mois réservés : S&P −4,0 bp par jour, Nasdaq −3,7, Dow −6,1 ; 4 mois positifs sur 13 ; −236 bp pendant les 6 mois négatifs de `bt_or` (repli d'indices : +609 bp) | **ne tient pas** (White p 0,81) |

1. Plan −30 % : la bonne mesure pour décider est le rythme du compte sur 12 mois (+1,6 % par mois en prudent, +4,3 % si l'avantage mesuré est vrai), toujours avec ses deux risques : 27 % d'années en perte et la moitié des mois négatifs. Le « +0,3 % » est le mois typique, pas ce que rapporte l'année.
2. Sans levier, la note de l'expert se retrouve à peu près : +0,4 à +0,7 % par mois selon la taille donnée à `bt_or` (+0,50 % par mois et −7,5 % de pire baisse dans la version la plus proche, contre +0,40 % et −5,4 % chez lui).
3. `bt_or` : environ la moitié du gain vient des renforcements ; le signal « prix contre moyenne de 2 jours » bat un sens tiré au sort (p 0,04 sur 4 ans), mais fait 90 R de moins que d'acheter tout le temps et rien du tout en 2022-2024, quand l'or ne montait pas franchement.
4. Conséquence pratique : `bt_or` est surtout un pari sur la hausse de l'or avec une pyramide ; si l'or fait du surplace ou baisse longtemps, il faut s'attendre à ce qu'il ne gagne plus.
5. Fin de séance : la règle publiée ne marche ni sur l'apprentissage (−0,7 bp) ni sur les 12 mois réservés ; elle perd pendant les mauvais mois de `bt_or`, alors que le repli d'indices les compense. Rien à mettre sur la démo.

# Avis pour Baptiste — 21/11/2026, fin d'après-midi (poche pari tendance, PRIORITES 21/11 15 h 20)

**Réponse courte : le meilleur montage est `bt_or` avec une petite mise (3 % du compte par R) et un objectif ×5. Il est sur la démo en variante `pari_tendance_opt` (v23, compte virtuel séparé, hors totaux).** Viser gros en misant gros ne marche pas : plus de mise donne surtout plus de ruine.

Poche de 100 € (compte cent), 24 mois, Monte-Carlo sur les vrais paniers (`banc_pari_tendance.py`). « Prudent » = avantage divisé par 2 ; c'est la colonne à regarder.

| Montage | ×objectif atteint : mesuré 18 mois / mesuré 4 ans / prudent 4 ans / sans avantage | Ruine (sous 20 €) : mesuré 4 ans / prudent / sans avantage | Durée médiane (prudent) | Semaine 16-20/11 |
|---|---|---|---|---|
| **`bt_or`, 3 %, ×5 (choisi)** | 94 % / 49 % / **23 %** / 8 % | 2 % / **11 %** / 36 % | 15 mois (66 % n'ont rien atteint en 24 mois) | 100 € → 140 € |
| `bt_or`, 3 %, ×3 | 98 % / 67 % / 39 % / 19 % | 2 % / 11 % / 35 % | 12 mois | 140 € |
| `bt_or`, 5 %, ×3 | 95 % / 70 % / 44 % / 24 % | 18 % / 45 % / 71 % | 8 mois | 166 € |
| `bt_or`, 10 %, ×3 | 69 % / 49 % / 34 % / 24 % | 51 % / 66 % / 76 % | 3 mois | 232 € |
| `bt_or_plus` (ajouts 1-2-3), 3 %, ×3 | 89 % / 61 % / 38 % / 23 % | 38 % / 61 % / 77 % | 4 mois | 219 € |
| `bt_or_plus`, 7,5 %, ×5 | 41 % / 27 % / 18 % / 12 % | 72 % / 82 % / 88 % | 1 mois | 397 € |
| Référence `pari_opt` (repli S&P + Russell), ×3 | prudent : 56 % en 5 ans | prudent : 39 % | ~17 mois | — |

1. Avec 3 % du compte par R, la poche a environ 1 chance sur 4 de faire ×5 en 2 ans si l'avantage n'est que la moitié de ce qu'on a mesuré, et 1 chance sur 9 d'être vidée ; le plus souvent (2 fois sur 3), elle n'a encore rien atteint au bout de 2 ans.
2. Monter la mise ne fait pas plus de ×3 ou ×5 : à 10 % par R, la ruine passe à 66 % (prudent) pour à peine 34 % de ×3.
3. `bt_or_plus` (ajouts 1-2-3) fait de très belles semaines (la semaine du 16/11 : 100 € → 397 € à 7,5 %), mais ses gros paniers perdants (jusqu'à −6,6 R) le ruinent une fois sur deux ou plus.
4. Sur la démo : `pari_tendance_opt` joue les paniers `bt_or` sur un compte virtuel de 11 600 $ (= 100 € en compte cent × 100), 3 % par R, encaisse et s'arrête à ×5 (58 000 $) ; s'arrête aussi si la poche passe sous 20 % ou si le cumul est négatif après 40 paniers (règle écrite avant).
5. Limites : le choix tombe sur la plus petite mise testée (3 %), une mise plus petite n'a pas été testée ; et c'est un pari, pas un placement. **Robot v23 : VERSION publiée, essais OK.**

# Avis pour Baptiste — 21/11/2026, soir (piste 2 : grilles et martingales sécurisées — LOT TERMINÉ, points 1 à 4)

**Réponse courte : rien ne tient. Pas de `grille_opt` sur la démo, robot inchangé (v22).** Les 10-20 % par mois des grilles viennent de mois positifs nombreux payés par des « sauts » rares qui effacent des mois, voire des années.

| Famille (or, sécurités : stop global, filtre de tendance, pause) | Réglages | Hors échantillon (walk-forward) M5 / H1 | Comparé à bt_or au même risque | p corrigé M5 / H1 | Verdict |
|---|---|---|---|---|---|
| 1. Grille contre le prix (×1 à ×2, cloche BlockFIFO) | 105 | −11,7 % / −14,7 % | bt_or +0,9 % / +3,4 % | 0,94 / 1,00 | **ne tient pas** |
| 2. Pyramide dans le sens du prix (×0,8 à ×2, cloche) | 105 | −43,5 % / +84,7 % | bt_or +149 % / +390 % | 0,10 / 0,29 | **ne tient pas** |
| 4a. Annonces US à fort levier | 72 × 4 | +24 % / −89 % | bt_or +341 % / +373 % | 0,10 / 0,07 | **ne tient pas** |
| 4b. Financement crypto | 34 | +3 % par an (≈ taux sans risque) | — | 0,46 | **pas d'avantage** |
| BlockFIFO réel (référence) | — | −6 269 $ en 5 jours (59 % de gagnants ; le 02/10 seul : −10 684 $) | — | — | — |

1. Pyramide : 29 réglages sur 105 font un peu mieux que bt_or sur tout l'historique (surtout ×1,2-1,3 ou ×0,8), mais rien ne se confirme hors échantillon ; ×2 est injouable sous 1 000 à 3 000 € (lot minimum).
2. Sauts (point 3) : la grille contre le prix en fait un tous les 1 à 5 mois sur 4 ans (−10 à −13 % chacun) ; la pyramide presque jamais, mais elle a de nombreuses grosses pertes « presque au maximum » (bt_or : 45 en 4 ans).
3. Mois positifs : jusqu'à 90-94 % avec la martingale ×2, qui perd pourtant 26 % en 4 ans ; bt_or n'a que 50-56 % de mois positifs mais gagne.
4. Ruine sur 24 mois, compte cent de 500 € : grille contre le prix 100 % (BlockFIFO rejoué) ; pyramide ×1,0 avec sécurités 3,4 %, bt_or 4,8 %, ×0,8 9,1 % (tout cela si la pire perte d'un panier vaut 5 % du compte ; à 3 % la ruine de bt_or tombe à 0,2 %).
5. Conseil : garder bt_or tel quel, avec une pire perte de panier d'environ 3 % du compte sur le compte cent, et ne pas relancer BlockFIFO ni de martingale, même « sécurisée ».


## Détail point 1

**Point 1 (grille / martingale contre le prix sur l'or, coefficient 1,0 à 2,0 et cloche BlockFIFO, avec stop global, filtre de tendance et pause) : ne tient pas.** (`banc_grille_coef.py`, 105 réglages, M5 17 mois, H1 4 ans, contrôle M1)

| Réglage | Gain par mois (médiane) M5 / H1 | Mois positifs M5 / H1 | Pire baisse M5 / H1 | « Sauts » (stop global) sur 4 ans | Ruine 24 mois, 500 € |
|---|---|---|---|---|---|
| BlockFIFO v25 rejoué (contrôle) | −17 % / −4 % | 18 % / 42 % | −94 % / −98 % | 47, un par mois environ, −12 % chacun | 100 % |
| BlockFIFO avec filtre et pause | −13 % / −1 % | 12 % / 46 % | −87 % / −86 % | 37 | 100 % |
| Pas 0,2 ATR, ×1,5, 10 paliers, stop −10 % (le moins mauvais) | +1,7 % / +1,8 % | 82 % / 79 % | −14 % / −36 % | 11 (un tous les 4,7 mois ; chacun efface 5,7 mois de gain) | 0 %, mais 64 % finissent sous la mise ; minimum 195 € pour poser le lot |
| Martingale ×2, 10 paliers, stop −10 % | +0,5 % / +0,5 % | 94 % / 90 % | −10 % / −32 % | 5 (un tous les 10 mois ; chacun efface 22 mois) ; total 4 ans −26 % | impossible sous 1 276 € (lot minimum) |

1. C'est exactement le piège : 90 % de mois positifs et pourtant −26 % sur 4 ans avec la martingale ×2, car un seul « saut » efface près de 2 ans de petits gains.
2. Le résultat d'une grille dépend surtout de l'ordre des prix à l'intérieur d'une bougie : en supposant le cas flatteur, la médiane des réglages fait +32 % (M5) ; avec l'ordre que confirment les bougies M1 et le réel, elle fait −33 % (M5) et −94 % (H1). Seuls 2 réglages sur 107 gagnent sur 4 ans.
3. Le simulateur retrouve le vrai stop de BlockFIFO : le 02/10/2026 à 18 h 53, 64 positions d'achat coupées pour −12 651 $ (réel : 18 h 57, 60 positions, −12 500 $ ; total réel −6 269 $, simulé −7 169 $).
4. Tests : walk-forward hors échantillon −11,7 % (M5) et −14,7 % (H1) contre +0,9 % et +3,4 % pour bt_or au même risque ; p corrigé 0,94 et 1,00 (105 essais).
5. Sur un compte cent de 100 €, presque aucune martingale n'est même posable (lot minimum trop gros pour le risque voulu). **Pas de `grille_opt` sur la démo pour la grille contre le prix.**



## Détail point 4

**Point 4 (annonces US à fort levier ; arbitrage du financement crypto) : rien ne tient.**

| Piste | Banc | Meilleur résultat honnête | Mois positifs | Pire baisse | Verdict |
|---|---|---|---|---|---|
| Annonces US, or, risque 10 % par annonce | `banc_annonces_levier.py` (72 réglages × 4 jeux) | walk-forward or M5 : +24 % sur 12 mois (bt_or au même risque : +341 %) ; or H1 4 ans : −89 % | 42 % (M5) | −33 % à −84 % | **ne tient pas** |
| Financement crypto (comptant acheté, perpétuel vendu) | `banc_financement.py` (34 réglages, BTC et ETH 2022-2026) | +3,0 % **par an** (+1,3 % de plus que les bons du Trésor) | 35 % (les autres mois : à plat) | −0,3 % | **pas d'avantage** (p corrigé 0,46) |

1. Annonces : aucun des 288 essais ne fait 10 % par mois en médiane ; le meilleur sur l'or fait +1,5 % par mois, avec un « saut » de −10 % du compte tous les 1,6 mois.
2. Sur 4 ans (H1), la même règle perd 89 % et ruine un compte cent sur 24 mois une fois sur trois (31 %).
3. Les fichiers du courtier ne montrent pas l'élargissement du spread aux annonces : les vrais coûts seraient encore pires.
4. Financement crypto : le taux payé est de +6,6 % par an sur BTC (+5,9 % sur ETH), mais après frais il reste environ 3 à 4,5 % par an, soit à peu près le taux sans risque, plus le risque d'une faillite de plateforme.
5. Ce montage est de toute façon impossible sur la démo MT5 (pas de vrai comptant ni de perpétuel) ; robot inchangé pour ce point.

# Avis pour Baptiste — 21/11/2026 (viser au moins +10 % par mois, PRIORITES 21/11)

**Réponse courte : +10 % par mois n'est pas atteignable de façon honnête avec ce qu'on a.** Rien de nouveau ne tient ; le seul bouton qui reste est la taille de la mise, et elle achète du rendement avec du risque d'arrêt.

1. **Plus de paniers `bt_or` : ne tient pas** (`banc_freq.py`, 22 réglages, M5 18 mois et H1 4 ans). Deux ou trois paniers par côté, une entrée toutes les heures, la reprise immédiate : c'est la même exposition en plus gros (corrélation 0,92 à 0,99 avec `bt_or`). À risque égal le gain ne bouge presque pas ; p corrigée 0,83 (M5) et 0,27 (H1) ; choisi en walk-forward, c'est moins bien que `bt_or` sur les deux jeux.
2. **Tendance sur d'autres actifs, en journalier, 14 marchés depuis 1970 à 2021 selon l'actif : ne tient pas** (`banc_tend_actifs.py`, 24 réglages). Aucun actif ne tient seul. Le portefeuille de tous fait +3,4 % par an pour une pire baisse de −30 % (0,3 % par mois), avec 51 % de mois négatifs. Le coût de portage (2 à 3 R par an) mange presque tout. Bitcoin et ether gagnent, mais pas plus que de simplement les acheter.
3. **Les montages (`banc_dix.py`, 5 000 tirages, 12 et 24 mois)** : pour faire 10 % par mois en rythme médian il faut 2,5 fois la mise du plan actuel (montage B), et ça ne marche que si l'avantage mesuré est entièrement vrai. Si l'avantage est moitié moindre : +2,7 % par mois, pire baisse de −60 % une fois sur dix, arrêt automatique 1 fois sur 3 en 24 mois.
4. **Le levier « pour 10 % » ne se retrouve pas d'une période à l'autre** : calculé sur 10/2024-11/2026 puis rejoué sur 08/2022-09/2024, il donne environ +2,3 % par mois. Les +13,8 % par mois du rejeu complet viennent de la hausse de l'or de 2024-2026 (`bt_or` : +1 R sur la première moitié, +154 R sur la seconde).
5. **Mon conseil** : rester au plan −30 % pour démarrer (A). Si tu acceptes plus de risque, le plan −50 % (C) est le meilleur compromis : +7,7 % par mois si tout est vrai, +2,4 % en prudent, arrêt 5 % sur 12 mois. La poche pari et `bt_or` seul coûtent beaucoup d'arrêts pour peu de gain. **Robot inchangé (v22), aucune nouvelle variante** : rien n'a passé la preuve. Attente réaliste : 2 à 3 % par mois.

**Montages, compte cent de 100 ou 500 €, 12 mois** (mesuré / prudent = avantage ÷ 2 / sans avantage ; arrêt automatique compris)

| Montage | Rythme médian par mois | Chance qu'un mois fasse ≥ +10 % | Chance de ≥ 10 % par mois en moyenne sur 12 mois | Mois négatifs | Pire baisse (1 cas sur 10) | Arrêt automatique, 12 mois | Arrêt, 24 mois |
|---|---|---|---|---|---|---|---|
| **A. Plan −30 % actuel** (mélange, arrêt à −34 %) | +4,4 % / +1,6 % / −1,4 % | 20 % / 14 % / 9 % | 9 % / 3 % / 1 % | 32 % / 48 % / 58 % | −19 % / −30 % / −35 % | 0 % / 4 % / 40 % | 0,2 % / 16 % / 79 % |
| B. Même mélange, mise × 2,5 (arrêt à −60 %) | **+10,0 %** / +2,7 % / −5,0 % | 42 % / 28 % / 16 % | 50 % / 19 % / 5 % | 33 % / 49 % / 53 % | −43 % / −60 % / −63 % | 0,2 % / 12 % / 60 % | 1 % / 34 % / 91 % |
| **C. Plan −50 %** (mise × 1,9, arrêt à −54 %) | +7,7 % / +2,4 % / −3,2 % | 36 % / 24 % / 15 % | 35 % / 12 % / 4 % | 33 % / 49 % / 57 % | −33 % / −49 % / −56 % | 0,1 % / 5 % / 45 % | 0,2 % / 20 % / 83 % |
| D. 90 % plan −30 % + 10 % poche pari | +8,2 % / +2,4 % / −2,0 % | 37 % / 29 % / 22 % | 40 % / 13 % / 4 % | 50 % / 59 % / 61 % | −48 % / −60 % / −62 % | 1 % / 12 % / 34 % | 5 % / 35 % / 72 % |
| E. 80 % + 20 % poche pari | +6,7 % / −1,9 % / −5,0 % | 31 % / 22 % / 16 % | 40 % / 15 % / 6 % | 48 % / 47 % / 44 % | −64 % / −65 % / −66 % | 39 % / 67 % / 81 % | 70 % / 92 % / 98 % |
| F. `bt_or` seul, mise maximale utile | +3,3 % / −2,2 % / −4,5 % | 33 % / 23 % / 16 % | 29 % / 13 % / 4 % | 38 % / 37 % / 34 % | −62 % / −62 % / −62 % | 49 % / 72 % / 88 % | 78 % / 94 % / 99 % |

- « Rythme médian » = ce que fait le compte sur 12 mois dans le cas médian, ramené à un mois. Le mois typique pris seul est plus bas (plan A : +2,8 % mesuré, +0,3 % prudent, comme le 18/11).
- Ruine (compte sous 20 % de la mise) : 0 % partout avec l'arrêt automatique, qui coupe avant. Finir sous la mise à 12 mois en prudent : 26 % (A), 33 % (B), 30 % (C), 52 % (E).
- Rejeu sur l'historique réel 08/2022-11/2026 (une seule trajectoire) : A fait une médiane de +1,9 % par mois (11 mois sur 52 à ≥ 10 %, 17 négatifs, pire baisse −17 %) ; B +4,1 % (pire baisse −41 %) ; C +3,2 % (−31 %) ; E et F touchent leur arrêt en 2023.
- Marge et lot : aucun montage ne dépasse 24 fois le capital hors poche ; le lot minimum cent passe à 100 € (écart d'arrondi 10 à 19 %) et à 500 € (moins de 10 %).

## Avis précédent — 18/11/2026, après-midi (règle de retrait avec intérêts composés, PRIORITES 18/11 14 h 15)

## VERDICT du test de la semaine 16-20/11 (DÉFINITIF, fenêtre close vendredi 23 h ; chiffres du samedi 0 h 10)

**Réponse courte : pas encore « un truc ».** La semaine finit positive (+384 $ en trades fermés), mais presque tout vient d'un seul panier `bt_or` (+760 $ vendredi). Le chemin a été très mauvais (−287 $ jeudi soir sur le compte simulé), et la sélection ne bat pas le témoin de façon significative. 1 critère tenu sur 4.

| Critère (fixé le 15/11) | Trades fermés seulement (base de la décision) | Avec le non encaissé (−71 $) | Tenu ? |
|---|---|---|---|
| 1. Total positif sur la semaine | +383,94 $ | +312,90 $ | **oui** |
| 2a. Jours agités positifs au total | +487,66 $ (4 jours) | — | oui |
| 2b. Jours calmes à moins de 10 $ de perte | mardi (seul jour calme) −103,72 $ | — | **non** |
| 2c. Information : part du meilleur jour | vendredi = 201 % du total (sans lui : −387 $) | — | — |
| 3. Bat le témoin de plus de 2 écarts types par trade | sélection +0,95 $ ± 1,99 (406 trades) contre témoin −0,08 $ ± 0,12 (1 259) : écart +1,02 $ pour 2 ET = 3,99 $ | — | **non** |
| 4. Plus bas du compte simulé de 100 $ au-dessus de 70 $ | plus bas −287,10 $ (jeudi soir) | fin de semaine 412,90 $ | **non** |

Compte simulé de 100 $, jour par jour (trades fermés) : lundi 69,01 $ (−30,99) · mardi −34,71 $ (−103,72) · mercredi 9,82 $ (+44,53) · jeudi −287,10 $ (−296,92) · vendredi 483,94 $ (+771,04).

**Pourquoi ça a lâché** : les règles de tendance M15 (`elan_m15`, `cassure_m15`) et `repli_ind` ont perdu gros lundi-jeudi (journées d'aller-retour) ; `bt_or` a tout rattrapé vendredi en un seul panier. Les variantes calme (+110 $) et les jumeaux de `bt_or` (`bt_or_plus_opt` +2 313 $, `bt_or_serre_opt` +516 $, hors test) confirment surtout que le gain de la semaine, c'est la mécanique `bt_or` sur une tendance de l'or. À confirmer sur 2 à 3 semaines de plus avant toute taille réelle, comme prévu ; pas de signal sérieux au sens des 4 critères.


1. **Règle simple conseillée : quand le compte a doublé, retire ta mise de départ, puis laisse tourner** (règle b). Avec 100 € : retirer 100 € quand le compte atteint 200 € ; avec 500 € : retirer 500 € à 1 000 €.
2. **Ce que ça coûte** (`banc_retrait.py`, plan à −30 %, 5 000 tirages) : rien si l'avantage est moitié moindre que mesuré (total à 24 mois : 1,58 fois la mise, contre 1,57 sans retrait). Si l'avantage est celui mesuré, on laisse 13 % du total (2,62 fois la mise contre 3,00).
3. **Ce que ça apporte** : une fois la mise retirée, tu ne peux plus perdre ton argent. Chance d'y arriver en 24 mois : 82 % (mesuré), 39 % (prudent), 14 % si l'avantage est nul. En 12 mois : 34 %, 17 %, 7 %.
4. **Aucune règle de retrait ne protège vraiment** : la chance de finir sous la mise (retraits comptés) reste la même pour toutes les règles, 16 % à 24 mois en prudent et 59 à 64 % si l'avantage est nul. Seule la taille de la mise et le seuil d'arrêt (−34 %) protègent.
5. **Les autres règles** : retirer en plus 25 ou 50 % des nouveaux gains ne change presque rien (2,60 et 2,59 contre 2,62). Tout retirer au-dessus de la mise chaque mois donne un revenu régulier mais tue les intérêts composés (2,21 contre 3,00). Le robot ne retire jamais d'argent : c'est toi qui le fais.

**Règles de retrait, plan à −30 %, après 24 mois** (en fois la mise de départ : ×100 € ou ×500 € ; médianes ; mesuré / prudent)

| Règle | Argent retiré | Mise récupérée | Reste sur le compte | Total (retiré + compte) | Finir sous la mise |
|---|---|---|---|---|---|
| (a) Aucun retrait | 0 / 0 | 0 % / 0 % | 3,00 / 1,57 | 3,00 / 1,57 | 0 % / 16 % |
| **(b) Retirer la mise quand le compte double (conseillée)** | **1,00 / 0** | **82 % / 39 %** | **1,78 / 1,29** | **2,62 / 1,58** | **0 % / 16 %** |
| (c) Comme (b), puis 25 % des nouveaux gains chaque mois | 1,11 / 0 | 82 % / 39 % | 1,67 / 1,28 | 2,60 / 1,58 | 0 % / 16 % |
| (c) Comme (b), puis 50 % des nouveaux gains | 1,21 / 0 | 82 % / 39 % | 1,54 / 1,25 | 2,59 / 1,58 | 0 % / 16 % |
| (d) Chaque mois, tout ce qui dépasse 1 fois la mise | 1,23 / 0,59 | 65 % / 28 % | 1,00 / 0,93 | 2,21 / 1,51 | 0 % / 15 % |
| (d) Tout ce qui dépasse 1,5 fois la mise | 1,17 / 0,22 | 58 % / 22 % | 1,50 / 1,32 | 2,64 / 1,59 | 0 % / 16 % |
| (d) Tout ce qui dépasse 2 fois la mise | 0,92 / 0 | 47 % / 15 % | 1,98 / 1,53 | 2,87 / 1,57 | 0 % / 16 % |

- À 12 mois, toutes les règles donnent le même total médian (1,66 mesuré, 1,20 prudent) ; finir sous la mise : 2 % mesuré, 27 % prudent.
- Si l'avantage est nul : total médian 0,81 à 0,87 fois la mise à 24 mois quelle que soit la règle, et 12 à 14 % de chances de finir sous la moitié.
- Mêmes limites que le plan de mise : 4 ans de données, période favorable, marge et frais de nuit du compte cent non vérifiés. Avec 100 €, les lots sont arrondis grossièrement.

## Avis précédent — 18/11/2026, après-midi (plan de mise du compte cent, et bt_or qui ajoute plus fort, PRIORITES 18/11 13 h 30)

1. **Plan de mise calculé (`banc_plan_cent.py`, 08/2022 à 11/2026, mise recalculée chaque semaine) : voir le tableau.** Le chiffre réaliste est la colonne « prudent » (avantage divisé par 2) : +0,2 à +0,3 % par mois en médiane, presque un mois sur deux négatif, une année sur quatre en perte.
2. **Avec 100 €, le plan à −15 % n'est pas faisable** : le plus petit lot (0,01 lot cent sur l'or) est 2,4 fois trop gros. Il faut 500 €, ou accepter le plan à −30 %.
3. **Si l'avantage est nul** (c'est le vrai risque : 4 ans de données, dont la grande hausse de l'or de 2024-2026), le plan à −30 % finit l'année en perte 65 % du temps, et le plan à −50 % perd la moitié du compte 38 % du temps. Je déconseille le plan à −50 %.
4. **`bt_or` qui ajoute plus fort (`banc_bt_plus.py`, 36 réglages, à risque égal) : ne tient pas.** Sur 18 mois, 1-2-3 jusqu'à 7 positions fait 8,62 $ gagnés par $ de pire baisse contre 6,34 ; mais sur 4 ans c'est l'inverse (2,52 contre 3,66), et le hasard l'explique (p = 0,42 à 0,95). Pas de `bt_or_plus_opt`.
5. **Rappel** : le labo ne calcule que sur la démo et ne passe aucun ordre réel ; ce tableau est une aide, pas une promesse. Robot inchangé (v20), test de la semaine non touché.

**Plan de mise, mélange `bt_or` + rebonds d'indices** (entre parenthèses : `bt_or` seul)

| Pire baisse visée | Risque par R sur l'or | Lot cent or, 100 € | Lot cent or, 500 € | Gain par mois, mesuré (médiane) | Gain par mois, prudent (médiane) | Mois négatif | Perdre la moitié en 12 mois | Année en perte | Arrêt automatique conseillé |
|---|---|---|---|---|---|---|---|---|---|
| −15 % | 0,22 % (0,34 %) | 0,01, trop gros (il faudrait 0,004) | 0,02 (0,03) | +1,3 % (+0,6 %) | +0,2 % (+0,1 %) | 48 % | 0 % | 25 % (31 %) | à −17 % du plus haut |
| −30 % | 0,47 % (0,72 %) | 0,01 | 0,05 (0,07) | +2,8 % (+1,2 %) | +0,3 % (0,0 %) | 48 % | 0 % | 27 % (33 %) | à −34 % |
| −50 % | 0,88 % (1,37 %) | 0,02 (0,03) | 0,08 (0,13) | +4,9 % (+1,9 %) | +0,3 % (−0,2 %) | 49 % | 5 % | 30 % (37 %) | à −55 % |

- « Pire baisse visée » : 9 trajectoires sur 10 restent au-dessus sur 12 mois, en scénario prudent. Les trois dernières colonnes de chances sont aussi en scénario prudent.
- Rejoué sur l'autre moitié des données, la pire baisse réelle est restée sous la cible pour le mélange (−7 à −33 %) ; `bt_or` seul a fait zéro sur 2022-2024 avec −16 à −54 %.
- Le mélange suppose des positions sur indices d'environ 7,5 fois le compte au plan −30 % (14 fois à −50 %) : marge et frais de nuit du compte cent non vérifiés. Lots indices pour 100 € à −30 % : Nasdaq 0,32, S&P 1,21, Dow 0,18, US2000 3,29 (lots cent).

## Avis précédent — 18/11/2026, après-midi (portefeuille bt_or + compléments, PRIORITES 18/11 12 h 30)

1. **Le calcul de mélange est fait (`banc_mix.py`, 08/2022 à 11/2026, 3 méthodes, poids fixés sur le passé et rejugés chaque semestre) : presque, pas prouvé.** À risque égal, hors échantillon (40 mois), le mélange « parité de risque » fait +26 % par an contre +18 % pour `bt_or` seul, avec 20 % de mois négatifs contre 35 %, et la même pire baisse (−7,6 % contre −7,4 %).
2. **Mais l'écart avec `bt_or` seul peut être du hasard** (p = 0,57 après correction), et une méthode sur trois fait moins bien que `bt_or` seul (moyenne-variance : pire baisse −11,7 % contre −5,9 %). Le mélange bat nettement les compléments seuls (p = 0,03) : c'est `bt_or` qui apporte le plus.
3. **Les compléments ne « compensent » pas `bt_or`, ils sont juste indépendants** : corrélation de −0,06 à +0,14. Pendant les 23 mois où `bt_or` perd, ils restent positifs (repli des indices +10 %, rebond Nasdaq +6 %, achat après pic du VIX +14 %), mais pas plus que les autres mois. En 2023 (`bt_or` −2,3 %), ils ajoutent +2 à +9 %.
4. **Rendement / risque** : au demi-Kelly, le mélange donnerait +108 % par an pour une pire baisse de −24 % (`bt_or` seul : environ +20 %, −12 à −16 %), mais avec des leviers de 13 à 35 fois, non jouables. Kelly entier : pire baisse de −45 à −76 %.
5. **Décision** : pas de variante `_mix_opt` (non prouvé, et le calcul met 44 à 75 % du poids sur Fed-DAX, la pièce la plus fragile). Les pièces tournent déjà séparément sur la démo (v20) : le direct dira si elles sont vraiment indépendantes. Test de la semaine non touché.

## Avis précédent — 18/11/2026, après-midi (un jumeau de bt_or qui encaisse petit à petit, PRIORITES 18/11 12 h 15)

1. **Testé avec ta correction (jumeau ajouté par-dessus `bt_or`, à la moitié, à la même et au double de sa mise ; 10 façons d'encaisser, 30 ensembles, `banc_jumeau.py`) : aucun jumeau n'est à garder.** Miser simplement plus sur `bt_or` fait aussi bien ou mieux.
2. **Sur 18 mois (M5)**, `bt_or` seul : +5 100 $, pire baisse −1 289 $, soit 6,34 $ gagnés par $ de pire baisse, 7 mois négatifs sur 18. Le meilleur ensemble fait 6,33 et garde les 7 mois négatifs : aucun des 30 ne fait mieux.
3. **Sur 4 ans (H1)**, petit mieux : 3,79 contre 3,66 pour le meilleur (un tiers à +1 R, un tiers à +3 R, stop remonté à l'entrée), mais 23 mois négatifs sur 52 comme `bt_or`. Hors échantillon, ça s'inverse : 4,43 contre 7,67 pour `bt_or` seul (M5 : 3,30 contre 3,51). Après correction, p = 0,87 : du bruit.
4. **Pourquoi** : encaisser tôt coupe les gros paniers, qui font tout le gain de `bt_or` (le jumeau n'en garde que 74 à 97 %), et les baisses évitées ne compensent pas. Le jumeau ajoute du risque au même prix que `bt_or`, avec un peu moins de gain.
5. **Décision** : pas de `bt_or_jumeau_opt`, robot inchangé (v20), test non touché. Si tu veux plus de gain, le calcul dit : augmenter la mise de `bt_or` (gain et pire baisse doublent ensemble). Suite : le portefeuille `bt_or` + compléments (12 h 30).

## Avis précédent — 18/11/2026, après-midi (allocation par régime connu en direct, PRIORITES 18/11 11 h 40)

1. **Le calcul d'allocation est fait (`banc_alloc.py`, 17 mois d'or, 18 réglages, walk-forward, spread réel) : il ne tient pas.** Hors échantillon, 12 mois : +104 $ (t = 0,1), 6 mois gagnants sur 12 ; face à la sélection actuelle à mise égale : +72 $ (t = 0,1, p = 0,29 après correction).
2. **Le « +109 $ au calme » ne se retrouve pas dans l'historique** : les mêmes règles jouées seulement au calme perdent 1 829 $ sur 17 mois (−5 $ par jour). Un gain de 109 $ ou plus en 3 jours arrive dans 7 % des fenêtres (5 % quand la sélection perd) : c'est de la chance, pas un avantage.
3. **Par régime, une seule chose gagne** : le panier `bt_or` (+16 à +18 $ par panier, calme ou agité, +13,75 $ par jour). La cassure M15 gagne un peu en agité (+1,56 $ par trade, t = 1,3) et perd au calme. Les règles de retour perdent partout, surtout la nuit (fausse cassure M5 en Asie : −1 673 $, t jusqu'à −3,8).
4. **Pourquoi le calcul échoue** : en trichant (poids connus d'avance) il ferait +14 668 $, mais les bonnes cases changent d'un mois à l'autre. Il garde 8 cases sur 90 et mise 5 fois moins : il évite des pertes (+1 839 $ face à « tout en marche », t = 1,1), il ne crée pas de gain. Des étiquettes décalées au hasard font mieux 1 fois sur 4.
5. **Décision** : pas de variante `_alloc_opt`, robot inchangé (v20), test de la semaine non touché. Résultat fragile en plus : décaler 11 étiquettes sur 10 000 le fait passer de +104 $ à −465 $.

## Avis précédent — 18/11/2026, matin (bt_or comme thermomètre de la tendance, PRIORITES 18/11 8 h 30)

1. **Ton idée testée sur 15 mois d'or (`banc_thermometre.py`, 24 réglages, walk-forward, spread réel) : elle ne tient pas.** Hors échantillon : +115 $ sur 10 mois (t = 0,1), 4 mois gagnants sur 10 ; face aux mêmes règles à mise égale sans thermomètre : −272 $ ; p = 0,38 après correction.
2. **Pourquoi** : les règles de retour perdent dans tous les états du panier, presque autant : −0,31 bp par trade sans panier, −0,75 bp panier perdant, −0,91 bp panier gagnant (plus de 1 R). L'écart va dans ton sens mais il est trop petit et change de signe d'une moitié à l'autre.
3. **Le hasard fait aussi bien** : en mettant les mêmes règles en pause au hasard, aussi souvent, on fait mieux que le thermomètre 2 fois sur 3. Et « suivre ce qui marche » sur 5 jours reste devant (+2 192 $ d'écart).
4. **Un indice sur 4 ans (or en H1)** : quand le panier gagne, la règle de retour perd 0,93 $ de plus par trade, de 2023 à 2026. C'est le bon sens, mais pas prouvé (t = 1,2) et pas retrouvé en M5.
5. **Décision** : pas de variante `_opt` (rien à mettre sur la démo), robot inchangé (v20), test de la semaine non touché. La leçon reste la même : ce sont les règles de retour elles-mêmes qui perdent sur 15 mois, pas leur calendrier.

## Avis précédent — 17/11/2026, nuit (pari court, de 1 jour à 1 mois, PRIORITES 17/11 20 h 10)

1. **Une seule piste bat un vrai pile-ou-face : le repli des 4 indices américains, joué à 100 fois la poche.** Sur un mois, avec 100 € : 17 % de chances de tripler (contre 13 % sans avantage), 29 % de doubler, 2 % de ×10. **Mais deux fois sur trois, la poche est perdue** (66 %).
2. **Les autres pistes ne battent pas la référence sans avantage** : cassures avec ajouts sur gain (BTC, ETH, Nasdaq, or), ordres des deux côtés aux annonces (un petit avantage, mais trop fragile), week-end crypto, et `bt_or` à forte mise (ruiné en un mois 88 % du temps). Le contre-pied Nasdaq + S&P en est proche, mais l'écart avec la référence n'est pas assez net.
3. Sur 1 jour ou 1 semaine, la chance de ×3 reste petite (6 à 7 %), parce qu'il n'y a pas assez de trades dans une si courte fenêtre. Avec 500 €, le plafond de 0,50 lot par position limite la mise, et la chance de tripler en un mois tombe à 5 %.
4. **Robot v20 publié** : `pari_court_opt` tourne sur la démo avec son propre compte virtuel de 100 €, séparé de `pari_opt` et hors totaux du test. Il s'arrête à ×3 (300 €), sous 20 €, ou 30 jours après son premier trade ; une nouvelle poche ne repart que si tu le décides.
5. Ces chances supposent un avantage réel moitié moindre que celui mesuré. Les chiffres viennent des vraies séquences du marché (1988-2026), pas d'un tirage au hasard.

**Pari court, 100 € au départ** (avantage ÷ 2 ; entre parenthèses, la même mise sans aucun avantage)

| Montage | Horizon | ×2 | ×3 | ×5 | ×10 | Tout perdre | Bat la référence ? |
|---|---|---|---|---|---|---|---|
| **Repli 4 indices US, 100 fois la poche (choisi)** | 1 jour | 16 % (12) | 6 % (4) | 0,6 % (0,5) | 0,1 % | 34 % (35) | non |
| même montage | 1 semaine | 20 % (14) | 7 % (5) | 1 % (1) | 0,3 % | 41 % (42) | oui |
| même montage | **1 mois** | **29 % (22)** | **17 % (13)** | **8 % (5)** | **2 % (1)** | **66 % (68)** | **oui** |
| même montage, 500 €, 50 fois, mise fixe | 1 mois | 18 % (12) | 5 % (2) | 0,1 % | 0 % | 36 % (39) | oui |
| Contre-pied Nasdaq + S&P, 100 fois | 1 mois | 29 % (23) | 17 % (13) | 8 % (6) | 1 % (1) | 65 % (71) | non (écart pas assez net) |
| `bt_or`, 25 fois | 1 mois | 24 % (21) | 17 % (14) | 10 % (9) | 4 % (4) | 88 % (92) | non |
| Annonces, ordres des deux côtés, 50 fois | 1 mois | — | 46 % (43) | — | — | 46 % (50) | non |
| Cassures avec ajouts / compression | 1 mois | — | ≈ la référence | — | — | — | non |
| Week-end crypto, 25 fois | 1 mois | 32 % | 16 % | 8 % | 2 % | 63 % | non (comme la référence) |

Repère : sur un jeu sans avantage, tripler avant de perdre 80 % arrive environ 1 fois sur 3 sans horizon. Sur un mois, c'est moins, parce que la plupart des poches n'ont encore rien atteint au bout de 30 jours.

# Avis pour Baptiste — 17/11/2026, soir (« trouver mieux que +10 % », PRIORITES 17/11 17 h)

1. **Deux nouvelles règles tiennent**. Le contre-pied d'une grande journée marche aussi sur le **S&P 500** (+16 bp par trade, 801 trades depuis 2008), mais il double en partie celui du Nasdaq. On peut aussi **acheter le DAX deux jours avant une annonce de la Fed** et revendre avant l'annonce (+31 bp, 176 trades), mais c'est faible depuis 2024. Tout le reste ne tient pas : 9 autres marchés, les excès en cours de séance, le tournant du mois, la nuit contre le jour.
2. **Le portefeuille de ce qui tient fait environ +19 % par an depuis 2008, mais avec une pire baisse de −41 %** (à 0,1 Kelly, environ 4,6 fois le capital). Honnêtement, une bonne part vient des années 2008-2009 de la règle Fed ; sans elle, c'est **+10 % par an pour −29 %**. Pour comparer, le S&P acheté et gardé fait +9 % par an, avec −53 %.
3. **À 0,5 et 1 Kelly, c'est la ruine** sur les données jamais vues : le Kelly calculé demande 20 à 35 fois le capital, et les krachs de 2011 et 2018 l'effacent.
4. **+10 % par mois n'est pas atteignable sans risquer la ruine.** Il faudrait 23 à 37 fois le capital : sur 12 mois, 26 à 36 % de chances d'y arriver, 4 à 22 % de tout perdre dans l'année, et la ruine presque sûre sur la durée (−98 à −100 % dans l'historique).
5. **Robot v19 publié** : `rebond_sp_opt` et `fomc_dax_opt` tournent à la taille minimale, hors totaux du test, avec leurs règles d'arrêt écrites d'avance. Le premier achat Fed est prévu lundi 7/12 à 17 h 29. Le test de la semaine n'est pas touché.

**Portefeuille : rendement par an et pire baisse** (walk-forward : les poids sont fixés sur le passé et refaits chaque année ; « depuis 2008 » = toutes les règles disponibles)

| Portefeuille | Mise | Levier moyen | Par an 1995-2026 | Par an depuis 2008 | Pire baisse |
|---|---|---|---|---|---|
| A. ce qui tient (repli 4 indices, contre-pied Nasdaq + S&P, Fed-DAX) | **1 Kelly** | 41 fois | ruine | ruine | −100 % |
| A | **0,5 Kelly** | 23 fois | ruine (dès 1995-2007) | +72 % mais en passant par −98 % | −98 à −100 % |
| A | 0,15 Kelly | 6,9 fois | +26 % | +28 % | −56 % |
| A | 0,1 Kelly | 4,6 fois | +18 % | +19 % | −41 % |
| A sans la règle Fed-DAX | 0,1 Kelly | — | — | +10 % | −29 % |
| B. A + les « presque » (non prouvé) | 0,1 Kelly | 7,7 fois | +25 % | +27 % | −42 % |
| Référence : S&P 500 acheté-gardé | — | 1 fois | +9 % | +9 % | −57 % |

**Viser +10 % par mois avec A** (Monte-Carlo sur 12 mois, blocs de 20 jours tirés dans 2008-2026) : à 23 fois le capital, 26 % de chances d'y arriver et 4 % de ruine dans l'année, mais −98 % de pire baisse dans l'historique ; à 37 fois, 36 % et 22 % ; au-delà, c'est pire.

**Ajouts au tableau « tout ce qui a été testé »** :
- **Tient** : contre-pied S&P (t 3,4) ; Fed-DAX (t 3,6, p = 0,003).
- **Presque** : Russell en contre-pied, veilles de férié, Fed sur les indices US.
- **Ne tient pas** : contre-pied sur Dow, DAX, Nikkei, BTC, ETH, pétrole, argent, or et euro ; excès en cours de séance (552 réglages) ; tournant du mois ; nuit contre jour.

# Avis pour Baptiste — 17/11/2026, soir (poche pari « triple ou rien », PRIORITES 17/11 17 h 20)

1. **Ta poche de 100 € joue maintenant « triple ou rien »** (robot v18) : dès qu'elle vaut 300 € (gains en cours compris), le robot ferme tout et s'arrête ; sous 20 €, il s'arrête aussi.
2. **Meilleure chance de tripler : le repli S&P + Russell à 14 fois la poche** (déjà en place) : **56 % de tripler, 39 % de tout perdre**, 5 % de n'avoir rien atteint en 5 ans ; il faut environ 1 an et demi en médiane. Pour comparer, un jeu sans avantage donne 29 %.
3. Le contre-pied du Nasdaq, l'or (`bt_or`) ou les deux règles ensemble font moins bien à 100 € (23 à 27 % de tripler) : leur plus petite taille est déjà trop grosse pour la poche.
4. **Avec 500 € au lieu de 100**, les deux règles ensemble à 1 Kelly montent à 68 % de tripler pour 24 % de ruine.
5. Ces chiffres supposent un avantage réel moitié moindre que celui mesuré (hypothèse prudente). Le test de la semaine n'est pas touché ; le lot « mieux que +10 % par an » est en cours.

| Montage (avantage ÷ 2) | Mise | Départ | Triple (×3) | Ruine | Rien en 5 ans | Durée médiane |
|---|---|---|---|---|---|---|
| **repli S&P + Russell (choisi, `pari_opt`)** | 2 Kelly | 100 € | **56 %** | 39 % | 5 % | ≈ 1,4 an |
| même montage, objectif ×5 | 2 Kelly | 100 € | 42 % | 45 % | 13 % | ≈ 2 ans |
| repli S&P + Russell | 1 Kelly | 100 € | 50 % | 11 % | 39 % | ≈ 4 ans |
| contre-pied Nasdaq | toutes | 100 € | 23-24 % | 76-77 % | 0 % | ≈ 2 mois |
| les deux | toutes | 100 € | 24-26 % | 74-76 % | 0 % | ≈ 2 mois |
| `bt_or` (or) | toutes | 100 € | 26-27 % | 73 % | 0 % | ≈ 1 semaine |
| les deux | 1 Kelly | 500 € | 68 % | 24 % | 7 % | ≈ 1,8 an |
| contre-pied Nasdaq | 2 Kelly | 500 € | 53 % | 33 % | 14 % | ≈ 2 ans |

# Avis pour Baptiste — 17/11/2026, après-midi (poche pari, PRIORITES 17/11 12 h 45)

1. **Poche pari de 100 $ : le vrai problème, c'est la taille minimale du courtier.** Un seul lot minimum, c'est déjà 42 % de la poche risqués par position sur l'or, et 23 à 52 fois la poche sur le Nasdaq ou le Dow. Avec ces tailles, 72 à 90 % des parcours finissent ruinés en un an si l'avantage réel n'est que la moitié de celui du banc (hypothèse prudente).
2. **Un seul montage passe ma règle** (fixée avant de regarder) : le repli d'indices (règle prouvée) sur les deux plus petits contrats, S&P et Russell 2000, à 14 fois la poche. Sur 12 mois, avantage divisé par 2 : **1 chance sur 7 de tout perdre, 1 sur 4 de finir sous 50 $, médiane ≈ 100 $, 1 sur 4 de doubler, 1 sur 16 de ×5, 1 sur 100 de ×10.** Il est lent : environ 18 trades par an.
3. `bt_or` en pari, c'est une loterie : 8 à 14 % de chances de ×10, mais 84 à 90 % de ruine (et il ne gagne que pendant la hausse de l'or depuis 2024).
4. **Robot v16 publié** : `pari_opt` tourne sur la démo avec un compte virtuel de 100 $, hors totaux du test. Il s'arrête de lui-même si la poche tombe sous 20 $, ou si la moyenne est négative après 40 trades. Le test de la semaine n'est pas touché, et le filtre retiré de la v15 reste retiré.
5. Si tu veux un vrai pari : une poche de 300 $ au lieu de 100 $ fait tomber la ruine du repli 4 indices à ≈ 33 % (et à ≈ 3 % avec 1 000 $). Passer en réel reste ta décision, sur ton PC.

| Montage (poche 100 $, 12 mois, avantage ÷ 2) | Tout perdre | Sous 50 $ | Médiane | ×2 | ×5 | ×10 |
|---|---|---|---|---|---|---|
| **`pari_opt` : repli S&P + Russell, 14 fois la poche (choisi)** | 15 % | 25 % | 102 $ | 26 % | 6 % | 1 % |
| même montage, sur 3 mois | 3 % | 11 % | 106 $ | 6 % | 0 % | 0 % |
| repli 4 indices US, lot minimum | 72 % | 73 % | 18 $ | 24 % | 10 % | 0 % |
| contre-pied du Nasdaq, lot minimum | 77 % | 77 % | 14 $ | 18 % | 7 % | 2 % |
| contre-pied + repli | 83 % | 84 % | 14 $ | 16 % | 11 % | 3 % |
| `bt_or` (or, 4 ans de données), lot minimum | 90 % | 90 % | 0 $ | 10 % | 10 % | 8 % |
| les trois ensemble | 89 % | 89 % | 1 $ | 11 % | 10 % | 9 % |

Avec l'avantage complet du banc (moins prudent), le choisi fait : ruine 61 %, ×5 11 % à 2 Kelly ; sur la 2de moitié seule : ruine 0 %, ×2 48 %, ×5 3 %. Détails : `banc_pari.py`, `donnees/pari_montecarlo.csv`, JOURNAL du 17/11 après-midi.

**Ajouts au tableau « tout ce qui a été testé »** : poche pari à 100 $ sur bt_or, contre-pied Nasdaq, repli 4 indices, mélanges → **ne tient pas** (ruine 72-90 % à cause du lot minimum) ; poche pari repli S&P + Russell à 14 fois la poche → **presque** (ruine 15 %, ×5 6 %, preuve mince : 107 trades) → en démo (`pari_opt`).

# Avis pour Baptiste — 17/11/2026 (Fable, recherche large, PRIORITES 17/11 11 h 20)

**Ajout du 17/11 au soir — « savoir en direct quel moment arrive » (PRIORITES 17/11 12 h 15), 4 pistes testées, aucune ne tient :**
- **Modèle à plusieurs indices** (71 indices) : 48 à 55 % de bonnes réponses hors échantillon, autant qu'en répondant toujours « calme » ; en $, pas mieux que la sélection actuelle.
- **Les autres marchés annoncent l'or** : seulement 5 minutes d'avance, pour 0,1 bp attendu contre 0,46 bp de spread. **Bascule rapide** : +374 $ (t = 0,4), le hasard fait aussi bien 1 fois sur 4, et 73 % des bascules sont ratées.
- **IA qui juge à l'aveugle** (180 moments anonymes, 2 modèles) : 48 à 52 % contre 46 % pour « toujours calme », mais 51 % pour la règle bête « les 4 heures d'avant se répètent ». Elle ne reconnaît pas l'aller-retour (5 à 7 sur 36).
- **Ce que ça veut dire** : la seule chose prévisible est « calme ou agité » (déjà dans le robot depuis la v11). Le sens et le type d'une journée agitée ne se devinent pas d'avance avec ces données ; même en trichant, le choix de famille ne rapporterait que +338 à +1 132 $ sur 9 mois.
- **Robot v15 bien installé sur le PC** ; `rebond_nas_opt` n'a pas encore eu de signal.

1. **Recherche large finie : 12 pistes, 14 bancs, tous en walk-forward avec spread réel et correction pour essais multiples.** Une seule vraie découverte : **le contre-pied d'une grande journée sur le Nasdaq** (+28 bp par trade sur 385 trades du courtier depuis 2018, t = 2,9, toutes les années positives).
2. **Robot v15 publié** (essais OK) : il ajoute `rebond_nas_opt` (Nasdaq, taille minimale, hors totaux du test ; arrêt écrit d'avance : somme < −1 000 bp, ou moyenne négative après 60 trades). Le filtre de tendance du relais, qui ne tenait pas, est retiré. La sélection du test n'est pas touchée.
3. **Le repli d'indices tient toujours, mais reste petit** : +2 % par an à 20 % du compte par trade (pire baisse −13 %), sur les 4 indices américains seulement ; aucune variante ne le bat.
4. **Alerte sur `bt_or`** : sur 4 ans, la mécanique fait −6 R puis +160 R : elle ne gagne que pendant la hausse de l'or de 2024-2026, et ne marche sur aucun autre marché. À garder petit.
5. **Presque** : suivre les spéculateurs sur l'euro (COT, t = 1,7), acheter le S&P quand le VIX bondit. **Ne tient pas** : pause annonces, Silver Bullet, COT sur l'or, coupe-circuit, paire or/argent, or contre dollar et taux, saisonnalités, momentum croisé, `bt_or` diversifié.

## Tout ce qui a été testé : tient / presque / ne tient pas

Règle du verdict, fixée avant : « tient » = gagne hors échantillon (walk-forward, spread réel) et résiste à la correction pour essais multiples ; « presque » = gagne hors échantillon mais preuve trop mince ; sinon « ne tient pas ».

| Piste | Verdict | Chiffres clés | Suite |
|---|---|---|---|
| Astra 23/11 : détecteur de régime horaire (oracle, veto de coût A/c < 4, prolongement après retournement, tenue du prix après CPI/emploi ; contrat figé avant, `banc_astra.py`) | ne tient pas | Oracle = bruit (mélangé +4 622 R contre +4 632) ; veto jamais actif (A/c médian 51) ; prolongement +89 R contre le 50/50 mais placebo p 0,13, et « tendance seule » fait +170 R ; annonces −9 R (p 0,51) ; SPA p 0,53 | recherche du détecteur arrêtée |
| Lot B : deviner le type de marché en direct (7 pistes : HMM, mesures tendance/bruit, méta-étiquetage, bandit, régime commun or/indices/dollar/taux, VIX/annonces/COT du matin, sortie adaptative ; 181 réglages, `regime_socle.py`, `banc_regime_p1..p7.py`) | ne tient pas | À risque égal, aucune ne bat « tout en marche » (+87 / +324 u en 2022-24 / 2024-26) ; meilleur p corrigé 0,26 ; 3 faux positifs à exposition égale (pistes 3, 5, 6) | — |
| Panier acheté seulement, risque égal (comptant) | **tient** (placement) | +7,6 % par an, pire baisse −12 %, 2016-2026 | registre papier |
| Repli d'indices américains (RSI 2 j < 10) | **tient** (petit) | +20 bp par trade, t = 2,3 ; +1,6 % par an à 20 % du compte | en direct (`repli_ind`) |
| `bt_or` (mécanique BlockTrend sur l'or) | presque | +102 R au banc, mais 8 mois négatifs sur 16 | en direct |
| Suivre ce qui marche (5 jours) | presque | +1 648 $ hors éch., p = 0,06 ; +633 $ seulement face à la tendance seule (t = 0,4) | sur le papier |
| Le marché choisit / les deux à la fois / filtre de tendance | ne tient pas | t = 0,9 / 1,0 / −0,2 | filtre retiré de la v15 |
| Retirer `elan_m15` | ne tient pas | −708 $ sur 15 mois | — |
| ORB 15 h 30 (Nasdaq, S&P, Dow), FVG, chasse aux stops d'Asie | ne tient pas | positif 1re moitié, négatif 2de | — |
| Sorties plus rapides aux retournements (7 sorties) | ne tient pas | toutes moins bien sur la 2de moitié | — |
| Mise selon la volatilité (×2 / ×0,5) | ne tient pas | médiane −78 $ en walk-forward sur 36 réglages | — |
| Détecteur d'aller-retour, règles de retour à stop court | ne tient pas | 38-50 % hors échantillon ; −0,13 R par trade | — |
| Compression puis cassure (or, Nasdaq, argent, EURUSD, BTC) | ne tient pas | pas mieux qu'une cassure normale | — |
| BlockTrend sur BTC et ETH | ne tient pas | nul quelle que soit la sortie | données seulement |
| Or/argent en paire (écart qui revient) | ne tient pas | M5 15 mois : +854 bp hors éch., t = 0,5, p = 0,78 (le spread de l'argent, 5 bp, mange tout) ; journalier 24 ans : −11 581 bp | — |
| « Silver Bullet » (fausse sortie de la fourchette 9-10 h New York, or et 3 indices) | ne tient pas | 96 réglages, 15-17 mois : somme des 4 marchés −193 bp hors éch. (t = −0,3), p = 0,61 ; la version inverse perd aussi | — |
| Repli d'indices élargi (12 marchés, sorties, stops, seuils) | **tient** sur les 4 indices américains seulement ; aucune variante ne bat la règle de base | 2000-2026 : Nasdaq +42 bp par trade (t = 3,0), S&P +27, Dow +21, Russell +33 ; p = 0,003 contre ne rien faire, p = 0,54 contre la base. Attendre +2 % par an (pire baisse −13 %) à 20 % du compte par trade, +4 % (−32 %) à 50 %. Europe, Japon, métaux : rien | garder la règle actuelle |
| `bt_or` rendu plus régulier (autres marchés, risque égal, mise selon l'ATR) | ne tient pas | Seul l'or gagne (+102 R, t = 2,2) ; Dow −64 R, S&P −37, euro −30. Portefeuille de 6 marchés : +12 R contre +103, autant de mois négatifs (6 sur 15). Alerte : sur 4 ans (H1), l'or fait −6 R puis +160 R : la mécanique ne gagne que pendant la hausse de 2024-2026. Mise selon l'ATR : +103 contre +82 R, un peu mieux mais non prouvé (t 0,6) | `bt_or` reste « presque » |
| Momentum croisé entre actifs (acheter les plus forts, 36 réglages, 2004-2026) | ne tient pas | +3,6 % par an contre +6,3 % pour le panier acheté seulement, à risque égal (différence t = −2,2) ; p = 0,91 | — |
| COT à contre-courant sur l'or (positions des spéculateurs, 72 réglages, 2003-2026) | ne tient pas | −2 030 bp hors éch. (t = −0,4), alors qu'acheter et garder l'or fait +12 230 bp à exposition égale | — |
| COT sur 7 autres marchés (576 réglages) | presque, sur l'euro seulement, et dans le sens inverse : **suivre** les spéculateurs | Euro : +6 349 bp hors éch. sur 2006-2026 (t = 1,7), positif sur les deux moitiés, p = 0,009 parmi ses 72 réglages mais p = 0,10 sur les 576 ; 57 trades seulement, portage de nuit non compté. Argent, S&P, Nasdaq, Dow, yen, bitcoin : rien de sûr | à suivre sur le papier (un signal par semaine) |
| Pause autour des annonces US fortes (emploi, inflation, Fed ; 24 réglages) | ne tient pas | 4 règles : +672 $ hors éch. (t = 1,2, p = 0,21), mais seulement +8 $ viennent vraiment des jours d'annonce : le reste est un effet de décalage des trades. Le calendrier Helious n'a pas d'historique : dates reconstruites à la main | — |
| Coupe-circuit journalier, pause après pertes, refus si spread trop cher (10 réglages) | ne tient pas | Meilleur (pause 24 h après 3 pertes) : +446 $ hors éch., t = 0,5, p = 0,39 ; un tirage au hasard fait aussi bien 1 fois sur 9 | — |
| Or contre dollar et taux réels US (14 réglages, 2006-2026) | ne tient pas | −13 856 bp hors éch. (t = −1,7) ; le lien existe le jour même mais n'annonce rien pour le lendemain | — |
| **Contre-pied d'une grande journée sur le Nasdaq** (amplitude > 1,5 fois la médiane de 20 jours → position inverse le lendemain, une journée) | **tient** (nouveau) | 1993-2026 : +10,8 bp par trade hors éch., t = 2,3, p < 0,001 sur 18 réglages. Revérifié sur les bougies du courtier 2018-2026 : 385 trades, +28 bp par trade, t = 2,9, toutes les années positives ; surtout les achats (+39 bp, t = 3,0), ventes faibles (+15 bp, t = 1,0). Sur l'or c'est l'inverse (−13 bp) | **sur la démo dans la v15 : `rebond_nas_opt`**, hors test |
| Acheter le S&P quand le VIX bondit (> moyenne 20 j + 2 écarts), 5 jours | tient de justesse | +97 bp par trade hors éch., t = 2,0, p = 0,007 ; mais 184 trades en 34 ans, et c'est un cousin du repli d'indices | sur le papier (le robot ne voit pas le VIX) |
| Mise inverse à la volatilité (or, indices) | ne tient pas | rendement/creux 3,1 contre 4,0 pour la mise fixe | — |
| Saisonnalités : jour de la semaine, début/fin de mois, heures de Londres et New York, nuit contre jour (264 réglages) | ne tient pas | rien ne bat « être acheteur le même temps » ; le lundi sur Nasdaq/S&P est « presque » (+12,6 bp, t = 1,6 à 2,2, p = 0,19 après correction) | — |
| Bascule rapide entre tendance et retour en cours de journée (36 réglages, 18 mois) | ne tient pas | +374 $ hors éch. (t = 0,4, p = 0,84) ; une alternance au hasard fait aussi bien 1 fois sur 4 ; 73 % des bascules sont ratées et coûtent −2 689 $ ; le spread mange 54 % du gain brut | — |
| Les autres marchés annoncent l'or (Nasdaq, S&P, Dow, argent, euro, bitcoin ; décalages de 5 min à 2 h) | ne tient pas | Une avance existe à 5 minutes seulement (corrélation +0,02, soit 0,1 bp attendu contre 0,46 bp de spread) et disparaît dès 15 min. Règle d'entrée : +230 bp hors éch., t = 0,4, p = 0,96. Filtre « les autres confirment » sur la tendance : −865 bp par rapport à sans filtre | — |
| Modèle à plusieurs indices (71 indices : or, indices US, argent, euro, heure, jour, annonces ; 30 réglages) pour prédire tendance / calme / aller-retour à 9 h, 12 h, 15 h 30 | ne tient pas | Bonnes réponses hors éch. : 51 %, 55 %, 48 % contre 54 %, 53 %, 44 % en répondant toujours « calme ». En $ : +232 / +150 / +68 contre +247 / +195 / −303 pour la sélection actuelle (p = 0,53) ; la tendance seule fait mieux à 9 h et 12 h. Même en trichant (type connu d'avance), le gain n'est que de +338 à +1 132 $ | — |
| Une IA qui juge en direct (180 moments anonymes, sans date ni prix réels, 2 modèles de langage à petit coût, à l'aveugle) | ne tient pas | 52 % et 48 % de bonnes réponses (54 % en vote à deux) contre 46 % en répondant toujours « calme »… mais la règle bête « les 4 heures d'avant se répètent » fait 51 % sur les mêmes moments. Aller-retour reconnu 5 à 7 fois sur 36. L'IA ne voit que la persistance du calme, que le robot utilise déjà | pas de journal en direct |
| `bt_or` comme thermomètre : pause des règles de retour quand le panier gagne, mise ×1 ou ×2 sinon (24 réglages, 15 mois) | ne tient pas | +115 $ hors éch. (t = 0,1) ; −272 $ face aux mêmes règles à mise égale ; p = 0,38 ; le hasard fait mieux 2 fois sur 3. Sur 4 ans en H1, signe favorable mais t = 1,2 | — |
| Allocation par régime connu en direct : poids par règle selon calme/agité × heure × état du panier `bt_or` (18 réglages, rétrécissement, 17 mois, `banc_alloc.py`) | ne tient pas | +104 $ hors éch. sur 12 mois (t 0,1) ; +72 $ contre la sélection à mise égale (p 0,29) ; variantes « calme » −1 829 $ sur l'historique ; triche +14 668 $ |
| Jumeau de `bt_or` qui encaisse petit à petit, ajouté par-dessus (10 sorties × mise 0,5 / 1 / 2, M5 18 mois et H1 4 ans, `banc_jumeau.py`) | ne tient pas | Gain / pire baisse : 6,33 au mieux contre 6,34 (M5), 3,79 contre 3,66 (H1) mais inversé hors éch. (4,43 contre 7,67) ; p 0,87 ; miser plus sur `bt_or` fait aussi bien |
| Portefeuille `bt_or` + compléments (repli 4 indices, rebonds Nasdaq et S&P, Fed-DAX, VIX, achat seul) : parité de risque, moyenne-variance rétrécie, Kelly ; walk-forward par semestre, 08/2022-11/2026 (`banc_mix.py`) | presque | À risque égal hors éch. : +26 %/an contre +18 % pour `bt_or` seul, 20 % de mois négatifs contre 35 %, mais p 0,57 ; corrélations −0,06 à +0,14 ; 1 méthode sur 3 fait moins bien |
| `bt_or` qui ajoute plus fort (tailles 1-2-3 ou 1-1,5-2, 3 / 5 / 7 positions, ajout seulement si gain > 1 R ou ATR en hausse ; 36 réglages à risque égal, `banc_bt_plus.py`) | ne tient pas | M5 18 mois : 8,62 contre 6,34 de gain / pire baisse ; H1 4 ans : 2,52 contre 3,66 ; p corrigée 0,42 à 0,95 ; hors éch. bon en M5, mauvais en H1 |
| Plus de paniers `bt_or` : toutes les heures / 2 h / 4 h, reprise immédiate, 2 ou 3 paniers par côté, échelles rapide et lente (22 réglages, M5 18 mois et H1 4 ans, `banc_freq.py`) | ne tient pas | Corrélation 0,92 à 0,99 avec `bt_or` : même exposition en plus gros. Gain / pire baisse à risque égal : 6,88 au mieux contre 6,34 (M5), 3,56 contre 3,66 (H1) pour 2 paniers ; p corrigée 0,83 / 0,27 ; hors éch. 1,17 contre 3,51 (M5), 5,62 contre 7,67 (H1) | — |
| Mécanique de panier de tendance en JOURNALIER sur 14 marchés (EMA 50 / 100 / 200 j, pyramide 1 ou 3, stop 2 ou 3 ATR ; 24 réglages, portage compris, `banc_tend_actifs.py`) | ne tient pas (aucun actif seul) ; portefeuille : trop petit | Portefeuille : +3,0 R par an contre +1,9 pour acheter-et-garder (t 1,4), moins bien que lui depuis 2016 ; +3,4 % par an à pire baisse −30 % ; 51 % de mois négatifs ; corrélation −0,03 avec `bt_or`. BTC +0,58 R par panier (t 2,7) mais pas mieux qu'acheter. Le portage coûte 2 à 3 R par an | — |
| Viser +10 % par mois par la taille de mise (6 montages, 5 000 tirages, `banc_dix.py`) | pas atteignable honnêtement | Mise × 2,5 : médiane +10,0 % par mois en mesuré, +2,7 % en prudent, arrêt 34 % à 24 mois ; levier appris sur une moitié et rejoué sur l'autre : ≈ +2,3 % par mois. Meilleur compromis : plan −50 % (+7,7 % / +2,4 %, arrêt 5 % à 12 mois) | plan −30 % gardé ; robot v22 inchangé |
<!-- fin tableau recherche large -->

## Avis précédent (17/11, 13 h)

0. **Test (relais, vendredi 20 h 10)** : trades fermés de la sélection : total **+390,90 $** (vendredi +778,00 $ sur 98 trades) ; non encaissé +5,70 $. Critères à cette heure : 1 tenu, 2a tenu (+495 $), 2b non (mardi calme −104 $), 3 non (+0,99 $ ± 2,04 par trade), 4 non (compte simulé à −287 $ jeudi). Verdict définitif après 23 h.
0 ter. **v22 installée à 15 h 50 (aucune erreur, aucune position fermée par la mise à jour) : `bt_or_serre_opt`** : `bt_or` dont le stop suiveur se resserre à 0,5 R une fois +3 R gagnés (seul réglage du banc X qui gardait le même total en protégeant mieux). Pour les données, hors test, arrêt à −20 R.
0 bis. **v21 installée à 14 h 03, toutes les positions reprises (dont le panier `bt_or` de 3 positions) : `bt_or_plus_opt`** (mêmes entrées et même suiveur que `bt_or`, ajouts de 1, 2, 3, 4, 5 × 0,01 lot), pour les données, hors test, arrêt à −20 R. Au banc : meilleur sur 18 mois, moins bon sur 4 ans.
1. **« La bonne famille au bon moment », version rigoureuse** (`banc_famille_wf.py` : 48 réglages, 10 mois de test glissants, réglage choisi sur les 6 mois d'avant). Une seule piste passe : **suivre ce qui marche sur 5 jours** (famille à double mise si elle a gagné sur 5 jours, coupée sinon) : +1 648 $ hors échantillon contre −71 $ pour la sélection actuelle, 7 mois gagnés sur 10, p = 0,06 après correction pour 48 essais.
2. **Mais la preuve est mince** : l'essentiel du gain vient de deux choses simples — couper les règles de retour, qui perdent sur 15 mois (−1 594 $), et miser double. Face à la tendance seule à mise égale, l'avantage tombe à +633 $ (t = 0,4) : pas prouvé. Je la garde donc **sur le papier** (`suivi_tendance.py`, sur les vrais trades), pas en position réelle `_opt`.
3. **Les trois autres ne tiennent pas** : le marché choisit (+627 $, t = 0,9), les deux à la fois (+439 $, t = 1,0), filtre de tendance (−152 $).
4. **Retirer `elan_m15` n'aide pas** : −708 $ sur 15 mois par rapport à la sélection actuelle (5 mois gagnés sur 10). Sa perte de cette semaine ressemble à de la malchance, pas à un défaut.
5. **Dépôts GitHub : analyse finie** (`SKILLS_TRADING.md` : 7 dépôts, un tableau chacun ; `APIS.md` ; `ECC.md`). ORB, FVG et chasse aux stops d'Asie : déjà testés, rien. Un des dépôts a lui-même rejoué 27 566 trades de ce style : −0,18 R par trade après coûts. 8 sources gratuites sans clé répondent (calendrier Helious, positions COT sur l'or depuis 1986, taux US…). À tester ensuite, dans l'ordre : pause autour des annonces US fortes, « Silver Bullet » 17-18 h, COT à contre-courant sur l'or, coupe-circuit journalier.
6. **Robot v15 (écrite par le relais, filtre de tendance en `_opt`) : je conseille de ne pas la publier telle quelle** — ce filtre est la piste 4, qui ne tient pas en walk-forward (−152 $). Le test de la semaine n'est pas touché.

## Avis du relais (17/11, 11 h, passage 46)

1. **« La bonne famille au bon moment », 4 pistes testées sur 15 mois d'or : une seule a un signe constant.** *Suivre ce qui marche* : quand les règles de tendance ont gagné sur les 3 derniers jours, elles gagnent ensuite +9 à +14 $ par jour ; quand elles ont perdu, −2 $. Vrai sur les deux moitiés, mais pas assez net pour être une preuve (t ≈ 1).
2. **Les trois autres ne tiennent pas** : basculer en « retour » après une fausse cassure (−455 $ contre +1 315 $ sans bascule), mélanger tendance et retour (le retour perd sur 15 mois, donc il tire le total vers le bas), filtrer par la tendance de fond (bon sur la 1re moitié, mauvais sur la 2de).
3. **Sur 15 mois, ce sont les règles de retour qui perdent**, pas celles de tendance : lundi et mardi sont deux jours d'aller-retour, pas la règle générale. Sans `elan_m15` : moitié moins de gain, mais trois fois moins de creux (−416 $ contre −1 401 $).
4. Cette piste est suivie « sur le papier » à partir des vrais trades de la démo (pas de position en double) : elle n'aurait **pas** évité la perte de mardi (les 3 jours d'avant étaient encore positifs grâce au 12/11) ; elle met la tendance en pause mercredi. Le test de la semaine n'est pas touché.
5. Dépôts GitHub (public-apis, ECC, skills de trading) : lecture en cours par deux sous-agents, résultats au prochain point.

**Ajouts de 11 h 40 :**
- **Moins de mois négatifs : une piste tient.** Ajouter le repli d'indices américains à côté de l'or : les 8 mois négatifs de l'or sont tous des mois positifs du repli (corrélation −0,11). À 20 000 $ de marché par trade : 8 → 2 mois négatifs sur 16 et un total plus haut. Prudence : ces 15 mois ont été exceptionnels pour les indices (+78 bp par trade contre +30 d'habitude) ; avec un repli « normal » on passe plutôt de 8 à 5 mois négatifs.
- Premier trade du repli d'indices en direct : achat du Dow (0,1 lot) cette nuit à 0 h, ouvert.
- **Cassure de l'ouverture de Wall Street (ORB, 15 h 30)** : testée sur le Nasdaq 15 mois (18 réglages) : un peu positive sur la 1re moitié, négative sur la 2de. Non retenue ; S&P et Dow à confirmer quand le pont enverra leurs bougies M5.

**Ajout de 12 h — réagir plus vite aux retournements :** 7 sorties testées sur les deux règles de tendance (sortie sur l'extrême de la dernière heure, sur inversion de l'élan, stop ramené à l'entrée, stop suiveur, retournement). Toutes embellissent la 1re moitié des 15 mois et font moins bien que la sortie simple sur la 2de : rien ne tient. Les ventes prises à contre-pied lundi sont le coût normal d'une règle de tendance un jour d'aller-retour, pas un défaut de sortie. Pas de variante `_opt` ajoutée.

**Test de la semaine, mardi 12 h 15 (trades fermés)** : lundi −30,99 $ (47 trades), mardi −48,04 $ (38 trades) ; total **−79,03 $**. `elan_m15` fait −57,98 $ sur 8 trades, `cassure_m15` −15,58 $ sur 1 ; les règles de retour sont à zéro près (`fcassure_m1` −7,10 $ sur 61). **Le critère 4 est déjà perdu** : le compte simulé de 100 $ est à ≈ 21 $, sous le plancher de 70 $. En cours : panier `bt_or` (vente 3 851,07) à −10 $, Dow à −35 $.

## Avis du relais (17/11, 6 h 15)

0. **Bonne famille au bon moment, 1re étape** : sur 15 mois, enlever `elan_m15` améliore la sélection (+6 078 $ contre +5 680 $). Filtrer les règles de tendance par la tendance de fond (20 h) les fait passer de −1 289 $ à +453 $ hors échantillon : prometteur, pas prouvé. Variantes `_opt` prêtes (v15, non publiée) ; Fable reprend ce point.
0. **Dépôts GitHub, 1re étape** : la cassure d'ouverture (ORB) de `day-trader-skill`, testée sur NAS100+, SP500+ et DJ30+ (15 mois, 4 réglages), ne gagne rien (≈ 0 R par trade, seconde moitié négative 10 fois sur 12). Leur outil le dit lui-même. Le détail est dans `labo/SKILLS_TRADING.md` ; prochain dépôt au passage suivant.
0. **Test, mardi 6 h 10** : sélection lundi −30,99 $ (47 trades), mardi déjà −20,88 $ (25 trades), dont `elan_m15` −23,75 $ sur 2 ; total −51,87 $. Témoin −12,41 $ mardi. Une erreur isolée à 2 h 39 (accès refusé à un fichier sous Windows) ; le robot a continué. Panier `bt_or` ouvert, pont à l'heure.

1. **Robot v14 en marche depuis 15 h 23** : désormais, toutes les positions survivent aux mises à jour. C'est vérifié au passage v13 → v14 : le témoin, `fcassure_m1` et le panier `bt_or` ont été repris ; une seule position, ouverte pendant la minute de bascule, a été fermée (+0,47 $).
2. **Nouveau sur la démo, hors totaux du test** : `bt_crypto` (BTC et ETH, taille minimale) et les deux règles d'aller-retour `retour_court_ar` et `retour_strict_ar`. Leurs règles d'arrêt sont écrites d'avance. Le banc ne les soutient pas (BTC/ETH nuls, retour −0,13 R) : c'est pour avoir des données en direct, comme tu l'as demandé.
3. **Sorties de BlockTrend** : garde le stop suiveur large ; encaisser plus tôt coûte (or : +102 R contre +64 R pour une prise partielle à +1 R).
4. **Détecteur d'aller-retour à 75 %** : introuvable hors échantillon (38-50 %). Fable reprendra mercredi la piste « perdre moins ces jours-là ».

0. **Mise selon la volatilité et mois négatifs (banc Z)** : en walk-forward, la mise ×2/×0,5 n'est **pas prouvée**. Sur 36 réglages, ceux qu'on aurait choisis sur la 1re moitié perdent 1 200 à 1 500 $ sur la 2de, et la médiane fait −78 $. Ton réglage (5 j) y fait +518 $, mais c'est un bon tirage parmi d'autres : je ne le mets pas sur la démo. Les mois négatifs viennent surtout de `bt_or` (4 sur 6). Aucun frein n'atteint ton objectif : le meilleur (mise ÷2 après une perte sur 20 jours) passe à 5 mois négatifs mais coûte 23 % du total. Reste à essayer : des pièces décorrélées (Fable, mercredi).

| mois | 25-08 | 09 | 10 | 11 | 12 | 26-01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | total | mois<0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v11, mise fixe | −125 | +808 | +1068 | −57 | +287 | +2625 | +192 | +1841 | −638 | −176 | +958 | −592 | +1597 | −1062 | −71 | −19 | +6635 | 8 |
| mise vol ×2/×0,5 | −50 | +812 | +1702 | −91 | +128 | +3434 | +307 | +3217 | −845 | +173 | +571 | −195 | +1966 | −1033 | −164 | +140 | +10070 | 6 |
| vol + frein 20 j | −50 | +615 | +1702 | +37 | +84 | +2992 | +307 | +2130 | −810 | +19 | +174 | −144 | +1658 | −960 | −82 | +108 | +7779 | 5 |

## Avis précédent

0. **Pont revenu à 6 h 57, v11 installée et en marche** ; marché calme ce matin, donc la sélection du test est en pause et seul le témoin trade. Le test compte les trades fermés depuis lundi 0 h.
0. **Aller-retour, étape (a)** : sur 15 mois, 14 % des journées de l'or sont des allers-retours. On ne les reconnaît sûrement qu'en fin de journée (après 17 h Paris : 1 fois sur 2). Avant, le détecteur se trompe 3 fois sur 4, et 4 signaux sur 10 tombent un jour de tendance. Étape (b) ensuite : une règle de retour assez prudente pour survivre à ces erreurs.
0 bis. **Détecteur d'aller-retour à 75 % : introuvable.** Les réglages qui atteignaient 75 % sur la première moitié tombent à 38-50 % sur la seconde, sur 4 à 8 jours seulement. Une règle de retour à stop court perd aussi : −0,13 R par trade, et +0,06 R même les vrais jours d'aller-retour. Piste suivante : y perdre moins (couper les règles de tendance quand le signal de fin de journée s'allume) plutôt que d'y gagner.
0 a. **v12 installée à 11 h 24, panier `bt_or` survivant** (repris par le robot, vente 3 851,07 toujours ouverte) ; les 2 petites positions du moment ont été fermées à la mise à jour (+0,58 $ au total).
0 a bis. `bt_crypto` et les sorties : au prochain passage. Rappel honnête : au banc (passage 24), la mécanique BlockTrend ne gagnait rien sur BTC et ETH ; sur la démo, ce sera donc pour les données, hors test.
0 a ter. **v13 prête** : toutes les positions survivront aux mises à jour (le nom de chaque position voyage dans les centimes de son stop). Je la publie quand les 2 petites positions ouvertes à 11 h 30 seront sorties, pour ne pas les couper.
0 a quater. **Sorties de BlockTrend testées (banc X, or/BTC/ETH, 12 réglages)** : rien ne bat le stop suiveur actuel. Prendre la moitié à +1 R fait passer l'or de +102 R à +64 R, un objectif à +2 R à +77 R. Le gain vient de quelques très gros paniers, et toute sortie précoce les coupe. Sur BTC et ETH, la mécanique est nulle quelle que soit la sortie.
0 a quinquies. **Réglage conseillé pour TON BlockTrend (tu décides)** : garde le stop suiveur large, sans prise partielle ni objectif. Si tu veux sécuriser les +5 686 $, le seul réglage gratuit au banc est de **resserrer le suiveur à 0,5 R seulement au-delà de +3 R** (même total, pas mieux). `bt_crypto` est prêt dans la v13 (données seulement) ; publication automatique dès que les positions du test en cours sont sorties.
0 b. **10 h 15** : panier `bt_or` toujours ouvert, v12 toujours en attente. Ta demande « réagir plus vite aux retournements » est notée : une idée à la fois au banc, puis en variantes `_opt` sur la démo, publiées avec la v12.
0 c. **Test, lundi à 11 h 10** : sélection fermée = 6 trades, −11,25 $ (`elan_m15` −11,95, `fcassure_m1` +0,34 sur 4, `exces_m1` +0,36) ; témoin −31,01 $ sur 51. Panier `bt_or` toujours ouvert (v12 en attente). Pont à l'heure.
0 bis. **public-apis (`labo/APIS.md`)** : Helious donne gratuitement, sans clé, le calendrier des annonces (heure, importance, prévu/publié) → on pourra tester « couper le robot autour des annonces fortes ». Goldprice.dev répond aussi ; TradingCalendars demande une clé (inutile pour l'instant).
0 ter. **Anti-secrets** : `labo/verif_secrets.py` vérifie chaque commit (clés, jetons, mots de passe, numéro de compte) ; idée tirée d'ECC, détails dans `labo/ECC.md`.
1. **Robot v11 publié** (pause des petites règles quand l'or est calme) : essais OK, aucun panier ouvert ; ton PC l'installera au rallumage lundi.
2. Le test de la semaine 16-20/11 démarre lundi 0 h avec les critères fixés le 15/11 ; bilan vendredi soir en tête de ce fichier.
3. Jusqu'à mercredi 16 h, passages courts : suivi du test et une petite étape à la fois sur public-apis, ECC et les dépôts de trading.

## Avis précédent (passage 43)

1. **Comment le robot reconnaît le calme** : il mesure de combien l'or bouge en moyenne d'une heure à l'autre sur les 24 dernières heures, et compare à sa valeur habituelle des 60 derniers jours ; en dessous de la médiane = calme. Recalculé chaque heure : il faut quelques heures de mouvement pour repasser en « agité ».
2. **Le calme avant le mouvement (compression puis cassure) : testé, non.** La cassure d'une fourchette très serrée (4 h, 8 h, 24 h) ne vaut pas mieux que celle d'une fourchette normale, plutôt moins : après un long calme, la première sortie est souvent fausse. Vérifié aussi sur le Nasdaq, l'argent, l'EURUSD et le BTC : rien non plus.
3. **Spread heure par heure** : 0,20 $ à toute heure, calme ou pas ; il n'y a pas d'heure moins chère. Un calme dure en moyenne 1 jour (le plus long : 25 jours).
4. **Portage** : je ne vois pas les swaps du courtier. Il faudrait que le pont ajoute `swap_long` et `swap_short` par symbole dans `etat.json` (à demander côté PC).
5. La règle reste « au calme, ne rien faire » ; la version 11 du robot (pause de ses petites règles quand l'or est calme) est écrite et testée, je la publie lundi à la réouverture. J'attends les règles de tes amis pour les tester.

## Robot sur la démo : résultats en direct par hypothèse (0,01 lot, essais non prouvés) — au 13/11 20 h 13 (Paris)

| Hypothèse | Trades fermés | Gain moyen après spread | Marge d'erreur (1 écart) | Décision |
|---|---|---|---|---|
| hasard_m1 (témoin) | 367 | −0,30 $ | ± 0,16 $ | référence |
| fcassure_m1 | 108 | +0,16 $ | ± 0,22 $ | continue jusqu'à 300 trades |
| exces_m1 | 16 | +1,32 $ | ± 1,82 $ | continue |
| elan_m15 | 15 | +3,08 $ | ± 3,52 $ | continue (banc 15 mois : −0,16 $) |
| cassure_m15 | 5 | +8,63 $ | ± 9,04 $ | continue |
| exces_m5 | 4 | +4,16 $ | ± 4,79 $ | continue |
| midi_agite (candidat) | 1 | −0,06 $ | inconnue | arrêt : < −0,50 $ après 60 trades ou −60 $ |
| repli_ind (repli d'indices) | 0 | — | — | arrêt : somme < −1 500 bp, ou moyenne < −20 bp après 60 trades |
| bt_or (mécanique BlockTrend) | 0 panier valable | — | — | arrêt à −20 R cumulés ou moyenne < −0,3 R après 40 paniers |
| elan_m1, retour_m1 | 322 et 279 | −0,03 $ et −0,55 $ | ± 0,18 $ | éteints (versions 8 et 7) |

## Candidat prouvé au banc, en direct depuis la version 9 : repli d'indices (mécanique BlockRange)

| Réglage | 2000-2015 | 2016-2026 | À 20 % du compte par trade |
|---|---|---|---|
| RSI 2 j < 10, au-dessus de la moyenne 200 j, sortie au-dessus de la moyenne 5 j | +20,3 bp par trade (519 trades) | +20,0 bp (454 trades, t = 2,3) | +1,6 % par an, pire baisse −6,5 % |

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
