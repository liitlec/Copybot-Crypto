# Priorités de Baptiste (à lire à chaque passage, après MISSION.md)

## 11/11/2026, 17 h 20 (Paris) : priorité au scalp sur XAUUSD
Baptiste veut que tu mettes en premier le **scalp sur l'or (XAUUSD)**, parce que les frais y pèsent moins, selon lui,
que sur les autres marchés. C'est sa priorité ; la méthode reste à toi, et la vérité aussi.

- Commence par **mesurer cette affirmation** chez son courtier : spread réel de XAUUSD (moyenne, par heure de la
  journée, pendant les annonces), commission et glissement, rapportés au mouvement moyen d'une bougie M1, M5, M15.
  Compare à EURUSD et à un indice. Dis-lui en clair si l'or est vraiment le moins cher à scalper, et à quelles heures.
- Le pont MT5 tourne depuis le 11/11 à 17 h 10 (`mt5/etat.json`). Demande-lui les vraies bougies du courtier par
  `mt5/demandes_donnees.json` : `{"demandes": [{"id": "xauusd_m1", "symbole": "XAUUSD", "periode": "M1", "nombre":
  200000}]}` (périodes M1 M5 M15 M30 H1 H4 D1, 200 000 bougies au plus par demande, 2 demandes servies par minute,
  réponse dans `mt5/donnees/<id>.csv.gz` avec le spread en points). Le nom exact du symbole chez le courtier peut
  différer (suffixe) : regarde `mt5/donnees/index.json` et `etat.json` après ta première demande.
- Cherche ensuite un scalp qui tient sur ces données : après spread réel, hors échantillon, essais comptés, comparé
  à des entrées au hasard de même fréquence. Séances (Londres, New York, fixing), retours après excès, cassures de
  fourchette, tout est permis.
- Limite technique à garder en tête : le pont relit ta consigne une fois par minute et tu ne passes que 4 fois par
  jour. Un scalp à la seconde n'est donc pas exécutable par toi. Si un montage demande de réagir bougie par bougie,
  la bonne forme est un **robot MT5** (ou un script côté PC) que tu spécifies, avec stops et objectifs posés chez le
  courtier : écris-en la spécification complète dans `labo/mt5/` et dis-le dans AVIS.md, Baptiste la fera installer.
- Les paniers de ton premier passage peuvent rester au registre papier comme références ; ils ne sont plus la
  priorité.
