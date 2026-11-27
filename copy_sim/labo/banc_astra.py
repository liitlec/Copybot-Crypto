"""Banc Lot M-Astra (PRIORITES 27/11, « Lot M : trois règles d'Astra », étude astra_protocole/Etude_bt_or_plus_2711.pdf).
CONTRAT FIGÉ ET POUSSÉ AVANT TOUT RÉSULTAT (la réserve n'a jamais été calculée pour ces règles).

CADRE. Or M5 du courtier 06/08/2025 -> 11/11/2026 (90 000 bougies, banc_lotg.jeu_m5). Moteur = banc_lotm.simule k=0,
c.-à-d. bt_or_plus v4 réel (sens EMA 576, heures 03:05 08:00 08:30 12:00 15:45 16:00 16:30 serveur, renforts 1-2-3-4-5
tous les 0,25 ATR, recul 0,6667 ATR, paliers 0,5 / 0,35 ATR à +2 / +4 R, point mort dès 4 positions) ; il rend 388,25 R
sur la période principale, comme le banc d'Astra. Principal = paniers fermés 06/08/2025 -> 31/08/2026 ; RÉSERVE =
01/09 -> 11/11/2026, calculée en même temps que le reste et lue une seule fois ; spread réel puis doublé.

VARIANTES (6), règles du PDF d'Astra, p. 2-3 :
  Z15, Z25  « zone » : après un panier fermé en perte (USD < 0) avec UNE seule position, mémoriser par sens son prix
            initial P, son ATR A et l'heure de sortie ; pendant 6 h, à chaque heure d'entrée v4, sauter l'entrée du même
            sens si |prix d'exécution théorique - P| <= w x A (w = 0,15 / 0,25). Un saut ne prolonge pas les 6 h ; une
            nouvelle perte admissible remplace la précédente.
  R2, R3    « rejet » : dès 4 positions (pyramide virtuelle), ancre A0 = prix exécuté du dernier renfort ; ATR du panier.
            Achat : compter les clôtures M5 (bid) < A0 - 0,05 ATR ; vente : clôtures ask (clôture + spread) > A0 +
            0,05 ATR ; compteur remis à zéro si la clôture repasse le seuil ou si un renfort entre. À 2 / 3 clôtures
            consécutives, si le panier (positions réelles) est net positif à cette clôture, la jambe la plus récente
            sort à l'ouverture suivante (bid / ask), une fois par panier ; si la sortie v4 est touchée sur cette bougie
            (écart), la sortie v4 a priorité pour tout. On garde la pyramide v4 VIRTUELLE (jambe retirée comprise) pour
            les seuils, le prix moyen (donc le point mort) et la taille des renforts suivants, comme écrit dans le PDF
            (la fiche PRIORITES dit « point mort recalculé sur le reste » : le PDF, texte complet, fait foi).
  B33, B50  « budget de risque » (règle d'argent, jugée seulement en argent) : avant chaque entrée ou renfort bt_or_plus,
            D = equity - 0,66 x plus haut d'equity (USC, equity = solde + flottant) ; recul = somme, sur les jambes
            ouvertes bt_or_plus ET l'ordre envisagé, de lots x 100 x distance du prix de sortie courant (bid achat, ask
            vente ; prix d'exécution pour l'ordre envisagé) au stop de secours de son panier (le plus protecteur de
            meilleur - 0,8333 ATR et sortie v4 - 0,1667 ATR, comme bt_or.py) ; autorisé si recul <= q x D (q = 1/3,
            1/2). Entrée : base v3 descendue au pas de 0,01 jusqu'au premier volume admissible, sinon panier sauté ;
            base figée à l'ouverture. Renfort inabordable sauté pour toujours (la grille virtuelle continue ; le suivant
            est examiné à son tour). Règles courtes hors calcul du recul (positions courtes, sans stop de secours connu).

ARGENT (pour toutes : V4, V4 base 0,03, les 6 variantes). 20 000 USC ; base v3 = b x solde / 20 000 au pas 0,01 vers
  le bas, au plus b (b = 0,05 ; référence additionnelle b = 0,03), figée à l'ouverture du panier ; jambe = rang x base
  (<= 0,25 lot) ; au plus 10 positions bt_or_plus ; les 5 règles courtes (banc_lotl.courtes, 0,01 x solde / 20 000, au
  moins 0,01) ; USC = USD par lot x 100 x lots. Equity flottante marquée à chaque ordre, sortie et à chaque heure.
  Garde-fou du pont : plus d'ouverture ni de renfort jusqu'au lendemain si equity < 95 % de l'equity du début du jour.
  Arrêt définitif si equity <= 66 % du plus haut d'equity (tout est fermé à ce prix).
  Monte-Carlo : 2 000 parcours de 12 mois par blocs de semaines (longueur moyenne 4 semaines, comme le lot I) ; un panier
  appartient à la semaine de son ouverture et garde ses heures relatives ; MÊMES tirages de blocs pour toutes les
  variantes (apparié). Rapport : P(arrêt), equity finale médiane et 10e centile ; écart à V4 avec intervalle à 90 %
  (bootstrap des parcours, 1 000 tirages). Rejeu historique en argent du 06/08/2025 (principal puis réserve à la suite).

MESURES DE JUGEMENT.
  Z/R : en R, à risque égal (même écart-type journalier que V4 sur le principal, facteur appliqué partout) : gain÷pire
        baisse et Sharpe (principal), total et gain÷pire baisse (réserve), total au spread doublé (principal).
  B   : sur le rejeu historique en USC (sans remise à risque égal, la règle étant une règle de taille) : mêmes mesures
        sur les variations journalières d'equity, spread doublé compris.
PLACEBOS (graine figée 27112026), Holm sur les 6 :
  Z : mêmes conditions sauf la distance : on saute, au hasard, des entrées admissibles (même sens, dans les 6 h après une
      perte à une seule position), avec par (sens, heure d'entrée) la fréquence des sauts réels ; 200 tirages ;
      p = part des placebos au gain÷pire baisse (risque égal, principal) >= réel.
  R : même nombre attendu de jambes retirées, à des clôtures tirées au hasard parmi celles où le panier a >= 4 positions
      virtuelles, est net positif et n'a pas encore été allégé ; 200 tirages ; même statistique.
  B : à chaque ordre d'un parcours Monte-Carlo, réduction ou saut au hasard avec, par rang (et par heure pour les
      entrées), la fréquence et l'ampleur des réductions réelles ; 100 tirages de 400 parcours (mêmes 400 parcours que
      la variante réelle) ; p = part des placebos avec P(arrêt) <= réel.
ADOPTION (toutes les conditions) : P(arrêt) < V4 ET equity médiane >= V4 (Monte-Carlo, b = 0,05) ; gain÷pire baisse
  ET Sharpe > V4 (principal) ; total ET gain÷pire baisse > V4 (réserve) ; total > V4 au spread doublé ; p Holm < 0,05 ;
  jamais plus de 10 positions bt_or_plus.
RAPPORTÉ AUSSI : V4 à 0,03 ; les 5 plus grands paniers gagnants de V4 et ce qu'ils deviennent ; les paniers V4 de >= 4
  positions finis entre -0,25 et +0,25 R ; les ordres refusés (par rang, 5es positions refusées et gain V4 de leur
  panier témoin) ; H1 2022-24 / 2024-26 (gain÷pire baisse, Z et R) en information.
Si une variante est ADOPTÉE : préparer la v5 réelle SANS la publier ; accord écrit de Baptiste avant toute installation.
Usage : python3 banc_astra.py
"""
