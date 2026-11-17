# Dépôts « skills » de trading : inventaire et essais (PRIORITES 15/11 15 h et 17/11 10 h 30)

Lecture seule (README et règles) ; rien installé, aucun script exécuté, aucun compte. Un tableau par dépôt.

## 1. Jakeschincariol/day-trader-skill (11 skills, Python standard, données Yahoo/Nasdaq/SEC)
| Idée | Règle exacte | Testé ? | Résultat |
|---|---|---|---|
| ORB (scanner + entrée + sortie) | fourchette des 15 premières minutes (9 h 30-9 h 45 NY = 16 h 30-16 h 45 serveur) ; entrée à la 1re clôture M5 hors de la fourchette ; stop au milieu de la fourchette ; objectif 1 R ; à plat à 15 h 55 NY | **oui**, `banc_orb.py`, NAS100+, SP500+, DJ30+, M5 du courtier ~15 mois, spread réel, 4 réglages | **rien** : moyenne −0,06 à +0,04 R par trade (\|t\| ≤ 1,1), 2de moitié négative 10 fois sur 12 ; leur propre Time Machine dit « proche d'un pile ou face » sur TSLA |
| Variantes ORB | objectif 2 R ; stop à l'autre bout ; fourchette 30 min | oui (même banc) | rien (meilleur : SP500+ 30 min +0,04 R, t = 0,6) |
| « Time Machine » | rejoue 10 000 fois le reste de la séance en tirant les bougies M5 de la même heure sur les 59 séances précédentes, + toutes les fois passées où le signal a eu lieu | non (outil) | **idée reprise possible** : notre banc fait déjà la 2e partie (historique réel) ; le tirage par heure est un bon contrôle des chances avant d'ouvrir — à réécrire si utile |
| Exit Planner | stop et objectif fixés avant l'entrée ; à plat avant la clôture | déjà fait chez nous (stop obligatoire, sortie au temps) | — |
| Risk / Budget | taille = perte max ÷ distance du stop ; limite de perte du jour ; nombre de trades par jour ; fenêtre d'entrée | déjà fait (garde-fou du pont, 0,01 lot) | — |
| News, Analyst, Pelosi | actualités, résultats trimestriels, déclarations des élus américains | non | actions individuelles américaines : hors de nos CFD MT5 |
| Broker | ordres via Alpaca, papier par défaut, jamais sans « oui » | non | hors sujet (notre pont MT5 démo) |

Dépôts restants (prochaines étapes du relais, une par passage) : Jakeschincariol/trader-skill,
tradermonty/claude-trading-skills, agiprolabs/claude-trading-skills, galleonlabs/hypergrok-trading-desk,
MobiusQuant/OpenMobius-skill (ICT/SMC), crypto-trader-skill (« 37 401 trades, aucun avantage » : lire leur méthode).
