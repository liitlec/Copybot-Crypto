_Mis à jour : 2026-10-13 18:01:02 UTC_

**Capital ≈ 0.6713 SOL** (départ 1.0 SOL, cash 0.3976, positions au coût d'achat)

## Positions ouvertes

| token | depuis | engagé SOL | prix d'entrée vs leader |
|---|---|---|---|
| r7YR…pump | 16:04:38 | 0.0440 | +2.7% |
| HbXn…pump | 16:39:36 | 0.0348 | +4.1% |
| HbXn…pump | 16:54:45 | 0.0332 | -17.7% |
| 5sTx…pump | 16:59:37 | 0.0314 | -8.5% |
| 8HbB…pump | 17:05:28 | 0.0305 | +15.2% |
| DTBk…pump | 17:07:15 | 0.0309 | +12.4% |
| Achf…pump | 17:48:06 | 0.0348 | +18.8% |
| CDh6…pump | 17:54:04 | 0.0341 | +31.5% |

## 15 derniers événements

| heure UTC | type | token | SOL | prix vs leader | retard |
|---|---|---|---|---|---|
| 17:54:04 | BUY | CDh6…pump | +0.0336 | +31.5% | 1.39 s |
| 17:53:51 | SELL | NTRN…WyV6 | +0.0261 | -1.6% | 1.49 s |
| 17:51:41 | SELL | FCVo…pump | +0.0257 | -2.0% | 0.86 s |
| 17:48:06 | BUY | Achf…pump | +0.0343 | +18.8% | 1.23 s |
| 17:47:17 | SELL | 6W1Q…S6Gg | +0.0296 | -3.5% | 1.34 s |
| 17:44:01 | BUY | FCVo…pump | +0.0345 | +1.7% | 0.67 s |
| 17:42:25 | BUY | 6W1Q…S6Gg | +0.0345 | +0.1% | 1.23 s |
| 17:38:52 | SELL | 3XST…pump | +0.0261 | -1.7% | 0.96 s |
| 17:38:41 | SELL | GQdE…pump | +0.0362 | -2.1% | 1.56 s |
| 17:38:21 | SELL | cfou…pump | +0.0047 | -1.8% | 1.54 s |
| 17:37:41 | BUY | GQdE…pump | +0.0355 | +1.4% | 0.7 s |
| 17:36:38 | SELL | Cox5…pump | +0.0616 | +2.4% | 1.53 s |
| 17:36:11 | SELL | Cox5…pump | +0.0062 | -6.2% | 8.66 s |
| 17:36:11 | SELL | Cox5…pump | +0.0062 | -7.0% | 9.54 s |
| 17:36:11 | SELL | Cox5…pump | +0.0080 | -5.4% | 9.36 s |

# Simulation copy trading — paper trading live

Hypothèses : capital=1.0 SOL, taille=0.05 (fraction), retard=2.0s, slippage=100bps, frais bot=1.0%, frais tx=0.0005 SOL, rotation=après 2 pertes, max positions=15

## Résultat par scénario

| scénario | capital final (SOL) | rendement | trades clos | win rate | gain moyen | perte moyenne | profit factor | drawdown max | slippage d'entrée médian vs leader | ouvertes à la fin |
|---|---|---|---|---|---|---|---|---|---|---|
| live (cotations Jupiter réelles) | 0.671 | -32.9% | 72 | 21% | +0.0186 | -0.0107 | 0.46 | 45% | +1.9% | 0 (0 sans prix) |

## Trades ignorés (premier scénario)

- renforcement ignoré (position déjà ouverte) : 79
- pas de prix / pas de route à l'achat : 1

Rotations de leader : 0

## Par leader (premier scénario)

| leader | trades | gagnants | PnL SOL |
|---|---|---|---|
| 7Js5…nyVm | 43 | 12 | -0.1782 |
| 2T5N…UNBH | 2 | 1 | -0.0077 |
| CAPn…UJdw | 1 | 0 | -0.0173 |
| HbCx…kwft | 1 | 0 | -0.0097 |
| 5T22…mwEP | 13 | 1 | -0.0015 |
| 5ghU…G36N | 3 | 0 | -0.0697 |
| 9St6…j89U | 4 | 0 | -0.0538 |
| J9TY…C8MB | 1 | 0 | -0.0099 |
| 87rR…AAxJ | 1 | 1 | +0.0450 |
| B799…YFdR | 2 | 0 | -0.0205 |
| CXnf…e99m | 1 | 0 | -0.0054 |

## Comment lire

- **neutral** et **pessimistic** encadrent la réalité ; si même *neutral* perd, la stratégie perd.
- Un win rate élevé avec un profit factor < 1 = beaucoup de petits gains, quelques grosses pertes.
- Le slippage d'entrée médian mesure combien plus cher que le leader on achète : c'est l'edge qu'il garde pour lui (et ce que les copieurs lui paient quand il revend).
