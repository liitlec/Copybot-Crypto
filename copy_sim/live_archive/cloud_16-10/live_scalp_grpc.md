_Mis à jour : 2026-10-16 15:36:53 — test démarré le 16/10 06:14 (cloud, hub gRPC Chainstack), règles du PC (prereg/scalp_rule.json du 15/10)_

Paper trading : état exact des courbes pump.fun enregistré en gRPC, mise 0.1 SOL par trade, frais pump.fun 1.25 % par côté. Les lancements que personne n'achète ensuite sont comptés.

| variante | trades | moyenne / trade | ± | gagnants | total SOL | sans les 3 meilleurs |
|---|---|---|---|---|---|---|
| B confirmé : +5 s, au moins 1 autre acheteur | 4647 | -0.05% | 0.41% | 21% | -0.243 | -0.53% |
| A brut : +1 s, sans confirmation | 8369 | -1.09% | 0.21% | 12% | -9.093 | -1.30% |
| C : entrée de B, gardée au-delà de 60 s si ≥ +20 %, stop suiveur −30 %, max 9 min | 4392 | -0.12% | 0.44% | 20% | -0.521 | -0.61% |
| B sur les mêmes lancements que C | 4392 | +0.04% | 0.42% | 21% | +0.174 | -0.46% |
| E : entrée de B, moitié vendue à ×2, reste stop suiveur −40 % ; sans ×2 à 60 s, sortie de C ; max 9 min | 3983 | +1.44% | 0.48% | 21% | +5.719 | +0.88% |
| B sur les mêmes lancements que E | 3983 | +0.09% | 0.46% | 21% | +0.371 | -0.46% |
| D : score de qualité (20 % meilleurs) + sortie C | 817 | +2.42% | 1.10% | 29% | +1.976 | +1.25% |
| F : sélection du score (comme D), sortie de E | 811 | +5.97% | 1.46% | 30% | +4.845 | +4.32% |
| D sur les mêmes lancements que F | 811 | +2.39% | 1.10% | 29% | +1.935 | +1.21% |
| F sur la même période que G | 387 | +7.58% | 2.46% | 34% | +2.935 | +4.79% |
| même sélection, revente à 60 s | 817 | +2.71% | 1.09% | 30% | +2.213 | +1.48% |
| tous les lancements, sortie C | 8942 | -2.41% | 0.23% | 11% | -21.515 | -2.66% |
| G : F seulement si B des 30 dernières minutes > 0 | 126 | +3.63% | 2.92% | 37% | +0.457 | +0.18% |
| F sur la même période que G | 387 | +7.58% | 2.46% | 34% | +2.935 | +4.79% |
| H : E seulement si B des 30 dernières minutes > 0 | 578 | +1.02% | 0.90% | 26% | +0.589 | +0.19% |
| E sur la même période que H | 2070 | +1.08% | 0.58% | 22% | +2.241 | +0.55% |

Verdict prévu (A, B) : après au moins 1 000 trades de B : gagnant seulement si la moyenne dépasse 2 fois sa marge d'erreur ET reste positive sans les 3 meilleurs trades
Verdict prévu (C) : après au moins 1 000 trades de C : gagnant seulement si la moyenne dépasse 2 fois sa marge d'erreur, reste positive sans les 3 meilleurs trades ET bat B sur les mêmes lancements

C n'est compté que sur les lancements postérieurs à sa fixation (prereg/scalp_rule_c.json), avec 9 min de suivi complètes ; la ligne « B sur les mêmes lancements » sert de comparaison directe.

## 15 derniers trades (variante principale)

| heure | token | résultat |
|---|---|---|
| 15:33:51 | FFwr…pump | -7.5% |
| 15:33:46 | 4YPr…pump | +17.1% |
| 15:33:46 | EpFV…pump | -3.8% |
| 15:33:44 | 5ZmU…pump | -4.7% |
| 15:33:41 | 7DTN…pump | +7.3% |
| 15:33:31 | Fxn5…pump | -9.0% |
| 15:33:28 | 9xxb…pump | -2.1% |
| 15:33:24 | BRCE…pump | +79.8% |
| 15:33:12 | 936v…pump | -12.4% |
| 15:33:09 | EG1i…pump | -3.2% |
| 15:33:05 | GoSE…pump | +2.1% |
| 15:33:02 | GAeu…pump | +4.9% |
| 15:33:02 | 7S9x…pump | -1.8% |
| 15:33:00 | 3sM3…pump | -11.0% |
| 15:32:52 | AZ8y…pump | +1.6% |
