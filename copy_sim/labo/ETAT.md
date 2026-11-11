# État du laboratoire (réécrit à chaque passage) — après le passage 2, 11/11/2026

## Où j'en suis
- Outils : `donnees.py` (téléchargement Yahoo), `banc_tendance.py` (A), `banc_scalp_h1.py` (B), `banc_prime.py` (C),
  `registre.py` (papier). Tout tourne en moins d'une minute.
- Réfuté : tendance long/court en CFD (devises surtout) ; scalp simple à l'heure (élan / retour).
- Meilleur montage honnête du moment : panier acheté seulement (indices, or, argent, BTC, ETH) à risque égal ;
  ≈ +8 à +13 %/an depuis 2016 selon le levier, mais c'est la prime de risque en période de hausse, pas un avantage.
- Réfuté aussi (passage 2) : 30 règles simples de bougies sur XAUUSD en M1, M5, M15 avec le spread réel.
- Mesuré : l'or est le moins cher (spread 0,46 bp = 28 % du mouvement M1, 11 % en M5 ; EURUSD 323 %).
- 263 essais comptés. Banc D : `banc_or.py` (données dans `mt5/donnees/`, poussées par le pont).

## À chaque passage, d'abord
`python3 donnees.py && python3 registre.py` puis recopier le tableau du registre dans AVIS.md.

## Pistes suivantes (par ordre ; priorité de Baptiste = scalp XAUUSD, voir PRIORITES.md)
1. **Robot de mesure 0,01 lot sur XAUUSD** (`mt5/robot/` : `robot.py`, `essais_robot.py`, `VERSION`) : lire d'abord
   `copy_sim/forex/ROBOT_INTERFACE.md` et `MISSION_ROBOT.md`. But : spread, glissement et délai réels, y compris
   pendant les annonces. À présenter comme « mesure », pas « stratégie ». Stop obligatoire sur chaque position.
2. **Scalp or, familles pas encore essayées** (banc D = 90 essais, tous nuls) : effets d'heure (fixing de Londres
   16 h Paris, ouverture NY, heure pleine), fourchette d'Asie cassée à Londres, retour vers le prix moyen de séance,
   filtre de volatilité (ne trader que 14 h – 17 h Paris), sorties par stop/objectif plutôt qu'à durée fixe (il faut
   alors simuler dans la bougie : prudence, haut/bas en prix vendeur). Seuil à battre : 0,5 bp brut par trade.
3. Demander plus d'historique M1 par tranches (`debut`/`fin`) si le terminal en a ; 90 000 bougies par demande max.
4. Portage (financement des perpétuels Hyperliquid) ; effets de calendrier sur indices.
5. Nom d'un indice chez le courtier : demandé à Baptiste dans AVIS.md.

## MT5 démo (section ajoutée à MISSION.md le 11/11, commit 36b30f3)
- Cible : compte démo via le pont (`labo/mt5/consigne.json` → pont ; `etat.json`, `executions.jsonl`, `donnees/` ← pont).
- Le pont tourne depuis le 11/11 17 h 10 ; lanceur de robot présent (champ `robot` de `etat.json`), aucun robot installé.
- Demandes d'historique : 90 000 bougies passent, 200 000 non. Serveur = UTC+2. Bougies en prix vendeur.
- `consigne.json` : rien envoyé, aucun montage prouvé.

## Pièges notés
- Yahoo : `range=max` → mensuel ; utiliser `period1/period2`. `query1` peut répondre « Too Many Requests », `query2` passe.
- Indices en 1 h : 7 barres par jour seulement, « 24 barres » ≈ 3,5 jours.
- Les Sharpe du banc C ne retranchent pas le taux sans risque.
