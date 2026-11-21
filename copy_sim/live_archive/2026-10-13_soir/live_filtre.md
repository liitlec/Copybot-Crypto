_Mis à jour : 2026-10-13 18:01:42 UTC — en cours depuis 0.8 h_

**Capital ≈ 1.0436 SOL** (départ 1.0 SOL, cash 1.0436, positions au coût d'achat)

## Positions ouvertes

Aucune.

## 15 derniers événements

| heure UTC | type | token | SOL | prix vs leader | retard |
|---|---|---|---|---|---|
| 17:55:37 | SELL | AMuS…VadE | +0.0516 | -9.2% | 1.12 s |
| 17:54:28 | SELL | AMuS…VadE | +0.0468 | -6.2% | 0.86 s |
| 17:53:05 | BUY | AMuS…VadE | +0.1051 | +13.2% | 1.71 s |
| 17:32:52 | SELL | C9Td…Y3Ch | +0.0285 | -5.8% | 0.99 s |
| 17:31:43 | SELL | C9Td…Y3Ch | +0.0506 | -13.3% | 1.1 s |
| 17:31:39 | SELL | C9Td…Y3Ch | +0.0666 | -15.4% | 1.64 s |
| 17:30:53 | BUY | C9Td…Y3Ch | +0.1006 | +28.1% | 1.51 s |
| 17:10:36 | SELL | GWH6…Gvej | +0.0298 | -7.1% | 1.79 s |
| 17:09:42 | SELL | GWH6…Gvej | +0.0546 | -13.8% | 1.55 s |
| 17:09:06 | BUY | GWH6…Gvej | +0.1025 | +16.4% | 2.42 s |
| 14:29:53 | SELL | AF1K…F7uG | +0.0130 | -3.7% | 1.52 s |
| 14:29:51 | SELL | AF1K…F7uG | +0.0479 | -15.5% | 0.92 s |
| 14:29:49 | SELL | AF1K…F7uG | +0.0642 | -17.5% | 1.03 s |
| 14:29:26 | BUY | AF1K…F7uG | +0.1000 | +33.3% | 1.33 s |

# Simulation copy trading — paper trading live

Hypothèses : capital=1.0 SOL, taille=0.1 (fraction), retard=2.0s, slippage=100bps, frais bot=1.0%, frais tx=0.0005 SOL, rotation=après 2 pertes, max positions=5

## Résultat par scénario

| scénario | capital final (SOL) | rendement | trades clos | win rate | gain moyen | perte moyenne | profit factor | drawdown max | slippage d'entrée médian vs leader | ouvertes à la fin |
|---|---|---|---|---|---|---|---|---|---|---|
| live (cotations Jupiter réelles) | 1.044 | +4.4% | 4 | 50% | +0.0346 | -0.0129 | 2.70 | 2% | +22.3% | 0 (0 sans prix) |

## Trades ignorés (premier scénario)

- anti-rug : liquidité < 5000 $ : 10
- anti-rug : fiche token indisponible : 9
- anti-rug : pool de moins de 120 s : 8
- anti-rug : pool de moins de 60 s : 6

Rotations de leader : 0

## Par leader (premier scénario)

| leader | trades | gagnants | PnL SOL |
|---|---|---|---|
| 515v…pNRp | 4 | 2 | +0.0436 |

## Comment lire

- **neutral** et **pessimistic** encadrent la réalité ; si même *neutral* perd, la stratégie perd.
- Un win rate élevé avec un profit factor < 1 = beaucoup de petits gains, quelques grosses pertes.
- Le slippage d'entrée médian mesure combien plus cher que le leader on achète : c'est l'edge qu'il garde pour lui (et ce que les copieurs lui paient quand il revend).
