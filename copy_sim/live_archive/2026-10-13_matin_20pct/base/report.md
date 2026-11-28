_Mis à jour : 2026-10-13 10:30:04 UTC — en cours depuis 0.1 h_

**Capital ≈ 1.0057 SOL** (départ 1.0 SOL, cash 0.6072, positions au coût d'achat)

## Positions ouvertes

| token | depuis | engagé SOL | prix d'entrée vs leader |
|---|---|---|---|
| ESMF…Ma1g | 09:54:56 | 0.1969 | +2.3% |
| DTbz…DX4J | 10:18:01 | 0.2016 | +11.6% |

## 15 derniers événements

| heure UTC | type | token | SOL | prix vs leader | retard |
|---|---|---|---|---|---|
| 10:18:01 | BUY | DTbz…DX4J | +0.2011 | +11.6% | 1.11 s |
| 10:14:44 | SELL | EJNL…yUjm | +0.1388 | -3.9% | 1.88 s |
| 10:14:34 | SELL | EJNL…yUjm | +0.0940 | -1.9% | 1.63 s |
| 10:12:52 | BUY | EJNL…yUjm | +0.1934 | +6.8% | 1.14 s |
| 10:11:46 | SELL | EJNL…yUjm | +0.1060 | -4.3% | 1.37 s |
| 10:11:27 | SELL | EJNL…yUjm | +0.0970 | -3.2% | 1.11 s |
| 10:10:56 | BUY | EJNL…yUjm | +0.1911 | +10.0% | 1.43 s |
| 10:08:42 | SELL | 3ygF…i3mV | +0.0812 | -6.7% | 0.89 s |
| 10:08:38 | SELL | 3ygF…i3mV | +0.0873 | -8.8% | 1.02 s |
| 10:08:03 | BUY | 3ygF…i3mV | +0.1969 | +17.3% | 0.91 s |
| 10:07:41 | SELL | 3ygF…i3mV | +0.1711 | -8.2% | 0.82 s |
| 10:06:47 | BUY | 3ygF…i3mV | +0.2034 | +2.0% | 1.25 s |
| 10:05:29 | SELL | E1yY…f8rj | +0.1736 | -8.8% | 1.12 s |
| 10:05:21 | BUY | E1yY…f8rj | +0.2110 | +6.1% | 0.99 s |
| 10:00:22 | SELL | Cn78…WsLz | +0.2331 | -5.0% | 1.61 s |

# Simulation copy trading — paper trading live

Hypothèses : capital=1.0 SOL, taille=0.2 (fraction), retard=2.0s, slippage=100bps, frais bot=1.0%, frais tx=0.0005 SOL, rotation=après 2 pertes, max positions=5

## Résultat par scénario

| scénario | capital final (SOL) | rendement | trades clos | win rate | gain moyen | perte moyenne | profit factor | drawdown max | slippage d'entrée médian vs leader | ouvertes à la fin |
|---|---|---|---|---|---|---|---|---|---|---|
| live (cotations Jupiter réelles) | 1.006 | +0.6% | 14 | 50% | +0.0234 | -0.0226 | 1.04 | 9% | +6.4% | 0 (0 sans prix) |

## Trades ignorés (premier scénario)

- renforcement ignoré (position déjà ouverte) : 1

Rotations de leader : 3

## Par leader (premier scénario)

| leader | trades | gagnants | PnL SOL |
|---|---|---|---|
| 515v…pNRp | 14 | 7 | +0.0057 |

## Comment lire

- **neutral** et **pessimistic** encadrent la réalité ; si même *neutral* perd, la stratégie perd.
- Un win rate élevé avec un profit factor < 1 = beaucoup de petits gains, quelques grosses pertes.
- Le slippage d'entrée médian mesure combien plus cher que le leader on achète : c'est l'edge qu'il garde pour lui (et ce que les copieurs lui paient quand il revend).
