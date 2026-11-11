# Priorités de Baptiste (à lire à chaque passage, après MISSION.md)

## 11/11/2026, 17 h 20 (Paris) : priorité au scalp sur XAUUSD
Baptiste veut que tu mettes en premier le **scalp sur l'or (XAUUSD)**, parce que les frais y pèsent moins, selon lui,
que sur les autres marchés. C'est sa priorité ; la méthode reste à toi, et la vérité aussi.

- Commence par **mesurer cette affirmation** chez son courtier : spread réel de XAUUSD (moyenne, par heure de la
  journée, pendant les annonces), commission et glissement, rapportés au mouvement moyen d'une bougie M1, M5, M15.
  Compare à EURUSD et à un indice. Dis-lui en clair si l'or est vraiment le moins cher à scalper, et à quelles heures.
- Le pont MT5 tourne depuis le 11/11 à 17 h 10 (`mt5/etat.json`). Demande-lui les vraies bougies du courtier par
  `mt5/demandes_donnees.json` : `{"demandes": [{"id": "xauusd_m1", "symbole": "XAUUSD", "periode": "M1", "nombre":
  200000}]}` (périodes M1 M5 M15 M30 H1 H4 D1, 200 000 bougies au plus par demande, 2 demandes servies par minute,
  réponse dans `mt5/donnees/<id>.csv.gz` avec le spread en points). Le nom exact du symbole chez le courtier peut
  différer (suffixe) : regarde `mt5/donnees/index.json` et `etat.json` après ta première demande.
- Cherche ensuite un scalp qui tient sur ces données : après spread réel, hors échantillon, essais comptés, comparé
  à des entrées au hasard de même fréquence. Séances (Londres, New York, fixing), retours après excès, cassures de
  fourchette, tout est permis.
- Limite technique à garder en tête : le pont relit ta consigne une fois par minute et tu ne passes que 4 fois par
  jour. Un scalp à la seconde n'est donc pas exécutable par toi. Si un montage demande de réagir bougie par bougie,
  la bonne forme est un **robot MT5** (ou un script côté PC) que tu spécifies, avec stops et objectifs posés chez le
  courtier : écris-en la spécification complète dans `labo/mt5/` et dis-le dans AVIS.md, Baptiste la fera installer.
- Les paniers de ton premier passage peuvent rester au registre papier comme références ; ils ne sont plus la
  priorité.

## 11/11/2026, 17 h 35 (Paris) : tu peux écrire toi-même le programme qui trade en direct sur la démo
Baptiste confirme XAUUSD et veut que tu trades **directement sur MT5 en démo, en continu**, quitte à créer toi-même
le programme. Tu en as donc le droit :
- Écris ton robot en Python dans `copy_sim/labo/mt5/robot/` : `robot.py` (la boucle : lit les prix du terminal,
  décide, passe ses ordres), `essais_robot.py` (essais hors ligne sur le faux terminal `copy_sim/forex/faux_mt5.py`,
  doit finir par « ESSAIS OK ») et `VERSION` (un entier croissant, changé en dernier, quand tout est poussé).
- Un **lanceur** sur le PC (voir `copy_sim/forex/MISSION_ROBOT.md`, à installer par la session PC ; tant que
  `mt5/etat.json` n'a pas de champ `robot`, il n'est pas là) installe chaque nouvelle VERSION seulement si les essais
  passent, relance le robot, et revient à la version d'avant s'il plante. Il écrit ce que fait le robot dans
  `mt5/robot_journal.jsonl` et l'état dans `etat.json`.
- Règles du robot, vérifiées par le lanceur : il n'envoie ses ordres **que** par les fonctions du pont
  (`copy_sim/forex/pont_mt5.py` : démo vérifiée à chaque ordre, 10 positions, 0,50 lot, numéro magique) ; il ne lit
  ni n'écrit de fichier hors de son dossier et de `mt5/` ; pas de réseau ; pas d'autre paquet que la bibliothèque
  standard, `MetaTrader5` et `numpy` ; chaque position a un stop chez le courtier ; il s'arrête si `STOP_PONT` existe.
- Avec le robot, la limite « une consigne par minute » disparaît : tu peux réagir à chaque bougie M1, voire à
  chaque prix. Toi, tu règles et surveilles 4 fois par jour ; lui exécute en continu.
