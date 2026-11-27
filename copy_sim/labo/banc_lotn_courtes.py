"""Banc « Ajout au lot N » (PRIORITES 27/11 13 h 40, Baptiste : améliorer les règles courtes pour plus de gain).
CONTRAT FIGÉ ET POUSSÉ AVANT TOUT CALCUL DE CES VARIANTES. Même cadre et même jugement que banc_lotn.py.

RÈGLES (robot réel, réglages actuels de banc_lotg.REGLES, données du courtier 06/08/2025 -> 11/11/2026) :
  elan_m15 (12, tenue 12 M15), cassure_m15 (48, 12 M15), exces_m5 (3, 3 M5), exces_m1 (3, 12 M1),
  retour_court_ar (2,5, 12 M15, avec son objectif / stop propres). REF = chaque règle telle quelle (banc_lotg.joue),
  0,01 lot, une position à la fois par règle. PRINCIPAL = trades entrés 06/08/2025 -> 31/08/2026 ; RÉSERVE =
  01/09 -> 11/11/2026 ; spread réel puis doublé. Le lot G (seuils, tenues, stop 0,5 ATR, heures, sens du panier
  bt_or) n'est PAS refait.
VARIANTES PAR RÈGLE (8 x 5 règles = 40), seule la partie nommée change :
  Sorties, au lieu de la tenue fixe (tenue maximale = 4 x la tenue actuelle ; stop de sécurité 1 ATR jour sauf TS ;
  pour retour_court_ar on garde en plus son stop d'extrême) :
    O05, O10, O15  objectif à +0,5 / +1 / +1,5 ATR jour ;
    TS             stop suiveur à 0,5 ATR jour du meilleur prix (haut / bas) depuis l'entrée ;
    ES             essoufflement : 1re clôture contre le sens sur l'unité de la règle (M15 pour les règles M15, M5
                   pour exces_m5 et exces_m1 — pour celle-ci, clôtures M5 reconstruites des M1) ;
    PM             tenue actuelle, mais stop ramené au prix d'entrée dès que le meilleur prix a fait +0,5 ATR.
  F    filtre du sens (EMA 576 M5, le sens de bt_or) avec la sortie actuelle : tendance courte (elan, cassure,
       exces_m5) seulement si clôture M5 du côté du sens ; contre-tendance (exces_m1, retour_court_ar) seulement si
       l'entrée est DANS le sens (achat de repli en tendance haussière, vente de rebond en baissière).
  Q    taille selon la qualité du signal, sortie actuelle : 0,02 lot si la force du signal dépasse la médiane des
       200 signaux PRÉCÉDENTS de la règle, sinon 0,01 (force : elan = |rendement sur k| / écart-type glissant 100 de
       ce rendement ; cassure = dépassement du canal / ATR ; exces = |z| ; retour = |c - m| / (k x écart-type)).
MESURES : par variante, principal / réserve / spread doublé : trades, total $, $ par trade ; écart à REF ; et pour
  l'ensemble avec bt_or_plus v4 : la règle remplacée par sa variante dans les règles courtes du Monte-Carlo apparié de
  banc_lotm_astra (2 000 parcours, base 0,05) -> P(arrêt -34 %) et equity médiane.
PLACEBOS (graine 2711_1340, 2 000 tirages ; statistique = écart de total à REF sur le principal) :
  sorties : signes des différences appariées (trades de même signal) tirés au hasard ;
  F : autant de trades retirés au hasard (même part) ; Q : autant de trades doublés au hasard (même nombre).
  Correction de Holm sur les 40.
« TIENT » si : total > REF au principal, au spread doublé ET sur la réserve ; p Holm < 0,05 ; P(arrêt) pas plus de
  1 point au-dessus de v4 + REF. « PRESQUE » : tout sauf Holm (p brut < 0,05). Ce qui tient -> démo `_opt` d'abord
  (version démo suivante), JAMAIS en réel sans accord écrit de Baptiste.
Usage : python3 banc_lotn_courtes.py
"""
