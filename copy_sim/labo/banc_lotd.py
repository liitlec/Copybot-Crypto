"""Banc Lot D (PRIORITES 23/11 11 h 15) : « les prochains MOIS de l'or seront-ils en tendance ? » sur historique long.
CONTRAT FIGE ET POUSSE AVANT TOUT RESULTAT (rien ci-dessous ne sera change apres le premier lancement ; tout ecart
eventuel sera ecrit dans AVIS.md comme ecart au contrat).

DONNEES (publiques, sans cle) :
  - GLD journalier Yahoo (OHLC reels, 18/11/2004 -> 11/2026) = source PRINCIPALE du mime. GC=F journalier Yahoo
    (08/2000 ->) n'a pas de haut/bas avant 2008 (45 % de bougies plates) : seulement en CONTROLE, de 2009 a la fin.
  - FRED : GVZCLS (2008+), DFII10 (2003+), dollar DTWEXM (jusqu'a 12/2005) puis DTWEXBGS (2006+) : seules les
    variations sur 3 mois servent, calculees dans chaque serie (pas de raccord de niveaux). Valeur connue en fin de
    mois = derniere observation datee au plus tard 2 jours avant le dernier jour de bourse du mois (dollar : 10 jours).
  - Vrai bt_or : banc_bt_regulier.simule sur or H1 du courtier (xau_h1_50k, span 48, heures H1 du socle), 08/2022 -> fin.

POINT 1 — MIME JOURNALIER DE bt_or (copie de la mecanique, aucun reglage nouveau) :
  sens = cloture d'hier contre EMA(span 2) des clotures jusqu'a hier ; a l'ouverture du jour, ouvrir un panier dans ce
  sens s'il n'y en a pas deja un de ce cote (les deux cotes peuvent coexister, comme bt_or) ; ATR = moyenne 20 j du
  vrai range, connue hier ; renforts tous les 0,25 ATR dans le sens du prix, 3 positions au plus ; sortie du panier sur
  recul de 0,6667 ATR depuis le meilleur prix. Chemin dans la bougie : O -> bas -> haut -> C si C >= O, sinon
  O -> haut -> bas -> C (convention usuelle) ; un renfort et le stop ne sont jamais declenches sur le meme segment
  dans le sens favorable. Cout = 0,51 pb du prix par entree (spread median de l'or chez le courtier) ; x2 en test.
  Gain d'un panier en R (1 R = perte d'une position au stop initial), rattache au mois d'OUVERTURE.
  VALIDATION (seuil fixe) : sur 08/2022 -> 11/2026, correlation de Pearson des R mensuels mime GLD / vrai bt_or H1
  (rattache aussi au mois d'ouverture) >= 0,6 ET meme signe du total sur B1 = 08/2022-09/2024 et B2 = 10/2024-11/2026.
  Si le mime echoue, rien d'autre ne compte (les points 2-3 sont alors donnes a titre indicatif seulement).
  Pas de variante du mime essayee pour passer le seuil.

POINT 2 — FILTRES LENTS, decides au dernier jour de bourse du mois M avec ce qui est connu, appliques aux paniers
OUVERTS en M+1. N = 18 filtres, chacun donne un score ; mise = 0 / 1 / 2 selon le tercile du score parmi TOUS les
scores des mois precedents (fenetre croissante, 24 mois au moins : sinon mise 1). Sauf F18 (binaire 2 / 0).
  F1-F3   momentum de l'or 3 / 6 / 12 mois (rendement, signe compris)
  F4-F6   |momentum| 3 / 6 / 12 mois divise par la volatilite journaliere 12 mois x racine(jours)  (force de tendance)
  F7      prix / moyenne 200 jours - 1 (signe compris)      F8   |prix / moyenne 200 j - 1|
  F9-F10  efficacite de Kaufman 60 j / 120 j                F11  |pente de regression du log-prix sur 120 j| / vol
  F12     GVZ (niveau)                                      F13  GVZ, variation sur 3 mois
  F14     - variation du taux reel 10 ans sur 3 mois         F15  - variation du dollar sur 3 mois (en %)
  F16-F17 R du mime sur le dernier mois / les 3 derniers mois
  F18     courbe de gains du mime au-dessus de sa moyenne mobile 6 mois -> 2, sinon 0
  F12-F13 commencent quand GVZ a 24 mois d'historique de score ; avant, mise 1.
  WF = choix en walk-forward : chaque mois, le filtre au meilleur rapport moyenne/ecart-type passe (fenetre croissante,
  >= 36 mois de resultats) ; c'est la serie « une seule regle choisie honnetement ».

POINT 3 — JUGEMENT. Serie d'un filtre = mise x R du panier. Reference = « toujours 1 ». Evaluation 01/2007 -> 11/2026.
  Risque egal : chaque serie mensuelle est mise a l'ecart-type mensuel de « toujours 1 » sur tout l'echantillon
  (equivalent a comparer les rapports moyenne/ecart-type) ; totaux montres a risque egal.
  - SPA de Hansen (et White) sur les 18 filtres + WF : differences mensuelles contre « toujours 1 » a risque egal,
    bootstrap stationnaire blocs moyens 6 mois, 2000 tirages -> p corrige.
  - Placebo : la serie de mises du filtre decalee circulairement de 6 a 18 mois (tirage uniforme), 1000 tirages ;
    p = part des placebos au rapport moyenne/ecart-type >= reel.
  - Decennies : D1 = 2007-2016, D2 = 2017-2026.
  - 2022-2026 : memes mises appliquees aux paniers du VRAI bt_or H1 (mois d'ouverture), blocs B1 et B2.
  RETENU si : mime valide ET p SPA < 0,05 ET placebo p < 0,05 ET bat « toujours 1 » a risque egal en D1 ET en D2
  ET sur le vrai bt_or en B1 ET en B2 ET bat encore « toujours 1 » sur tout 2007-2026 au cout double.

POINT 4 — ECHELLE DE TEMPS : regime « tendance » = mois ou la somme glissante sur 6 mois du mime est > 0 ; on compte
  les regimes (suites de meme etat de 3 mois ou plus) sur 2007-2026, sur 2022-2026 et sur les 15 derniers mois ;
  autocorrelation des R mensuels du mime (retards 1 a 3) ; puissance : ecart de rapport moyenne/ecart-type annuel
  detectable a 2 ecarts-types avec n mois (2 x racine(12 / n)), et avec n regimes.

POINT 5 — variante demo bt_or_filtre_opt seulement si un filtre est RETENU. Sinon, dire la meilleure piste restante.
Usage : python3 banc_lotd.py   (ecrit donnees/lotd.csv)
"""
