# public-apis : ce qui peut nous servir (étapes 1 et 2 du 16/11, étape 3 finie le 17/11)

Source : README de github.com/public-apis/public-apis (≈ 3 000 lignes, lu en local, lecture seule). Lu : Calendar,
Currency Exchange, Cryptocurrency, Finance, Government (en partie). Aucun compte créé, rien installé, aucune clé
utilisée. Une clé ne va jamais dans le dépôt (la demander à Baptiste par AVIS.md).

## Tableau (essais du 17/11, un appel `curl` par API, sans clé, délai 15 s)

| API | Ce qu'elle donne | Clé ? | Répond aujourd'hui ? | Utilité pour le labo | Testé au banc ? |
|---|---|---|---|---|---|
| **Helious** `api.helious.io/api/calendar` | calendrier US : annonces économiques avec importance (Low/Medium/High), prévision, publié, surprise ; discours Fed, FOMC, adjudications, fériés | non | **répond** (428 lignes, 13/10/2025 → 26/11/2027) | **n° 1** : couper le robot autour des annonces High ; repérer les journées à risque d'aller-retour | non (banc X a testé l'or à 8 h 30 NY **sans** calendrier : rien) |
| **FXMacroData** `api.fxmacrodata.com/v1/calendar/usd` (cité par tradermonty) | calendrier USD officiel, heure exacte de publication (NY et UTC) | non pour l'USD | **répond** (501 annonces) | complément de Helious, mais **seulement l'avenir** (17/11/2026 → 2027) : utile au robot, pas au banc | non |
| **CFTC** (données ouvertes, `publicreporting.cftc.gov`, source citée par XOOMAR) | rapport COT hebdomadaire : positions longues/courtes des spéculateurs (« non commerciaux ») par marché | non | **répond** (or : 1 942 semaines depuis 1986 ; S&P 500 e-mini, Nasdaq 100 e-mini présents) | positionnement : tester le « COT à contre-courant » (voir SKILLS_TRADING.md) sur l'or jour | non |
| **Fed Treasury** (fiscaldata) `avg_interest_rates` | taux moyens de la dette US (bons du Trésor : 4,014 % fin octobre 2026) | non | **répond** | coût du portage des CFD (financement de nuit) ; taux sans risque | non |
| **Goldprice.dev** | or, argent, cuivre au comptant (3 861,76 $ ce matin), historique long annoncé | non | **répond** | contrôle du prix de l'or ; historique long à vérifier dans la doc | non |
| **Frankfurter** | taux de change BCE quotidiens, séries historiques | non | **répond** (série 2024 testée) | devises jour si on reprend la piste fin de mois FX ; on a déjà Yahoo | non |
| **Nager.Date** | jours fériés de 90 pays (US 2026 testé) | non | **répond** | jours fériés US/UK pour éviter les séances minces (remplace TradingCalendars) | non |
| **CoinGecko** | prix crypto (BTC 64 380 $ ce matin) | non | **répond** | contrôle BTC/ETH ; on a déjà les bougies du courtier | non |
| **Indice peur/avidité crypto** (alternative.me) | sentiment crypto quotidien 0-100 (aujourd'hui 12, « peur extrême ») | non | **répond** | filtre de régime crypto, peu utile tant qu'on ne trade pas la crypto | non |
| **Econdb** | macro mondiale | **oui** (401 sans clé) | ne répond pas sans clé | régimes de fond ; pas urgent | non |
| TradingCalendars | fériés et séances écourtées | oui (gratuite, 10 appels/j) | essai du 16/11 : clé obligatoire | inutile : Helious + Nager suffisent | non |
| FRED | séries de la Fed | oui (gratuite) | non essayé | taux ; Fed Treasury suffit pour l'instant | non |
| Futures Clock, XOOMAR | horaires de 65 contrats ; données SEC/FINRA/CFTC | non | non essayés (adresse d'API non trouvée dans le README) | la CFTC directe remplace XOOMAR | non |

Écartés : actions individuelles, paiements, fiscalité, marchés de prédiction, « signaux IA » payants, sentiment
« IA » des actualités (clé, aucune preuve mesurable).

## Ce qui répond sans clé et sert vraiment (dans l'ordre)
1. **Helious** : seul calendrier avec un historique (13 mois) → banc « pause ± 30 min autour des annonces High »
   sur l'or M5 et le Nasdaq M5. Prochaine étape : `calendrier.py` qui garde une copie dans `labo/donnees/`.
2. **CFTC COT** : 40 ans d'historique gratuit → banc « COT à contre-courant » sur l'or jour (règle dans
   SKILLS_TRADING.md).
3. **Fed Treasury** : taux pour chiffrer le portage ; **Nager.Date** : fériés.
FXMacroData sert au robot en direct (heures exactes à venir), pas au banc.
