# weather_arb — scanner météo Polymarket (PAPER TRADING UNIQUEMENT)

Détecte les écarts entre les prévisions ECMWF (Open-Meteo) et les prix des marchés de température
Polymarket, les enregistre en paper trades, les résout (WIN/LOSS) et mesure si le modèle bat le marché.
**Aucun ordre réel n'est envoyé** : pas de clé privée, pas d'appel CLOB authentifié, pas de contournement
de géoblocage. Les clés wallet / Chainstack / OpenRouter ne sont pas utilisées par ce module.

## 1. Audit des hypothèses fragiles

> `weather_scanner.py` n'est pas dans ce dépôt : l'audit ci-dessous porte sur la logique décrite
> (normale centrée sur la prévision, sigma 0.7 / 1.5 °C, edge ≥ 8 % sur `outcomePrices`). Pousse le fichier
> pour une relecture ligne à ligne. La colonne « à chercher » dit quoi vérifier dans ton code.

| # | Problème | Gravité | À chercher dans `weather_scanner.py` | Corrigé ici par |
|---|---|---|---|---|
| 1 | **Mauvais point de grille** : prévision au centre-ville alors que le marché se résout sur un aéroport. Incheon (RKSI) et Haneda (RJTT) sont côtiers : en mai, la brise de mer y tient souvent le Tmax 2-5 °C sous Séoul/Tokyo intra-muros. Très probablement l'explication de Séoul 26 °C+ (48 % vs 99 %) et de Tokyo 30 °C+. | Critique | Géocodage par nom de ville, `latitude`/`longitude` d'une table de villes | ICAO extrait de l'URL Wunderground de la description -> coordonnées exactes de la station (`stations.py`) ; commande `explain` qui affiche l'écart station / centre-ville |
| 2 | **Sigma trop faible** : 0.7 °C à J0 et 1.5 °C à J+1, c'est l'erreur d'une prévision corrigée de son biais à une station bien modélisée. ECMWF brut à un aéroport, c'est plutôt 1.3-2 °C à J0-J+1 et 3 °C+ à J+6. Prévision 28 °C, tranche « 26 °C or higher » : 99.98 % avec sigma 0.7, 89 % avec sigma 2.0. | Critique | Constantes 0.7 / 1.5 | Table biais + sigma calibrée par station et horizon (`calibrate`), a priori prudents sinon, plafond 2-98 % |
| 3 | **Bornes des tranches** : la source arrondit au degré entier. « 25 °C » = continu [24.5, 25.5[ ; « 26 °C or higher » = ≥ 25.5 ; « 84-85 °F » = [83.5, 85.5[. `P(T>26)` ou `P(25≤T<26)` décale tout d'un demi-degré. | Élevée | `cdf(hi) - cdf(lo)` sans ±0.5 | `Bucket.cont_lo/cont_hi` |
| 4 | **°F / °C** : Open-Meteo renvoie des °C par défaut. Comparer 24 °C à « 74-75 °F » met toute la masse dans la tranche basse -> des edges énormes sur les villes US. | Critique si présent | `temperature_unit` absent, pas de conversion | Unité lue dans le marché, conversion explicite, test dédié |
| 5 | **Fuseau horaire** : sans `timezone=<tz station>`, Open-Meteo agrège sur la journée GMT. Le marché porte sur le jour local de la station. | Moyenne | `timezone` absent ou `GMT` | Max recalculé depuis l'horaire, en heure locale de la station (identique scan/calibration) |
| 6 | **Max journalier vs max METAR** : Wunderground prend le max des METAR horaires/spéciaux, en °C entiers hors US. C'est plus bas que le vrai max continu (~0.3-0.5 °C). | Faible-moyenne | — | Calibration contre les METAR (IEM) : le biais est absorbé |
| 7 | **Prix utilisé** : `outcomePrices` ≈ mid/dernier prix. Acheter YES coûte le *best ask*, acheter NO coûte `1 - best bid`. Sur des carnets à 5-10 cents de spread, l'edge affiché fond. | Élevée | `outcomePrices` comme prix d'entrée | Entrée au best ask + slippage + frais ; filtres spread et liquidité |
| 8 | **Côté NO ignoré** : un modèle à 10 % sur une tranche cotée 40 % = edge NO. | Moyenne | Seulement `model - price` | Les deux côtés évalués |
| 9 | **Comptage gonflé** : 487 « opportunités » = mêmes marchés re-loggés à chaque scan + plusieurs tranches mutuellement exclusives du même événement (paris corrélés). | Élevée pour l'évaluation | Append à chaque scan | 1 entrée par marché, max N par événement (défaut 1) |
| 10 | **J0 sans observations** : l'après-midi local, le max est déjà partiellement observé ; le marché le sait, le modèle non. | Moyenne (J0) | — | À J0 les tranches sous le max déjà observé (METAR) passent à 0 |
| 11 | **Partition** : la somme des probas des tranches d'un événement doit faire 1. Un trou/chevauchement trahit un parsing faux. | Contrôle | — | `check_partition` ; marché non tradé si partition incomplète |
| 12 | **Source de résolution non-WU** (ex. Hong Kong Observatory, NOAA) : la station n'est pas un METAR. | Variable | — | Avertissement ; marché ignoré sans ICAO (`WX_REQUIRE_STATION=1`) |

Conclusion attendue : des écarts de 50 points sur des centaines de marchés viennent quasi sûrement de 1 + 2
(+ 4 sur les villes US si non converti), pas d'une inefficience. Le pipeline ci-dessous permet de le
**mesurer** au lieu de le supposer.

## 2. Installation (Windows, uv)

```powershell
cd C:\Users\troc\polymarket-weather-bot
# copier le dossier polymarket_weather\ ici, puis :
cd polymarket_weather
uv venv
uv pip install -r requirements.txt
copy .env.example .env      # ajuster frais/slippage si besoin
uv run pytest -q            # 29 tests hors-ligne
```

`tzdata` est requis sous Windows pour les fuseaux IANA (`zoneinfo`).

## 3. Utilisation — dans cet ordre

```powershell
# 1) Calibrer biais + sigma par station et horizon (180 jours, ~2-5 min, mis en cache)
uv run python -m weather_arb calibrate --from-markets --days 180
uv run python -m weather_arb calibrate --from-markets --days 180 --kind low   # si marchés "lowest"

# 2) Diagnostiquer un marché suspect (station vs centre-ville, sigma ancien vs calibré)
uv run python -m weather_arb explain highest-temperature-in-seoul-on-may-17

# 3) Scanner (une fois, ou en boucle toutes les 30 min avec résolution auto)
uv run python -m weather_arb scan
uv run python -m weather_arb loop --with-resolve
uv run python -m weather_arb --prob-model ensemble scan     # option : ensemble ECMWF 51 membres

# 4) Résoudre les trades échus puis générer le rapport
uv run python -m weather_arb resolve
uv run python -m weather_arb report        # -> reports/report.md + reports/report.json
```

Fichiers produits (`data/`, ignoré par git) :

| Fichier | Contenu |
|---|---|
| `paper_trades.json` | trades simulés : côté, prix d'entrée (ask + slippage), proba, edge après coûts, station, horizon, puis résultat, PnL, valeur observée |
| `predictions.jsonl` | **tous** les marchés évalués, 1 ligne par (marché, horizon) : sert à la calibration sans biais de sélection |
| `sigma_table_high.json` | biais / sd / RMSE par station et horizon |
| `stations.json` | surcharges manuelles de stations (+ stations géocodées à vérifier) |
| `cache/` | cache HTTP de la calibration |

## 4. Fonctionnement

**Station** (`markets.py`, `stations.py`) : l'ICAO est extrait de l'URL Wunderground de la description
(`.../history/daily/kr/incheon/RKSI` -> `RKSI`), puis converti en coordonnées exactes + fuseau via une table
de ~80 aéroports. Station inconnue : `data/stations.json` (prioritaire), sinon géocodage Open-Meteo du nom
de station (marqué `geocoded`, à vérifier). Exemple de surcharge :

```json
{"RKSI": {"name": "Seoul Incheon", "lat": 37.4602, "lon": 126.4407, "tz": "Asia/Seoul"}}
```

**Probabilité** (`probability.py`) :
- *normale* : `T ~ N(prévision + biais_station_horizon, sigma_station_horizon)`, intégrée sur [lo−0.5, hi+0.5[.
  Biais et sigma de la station sont tirés vers la moyenne globale tant qu'elle a peu d'historique
  (k = 20 jours). Plancher sigma 0.6 °C, probas plafonnées à [2 %, 98 %].
- *ensemble* (`--prob-model ensemble`) : les 51 membres ECMWF ENS sont recentrés sur la prévision
  déterministe débiaisée (l'ENS Open-Meteo est au pas de 3 h, son max brut est biaisé bas), puis chaque
  membre est « habillé » d'une gaussienne pour que la variance totale ne descende jamais sous l'erreur
  historique calibrée. Un comptage brut de membres donnerait 0 % / 100 % sur des tranches de 1 °C.

**Edge** : `edge_YES = p − (ask + slippage)·(1 + frais)`, `edge_NO = (1−p) − (1 − bid + slippage)·(1 + frais)`.
Trade si edge ≥ 8 %, spread ≤ 10 cents, liquidité ≥ 200 $, partition complète. 1 trade max par marché et par
événement.

**Résolution** (`resolution.py`) : 1) résultat officiel Polymarket (Gamma, `outcomePrices` 1/0 une fois le
marché clos) ; 2) max/min METAR de la station via Iowa Environmental Mesonet. Tant que l'officiel n'est pas
là, le trade est `PROVISIONAL` (résolu sur METAR) et repasse en `RESOLVED` dès que Gamma tranche.
**Tout désaccord officiel vs METAR est listé dans le rapport** : c'est le détecteur de bugs de
station/unité/bornes.

**Calibration** (`calibration.py`) : Open-Meteo *Previous Runs API* (`temperature_2m_previous_dayN`, N = 1..7)
donne la prévision émise N jours avant, ce qui permet une calibration **par horizon**. L'*Historical Forecast
API* ne recoud que les premières heures de chaque run (≈ J0) : elle reste disponible
(`fetch_historical_forecast`) en repli. La vérité est le METAR de la station, **pas l'archive ERA5** : ERA5 est
une maille de réanalyse et masquerait le biais station/maille qu'on cherche à mesurer. La table rapporte aussi
la part des erreurs hors ±2 sd (4.6 % si gaussien ; nettement plus = queues épaisses, préférer l'ensemble).

**Rapport** (`report.py`) : win rate (IC de Wilson), win rate *attendu* par le modèle vs *implicite* dans le
prix payé, PnL et ROI nets de spread/slippage/frais, score de Brier modèle vs marché, courbes de fiabilité
(sur les trades et sur tous les marchés scannés), découpage par ville, horizon, côté et tranche de proba,
erreur de prévision réelle vs sigma utilisé.

## 5. Critères avant d'envisager de l'argent réel

À juger sur le journal de prédictions **et** les trades, après au moins 4 semaines :

1. ≥ 200 trades résolus **officiellement**, 0 désaccord officiel/METAR non expliqué.
2. Brier modèle < Brier marché sur `predictions.jsonl` (sinon le marché sait mieux).
3. Borne basse de l'IC 95 % du win rate > prix moyen payé, et PnL net > 0 en ville **et** en horizon
   (pas porté par 1-2 villes).
4. Courbe de fiabilité proche de la diagonale : quand le modèle dit 80 %, ça gagne ~80 %.

Pistes légales ensuite : IBKR Ireland (ForecastEx / contrats de prévision), offres conformes MiCA.

## 6. Limites / non vérifié

- Écrit et testé **hors-ligne** (APIs simulées) : les formats Gamma / Open-Meteo / IEM suivent leur
  documentation publique mais n'ont pas été appelés en réel depuis l'environnement de développement.
  Premier lancement : `explain` sur 2-3 événements pour valider la chaîne.
- Les frais Polymarket sur ces marchés sont un paramètre (`WX_FEE_RATE`, 1 % par défaut, prudent) : à
  ajuster selon le barème en vigueur.
- Le max METAR (IEM) peut différer de ±1 degré de Wunderground sur des cas limites : d'où la priorité à la
  résolution officielle.
- La correspondance horizon de scan / `previous_dayN` est approximative (± quelques heures selon le run).
