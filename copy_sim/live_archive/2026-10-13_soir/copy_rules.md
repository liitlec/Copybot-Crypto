# Règles de copie pré-enregistrées

Fixées le 2026-10-13 16:00:36 UTC ; évaluées uniquement sur les trades ouverts après. Écart de PnL (SOL) par rapport à la copie simple, sur les mêmes trades.

| test | trades | PnL copie simple | R1 prix d'entrée max | R2 moitié à +50 % | R3 confluence |
|---|---|---|---|---|---|
| data | 13 | +0.2111 | -0.0283 (2 trades ; +0.0277 / -0.0560) | +0.1054 (4 trades ; +0.0289 / +0.0764) | +0.0000 (0 trades ; +0.0000 / +0.0000) |
| data_filtre | 3 | +0.0190 | -0.0447 (1 trades ; +0.0000 / -0.0447) | +0.0373 (2 trades ; +0.0000 / +0.0373) | +0.0000 (0 trades ; +0.0000 / +0.0000) |
| data_raven | 3 | +0.0008 | -0.0346 (1 trades ; +0.0000 / -0.0346) | +0.0152 (1 trades ; +0.0000 / +0.0152) | +0.0000 (0 trades ; +0.0000 / +0.0000) |
| data_cands | 52 | -0.2079 | +0.0137 (2 trades ; +0.0137 / +0.0000) | -0.0314 (3 trades ; +0.0000 / -0.0314) | +0.0000 (0 trades ; +0.0000 / +0.0000) |
| data_scalp | 35 | -0.3572 | +0.0505 (6 trades ; +0.0198 / +0.0307) | +0.0300 (4 trades ; +0.0433 / -0.0133) | -0.0498 (3 trades ; -0.0498 / +0.0000) |

Entre parenthèses : trades concernés ; écart sur la 1re / 2e moitié chronologique.

Critères : ≥ 50 trades, amélioration du PnL total et sur chaque moitié.

- data / R1 : ⏳ 13/50 trades
- data / R2 : ⏳ 13/50 trades
- data / R3 : ⏳ 13/50 trades
- data_filtre / R1 : ⏳ 3/50 trades
- data_filtre / R2 : ⏳ 3/50 trades
- data_filtre / R3 : ⏳ 3/50 trades
- data_raven / R1 : ⏳ 3/50 trades
- data_raven / R2 : ⏳ 3/50 trades
- data_raven / R3 : ⏳ 3/50 trades
- data_cands / R1 : ❌ rejetée
- data_cands / R2 : ❌ rejetée
- data_cands / R3 : ❌ rejetée
- data_scalp / R1 : ⏳ 35/50 trades
- data_scalp / R2 : ⏳ 35/50 trades
- data_scalp / R3 : ⏳ 35/50 trades

R2 n'est évaluable que sur les trades qui ont des cotations enregistrées (--record-paths).
