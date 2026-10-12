# Copybot-Crypto

Projets crypto séparés des EA MT5 :
1. **Arbitrage des taux de financement** (`funding/`) : encaisser le financement des perpétuels sans parier sur le prix.
2. **Bot momentum altcoins** (`momentum/`) : suivi de tendance agressif, avec backtest et simulation en direct.

Rien ne passe d'ordre réel : scanner, backtests et simulation uniquement.

## Alertes Telegram (optionnel)
Crée un bot avec @BotFather, puis définis `TELEGRAM_TOKEN` et `TELEGRAM_CHAT_ID`. Sans ces variables, les messages sont seulement affichés.

## 1. Arbitrage des taux de financement
Deux montages :
- **Comptant + perpétuel** : on achète au comptant et on vend le perpétuel sur la même plateforme quand le taux est positif.
- **Entre plateformes** : on vend le perpétuel là où le taux est haut et on l'achète là où il est bas.

Plateformes : Binance, Bybit, Hyperliquid (API publiques, sans clé). Les rendements affichés sont **nets** des frais d'entrée et de sortie.
```
python -m funding.scanner                          # meilleures occasions du moment
python -m funding.scanner --confirm                # + moyenne 7 jours (un pic ponctuel ne suffit pas)
python -m funding.scanner --alert 0.25 --every 60  # alerte Telegram au-dessus de 25 %/an, toutes les heures
python -m funding.backtest download --exchange binance --top 40 --start 2022-01-01
python -m funding.backtest run --exchange binance  # rendement par année, vs BTC/ETH gardés en permanence
python -m funding.backtest grid --exchange binance # robustesse : 36 combinaisons
```
Règle testée : chaque semaine, on garde les 5 cryptos au financement moyen le plus haut sur 7 jours, à poids égaux, avec un levier de 3 sur le perpétuel (75 % du capital couvert).

Limites : l'écart entre le prix comptant et le prix du perpétuel n'est pas modélisé, et la liste des cryptos vient des volumes actuels.

## 2. Bot momentum altcoins
Suivi de tendance **agressif** sur les altcoins, testé sur les données Binance journalières.

## Règles testées
- **Filtre Bitcoin** : nouvelles entrées seulement si le BTC clôture au-dessus de sa moyenne 50 jours. Sinon, tout est fermé.
- **Univers** : toutes les paires USDT (stablecoins et tokens à levier exclus), avec plus de 5 M$ de volume moyen par jour et au moins 60 jours de cotation.
- **Entrée** : clôture au-dessus du plus haut des 20 derniers jours, avec au moins 2 fois le volume moyen. Les candidats sont classés par performance sur 30 jours, avec au plus 5 positions.
- **Risque** : 2 % du capital par trade (stop à 2,5 ATR), levier total plafonné à 3x.
- **Sorties** : moitié de la position à +3 R, le reste sur un stop suiveur (plus haute clôture − 3 ATR).
- **Coûts** : 0,05 % de frais + 0,05 % de glissement par ordre, 0,3 % de glissement en plus sur les stops, et environ 11 %/an de financement sur les positions.

## Utilisation
```
pip install -r requirements.txt
python -m momentum.data                  # télécharge les bougies 1d depuis 2020 (data/1d/)
python -m momentum.backtest              # rapport : CAGR, pire chute, par année, vs BTC acheté et gardé
python -m momentum.backtest --grid       # robustesse : 36 combinaisons de paramètres
python -m momentum.backtest --risk 0.03 --lev 5 --start 2021-01-01
python -m momentum.live --since 2026-10-13   # simulation en direct : point du jour (+ Telegram)
python -m pytest tests                   # tests (données synthétiques)
```
La simulation en direct est à lancer chaque jour vers 00:15 UTC, avec cron ou le Planificateur de tâches Windows. Elle rejoue les règles du backtest depuis la date de départ.
Les résultats détaillés (`equity.csv`, `trades.csv`) sont écrits dans `resultats/`.

## Limites connues
- Les paires retirées de la cote ne sont incluses que si Binance sert encore leur historique : il reste un biais du survivant, qui rend les résultats un peu trop beaux.
- Les données sont journalières : l'ordre des événements dans la journée est inconnu. On suppose que le stop passe avant l'objectif.
- Rien n'est branché en réel. Étapes suivantes si le backtest tient : quelques semaines de simulation en direct, puis petit compte séparé.
