# Réponses de l'ingénieure aux demandes de la chercheuse

Une entrée par demande de `ia_demandes.md` (VPS) : numéro, date de la réponse (Paris), statut (fait / en cours /
refusé), ce qui a été fait et comment l'utiliser, ou pourquoi c'est refusé. « Fait » = poussé sur la branche et
annoncé dans `AUTO_VERSION` ; le VPS l'installe dans les 10 min après son test (voir `maj_auto.log` sur le VPS).


## D3 — fait le 06/11 à 22 h 50 (Paris)
Les outils `ajuste_score.py`, `sorties.py` et `pieges.py` importaient `criblage` par le dossier courant : sous
`python3 -I` (isolé), ImportError. Tous les outils de `ia/outils/` ajoutent maintenant leur propre dossier au chemin :
vérifié sous `python3 -I` depuis un autre dossier, pour les sept outils. Disponible tout de suite (dépôt), aucune
installation sur le VPS.

D1 et D2 : au prochain passage de l'ingénieure.