- La discipline ne change pas : n'y mets qu'un montage que tu défendrais (hors échantillon, spread réel). En
  attendant la preuve, tu peux faire tourner le robot à **0,01 lot** pour mesurer l'exécution réelle (spread,
  glissement, délai) : dis-le clairement dans AVIS.md comme « mesure », pas comme « stratégie ».

## 11/11/2026, 18 h (Paris) : noms exacts des indices chez STARTRADER (réponse à ta question du passage 2)
Lus dans le terminal MT5 de Baptiste : les indices portent un **« + »** à la fin.
- Nasdaq 100 : `NAS100+` ; S&P 500 : `SP500+` ; Dow Jones : `DJ30+` ; DAX : `GER40+`.
- Il existe aussi `NAS100ft+`, `SP500ft+`, `DJ30ft+`, `GER40ft+` (probablement les contrats à terme : à vérifier par
  le spread et l'échéance avant usage).
Utilise ces noms tels quels dans `mt5/demandes_donnees.json` et dans ton robot.

## 11/11/2026, 18 h 05 (Paris) : quand un scalp semble gagner, explore ses combinaisons à fond
Baptiste veut que, dès qu'une règle de scalp sort gagnante (même de peu, même une seule au réglage), tu ne t'arrêtes
pas à la version testée : **essaie plusieurs combinaisons autour d'elle**.
- Réglages voisins : longueurs, seuils, tenue (en bougies et en minutes), stop et objectif (fixes, en ATR, sans
  objectif), sortie au temps.
- Filtres croisés : heures (14 h – 17 h, 2 h – 4 h, fixing, ouverture de New York), jour de la semaine, sens (achat
  seul / vente seule), volatilité du moment, tendance de fond (M15, H1), annonces exclues ou seules.
- Autres terrains : autres périodes (M1, M5, M15), argent, indices (`NAS100+`, `SP500+`, `GER40+`), EURUSD et USDJPY.
- Combinaisons de deux règles qui se confirment, ou d'une règle avec un filtre.

La discipline va avec, sinon les combinaisons fabriquent des gagnants par hasard :
- compte chaque combinaison dans le total des essais et dis combien tu en as testé autour de chaque idée ;
- ne garde qu'un **plateau** (les réglages voisins gagnent aussi), jamais un pic isolé ;
- choisis sur la période de réglage, juge sur une dernière période jamais touchée (ou en glissant : réglage puis
  verdict, plusieurs fois de suite), avec le spread réel, comparé au hasard de même fréquence ;
- assez de trades au verdict pour que le résultat ne tienne pas à quelques-uns (vise t > 2) ;
- ce qui passe tout ça va d'abord dans ton robot à **0,01 lot** sur la démo pour vérifier spread et glissement réels,
  puis seulement ensuite plus gros. Écris dans AVIS.md ce qui a tenu et ce qui est tombé, en clair.

## 11/11/2026, 18 h 10 (Paris) : recherche la plus large possible, et une première démo dès ton prochain passage
Baptiste veut **le plus de combinaisons possible** et **une première démo bientôt**. Concrètement :
1. **Recherche massive** : balaie systématiquement tout ce qui est listé à 18 h 05 (règles × réglages × heures ×
   sens × filtres × stops/objectifs × périodes × symboles), par milliers de combinaisons si ton temps le permet,
   par programme (grilles, puis affinage autour des plateaux). Garde les garde-fous de 18 h 05 ; avec autant
   d'essais, exige un verdict hors échantillon plus net (le meilleur de N essais gagne par hasard : compare à la
   distribution des meilleurs résultats sur des entrées au hasard, et annonce N).
2. **Première démo au prochain passage, sans attendre la preuve** : pousse un robot (`mt5/robot/`, voir
   `copy_sim/forex/ROBOT_INTERFACE.md` et l'exemple `copy_sim/forex/robot_exemple/`) qui fait tourner sur la démo,
   à **0,01 lot** et avec stop, ta mesure d'exécution ET ton ou tes **meilleurs candidats du moment** (les plus
   solides, même non prouvés). Étiquette chaque trade dans `pont.noter` (quel candidat, « essai non prouvé »), pour
   comparer ensuite démo réelle et backtest. Ne monte au-delà de 0,01 lot que pour ce qui passe tous les garde-fous.
3. Dans AVIS.md : nombre de combinaisons testées, ce qui tourne sur la démo et pourquoi, premiers résultats réels.

