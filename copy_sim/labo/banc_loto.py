"""Banc Lot O (PRIORITES 28/11, Baptiste : « à partir de tant de % par jour, on coupe les paniers pour encaisser et on
rouvre directement »). CONTRAT FIGÉ ET POUSSÉ AVANT TOUT CALCUL.

CADRE : celui de banc_lotm_astra.py. Or M5 du courtier 06/08/2025 -> 11/11/2026 ; bt_or_plus v4 (moteur
banc_lotm_astra.simule) ; argent : 20 000 USC, base v3 0,05 x solde / 20 000, règles courtes (0,01 x solde / 20 000),
garde-fou −5 %/jour, arrêt −34 %, BUDGET DE RISQUE q = 1/2 (la v5) ; principal = jusqu'au 31/08/2026, réserve
01/09 -> 11/11/2026 ; spread réel puis doublé. Swap : non modélisé (aucune donnée de swap ; couper et rouvrir ne change
presque pas la durée tenue, donc l'effet est voisin pour toutes les variantes) — dit comme une limite.
RÉFÉRENCE = v4 + budget 1/2 (la v5), sans coupure.

DÉCLENCHEUR, évalué à chaque clôture M5 dans le moteur (qui suit son propre solde : base v3, règles courtes ajoutées
à leur sortie, journée = jour de Paris, référence = solde au début de la journée S0) :
  « compte » (C) : (solde + latent des paniers bt_or_plus) - S0 >= X % de S0 -> on ferme TOUS les paniers bt_or_plus
                   ouverts au prix de la bougie (bid achat, ask vente), on encaisse, et on rouvre aussitôt un panier
                   neuf dans le même sens à la même bougie (prix + spread), base v3 du nouveau solde, ATR du jour,
                   pyramide repartie de zéro (renforts, recul, paliers, point mort : règles v4 depuis ce nouveau départ) ;
  « panier » (P) : latent d'UN panier >= X % de S0 -> on ferme ce panier seulement et on le rouvre de même.
  X = 1 / 2 / 3 / 5 %. Mode « une fois » (U) : au plus une coupure par jour (par déclencheur) ; mode « palier » (K) :
  une coupure chaque fois que le seuil suivant (k x X %, k = 1, 2, 3…) est atteint dans la journée.
  16 VARIANTES : {C, P} x {1, 2, 3, 5 %} x {U, K}. Règles courtes inchangées, jamais coupées.
MESURES : rejeu historique en USC (budget 1/2 appliqué par la couche d'argent de banc_lotm_astra, comme la v5) :
  total, gain÷pire baisse et Sharpe journaliers (principal), total et gain÷pire baisse (réserve), total au spread
  doublé ; nombre de coupures ; gain moyen d'une coupure (encaissé) ; Monte-Carlo apparié (2 000 parcours de 12 mois,
  blocs de semaines, mêmes tirages que la référence) : P(arrêt −34 %), equity médiane, écarts avec IC 90 %.
PLACEBO (graine 2811, 200 tirages par variante) : autant de coupures-réouvertures (en espérance) à des clôtures M5
  tirées au hasard parmi celles où un panier est ouvert, même type (C : tous les paniers ; P : un panier) ;
  statistique = gain÷pire baisse du principal en USC ; p = part des placebos >= réel. Holm sur les 16.
ADOPTION : gain÷pire baisse ET Sharpe > RÉFÉRENCE (principal) ; total ET gain÷pire baisse > RÉFÉRENCE (réserve) ;
  total > RÉFÉRENCE au spread doublé ; P(arrêt) <= RÉFÉRENCE + 1 point ET médiane >= RÉFÉRENCE ; p Holm < 0,05.
SEMAINE DU 23-27/11 (descriptif) : le panier réel 25-27/11 (journal du robot réel, prix relevés dans les états du pont
  publiés sur la branche) : pour chaque X, heure et prix de la coupure et résultat, contre le réel (+4,72 USC).
Rien en réel sans accord écrit de Baptiste ; si une variante est adoptée : démo `_opt` d'abord.
Usage : python3 banc_loto.py
"""
