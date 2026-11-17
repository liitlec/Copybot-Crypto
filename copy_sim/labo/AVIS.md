# Avis pour Baptiste — 17/11/2026, 11 h (passage 46, reprise)

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

## Avis du relais (17/11, 6 h 15)

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
