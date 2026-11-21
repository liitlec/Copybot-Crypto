_Mis à jour : 2026-10-13 18:01:03 UTC_

**Capital ≈ 0.1966 SOL** (départ 1.0 SOL, cash 0.1604, positions au coût d'achat)

## Positions ouvertes

| token | depuis | engagé SOL | prix d'entrée vs leader |
|---|---|---|---|
| 3sKa…pump | 16:53:06 | 0.0189 | +5.7% |
| 9v3v…pump | 16:57:19 | 0.0173 | +1.4% |

## 15 derniers événements

| heure UTC | type | token | SOL | prix vs leader | retard |
|---|---|---|---|---|---|
| 17:02:11 | SELL | Acxm…ETCH | +0.0050 | -0.7% | 0.74 s |
| 17:02:11 | SELL | Acxm…ETCH | +0.0132 | -5.4% | 1.45 s |
| 17:02:11 | SELL | Acxm…ETCH | +0.0136 | -5.3% | 1.31 s |
| 17:02:11 | SELL | Acxm…ETCH | +0.0111 | -3.9% | 1.14 s |
| 17:02:11 | SELL | Acxm…ETCH | +0.0116 | -1.6% | 0.94 s |
| 17:01:14 | SELL | CFsq…ETCH | +0.0084 | -11.4% | 1.36 s |
| 16:59:52 | BUY | CFsq…ETCH | +0.0168 | +35.0% | 1.73 s |
| 16:59:21 | BUY | Acxm…ETCH | +0.0168 | +15.8% | 1.54 s |
| 16:57:19 | BUY | 9v3v…pump | +0.0168 | +1.4% | 1.61 s |
| 16:55:44 | SELL | 9Aru…pump | +0.0100 | -3.0% | 1.46 s |
| 16:55:13 | SELL | B1Nc…pump | +0.0123 | -6.6% | 1.19 s |
| 16:55:11 | BUY | B1Nc…pump | +0.0184 | +6.5% | 1.3 s |
| 16:53:06 | BUY | 3sKa…pump | +0.0184 | +5.7% | 1.25 s |
| 16:52:47 | BUY | 9Aru…pump | +0.0184 | +3.3% | 1.12 s |
| 16:52:20 | SELL | 5tbA…dCsa | +0.0117 | +8.6% | 1.73 s |

# Simulation copy trading — paper trading live

Hypothèses : capital=1.0 SOL, taille=0.1 (fraction), retard=2.0s, slippage=100bps, frais bot=1.0%, frais tx=0.0005 SOL, rotation=après 2 pertes, max positions=5

## Résultat par scénario

| scénario | capital final (SOL) | rendement | trades clos | win rate | gain moyen | perte moyenne | profit factor | drawdown max | slippage d'entrée médian vs leader | ouvertes à la fin |
|---|---|---|---|---|---|---|---|---|---|---|
| live (cotations Jupiter réelles) | 0.197 | -80.3% | 49 | 10% | +0.0164 | -0.0201 | 0.09 | 84% | +9.6% | 0 (0 sans prix) |

## Trades ignorés (premier scénario)

- renforcement ignoré (position déjà ouverte) : 18
- pas de prix / pas de route à l'achat : 2

Rotations de leader : 0

## Par leader (premier scénario)

| leader | trades | gagnants | PnL SOL |
|---|---|---|---|
| PMJA…gyYN | 13 | 0 | -0.3183 |
| EHg5…Myaf | 9 | 1 | -0.2115 |
| 8Ltv…u6YP | 26 | 4 | -0.2671 |
| xyzf…StB6 | 1 | 0 | -0.0065 |

## Comment lire

- **neutral** et **pessimistic** encadrent la réalité ; si même *neutral* perd, la stratégie perd.
- Un win rate élevé avec un profit factor < 1 = beaucoup de petits gains, quelques grosses pertes.
- Le slippage d'entrée médian mesure combien plus cher que le leader on achète : c'est l'edge qu'il garde pour lui (et ce que les copieurs lui paient quand il revend).
