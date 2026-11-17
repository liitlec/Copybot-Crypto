# Dépôts « skills » de trading : inventaire et essais (PRIORITES 15/11 15 h et 17/11 10 h 30)

Lecture seule (README, fichiers SKILL.md et règles) ; rien installé, aucun script exécuté, aucun compte. Un tableau
par dépôt. Heures : serveur du courtier = New York + 7 h = Paris + 1 h. Nos données : or M1/M5/M15/H1, Nasdaq,
S&P et Dow M1/M5 (≈ 15 mois en M5), indices jour (courtier et Yahoo 2000-2026), argent, EURUSD, BTC/ETH M5.
« Testable » = codable au banc avec ces données, spread réel et entrée à la bougie suivante.

## 1. Jakeschincariol/day-trader-skill (11 skills, Python standard, données Yahoo/Nasdaq/SEC)
| Idée | Règle précise | Testable ? | Déjà testé ? | Résultat |
|---|---|---|---|---|
| ORB (scanner + entrée + sortie) | fourchette des 15 premières minutes (9 h 30-9 h 45 NY = 16 h 30-16 h 45 serveur) ; entrée à la 1re clôture M5 au-dessus ; stop au milieu de la fourchette ; objectif 1 R (2 R par défaut) ; à plat à 15 h 55 NY ; achats seulement | oui | **oui**, `banc_orb.py`, NAS100+, SP500+, DJ30+ M5 ~15 mois | **rien** : −0,06 à +0,04 R par trade (\|t\| ≤ 1,1), 2de moitié négative 10 fois sur 12 ; leur propre exemple TSLA donne « pile ou face » |
| Variantes ORB | objectif 2 R ; stop à l'autre bout ; fourchette 30 min | oui | oui (même banc) | rien (meilleur : SP500+ 30 min +0,04 R, t = 0,6) |
| Scanner jour « cassure 20 j » | clôture au-dessus de la plus haute clôture des 20 jours | oui (indices jour) | en partie (banc A, suivi de tendance 20-250 j) | banc A : les indices tiennent, les devises perdent |
| Scanner jour « survendu » | RSI 14 < 30 ; « rebond » : RSI 14 < 30 la veille et clôture du jour en hausse | oui (indices jour) | cousin testé : repli RSI 2 + moyenne 200 j (bancs R, S) | **le repli tient** (en démo) ; la version RSI 14 n'est pas testée |
| Drapeau haussier, reprise de la moyenne 20 j | +10 % sur 10 séances puis 5 clôtures dans 5 % ; clôture repasse au-dessus de la moyenne 20 j | oui (jour) | non | — (règles faites pour des actions) |
| « Time Machine » | rejoue 10 000 fois le reste de la séance en tirant pour chaque bougie M5 une bougie de la même heure (± 2) parmi les 59 séances précédentes, mise à l'échelle ; compte objectif d'abord / stop d'abord / ni l'un ni l'autre ; + rejoue la règle sur ces 59 séances réelles | oui (outil) | non | idée reprise possible : chances avant d'ouvrir ; nos bancs font déjà la partie « historique réel » |
| Exit Planner | stop et objectif fixés avant l'entrée ; refus d'un stop trop serré pour le spread ; à plat avant la clôture | — | déjà chez nous (stop obligatoire, sortie au temps) | — |
| Risk / Budget | taille = perte max ÷ distance du stop ; 3 trades/jour ; perte du jour 150 $ ; R:R ≥ 1 ; fenêtre d'entrée ; une sortie n'est jamais bloquée | — | déjà fait (garde-fou du pont, 0,01 lot) ; pas de limite de perte du jour | — |
| News, Analyst, Pelosi, Broker | actualités, résultats, déclarations des élus, ordres Alpaca | non | non | actions américaines / courtier : hors de nos CFD MT5 |

## 2. Jakeschincariol/trader-skill (prédécesseur, placement long terme)
| Idée | Règle précise | Testable ? | Déjà testé ? | Résultat |
|---|---|---|---|---|
| Copycat 13F | recopier le portefeuille trimestriel d'un grand investisseur | non | non | actions, 45 jours de retard : hors sujet |
| Screener, rééquilibrage (bande 5 %), impôts | critères fondamentaux, retour aux poids cibles | non | non | hors sujet |
| Alertes avec le vrai calendrier NYSE | sonne à l'ouverture, au stop, à l'objectif | — | non | idée : notre calendrier vient de Helious + Nager (APIS.md) |

