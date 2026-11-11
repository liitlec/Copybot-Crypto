# État du laboratoire (réécrit à chaque passage) — après le passage 1, 11/11/2026

## Où j'en suis
- Outils : `donnees.py` (téléchargement Yahoo), `banc_tendance.py` (A), `banc_scalp_h1.py` (B), `banc_prime.py` (C),
  `registre.py` (papier). Tout tourne en moins d'une minute.
- Réfuté : tendance long/court en CFD (devises surtout) ; scalp simple à l'heure (élan / retour).
- Meilleur montage honnête du moment : panier acheté seulement (indices, or, argent, BTC, ETH) à risque égal ;
  ≈ +8 à +13 %/an depuis 2016 selon le levier, mais c'est la prime de risque en période de hausse, pas un avantage.
- 173 essais comptés.

## À chaque passage, d'abord
`python3 donnees.py && python3 registre.py` puis recopier le tableau du registre dans AVIS.md.

## Pistes suivantes (par ordre)
1. **Portage et financement** : là où le coût devient un revenu. Financement des perpétuels Hyperliquid
   (`fundingHistory`) : achat comptant + vente du perpétuel ; mesurer le revenu net sur l'historique, par actif.
2. **Effets de calendrier / de séance documentés** sur indices et or (nuit contre journée, fin de mois), en 1 h,
   avec moitié réglage / moitié verdict ; l'or et les indices ont le coût relatif le plus bas (6 à 12 %).
3. **Retour à la moyenne à quelques jours sur indices** (achat après forte baisse, cours > moyenne 200 j) : connu,
   peu de trades, à tester sur 1985-2015 puis verdict 2016-2026.
4. Vraies conditions STARTRADER (écarts, swaps) : à demander à Baptiste seulement si un montage passe.
5. Bougies 5 min (histdata.com) seulement si une piste horaire survit.

## MT5 démo (section ajoutée à MISSION.md le 11/11, commit 36b30f3)
- Cible : compte démo via le pont (`labo/mt5/consigne.json` → pont ; `etat.json`, `executions.jsonl`, `donnees/` ← pont).
- Au 11/11 : pas de dossier `mt5/`, pont non installé. Ne rien envoyer tant qu'aucun montage n'est solide hors échantillon.
- Dès que `etat.json` existe : demander par `demandes_donnees.json` les bougies et spreads réels du courtier pour recaler les coûts.

## Pièges notés
- Yahoo : `range=max` → mensuel ; utiliser `period1/period2`. `query1` peut répondre « Too Many Requests », `query2` passe.
- Indices en 1 h : 7 barres par jour seulement, « 24 barres » ≈ 3,5 jours.
- Les Sharpe du banc C ne retranchent pas le taux sans risque.
