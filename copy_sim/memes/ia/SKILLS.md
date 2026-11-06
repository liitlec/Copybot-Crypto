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

## 8. Optimiser la sortie d'une entrée
Quand : une entrée semble bonne mais la sortie a été choisie à la main (souvent le cas), ou des gagnants repartent
après ton objectif.
`python3 ia/outils/sorties.py /tmp/d regle.json --essais N` : 400 sorties (stop, objectif, suiveur, durée) sur les
MÊMES achats, classées sur l'ancien, jugées sur le récent. « RETENUE » seulement si elle passe le seuil (qui compte les
400 essais) ET bat la sortie actuelle sur le récent. Grille réglable (`--stops`, `--objectifs`, `--suiveurs`,
`--durees`, 0 = sans). Une nouvelle sortie se teste en challengeuse avec la même entrée, jamais directement.

## 9. Test contre le hasard (obligatoire avant toute promotion)
`python3 ia/outils/hasard.py /tmp/d regle.json` : 2000 tirages d'achats au hasard, mêmes jours, même sortie, même
nombre. p < 5 % : l'entrée choisit vraiment ses tokens. Sinon, son résultat vient du marché du moment ou de la
sortie (au 06/11 : v15 p = 4 %, defi_5 p = 3 %, defi_3 p = 31 %). Avec k règles testées, exige p < 5 % / k.

## 10. Détecteur de pièges (filtre à ajouter à toute règle)
`python3 ia/outils/pieges.py /tmp/d [--horizon 24] [--chute 0.8]` : quels champs, à l'achat, séparent les tokens
qui se vident ou s'effondrent de 80 % dans les 24 h. Il propose des conditions « garder si » vérifiées sur le récent.
Au 06/11 : sous ~4 200 achats sur 1 h (`transactions.h1.buys`), 83 % de pièges sur l'ancien et 94 % sur le récent,
contre 16 % au-dessus. Ajouter un tel filtre à une bonne entrée est souvent le gain le plus sûr.

## 11. Diversité du tournoi
`python3 ia/outils/diversite.py /tmp/d` (aussi sur la page) : les places qui achètent surtout les mêmes tokens ne
testent qu'une idée. Au 06/11 : la championne, defi_1 et defi_2 ont 89 à 100 % d'achats communs. Quand une place
se libère, remplace l'une des deux d'une paire trop proche par une autre famille d'idées.

## 12. Validation glissante
`python3 ia/outils/glissante.py /tmp/d regle.json [autres.json]` : la règle jugée sur 6 périodes successives.
« SOLIDE » = au moins 2/3 des périodes positives, aucune sous −20 %, positive sans la meilleure période. Au 06/11,
v15, defi_3 et defi_5 sont « FRAGILE » : chacune ne gagne que sur une période. À passer avant toute promotion, avec
le test contre le hasard.

## Ordre conseillé pour une idée
criblage ou pièges (piste) → règle → banc `--essais N` → hasard → glissante → sorties → challengeuse → 15 trades en
direct → promotion. Note chaque étape au registre.

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
