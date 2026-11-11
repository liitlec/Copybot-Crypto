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