## 11/11/2026, 18 h 15 (Paris) : trade sur la démo dès maintenant, et apprends des résultats
Baptiste ne veut pas attendre une preuve complète pour voir des trades : **lance dès ce passage des trades réels sur
la démo** (XAUUSD d'abord) et apprends de ce qu'ils donnent. Cela remplace la consigne « n'y envoie que ce que tu
défendrais » et « mesure seulement » des entrées précédentes.
- Mets dans ton robot tes meilleures hypothèses du moment (plusieurs en parallèle si tu veux, chacune avec son
  étiquette dans le commentaire ou l'identifiant de l'ordre), à **petite taille** (0,01 à 0,05 lot) tant qu'aucune
  n'est prouvée. Le but est d'apprendre vite sur le vrai marché : exécution, heures, comportement des stops.
- À chaque passage : lis `mt5/executions.jsonl`, `mt5/robot_journal.jsonl` et `etat.json`, tiens un tableau des
  résultats **par hypothèse** (trades, gain moyen après spread, erreur type), coupe ce qui perd nettement, garde et
  affine ce qui tient, ajoute de nouvelles idées. Monte la taille d'une hypothèse seulement quand ses trades en
  direct **et** ton banc hors échantillon vont dans le même sens.
- Reste honnête dans AVIS.md : quelques dizaines de trades ne prouvent rien ; donne toujours le nombre de trades et
  la marge d'erreur à côté de chaque résultat, et dis clairement ce qui est « essai en direct » et ce qui est prouvé.
- Les sécurités du lanceur ne changent pas (démo, stop sur chaque position, 10 positions, 0,50 lot, −5 % par jour).

## 11/11/2026, 18 h 45 (Paris) : beaucoup plus de trades, presque en continu
Baptiste trouve que le robot v1 trade trop peu (2 trades en 25 minutes). Il veut du **vrai scalp : des trades
nombreux, presque tout le temps**. C'est aussi dans ton intérêt : plus de trades = un verdict plus rapide.
- Vise **au moins 100 à 200 trades par jour** sur la démo : hypothèses en M1 (et à la bougie M5), tenues courtes
  (1 à 15 minutes), plusieurs hypothèses en parallèle dans la limite des 10 positions, et le témoin au hasard à la
  même cadence pour comparer. Garde 0,01 lot tant que rien n'est prouvé : à cette taille le spread coûte environ
  0,20 $ par trade, la démo peut en absorber des milliers.
- Trade aussi en dehors des meilleures heures pour mesurer la différence, mais étiquette l'heure : tu sauras vite
  quelles séances valent quelque chose.
- Chaque position garde son stop chez le courtier. Si le lanceur ou le pont limite la cadence (délai, refus), note-le
  dans AVIS.md avec ce qu'il faudrait changer côté PC.
- Publie la nouvelle version du robot dès ce passage.

## 11/11/2026, 22 h 35 (Paris) : une stratégie « de la période actuelle » est acceptable
Baptiste ne demande pas une règle valable depuis toujours. Une règle qui marche **dans le régime actuel** lui va,
même si elle perdait il y a deux ans : son plan est de retirer les gains au fur et à mesure et d'arrêter quand elle
casse. Ne rejette donc plus un candidat seulement parce qu'il échoue sur une période ancienne.
- Juge les candidats sur le **récent** (6 à 15 derniers mois), toujours en avance glissante (réglé sur le passé,
  jugé sur la suite) et en comptant tes essais : sur 48 000 combinaisons, les meilleures du récent sont en partie
  de la chance. La confirmation qui compte ensuite, c'est le **direct sur la démo**.
- Pour chaque candidat mis en direct, écris **avant** ses premiers trades sa règle d'arrêt : par exemple « arrêt si,
  après N trades, la moyenne est sous X, ou si la perte cumulée dépasse Y fois la perte normale du banc ». Une
  stratégie de régime sans règle d'arrêt n'est pas un plan.
- Dis à quoi tu reconnais le régime où elle marche (volatilité, tendance, heures, niveau du spread) pour savoir
  quand la remettre ou la couper.
- Le « retour de midi » redevient donc un candidat sérieux : garde-le, avec sa règle d'arrêt.
- Reste honnête dans AVIS.md sur ce que cela implique : un gain qui peut s'arrêter du jour au lendemain, et une
  taille à garder modeste tant que le direct n'a pas confirmé.
