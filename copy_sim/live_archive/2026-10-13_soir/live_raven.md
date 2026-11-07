_Mis à jour : 2026-10-13 18:01:42 UTC — en cours depuis 0.8 h_

**Capital ≈ 0.9405 SOL** (départ 1.0 SOL, cash 0.9405, positions au coût d'achat)

## Positions ouvertes

Aucune.

## 15 derniers événements

| heure UTC | type | token | SOL | prix vs leader | retard |
|---|---|---|---|---|---|
| 17:55:37 | SELL | AMuS…VadE | +0.0455 | -9.1% | 1.1 s |
| 17:54:28 | SELL | AMuS…VadE | +0.0410 | -6.2% | 0.85 s |
| 17:53:05 | BUY | AMuS…VadE | +0.0952 | +13.1% | 1.63 s |
| 17:32:52 | SELL | C9Td…Y3Ch | +0.0243 | -5.8% | 1.0 s |
| 17:31:43 | SELL | C9Td…Y3Ch | +0.0449 | -13.3% | 1.11 s |
| 17:31:39 | SELL | C9Td…Y3Ch | +0.0598 | -15.4% | 1.62 s |
| 17:30:53 | BUY | C9Td…Y3Ch | +0.0917 | +28.1% | 1.46 s |
| 17:10:36 | SELL | GWH6…Gvej | +0.0252 | -7.5% | 1.58 s |
| 17:09:43 | SELL | GWH6…Gvej | +0.0492 | -12.1% | 1.64 s |
| 17:09:07 | BUY | GWH6…Gvej | +0.0940 | +18.0% | 2.49 s |
| 14:30:08 | SELL | AF1K…F7uG | -0.0027 | -100.0% | 1.51 s |
| 14:29:53 | SELL | AF1K…F7uG | +0.0215 | -20.3% | 1.33 s |
| 14:29:52 | SELL | AF1K…F7uG | +0.0236 | -36.8% | 1.03 s |
| 14:29:42 | BUY | AF1K…F7uG | +0.1000 | +156.8% | 1.36 s |

# Simulation copy trading — paper trading live

Hypothèses : capital=1.0 SOL, taille=0.1 (fraction), retard=2.0s, slippage=100bps, frais bot=0.0%, frais tx=0.0027 SOL, rotation=après 0 pertes, max positions=5

## Résultat par scénario

| scénario | capital final (SOL) | rendement | trades clos | win rate | gain moyen | perte moyenne | profit factor | drawdown max | slippage d'entrée médian vs leader | ouvertes à la fin |
|---|---|---|---|---|---|---|---|---|---|---|
| live (cotations Jupiter réelles) | 0.940 | -6.0% | 4 | 25% | +0.0346 | -0.0314 | 0.37 | 8% | +23.1% | 0 (0 sans prix) |

## Trades ignorés (premier scénario)

- anti-rug : liquidité < 5000 $ : 10
- anti-rug : fiche token indisponible : 9
- anti-rug : pool de moins de 120 s : 8
- anti-rug : pool de moins de 60 s : 6

Rotations de leader : 0

## Par leader (premier scénario)

| leader | trades | gagnants | PnL SOL |
|---|---|---|---|
| 515v…pNRp | 4 | 1 | -0.0595 |

## Comment lire

- **neutral** et **pessimistic** encadrent la réalité ; si même *neutral* perd, la stratégie perd.
- Un win rate élevé avec un profit factor < 1 = beaucoup de petits gains, quelques grosses pertes.
- Le slippage d'entrée médian mesure combien plus cher que le leader on achète : c'est l'edge qu'il garde pour lui (et ce que les copieurs lui paient quand il revend).
