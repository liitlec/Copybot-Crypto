"""Banc Lot N (PRIORITES 27/11 13 h, demande écrite de Baptiste) : d'AUTRES stratégies à greffer à bt_or_plus.
CONTRAT FIGÉ ET POUSSÉ AVANT TOUT CALCUL DE CES CANDIDATS.

DONNÉES : or M5 du courtier xau_m5_90k (06/08/2025 -> 11/11/2026, spread réel par bougie). Heure serveur = New York
+ 7 h ; Londres, Shanghai et New York se déduisent par les fuseaux (changements d'heure compris). M15 = M5 regroupées.
PRINCIPAL = trades ENTRÉS du 06/08/2025 au 31/08/2026 ; RÉSERVE = 01/09 -> 11/11/2026 (gelée, lue une fois).
EXÉCUTION commune : entrée à l'OUVERTURE de la bougie qui suit le signal (achat à ouverture + spread, vente à
ouverture) ; stop / objectif vérifiés sur haut / bas (+ spread pour une vente) des bougies suivantes, le stop d'abord
si les deux sont touchés ; sortie au temps à la clôture (achat au bid, vente à l'ask). Gain en $ par once = USC à 0,01
lot cent ; 0,01 lot par trade. Puis spread doublé.

CANDIDATS (10 ; grille fixée ici, aucun autre réglage) :
 Jumeau « début de mouvement » sorti sur ESSOUFFLEMENT (demande 1) : entre en même temps, au même prix et dans le
 même sens que la 1re position de chaque panier bt_or_plus v4 (banc_lotm_astra.simule) ; stop de sécurité 0,6667 ATR
 jour sous l'entrée ; sortie au premier des signaux suivants, ou au plus tard à la sortie du panier bt_or_plus :
  J1 1re clôture M15 de l'autre côté de l'EMA 20 M15 ;
  J2 1re bougie M15 de rejet : mèche contre le sens >= 50 % de sa hauteur ET clôture dans la moitié défavorable ;
  J3 ralentissement : 1re clôture M15 sous le plus bas de la M15 précédente (au-dessus du plus haut en vente) une fois
     le trade en gain d'au moins 0,25 ATR (avant : stop de sécurité seulement) ;
  J4 objectif fixe à +1 ATR jour.
 Recherche large (demande 2 ; sources dans AVIS.md) :
  C1 « momentum de fin de Comex » (Gao-Han-Li-Zhou 2018 ; Baltussen-Da-Lammers-Martens 2021, 60 contrats à terme) :
     signe du rendement de 18 h 00 NY (veille, ouverture Globex) à 13 h 00 NY ; trade dans ce sens de 13 h 00 à 13 h 30
     NY (clôture Comex), lundi-vendredi.
  C2 « ouverture de Shanghai » (momentum de première demi-heure, littérature sur les contrats chinois or/argent) :
     signe du rendement 9 h 00 -> 9 h 30 heure de Pékin ; trade dans ce sens de 9 h 30 à 11 h 30 Pékin.
  C3 « trou du week-end » : écart entre la 1re ouverture de la semaine et la dernière clôture du vendredi >= 0,10 ATR
     jour ; à la 3e bougie, position contre l'écart, objectif = clôture du vendredi, stop = 1 ATR, au plus 12 h.
  C4 « retour en séance asiatique » (marché mince, Boyarchenko et al.) : de 1 h 00 à 6 h 00 Londres, clôture M5 hors
     EMA 20 M5 ± 2 écarts-types (20 bougies) -> position contre l'excès ; sortie au retour sur l'EMA 20, stop 0,5 ATR
     jour, au plus 6 h 30 Londres ; un trade à la fois.
  C5 « cassure de l'ouverture Comex » : fourchette 8 h 20 -> 8 h 50 NY ; 1re clôture M5 hors fourchette avant 11 h 00
     NY -> dans ce sens, stop de l'autre côté de la fourchette, sortie 13 h 30 NY ; un trade par jour.
  C6 « cassure de la séance asiatique à Londres » (version SUIVIE ; la version contrariante a échoué le 16/11) :
     fourchette 0 h 00 -> 7 h 00 Londres ; 1re clôture M5 hors fourchette entre 7 h 00 et 12 h 00 Londres -> dans ce
     sens, stop au milieu de la fourchette, sortie 16 h 30 Londres ; un trade par jour.
 Écartés d'avance (déjà testés sans succès, AVIS « Tout ce qui a été testé ») : nuit contre jour / saisonnalités
 horaires, ratio or/argent, bt_or sur l'argent, suite après annonces CPI/emploi, momentum croisé, COT, autres marchés
 qui annoncent l'or, compression-cassure, Silver Bullet. Pré-FOMC : trop peu de réunions sur 15 mois (non testé).

MESURES (principal, réserve, spread doublé) : trades, total $ (0,01 lot), $ par trade, t de Student, part gagnante ;
  corrélation HEBDOMADAIRE avec bt_or_plus v4 (USD par lot de base) et gain moyen du candidat les semaines où bt_or_plus
  perd ; effet sur le compte réel : candidat ajouté aux règles courtes (0,01 x solde / 20 000, au moins 0,01) dans le
  Monte-Carlo apparié de banc_lotm_astra (2 000 parcours, v4 base 0,05) -> P(arrêt -34 %) et equity médiane.
  Jumeaux : en plus, « miser plus sur bt_or » : à écart-type journalier égal (principal, USC), gain÷pire baisse de
  bt_or_plus (base 0,05) + jumeau contre bt_or_plus seul agrandi.
PLACEBOS (graine 2711_13, 2 000 tirages ; p = part >= réel, total du principal) : C1-C6 : mêmes trades, sens tiré au
  hasard ; J1-J4 : mêmes entrées, durées de détention des trades permutées au hasard (sortie à la clôture M5 après la
  durée tirée, bornée par le stop et la sortie du panier). Correction de Holm sur les 10.
« TIENT » si : total principal > 0 au spread réel ET doublé ; total réserve > 0 ; p Holm < 0,05 ; P(arrêt) pas plus
  de 1 point au-dessus de v4 ; jumeaux : en plus, battre « miser plus sur bt_or ». « PRESQUE » : tout sauf Holm (p brut
  < 0,05). Ce qui tient -> variante démo `_opt` hors totaux (version démo suivante), JAMAIS en réel sans accord écrit.
Usage : python3 banc_lotn.py
"""
