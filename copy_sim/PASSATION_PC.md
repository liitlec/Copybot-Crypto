# Passation cloud → PC (16/10/2026, 17:30 heure de Paris)

Document de passation entre la session cloud « Polymarket météo : calibrage sigma et résolution »
(session_01SsuaMVtAjm1uhUSFC3B9Xi) et la session qui tourne sur le PC Windows de l'utilisateur
(`C:\Users\bapti\copysim`). Il contient tout ce qui a été fait, mesuré, supposé et décidé.
**Aucune clé ni aucun secret ici** (le repo est lisible publiquement).

---

## 0. À lire en premier (pour la session PC)

- **Langue : français. Heures : toujours en heure de Paris (UTC+2).** L'utilisateur lit sur téléphone : réponses claires, tableaux, pas de jargon inutile.
- **Tout est en simulation (paper trading) jusqu'ici.** Aucun ordre réel n'a été passé. L'utilisateur a précisé que passer des ordres réels et manipuler des clés n'a jamais été interdit : c'est **sa** décision. Il a validé le principe d'un **petit test réel de F** à son retour (section 11), mais rien n'est encore codé pour le réel.
- **Ne jamais mettre de clé dans le repo** (il est public). Les clés restent dans `.env` (ignoré par git) ou sur le PC.
- **Ne rien relancer en double avec le cloud sans y penser** : le cloud utilise la même connexion gRPC Chainstack et la même clé Helius que le PC (section 3).
- Le PC a **planté le 16/10 à 06:15** (écran noir, ne se réveillait plus). Avant de relancer les tests du PC : vérifier l'espace disque, les fenêtres/tâches lancées au démarrage, et l'état des enregistrements.

---

## 1. Historique en bref

| Date | Quoi |
|---|---|
| 11-12/10 | Scanner Polymarket météo (calibrage sigma) ; sans ordre réel. |
| 12-13/10 | Simulateur de copy trading Solana (`copysim`) : copie des achats/ventes de wallets « leaders », cotations Jupiter réelles. Leader principal 515vh1. Candidats KOL, scalpeurs, Mr. Frog. Sniper Pump.fun testé puis rejeté. Scout de wallets, filtre anti-rug, règles R1-R3 (prereg/copy_rules.json). |
| 13/10 | Installation sur le PC (`install_live.ps1`) d'un test de 2 semaines (témoin, anti-rug, Raven, sniper) au démarrage de Windows. |
| 13-15/10 | Sur le PC, une session Remote Control « Bonjour » (session_01GBEd948JhNZLX5i8WNgfge) a ajouté : hub gRPC Chainstack, scalp Pump.fun A/B, momentum, copie v3, score de qualité. |
| 15/10 20:17 | Règles scalp A/B figées sur le PC (prereg/scalp_rule.json du PC). Dernier point connu du PC (22:28) : **B 1 881 trades, +3,05 SOL (+1,6 % ± 1,1 %)** ; momentum G 4h+course +1,1 % ; v3bp −0,9 % ; top (Mr. Frog) −26,5 % ; v2 gRPC −44,8 % ; v2 ws −72,6 %. |
| 16/10 06:15 | **Plantage du PC.** Les tests et la session « Bonjour » sont coupés. |
| 16/10 08:14 | Le cloud reprend tout : copie exacte du code scalp du PC, hub gRPC Chainstack, collecteur, score. Puis ajout des règles C, D, E, F, G, H (figées une par une, évaluées seulement sur les lancements postérieurs). |
| 16/10 ~17:00 | L'utilisateur est rentré, sur le PC. Bascule vers une session locale. |

---

## 2. Ce qui tourne dans le cloud (au moment de la passation)

Dossier : `/home/user/Copybot-Crypto/copy_sim` (branche `claude/polymarket-weather-sigma-resolution-olv0bs` du repo `liitlec/Copybot-Crypto`).
Lancé par `data/relaunch.sh` (idempotent, ignoré par git) ; un gardien relance ce qui manque chaque minute.

