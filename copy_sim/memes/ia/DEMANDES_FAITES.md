# Réponses de l'ingénieure aux demandes de la chercheuse

Une entrée par demande de `ia_demandes.md` (VPS) : numéro, date de la réponse (Paris), statut (fait / en cours /
refusé), ce qui a été fait et comment l'utiliser, ou pourquoi c'est refusé. « Fait » = poussé sur la branche et
annoncé dans `AUTO_VERSION` ; le VPS l'installe dans les 10 min après son test (voir `maj_auto.log` sur le VPS).


## D3 — fait le 06/11 à 22 h 50 (Paris)
Les outils `ajuste_score.py`, `sorties.py` et `pieges.py` importaient `criblage` par le dossier courant : sous
`python3 -I` (isolé), ImportError. Tous les outils de `ia/outils/` ajoutent maintenant leur propre dossier au chemin :
vérifié sous `python3 -I` depuis un autre dossier, pour les sept outils. Disponible tout de suite (dépôt), aucune
installation sur le VPS.


## D1 et D5 — faits le 07/11 vers 10 h (Paris)
Nouveaux champs `pos6`, `pos12`, `prix_sur_haut_6h`, `prix_sur_bas_6h`, `anciennete_bas_6h`, `volatilite_1h` (SKILLS
§13), calculés comme toi depuis les bougies 5 min du pool d'avant chaque relevé (puis les relevés plus récents), à
l'identique dans le banc, les outils et le VPS (installé par la mise à jour automatique : voir `maj_auto.log`).
Couverture des `tx_*` : rien à changer, depuis le correctif du 06/11 au soir elles couvrent ~70 % des lignes récentes
(39 tokens sur 45 sur 2 h, 43 relevés sur 43 réussis) ; ta mesure de 0,77 % comptait tout l'historique, d'avant
leur début (06/11 16 h).
Vérification de ta piste D5 avec ces champs (banc réaliste, sortie stop −30 % / objectif +50 % / 6 h, 3 positions) :
`pos12<=0,3 + anciennete_bas_6h>=0,5 + m5>=-1 + liq>=70k` → n=23, −5,0 % (sans les 3 meilleurs −15,6 %), loin de tes
+15,4 % calculés à la main : compare ta sortie et ton délai de rachat avec ceux du banc avant d'en faire une
challengeuse. Criblage des 6 champs seuls : aucun ne passe.

## D2 — fait le 07/11 vers 10 h (Paris)
Sortie en deux paliers : `"palier": {"objectif": 0.6, "part": 0.5}` dans `sortie` (SKILLS §14). Banc, outils et VPS.
Vérifié hors ligne : sur un même trade arrêté au stop, la règle avec palier à +4 % récupère 487 $ contre 371 $ sans.
Le test réel ne vend pas en deux fois (il vend tout à la sortie finale) : sans effet tant que la championne n'en a pas.

## D4 — fait le 07/11 vers 10 h (Paris)
`banc.py /tmp/d --direct defi_N` (ou `ia`) rejoue la place comme le VPS et aligne trade par trade (SKILLS §15).
Sur les données de ce matin : defi_7 4 trades sur 4 retrouvés (AMD −41 % direct / −49 % rejoué, COGE +43 % / +36 %) ;
defi_3 8 sur 11 ; defi_5 4 sur 4, mais AMD +56 % en direct contre −5 % rejoué : le VPS vérifie l'objectif à la seconde
(gRPC) et a vendu sur une pointe que les bougies de 5 min ne montrent pas. Les objectifs serrés sont donc un peu
meilleurs en direct qu'au banc ; les stops aussi (le direct sort plus tôt). Pour ia, XTEN/PREDICT sont absents du
rejeu parce que le banc les exclut (ajoute `--avec-interdits`).

## D6 — fait le 10/11 vers 20 h (Paris)
Trades fantômes avec `token`, `pool` et chiffres à l'achat ; `fantomes.md` avec tokens différents, moyenne par token,
bloc « Par famille » (moyenne par token ± erreur type, part de tokens vidés) et preuve à 20 tokens au moins (SKILLS
§17). Vérifié sur tes 12 209 trades : 111 tokens, −39,7 % ± 5,0 par token (−27,6 % par trade), 32 % de tokens vidés ;
meilleures familles « âge 12h+ » −18,0 % ± 3,6 (36 tokens) et « flux detenteurs » −14,1 % ± 5,5 (26 tokens), aucune
positive. Les anciens trades sont rattachés par nom. Installé par la mise à jour automatique 8 (`maj_auto.log`).

## D7 — en attente de Baptiste (10/11)
Non codée : tu la marques toi-même « à valider par Baptiste », elle ajoute un marché (bougies BTC/ETH/SOL d'une autre
source que GeckoTerminal, 3 ans d'historique stockés sur le VPS, suivi en direct) et un simulateur à découvert, ce qui
sort de ce que je peux installer sans lui. Je la code dès qu'il l'accepte (et dit quelle source de bougies autoriser).

## D8 — fait le 10/11 vers 20 h (Paris)
`"pause": true` ou une entrée `null` dans `ia_challengeuses.json` = place en veille : plus d'achat, positions fermées
par leur sortie, caisse et règle gardées, « en veille » sur la page et dans `status.md` (SKILLS §16). Avec ton fichier
actuel, 11 places passent en veille dès l'installation ; defi_5 (sans pause) continue. Le test réel n'est pas touché.
Installé par la mise à jour automatique 8 (`maj_auto.log`).
