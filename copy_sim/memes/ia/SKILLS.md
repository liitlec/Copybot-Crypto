# Tes skills (06/11) : méthodes prêtes à suivre

Chaque fiche dit QUAND l'utiliser, la COMMANDE, et COMMENT lire le résultat. Tous les chemins partent de
`/tmp/cc/copy_sim/memes` ; les données sont dans `/tmp/d`. Compte TOUTES les variantes essayées pendant le passage
(toi et tes agents) et passe ce total en `--essais` : c'est ce qui t'empêche de prendre du hasard pour une découverte.

## 1. Criblage : quels champs comptent ?
Quand : au début d'un passage, ou dès qu'un nouveau champ apparaît (tx_*, evol_*, un composé).
```
python3 ia/outils/criblage.py /tmp/d --test-heures 24 --delai 6 --essais N
python3 ia/outils/criblage.py /tmp/d --composes mes_composes.json      # crible aussi tes champs composés
python3 ia/outils/criblage.py /tmp/d --sortie sortie.json               # avec ta sortie au lieu de −25 % / +40 % / 4 h
```
Lecture : « RETENU » = le côté choisi sur l'ancien passe le seuil t ET reste positif sur le récent. Ce n'est qu'une
piste : elle doit passer au banc puis au tournoi. Si rien n'est retenu, c'est une information (note-la au registre).

## 2. Ajuster un score pondéré (un vrai modèle, sans code)
Quand : plusieurs champs donnent chacun un petit signal, aucun ne suffit seul.
```
python3 ia/outils/ajuste_score.py /tmp/d --champs rotation_h1,log:liquidite,c_flux --composes c.json --part 0.2 --essais N
```
Lecture : seul le chiffre « récent » compte (l'ancien est appris dessus). Il imprime le bloc `score` à coller tel quel
dans `entree.score`. Garde 2 à 5 champs : au-delà, le modèle apprend le bruit. Puis banc, puis tournoi.

## 3. Champs composés (inventer un signal)
Quand : l'idée est un rapport ou un écart entre deux données (« acheteurs des 5 dernières min / acheteurs de l'heure »,
« liquidité / volume », « détenteurs − acheteurs »). Dans la règle, `entree.composes` (10 au plus) :
```
"composes": [{"nom": "c_flux", "a": "transactions.m5.buyers", "op": "/", "b": "transactions.h1.buyers"},
             {"nom": "c_flux_log", "a": "c_flux", "op": "*", "b": 12, "log": true}]
```
`op` : + - * / min max ; `b` peut être un nombre ; un composé peut utiliser ceux définis avant lui ; nom en
`c_minuscules`. Utilisables dans les conditions, le score et le classement. Un opérande absent ou une division par 0 =
champ absent = pas d'achat.

## 4. Test vraiment hors échantillon
Quand : à chaque passage, pour chaque hypothèse « en jeu » du registre.
`python3 ia/banc.py /tmp/d regle.json --depuis <date de l'hypothèse>` : seulement les signaux arrivés après qu'elle
a été écrite. C'est le juge le plus honnête après le tournoi en direct.

## 5. Coût réel
Le banc lit `/tmp/d/reel.jsonl` (télécharge-le) : dès 5 ventes réelles, si le vrai marché coûte plus que les 4,2 %
supposés par aller-retour, le banc prend le coût mesuré. Une idée qui ne gagne que de 3 % par trade sur le papier
ne gagne rien en vrai : vise plus large, ou des sorties qui laissent courir les gagnants.

## 6. Autopsie
`python3 ia/autopsie.py /tmp/d --caisse defi_4` : chaque trade fermé, ce que le token montrait à l'achat, ce qu'il a
fait ensuite. À faire sur chaque place du tournoi, pas seulement sur la championne.

## 7. Demander un outil ou une donnée (sans attendre l'utilisateur)
Quand : il te manque une donnée (« âge des portefeuilles acheteurs »), un type de sortie (« vendre la moitié à +X »),
un outil. Écris-le dans `ia_demandes.md` sur le VPS (même envoi que ton carnet), une demande par bloc :
```
## D3 — 2026-11-06T19:00 — sortie en deux fois
Besoin : vendre 50 % à l'objectif et laisser courir le reste avec un stop suiveur.
Pourquoi (chiffré) : sur 40 trades de defi_3, 12 ont fait +60 % après l'objectif de +30 %.
Comment je l'utiliserai : nouvelle challengeuse, comparée à defi_3 sur 15 trades.
```
L'ingénieure (une session Claude, une fois par jour) lit tes demandes, code celles qui sont faisables et sûres, les
teste hors ligne, et le VPS les installe tout seul après son propre test (retour arrière automatique en cas de
problème). Sa réponse est dans `copy_sim/memes/ia/DEMANDES_FAITES.md` du dépôt (fait, refusé et pourquoi, en
cours). Une demande « faite » est utilisable dès le passage suivant son installation (`maj_auto.log` sur le VPS
dit quand). Ne demande jamais rien qui touche au test réel, au portefeuille ou au serveur : ce n'est pas
automatisable et ce sera refusé.
