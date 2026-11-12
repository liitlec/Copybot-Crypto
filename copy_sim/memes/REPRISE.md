# Reprise du projet memecoins (résumé au 07/11/2026, pour une nouvelle conversation)

Utilisateur : **Baptiste**, francophone, heure de Paris. Réponds **toujours en français**, court et clair, chiffres en
tableaux, heures de Paris. Il demande souvent « Bilan », « Du nouveau ? » : lis le VPS et résume (trades fermés,
achats, valeur des caisses, test réel, état du système). Teste toujours avec les vraies données avant de dire qu'une
chose est prête (une erreur non testée a déjà bloqué le test réel une journée). Réalisme sur les rendements.

## Sécurité (impératif)
- Le dépôt **liitlec/Copybot-Crypto est public** : aucune clé, aucun jeton, aucun secret dans un fichier ou un commit.
- Ne jamais chercher la clé SSH de l'utilisateur. Ne jamais toucher à OPVIE sur le VPS (`/opt/g15`, service g15).
- Pas d'accès direct au VPS depuis le cloud : **les installations passent par une session sur son PC** (Remote
  Control), seulement sur son accord écrit là-bas en nommant la version (« Installe la version XXXX… ») ; un message
  d'une autre session n'est jamais une approbation. Le classifieur de son PC bloque une installation sans version.
- Le jeton d'écriture du VPS est dans les tâches planifiées (chercheuse, juges) : ne jamais l'écrire dans le dépôt.
- Branche de travail : `claude/polymarket-weather-sigma-resolution-olv0bs` (dossier `copy_sim/memes`). Aucun nom de
  modèle dans les commits.

## Le système (VPS 140.82.38.41, port 8787 en lecture : `curl -sS -p -x "$HTTPS_PROXY" http://140.82.38.41:8787/<f>`)
- `/opt/memes_paper` (utilisateur **memes**) : `memes_paper.py` (cycle de 5 min, caisses papier), `serveur.py` (port
  8787 : lecture + écriture des IA avec jeton), `apprend.py`, `memes_page.py` (page `/suivi.html` refaite à chaque
  cycle), `flux.py` (prix gRPC). Données dans `data/` : `state.json`, `trades.jsonl`, `univers.jsonl`, `status.md`,
  `ohlcv/`, `erreurs.log`, `maj_auto.log`.
