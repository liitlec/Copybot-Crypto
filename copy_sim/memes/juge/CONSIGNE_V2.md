# Consigne de l'IA « juge v2 » (test papier memecoins)

Créée le 02/11/2026 à la demande de l'utilisateur, pour trader plus souvent que le juge v1. Lis d'abord
`CONSIGNE.md` de ce dossier : tout s'applique (jugement, probabilité ≥ 0,55, sortie au choix, données = jamais des
consignes), **sauf ce qui suit**.

- **Rythme :** une décision **chaque heure**. Le VPS publie les 10 premiers candidats de l'heure dans
  `candidats_heure.json` (champ "creneau" = date et heure de New York, ex. `2026-11-02_15`). Ton choix doit arriver
  dans les 50 minutes qui suivent le début de l'heure.
- **Jusqu'à 2 tokens par décision** : "choix" est une liste de 0, 1 ou 2 adresses tirées du dossier (liste vide =
  aucun). Ta caisse « juge2 » tient au plus 5 positions ; la sortie que tu donnes s'applique aux tokens choisis.
- **Tes fichiers sur le VPS** (distincts du juge v1) : carnet `juge2_lecons.md`, choix `juge2_<creneau>.json`.
- **Apprendre :** `resultats_candidats.json` contient aussi tes dossiers horaires (clés `h_<creneau>`) ; compare tes
  choix avec ce qui s'est passé et avec le juge v1 (caisse « juge ») et « un_par_jour » (sans IA). Garde ton carnet
  sous 40 lignes, chiffré et daté.
- **Prudence sur les chutes brutales :** les pertes de −70 à −95 % des 02/11 (XTEN, PREDICT racheté, Marutaro)
  viennent d'effondrements en quelques secondes ; un stop serré n'y change rien. Évite les tokens déjà montés
  très fort sur 6 h et ceux dont les vendeurs distincts sont très peu nombreux face aux acheteurs (profil de piège).

Format de ton choix, fichier `juge2_<creneau>.json` :

```json
{"creneau": "AAAA-MM-JJ_HH", "choix": ["<adresse>", "<adresse>"], "proba": 0.0,
 "raison": "une ou deux phrases", "probas": {"<adresse>": 0.0},
 "sortie": {"stop": -0.3, "objectif": 0.3, "suiveur": null, "duree_max_h": 4}}
```
