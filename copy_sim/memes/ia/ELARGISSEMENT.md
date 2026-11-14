# « L'élargissement de l'IA » (décidé par Baptiste le 08/11, lancement le mercredi 11/11 après 16 h)

But : voir le marché en temps réel au lieu de 400 pools GeckoTerminal toutes les 5-7 min, et tester avec des chiffres
deux idées : copier les portefeuilles « smart money », et élargir l'univers (jetons plus jeunes ou plus petits).

## Étapes (dans l'ordre, chacune testée sur les vraies données avant installation)

1. **Remettre `ia/BUDGET.md` sur `normal`** (fin du dépassement le 11/11 à 16 h).
2. **Détecteur gRPC des nouveaux pools** (flux.py, abonnement aux programmes pump.fun / PumpSwap / Raydium) :
   écrit `data/nouveaux_pools.jsonl` (pool, jeton, heure, liquidité, premiers achats). Mesure sur 24 h : combien de
   pools existent, combien GeckoTerminal nous montre, et le devenir des ratés (prix à +1 h, +6 h, vidés ou non).
3. **Caisse papier « baleines »** : liste de portefeuilles (classements publics GMGN ou nos propres mesures sur
   univers.jsonl), suivie par gRPC ; achat quand 2 portefeuilles de la liste entrent sur le même jeton en peu de
   temps, vente quand ils sortent ; prix d'achat = prix observé après leur achat (pas le leur), frais et glissement
   réalistes. Jugée comme les autres : au moins 100 trades, marge d'erreur, sans les 3 meilleurs, contre un témoin.
   Lire d'abord le code des dépôts cités dans le post (SolScope, GMGNAI/gmgn-skills, gmgnAgent) : sources de données,
   clé API, liens de parrainage.
4. **Univers plus large pour le tournoi** : champs « âge », « liquidité » accessibles aux challengeuses sur les
   nouveaux pools du détecteur, avec un filtre de base plus bas mais un plafond de mise lié à la liquidité.

## Garde-fous
- Rien en réel tant qu'une caisse n'a pas fait ses preuves en papier (règle de promotion habituelle).
- Pas de clé, de jeton ni de portefeuille dans le dépôt (public).
- reel.py, serveur.py, maj_auto.py, installer.sh : installation seulement depuis le PC de Baptiste.
