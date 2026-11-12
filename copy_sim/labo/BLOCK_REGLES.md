# Règles des robots « Block » de Baptiste (résumé du code MQL5, 12/11/2026)

Résumé écrit à partir du code des EA et de leurs réglages en vigueur (fichiers `.ini` relus toutes les 5 min et
fichiers d'état écrits par les EA), **sans le code**. Tous tournent sur le compte démo STARTRADER (levier 1:500,
**hedging**), un seul EA par famille posé sur un graphique, qui gère tous ses marchés ; chaque marché a son numéro
magique (base + 0, +1, …). Heures = **heure du serveur** (Paris + 1 h). Trades réels de ces robots :
`mt5/autres/historique.csv.gz` et `mt5/autres/ouvertes.json` (même table magique → robot).

| Robot | Magiques | État au 12/11 | Idée |
|---|---|---|---|
| BlockTrend v1.05 | 702100-702112 | **en marche** depuis le 05/10 | suivi de tendance, renforcement dans le sens du prix |
| BlockGrille v1 | 704100-704132 | **en marche** depuis le 06/10 | retour à la moyenne en H4 quand le marché fait du surplace |
| BlockRange v1 | 703100-703111 | **en marche** depuis le 05/10 | achat d'indices après une petite baisse dans une tendance haussière |
| BlockFinMois v1 | 705100-705161 | **en marche** depuis le 09/10 (aucun trade fermé à ce jour) | effet de fin de mois |
| BlockFIFO v25 | 701100 | **en pause** depuis le 05/10 (fichier de risque = 1) | grille contre le prix, clôture FIFO par blocs |
| BlockTrend_pari, BlockFinMois_pari | 7121xx, 7151xx | copies pour un **autre** compte (« pari »), état non mis à jour depuis le 16/10 | même code, risque plus élevé |

Réglages communs à tous : interrupteur `InpEnabled` (false = plus de nouveau panier, les ouverts sont gérés jusqu'au
bout), liste `InpBloques` (marchés sans nouvelle entrée), plafond de lot par position, pause de 60 s après un ordre
refusé par le courtier, pas d'entrée si le spread dépasse N × le spread habituel (moyenne glissante).

---

## 1. BlockTrend v1.05 — suivi de tendance (le principal)

**Marchés** : XAUUSD (réglage « serré »), XAGUSD, BTCUSD, ETHUSD, Cocoa-C (réglage « très large »). L'argent est
**bloqué** (swap acheteur trop cher, ≈ −138 %/an). Trois paniers indépendants par signal (même entrée, sorties
différentes) :
- **BT** (702100-702104) : panier normal, sur les 5 marchés ;
- **BTS** (702105-702108, or, BTC, ETH, cacao) : « sortie resserrée » — une fois le panier monté à +2 R (R = distance
  du stop initial), le recul de sortie est divisé par 2 ;
- **BTI** (702109-702112, mêmes marchés) : « sortie si tendance inversée » — fermé s'il est perdant et que la clôture M1
  passe de l'autre côté de l'EMA de plus de 0,4 × ATR.

**Sens** : clôture M1 précédente au-dessus de l'EMA M1 2880 (2 jours) → achats seulement ; en dessous → ventes
seulement. Un panier ouvert n'est pas fermé par un changement de sens : les deux côtés peuvent coexister.

**Entrée** : aux heures serveur 03:02, 08:00, 08:30, 12:00, 15:45, 16:00, 16:30 (fenêtre de 120 s), ou en « reprise »
dans les 30 min qui suivent la fin d'un panier du même côté.

**Ajouts** : dans le sens du prix (pyramide), +1 position de même lot à chaque « pas », 10 positions au plus par
panier, 3 s au moins entre deux ajouts. Depuis v1.05 : seulement sur **clôture d'une bougie M5** au-delà du niveau ;
si la clôture est déjà à plus d'½ pas au-delà, le niveau est sauté (pas de course après le prix).

**Distances** (multiples de l'ATR journalier 20 j de la veille, figées à l'ouverture du panier) :

| Réglage | Pas des ajouts | Stop initial et recul de sortie |
|---|---|---|
| Serré (or) | 0,25 ATR | 0,6667 ATR |
| Très large (autres) | 0,5 ATR | 1,5 ATR |

