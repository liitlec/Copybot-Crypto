# copysim — tester la stratégie « copier le top du classement » SANS argent

Reproduit la stratégie du post @0xNevsky (copyfomo + Grok) :
copier un trader du classement hebdo, suivre ses ventes, et passer au suivant après 2 pertes d'affilée.
Tout est **simulé** : lecture seule de la blockchain Solana, **aucune clé privée, aucune transaction signée,
aucun bot Telegram**.

## Ce que ça mesure

- **PnL réel d'un copieur** : retard, slippage, frais du bot (1 %), frais réseau/priority fee, composition
  (20 % du capital par trade comme le post).
- **Écart avec le leader** : son propre résultat sur les mêmes tokens, comparé au nôtre. Cet écart, c'est ce
  que coûte le fait d'arriver après lui.
- **Effet de la rotation** : même backtest avec et sans le changement de leader après 2 pertes.

## Installation (Windows, uv)

```powershell
cd copy_sim
uv venv
uv pip install -r requirements.txt
copy .env.example .env
uv run pytest -q      # 16 tests hors-ligne
```

**RPC Solana** : le RPC public est trop limité. Crée un endpoint gratuit (Helius, QuickNode, ou Chainstack
Solana : tu as déjà un compte Chainstack) et mets son URL dans `SOLANA_RPC_URL` du `.env`.
C'est une URL de lecture : elle ne donne accès à aucun wallet.

## Liste des leaders (automatique)

```powershell
uv run python -m copysim leaders --top 10      # écrit leaders.txt, dans l'ordre du classement
```

- **Avec `SOLANATRACKER_API_KEY`** (clé gratuite sur solanatracker.io, à mettre dans `.env`) : classement KOL
  des 7 derniers jours par gains réalisés, c'est-à-dire le même classement que Kolscan. Wallets publics et
  identifiés (nom, Twitter).
- **Sans clé** : repli sur GeckoTerminal. Le classement est reconstruit à partir des derniers trades des pools
  Solana en tendance. Il ne couvre que quelques heures, donc il est plus grossier.
- Ensuite, vérification on-chain : on garde les wallets actifs dans les dernières 24 h et on écarte les bots
  (≥ 1000 tx/jour). Chaque adresse est validée (base58, 32 octets).
- Si `leaders.txt` est absent, `backtest` et `live` le génèrent tout seuls.

Le classement de l'app FOMO elle-même n'est pas public (il est dans l'app). Pour l'utiliser, colle ses
adresses dans `leaders.txt`, une par ligne.

**Biais à connaître** : un classement de la semaine liste ceux qui ont *eu de la chance cette semaine*.
Le backtest sur ces mêmes jours est donc optimiste (on copie des gagnants connus d'avance). Le test honnête
est le mode **live** : on fige le classement aujourd'hui et on regarde la suite.

## 1. Backtest (résultat en 10-30 min)

```powershell
uv run python -m copysim backtest --leaders leaders.txt --days 3
```

Récupère les swaps des leaders (Pump.fun, PumpSwap, Raydium, Jupiter… tout swap contre SOL), puis les
bougies 1 minute GeckoTerminal de chaque token, et rejoue la copie. Trois scénarios :

| scénario | prix d'exécution du copieur |
|---|---|
| `neutral` | clôture de la minute où arrive la copie (+ 1 % de slippage) |
| `pessimistic` | plus haut de la minute à l'achat, plus bas à la vente, jamais mieux que le leader |
| `neutral, sans rotation` | comme neutral, mais on copie tous les leaders en même temps |

Sortie : `reports/backtest.md` et `reports/backtest.json`.

## 2. Paper trading live (le vrai test, 1-2 semaines)

```powershell
uv run python -m copysim live --leaders leaders.txt
uv run python -m copysim report        # à tout moment -> reports/live.md
```

Le simulateur interroge les wallets toutes les 3 s. Chaque swap détecté est « copié » avec une **vraie
cotation Jupiter** prise à ce moment-là (impact de prix pour notre taille inclus, montant minimum garanti
après slippage). Rien n'est signé ni envoyé. Le retard réel de détection est enregistré. L'état est sauvegardé
dans `data/live_state.json` : on peut arrêter et relancer.

## Réglages (`.env`)

| variable | défaut | rôle |
|---|---|---|
| `CS_BANKROLL_SOL` | 1.0 | capital simulé |
| `CS_SIZE_MODE` / `CS_SIZE` | fraction / 0.2 | 20 % du capital courant par trade (ou X SOL fixe) |
| `CS_MAX_OPEN` | 5 | positions simultanées max |
| `CS_ROTATE_AFTER_LOSSES` | 2 | change de leader après N pertes d'affilée (0 = tous) |
| `CS_MAX_LEADER_BUY_SOL` | 0 | ignore les achats du leader au-dessus de X SOL |
| `CS_LATENCY_S` | 2 | retard de copie en backtest (le post annonce 0.5 s) |
| `CS_SLIPPAGE_BPS` | 100 | slippage par exécution |
| `CS_BOT_FEE_PCT` | 1.0 | commission typique d'un bot de copy trading |
| `CS_TX_FEE_SOL` | 0.0005 | frais réseau + priority fee/Jito |

## Lire le résultat

- Si **même `neutral` perd**, la stratégie perd.
- **Win rate élevé + profit factor < 1** = beaucoup de petits gains, quelques pertes qui effacent tout.
  C'est le profil classique sur les memecoins.
- **Slippage d'entrée médian** = combien plus cher que le leader on achète.
- **Positions « sans prix (compté 0) »** = tokens morts ou sans liquidité : c'est une perte réelle.
- Critère pour prendre la stratégie au sérieux : PnL positif en **live** sur au moins 2 semaines et 100 trades,
  avec un profit factor > 1.3, dans le scénario Jupiter (pas seulement en backtest).

## Limites

- Backtest : l'impact de **notre** taille sur le pool est ignoré, et les bougies sont à la minute alors que
  les memecoins bougent à la seconde. D'où les deux scénarios qui encadrent la réalité ; le live corrige ces
  deux points.
- Seuls les swaps contre SOL sont suivis (pas les routes via USDC ni les swaps token-token).
- Les APIs (RPC, GeckoTerminal, Jupiter) suivent leur documentation publique mais n'ont pas été appelées en
  réel depuis l'environnement de développement : premier lancement = vérifier sur 1 leader et 1 jour.
- Si l'URL de cotation Jupiter change, mets la nouvelle dans `JUP_QUOTE_URL`.

## Sécurité

Ce simulateur ne demande jamais de clé privée. **Aucun** bot Telegram de trading ne devrait recevoir celle
de ton wallet principal : si un jour tu testes en réel, utilise un wallet séparé avec une petite somme, et
révoque les autorisations ensuite.
