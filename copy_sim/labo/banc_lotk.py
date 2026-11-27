"""Banc Lot K (PRIORITES 27/11 9 h 35, demande écrite de Baptiste) : taille des renforts de bt_or_plus par coefficient.
CONTRAT FIGÉ ET POUSSÉ AVANT TOUT RÉSULTAT.

DONNÉES et CADRE : ceux du lot J (banc_lotj) : or M5 du courtier, principal = paniers fermés 06/08/2025 -> 31/08/2026,
RÉSERVE = 01/09 -> 11/11/2026 ; spread réel puis doublé ; même entrée, mêmes renforts (tous les 0,25 ATR, 5 positions),
SORTIE v4 (point mort dès 4 positions + paliers +2/+4 R) pour TOUTES les variantes. Seule change la taille w_n du
n-ième ordre du panier (w_1 = 1, en lots de base). H1 2022-24 / 2024-26 en information.
VARIANTES (13 + référence) :
  REF       v4 : w_n = n (1-2-3-4-5) ;
  g1,2 / g1,4 / g1,6 / g2,0   géométrique fixe w_n = c^(n-1), 5 positions ; g1,4x6 : c = 1,4 et 6 positions ;
  d0,8      décroissant w_n = 0,8^(n-1) ;
  Adaptatifs (w_n = w_(n-1) x c, c calculé au moment du renfort avec les seules bougies fermées, borné 1,0-2,0) :
  er4, er12      c = 1 + efficacité de Kaufman de la clôture sur 48 / 144 bougies M5 (4 h / 12 h) ;
  er4x2          c = 1 + 2 x efficacité 4 h (borné à 2) ;
  gain2, gain4   c = 1 + gain latent du panier en R / 2 (resp. / 4), borné ;
  volbas, volhaut  c = 1 + (1 - ATR/médiane 20 j de l'ATR) (calme -> plus gros) / 1 + (ATR/médiane - 1) (agité -> plus
                 gros), bornés.
MESURES : brut (base 1) : total R, gain÷pire baisse, Sharpe journalier ; À RISQUE ÉGAL : chaque variante multipliée par
  un facteur constant qui donne le même écart-type journalier que REF sur la période principale (le même facteur sert
  sur la réserve et pour l'argent) ; réserve : total et gain÷pire baisse ; argent : 20 000 USC, base 0,05 x solde /
  20 000 (v3) x facteur, P(arrêt -34 %) en 12 mois (Monte-Carlo du lot I, 1 000 parcours) ; plus grosse position et
  plus gros panier en lots à base 0,05 x facteur (signalé si une position dépasse le plafond local 0,25 lot) et marge
  maximale du panier au levier 500 (contrat 1 : marge = lots x prix / 500 $) ; paniers démo/réels depuis le 18/11
  (rejeu GC=F 5 min du lot J, descriptif).
TESTS : placebo = signes des différences appariées (paniers de même ouverture, séries à risque égal) tirés au hasard,
  2 000 tirages, période principale ; correction de Holm sur les 13.
RETENUE si (à risque égal) : gain÷pire baisse ET Sharpe > REF sur la période principale ; total ET gain÷pire baisse >
  REF sur la réserve ; p Holm < 0,05 ; > REF au spread doublé (principale) ; P(arrêt) pas plus de 2 points au-dessus de
  REF ; aucune position au-dessus de 0,25 lot à base 0,05.
Si une variante est RETENUE : préparer le robot réel v5 SANS le publier (VERSION inchangée) ; Baptiste décide.
Usage : python3 banc_lotk.py
"""
