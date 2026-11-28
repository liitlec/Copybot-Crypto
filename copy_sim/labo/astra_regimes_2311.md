
Détection en direct des régimes de marché sur l’or
Je garderais une allocation fixe entre suivi de tendance et retour à la moyenne comme référence, et je donnerais au détecteur une dernière expérience bornée. Les dix essais du labo ne montrent pas encore qu’une bascule en direct ajoute de la valeur après frais.
Les 16 et 17 novembre peuvent être en aller-retour à l’intérieur d’une semaine baissière. Pour décider d’ouvrir un panier, la question utile est donc : « Pendant la prochaine heure, quelle famille puis-je favoriser à risque égal ? »
Mesurer le gain accessible avec un oracle horaire
Dans les essais du labo, connaître le type de journée d’avance n’ajoutait que 338 à 1 132 $ sur neuf mois. Sans le capital, le risque engagé et le nombre de décisions, ces montants sont difficiles à juger. Un oracle journalier ne borne pas ce qu’un choix horaire pourrait rapporter.
À chaque heure pleine, partir du même état de compte et comparer trois autorisations pour les nouvelles entrées : répartition fixe 50/50 du budget de risque, tendance seule, retour seul. Les paniers déjà ouverts suivent leurs sorties habituelles. Attribuer aux nouvelles entrées leur résultat jusqu’à clôture et respecter le plafond de risque commun. Le meilleur choix connu après coup donne une estimation optimiste. Si le gain est trop faible, arrêter. S’il vient de trois décisions, examiner ce que le détecteur aurait dû reconnaître à ces trois moments.
Trois règles à figer avant le replay
Les seuils suivants sont des hypothèses expérimentales. Leur performance sur les cotations STARTRADER du labo reste à mesurer. Tester chaque règle séparément, sur bougies terminées, avec exécution au premier prix disponible suivant. Un état indéterminé conserve le 50/50.
1   Prolongement après un retournement confirmé
À l’ouverture de séance, fixer δ = max(4c, 0,15 × ATR journalier sur 14 séances terminées). La variable c est le coût aller-retour médian en dollars par once sur les 20 séances terminées. Utiliser les clôtures M5. En phase montante, conserver le plus haut de clôture et confirmer une inversion au premier recul de δ ; appliquer la règle symétrique en descente.
Pour chaque jambe terminée, diviser par δ la distance parcourue dans son sens entre sa clôture de confirmation et son extrême ultérieur. À l’heure pleine, prendre la médiane des trois derniers prolongements terminés dans la séance. À partir de 1, autoriser la tendance. À 0,25 ou moins, autoriser le retour. Entre ces seuils ou avant trois jambes terminées, conserver le 50/50.

Vérifier ce qui reste négociable après le signal
Pourquoi tester le prolongement ?  Il mesure le parcours qui reste après un mouvement identifiable et qui pourrait payer un renfort. Un faible prolongement, à lui seul, ne prouve pas qu’un retour est exploitable.
Placebo du premier test.  Permuter les prolongements entre séances, à heure et volatilité comparables, en conservant les heures auxquelles trois jambes étaient disponibles. Publier l’heure du premier signal. Si la règle n’agit qu’après 18 h, elle reproduit le premier échec du labo. Les travaux sur les changements directionnels motivent cette représentation sur le marché des changes. Les seuils et leur profitabilité sur l’or restent à valider.
Glattfelder, Dupuis et Olsen · Patterns in high-frequency FX data
2   Détecter le calme qui rend une entrée trop chère
À chaque heure pleine, relever pour les 60 séances antérieures, à la même heure de New York, l’amplitude haut–bas de l’heure qui suivait. Leur médiane A est disponible à la décision du jour. Estimer le coût aller-retour exécutable c au moment de décider, dans la même unité : spread compté une fois, commissions et provision de glissement incluses. Si A/c < 4, suspendre les nouvelles entrées pendant une heure. Sinon, conserver le 50/50. Les paniers ouverts continuent.
Pourquoi ce test en premier ?  Une stratégie ne capture qu’une fraction de l’amplitude d’une heure. Le rapport amplitude/coût teste donc un mécanisme économique concret. La saisonnalité intrajournalière de la volatilité est documentée ; le seuil de quatre est expérimental.
Placebo.  Suspendre autant d’heures dans les mêmes tranches horaires et les mêmes mois. Comparer aussi à une réduction permanente du risque donnant la même exposition moyenne. Si le bénéfice vient uniquement de la moindre exposition, le filtre n’a rien apporté.
Andersen et Bollerslev · Intraday periodicity and volatility persistence in financial markets
3   Tester si le marché conserve le prix après une annonce
Limiter l’essai aux publications américaines CPI et emploi, à l’heure officielle effectivement connue ce jour-là. P₀ est la dernière clôture M5 avant publication. À +5 minutes, calculer J = P₅ − P₀. Ignorer le mouvement si |J| est inférieur à deux fois la médiane des variations M5 absolues au même créneau sur les 60 séances antérieures. À +15 minutes, calculer F = (P₁₅ − P₀)/J pour un choc non nul.
Si F ≥ 0,75, autoriser la tendance dans le sens du choc. Si F ≤ 0,25, autoriser le retour vers P₀ uniquement si le prix ne l’a pas déjà traversé depuis le choc. Sinon, conserver le 50/50. L’autorisation expire à +60 minutes. Aucun gain du saut initial ne revient au détecteur.
Placebo.  Appliquer la règle à de faux événements de même heure, de même jour de semaine et d’amplitude initiale comparable. Le modèle à 71 variables incluait déjà les annonces. Cette hypothèse vise la tenue du prix après quinze minutes. Les travaux sur le FX établissent une réaction rapide aux nouvelles ; la persistance exploitable sur l’or reste à démontrer. Avec 15 à 18 mois, cet essai reste exploratoire.
Andersen et al. · Micro Effects of Macro Announcements

