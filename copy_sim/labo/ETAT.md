# État du laboratoire (réécrit à chaque passage) — après le passage 33, 14/11/2026 (0 h 25) — rythme : toutes les 2 h 30 — marché fermé jusqu'au lundi 16/11 0 h : **passages très courts le week-end** (une ligne au journal, sauf nouvelle priorité)

## Où j'en suis
- Outils : `donnees.py` (téléchargement Yahoo), `banc_tendance.py` (A), `banc_scalp_h1.py` (B), `banc_prime.py` (C),
  `registre.py` (papier). Tout tourne en moins d'une minute.
- Réfuté : tendance long/court en CFD (devises surtout) ; scalp simple à l'heure (élan / retour).
- Meilleur montage honnête du moment : panier acheté seulement (indices, or, argent, BTC, ETH) à risque égal ;
  ≈ +8 à +13 %/an depuis 2016 selon le levier, mais c'est la prime de risque en période de hausse, pas un avantage.
- Réfuté aussi (passage 2) : 30 règles simples de bougies sur XAUUSD en M1, M5, M15 avec le spread réel.
- Mesuré : l'or est le moins cher (spread 0,46 bp = 28 % du mouvement M1, 11 % en M5 ; EURUSD 323 %).
- Réfuté (passage 5) : grille de 47 628 combinaisons (or, argent, Nasdaq, S&P, DAX) : aucune à t > 2 au verdict.
- Réfuté (passage 9) : effets d'heure purs sur or et Nasdaq ; le « gain » de la réouverture de 1 h serveur est un
  artefact du spread (bougies en prix vendeur, spread enregistré faux à la réouverture).
- Réfuté (passage 13) : portage Hyperliquid (≈ 6 % par an brut, 4-5 % net = taux sans risque).
- Passage 17 (banc J, `banc_decoupes.py`) : aucune condition (semaine, heure, agitation, tendance) où `elan_m1` ou
  `exces_m1` gagne sur 3 mois.
- Passage 18 : ordres limites réfutés (un CFD sert l'achat limite à l'ask : pas d'économie de spread, sélection
  adverse en plus) ; concepts de liquidité (Asie, veille, niveaux ronds, FVG, VWAP) : rien à t > 2.
- Passage 19 : BlockFIFO, entrée seule = −0,50 $ à 3 min (pire que le spread) : rien à sauver. Mécanique de
  BlockTrend sur l'or M5 15 mois : +166 R sur 269 paniers (t = 2,2, 22 % de gagnants, 75 % du gain dans 5 paniers),
  zéro sur le Nasdaq → candidat de régime n° 2 (`banc_blocktrend.py`).
- Passage 21 : modèles appris réfutés (banc N) ; « 1 % par jour » chiffré (banc O) : BlockTrend-or demanderait
  3,1 % par R → 41 % de chances de perdre la moitié du compte dans l'année.
- Passage 22 : critères multiples fixés d'avance (banc P) : zéro, 1 trade tous les 3 jours. Mélange de Baptiste
  (banc Q) : 96 % du gain vient de `bt_or`, les autres valent zéro et gagnent/perdent les mêmes jours.
- Passage 23 : **BlockRange refait** (`banc_blockrange.py`, `banc_blockrange_ohlc.py`, Yahoo jour 2000-2026, 5 indices) :
  +20 bp net par trade au réglage et au verdict (t ≈ 2,3), plateau sur 11 variantes ; petit (+1,6 %/an à 20 % du
  compte par trade). Premier montage qui passe les deux périodes. FTSE perdant.
- Passage 24 : repli d'indices confirmé sur les bougies D1 du courtier (NAS100+ +25 bp, SP500+ +40 bp) ; mécanique
  BlockTrend réfutée sur argent, BTC, ETH (et Nasdaq) : elle ne tient que sur l'or.
- Passage 26 (banc S, `banc_repli_plus.py`) : améliorer le repli d'indices : 54 réglages tous positifs mais le
  réglage ne rapporte rien en avance glissante ; 8 indices = même Sharpe, plus de gain et de risque ; or, argent,
  CAC, FTSE : non. Plafond réaliste +8 à +15 %/an pour −24 à −44 % de pire baisse. Règle du robot inchangée.
- Passage 27 (banc T, `banc_finmois.py`) : BlockFinMois refait. Indices : +125 bp depuis 2016 mais nul avant
  (règle de régime). Devises (RSI 2 j < 30 en fin de mois) : +12 à +14 bp sur les deux périodes, témoin +1 à +4.
