"""Banc Lot E (PRIORITES 23/11 12 h) : verifier l'etude d'Astra « type de seance sur l'or » (copy_sim/labo/astra_seances/).
CONTRAT FIGE ET POUSSE AVANT LES RESULTATS DES POINTS 2 A 5 (seules l'inspection des donnees et l'alignement des heures,
ci-dessous, ont ete faits avant).

CONSTATS D'INSPECTION (avant contrat) :
  - Source H4 GitHub (tohaitrieu GOLD-H4) : vraies bougies 4 h seulement a partir de 06/2013 (avant : 1 bougie par jour).
    Donc ~12,7 ans de H4 (06/2013 -> 06/02/2026), PAS 20 ans.
  - Fuseau : heure de la source = heure serveur STARTRADER - 3 h, ete comme hiver (ecart median des clotures H4 contre
    nos H1 regroupees : 0,2 pb a -3 h, >= 7 pb sinon ; seules les semaines de mars ou les changements d'heure US / Europe
    different restent a 1,6 pb). Le « 9 h » d'Astra = 12:00 serveur = 11 h a Paris (ete comme hiver).

POINT 1 — reproduction : ses scripts, sans modification, dans une copie du dossier (detecter, cassure, verifier,
  calendrier, figer) ; on compare aux tableaux de Resultats_pour_Claude.md (precision « calme », FOMC 0/76, cassure).

POINTS 2-3 — robots du labo, or H1 du courtier 01/08/2022 -> 11/11/2026, decision a 12:00 serveur (son « 9 h ») :
  Drapeaux ecrits chaque jour : FOMC (date de decision programmee, donnees/fomc.csv) ; alerte calme (score_matin.score
  sur nos H1 decalees de -3 h et regroupees en H4 de la source, parametres.json fige, seuil 0,2617) ; cassure
  (sortie « hausse » / « baisse » de score_matin) ; « indetermine » sinon.
  Familles (inchangees, regime_socle._fam_trades) : bt_or (bt_or_h1), tendance = cassure_h1, retour = retour_h1. P&L par
  jour d'entree, en R ; chaque famille mise a ecart-type journalier 1 sur la chauffe 08/2022-01/2023 (risque egal).
  Couts : spread reel x 1,5 (spread + provision de glissement 50 %, comme banc_astra) ; stress spread x 3.
  Bases : bt_or seul, retour seul, 50/50 = 0,5 bt_or + 0,5 retour.
  Regles (12) : sur les jours a drapeau X (FOMC, calme, cassure), suspendre UNE famille pour les entrees a partir de
  12:00 serveur ce jour-la ; les positions ouvertes avant 12:00 sont gardees et suivies a part ; jours sans drapeau
  inchanges. 50/50 : X x {bt_or, retour} = 6 ; bt_or seul : X -> bt_or coupe = 3 ; retour seul : X -> retour coupe = 3.
  Temoin obligatoire : coupure aleatoire, meme nombre de jours coupes dans chaque mois, meme famille, 2000 tirages ;
  p = part des tirages au gain >= gain reel. Rapporte : nombre de signaux, gain contre la base, pire baisse, part des
  semaines perdantes, esperance par semaine et IC 95 % (bootstrap par semaines). Blocs B1 = 08/2022-09/2024,
  B2 = 10/2024-11/2026. Correction : Holm sur les 12 p du temoin.
  RETENU si : bat sa base en B1 ET B2 ET p temoin corrige (Holm) < 0,05 ET bat encore sa base au stress spread x 3.

POINT 4 — le « jour » du lot D sur la source H4 (06/2013 -> 02/2026) : jour serveur = bougies source 21 h (veille), 1, 5,
  9, 13, 17 ; decisions a 7 h Paris (apres la bougie source 1 h), 11 h (apres 5 h) et 15 h (apres 9 h), les heures du
  quadrillage H4 les plus proches de 9 h / 11 h / 14 h. Etiquette = efficacite du reste du jour >= mediane de
  l'apprentissage. Memes 16 variables et memes modeles que banc_lotd_jour (annonces : FOMC + premier vendredi du mois ;
  CPI non disponible avant 2022 ; VIX et GVZ FRED, decalage de 2 jours). Walk-forward croissant (>= 250 jours).
  Argent : bt_or rejoue sur H4 (banc_bt_regulier.simule, span 12, entrees aux bougies source 1, 5, 9, 13 h, spread
  0,51 pb du prix), valide si correlation des R mensuels avec le vrai bt_or H1 (08/2022 -> 02/2026) >= 0,6 et meme
  signe en B1 et B2 ; sinon la partie argent est indicative et seule l'AUC compte.
  RETENU si : borne basse de l'IC 95 % de l'AUC > 0,5 ET (bt_or H4 valide ET bat « toujours 1 » a risque egal en
  2014-2019 ET 2020-2026 ET placebo p < 0,05 ET SPA p < 0,05 sur les 6 regles).

POINT 5 — variante demo `_opt` hors totaux seulement si une regle est RETENUE.
Usage : python3 banc_lote.py
"""