Protocole et décision pour le laboratoire
Les trois règles peuvent être étudiées sans carnet d’ordres, sans vrai volume et sans série FRED révisée. Je laisserais le COT et le VIX hors de cette expérience. Le labo étudie déjà le VIX, et chaque essai doit permettre d’identifier quelle hypothèse a réussi ou échoué.
1   Réserver une période vierge
Les 15 à 18 mois déjà inspectés servent au diagnostic et à la vérification du code. À défaut d’une archive M5 avec spread réel entièrement tenue à l’écart, geler les règles maintenant et prendre les six mois suivants en démo comme premier contrôle prospectif. Pour les annonces, six mois donneront trop peu d’événements pour un verdict ferme.
2   Comparer à quatre témoins
Sur le même capital, comparer au 50/50 fixe en risque, à la tendance seule, au retour seul et au placebo propre à la méthode. Exécuter les paniers complets, y compris ceux qui se chevauchent. Prélever les 30 % sur le bénéfice quotidien agrégé selon la convention effective. Pour la règle « suivre ce qui marche sur cinq jours », ajouter un témoin à même exposition totale : doubler la mise du gagnant peut modifier le levier en même temps que l’allocation.
3   Fixer le gain minimal avant les résultats
Je propose d’exiger +0,05 R net en moyenne par décision qui change effectivement l’allocation, face au 50/50, et un gain net positif sur le portefeuille entier avec les coûts d’exécution doublés, sans aggravation du recul maximal observé. Un R désigne ici le budget de risque global disponible à la décision, commun aux variantes. Le seuil économique de 0,05 R est à adopter ou remplacer avant le test.
Exiger également que la borne basse à 95 % du gain incrémental dépasse zéro après prise en compte des trois essais. Rééchantillonner des blocs temporels qui préservent les paniers simultanés. Si l’intervalle reste large, le verdict est « indéterminé ».
Politis et Romano · The Stationary Bootstrap
Hansen · A Test for Superior Predictive Ability
4   Mesurer le retard en argent
Pour chaque alerte, enregistrer l’heure, le premier prix exécutable, le gain déjà passé et le gain encore accessible. Une journée correctement reconnue à 18 h peut valoir zéro. Un détecteur peu précis peut être rentable s’il évite à temps quelques pertes coûteuses. Le pourcentage de bonnes réponses laisse cette question ouverte.
Décision
Conserver l’allocation fixe si chaque famille justifie sa place après frais et si leurs pertes se compensent réellement. Tester d’abord le veto de coût, puis le prolongement après retournement. Garder le résultat à cinq jours (p = 0,06) pour une réplication avec fenêtre gelée. Si aucun mécanisme ne bat le mélange fixe selon le contrat ci-dessus, arrêter la recherche du détecteur sur cet historique. Les observations de novembre motivent la complémentarité des familles. Leur répartition dynamique doit encore prouver sa valeur.

