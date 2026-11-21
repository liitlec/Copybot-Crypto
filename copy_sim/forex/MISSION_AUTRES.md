# Exporter les autres trades du compte démo pour le laboratoire (demandé par Baptiste le 12/11/2026)

Le compte démo contient aussi les positions des anciens robots de Baptiste (BlockTrend, BlockRange, BlockGrille,
BlockFinMois…). Le 12/11 au matin elles faisaient environ +650 $ en cours, alors que le robot du labo était à
l'équilibre. Baptiste veut que l'IA du labo les étudie aussi. Le pont ne les montre pas : à toi de les exporter.
Réponds-lui en français, court et clair.

## Ce qu'il faut ajouter au pont (lecture seule, aucune action sur ces positions)
Toutes les 5 minutes, écrire dans `copy_sim/labo/mt5/autres/` :
- `ouvertes.json` : les positions ouvertes qui ne sont pas au pont (numéro magique différent) : robot (nom tiré du
  commentaire ou d'une table numéro magique → nom de robot, faite une fois avec Baptiste), symbole, sens, lots, prix
  d'entrée, heure d'ouverture, prix actuel, stop, objectif, résultat en cours, swap.
- `historique.csv.gz` : toutes les transactions fermées de ces robots depuis l'ouverture du compte (même champs, plus
  heure et prix de sortie, commission, swap, résultat). Une fois en entier, puis seulement les nouvelles.

## Règles
- **Lecture seule** : le pont ne modifie ni ne ferme jamais ces positions.
- Rien d'identifiant dans le dépôt (public) : ni numéro de compte, ni serveur, ni nom, ni tickets réels si un
  numéro relatif suffit ; pas le code source des robots de Baptiste sans son accord (leurs réglages, si utiles, peuvent
  être résumés).
- Montre à Baptiste un extrait de ce qui sera publié avant de l'activer, puis dis-lui en 2 lignes que c'est en place.