**Sortie** : tout le panier quand le prix recule de la distance « stop » depuis son meilleur niveau (stop suiveur),
ou stop initial à la même distance contre la 1re entrée. Les stops sont surveillés par l'EA (stop virtuel) ; depuis
v1.05, un **stop de secours** est aussi posé chez le courtier sur chaque position, 0,25 × stop au-delà du stop virtuel.

**Taille** : lot = risque % du solde / (distance du stop × valeur d'un point par lot), plafond 20 lots par position.
Risque **0,53 % du solde par panier** (choisi le 07/10 : avec 3 paniers par signal, même pire baisse simulée que
0,65 % avec 2). Multiplicateurs : or × 1,5, cacao × 1,5 ; **ventes × 0,5** ; marché agité (ATR 20 j > 1,2 × ATR
100 j) × 0,5. Frein sur baisse du solde : présent, désactivé.

**Protections** : pas d'entrée ni d'ajout si spread > 4 × habituel ; repos après un panier perdant : 60 min (or),
**24 h** pour BTC, ETH et cacao (par marché et par côté). Pause après N pertes d'affilée et filtre d'annonces :
présents, désactivés.

**Copie « pari »** (7121xx) : même code, autre compte, risque 1 % par panier.

## 2. BlockGrille v1 — retour à la moyenne en H4

**Marchés** (33) : 12 indices (SP500+, NAS100+, DJ30+, US2000+, GER40+, UK100+, FRA40+, EU50+, Nikkei225+, SPI200+,
HK50+, ES35+), 18 paires de devises, XAUUSD, BTCUSD, ETHUSD.

**Signal** (à chaque nouvelle bougie H4, sur celle qui vient de fermer) : le marché fait du **surplace** (efficacité
de Kaufman sur 30 bougies ≤ 0,3) **et** la clôture est à au moins **2 ATR H4** de l'EMA 20 → panier à contre-sens
(vente au-dessus, achat en dessous). Un panier à la fois par marché.

**Entrées et ajouts** : 1re position au marché ; 2e et 3e en **ordres limites** à 1 et 2 ATR plus loin contre le prix,
même lot. Pas d'autres ajouts.

**Stop** : commun, chez le courtier, à 3 ATR de la 1re position (1 R = perte si les 3 positions sont prises).

**Sortie** : tout le panier quand une clôture H4 revient à l'EMA 20, ou après 30 bougies H4 (5 jours) ; les ordres
limites restants sont supprimés.

**Taille** : lot = risque / (6 ATR × valeur du point) → **0,2 % du solde** perdu si les 3 positions vont au stop ;
plafond 20 lots. Spread maximal : 3 × habituel. Le code le dit lui-même : avantage « très mince », à tester en démo.

## 3. BlockRange v1 — achat des indices après un repli

**Marchés** : les 12 indices ci-dessus. Achats seulement, 1 position à la fois par indice.

**Entrée** (au début de chaque journée, nouvelle bougie D1) : RSI 2 jours de la veille **< 10** et clôture de la
veille **au-dessus de la moyenne 200 j** → achat. Pas de nouvel achat le jour qui suit une sortie. Si le spread est
anormal (ouverture de séance), l'achat attend, puis est abandonné pour la journée après 180 min.

**Stop** : dur, chez le courtier, à **2 × ATR 20 j** sous l'entrée.

**Sortie** : au début d'une journée, dès que la clôture de la veille passe au-dessus de la moyenne 5 j, ou au plus tard
après 10 jours de bourse.

**Taille** : **1 % du solde** perdu au stop dur ; plafond 50 lots. Spread maximal : 3 × habituel.

## 4. BlockFinMois v1 — effet de fin de mois

**Quand** : le **dernier jour de bourse du mois, à 21 h serveur** (2-3 h avant minuit, où le spread des devises est
≈ 4 × plus large), avec 120 min pour réussir l'entrée. Les sorties se décident à la même heure les jours suivants.

**Piste A, devises** (18 paires, 705100-705117) : achat si le **RSI 2 j < 30** ; stop dur à **2 × ATR 20 j** ; sortie
dès que le prix dépasse la moyenne 5 j, ou après 10 jours de bourse.

**Piste B, indices** (12 indices, 705150-705161) : achat si le **mois est négatif** et le prix **au-dessus de la
moyenne 200 j** ; stop dur à **3 × ATR 20 j** ; sortie après 10 jours de bourse.

**Taille** : risque **par occasion** de 3 % du solde pour chaque piste, réparti à parts égales entre les marchés qui
donnent un signal ce jour-là ; plafond 50 lots. Spread maximal : 3 × habituel (on réessaie). Copie « pari » (7151xx) :
5 % par occasion.

## 5. BlockFIFO v25 — grille contre le prix, clôture par blocs (en pause)

**Marché** : XAUUSD seul, magique 701100.

**Sens** : clôture M1 au-dessus / au-dessous de l'EMA M1 720 (12 h) → panier acheteur / vendeur.

**Entrée** : mêmes heures que BlockTrend (03:02 … 16:30, fenêtre 120 s) ou reprise dans les 30 min après la clôture
complète d'un côté. Pas de nouveau panier de 130 min avant à l'heure d'une annonce USD rouge (calendrier MT5), ni si le
spread dépasse 0,50 $, ni quand le fichier de risque externe vaut « 1 » (c'est ainsi qu'il est en pause).

**Ajouts** : **contre le prix** (grille) : un niveau tous les 1,5 $ contre la dernière entrée, jusqu'à 223 niveaux et
100 $ entre la 1re entrée et le dernier ajout, 3 s au moins entre deux ajouts. Lot « en cloche » : 0,02 au niveau 0,
monte jusqu'à × 3 (0,06) au niveau 5, puis décroît de 2 % par niveau ; plafond 1 lot par niveau.

**Sortie (le cœur)** : clôture **FIFO par blocs** — l'EA cherche le plus petit bloc des positions **les plus
anciennes** dont le résultat net cumulé atteint le seuil (2,4 $ ; à partir de 6 positions, 80 $ par lot du bloc), et
le ferme entièrement (20 positions au plus d'un coup). Gros paniers (≥ 6 positions) : au lieu de fermer tout de suite,
**suivi du gain** — plus d'ajout, mémorisation du meilleur prix, fermeture du plus grand bloc gagnant sur un recul de
2 $ ou si le gain retombe sous un plancher de 20 $ par lot.

**Stops** : stop du panier à **−12 % du solde** (il attend si le spread dépasse 1 $, sauf perte > 15 %) ; plafond de
perte toutes directions confondues à 20 % du solde. Contrôle de marge avant chaque ordre.

**Options présentes mais désactivées** : filtre ADX et distance minimale à l'EMA, arrêt du vendredi soir, filtre de
volatilité, grille adaptative à l'ATR, contre-panier renforcé, durée maximale d'un panier, jours bloqués.

**Pourquoi en pause** (notes de Baptiste du 05/10) : un stop de panier le 02/10 a coûté ≈ −12 700 $ ; en simulation
sur ticks réels, la grille est ruinée vers février 2026 et les 13 variantes testées perdent toutes (cause : les
tendances de ≈ 100 $ contre un panier).

---

## Ce que Baptiste en attendait (ses simulations, à vérifier par toi)
- BlockTrend : gagnant en simulation sur or, argent, BTC et ETH en 2025 **et** 2026 avec 4 largeurs de réglage ;
  perdant sur indices, devises et platine (d'où leur absence). Portefeuille « or serré + 3 autres très large » à
  0,75 % : ≈ +9 %/mois simulé, pire baisse ≈ −24 %.
- BlockRange, BlockGrille, BlockFinMois : « amortisseurs » qui gagnent quand les marchés ne tendent pas, testés par
  des scripts Python (`outils\mr_test.py`, `grille_h4_long.py`, `sniper_robuste.py`) ; avantage annoncé mince.
- **Le réel en démo ne confirme pas tout** : voir `mt5/autres/historique.csv.gz` (au 12/11 : BlockTrend −24 647 $ en
  positions fermées sur 139, BlockFIFO −6 340 $ sur 1 507, BlockRange −2 307 $ sur 4, BlockGrille −31 $ sur 82).
