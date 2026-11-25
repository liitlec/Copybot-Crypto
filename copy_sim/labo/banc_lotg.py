"""Banc Lot G (PRIORITES 25/11 22 h, demande ecrite de Baptiste) : ameliorer ce qu'on garde en v28.
CONTRAT FIGE ET POUSSE AVANT TOUT RESULTAT.

DONNEES (courtier, spread reel de chaque bougie ; stress = spread x 2) :
  M5  xau_m5_90k 08/2025 -> 11/2026 (15 mois) ; M15 xau_m15_50k sur la meme periode ; M1 xau_m1_90k (3 mois seulement,
  08 -> 11/2026 : exces_m1 jugee sur 3 mois, dit comme tel) ; H1 xau_h1_50k 08/2022 -> 11/2026 (4 ans, blocs
  B1 = 08/2022-09/2024 et B2 = 10/2024-11/2026). Heures serveur = Paris + 1 h.

PARTIE 1 — SORTIES DE bt_or_plus (mecanique du robot : entrees bt_or aux heures fixes, sens EMA 2 jours, renforts tous
  les 0,25 ATR de taille 1, 2, 3, 4, 5, 5 positions au plus, recul de 0,6667 ATR depuis le meilleur prix ; gain en R
  de la position de base : 1 R = perte d'une position de taille 1 au stop initial). M5 : span 576, heures bt_or M5 ;
  H1 : span 48, heures H1 du socle. Convention de BR.simule (achat a cloture + spread, sortie au niveau, vente
  declenchee par haut + spread). Variantes (11, grille fixee) :
    REF      bt_or_plus tel quel
    a35, a50 les 2 derniers renforts (positions 4 et 5) sortent seuls a un recul de 0,35 / 0,50 ATR depuis le meilleur
             prix (le reste du panier garde 0,6667) ; pas de remise.
    b36, b24 paliers : recul 0,6667 -> 0,5 -> 0,35 ATR quand le meilleur prix depasse +3 / +6 R (b36) ou +2 / +4 R (b24)
             depuis la 1re entree.
    c05, c10 chaque renfort (positions 2 a 5) encaisse a +0,5 / +1,0 ATR de son entree (ordre limite au niveau).
    d        stop au point mort du panier (prix moyen pondere) des que la 4e position est ouverte (3e renfort).
    e4, e8   sortie de tout le panier a la cloture qui repasse du mauvais cote de la moyenne mobile exponentielle de
             4 h / 8 h (M5 : 48 / 96 bougies ; H1 : 4 / 8).
    serre    temoin bt_or_serre (deja perdant en direct) : au-dela de +3 R, recul 0,5 R (= 0,333 ATR).
  Mesures par jeu : paniers, total R, pire baisse (cumul des paniers par jour de sortie), gain/pire baisse, Sharpe
  journalier (par jour de sortie, x racine 252), « gain rendu » moyen par panier = latent max (aux clotures) - gain
  ferme, « grands paniers coupes » = paniers de REF a >= +5 R dont le panier de meme ouverture de la variante fait moins
  de la moitie. Appariement des paniers par bougie d'ouverture.
  Tests : placebo = changement de signe au hasard des differences appariees variante - REF (2000 tirages) sur M5 et
  sur H1 ; reality check de White (bootstrap stationnaire par paniers, blocs moyens 5) sur les 10 variantes ->
  p corrige. Walk-forward (M5 6 -> 1 mois ; H1 12 -> 3 mois) : variante au meilleur gain/pire baisse d'apprentissage.
  RETENUE si : gain/pire baisse ET Sharpe > REF sur M5, sur H1 B1 ET sur H1 B2 ; p corrige < 0,05 sur un jeu et
  < 0,15 sur l'autre ; walk-forward >= REF sur les deux jeux ; encore > REF au spread double.

PARTIE 2 — REGLES COURTES (trades non chevauchants, decision a la cloture i, entree a l'ouverture i+1, sortie a la
  cloture i+h, stop eventuel en ATR jour 20 j touche dans la bougie = sortie au niveau ; gain en $ pour 0,01 lot).
  Regle telle quelle (REF) = celle du robot. Grilles (fixees) :
    elan_m15    : recul k {8, 12, 16} bougies x tenue h {8, 12, 16}                     (REF k 12, h 12)
    cassure_m15 : fourchette k {32, 48, 64} x tenue h {8, 12, 16}                         (REF 48, 12)
    exces_m5    : seuil z {2,5 ; 3 ; 3,5} x tenue h {2, 3, 6}, on suit                    (REF 3, 3)
    exces_m1    : seuil z {2,5 ; 3 ; 3,5} x tenue h {6, 12, 20}, on contre                (REF 3, 12)
    retour_court_ar (M15) : ecart z {2 ; 2,5 ; 3} x tenue {8, 12}, objectif milieu du range du jour, stop court
                  (extreme des 2 dernieres bougies + 0,5 $)                               (REF 2,5, 12)
    x stop {aucun, 0,5 ATR} (sauf retour_court_ar : son stop court) x heures {toutes, sans 10, 16, 17, 22 h serveur =
    9, 15-16, 21 h Paris} x lien bt_or {aucun ; tendances (elan, cassure, exces_m5) seulement dans le sens du panier
    bt_or_plus ouvert, contre-tendances (exces_m1, retour_court_ar) seulement a l'oppose ; sans panier ouvert : pas de
    trade}. Filtres heures et lien appliques a la liste de trades du reglage.
  Walk-forward glissant 6 -> 1 mois (reglage au meilleur t d'apprentissage ; M1 : 1 -> 1 mois). Placebo : memes
  reglages mais filtres heures et lien remplaces par un tri au hasard de meme taux de garde par mois (500 tirages) ;
  p = part des placebos au total walk-forward >= reel. Controle H1 4 ans (elan, cassure, retour) : le reglage le plus
  choisi, transpose en H1 (k et h divises par 4), contre la regle telle quelle transposee, en B1 et B2.
  RETENU si : walk-forward > REF dans chaque moitie de la periode de test ET placebo p < 0,05 ET > REF au spread
  double ET (regles M15) controle H1 > REF en B1 et B2.

PARTIE 3 — ENSEMBLE en $ (0,01 lot de base) : bt_or_plus REF + regles telles quelles, contre bt_or_plus (variante
  retenue s'il y en a) + regles en walk-forward ; a risque egal (meme ecart-type journalier) : total, pire baisse,
  part des semaines perdantes, sur les deux moities de la periode M5.
PARTIE 4 — variante demo `_opt` (v29) seulement pour ce qui est RETENU. Resultats en tete d'AVIS.md.
Usage : python3 banc_lotg.py
"""
