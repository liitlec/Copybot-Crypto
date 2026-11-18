# Plan pour le compte réel (compte cent) — décidé avec Baptiste le 18/11/2026

Démarrage seulement si le verdict du test (vendredi 20/11 soir) est bon, et sur décision de Baptiste sur son PC
(le pont est verrouillé sur la démo ; aucun ordre réel n'est passé par le labo sans son geste explicite).

1. **Compte cent**, mêmes conditions que la démo (tout divisé par 100).
2. **Le mélange simple** : bt_or + rebonds d'indices (repli_ind, rebond_nas, rebond_sp, fomc_dax). Pas de règles
   courtes sur l'or, pas de variantes, pas de témoin en réel.
3. **Plan de mise à −30 %** (banc_plan_cent.py) : 0,01 lot cent sur l'or pour 100 € (0,05 pour 500 €), mise en % du
   compte recalculée chaque semaine. **Arrêt automatique à −34 % du plus haut**, puis attente de la décision de Baptiste.
4. **Intérêts composés** : tous les gains restent sur le compte et augmentent la mise de trade en trade (mise en % du
   compte, recalculée chaque semaine).
5. **Retraits pour sécuriser** (faits par Baptiste lui-même, le robot ne retire jamais d'argent) : récupérer la mise de
   départ dès que possible, puis trader uniquement avec les gains, et retirer une part des gains de temps en temps.
   **Règle retenue (banc_retrait.py, 18/11) : quand le compte a doublé, retirer la mise de départ, puis laisser
   tourner** (100 € → retrait de 100 € à 200 € ; 500 € → retrait de 500 € à 1 000 €). Coût : ≈ 0 en scénario prudent,
   ≈ 13 % du total à 24 mois si l'avantage mesuré se confirme ; mise récupérée en 24 mois : 82 % (mesuré), 39 % (prudent).
6. **Ajustement mensuel** : la démo continue avec toutes les variantes (dont bt_or_plus_opt) ; chaque mois, les poids
   du compte réel bougent un peu vers ce qui a vraiment gagné en direct, jamais d'un coup.
7. Aucune nouvelle VERSION n'est installée sur le compte réel sans l'accord explicite de Baptiste sur son PC.