| Processus | Rôle | Sortie |
|---|---|---|
| `copysim live --leaders leaders_live.txt --report live_temoin` | copie de 515vh1 (témoin) | `data/` |
| idem `--rug-filter`, `CS_DATA_DIR=data_filtre` | témoin + anti-rug | `data_filtre/` |
| idem Raven (`CS_BOT_FEE_PCT=0 CS_TX_FEE_SOL=0.0027`) | frais du bot Raven | `data_raven/` |
| `--leaders leaders_cands.txt` (`CS_SIZE=0.05 CS_MAX_OPEN=15`) | 13 KOL candidats | `data_cands/` |
| `--leaders top.txt` (Mr. Frog, `CS_SIZE=0.1`) | top wallet | `data_top/` |
| `copysim grpc-hub --pumpfun data_grpc/pumpfun.jsonl` | flux Yellowstone gRPC Chainstack du programme Pump.fun | `data_grpc/pumpfun.jsonl` (≈ 900 000 tx enregistrées, 0 perdue) |
| `copysim scalp-grpc --file data_grpc/pumpfun.jsonl --start-file data_grpc/START` | rejoue A à H toutes les 5 min | `reports/live_scalp_grpc.md` |
| `python -u nuit/pump_enrich.py` | collecteur (créateur, wallet, métadonnées) pour le score | `data_grpc/pump_enrich.jsonl` (≈ 13 000 lancements, 0 erreur) |

