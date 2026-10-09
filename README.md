# Copybot-Crypto : bot momentum altcoins

Projet crypto séparé des EA MT5. Il s'agit d'un bot **agressif** de suivi de tendance sur les altcoins, testé d'abord en backtest, sur données Binance journalières.

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
python -m pytest tests                   # tests de mécanique (données synthétiques)
```
Les résultats détaillés (`equity.csv`, `trades.csv`) sont écrits dans `resultats/`.

## Limites connues
- Les paires retirées de la cote ne sont incluses que si Binance sert encore leur historique : il reste un biais du survivant, qui rend les résultats un peu trop beaux.
- Les données sont journalières : l'ordre des événements dans la journée est inconnu. On suppose que le stop passe avant l'objectif.
- Rien n'est encore branché en réel. Étapes suivantes si le backtest tient : simulation en direct, puis petit compte séparé.
