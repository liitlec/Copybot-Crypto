#!/bin/sh
# Mise à jour du test papier memecoins sur le VPS. Ne touche pas à /opt/g15 ni au service g15.
# Usage (en root) : curl -fsSL <url>/installer.sh | sh -s JETON
#
# Sécurité : les deux services tournent sous un utilisateur dédié « memes », sans droits root, dans un bac à sable
# systemd qui leur rend /opt/g15 et /root invisibles et le reste du système en lecture seule ; seul /opt/memes_paper
# est modifiable. Les fichiers sont pris à un commit figé (VERSION), pas à la tête de la branche.
# Le prix en direct par gRPC s'active si /opt/memes_paper/grpc.env contient GRPC_ENDPOINT=... et GRPC_TOKEN=...
set -e
[ -n "$1" ] || { echo "usage : sh installer.sh JETON"; exit 1; }
VERSION=a469f0e54e27b0ca4ce5421638baadef8e3063d0
D=/opt/memes_paper
U=https://raw.githubusercontent.com/liitlec/Copybot-Crypto/$VERSION/copy_sim/memes
mkdir -p "$D/yproto" "$D/data"
cd "$D"
for f in memes_paper.py memes_page.py apprend.py serveur.py flux.py reel.py yproto/__init__.py yproto/geyser_pb2.py yproto/geyser_pb2_grpc.py \
         yproto/solana_storage_pb2.py yproto/solana_storage_pb2_grpc.py; do
  curl -fsSL -o "$f.new" "$U/$f" && mv "$f.new" "$f"
done
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
chown -R memes:memes "$D"
chmod 700 "$D"
chmod 600 "$D/jeton"
[ -f "$D/grpc.env" ] && chmod 600 "$D/grpc.env"
SANDBOX="User=memes
Group=memes
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ReadWritePaths=$D
InaccessiblePaths=-/opt/g15 -/root -/etc/shadow
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
# test réel (05/11) : copie la caisse « ia » sur un portefeuille dédié ; ne fait rien tant que wallet.json n'existe pas
[ -f "$D/reel.json" ] || printf '%s\n' '{"actif": true, "mise_usd": 2, "max_positions": 3, "max_achats": 20, "plancher": 0.5, "caisse": "ia"}' > "$D/reel.json"
chown memes:memes "$D/reel.json"
[ -f "$D/wallet.json" ] && chown memes:memes "$D/wallet.json" && chmod 600 "$D/wallet.json"
cat > /etc/systemd/system/memes-reel.service <<UNIT
[Unit]
Description=Test réel à petites sommes (copie de la caisse papier ia, portefeuille dédié)
After=network.target memes-paper.service

[Service]
WorkingDirectory=$D
ExecStart=$PY $D/reel.py --dir $D/data
Restart=always
RestartSec=20
$SANDBOX

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable -q memes-reel 2>/dev/null || true
systemctl restart memes-web memes-paper memes-reel
sleep 3
systemctl is-active memes-web memes-paper memes-reel
echo "utilisateur des services : $(systemctl show -p User --value memes-paper)"
[ -f "$D/grpc.env" ] && echo "gRPC : grpc.env présent" || echo "gRPC : pas de grpc.env (suivi GeckoTerminal toutes les 15 s)"
echo "mise à jour terminée (version $VERSION)"
