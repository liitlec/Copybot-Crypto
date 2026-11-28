# Monter le plafond de positions du pont à 30 (demandé par Baptiste le 12/11/2026), pour la session du PC

Baptiste veut que le robot du laboratoire puisse ouvrir plusieurs positions en même temps pour une même stratégie.
Le pont plafonne aujourd'hui à 10 positions au total : passe ce plafond à **30**. Rien d'autre ne change : démo
seulement, 0,50 lot au plus par position, stop obligatoire, garde-fou −5 % par jour, positions du pont seulement.
Mets à jour `plafonds.positions` dans `etat.json`, relance les essais du pont (`essais_pont.py`) et du lanceur, puis
dis à Baptiste en une ligne que c'est fait. Réponds-lui en français.