Tâches planifiées du compte (à arrêter quand le cloud s'arrête) :
- « Garde active cloud (15 min) » : chaîne de `send_later` toutes les 15 min (relance, contrôle, mise à jour des pages).
- « Garde tests copysim cloud (PC hors ligne) » (trig_0189G6U3ui4cX4gDSp6r5Dsm) : contrôle horaire, copies `live_snapshot*`, vérification du retour du PC.

Pages de suivi (privées, compte de l'utilisateur) :
- **Suivi scalp Pump.fun** (simple, épinglée, marche sur l'iPhone) : https://claude.ai/artifact/Rw6rQvZFzeoSqxs8tR5N87
- Scalp Pump.fun en direct (interactive, ne s'ouvre pas sur l'iOS de l'utilisateur) : https://claude.ai/artifact/HC6T7tTzhjxneLgDvnRzwf
- Générées par `nuit/dash_export.py` (→ `data_grpc/dash_trades.json`) et `nuit/dash_static.py` (→ `reports/suivi_scalp.html`).

**Le cloud est éphémère** : si la session cloud s'arrête, tout ce qui précède s'arrête aussi. Les données `data_grpc/` ne sont pas dans git (trop gros, ignorées).

---

## 3. Clés, comptes et sécurité (sans les valeurs)

- `copy_sim/.env` (cloud, ignoré par git) contient : `SOLANA_RPC_URL` (Helius), `SOLANATRACKER_API_KEY`, `GRPC_ENDPOINT` (yellowstone-solana-mainnet.core.chainstack.com:443), `GRPC_TOKEN` (x-token Chainstack), `CS_POLL_S=1`, `CS_SIZE=0.1`. Le PC a ses propres valeurs dans son `.env`.
- **Partagé entre cloud et PC** : le token Chainstack (gRPC + RPC `https://solana-mainnet.core.chainstack.com/<token>` utilisé par le collecteur) et la clé Helius. Si on relance les mêmes tests sur le PC, **arrêter d'abord les équivalents du cloud** (limites de connexions / de requêtes).
- Conseillé après les tests : **régénérer le x-token Chainstack, la clé Helius et la clé Solana Tracker** (elles ont circulé dans des conversations).
- **Repo Raven** (`liitlec/raven`) : son `.env` contient des **clés privées exposées** → considérer ce wallet comme compromis ; ne pas l'utiliser pour le test réel ; changer les tokens.
- Pour le réel : **wallet neuf dédié au bot**, clé seulement sur le PC, jamais dans git ni dans le cloud.

---

## 4. Données enregistrées

`data_grpc/pumpfun.jsonl` (format du recorder du PC, `copysim/pumprec.py` recopié tel quel) : une ligne JSON par transaction Pump.fun :
`slot, idx, bt` (heure du bloc = première vue du slot), `seen` (réception), `sig, kind` (create/buy/sell), `signer, mint, curve_acc, quote, sol, curve, vault_tok, curve_tok, tok, px, signer_sol, fee, prio, jito, cu` (+ `accs` sur les créations). Fenêtre de suivi par lancement : 600 s.

Mesures sur ces données :
- Latence gRPC (réception − bloc) : **médiane 0,14 s, 90 % sous 0,21 s**.
- Frais payés par les acheteurs entre +3 et +10 s : **médiane 0,000037 SOL**, 75 % ≤ 0,000105, 90 % ≤ 0,00026 ; tips Jito sur 7 % des achats seulement (≈ 0,00001 SOL).
- **7 états de courbe aberrants sur 868 000** (vente mal lue : réserve qui paraît vide ou trop pleine le temps d'une ligne). Filtrés depuis 17:10 par `drop_spikes()` dans `copysim/scalpgrpc.py` (voir section 9).

`data_grpc/pump_enrich.jsonl` : par lancement, infos du créateur et du token (achat du créateur, âge du wallet, outil de lancement, X/Telegram/site…). Sert au score.

---

## 5. Modèle de simulation (hypothèses)

Courbe Pump.fun (identique au PC, `copysim/scalpgrpc.py`) :
- `v_tok = vault_tok + 73 000 000` ; `K = 30 × 1,073e9` ; SOL virtuels = K / v_tok.
- Achat : `tokens_for(v_tok, sol) = v_tok − K / (K/v_tok + sol × (1 − FEE))`.
- Vente : `sol_for(v_tok, tok) = (K/v_tok − K/(v_tok + tok)) × (1 − FEE)`.
- `FEE = 0,0125` par côté (1,25 %), `SIZE = 0,1 SOL`, `BASE_COST = 0,000105 SOL` par transaction, `CREATE_RENT = 0,03`.
- Rendement d'un trade = (SOL récupérés − BASE_COST) / (SIZE + BASE_COST) − 1, frais compris.
- L'impact de **notre propre achat** sur le prix est compté. Celui des autres est celui réellement observé.

**Ce que la simulation ne compte pas** (= « coûts réels », section 8) : le retard entre décision et inclusion dans un bloc, les transactions ratées, les sandwichs, la fermeture du compte du token (≈ 0,002 SOL de loyer récupérable), d'éventuels frais de priorité plus élevés.

Vente « moitié à ×2 » (E/F) : approximation linéaire `(rendement de la 1re moitié + rendement de la 2e moitié) / 2`.

---

## 6. Les règles (toutes en paper trading, mise 0,1 SOL)

Chaque règle est **figée avant d'être évaluée** (fichier `prereg/…` avec `debut_ts`) et n'est jugée que sur les lancements créés après.

| Règle | Fixée le (Paris) | Entrée | Sortie | Verdict prévu |
|---|---|---|---|---|
| **A** | 15/10 20:17 (PC) | +1 s après la création, courbe < 0,5 SOL | revente à 60 s | 1 000 trades ; moyenne > 2 × marge ; positive sans les 3 meilleurs |
| **B** (règle du PC) | 15/10 20:17 (PC) | +5 s, au moins 1 acheteur autre que le créateur, courbe < 2,5 SOL, aucun achat dans le slot de création | revente à 60 s | idem A |
| **C** | 16/10 08:32 | entrée de B | à 60 s : < +20 % → revente ; sinon stop suiveur −30 % sous le plus haut, max 9 min | 1 000 trades ; idem + bat B sur les mêmes lancements |
| **D** | 16/10 09:45 | score de qualité (`nuit/scalp_score.py`) à +5 s, réappris toutes les 30 min sur les lancements finis, achat si score ≥ 80e centile de l'apprentissage ; pas d'achat dans le slot de création ; lancements enrichis seulement ; pas de plafond de courbe | sortie de C | 300 trades ; idem + bat « tous les lancements, sortie C » |
| **E** | 16/10 10:01 | entrée de B | **dès ×2 : moitié vendue ; reste vendu à −40 % sous son plus haut** ; sans ×2 à 60 s : sortie de C (< +20 % → revente, sinon stop −30 % en attendant ×2) ; max 9 min | 1 000 trades ; idem + bat B sur les mêmes lancements |
| **F** | 16/10 10:01 | sélection de D | sortie de E | 300 trades ; idem + bat D sur les mêmes lancements |
| **G** | 16/10 13:41 | F, seulement si les trades B déjà revendus des 30 dernières minutes (au moins 10) sont positifs en moyenne | sortie de E | 200 trades ; idem + moyenne et total ≥ F même période |
| **H** | 16/10 13:41 | E avec le même filtre « vague » | sortie de E | 600 trades ; idem vs E même période |

Score de qualité (code du PC) : scorecard de log-odds par tranches (5 tranches), cible « run » = prix × 2 dans les 10 min, variables connues à +5 s. Critères qui pèsent le plus : achat du créateur, âge du wallet du créateur, outil de lancement, acheteurs distincts, créateur a vendu, SOL dans la courbe, compte X, ventes avant décision.

---

## 7. Résultats (16/10, 08:14 → 17:17, heure de Paris)

### Scalp Pump.fun

| Règle | Trades | Moyenne / trade | ± (marge) | Total | Sans les 3 meilleurs | Référence (mêmes lancements) | Verdict |
|---|---|---|---|---|---|---|---|
| **F** | 771 | **+6,09 %** | 1,52 | **+4,70 SOL** | +4,35 % | D : +2,40 % | ✅ validé |
| **E** | 3 782 | +1,46 % | 0,50 | +5,53 SOL | +0,87 % | B : +0,12 % | ✅ validé |
| **D** | 777 | +2,44 % | 1,15 | +1,89 SOL | +1,21 % | tous, sortie C : −2,38 % | ✅ validé (de justesse) |
| B | 4 402 | +0,14 % | 0,43 | +0,60 SOL | −0,36 % | | ❌ |
| C | 4 191 | −0,07 % | 0,46 | −0,29 SOL | −0,58 % | B : +0,09 % | ❌ |
| A | 7 985 | −1,02 % | 0,22 | −8,18 SOL | −1,25 % | | ❌ |
| G | 126 / 200 | +3,63 % | 2,93 | +0,46 SOL | +0,18 % | F même période : +8,03 %, +2,79 SOL | en cours, mauvais |
| H | 578 / 600 | +1,02 % | 0,90 | +0,59 SOL | +0,19 % | E même période : +1,10 %, +2,05 SOL | en cours, mauvais |

Par heure (nombre de trades / moyenne / total SOL) :

| Heure | A | B | C | D | E | F |
|---|---|---|---|---|---|---|
| 08 h | 570 / −1,2 % | 344 / −2,1 % / −0,72 | 209 / −3,0 % | — | — | — |
| 09 h | 298 / +0,9 % | 186 / +3,2 % / +0,59 | 186 / +4,4 % | 4 / −8,6 % | — | — |
| 10 h | 822 / −0,8 % | 487 / +1,2 % / +0,58 | 487 / 0,0 % | 62 / +4,3 % | 473 / +1,5 % / +0,69 | 60 / +5,9 % / +0,35 |
| 11 h | 736 / +2,6 % | 481 / **+5,1 %** / +2,47 | 481 / +4,7 % | 106 / +5,8 % | 481 / **+7,4 %** / +3,54 | 106 / **+17,2 %** / +1,83 |
| 12 h | 822 / −1,2 % | 605 / −1,2 % / −0,75 | 605 / −1,3 % | 199 / −1,3 % | 605 / −0,2 % / −0,15 | 199 / −0,4 % / −0,08 |
| 13 h | 1 110 / −2,5 % | 490 / −1,1 % / −0,53 | 490 / −1,4 % | 69 / −3,0 % | 490 / −0,3 % / −0,15 | 69 / −2,2 % / −0,15 |
| 14 h | 793 / −1,7 % | 462 / −1,8 % / −0,81 | 462 / −2,6 % | 61 / +2,2 % | 462 / +0,9 % / +0,40 | 61 / **+17,2 %** / +1,05 |
| 15 h | 1 204 / −1,9 % | 536 / −0,8 % / −0,45 | 536 / 0,0 % | 95 / +7,9 % | 536 / +0,6 % / +0,33 | 95 / +10,2 % / +0,97 |
| 16 h | 1 327 / −1,1 % | 648 / −0,3 % / −0,17 | 648 / −0,3 % | 159 / +2,2 % | 648 / +0,5 % / +0,35 | 159 / +1,4 % / +0,23 |
| 17 h (début) | 303 / −0,5 % | 163 / +2,4 % / +0,38 | 87 / +1,5 % | 22 / +11,7 % | 87 / +5,9 % / +0,51 | 22 / +23,3 % / +0,51 |

Matin (avant 12 h) / après-midi : F +13,1 % (166 trades) / **+4,5 % (478)** ; E +4,4 % / +0,5 % ; D +5,0 % / +2,0 % ; B +2,0 % / −0,8 % ; C +1,8 % / −1,1 % ; A +0,35 % / −1,6 %.
**F est la seule règle nettement positive le matin ET l'après-midi.** Pire creux de F sur la journée : −0,41 SOL depuis un plus haut ; F n'est jamais passée sous zéro.

Vagues observées : ~11 h, ~14 h 30, ~15 h 30-16 h 30 (D), ~17 h. Plus gros trades :
F : AUnB 14:29 +720 %, 4eHW 11:06 +336 %, ECjn 11:40 +298 %, HJ3k 11:17 +219 %, 2LE5 17:04 +189 % ;
E : 6ePH 11:46 +938 %, AUnB +720 %, GYcV 11:27 +569 % ; B : 6ePH +1 293 %, VYmw 10:47 +528 %, 4iPQ 16:31 +378 % ; D : DqYC 16:18 +486 %.

### Copy trading (cloud, depuis le 16/10 matin, paper trading)

| Test | Trades fermés | Résultat |
|---|---|---|
| Témoin (515vh1) | 62 | **+0,64 SOL** |
| Témoin + anti-rug | 25 | +0,03 SOL |
| Raven (frais Raven) + anti-rug | 25 | +0,04 SOL |
| Candidats (13 KOL, 0,05 SOL, max 15 ouverts) | 107 | **−0,56 SOL** (14 ouverts, capital libre presque nul) |
| Top (Mr. Frog) | 1 | −0,01 SOL |

Conclusion : le copy trading est nettement moins bon que le scalp F, sauf le témoin 515vh1.

---

## 8. Analyses complémentaires (faites le 16/10 sur ces données)

**Retard d'exécution** (décision prise sur le prix vu, exécution au prix d secondes plus tard, à l'achat et à chaque vente) :

| Retard | E | F (≈ 475 trades) |
|---|---|---|
| 0 s | +1,77 %, +4,39 SOL | +7,0 %, +3,33 SOL |
| 0,4 s | +1,47 %, +3,62 SOL | +5,6 %, +2,65 SOL |
| 1 s | +1,27 %, +3,13 SOL | +4,8 %, +2,30 SOL |
| 2 s | +0,74 %, +1,83 SOL | +3,2 %, +1,52 SOL |

→ en réel, compter **environ −1,5 à −2 points par trade pour F** avec un bon bot (0,4-1 s). F attendu ≈ **+4 à +5 %** par trade.

**Frais et tips** : déjà couverts par la simulation (0,000105 SOL par transaction ≥ ce que paient 75 % des acheteurs à +5 s). Pas besoin de gros tips à +5 s.

**Taille de la mise** (même journée rejouée) :

| Mise | F moyenne / total | E moyenne / total |
|---|---|---|
| 0,1 SOL | +6,0 % / +2,98 SOL | +1,7 % / +4,32 SOL |
| 0,25 SOL | +5,1 % / +6,26 SOL | +0,8 % / +4,83 SOL |
| 0,5 SOL | +3,3 % / +8,31 SOL | −0,9 % / −11,1 SOL |
| 1 SOL | −0,35 % / −1,74 SOL | −4,3 % / −108 SOL |
| 2 SOL | −6,5 % / −65 SOL | −10 % / −510 SOL |

→ plafond raisonnable **≈ 0,25 SOL par trade pour F** (≈ +3 % réel après retard) ; E ne supporte pas plus de 0,1-0,15 SOL. Plusieurs bots sur les mêmes tokens = une seule grosse mise (même impact) : inutile. Pour grossir : diversifier (autres règles, autres plateformes).

**Capital nécessaire** (positions ouvertes en même temps, au pire) : F ≈ 25 → 2,5 SOL à 0,1 SOL/trade (+ réserve → **3 SOL**) ; E jusqu'à 94 → 5-10 SOL ; B ≈ 18.

**Ce qu'aurait fait le réel depuis 10 h** (SOL ≈ 93,8 €, Kraken 16/10) : F (3 SOL de départ) +2,88 SOL en simulation à 14:52 → **≈ +2,0 à +2,3 SOL réels** ; E (10 SOL) +4,26 → ≈ +3,0 à +3,5 SOL. Avec 3 % de coûts réels par trade, E serait négative (−2,95 SOL) et F resterait positive (+1,44 SOL).

**Filtre « vague »** (indicateur causal = moyenne des trades B déjà revendus sur 30 min) : sur la journée (déjà vue), après 30 min où B était négatif, F/E/B perdaient (F −0,8 %, E −1,2 %) ; après 30 min où B > +2 %, ils gagnaient (F +11,9 %, E +4,8 %). Le nombre de lancements, lui, ne prédisait rien. **Mais en test sur l'avenir (G/H), le filtre rate des pumps qui arrivent sans prévenir (AUnB +720 % à 14:29) et fait 3 à 6 fois moins que F/E.**

---

## 9. Erreurs trouvées et corrigées (à connaître)

1. **Biais d'anticipation dans la première analyse de sortie (16/10 ~10 h)** : « moitié à ×2, reste −40 % » donnait +10 % / +4 % parce que la revente à 60 s était décidée en sachant si ×2 viendrait plus tard. Corrigé avant de figer E/F (règle causale actuelle : sans ×2 à 60 s → sortie de C). Les vrais chiffres étaient +1,2 % / +0,8 %.
2. **Faux trade +9 784 % (CcyF…, 16:39)** : une transaction de vente mal lue (réserve qui paraît vide une ligne). 7 cas sur 868 000. Corrigé par `drop_spikes()` (une ligne qui s'écarte de > 40 % de ses deux voisines, elles-mêmes à moins de 10 % l'une de l'autre, est ignorée) ; test `test_scalp_drop_spikes`. Sans ce filtre, E affichait +14,9 SOL au lieu de +5,4. **Le code du PC (`scalp.py`) a probablement le même défaut** : à corriger aussi sur le PC.
3. Le premier scalp cloud passait par PumpPortal (≈ 0,5 s de retard, plafonds différents) ; remplacé par la réplique exacte via gRPC.
4. Les processus cloud mouraient ~5 min après inactivité de la session → gardien en boucle + réveils toutes les 15 min.

---

## 10. Hypothèses et limites (honnêtement)

- **Une seule journée** de données pour C-H, avec 3-4 vraies vagues. Les trades d'une même vague sont corrélés : il y a moins d'exemples indépendants que de trades. **La nuit et les heures US tardives n'ont pas encore été vues** par E/F.
- Les gains dépendent de quelques gros pumps : c'est le principe (« les gros gains rattrapent les petites pertes »). F reste positive sans ses 3 meilleurs trades, mais une journée sans vague peut coûter ≈ −1 à −2 SOL à 0,25 SOL/trade.
- Le score utilise parfois des métadonnées (X, Telegram, site) récupérées après +5 s : en réel elles ne seront pas toujours là au moment de décider (peut réduire F/D).
- Retard d'exécution, transactions ratées, sandwichs : estimés (section 8), pas mesurés. **Le test réel sert à les mesurer.**
- La vente de la moitié est approximée linéairement.
- Les autres acheteurs ne réagissent pas à nos ordres dans la simulation (vrai à 0,05-0,1 SOL, de moins en moins vrai au-dessus).
- Fiscalité (France) : conversion en euros imposable (≈ 30 % sur la plus-value), formulaire 2086, et 3916-bis pour un compte sur une plateforme étrangère.

---

## 11. Plan du test réel (validé dans le principe par l'utilisateur, pas encore codé)

- **Règle : F** (sélection du score + sortie E), seule. E reste en simulation à côté pour comparer.
- **Mise : 0,05 SOL par trade** (0,02 SOL ferait trop peser les frais fixes).
- **Wallet neuf** dédié au bot, clé seulement sur le PC. Capital de travail ≈ **1,5 SOL**.
- **Arrêt automatique** si le wallet du bot passe sous **1 SOL** (perte max ≈ 0,5 SOL ≈ 47 €).
- **Retrait automatique** du surplus au-dessus de **2 SOL** vers le wallet personnel de l'utilisateur (adresse fixée à l'avance dans la config, seule destination autorisée).
- **Tolérance de prix serrée** sur chaque ordre (limite sandwichs / mauvais prix) ; fermer le compte du token après chaque vente (récupère ≈ 0,002 SOL).
- **Pour chaque trade, enregistrer prix simulé ET prix réel**, latence décision → bloc, transaction ratée ou non.
- **Bilan après 100-150 trades réels (≈ 1 jour)** : si F réel ≥ +2 % par trade → passer à 0,1 SOL, puis 0,25 SOL (plafond).
- Étape proposée (pas encore acceptée) : écrire d'abord le bot réel en **mode à blanc** (tout comme en vrai sans rien envoyer, sans clé), puis passer en réel.
- Suivi en direct souhaité par l'utilisateur sur PC et téléphone : petite page locale sur le PC (accès téléphone via Tailscale), et/ou notifications Telegram par trade.

---

## 12. À faire sur le PC, dans l'ordre

1. **Diagnostic** sans rien relancer : espace disque (`Get-PSDrive C`), fenêtres/tâches lancées au démarrage (les `start_*.bat` d'`install_live.ps1` sont dans le dossier Démarrage), journaux du plantage si utile.
2. **Récupérer l'enregistrement gRPC de la nuit du 15 au 16/10 sur le PC** (fichier du recorder du PC, même format que `pumpfun.jsonl`) et y **rejouer B, E, F** (code : `copysim/scalpgrpc.py` + `copysim/scoreD.py` de cette branche) pour voir **la nuit**, jamais vue. Attention : D/F ont besoin du fichier enrichi (`pump_enrich.jsonl`) du PC pour le score.
3. **Mettre à jour le code du PC** depuis cette branche (au minimum `drop_spikes()` dans le chargement des lancements, règles C-H, `scoreD.py`, `nuit/lecons.py`, `nuit/dash_*.py`, `prereg/scalp_rule_*.json`).
4. Décider avec l'utilisateur **ce qui tourne où** (cloud ou PC) pour ne pas doubler Chainstack/Helius ; si le PC reprend le hub gRPC + scalp, arrêter ceux du cloud et les deux tâches planifiées du cloud.
5. Préparer le **bot réel de F** (section 11), d'abord à blanc.
6. Régénérer les clés exposées après les tests (section 3).

---

## 13. Idées pour plus tard (non commencées)

- Autres plateformes de lancement sur Solana (LetsBonk / Raydium LaunchLab, Moonshot, Believe), tokens « diplômés » sur PumpSwap ; plus tard d'autres chaînes (four.meme sur BNB, Zora/Clanker sur Base). Même parcours : enregistrer → papier → figer → vérifier sur l'avenir.
- Réoptimisation nocturne « walk-forward » (proposée, pas acceptée). Pour l'instant la « leçon du jour » est **manuelle** : quand l'utilisateur dit « leçon du jour », lancer `python3 nuit/lecons.py` (avec `.env`) et présenter `reports/lecons.md`.
- Notifications Telegram par trade (proposées).

---

## 14. Commandes utiles (cloud, Linux ; adapter sur Windows)

```bash
cd copy_sim
set -a; . ./.env; set +a
PYTHONPATH=$PWD python3 -m copysim scalp-grpc --file data_grpc/pumpfun.jsonl --start-file data_grpc/START --once   # rapport A-H
PYTHONPATH=$PWD python3 nuit/lecons.py            # leçon du jour
PYTHONPATH=$PWD python3 nuit/dash_export.py && python3 nuit/dash_static.py   # pages de suivi
python3 -m pytest -q tests                        # 37 tests
```

Fichiers clés : `copysim/scalpgrpc.py` (A, B, C, E, G, H, courbe, `drop_spikes`), `copysim/scoreD.py` (D, F), `copysim/grpchub.py` + `copysim/pumprec.py` (hub et recorder gRPC), `nuit/scalp_score.py` (score du PC), `nuit/pump_enrich.py` (collecteur), `prereg/scalp_rule_*.json` (règles figées), `tests/test_copysim.py`.
