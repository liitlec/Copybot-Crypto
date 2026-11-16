# public-apis : ce qui peut nous servir (étape 1/2, 16/11 nuit — lecture du README seulement, rien testé)

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

**Étape 2 (prochain passage)** : un seul appel chacun à Helious, TradingCalendars et Goldprice.dev, noter ce qui
répond réellement (le réseau peut bloquer), puis résumé 3 lignes dans AVIS.md.
