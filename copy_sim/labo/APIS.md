# public-apis : ce qui peut nous servir (étapes 1 et 2 faites, 16/11)

Source : README de github.com/public-apis/public-apis (≈ 3 000 lignes). Lu : Calendar, Currency Exchange, Finance,
Government (en partie). Aucun compte créé, rien installé. Une clé ne va jamais dans le dépôt.

| Priorité | API | Ce qu'elle donne | Clé | Usage pour nous |
|---|---|---|---|---|
| 1 calendrier | Helious | résultats d'adjudications du Trésor US + annonces économiques « scorées » | non | heures et importance des annonces US → tester « couper le robot autour des annonces » |
| 1 calendrier | TradingCalendars | jours fériés et fermetures FX / banques / bourses, séances écourtées | non | savoir d'avance les jours de marché mince (piège de l'aller-retour) |
| 1 calendrier | Futures Clock | horaires de séance de 65 contrats à terme | non | contrôle des heures d'ouverture US (ORB 15 h 30 Paris) |
| 2 historiques | Goldprice.dev | or, argent, cuivre au comptant et à terme, 30 ans d'histoire | non | allonger l'historique de l'or au-delà de Yahoo |
| 2 historiques | Econdb | macro mondiale | non | régimes de fond (inflation, taux) |
| 3 taux / COT | Fed Treasury (fiscaldata) | taux et données du Trésor US | non | portage, taux sans risque |
| 3 taux / COT | XOOMAR | données SEC, FINRA, **CFTC** (positionnement) | à vérifier | COT si l'accès est libre |
| 3 taux | FRED | séries de la Fed de St. Louis | oui (gratuite) | taux, à demander à Baptiste si besoin |

Écartés : bourses actions individuelles, paiements, fiscalité, marchés de prédiction (hors sujet pour nos CFD MT5),
les « signaux IA » payants (aucune preuve mesurable).

## Étape 2 : essais réels (16/11, 6 h 10 Paris, un appel chacune, sans clé)
- **Helious — oui, c'est notre calendrier.** `GET https://api.helious.io/api/calendar` (sans clé ; attention, pas
  `helious.io/api/...`). 413 lignes d'oct. 2025 à nov. 2027 : annonces économiques (283), discours Fed (30),
  adjudications (19), fériés (68), FOMC. Chaque ligne : `datetime_utc`, `impact` (Low/Medium/High), `forecast`,
  `actual`, `previous`, `surprise`, `sigma`. Version gratuite : le chiffre publié n'apparaît qu'1 h après (sans gêne
  pour couper le robot avant/après). Historique ≈ 13 mois seulement → suffit pour un premier test « pause autour des
  annonces High » sur l'or M5.
- **Goldprice.dev — répond** (`GET https://api.goldprice.dev/v1/prices?symbol=XAU-USD-SPOT`, sans clé : 3 869,82 $).
  Historique long à vérifier dans la doc ; utile en complément, pas urgent (on a déjà le courtier et Yahoo).
- **TradingCalendars — clé obligatoire** (gratuite, 10 appels/jour). Pas indispensable : Helious donne déjà les fériés.

Prochaine étape utile (hors relais, quand l'usage le permet) : `calendrier.py` qui garde une copie de
`api/calendar` dans `labo/donnees/`, puis banc « pause ± 30 min autour des annonces High » sur les règles du robot.