## 3. tradermonty/claude-trading-skills (≈ 80 skills, beaucoup d'actions US, certaines avec clé FMP)
| Idée | Règle précise | Testable ? | Déjà testé ? | Résultat |
|---|---|---|---|---|
| **COT à contre-courant** (méthode Shapiro) | indice COT = position nette des spéculateurs ramenée entre son min et son max des 156 dernières semaines ; ≥ 90 = foule acheteuse, ≤ 10 = foule vendeuse ; entrer **contre** la foule seulement si une bonne nouvelle n'a pas fait monter le prix et si la semaine confirme un retournement ; stop au dernier extrême ; sortie quand l'indice revient vers 50 | **oui** sur l'or jour (CFTC gratuit depuis 1986, voir APIS.md) ; partie « nouvelle ignorée » non codable | non | — |
| Coupe-circuit de perte (drawdown-circuit-breaker) | perte du jour ≥ 2 % → arrêt jusqu'au lendemain ; 2 pertes de suite → pause 24 h ; −5 % sur la semaine → arrêt jusqu'à lundi ; −8 % sur le mois → arrêt jusqu'au mois suivant | **oui** en rejouant les trades du robot | non | — |
| Jours de distribution (IBD) | clôture ≥ 0,2 % sous la veille avec volume plus fort ; compter ceux des 25 dernières séances ; beaucoup = marché fragile | oui (S&P/Nasdaq jour Yahoo, volume) | non | filtre possible pour le repli d'indices |
| Follow-Through Day (O'Neil) | après une baisse, jour 4 à 10 d'une reprise : hausse nette avec volume plus fort → fond confirmé | oui (jour) | non | règle floue sur le seuil de hausse |
| Calendrier économique | FMP (clé) ou FXMacroData (USD sans clé) | — | non | FXMacroData répond sans clé mais seulement pour l'avenir (APIS.md) |
| backtest-expert | coûts × 1,5 à 2 pour se mettre à l'abri ; ≥ 100 trades (30 au minimum) ; chercher des plateaux, pas des pics ; rejet si le hors-échantillon < 50 % de l'échantillon | — | **déjà notre méthode** (réglage 60 % / verdict 40 %, plateaux, t) | — |
| mt5-robot-tester | lance le testeur de stratégie MT5 en ligne de commande, 3 tours | non (pas de terminal MT5 ici) | non | idée seulement |
| VCP, CANSLIM, PEAD, Stockbee, dividendes | sélection d'actions | non | non | actions américaines : hors sujet |

## 4. agiprolabs/claude-trading-skills (68 skills, surtout crypto/DeFi Solana)
| Idée | Règle précise | Testable ? | Déjà testé ? | Résultat |
|---|---|---|---|---|
| Régime par ADX | ADX 14 > 25 = tendance, < 20 = range : suivre en tendance, revenir à la moyenne en range | oui (or M5/M15) | en partie (bancs Y, AB : régime par amplitude, pas par ADX) | régime « calme / agité » utile (pause au calme de la v11) ; ADX non testé |
| Régime par largeur de Bollinger / centile d'ATR / Hurst | centile de l'ATR sur sa propre histoire ; Hurst < 0,5 = retour, > 0,5 = tendance | oui | en partie (compression = centile de fourchette, banc AA) | compression : rien |
| Sorties | stop 2 × ATR 14 ; sortie « Chandelier » (plus haut de N bougies − k × ATR) ; sortie au temps | oui | **oui** (bancs H, V, X, sorties_bt) | les sorties changent la forme, pas le signe |
| Retour à la moyenne | z-score, demi-vie AR(1), test ADF | oui | **oui** (bancs F, H, L : VWAP, z-score) | seul le midi sur l'or est faiblement positif |
| Walk-forward avec purge et embargo | enlever de l'apprentissage les lignes dont la cible chevauche le test ; laisser un trou entre les deux | — | en partie (banc N) | à reprendre si on refait des modèles appris |
| Kelly fractionné | mise = ¼ à ½ Kelly, 100 trades au moins pour l'estimer ; Kelly négatif = pas d'avantage | oui (sur les trades du banc) | en partie (banc O, Monte-Carlo) | — |
| Limites de risque | arrêt à un recul max du compte, perte du jour et de la semaine, concentration | — | en partie | rejoint le coupe-circuit (dépôt 3) |
| DEX, Solana, mempool, marchés de prédiction, impôts | — | non | non | hors sujet |

## 5. galleonlabs/hypergrok-trading-desk (Hyperliquid, 7 rôles, 17 skills)
| Idée | Règle précise | Testable ? | Déjà testé ? | Résultat |
|---|---|---|---|---|
| Exemple « funding-fade-v1 » | bougies 4 h ; si le financement horaire moyen des 8 dernières heures > +0,005 %/h, vendre à l'ouverture 4 h suivante ; sortie si financement ≤ 0, ou après 72 h, ou stop à 2 × ATR 24 bougies ; risque 0,5 % du compte | en partie : il faut l'historique de financement Hyperliquid (public) + BTC/ETH M5 du courtier | non (banc I a testé le **portage** neutre, pas le pari directionnel) | — |
| Limites du bureau | 0,5 % de risque par trade ; 2 % de risque ouvert au total ; 3 positions ; BTC/ETH/SOL comptent pour un seul groupe (2 positions au plus) ; perte du jour −2 % → plus de nouveau risque ; glissement max 10 points de base à l'envoi | — | en partie (garde-fou du pont) | idée à reprendre : limite par **groupe corrélé** (or + argent, indices US entre eux) |
| Rôles séparés (analyste, risque, exécution, revue) et « porte » avant tout ordre | un seul rôle peut envoyer, après accord | — | déjà chez nous (le pont démo seul passe des ordres) | — |

## 6. MobiusQuant/OpenMobius-skill (ICT/SMC, 726 fiches de concepts, surtout en chinois)
| Idée | Règle précise | Testable ? | Déjà testé ? | Résultat |
|---|---|---|---|---|
| **Silver Bullet** | fourchette de 9 h-10 h NY (16 h-17 h serveur) ; entre 10 h et 11 h NY (17 h-18 h serveur), attendre que le prix dépasse un bord puis revienne dedans, entrer à l'inverse, objectif l'autre bord | **oui** (NAS, S&P, Dow, or M5) | non | — |
| Kill zones | fenêtres actives : Londres 2 h-5 h NY (9 h-12 h serveur) ; New York matin indices 8 h 30-11 h (15 h 30-18 h serveur) ; après-midi indices 13 h 30-16 h | oui (filtre d'heure) | en partie (bancs E, J : découpes par heure) | seul 12 h-15 h serveur sur l'or est faiblement positif |
| Ouverture de minuit (« premium / discount ») | prix au-dessus de l'ouverture de 0 h NY (7 h serveur) → ne chercher que des ventes ; au-dessous → que des achats | oui | non | — |
| Judas swing | fausse poussée contre le sens du jour juste après 0 h, 8 h 30, 9 h 30 ou 10 h NY, puis vrai mouvement | oui, mais la règle est floue | en partie (banc X à 8 h 30 : rien) | — |
| Balayage du range d'Asie, retournement de Londres | Londres passe le haut ou le bas d'Asie (20 h-0 h NY) puis repart dans l'autre sens | oui | **oui** (banc L) | chasse aux stops d'Asie : **perd** ; cassure d'Asie suivie 2 h : +4 bp, non prouvé |
| Écart de juste valeur (FVG) | 3 bougies dont la 1re et la 3e ne se recouvrent pas ; retour vers son milieu | oui | **oui** (banc L) | **perd** (−0,04 à −0,7 bp) |
| OTE (entrée optimale) | après une poussée, retracement Fibonacci 0,62-0,79 (cœur 0,705) | oui si on fixe « poussée » | non | — |
| Order blocks, breaker blocks | dernière bougie contraire avant une poussée | difficile (définitions qui changent selon les sources) | non | — |

## 7. syedishaq7262-svg/crypto-trader-skill (« 37 401 trades, aucun avantage après coûts »)
Comment ils ont mesuré : 6 familles (ORB du jour UTC et de New York, cassure de range, compression, repli en
tendance, retournement RSI, pic de volume), achats et ventes, sur les perpétuels Binance les plus liquides ; le
scanner ne voit que les bougies fermées ; stop au point d'invalidation, objectif 2 R, sortie à 24 h ; un trade à la
fois par pièce et par règle ; rejoué sur les bougies 5 min ; **stop compté quand une bougie touche stop et objectif** ;
frais, glissement et financement payés. 27 566 trades sur 90 jours, puis 9 835 sur les 90 jours d'avant comme contrôle.
Résultat : +0,02 R avant coûts, **−0,18 R après** (coûts 0,20 R par trade), facteur de profit 0,77 ; à peine
mieux que des entrées au hasard aux mêmes heures (+0,06 R) ; l'ORB du jour UTC est la pire (−0,37 R et −0,50 R).
| Idée | Règle précise | Testable ? | Déjà testé ? | Résultat |
|---|---|---|---|---|
| Témoin « hasard aux mêmes heures » | même stop, même objectif, entrée tirée au hasard aux mêmes heures | oui | en partie (témoins hasard des bancs D, E, V) | à généraliser à chaque banc |
| **Règle du coût** | refuser un trade si le spread + glissement à la sortie au stop prend plus de 0,2 R | **oui** sur les trades du robot | non | eux : seule règle (avec la suivante) qui tient sur les deux moitiés |
| Contrôle 30 jours | ne prendre une règle sur un marché que si elle a gagné après coûts sur ses 30 derniers jours (5 trades au moins) | oui | non (proche de la « bonne famille au bon moment », banc AB) | — |
| Coûts selon la distance du stop | stop < 0,25 % : −0,61 R après coûts ; stop ≥ 2 % : −0,08 R | — | rejoint nos bancs (scalps tués par le spread) | confirme : stops serrés = coûts mortels |

## À tester en priorité (assez précis pour être codé)
1. **Pause autour des annonces High** (Helious, 13 mois) : sur les règles du robot (or M5 et repli d'indices), pas de
   nouvelle entrée de 30 min avant à 30 min après une annonce US « High » ; positions ouvertes gardées. Comparer
   avec / sans, et avec des pauses aux mêmes heures les jours sans annonce (témoin).
2. **Silver Bullet** sur NAS100+, SP500+, DJ30+ et or M5 : fourchette haut/bas des bougies 16:00-16:55 serveur ;
   de 17:00 à 17:55, si une bougie M5 dépasse un bord puis **clôture de nouveau dedans**, entrer à l'inverse à
   l'ouverture suivante ; stop au-delà de l'extrême du dépassement ; objectif l'autre bord (variante : le milieu) ;
   sortie forcée à 18:55 ; un trade par jour ; spread réel ; réglage 1re moitié / verdict 2de.
3. **COT à contre-courant sur l'or** (or jour + CFTC) : chaque vendredi, indice COT 156 semaines des non-commerciaux ;
   ≥ 90 → vente à l'ouverture du lundi, ≤ 10 → achat, seulement si la semaine écoulée clôture déjà dans le sens
   voulu ; stop au plus haut (plus bas) des 4 dernières semaines ; sortie quand l'indice repasse 50 ou au stop.
   Comme les données sont du mardi publiées le vendredi, ne jamais utiliser une semaine avant sa publication.
4. **Règle du coût + coupe-circuit** en rejouant les trades du robot : (a) supprimer les trades dont le spread à
   l'entrée dépasse 0,2 R (puis 0,1 R) ; (b) arrêt du jour après −2 % du compte, pause 24 h après 2 pertes de suite.
   Mesurer : gain, pire mois, nombre de mois négatifs.
5. **Ouverture de minuit** sur l'or et le Nasdaq M5 : de 15:30 à 18:00 serveur, n'accepter que les achats des règles
   du robot si le prix est sous l'ouverture de 07:00 serveur, que les ventes s'il est au-dessus ; comparer au robot
   sans ce filtre.
