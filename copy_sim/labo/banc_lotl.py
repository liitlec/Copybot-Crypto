"""Banc Lot L (PRIORITES 27/11 9 h 50, demande écrite de Baptiste, fait sur Opus) : tirer plus des tendances sans
augmenter le risque d'arrêt. CONTRAT FIGÉ ET POUSSÉ AVANT TOUT RÉSULTAT.

CADRE : celui des lots J/K. Or M5 du courtier ; principal = paniers / trades fermés 06/08/2025 -> 31/08/2026 ; RÉSERVE =
01/09 -> 11/11/2026 ; H1 2024-26 en information. Référence REF = robot actuel : bt_or_plus v4 (renforts 1-2-3-4-5 tous
les 0,25 ATR, sortie point mort dès 4 positions + paliers +2/+4 R) + les 5 règles courtes telles quelles (0,01 lot).
PISTES NOUVELLES (8 variantes ; seule la partie concernée change, le reste = REF) :
  P1 « pyramide de paniers » : quand un panier atteint un gain latent >= 2 R (P1a) / 4 R (P1b), un 2e panier INDÉPENDANT
     s'ouvre dans le même sens à la clôture suivante (mêmes renforts, même sortie v4, au plus 2 paniers par sens).
  P2 « réentrée » : après une sortie de panier au-delà de +2 R (palier ou point mort en gain), réouverture dans le même
     sens sans attendre les heures d'entrée : P2a à la clôture suivante si la clôture reste du bon côté de l'EMA 2 jours ;
     P2b seulement si une clôture dépasse le prix de sortie (sens du panier) dans les 12 bougies (1 h).
  P3 « renforts sur replis » : à la place de la grille sur cassure, renfort (même taille n, même maximum 5) quand le
     panier est en gain et que la clôture revient toucher la moyenne exponentielle courte (P3a EMA 20 M5, P3b EMA 50 M5)
     dans le sens du panier ; un renfort au plus par repli (il faut ressortir de la moyenne de 0,25 ATR).
  P4 « règles courtes avec le panier » : P4a elan_m15 et cassure_m15 seulement dans le sens d'un panier bt_or_plus d'au
     moins 4 positions ouvert au moment du signal (les 3 autres règles inchangées) ; P4b toutes les règles inchangées
     sauf la tenue d'elan_m15 / cassure_m15 portée de 12 à 24 bougies M15 quand un tel panier est ouvert dans leur sens.
MESURES (série journalière combinée en USC : bt_or_plus = USD par lot de base x 0,05 x 100, règles courtes = gain à 0,01
  lot) : total, gain÷pire baisse, Sharpe ; À RISQUE ÉGAL (facteur constant pour le même écart-type journalier que REF sur
  la période principale, appliqué aussi à la réserve et au Monte-Carlo) ; réserve : total et gain÷pire baisse ; P(arrêt
  -34 %) en 12 mois (Monte-Carlo par semaines du lot I, base 0,05 v3, 1 000 parcours) ; positions simultanées maximales
  (plafond du pont : 10) ; rejeu du panier réel / démo depuis le 18/11 quand c'est calculable.
PLACEBO (par piste, 200 tirages ; p = part des placebos au gain÷pire baisse à risque égal >= réel, période principale) :
  P1 : 2e panier ouvert à des clôtures tirées au hasard pendant la vie d'un panier du même sens (même fréquence) ;
  P2 : réouvertures à des clôtures tirées au hasard après une sortie (même nombre) ; P3 : renforts à des clôtures tirées au
  hasard pendant que le panier est en gain (même fréquence) ; P4 : le même nombre de trades d'elan/cassure gardés (P4a)
  ou allongés (P4b) tirés au hasard par mois. Correction de Holm sur les 8.
RETENUE si (à risque égal) : gain÷pire baisse ET Sharpe > REF sur la période principale ; total ET gain÷pire baisse >
  REF sur la réserve ; p Holm < 0,05 ; > REF au spread doublé ; P(arrêt) pas plus de 2 points au-dessus de REF ; jamais
  plus de 10 positions simultanées. Si une piste est RETENUE : préparer la v5 réelle SANS la publier ; Baptiste décide.
Usage : python3 banc_lotl.py
"""
