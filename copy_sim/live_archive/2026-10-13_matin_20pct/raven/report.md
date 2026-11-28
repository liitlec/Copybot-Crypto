_Mis à jour : 2026-10-13 10:30:21 UTC — en cours depuis 0.9 h_

**Capital ≈ 0.9864 SOL** (départ 1.0 SOL, cash 0.5879, positions au coût d'achat)

## Positions ouvertes

| token | depuis | engagé SOL | prix d'entrée vs leader |
|---|---|---|---|
| ESMF…Ma1g | 09:54:35 | 0.1985 | +10.4% |
| DTbz…DX4J | 10:18:01 | 0.2000 | +11.5% |

## 15 derniers événements

| heure UTC | type | token | SOL | prix vs leader | retard |
|---|---|---|---|---|---|
| 10:18:01 | BUY | DTbz…DX4J | +0.1973 | +11.5% | 1.11 s |
| 10:14:44 | SELL | EJNL…yUjm | +0.1370 | -3.9% | 1.89 s |
| 10:14:34 | SELL | EJNL…yUjm | +0.0921 | -1.9% | 1.64 s |
| 10:12:52 | BUY | EJNL…yUjm | +0.1900 | +6.8% | 1.14 s |
| 10:11:46 | SELL | EJNL…yUjm | +0.1044 | -4.3% | 1.38 s |
| 10:11:27 | SELL | EJNL…yUjm | +0.0953 | -3.2% | 1.11 s |
| 10:10:56 | BUY | EJNL…yUjm | +0.1883 | +10.0% | 1.44 s |
| 10:08:42 | SELL | 3ygF…i3mV | +0.0797 | -6.7% | 0.9 s |
| 10:08:38 | SELL | 3ygF…i3mV | +0.0858 | -8.8% | 1.02 s |
| 10:08:03 | BUY | 3ygF…i3mV | +0.1946 | +17.3% | 0.92 s |
| 10:07:41 | SELL | 3ygF…i3mV | +0.1654 | -8.2% | 0.82 s |
| 10:06:47 | BUY | 3ygF…i3mV | +0.2026 | +5.8% | 1.26 s |
| 10:05:29 | SELL | E1yY…f8rj | +0.1790 | -8.9% | 1.13 s |
| 10:05:21 | BUY | E1yY…f8rj | +0.2092 | +2.8% | 0.99 s |
| 10:00:22 | SELL | Cn78…WsLz | +0.2335 | -5.0% | 1.59 s |

# Simulation copy trading — paper trading live

Hypothèses : capital=1.0 SOL, taille=0.2 (fraction), retard=2.0s, slippage=100bps, frais bot=0.0%, frais tx=0.0027 SOL, rotation=après 0 pertes, max positions=5

## Résultat par scénario

| scénario | capital final (SOL) | rendement | trades clos | win rate | gain moyen | perte moyenne | profit factor | drawdown max | slippage d'entrée médian vs leader | ouvertes à la fin |
|---|---|---|---|---|---|---|---|---|---|---|
| live (cotations Jupiter réelles) | 0.986 | -1.4% | 13 | 46% | +0.0262 | -0.0244 | 0.92 | 10% | +5.8% | 0 (0 sans prix) |

## Trades ignorés (premier scénario)

- renforcement ignoré (position déjà ouverte) : 1

Rotations de leader : 0

## Par leader (premier scénario)

| leader | trades | gagnants | PnL SOL |
|---|---|---|---|
| 515v…pNRp | 13 | 6 | -0.0136 |

## Comment lire

- **neutral** et **pessimistic** encadrent la réalité ; si même *neutral* perd, la stratégie perd.
- Un win rate élevé avec un profit factor < 1 = beaucoup de petits gains, quelques grosses pertes.
- Le slippage d'entrée médian mesure combien plus cher que le leader on achète : c'est l'edge qu'il garde pour lui (et ce que les copieurs lui paient quand il revend).
