"""Banc Astra (PRIORITES 23/11 10 h 20, texte astra_regimes_2311.md) : derniere experience bornee du detecteur de regime.
CONTRAT FIXE AVANT TOUT CALCUL (commit separe, avant le premier lancement) :

Donnees : or du courtier, M5 xau_m5_90k (08/2025 -> 11/2026) et M15 xau_m15_50k sur la meme periode ; spread reel
(colonne sp, prix en $/once) ; heure serveur = New York + 7 h (Paris = serveur - 1 h). Controle 4 ans (oracle et veto
seulement) : or H1 08/2022 -> 11/2026.
Familles (celles du labo, banc_famille, SANS la pause au calme v11 pour ne pas melanger deux filtres) :
  TENDANCE = elan_m15 + cassure_m15 ; RETOUR = fcassure_m5 + contre_exces_m5 ; une position a la fois par regle,
  decision a la cloture d'une bougie, entree a l'ouverture suivante (banc_or.trades), cout = spread reel (x2 = double).
  Controle H1 : TENDANCE = cassure_h1 (12 h, tenue 3 h) ; RETOUR = contre un exces H1 (rendement > 2,5 ecarts-types
  des 100 H1 precedentes, tenue 2 h). (cassure/retour du socle sont des miroirs, inutilisables ici.)
Unite R : budget de risque global a la decision, commun aux variantes. Une entree prise avec tout le budget = poids 1 ;
  1 R = ecart-type du gain d'un trade de la famille sur la chauffe 08-10/2025 (H1 : 08-10/2022). Allocations des
  NOUVELLES entrees decidees dans l'heure [H, H+1) : 50/50 = (0,5 ; 0,5) ; tendance seule = (1 ; 0) ;
  retour seul = (0 ; 1) ; veto = (0 ; 0). Les positions deja ouvertes suivent leurs sorties (le gain d'un trade va a
  l'heure de sa decision).
1. Oracle horaire : a chaque heure, meilleur des trois choix connu apres coup (tendance seule, retour seul, 50/50).
   Gain de l'oracle sur le 50/50 = borne haute. Seuil d'arret fixe : si la borne haute est < 0,05 R par heure qui
   change l'allocation, OU si les 10 meilleures heures font plus de 50 % du gain, la recherche du detecteur est jugee
   sans objet. On liste les 10 heures qui font le plus de gain.
2. Veto de cout : A = mediane, sur les 60 seances anterieures (meme heure serveur), de l'amplitude haut-bas de l'heure
   [H, H+1) ; c = cout aller-retour executable = 1,5 x mediane du spread des bougies M5 de l'heure precedente
   (spread une fois + provision de glissement 50 %). Si A/c < 4 : veto pendant l'heure, sinon 50/50.
   Placebos : (a) autant d'heures suspendues tirees au hasard dans les memes cases (heure serveur x mois), 1 000 tirages ;
   (b) reduction permanente du risque donnant la meme exposition moyenne (50/50 x part des trades gardes).
3. Prolongement apres retournement (changements directionnels) : par seance serveur, c = mediane sur les 20 seances
   anterieures du cout aller-retour journalier (1,5 x mediane du spread M5) ; delta = max(4 c ; 0,15 x ATR journalier
   14 seances terminees) ; clotures M5 ; inversion confirmee au premier recul de delta depuis l'extreme de cloture ;
   prolongement d'une jambe terminee = (extreme - prix de confirmation) / delta. A chaque heure pleine, mediane des 3
   derniers prolongements termines dans la seance : >= 1 -> tendance seule ; <= 0,25 -> retour seul ; sinon (ou moins
   de 3 jambes) 50/50. Placebo : 1 000 permutations des medianes entre seances, a heure egale et meme tiers de
   volatilite (delta), en gardant les heures ou 3 jambes existaient. Heure du 1er signal publiee (Paris).
4. Tenue du prix apres annonce (CPI, emploi US, 8 h 30 New York = 15:30 serveur ; dates de banc_annonces_levier) :
   P0 = cloture de la bougie 15:25 ; J = P5 - P0 (cloture 15:30) ; ignore si |J| < 2 x mediane |variation| de la bougie
   15:30 sur les 60 seances anterieures ; F = (P15 - P0) / J (cloture de la bougie 15:40). F >= 0,75 -> tendance dans le
   sens du choc ; F <= 0,25 et P0 non traverse entre 15:30 et 15:45 -> retour vers P0 ; sinon 50/50 ; expire a +60 min.
   Mesure : (a) poids sur les familles (tendance seulement dans le sens du choc, retour seulement vers P0) dans
   [15:45, 16:30) ; (b) trade direct de l'autorisation : entree a l'ouverture 15:45, sortie a la cloture 16:25
   (bougie de 16:25), spread reel. Placebo : faux evenements a 15:30 les autres jours de meme jour de semaine passant
   le meme seuil |J|, 1 000 tirages de meme taille. Exploratoire (peu d'evenements).
Retard en argent (regles 3 et 4) : a chaque alerte, heure, premier prix executable, gain deja passe (famille favorisee
  moins 50/50, du debut de seance a l'alerte) et gain encore accessible (de l'alerte a la fin de seance).
Verdict (pour chaque regle 2, 3, 4, contre le 50/50 ; fixe d'avance) : TIENT si les 6 conditions :
  (i) gain net moyen >= +0,05 R par heure ou la regle change l'allocation ; (ii) gain net total > 0 avec couts doubles ;
  (iii) pire recul (cumul de R) pas pire que celui du 50/50 ; (iv) borne basse de l'IC a 95 % du gain journalier
  incremental > 0 apres correction pour 3 essais (quantile unilateral 1,67 %, bootstrap stationnaire blocs moyens 5 j,
  2 000 tirages) ; (v) test SPA de Hansen (3 regles contre 50/50) p < 0,05 ; (vi) bat son placebo (p < 0,05).
  INDETERMINE si gain total > 0 et (i) tient mais l'IC contient 0 ; sinon NE TIENT PAS.
  Une regle qui tient part en demo `_opt` hors totaux (6 mois prospectifs) ; si rien ne bat le 50/50 : arreter la
  recherche du detecteur sur cet historique et le dire. Usage : python3 banc_astra.py
"""
