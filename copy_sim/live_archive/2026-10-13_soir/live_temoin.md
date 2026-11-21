_Mis à jour : 2026-10-13 18:01:43 UTC — en cours depuis 0.8 h_

**Capital ≈ 1.4784 SOL** (départ 1.0 SOL, cash 1.2939, positions au coût d'achat)

## Positions ouvertes

| token | depuis | engagé SOL | prix d'entrée vs leader |
|---|---|---|---|
| EnNX…pux5 | 10:36:25 | 0.1005 | +1.5% |
| 8k68…rkga | 16:55:07 | 0.1250 | +8.6% |

## 15 derniers événements

| heure UTC | type | token | SOL | prix vs leader | retard |
|---|---|---|---|---|---|
| 17:55:37 | SELL | AMuS…VadE | +0.0730 | -9.2% | 1.1 s |
| 17:54:28 | SELL | AMuS…VadE | +0.0662 | -6.2% | 0.87 s |
| 17:53:04 | BUY | AMuS…VadE | +0.1488 | +13.5% | 1.23 s |
| 17:46:56 | SELL | Eo4g…C5MV | +0.0394 | -3.9% | 1.56 s |
| 17:46:34 | SELL | Eo4g…C5MV | +0.0993 | -10.4% | 1.02 s |
| 17:46:09 | BUY | Eo4g…C5MV | +0.1500 | +3.1% | 1.05 s |
| 17:43:45 | SELL | 9Pk4…Qbyh | +0.1358 | -13.8% | 1.42 s |
| 17:43:05 | BUY | 9Pk4…Qbyh | +0.1517 | +15.0% | 1.55 s |
| 17:39:30 | SELL | 5C9m…d5JH | +0.0525 | -6.4% | 1.49 s |
| 17:38:39 | SELL | 5C9m…d5JH | +0.0903 | -3.9% | 2.82 s |
| 17:37:52 | SELL | 5C9m…d5JH | +0.0901 | -11.0% | 1.03 s |
| 17:37:48 | SELL | 5C9m…d5JH | +0.1043 | -12.2% | 1.49 s |
| 17:37:13 | BUY | 5C9m…d5JH | +0.1311 | +3.9% | 0.91 s |
| 17:32:52 | SELL | C9Td…Y3Ch | +0.0356 | -5.9% | 0.97 s |
| 17:31:43 | SELL | C9Td…Y3Ch | +0.0629 | -13.3% | 1.09 s |

# Simulation copy trading — paper trading live

Hypothèses : capital=1.0 SOL, taille=0.1 (fraction), retard=2.0s, slippage=100bps, frais bot=1.0%, frais tx=0.0005 SOL, rotation=après 2 pertes, max positions=5

## Résultat par scénario

| scénario | capital final (SOL) | rendement | trades clos | win rate | gain moyen | perte moyenne | profit factor | drawdown max | slippage d'entrée médian vs leader | ouvertes à la fin |
|---|---|---|---|---|---|---|---|---|---|---|
| live (cotations Jupiter réelles) | 1.478 | +47.8% | 29 | 55% | +0.0440 | -0.0174 | 3.11 | 6% | +5.7% | 0 (0 sans prix) |

## Trades ignorés (premier scénario)

- renforcement ignoré (position déjà ouverte) : 6

Rotations de leader : 5

## Par leader (premier scénario)

| leader | trades | gagnants | PnL SOL |
|---|---|---|---|
| 515v…pNRp | 29 | 16 | +0.4784 |

## Comment lire

- **neutral** et **pessimistic** encadrent la réalité ; si même *neutral* perd, la stratégie perd.
- Un win rate élevé avec un profit factor < 1 = beaucoup de petits gains, quelques grosses pertes.
- Le slippage d'entrée médian mesure combien plus cher que le leader on achète : c'est l'edge qu'il garde pour lui (et ce que les copieurs lui paient quand il revend).
