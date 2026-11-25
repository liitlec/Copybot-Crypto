# Lancer le robot en RÉEL sur le compte cent (guide pour Baptiste)

Tout est prêt dans le dépôt. **Rien ne trade tant que tu n'as pas fait l'étape 6 toi-même, sur ton PC.**
Tes identifiants restent dans MetaTrader 5 : le pont ne les lit jamais et ne les écrit nulle part.

## Ce qui tournera en réel

| Stratégie | Taille | Rôle |
|---|---|---|
| bt_or_plus | 0,02 lot cent de base, renforts 0,04 / 0,06 / 0,08 / 0,10 | le moteur (suivi de tendance de l'or) |
| elan_m15, cassure_m15, exces_m1, exces_m5, retour_court_ar | 0,01 lot cent | règles courtes, comme en démo |

Rien d'autre : ni témoin, ni variante, ni indices. Le nom exact de l'or chez le courtier (par ex. `XAUUSD` ou
`XAUUSD.c`), le lot minimum et le pas de lot sont lus dans MetaTrader, jamais devinés.

## Les sécurités (dans le pont réel, impossibles à contourner par le robot)

| Sécurité | Effet |
|---|---|
| Fichier d'autorisation | Sans `AUTORISATION_REEL.json` écrit par toi (étape 6) : **aucun ordre** |
| Version du robot | Seule la version inscrite par toi dans ce fichier (`"robot"`) peut s'installer |
| Bon compte | Le numéro du fichier doit être celui du compte connecté, en mode réel et en devise cent (USC ou EUC) |
| Arrêt automatique à **−34 %** | Si la valeur du compte tombe à −34 % de son plus haut : plus aucun ordre, les positions restent sur leurs stops. Il ne repart que si tu supprimes `sommet_reel.json` |
| Garde-fou du jour | Perte du jour au-delà de −5 % : plus d'ouverture jusqu'au lendemain |
| Plafonds | 10 positions au plus, 0,10 lot cent par position, stop obligatoire, spread maximal par ordre |
| Arrêt d'urgence | Créer le fichier `STOP_PONT` dans `%USERPROFILE%\pont_mt5_reel` : plus aucun ordre, robot arrêté |

Le pont démo (tâche `PontMT5`, port 8765) ne change pas. Le pont réel tourne à part (tâche `PontMT5Reel`, port 8766,
dossier `%USERPROFILE%\pont_mt5_reel`, clone du dépôt `%USERPROFILE%\depot_reel`).

## Pas à pas

1. **Installer un 2e MetaTrader 5** pour le compte cent. Prends l'installateur STARTRADER et choisis **un autre
   dossier** que celui de la démo, par exemple `C:\Program Files\STARTRADER MT5 cent`. Note le chemin de son
   `terminal64.exe`.
2. **Te connecter au compte cent** dans ce 2e terminal (Fichier → Connexion au compte de trading). Coche
   « Enregistrer le mot de passe » pour qu'il se reconnecte seul.
3. **Vérifier**, dans ce terminal :
   - en haut, le compte affiche **« Réel »** et la devise **USC** (ou EUC) ;
   - le symbole de l'or (Affichage → Symboles, chercher XAUUSD) : son nom exact, lot minimum 0,01, pas 0,01 ;
   - le levier (Outils → Options → Serveur, ou ton espace client) ;
   - Outils → Options → Expert Advisors : **« Autoriser le trading algorithmique »** coché, et le bouton
     « Trading algo » vert dans la barre d'outils.
4. **Déposer l'argent** (200 €) quand tu es prêt. Le pont peut être installé avant : sans autorisation, il ne fait rien.
5. **Installer le pont réel** : ouvre PowerShell dans le dossier `copy_sim\forex` du dépôt et tape
   (avec ton chemin de l'étape 1) :

   ```powershell
   .\installer_tache_reel.ps1 -Terminal "C:\Program Files\STARTRADER MT5 cent\terminal64.exe"
   ```

   Il crée la tâche `PontMT5Reel`, un raccourci « Robot REEL en direct » sur le bureau (http://127.0.0.1:8766/), et
   rappelle qu'il n'y a pas encore d'autorisation. Le tableau de bord doit afficher « pas d'autorisation : aucun ordre ».
   *Avec deux MT5 ouverts* : si le pont démo se met à dire « compte non démo », relance son installateur avec le
   chemin du terminal démo : `.\installer_tache.ps1 -Terminal "<chemin du terminal64.exe de la démo>"`.
6. **Autoriser** (le seul geste qui permet de trader) : dans le Bloc-notes, crée le fichier
   `%USERPROFILE%\pont_mt5_reel\AUTORISATION_REEL.json` avec exactement :

   ```json
   {"compte": 12345678, "phrase": "J'autorise le robot a trader en reel sur ce compte cent", "robot": 1}
   ```

   Remplace `12345678` par **ton numéro de compte cent** (sans guillemets). `"robot": 1` est la version du robot réel
   que tu autorises : une nouvelle version ne s'installera que lorsque tu changeras ce nombre toi-même. Ce fichier reste sur ton PC : il n'est
   jamais envoyé dans le dépôt. Dans la minute, le tableau de bord passe à « ordres autorisés » et le robot réel
   s'installe (« ESSAIS OK » obligatoire).
7. **Suivre** : le tableau de bord réel (raccourci du bureau) en direct ; la page `copy_sim/reports/reel_suivi.html`
   (solde, valeur, résultat du jour, par stratégie, recul depuis le plus haut, distance à l'arrêt −34 %) ; et dans
   MetaTrader, l'onglet « Trading ».
8. **Retraits** (toujours faits par toi, le robot ne retire jamais d'argent) : **quand le compte a doublé (400 €),
   retire tes 200 €**, puis laisse tourner. La page de suivi le signale.

## Arrêter

| Pour… | Faire |
|---|---|
| Arrêter tout de suite (urgence) | Créer un fichier vide `STOP_PONT` dans `%USERPROFILE%\pont_mt5_reel`. Les positions restent sur leurs stops ; tu peux les fermer à la main dans MetaTrader |
| Retirer l'autorisation | Supprimer `AUTORISATION_REEL.json` : plus aucun ordre dans la minute |
| Désinstaller | PowerShell : `Unregister-ScheduledTask -TaskName PontMT5Reel -Confirm:$false` |
| Repartir après l'arrêt −34 % | Seulement après réflexion : supprimer `sommet_reel.json` (le plus haut repart de la valeur actuelle) |
| **Arrêter à distance** (pas chez toi) | Voir ci-dessous : un message à Claude depuis ton téléphone suffit |

### Arrêt à distance (depuis ton téléphone)

Écris à Claude dans l'app, par exemple : **« Arrête le robot réel »** ou **« Arrête le robot réel et ferme tout »**.
Claude écrit alors dans le dépôt le fichier `copy_sim/labo/mt5_reel/ARRET_DISTANT.json` :

| Contenu | Effet (dans la minute qui suit) |
|---|---|
| `{"arret": true}` | Plus aucune ouverture ni renfort, robot réel arrêté ; les positions restent sur leurs stops |
| `{"arret": true, "fermer_tout": true}` | En plus, ferme toutes les positions du robot réel (seulement les siennes, une fois) |
| `{"arret": false}` ou fichier supprimé | Fonctionnement normal |

Le tableau de bord réel et la page de suivi affichent « ARRÊT À DISTANCE » avec l'heure. **Ce fichier ne peut
qu'arrêter** : il ne peut jamais autoriser ni relancer quoi que ce soit, car l'autorisation reste ton fichier local
`AUTORISATION_REEL.json`. Pour reprendre, demande à Claude de remettre `{"arret": false}`, ou fais-le toi-même.

**Important** : le pont réel tourne depuis une copie figée. Cette fonction ne marche qu'après avoir **relancé
`installer_tache_reel.ps1` une fois**, rentré chez toi (même commande qu'à l'étape 5). Avant ça, à distance, il ne
reste que la fermeture à la main depuis l'application MetaTrader 5 du téléphone, connectée au compte cent.

Une nouvelle version du robot réel (`copy_sim/labo/mt5_reel/robot/VERSION`) ne s'installe que si **tu** mets son
numéro dans le champ `"robot"` de ton fichier d'autorisation, et seulement si ses essais passent.
