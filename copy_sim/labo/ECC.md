# ECC (« Everything Claude Code ») : ce qui peut servir au labo (fini le 17/11)

Copie lue : github.com/affaan-m/everything-claude-code (la plus étoilée ; 72 agents, 327 skills, des hooks, des règles,
deux guides « court » et « long »). Lecture seule : rien installé, aucun script ni hook exécuté, aucun réglage changé.

| Idée (d'où elle vient dans ECC) | Utile au labo ? | Déjà en place ? | Effort |
|---|---|---|---|
| Contrôle anti-secrets avant commit (security-scan, guide sécurité) | **oui**, dépôt public | **oui** : `verif_secrets.py` (à lancer à la main) | fait |
| Le même contrôle en hook automatique avant commit | oui | non : touche aux réglages, **accord de Baptiste** | faible |
| Mémoire courte : fichier d'état court, l'historique ailleurs (guide long, « mémoire entre sessions ») | **oui**, c'est le 1er coût d'un passage | en partie : ETAT.md fait **192 lignes** (visé : ≤ 40), JOURNAL.md 1 550 | faible |
| Fichier de passation écrit en fin de passage, seul fichier lu au début | oui | en partie (ETAT + PRIORITES) | faible |
| Chercher avant de coder (search-first) : vérifier qu'un banc existant ne fait pas déjà la chose | **oui** (37 bancs, beaucoup de doublons possibles) | en partie : il faut lire les en-têtes un par un | faible |
| Sous-agents : une entrée, une sortie écrite dans un fichier ; donner le **but**, pas seulement la question ; 3 allers-retours au plus (iterative-retrieval) | oui | en partie (relais) | faible |
| Compaction volontaire entre phases (lecture → banc → écriture) plutôt qu'au hasard (strategic-compact) | oui | non | faible |
| Boucle de vérification avant commit : compiler les fichiers touchés, anti-secrets, relire le diff (verification-loop) | oui | en partie (anti-secrets seulement) | faible |
| Petits tests hors ligne sur données figées (comme les « fixtures » des dépôts de trading) pour le robot : heures serveur NY + 7, taille, stop | oui, évite les erreurs d'heure | non | moyen |
| Boucles : but vérifiable par la machine, nombre d'essais plafonné, pas de « tricher le juge » (loop-design-check) | oui : chaque banc compte ses essais | en partie (compteur d'essais tenu dans JOURNAL) | faible |
| Sécurité d'un agent qui trade : limites, coupe-circuit, simulation avant envoi (llm-trading-agent-security) | oui | **oui** pour l'essentiel (pont démo, 0,01 lot, garde-fou) ; pas de coupe-circuit journalier | moyen |
| Peu d'outils actifs à la fois (MCP, plugins) pour garder le contexte | oui | dépend des réglages : **accord de Baptiste** | faible |
| Apprentissage continu par hooks (« instincts ») | non : lourd, installe des hooks | non | élevé |

## Les 3 idées à adopter en premier
1. **ETAT.md en 40 lignes au plus** (état du robot, résultats en cours, 3 prochaines tâches) ; tout le reste va
   dans JOURNAL.md, qu'on ne lit plus que par `grep`. Je peux le faire seul dans `labo/`. Gain : moins de lecture à
   chaque passage.
2. **Un index des bancs** (`BANCS.md`, une ligne par banc : règle, données, verdict, nombre d'essais), mis à jour
   à chaque nouveau banc. Évite de relire JOURNAL et les en-têtes pour savoir si une idée a déjà été testée
   (« chercher avant de coder »). Je peux le faire seul.
3. **Boucle de vérification avant chaque commit** : `verif_secrets.py`, compilation des `.py` touchés, relecture du
   diff. À la main tout de suite ; en hook automatique seulement avec l'accord de Baptiste.
