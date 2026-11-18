# Avis pour Baptiste — 18/11/2026, matin (bt_or comme thermomètre de la tendance, PRIORITES 18/11 8 h 30)

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
<!-- fin tableau recherche large -->

## Avis précédent (17/11, 13 h)

0. **Test (relais, mercredi 11 h 10)** : sélection lundi −30,99 $, mardi −103,72 $, mercredi **+56,30 $** (32 trades) : total **−78,41 $**. Hors test : variantes calme +109,71 $, `retour_court_ar` −22,15 $ (il a rendu ses gains), `bt_crypto_btc` −36,88 $. Robot v20 sans erreur, panier `bt_or` toujours ouvert, pont à l'heure. Le relais finit à 16 h.
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