- Passage 28 (banc T bis, `banc_finmois_fx.py`) : devises de fin de mois **réfutées** (14 paires, deux sens :
  −2 à −3 bp, comme le témoin). Le gain du passage 27 était un sous-groupe chanceux.
- Passage 29 (banc U, `banc_structure.py`) : signal M5 or filtré par la structure H1/M15 : rien à t > 2 ; le
  mieux = repli dans le sens de la structure H1, 2 h : +2 à +4 bp (t ≈ 1). Famille 4 faite.
- Passage 30 (banc V, `banc_sorties_fines.py`) : sorties fines sur l'or M1 : aucune ne crée de gain ; petit
  objectif = 78 % de gagnants et −0,30 $ par trade. Famille 6 faite ; reste la 3 (annonces économiques : trouver
  un calendrier historique NFP / CPI / FOMC sur internet, dates seulement, puis or M5 autour).
- Passage 32 : repli d'indices sur les D1 du courtier : effet américain (SP500+ et DJ30+ +40 bp, NAS100+ et
  US2000+ +25 bp ; GER40+, FRA40+, EU50+ ≈ 0 ; or rien). `JPN225+` n'existe pas. `GER40+` gardé jusqu'au direct.
- Passage 33 (banc W, `banc_repli_h4.py`) : repli d'indices en H4 sur NAS100+ : zéro. Rester en D1. Robot v10
  installé (13/11 22 h 42).
