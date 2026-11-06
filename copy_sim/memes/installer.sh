#!/bin/sh
# Mise à jour du test papier memecoins sur le VPS. Ne touche pas à /opt/g15 ni au service g15.
# Usage (en root) : curl -fsSL <url>/installer.sh | sh -s JETON
#
# Sécurité : les deux services tournent sous un utilisateur dédié « memes », sans droits root, dans un bac à sable
# systemd qui leur rend /opt/g15 et /root invisibles et le reste du système en lecture seule ; seul /opt/memes_paper
# est modifiable. Les fichiers sont pris à un commit figé (VERSION), pas à la tête de la branche.
# Le prix en direct par gRPC s'active si /opt/memes_paper/grpc.env contient GRPC_ENDPOINT=... et GRPC_TOKEN=...
#
# Depuis le 06/11 (mises à jour automatiques demandées par l'utilisateur) :
# - le code de recherche (memes_paper.py, apprend.py, memes_page.py, flux.py) peut être remplacé sans validation par
#   memes-maj.timer (maj_auto.py, sous l'utilisateur memes, après son test hors ligne, avec retour arrière automatique) ;
# - le test réel tourne sous un AUTRE utilisateur, « memesreel », dans /opt/memes_reel (clé, réglage, état, son propre
#   Python) : l'utilisateur memes ne peut ni lire la clé ni modifier ce code. Le test réel ne fait que lire les
#   fichiers du papier. reel.py, serveur.py, maj_auto.py et ce script ne changent que par ce script (donc validé).
set -e
[ -n "$1" ] || { echo "usage : sh installer.sh JETON"; exit 1; }
VERSION=ff5de85cc24f62edf8ac70999aea7a0403d74ba0
SEQ=1  # numéro de la version automatique incluse (AUTO_VERSION) : maj_auto.py n'installe que les numéros suivants
D=/opt/memes_paper
R=/opt/memes_reel
L=/usr/local/lib/memes
U=https://raw.githubusercontent.com/liitlec/Copybot-Crypto/$VERSION/copy_sim/memes
mkdir -p "$D/yproto" "$D/data"
cd "$D"
for f in memes_paper.py memes_page.py apprend.py serveur.py flux.py yproto/__init__.py yproto/geyser_pb2.py yproto/geyser_pb2_grpc.py \
         yproto/solana_storage_pb2.py yproto/solana_storage_pb2_grpc.py; do
  curl -fsSL -o "$f.new" "$U/$f" && mv "$f.new" "$f"
done
rm -f "$D/reel.py"  # le test réel vit maintenant dans /opt/memes_reel
mkdir -p "$L" "$R/data"
curl -fsSL -o "$L/maj_auto.py.new" "$U/maj_auto.py" && mv "$L/maj_auto.py.new" "$L/maj_auto.py"
curl -fsSL -o "$R/reel.py.new" "$U/reel.py" && mv "$R/reel.py.new" "$R/reel.py"
chown -R root:root "$L" && chmod 755 "$L" && chmod 644 "$L/maj_auto.py"
printf '%s\n' "$1" > "$D/jeton"
# environnement Python à part pour le gRPC (grpcio, protobuf récent) ; en cas d'échec, le test tourne sans gRPC
PY=/usr/bin/python3
if [ ! -x "$D/.venv/bin/python" ]; then
  python3 -m venv "$D/.venv" 2>/dev/null || { apt-get install -y -qq python3-venv >/dev/null 2>&1 && python3 -m venv "$D/.venv"; } || true
fi
if [ -x "$D/.venv/bin/python" ] && "$D/.venv/bin/pip" install -q --disable-pip-version-check grpcio protobuf solders; then
  PY="$D/.venv/bin/python"
else
  echo "gRPC : installation de grpcio impossible, le test continue avec GeckoTerminal toutes les 15 s"
fi
id memes >/dev/null 2>&1 || useradd --system --home-dir "$D" --shell /usr/sbin/nologin memes
id memesreel >/dev/null 2>&1 || useradd --system --home-dir "$R" --shell /usr/sbin/nologin memesreel
usermod -a -G memes memesreel  # pour LIRE trades.jsonl et state.json du papier
chown -R memes:memes "$D"
chmod 750 "$D"
chmod 750 "$D/data"
chmod 600 "$D/jeton"
[ -f "$D/grpc.env" ] && chmod 600 "$D/grpc.env"
mkdir -p "$D/maj"
[ -f "$D/maj/etat.json" ] || printf '{"version": "%s", "seq": %s}\n' "$VERSION" "$SEQ" > "$D/maj/etat.json"
python3 - "$D/maj/etat.json" "$VERSION" "$SEQ" <<'PY'
import json, sys
p, v, seq = sys.argv[1], sys.argv[2], int(sys.argv[3])
e = json.load(open(p))
if seq >= e.get("seq", 0):  # installation manuelle plus récente que la dernière automatique : elle fait foi
    e.update(version=v, seq=seq)
    e.pop("en_cours", None)
json.dump(e, open(p, "w"), indent=1)
PY
chown -R memes:memes "$D/maj"
SANDBOX="User=memes
Group=memes
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ReadWritePaths=$D
InaccessiblePaths=-/opt/g15 -/root -/etc/shadow -$R/wallet.json
CapabilityBoundingSet=
RestrictSUIDSGID=yes"
SANDBOX_REEL="User=memesreel
Group=memesreel
SupplementaryGroups=memes
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ReadWritePaths=$R/data
InaccessiblePaths=-/opt/g15 -/root -/etc/shadow -$D/jeton -$D/grpc.env -$D/.venv
CapabilityBoundingSet=
RestrictSUIDSGID=yes"
cat > /etc/systemd/system/memes-paper.service <<UNIT
[Unit]
Description=Test papier memecoins (aucun ordre réel)
After=network.target

