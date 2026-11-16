# ECC (« Everything Claude Code ») : idées retenues (relais, 16/11 — étape 1, dépôt pas encore lu en détail)

1. **Vérification anti-secrets avant commit** — appliquée : `labo/verif_secrets.py` lit `git diff --cached` et
   refuse (code 1) clés privées, jetons GitHub/AWS/Anthropic/Slack, mots de passe en clair, numéros de compte MT5.
   À lancer à chaque passage avant `git commit`. Rien n'est installé comme hook (cela demanderait l'accord de Baptiste).
2. **Mémoire courte** (à faire) : ETAT.md réécrit en ≤ 40 lignes ; l'historique des passages part dans JOURNAL.md.
3. **Passages économes** (à faire) : lire seulement l'en-tête d'ETAT et les entrées nouvelles de PRIORITES (comme le relais).
Étape suivante : lire le README d'ECC (copie la plus étoilée) pour confirmer ou remplacer 2 et 3.
