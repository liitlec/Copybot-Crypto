"""Banc Lot D, points 6-8 (ajout de Baptiste 23/11 11 h 25) : « la journee qui commence sera-t-elle une journee de
tendance ou d'aller-retour ? », decide a 9 h Paris puis mis a jour a 11 h et 14 h.
CONTRAT FIGE ET POUSSE AVANT TOUT RESULTAT.

ECART FORCE AU POINT 6 : l'historique intrajour long (Dukascopy, HistData) est BLOQUE par la politique reseau de
l'environnement cloud (connexions refusees le 23/11). On travaille donc sur l'or H1 du courtier (xau_h1_50k,
08/2022 -> 11/2026, ~1 100 jours). Pas de « 15-20 ans » : le resultat sera dit indicatif sur cette duree.

JOUR = jour serveur (New York + 7 h), lundi-vendredi. Heure serveur = heure de Paris + 1 h. Decisions :
  9 h Paris = apres les bougies H1 serveur 00..09 (fermees a 10:00 serveur) ; 11 h = 00..11 ; 14 h = 00..14.
ETIQUETTE (point 6) : efficacite du jour = |cloture - ouverture| / (haut - bas) ; « tendance » = efficacite du RESTE
  du jour (de l'heure de decision a la fin) >= mediane des jours d'apprentissage. Resultat en argent = R des paniers
  bt_or (banc_bt_regulier.simule, reglage H1 du socle, spread reel) OUVERTS ce jour a/apres l'heure de decision
  (9 h : entrees 11, 14, 15 serveur ; 11 h : 14, 15 ; 14 h : 15). Les paniers ouverts avant restent a mise 1.
  Controle du point 6 : etiquettes du jour calculees aussi sur l'or M5 du courtier (xau_m5_90k) sur la periode commune ;
  accord des etiquettes H1 / M5 (part des jours de meme etiquette) donne en clair.
INDICES CONNUS A LA DECISION (point 7) : amplitude / ATR20 et sens / efficacite de la seance depuis minuit serveur
  (Asie + debut d'Europe) ; ecart d'ouverture (ouverture du jour - cloture de la veille) / ATR20 ; efficacite des 1 et
  5 jours precedents ; compression = amplitude d'hier / ATR20 ; jour de la semaine (4 indicatrices) ; jour d'annonce
  (NFP, CPI, FOMC : listes de banc_regime_p6) ; position dans la tendance du mois (prix - ouverture du mois) / ATR20 et
  |idem| ; VIX connu (S.vix_connu) et GVZ connu (decalage du socle, 2 jours). 15 variables.
MODELES : logistique (variables centrees-reduites sur l'apprentissage, L2, C = 1) et arbre de profondeur 2 (feuilles
  >= 50 jours). Walk-forward croissant : apprentissage >= 250 jours, re-estimation chaque mois, prevision du mois
  suivant. Taux de base = toujours la frequence d'apprentissage (AUC 0,5).
MISE : probabilite prevue dans le tiers haut des previsions de l'apprentissage -> 2 ; tiers bas -> 0 ; sinon 1 ;
  appliquee aux paniers bt_or ouverts apres la decision ce jour-la. 6 regles = 2 modeles x 3 heures.
JUGEMENT : reference « toujours 1 » ; risque egal (comparaison des rapports moyenne/ecart-type des P&L JOURNALIERS) ;
  blocs B1 = debut de prevision -> 09/2024, B2 = 10/2024 -> fin. AUC hors echantillon (IC bootstrap 95 %).
  SPA de Hansen sur les 6 regles (bootstrap stationnaire, blocs moyens 5 jours, 2000 tirages). Placebo : previsions
  melangees entre jours d'un meme mois, 1000 tirages. Spread double (simule refait avec sp x 2).
  RETENU si : AUC > 0,5 (borne basse IC > 0,5) ET bat « toujours 1 » a risque egal en B1 ET B2 ET p SPA < 0,05 ET
  placebo p < 0,05 ET bat encore au spread double.
VALEUR D'UNE BONNE PREVISION : prevision synthetique juste avec probabilite q du signe du R apres decision (mise 2 si
  « bon jour » prevu, 0 sinon) ; gain a risque egal contre « toujours 1 » pour q = 0,50 ... 0,70 ; precision minimale
  qui paie (moyenne de 200 tirages par q). Comparee a la precision reelle des modeles.
POINT 8 : bilan jour / mois. Variante demo seulement si une regle est RETENUE.
Usage : python3 banc_lotd_jour.py   (ecrit donnees/lotd_jour.csv)
"""
