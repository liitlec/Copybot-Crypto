"""Variante pari_court_opt (v20, PRIORITES 17/11 20 h 10 « pari court, de 1 jour a 1 mois ») : HORS totaux du test,
compte VIRTUEL separe de 100 $ (fichier etat_pari_court.json), distinct de pari_opt.
Banc : labo/banc_pc_rebonds.py avec l'outil labo/pari_court_commun.py (fenetres historiques reelles, Yahoo 1988-2026,
plafond du pont 0,50 lot par position). 4 pistes testees (cassures pyramidees et compression, annonces, week-end crypto,
rebonds a forte mise) : seul le repli des 4 indices US bat nettement la reference sans avantage. Choix fixe d'avance
(chance de x3 en 1 mois a 100 $ maximale parmi les essais qui battent la reference) : repli 4 indices, levier 100 fois
le compte virtuel, mise recalculee sur le compte (« tout remiser »). Chances en 1 mois a 100 $ (avantage / 2, contre la
reference sans avantage) : x2 29 % (22 %), x3 17 % (13 %), x5 8 % (5 %), x10 2 % (1 %), ruine 66 % (68 %).
C'est un pari : deux fois sur trois la poche est perdue.
Regles : celles de repli_ind sur NAS100+, SP500+, DJ30+, US2000+ ; taille = max(1, plancher(100 x compte / notionnel
d'un lot mini)) lots mini, plafond 0,50 lot ; trade saute si un lot mini depasse 120 fois le compte.
REGLE D'ARRET (ecrite avant le premier trade) : objectif x3 (compte virtuel + gains latents >= 300 $ : on ferme tout) ;
ruine (compte virtuel < 20 $) ; fin de l'horizon : 30 jours apres la 1re ouverture, on ferme tout et on s'arrete. Une
nouvelle poche ne repart que sur decision de Baptiste (effacer etat_pari_court.json)."""
import pari_opt


class PariCourt(pari_opt.Pari):
    NOM = "pari_court_opt"
    SYMBOLES = ("NAS100+", "SP500+", "DJ30+", "US2000+")
    LEVIER, NOTIONNEL_MAX_X, OBJECTIF = 100.0, 120.0, 3.0
    HORIZON = 30 * 86400

    def __init__(self, pont, fichier="etat_pari_court.json"):
        super().__init__(pont, fichier)
