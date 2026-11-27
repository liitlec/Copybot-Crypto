"""Banc « Ajout au lot M » (PRIORITES 27/11 12 h 50, Baptiste : « si ça redescend, au moins récupérer un peu de gain et
pas être à zéro »). CONTRAT FIGÉ ET POUSSÉ AVANT TOUT RÉSULTAT DE CES VARIANTES.

CADRE ET ÉPREUVES : ceux de banc_lotm_astra.py (contrat 4affbbf), dont on réutilise le moteur, l'argent et le
Monte-Carlo apparié (mêmes 2 000 tirages de blocs de semaines, 20 000 USC, base v3 0,05, règles courtes, garde-fou
-5 %/jour, arrêt -34 % sur equity flottante). Référence V4 = sortie actuelle (point mort = prix moyen + spread dès 4
positions, paliers 0,5 / 0,35 ATR à +2 / +4 R).
VARIANTES (10) — seul change le PLANCHER dès 4 positions (le plus protecteur avec la sortie v4 s'applique) :
  F10, F20, F30 : plancher = prix moyen + spread + 0,10 / 0,20 / 0,30 ATR (au-dessous en vente) au lieu de prix
                  moyen + spread (k = 0,10 avait été vu au lot M « point mort + k », non retenu : refait ici en argent) ;
  G20, G30      : en plus du point mort v4, une fois le gain latent maximal du panier >= 3 R (R = 0,6667 ATR x 1 base,
                  gain calculé à la clôture, jambes réelles), plancher = prix où le gain latent vaut 20 / 30 % de ce
                  maximum (prix moyen réel + gain gardé / taille) ;
  F10R3, F20R3, F30R3, G20R3, G30R3 : la même chose + la règle « rejet » d'Astra à 3 clôtures (R3, celle qu'Astra
                  classe devant R2 ; prix moyen virtuel pour le point mort comme dans banc_lotm_astra, le gain gardé de
                  G se calcule sur les jambes réelles).
MESURES : comme banc_lotm_astra (R à risque égal : gain÷pire baisse et Sharpe principal, total et gain÷pire baisse
  réserve, total au spread doublé ; argent : P(arrêt), médiane, 10e centile, écarts à V4 avec IC 90 %).
  En plus (demandé) : paniers qui RETOMBENT = paniers V4 de >= 4 positions dont le gain latent maximal a atteint >= 2 R
  et qui finissent à <= +0,5 R (principal) : nombre, gain moyen V4 et gain moyen de la variante sur les mêmes paniers ;
  GRANDS PANIERS COUPÉS TROP TÔT = paniers V4 >= +5 R que la variante finit à moins de la moitié ; 5 plus grands.
PLACEBO : signes des différences appariées (paniers de même ouverture) tirés au hasard, 2 000 tirages, principal (comme
  les lots J/K/M de sortie) ; p = part des placebos à somme >= réelle. Holm sur les 10.
ADOPTION : celle de banc_lotm_astra (moins d'arrêts ET médiane >= V4 ; gain÷pire baisse ET Sharpe > V4 principal ;
  total ET gain÷pire baisse > V4 réserve ; > V4 spread doublé ; p Holm < 0,05).
PANIER RÉEL DU 27/11 (descriptif) : 0,02 @ 3 563,54 / 0,04 @ 3 598,58 / 0,06 @ 3 648,08 / 0,08 @ 3 677,30, meilleur
  ≈ 3 685 $, ATR ≈ 110,19 $ (0,6667 ATR = 73,46 $) : pour chaque variante, niveau du plancher et gain en $ gardé si le
  prix redescend jusqu'à lui (et, avec R3, si la 4e jambe sort à 3 671,79 $).
Si une variante est ADOPTÉE : préparer la v5 réelle SANS la publier ; accord écrit de Baptiste avant toute installation.
Usage : python3 banc_lotm_plancher.py
"""
