# Résultats des backtests (12/10/2026)

Données réelles, frais compris. Sources : miroir public Binance (data-api.binance.vision), archives Binance (data.binance.vision) et API Hyperliquid.

## Arbitrage des taux de financement (comptant + perpétuel, levier 3 sur le perpétuel)

| Version | Plateforme, période | Rendement/an | Pire chute | Semaines négatives |
|---|---|---|---|---|
| **BTC + ETH en permanence** | Hyperliquid, 07/2023 → 10/2026 | **+11,1 %** | −0,4 % | 8/172 |
| **BTC + ETH en permanence** | Binance, 2021 → 10/2026 | **+8,4 %** | −0,6 % | 32/299 |
| Rotation des 5 meilleurs taux (7 j, hebdo) | Hyperliquid | +12,0 % | −3,0 % | 59/172 |
| Rotation des 5 meilleurs taux (7 j, hebdo) | Binance | +1,4 % | −17,3 % | 196/299 |

Par année, BTC + ETH en permanence :
- **Binance :** 2021 +26,5 %, 2022 +1,9 %, 2023 +6,2 %, 2024 +9,8 %, 2025 +3,8 %, 2026 +1,4 %.
- **Hyperliquid :** 2023 (depuis juillet) +7,1 %, 2024 +19,0 %, 2025 +7,5 %, 2026 +3,3 %.

Grilles de 36 réglages de la rotation :
- **Hyperliquid :** 30/36 rentables, médiane +10,9 %/an. La meilleure (lookback 14 j, hebdo) fait +16 à +18 %/an.
- **Binance :** 18/36 rentables, médiane 0 %/an.
- Changer de position chaque jour perd partout, à cause des frais.

**Conclusion :** courir après les taux les plus hauts n'apporte rien de fiable, car les pics retombent et peuvent devenir très négatifs sur les petites cryptos. Le montage simple BTC + ETH en permanence est le plus régulier.

**Limites :**
- L'écart de prix entre comptant et perpétuel n'est pas modélisé.
- Sur Hyperliquid, la couverture au comptant se fait ailleurs.
- Les rendements baissent nettement depuis 2025.

## Bot momentum altcoins (06/2020 → 10/2026, 678 paires Binance)

| | Bot (réglages de base) | BTC acheté et gardé |
|---|---|---|
| 10 000 $ deviennent | 21 154 $ | 82 124 $ |
| Rendement/an | +12,5 % | ≈ +39 % |
| Pire chute | −56,9 % | −77 % |

Par année, bot puis BTC acheté et gardé :

| Année | Bot | BTC |
|---|---|---|
| 2020 (depuis juin) | +29 % | +184 % |
| 2021 | +34 % | +60 % |
| 2022 | −10 % | −64 % |
| 2023 | +85 % | +156 % |
| 2024 | −12 % | +121 % |
| 2025 | −25 % | −6 % |
| 2026 | +11 % | −4 % |

Grille de 36 réglages : 34/36 rentables, médiane +11,6 %/an, mais pire chute médiane −56 %. La meilleure variante (stop suiveur 4 ATR, filtre BTC 100 j, risque 1 %) fait +12,4 %/an pour une pire chute de −30 %.

**Conclusion :** pas assez bon tel quel. Le bot protège en 2022 mais rate la plupart des hausses, et il demande d'encaisser des chutes de 30 à 60 %.

## Variantes de l'arbitrage (12/10/2026)

**Règle de sortie quand le taux moyen devient négatif : moins bien que rester en permanence**, à cause des frais et des taux qui remontent vite.
- Binance, BTC + ETH : +6,7 à +6,9 %/an avec la règle, contre +8,4 % en permanence.
- Hyperliquid, BTC + ETH : +9,6 à +10,3 %/an, contre +11,1 %.

**Base BTC + ETH permanente, plus 2 altcoins seulement si leur taux moyen sur 14 jours dépasse 20 %/an** (contrôle chaque semaine) :

| | Binance | Hyperliquid |
|---|---|---|
| Rendement/an | +8,9 % | **+15,3 %** |
| Pire chute | −0,6 % | −0,4 % |

**Leviers de gain** (sur la base BTC + ETH + 2 altcoins à plus de 20 %) :

| Levier | Binance | Hyperliquid |
|---|---|---|
| Référence : levier 3, 75 % couvert, frais taker | +8,9 % | +15,3 % |
| Levier 5, 83 % couvert | +9,9 % | +17,1 % |
| Comptant servant de marge, ~95 % couvert | +11,4 % | +19,8 % |
| Frais maker | +10,0 % | +17,6 % |
| ETH stakée au comptant (+3 %/an) | +9,9 % | +16,1 % |
| **Tout combiné** | **+14,2 %** | **+23,9 %** |