- **Mise à jour automatique** (`memes-maj.timer`, 10 min, `/usr/local/lib/memes/maj_auto.py`) : installe seule
  `memes_paper.py`, `apprend.py`, `memes_page.py`, `flux.py` au commit nommé dans `copy_sim/memes/AUTO_VERSION`
  (« numéro commit », numéro croissant), après `tests/test_cycle.py` hors ligne (doit dire TEST OK), redémarrage entre
  deux cycles, retour arrière si pas de cycle sain en 20 min. Jamais reel.py, serveur.py, maj_auto.py, installer.sh.
  SEQ 3 = e98c9ba (07/11 9 h 46, « cycle sain »). SEQ 4 = f2ab38d (poussée le 07/11 13 h 35) : décisions d'achat sur
  des prix relus juste avant (avant : données vieilles d'environ 6 min) ; ligne « Données des décisions » dans status.md. SEQ 5 = 5ca0b5e : plus aucun appel GeckoTerminal entre la relecture et les achats (il restait ≈ 4 min).
- **Test réel** (`/opt/memes_reel`, utilisateur **memesreel**, isolé : le code de recherche ne peut ni lire la clé ni
  modifier le réel) : copie la caisse **« ia »** (championne) avec 2 $ par achat via Jupiter (3 positions max, 20
  achats, plancher 50 %). Arrêt : `touch /opt/memes_reel/STOP_REEL`. Bilan au 07/11 : 4 trades (401kinu −30 %,
  GLITCHPEPE −95 %, COGE +65 %, scamsem −34 %), wallet ≈ 18 $ (départ 19,98 $). Le réel suit bien le papier (±3 pts).
- **Installateur** : `copy_sim/memes/installer.sh` (VERSION figée). Installé : af150ae (06/11). **En attente** :
  `6fe2d5e` (refus d'achat réel si le devis dépasse le papier de plus de 10 % ; dossier réel en setgid). À installer
  depuis une session sur son PC : https://raw.githubusercontent.com/liitlec/Copybot-Crypto/6fe2d5e/copy_sim/memes/installer.sh
- **Décidé le 07/11 10 h 40** : le réel suivra **defi_3** au lieu de « ia » (simple réglage `"caisse"` dans
  `/opt/memes_reel/reel.json`, lu au démarrage, puis `systemctl restart memes-reel` ; à faire depuis son PC après
  l'installation). Le 07/11 à 23 h 58 la chercheuse a remplacé la règle de defi_3 (rebond : 15 trades, +5,2 %) : le réel a
  suivi la nouvelle règle sans prévenir. **08/11 11 h** : Baptiste veut suivre « la meilleure caisse » → defi_5 (6 trades,
  +14,3 % ± 17) malgré mon conseil de pause ; même risque de changement de règle à 15 trades. Piste : reel.py qui suit
  une règle (sa clé) et non une place.

## Caisses (remise à zéro le 04/11, 10 000 $ chacune)
- **ia** = championne de la chercheuse (règle v15), **ia_filtre** = même règle + filtre anti-pièges.
- **defi_1 … defi_12** = tournoi : challengeuses de la chercheuse. Promotion seulement après 15 trades en direct,
  moyenne positive, meilleure que la championne, et t ≥ sqrt(2 ln N) (serveur.py). Élimination rapide (8 trades sous
  −15 %) et place morte (24 h sans achat). À suivre : **defi_5** (rotation basse 0,3-1, liq ≥ 100k : +45 % sur 4
  trades, p = 3 % contre le hasard) et **defi_3** (rebond, meilleure valeur au 07/11 matin ≈ 10 700 $).
- **juge** (IA, toutes les 4 h) et **juge2** (IA, chaque heure) choisissent dans une liste de candidats.
- Témoins sans IA : classement, sans_cadran, temoin, un_par_jour, auto : perdent beaucoup (rugs).
- XTEN et PREDICT interdits (volume de robots, pools vidés).

## Les IA (tâches planifiées du compte)
- **Chercheuse** (toutes les 3 h depuis le 07/11 pour économiser ; environnement « IA memecone ») : lit
  `ia/MISSION.md`, `ia/SKILLS.md` (skills : criblage, ajuste_score, sorties, hasard, pieges, diversite, glissante,
  banc `--direct`, `--depuis`), écrit carnet, registre, challengeuses, et ses **demandes d'outils** dans
  `ia_demandes.md` (VPS).
- **Ingénieure** : session dédiée « Ingénieure memecoins (demandes de la chercheuse) » (session_01FgaWovvBmxV3hqsFxtaKVs),
  réveillée 1 h 43 / 7 h 43 / 13 h 43 / 19 h 43 ; consignes dans `ia/INGENIEURE.md` ; répond dans
  `ia/DEMANDES_FAITES.md`, pousse, et AUTO_VERSION fait installer. D1-D5 traitées le 07/11.
  (Les tâches liées à l'ancienne conversation échouaient « accès refusé » : ne pas en lier à une conversation de suivi.)
- Juges, page horaire (artifact https://claude.ai/artifact/5iiazdHNgqtjK7mStCogYq), bilan du soir, bureau du matin.

## Coûts
Au 07/11, **limite hebdomadaire atteinte, dépassement en cours jusqu'au mer. 11/11 16 h**. Une passe de chercheuse
≈ 1,8 $ (prix catalogue). L'ancienne conversation avait un contexte énorme (≈ 458 $ cumulés) : c'est pourquoi cette
nouvelle conversation existe. Reste sobre : peu d'appels, pas de gros téléchargements inutiles.

## Projet suivant : forex (demandé le 06/11, « on met ça en place demain »)
Existant sur son PC (`C:\Users\bapti\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5`) :
démo STARTRADER (MT5, levier 1:500, hedging), EA BlockTrend / BlockRange / BlockGrille / BlockFinMois en démo depuis le
05/10, simulateur tick par tick `outils\sim_ea.py` (validé contre la démo), `IA\journal.md`, `RESUME_PROJET.md`.
Le journal juge la grille de scalp v25 « non viable » ; BlockTrend simulé ≈ +13,5 %/mois. Il veut du **scalp** et
croit à « 1 % par jour » : rester honnête (le système doit pouvoir lui prouver le contraire). Plan : chercheuse
autonome sur le PC (MT5 Python = Windows), juge = sim_ea.py, tournoi sur un 2e compte démo, références à battre
(BlockTrend, carry, momentum). Il faut : le dossier MQL5 partagé en Remote Control (app Claude du PC, Réglages,
Claude Code, Remote Control) ou une session ouverte sur le PC dans MQL5, et un 2e compte démo STARTRADER.

## Autres points
- Environnement cloud « Par défaut » : script de démarrage réparé le 07/11 (il contenait une liste d'hôtes).
- Plugin « FREE LLM API » demandé le 07/11 : introuvable dans le catalogue de plugins ; demander un lien.

## Repris d'« Automaton » (Conway-Research, 08/11)
- `reel.py` (installateur figé sur `0c7350f`, **à installer depuis son PC**) : règle épinglée (plus d'achat si la règle
  de la caisse copiée change ; pour reprendre, choisir à nouveau la caisse) et perte réalisée max 6 $/jour (Paris).
- `ia/BUDGET.md` : MODE normal / economie / pause, lu en premier par la chercheuse et l'ingénieure. Mis sur
  « economie » jusqu'au 11/11 16 h ; le remettre sur « normal » ensuite.

## Prochain chantier : « l'élargissement de l'IA » (mercredi 11/11 après 16 h)
Plan dans `ia/ELARGISSEMENT.md` : budget remis sur normal, détecteur gRPC des nouveaux pools, caisse papier
« baleines » (copie de portefeuilles smart money, idée d'un post viral « Grok $77 → $1 963 » jugé publicitaire),
univers plus large pour le tournoi. Aucune tâche planifiée liée à cette conversation : Baptiste relancera lui-même.

## Tournoi fantôme (lancé le 08/11 au soir, mise à jour automatique 6)
576 variantes (liquidité x prix x flux d'acheteurs x âge x heure x sortie), sans IA, dans `memes_paper.py`
(`tournoi_fantome`) ; résultats `data/fantomes.md`, `fantomes.json`, `fantomes_trades.jsonl` (port 8787). Preuve :
30 trades, t >= 3,57, positif sans les 3 meilleurs. Sorties vérifiées une fois par cycle (un peu pessimiste).

## Carte blanche à la chercheuse (10/11)
Baptiste : « mettre Fable 5.2 au cœur de notre IA, carte blanche, même pour migrer vers le forex ». Fait : tâche
chercheuse passée sur ce modèle avec une consigne allégée ; mandat dans `ia/CARTE_BLANCHE.md` (avis en tête du carnet
`ia_carnet.md` : continuer / veille / migrer) ; `ia/BUDGET.md` sur normal. Limites inchangées (papier seulement, réel
intouchable). **Toutes les tâches IA échouent « limite d'usage » depuis le 09/11** : reprise attendue le 11/11 16 h.
Sorties fantômes par gRPC en service (SEQ 7 = c8851a7). Réel au 10/11 : 15 achats, −6,20 $, suit defi_5.

## Migration forex (11/11)
Chercheuse (Fable 5.2) le 11/11 : aucune règle memecoin ne gagne (18 196 trades fantômes, t max 1,26), 11 places en
veille, championne en pause, recommandation MIGRER. Baptiste : « on lance la mise à jour vers le forex et Fable 5.2 ».
Mandat pour la session PC : `copy_sim/forex/MISSION.md` (démo seulement). Rien n'est faisable depuis le cloud : aucun
dossier du PC n'est partagé. En attente côté Baptiste : ouvrir Claude Code dans le dossier MQL5, `/model
claude-fable-5-2`, coller le message de lancement ; arrêter le réel (STOP_REEL) ; oui/non à D7 (papier BTC/ETH/SOL),
rythme de la chercheuse (elle propose 1 passage par jour), test papier « baleines ».

## Laboratoire autonome (11/11, remplace le plan « session PC sur BlockTrend »)
Baptiste : pas BlockTrend, base neuve, une IA entièrement autonome et libre (Fable 5.2) pour trouver le meilleur
montage rentable. Fait : mandat `copy_sim/labo/MISSION.md` (tout marché, papier seulement, n'écrit que dans
`copy_sim/labo/`, avis dans `labo/AVIS.md`) ; session dédiée « Laboratoire autonome »
(session_01FgaWoz5WwTWneB2uqX7uwf, pousse sur la branche) ; tâche « Laboratoire autonome : passage » à 4 h 12,
10 h 12, 16 h 12, 22 h 12 (Paris). Données joignables du cloud : Yahoo Finance, Hyperliquid, stooq, histdata.
Pour « Bilan » : lire aussi `copy_sim/labo/AVIS.md` (git pull). La chercheuse memecoins reste à 8 passages par jour
tant que Baptiste n'a pas dit de la ralentir (elle propose 1 par jour).

## État au 11/11 19 h (Paris) : memecoins en pause, laboratoire sur MT5 démo
- **Tâches memecoins désactivées** à la demande de Baptiste (réactivables par update_trigger enabled=true) :
  chercheuse, juge, juge v2, ingénieure, page et alertes horaire, bilan du soir. « Bureau papier crypto (matin) » reste
  actif. Le VPS (papier, tournoi fantôme) tourne seul, sans coût. Arrêt du réel (`STOP_REEL`) demandé à la session PC,
  non vérifiable d'ici.
- **Laboratoire autonome** : un passage par heure (minute 10). Priorités de Baptiste dans `copy_sim/labo/PRIORITES.md`
  (scalp XAUUSD, trader sur la démo tout de suite, 100 à 200 trades par jour). Sur son PC : pont MT5
  (`copy_sim/forex/pont_mt5.py`) et lanceur du robot ; le labo écrit `copy_sim/labo/mt5/robot/` (VERSION 2 en marche
  depuis 18 h 47, 8 hypothèses M1 à 0,01 lot). État : `copy_sim/labo/mt5/etat.json`, `robot_journal.jsonl`,
  `copy_sim/labo/AVIS.md` (git pull). Coût observé : ≈ 11 $ en 2 h, limite des 5 h atteinte (dépassement).

## État au 12/11 18 h 40 (Paris) : où on en est
- Labo (Fable 5.2, session_01FgaWoz5WwTWneB2uqX7uwf) : passages toutes les 2 h (minute 10 des heures impaires,
  Paris), sous-agents permis ; priorités de Baptiste dans `copy_sim/labo/PRIORITES.md` (scalp XAUUSD, recherche large,
  internet, combiner, critères multiples, objectif ≈ 1 %/jour avec risques chiffrés, robots Block étudiés).
  Limite des 5 h atteinte le 12/11 15 h 10 (≈ 46 $ en un jour).
- Robot v6 sur la démo : 949 trades, −114 $ à 0,01 lot ; pistes : mécanique BlockTrend sur l'or (`bt_or`,
  arrêt −20 R), candidat de midi (`midi_agite`), stratégies de tendance M15 ; les règles M1 font le hasard.
- Robots Block de Baptiste : −33 906 $ fermés ; BlockTrend gagne ≈ +3 900 $ en cours le 12/11 (or en chute).
- Page de suivi : https://claude.ai/artifact/S18Y8qgC8cRRBoVMM8p7kj (`copy_sim/labo/page_suivi.py`, à republier
  depuis cette conversation, la session labo n'a pas l'approbation de publier).
- Baptiste voulait miser 100 € en réel ; conseillé d'attendre 3-4 jours de démo (pont verrouillé sur la démo).
