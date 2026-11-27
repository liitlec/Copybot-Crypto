"""Banc Lot J (PRIORITES 27/11 9 h 15, demande écrite de Baptiste) : protéger les gains du panier bt_or_plus.
CONTRAT FIGÉ ET POUSSÉ AVANT TOUT RÉSULTAT.

DONNÉES : or M5 du courtier 06/08/2025 -> 11/11/2026 (spread réel, puis doublé).
  Période de jugement PRINCIPALE = paniers fermés du 06/08/2025 au 31/08/2026 ; RÉSERVE = 01/09/2026 -> 11/11/2026
  (vérification finale, regardée une seule fois). H1 2022-24 et 2024-26 en information seulement.
Mécanique bt_or_plus (banc_loth.simule : entrées bt_or, sens EMA 2 jours, renforts tous les 0,25 ATR, tailles
1-2-3-4-5, 5 positions). Seule la SORTIE change. Niveaux évalués avec l'état d'avant la bougie (meilleur prix, prix
moyen pondéré, gain maximal latent), touchés par le bas / haut (+ spread pour une vente) ; le plus protecteur s'applique.
VARIANTES (14 + témoin) :
  REF        sortie actuelle : recul de 0,6667 ATR depuis le meilleur prix ;
  pm2, pm3   stop au point mort (prix moyen + spread) dès 3 / 4 positions (après le 2e / 3e renfort) ;
  pal36, pal24, pal153  paliers : recul 0,5 puis 0,35 ATR quand le meilleur prix dépasse +3/+6, +2/+4, +1,5/+3 R
             depuis la 1re entrée ;
  pm3pal36, pm3pal24    combinaison point mort après le 3e renfort + paliers ;
  cl30_2, cl40_2, cl50_2, cl30_3, cl40_3, cl50_3  cliquet : une fois le gain maximal latent du panier >= 2 / 3 R,
             ne jamais rendre plus de 30 / 40 / 50 % de ce gain (stop au prix où le gain latent vaut 70 / 60 / 50 %
             du maximum, avec les positions du moment) ;
  moy3       dès 3 positions, stop au plus protecteur de la sortie actuelle et de « prix moyen - 0,25 ATR » (achat ;
             symétrique en vente) : le stop suiveur se cale sur le prix moyen du panier.
MESURES : total R et en USC (20 000 USC, mise v3 base 0,02), gain÷pire baisse et Sharpe journalier (risque égal),
  gain rendu moyen par panier (gain maximal latent - gain fermé), grands paniers (REF >= +5 R) coupés à moins de la
  moitié, résultat sur la réserve, P(arrêt -34 %) en 12 mois aux bases 0,02 / 0,03 / 0,05 (Monte-Carlo du lot I,
  bt_or_plus seul, 1 000 parcours, période principale + réserve).
TESTS : placebo = signes des différences appariées (paniers de même ouverture) tirés au hasard, 2 000 tirages, sur la
  période principale ; correction de Holm sur les 14 variantes (plus stricte que « 6 essais »).
RETENUE si : gain÷pire baisse ET Sharpe > REF sur la période principale ; total ET gain÷pire baisse > REF sur la
  réserve ; p Holm < 0,05 ; total > REF au spread doublé (principale) ; P(arrêt) à 0,02 pas plus de 2 points au-dessus
  de REF.
PANIERS RÉELS / DÉMO DEPUIS LE 18/11 (descriptif, aucune décision dessus) : les paniers bt_or_plus des journaux (démo
  bt_or_plus_opt et réel), entrées réelles reprises du journal, rejoués sur l'or à terme GC=F 5 min (Yahoo, seule
  source après le 11/11), décalé de l'écart moyen observé entre les prix d'entrée réels et GC=F ; le panier réel
  ouvert du 27/11 est complété jusqu'au dernier prix publié par le pont réel. Approximation dite comme telle.
Si une variante est RETENUE : préparer le robot réel v4 (mode auto) SANS le publier (VERSION inchangée) ; Baptiste décide.
Usage : python3 banc_lotj.py
"""