**Taux bruts BTC / ETH, 90 derniers jours** (par an, sur le notionnel, avant frais) :

| Plateforme | BTC | ETH |
|---|---|---|
| Hyperliquid | +8,4 % | +9,1 % |
| Binance (78 j) | +6,4 % | +4,9 % |
| BingX | +5,9 % | +5,7 % |
| MEXC | +5,8 % | +4,5 % |
| Aster | +5,7 % | +5,4 % |
| Bitget | +5,6 % | +6,4 % |
| OKX | +5,3 % | +4,2 % |
| KuCoin (33 j) | +3,9 % | +4,7 % |
| Gate (30 j) | +3,5 % | +3,3 % |
| dYdX | +0,3 % | −0,9 % |

## Pistes pour augmenter le gain (12/10/2026)

**Écart de taux entre Hyperliquid et Binance** (vendre le perpétuel là où le taux est haut, l'acheter là où il est bas ; 27 cryptos communes, 07/2023 → 09/2026) :
- 3 meilleurs écarts au-dessus de 10 %/an, levier 3 par jambe : +15,4 %/an, pire chute −4,1 %.
- Par année : 2023 +27,5 %, 2024 +25,6 %, 2025 +0,6 %, 2026 −1,1 %.
- L'écart a disparu depuis 2025.

**Arbitrage avec emprunt** (BTC + ETH + altcoins à plus de 20 %, Hyperliquid ; calcul simplifié, coût d'emprunt fixe) :

| Exposition | Taux d'emprunt | Rendement/an | Pire chute | 2024 | 2026 |
|---|---|---|---|---|---|
| 1,5 fois le capital | 6 %/an | +29,0 % | −1,4 % | +53,0 % | +9,5 % |
| 2 fois le capital | 6 %/an | +37,6 % | −2,1 % | +72,8 % | +11,1 % |
| 2 fois le capital | 9 %/an | +33,5 % | −3,6 % | – | – |

Hypothèse optimiste : en pratique, le taux d'emprunt monte justement quand les taux de financement sont hauts, et le risque de liquidation augmente avec l'emprunt.

## Plateformes qui distribuent des points (état au 12/10/2026)

**Token déjà lancé, plus d'airdrop à attendre :** Hyperliquid, Lighter, Aster, edgeX (03/2026), Paradex (05/03/2026), GRVT (30/07/2026).

**Points en cours, token pas encore lancé :**
- Variational : 32 % de l'offre prévue en airdrop, lancement visé T4 2026.
- PERPTools : saison 2 depuis le 02/10/2026, lancement visé fin T4 2026.
- Backpack : saison 4, 25 % prévus pour la communauté.
- Pacifica et Extended : informations récentes non vérifiées.

**Taux BTC / ETH relevés le 12/10/2026, par an :**

| Plateforme | BTC | ETH | Type de mesure |
|---|---|---|---|
| Backpack | +7,4 % | +9,8 % | moyenne 30 j |
| Pacifica | +11,0 % | +11,0 % | instantané |
| Extended | +11,4 % | +8,8 % | instantané |
| Variational | ≈ +8,3 % | ≈ +6,9 % | instantané, affiché annualisé |
| Repère Hyperliquid | +6,5 % | +5,8 % | moyenne 7 j |

## Levier qui s'adapte et rotation rapide (12/10/2026)

Base : BTC + ETH permanents, plus 2 altcoins à plus de 20 % (moyenne 14 j), frais maker, 95 % couvert, ETH stakée.

**Rotation plus rapide des altcoins** (tous les 1 à 3 jours) : pas mieux que la rotation hebdomadaire.
- Hyperliquid : +21,5 à +23,1 %/an, contre +23,9 % en hebdomadaire.

**Levier qui s'adapte** : emprunt seulement quand le taux moyen 14 j de BTC/ETH dépasse le coût de l'emprunt ; taille revue chaque semaine ; emprunt supposé fixe à 6 %/an.

| Règle | Hyperliquid | Binance |
|---|---|---|
| Sans emprunt | +23,9 % (pire chute −0,4 %) | +14,2 % (−0,7 %) |
| 1,5x si taux > emprunt + 5 pts | +31,1 % (−0,6 %) | +18,2 % (−0,7 %) |
| 1,5x / 2x si > +5 / +10 pts | **+37,1 %** (−0,8 %) | **+21,8 %** (−0,7 %) |
| 2x / 3x si > +5 / +10 pts | +51,7 % (−1,2 %) | +30,0 % (−1,0 %) |
| 2x en permanence | +44,5 % (−1,3 %) | +22,8 % (−1,9 %) |

Part du temps avec emprunt : 38 % sur Hyperliquid, 21 % sur Binance. Les gains en plus viennent surtout de 2021 et 2024 ; en 2026, presque rien (taux trop bas).

**Hypothèses optimistes :**
- Le taux d'emprunt est fixé à 6 %, alors qu'en pratique il monte quand le financement est haut (souvent 10 à 20 % en 2021 et 2024).
- Le risque de liquidation n'est pas modélisé, et il augmente nettement à 2x et 3x.

## Deuxième algo : tendance BTC/ETH (12/10/2026, Binance, 15/01/2021 → 30/09/2026)

Règle : BTC et ETH détenus sans couverture quand la clôture dépasse la moyenne 50 jours, avec une taille réduite si la volatilité 20 j dépasse 40 %/an. Sinon, arbitrage neutre. Mélanges rééquilibrés chaque jour.

| Stratégie | Rendement/an | Pire chute | Mois négatifs | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|
| BTC + ETH achetés et gardés | +17,1 % | −76,3 % | 31/69 | +97 % | −65 % | +123 % | +83 % | −6 % | −6 % |
| Arbitrage optimisé | +14,2 % | −0,7 % | 4/69 | +45 % | +4 % | +10 % | +18 % | +7 % | +2 % |
| Tendance seule (SMA50) | +34,2 % | −40,8 % | 31/69 | +62 % | −30 % | +87 % | +55 % | +27 % | +27 % |
| 80 % arbitrage + 20 % tendance | +18,7 % | −5,8 % | 19/69 | +49 % | −4 % | +23 % | +25 % | +11 % | +7 % |
| **70 % arbitrage + 30 % tendance** | **+20,8 %** | **−11,0 %** | 24/69 | +51 % | −7 % | +30 % | +29 % | +13 % | +10 % |
| 50 % arbitrage + 50 % tendance | +25,0 % | −20,6 % | 25/69 | +55 % | −14 % | +45 % | +37 % | +18 % | +15 % |

Corrélation journalière tendance/arbitrage : 0,08.

Robustesse : avec la moyenne 100 jours, la tendance seule fait +23,7 %/an (pire chute −36,5 %), et le mélange 70/30 +17,9 % (−9,2 %). La moyenne 50 jours est la meilleure des trois testées (50, 100, 200), donc un peu optimiste.

**Piste écartée : acheter quand le taux de financement est très négatif.**
- 52 cryptos, seuils de −30 à −300 %/an, détention de 3 à 14 jours.
- Médiane négative partout, et moins de 50 % de trades gagnants.
- Aucun avantage fiable.

## Tout sur Hyperliquid : arbitrage + emprunt quand ça paie + tendance (01/07/2023 → 11/10/2026)

Commande : `python -m tendance.algo backtest --exchange hyperliquid --start 2023-07-01 --borrow 0.06`

| Stratégie | Rendement/an | Pire chute | Mois négatifs | 2023 (dès juillet) | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| BTC + ETH achetés et gardés | +23,8 % | −59,9 % | 18/40 | +29 % | +83 % | −6 % | −9 % |
| Arbitrage optimisé, sans emprunt | +23,9 % | −0,4 % | 1/40 | +15 % | +38 % | +16 % | +10 % |
| Arbitrage + emprunt quand ça paie (6 %) | +37,1 % | −0,8 % | 1/40 | +26 % | +71 % | +19 % | +10 % |
| Tendance seule (SMA50) | +45,9 % | −21,4 % | 17/40 | +34 % | +61 % | +30 % | +23 % |
| **80 % arbitrage+emprunt / 20 % tendance** | **+39,7 %** | **−2,9 %** | 5/40 | +28 % | +70 % | +22 % | +13 % |
| **70 % / 30 %** | **+40,8 %** | **−4,6 %** | 9/40 | +29 % | +69 % | +23 % | +15 % |
| 50 % / 50 % | +42,8 % | −8,1 % | 14/40 | +30 % | +68 % | +25 % | +18 % |

L'emprunt est actif 39 % du temps (1,5x : 11 %, 2x : 28 %).

**Sensibilité :**
- Emprunt à 9 % : 80/20 → +37,6 %/an, 70/30 → +38,9 %/an.
- Moyenne 100 jours : 80/20 → +36,5 %/an (pire chute −2,6 %), 70/30 → +36,1 % (−4,0 %).

**1 000 € du 01/01 au 11/10/2026 sur Hyperliquid :**

| Stratégie | Résultat | Pire mois |
|---|---|---|
| Arbitrage sans emprunt | 1 097 € | – |
| Arbitrage + emprunt | 1 098 € (l'emprunt ne s'est presque pas déclenché) | – |
| 80/20 | 1 130 € | −1,1 % |
| 70/30 | 1 145 € | −1,8 % |
| 50/50 | 1 173 € | −3,2 % |
| Tendance seule | 1 234 € | −6,7 % |

**Scénario krach** (même montage sur Binance, qui couvre 2022) :

| Stratégie | 2022 | Pire chute |
|---|---|---|
| 80/20 | −3,6 % | −5,8 % |
| 70/30 | −7,2 % | −10,6 % |
| 50/50 | −14,0 % | −20,3 % |
| Tendance seule | −29,7 % | −40,8 % |

**Limites :**
- La période Hyperliquid ne contient pas de krach.
- L'emprunt est supposé à taux fixe, et la liquidation n'est pas modélisée.
- Les altcoins se couvrent au comptant hors d'Hyperliquid.
- La moyenne 50 jours est un peu optimiste.

## Encore plus de gain ? Tests de robustesse (13/10/2026)

Chaque idée est testée sur deux périodes : Hyperliquid 07/2023 → 10/2026, et Binance 2021 → 09/2026, qui contient le krach de 2022. Tendance BTC + ETH, volatilité cible 40 %, sauf mention contraire.

| Variante de la tendance | Hyperliquid : rendement / pire chute | Binance 2021-26 : rendement / pire chute |
|---|---|---|
| Référence : BTC + ETH, SMA50 | +45,9 % / −21,4 % | +34,2 % / −40,8 % |
| + SOL | +46,0 % / −25,2 % | +38,4 % / −42,2 % |
| + SOL + XRP (+ BNB) | +40,0 % / −24,3 % | +33,0 à +36,3 % / −39 à −40 % |
| Volatilité cible 60 % | +49,1 % / −27,3 % | +36,9 % / −50,6 % |
| Volatilité 60 %, jusqu'à 1,5x | +62,9 % / −33,9 % | +44,1 % / −56,3 % |
| Volatilité 80 %, jusqu'à 2x | +80,0 % / −44,5 % | +52,3 % / −68,3 % |

**Plus de cryptos :** pas mieux. **Levier sur la tendance :** plus de gain, mais la pire chute augmente autant ; c'est du risque en plus, pas un avantage.

**Robustesse du signal** (8 signaux testés) :

| Signal | Hyperliquid | Binance 2021-26 |
|---|---|---|
| SMA30 | +33,9 % | +23,4 % |
| **SMA50** | **+45,9 %** | **+34,2 %** |
| SMA100 | +30,5 % | +23,7 % |
| SMA200 | +29,0 % | +25,8 % |
| EMA 20/50 | +30,0 % | +22,7 % |
| EMA 20/100 | +25,3 % | +19,6 % |
| Cassure 20 j | +25,0 % | +21,4 % |
| Cassure 50 j | +32,9 % | +18,0 % |

La SMA50 est la meilleure des 8 : son résultat est probablement en partie dû à la chance. Option plus robuste, `--ensemble` (moyenne de 6 signaux : SMA 30/50/100/200 et cassures 20/50 j) :

| | Hyperliquid | Binance 2021-26 |
|---|---|---|
| Tendance ensemble seule | +33,6 % / −21,7 % | +25,2 % / −33,3 % |
| **70/30 avec arbitrage + emprunt** | **+36,8 % / −3,5 %** | **+23,6 % / −7,4 %** (2022 : −5 %) |
| 50/50 | +36,3 % / −8,1 % | +24,4 % / −15,5 % |
| Pour comparer, 70/30 avec SMA50 | +40,8 % / −4,6 % | +26,4 % / −10,6 % (2022 : −7 %) |

## Pilote : rejeu de 2026 jour par jour (13/10/2026)

`python -m pilote.bot replay --since 2026-01-01 --capital 1000` : 70 % arbitrage + emprunt quand ça paie, 30 % tendance (ensemble de signaux). Chaque décision utilise uniquement les données disponibles à sa date.

- **Résultat :** 1 000 $ → 1 102 $ (+10,2 %), pire chute −2,3 %.
- **Par mois :** janvier −0,6 %, février +0,3 %, mars −0,5 %, avril +0,9 %, mai +0,8 %, juin +0,8 %, juillet +1,2 %, août +5,2 %, septembre +2,3 %, octobre −0,5 %.
- **D'où vient le gain :** prix (part tendance) +37 $, financement +65 $, staking +9 $, emprunt 0 $ (jamais déclenché), frais −10 $.
- **Cohérence :** même ordre de grandeur que le backtest 70/30 ensemble pour 2026 (+11 %).

Simulation en direct démarrée le 13/10/2026 avec 1 000 $ fictifs.