[Service]
WorkingDirectory=$D
ExecStart=$PY $D/memes_paper.py --dir $D/data --bank 10000
Restart=always
$SANDBOX

[Install]
WantedBy=multi-user.target
UNIT
cat > /etc/systemd/system/memes-web.service <<UNIT
[Unit]
Description=Serveur web du test papier memecoins (lecture + dépôts des IA avec jeton)
After=network.target

[Service]
WorkingDirectory=$D
ExecStart=/usr/bin/python3 $D/serveur.py --dir $D/data --port 8787
Restart=always
$SANDBOX

[Install]
WantedBy=multi-user.target
UNIT
# test réel (05/11) : copie la caisse « ia » sur un portefeuille dédié ; ne fait rien tant que wallet.json n'existe pas.
# 06/11 : déplacé sous l'utilisateur memesreel (clé, réglage et état), avec son propre Python que memes ne peut modifier
systemctl stop memes-reel 2>/dev/null || true
for f in wallet.json reel.json STOP_REEL; do
  [ -f "$D/$f" ] && [ ! -e "$R/$f" ] && mv "$D/$f" "$R/$f"
done
for f in reel.jsonl reel_etat.json; do
  [ -f "$D/data/$f" ] && [ ! -L "$D/data/$f" ] && [ ! -e "$R/data/$f" ] && mv "$D/data/$f" "$R/data/$f"
  [ -e "$R/data/$f" ] || : > "$R/data/$f"
  ln -sfn "$R/data/$f" "$D/data/$f"  # la page et le serveur continuent de les lire au même endroit
done
[ -s "$R/data/reel_etat.json" ] || rm -f "$R/data/reel_etat.json"  # vide = premier lancement du test réel
[ -f "$D/wallet.json" ] && { echo "ARRÊT : un wallet.json existe aux deux endroits, rien n'est écrasé ; à régler à la main"; exit 1; }
[ -f "$R/reel.json" ] || printf '%s\n' '{"actif": true, "mise_usd": 2, "max_positions": 3, "max_achats": 20, "plancher": 0.5, "caisse": "ia"}' > "$R/reel.json"
PYR=/usr/bin/python3
if [ ! -x "$R/.venv/bin/python" ]; then python3 -m venv "$R/.venv" 2>/dev/null || true; fi
if [ -x "$R/.venv/bin/python" ] && "$R/.venv/bin/pip" install -q --disable-pip-version-check solders; then
  PYR="$R/.venv/bin/python"
else
  echo "test réel : solders introuvable, le service attendra"
fi
chown root:root "$R/reel.py" && chmod 644 "$R/reel.py"
[ -d "$R/.venv" ] && chown -R root:root "$R/.venv"
chown memesreel:memes "$R" "$R/data" && chmod 750 "$R" "$R/data"
chown -R memesreel:memes "$R/data" && chmod 640 "$R/data/"* 2>/dev/null || true
chown root:memesreel "$R/reel.json" && chmod 640 "$R/reel.json"
[ -f "$R/wallet.json" ] && chown memesreel:memesreel "$R/wallet.json" && chmod 600 "$R/wallet.json"
cat > /etc/systemd/system/memes-reel.service <<UNIT
[Unit]
Description=Test réel à petites sommes (copie de la caisse papier ia, portefeuille dédié, utilisateur à part)
After=network.target memes-paper.service

[Service]
WorkingDirectory=$R
ExecStart=$PYR $R/reel.py --dir $D/data --sortie $R/data
Restart=always
RestartSec=20
UMask=0027
$SANDBOX_REEL

[Install]
WantedBy=multi-user.target
UNIT
# mises à jour automatiques du code de recherche (06/11) : toutes les 10 min, sous l'utilisateur memes
cat > /etc/systemd/system/memes-maj.service <<UNIT
[Unit]
Description=Mise à jour automatique du code de recherche du test papier (testée, avec retour arrière)

[Service]
Type=oneshot
WorkingDirectory=$D
ExecStart=/usr/bin/python3 $L/maj_auto.py
TimeoutStartSec=900
$SANDBOX
UNIT
cat > /etc/systemd/system/memes-maj.timer <<UNIT
[Unit]
Description=Mise à jour automatique du test papier toutes les 10 min

[Timer]
OnBootSec=5min
OnUnitActiveSec=10min

[Install]
WantedBy=timers.target
UNIT
systemctl daemon-reload
systemctl enable -q memes-reel 2>/dev/null || true
systemctl enable -q --now memes-maj.timer
systemctl restart memes-web memes-paper memes-reel
sleep 3
systemctl is-active memes-web memes-paper memes-reel memes-maj.timer
echo "utilisateur du test réel : $(systemctl show -p User --value memes-reel)"
[ -f "$R/wallet.json" ] && echo "clé : $(stat -c '%U:%G %a' "$R/wallet.json") (doit être memesreel:memesreel 600)"
echo "memes dans le groupe memesreel ? $(id -nG memes | tr ' ' '\n' | grep -qx memesreel && echo OUI, ANORMAL || echo non, ok)"
echo "utilisateur des services : $(systemctl show -p User --value memes-paper)"
[ -f "$D/grpc.env" ] && echo "gRPC : grpc.env présent" || echo "gRPC : pas de grpc.env (suivi GeckoTerminal toutes les 15 s)"
echo "mise à jour terminée (version $VERSION)"
