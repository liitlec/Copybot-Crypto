"""Banc Lot H, tests B1 à B4 (PRIORITES 26/11 19 h 30, demande écrite de Baptiste : « pousser la stratégie au
maximum… s'adapter en live aux trades passés »). CONTRAT FIGÉ ET POUSSÉ AVANT TOUT RÉSULTAT.

DONNÉES : or du courtier, spread réel de chaque bougie (puis doublé). M5 08/2025 -> 11/2026 (15 mois) ; H1 08/2022 ->
11/2026 (4 ans), blocs B1 = 08/2022-09/2024, B2 = 10/2024-11/2026. Mécanique bt_or_plus (entrées bt_or, sens EMA
2 jours, renforts tous les « pas » ATR à la clôture, sortie de tout le panier au recul depuis le meilleur prix), même
convention que banc_lotg.plus. Unité R = perte d'une position de taille 1 au recul de référence 0,6667 ATR.
Argent : compte cent, contrat 1 (journal réel), 1 USD de mouvement x 1 lot = 100 USC ; gain d'un panier en USC =
base x somme(taille_k x sens x (sortie - entrée_k)) x 100. Départ 20 000 USC. Arrêt du pont à -34 % du plus haut.

B1 — INTÉRÊTS COMPOSÉS. Mise fixe (base 0,05) contre mise proportionnelle au solde (v3 : base = 0,05 x solde / 20 000,
  vers le bas au pas 0,01, fixée à l'ouverture de chaque panier, 5 x base <= plafond ; plafond 0,25 = aujourd'hui,
  et 0,50 = borne du pont). Paniers de bt_or_plus tel quel (REF). Rejeu réel (H1 depuis le début de B1 et de B2, M5
  depuis son début) et Monte-Carlo (2 000 parcours, blocs de semaines entières tirées au hasard, longueur moyenne
  4 semaines) sur 6 / 12 / 24 mois ; scénarios mesuré et prudent (avantage ÷ 2 : chaque panier diminué de la moitié du
  R moyen). Mesures : valeur finale (médiane, 10e centile), pire baisse, temps médian pour x2, probabilité d'atteindre
  l'arrêt -34 %.
B2 — FORME DE LA PYRAMIDE (une dimension à la fois autour de REF = 5 positions, pas 0,25, tailles 1-2-3-4-5) :
  positions max {4, 6, 7} ; pas {0,20 ; 0,35} ATR ; tailles {1-1-2-2-3, 1-1,5-2-2,5-3, constante 1}. 8 variantes + REF.
  Les paniers s'ouvrent et se ferment aux mêmes instants (seuls les renforts changent) : comparaison appariée.
  Mesures : gain÷pire baisse et Sharpe journalier (indépendants de la mise : risque égal), total R ; M5, H1 B1, H1 B2 ;
  placebo = signes des différences appariées tirés au hasard (2 000) ; reality check de White sur les 8 ; walk-forward
  (M5 6->1 mois, H1 12->3 mois, choix au meilleur gain÷pire baisse). RETENUE si gain÷pire baisse ET Sharpe > REF sur M5,
  H1 B1 et H1 B2, p White < 0,05 sur un jeu et < 0,15 sur l'autre, walk-forward >= REF sur les deux, et > REF au spread
  double.
B3 — RETRAITS (calcul seulement ; le robot ne retire jamais rien) sur la mise proportionnelle (plafond 0,50), rejeu et
  Monte-Carlo 12 / 24 mois : (a) retirer 20 000 USC au premier doublement ; (b) 25 % et 50 % des gains de la semaine
  chaque lundi ; (c) chaque lundi, tout ce qui dépasse 40 000 USC. Mesures : argent retiré (médiane, 10e centile),
  valeur restante, total (retiré + restant), probabilité d'arrêt -34 %, contre « sans retrait ».
B4 — ADAPTATION EN DIRECT AUX TRADES PASSÉS. Grille bt_or_plus (27) : pas {0,20 ; 0,25 ; 0,35} x recul de sortie
  {0,50 ; 0,6667 ; 0,85} ATR x positions max {3, 5, 7}. Chaque lundi, le réglage est re-choisi sur les paniers FERMÉS
  des N dernières semaines (N = 4, 13, 26 ; critère : total R, puis gain÷pire baisse : 6 règles d'adaptation) et appliqué
  aux paniers ouverts la semaine suivante. Contre « réglage fixe » REF (pas 0,25, recul 0,6667, 5 positions), hors
  échantillon. Placebo : réglage tiré au hasard chaque lundi (même grille), 500 tirages ; p = part des placebos >= réel.
  Règles courtes (listes de trades REF du lot G, M15/M5, 15 mois) : poids de chaque règle chaque lundi = 1 si son résultat
  sur les N dernières semaines est > 0, sinon 0 ; et « proportionnel » (poids = résultat / moyenne des résultats positifs,
  plafonné à 2) ; contre poids 1 fixe ; placebo = poids permutés entre règles chaque semaine (500 tirages).
  Comparaison à risque égal (rapport moyenne/écart-type des P&L hebdomadaires) et en total. RETENUE si bat le fixe en
  B1 ET B2 (H1) et sur M5, p placebo < 0,05 (Holm sur les règles d'adaptation essayées), et encore au spread double.
B5 — ce qui est RETENU -> version réelle suivante (mode auto) ; sinon on reste en v3. Résultats en tête d'AVIS.md.
Usage : python3 banc_loth.py
"""
