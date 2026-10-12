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