- 48 775 essais comptés (passage 11 : la règle du candidat ne marche à aucune autre heure, ni sur le Nasdaq ;
  passage 12 : cassure d'ouverture de Wall Street réfutée sur Nasdaq et or). Banc H (`banc_sorties.py`) : la sortie au temps 15 min est la meilleure pour le candidat ;
  dans le sens de la tendance de 20 h il fait +3,5 bp. Banc F : `banc_plateau.py`. Banc D : `banc_or.py` (données dans `mt5/donnees/`, poussées par le pont).

## À chaque passage, d'abord
`python3 donnees.py && python3 registre.py` puis recopier le tableau du registre dans AVIS.md.

## À chaque passage, ensuite (priorité de Baptiste du 11/11 18 h 15)
Lire `mt5/etat.json` (champ `robot` : version installée, en marche, dernier refus), `mt5/robot_journal.jsonl`,
`mt5/executions.jsonl`. Tenir dans AVIS.md le tableau **par hypothèse** : trades, gain moyen après spread, erreur
type. Couper ce qui perd nettement, garder ce qui tient, ne monter la taille que si direct ET banc concordent.
Le robot note `evenement` = ouverture / sortie (avec `hypothese`, `profit` en $ juste avant la fermeture, `raison`).
Pour changer le robot : modifier `mt5/robot/`, relancer les essais (voir JOURNAL passage 3), monter `VERSION` en dernier.

## Robot : version 10 publiée le 13/11 ≈ 23 h (`repli_ind` + `US2000+`, orphelines : un essai par minute) — vérifier `version_installee` = 10
- **Règle (Baptiste) : ne jamais publier de VERSION pendant qu'un panier `bt_or` est ouvert** (un changement de
  version ferme tout sauf les positions d'indices). Vérifier : dernière note `bt_or` de `robot_journal.jsonl` et
  `positions_robot` de `etat.json` (XAUUSD avec stop à ≈ 55-70 $ du prix = `bt_or`).
- `bt_or` : arrêt à −20 R cumulés ou moyenne < −0,3 R après 40 paniers ; cumul par les notes « sortie panier »
  (champ `R`). 1er panier (12/11, −0,94 $) coupé par la v7 : non compté. Aucun panier depuis. Heures d'entrée
  serveur : 03:05, 08:00, 08:30, 12:00, 15:45, 16:00, 16:30.
- `repli_ind` (`mt5/robot/repli_ind.py`) : NAS100+, SP500+, DJ30+, GER40+, lot minimal, RSI 2 j < 10 et > moyenne
  200 j, stop 2 ATR, sortie > moyenne 5 j ou 10 jours. **Arrêt : somme des trades < −1 500 bp ou moyenne < −20 bp
  après 60 trades** (champ `bp` des notes « sortie » ; pour une sortie au stop, calculer avec `executions`).
  À vérifier au prochain passage : notes « erreur » `repli_ind` (symbole absent ?), puis au premier trade le champ
  `notionnel` (ce que vaut un lot minimal). `analyse_robot.py` multiplie par 100 × lots (contrat de l'or) : faux
  pour les indices → lire le champ `profit`/`bp` des notes.
- `fcassure_m1` : couper à 300 trades s'il reste dans la marge du témoin (97 au passage 24).
- Candidat de midi étiqueté `midi_agite_f/_c`, `midi_calme_f/_c` ; mélange fixé = `midi_agite_f`.
- Fin de mois : devises réfutées (passage 28), ne rien publier ; indices = règle de régime, non ajoutée.
- **À faire ensuite** : (1) quand le pont revient : lire les D1 demandées (`dj_d1_5k`, `ger_d1_5k`, `jpn_d1_5k`,
  `fra_d1_5k`, `eu50_d1_5k`) pour connaître les noms valides ; ajouter Nikkei / EuroStoxx / Russell à
  `repli_ind.SYMBOLES` s'ils existent (pas CAC ni FTSE) ; version à publier seulement sans panier `bt_or` ouvert.
  (2) L'amélioration du repli d'indices est **faite** (banc S) : ne pas la refaire ; reste éventuellement l'entrée
  en H4/H1 (non testée, demander les H4 des indices au pont). (3) Recherche large restante : annonces économiques,
  structure M15/H1, sorties fines (voir section suivante) ; effet de fin de mois (BlockFinMois) sur indices avec
  `banc_repli_plus.ohlc()`.
- Ensuite : faire survivre `bt_or` aux changements de version ; BlockGrille, BlockFinMois ; tableau des paniers
  `bt_or` dans `analyse_robot.py`.
- Clone neuf : `mkdir data` avant `python3 donnees.py` ; essais du robot : copier `mt5/robot/*.py` dans un dossier
  temporaire, `PYTHONPATH=<dépôt>/copy_sim/forex python3 essais_robot.py` ; contrôle du texte :
  `lanceur_robot.controle_source`.

## Recherche large sur le scalp XAUUSD (PRIORITES 12/11 12 h 30 et 12 h 40) : où j'en suis
Fait : 1. ordres limites (banc K, réfuté) ; 2. concepts de liquidité (banc L, rien ; à creuser : cassure du range
d'Asie tenue 2 h, par sens) ; 5. modèles appris (banc N, réfuté ; `pip install scikit-learn` à refaire si absent).
**Nouveau (PRIORITES 16 h 55)** : stratégies à critères multiples (5 à 15 conditions) ; pour chaque candidat, tableau
« 1 % par jour » avec `banc_objectif.py`. Sous-agents autorisés (3-4 au plus, tâches bornées) : utile pour mener
annonces + structure M15/H1 + sorties fines en parallèle au prochain passage. **Reste, une famille par passage** : 3. annonces économiques (trouver un calendrier
historique sur internet : source d'idées et de dates seulement) ; 4. signal M1 filtré par la structure M15/H1 ;
5. modèles appris (scikit-learn s'il est installé, validation glissante, témoin à étiquettes permutées) ; 6. sorties
fines (stop suiveur, sortie partielle, retour au point d'entrée) ; chercher sur internet des règles exactes de scalp
or publiées et les refaire. Si `labo/IDEES_AMIS.md` apparaît : le tester en premier, tel quel.

## Pistes suivantes (par ordre)
1. **Résultats du robot** : `python3 analyse_robot.py` ; attendre ≈ 300 trades par hypothèse continue (≈ 30 h de
   marché) avant de couper ; couper alors ce qui est sous le témoin `hasard_m1` de plus de 2 erreurs types.
   Ajouter à `analyse_robot.py` le découpage par heure (`h_serveur` dans les notes ; serveur = Paris + 1 h).
   `ecart_midi_m5` ne trade que de 11 h à 14 h Paris : premiers trades le 12/11.
2. **Candidat de midi** (premiers trades le 12/11 de 11 h à 14 h Paris), noté `midi_agite` / `midi_calme` (robot v5).
   Arrêt `midi_agite` : moyenne < −0,50 $ après 60 trades ou −60 $ cumulés ; `midi_calme` : coupé si moyenne négative
   après 40 trades. Taille > 0,01 lot seulement après 100 trades `midi_agite` positifs (t > 1,5).
   Banc : agité +3,8 à +4,2 bp (t ≈ 3, 5 tranches sur 5), calme ≈ +0,7 bp. Régime au 12/11 3 h : calme.
2 bis. **Robot v6 à faire après 14 h (Paris)** : étiqueter aussi le sens de la tendance de 20 h (cours M5 contre sa
   moyenne de 240 bougies) : `midi_agite_fond`, `midi_agite_contre`, `midi_calme_fond`, `midi_calme_contre` (≤ 20
   caractères). Mélange fixé au passage 16 : agité × sens du fond, jugé sur les trades suivants. Couper `elan_m1` et
   `retour_m1` à 300 trades s'ils restent dans la marge du témoin (banc 18 000 trades : −0,19 $ et −0,14 $ = spread).
   PRIORITES 12/11 10 h 45 : combiner seulement des pièces qui ont un avantage seules.
3. **Nuit : passages courts** (rien de neuf en direct avant 11 h). Idées restantes : deux règles qui se confirment ;
   Autres robots de Baptiste (`mt5/autres/`) : lus aux passages 14 et 15, −33 906 $ fermés ; sous-ensembles gagnants
   = sens du marché ; « tendance à la vente seule » réfutée sur 20 ans. Rien à reprendre.
   Positions multiples : autorisées (PRIORITES 12/11 8 h 15) mais inutiles pour le candidat (JOURNAL passage 13).
   **À partir de 11 h : priorité à la lecture des trades `midi_*` et à la page de suivi.** Étiqueter dans le robot le sens du fond (v6) si le direct de
   midi donne assez de trades.
3 bis. **Étendre la grille** (`banc_grille.py`) : stops/objectifs dans la bougie, tendance de fond (M15/H1), deux règles
   qui se confirment, jour de semaine ; `NAS100+` en priorité (spread = 21 % du mouvement M1, moins cher que l'or).
   Demander plus d'historique par tranches (`debut`/`fin`) si le terminal en a.
4. Portage (Hyperliquid), effets de calendrier sur indices : après.

## MT5 démo (section ajoutée à MISSION.md le 11/11, commit 36b30f3)
- Cible : compte démo via le pont (`labo/mt5/consigne.json` → pont ; `etat.json`, `executions.jsonl`, `donnees/` ← pont).
- Le pont tourne depuis le 11/11 17 h 10 ; lanceur de robot présent (champ `robot` de `etat.json`), aucun robot installé.
- Demandes d'historique : 90 000 bougies passent, 200 000 non. Serveur = UTC+2. Bougies en prix vendeur.
- `consigne.json` : rien envoyé. Robot v1 en marche le 11/11 à 18 h 16 ; **v2 poussée ≈ 19 h** (8 hypothèses, ≈ 850 trades/jour, coût attendu ≈ 160 $/jour de démo) : vérifier `etat.json` → `robot.version_installee` = 2 (4 hypothèses XAUUSD, 0,01 lot, non prouvées).
- Indices : `NAS100+`, `SP500+`, `DJ30+`, `GER40+` (et variantes `ft+`).

## Robot
- v5 poussée le 12/11 ≈ 3 h 30 (v4 + étiquette de régime du candidat de midi) : vérifier `version_installee` = 5.
- Le compte démo porte aussi d'autres robots de Baptiste : juger le mien par `analyse_robot.py`, pas par le solde.
- Le terminal n'a pas de M5 avant juin 2025 pour l'or (demande 2024 : « aucune bougie »).
- La session redémarre souvent en plein passage : committer tôt ; plusieurs déclenchements peuvent arriver d'un coup
  (les traiter en un seul passage).

## Page de suivi (PRIORITES, entrée du 11/11 23 h)
`page_suivi.py` est tenu à jour (section « Autres robots du compte » ajoutée au passage 14). **Ne plus tenter de
publier depuis cette session** : l'outil attend une approbation que personne ne donne, puis la session redémarre
(passages 7, 8, 13). La conversation de suivi publie la page de son côté (vu à 7 h 52 le 12/11).

## Outils à ne pas utiliser d'ici
Publication d'Artifact et envoi de message à une autre session : ils attendent une approbation que personne ne
donne, puis la session redémarre (passages 7, 8, 13, 21). Passer par AVIS.md / ETAT.md dans le dépôt.

## Pièges notés
- `demandes_donnees.json` : le pont ne lit que les **20 premières** demandes ; retirer celles déjà servies (les fichiers restent).
- Yahoo : `range=max` → mensuel ; utiliser `period1/period2`. `query1` peut répondre « Too Many Requests », `query2` passe.
- Indices en 1 h : 7 barres par jour seulement, « 24 barres » ≈ 3,5 jours.
- Les Sharpe du banc C ne retranchent pas le taux sans risque.
