#!/bin/sh
# Mise à jour du test papier memecoins sur le VPS (ne touche à rien d'autre, notamment pas à /opt/g15).
# Usage : curl -fsSL <url>/installer.sh | sh -s JETON
# Le prix en direct par gRPC s'active si /opt/memes_paper/grpc.env contient GRPC_ENDPOINT=... et GRPC_TOKEN=...
set -e
[ -n "$1" ] || { echo "usage : sh installer.sh JETON"; exit 1; }
D=/opt/memes_paper
U=https://raw.githubusercontent.com/liitlec/Copybot-Crypto/claude/polymarket-weather-sigma-resolution-olv0bs/copy_sim/memes
cd "$D"
mkdir -p yproto
for f in memes_paper.py apprend.py serveur.py flux.py yproto/__init__.py yproto/geyser_pb2.py yproto/geyser_pb2_grpc.py \
         yproto/solana_storage_pb2.py yproto/solana_storage_pb2_grpc.py; do
  curl -fsSL -o "$f.new" "$U/$f" && mv "$f.new" "$f"
done
umask 077
printf '%s\n' "$1" > "$D/jeton"
umask 022
# environnement Python à part pour le gRPC (grpcio, protobuf récent) ; en cas d'échec, le test tourne sans gRPC
PY=/usr/bin/python3
if [ ! -x "$D/.venv/bin/python" ]; then
  python3 -m venv "$D/.venv" 2>/dev/null || { apt-get install -y -qq python3-venv >/dev/null 2>&1 && python3 -m venv "$D/.venv"; } || true
fi
if [ -x "$D/.venv/bin/python" ] && "$D/.venv/bin/pip" install -q --disable-pip-version-check grpcio protobuf; then
  PY="$D/.venv/bin/python"
else
  echo "gRPC : installation de grpcio impossible, le test continue avec GeckoTerminal toutes les 15 s"
fi
cat > /etc/systemd/system/memes-paper.service <<UNIT
[Unit]
Description=Test papier memecoins (aucun ordre réel)
After=network.target

[Service]
WorkingDirectory=$D
ExecStart=$PY $D/memes_paper.py --dir $D/data --bank 10000
Restart=always

[Install]
WantedBy=multi-user.target
UNIT
cat > /etc/systemd/system/memes-web.service <<UNIT
[Unit]
Description=Serveur web du test papier memecoins (lecture + dépôts des IA avec jeton)
After=network.target

[Service]
ExecStart=/usr/bin/python3 $D/serveur.py --dir $D/data --port 8787
Restart=always

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl restart memes-web memes-paper
sleep 2
systemctl is-active memes-web memes-paper
[ -f "$D/grpc.env" ] && echo "gRPC : grpc.env présent" || echo "gRPC : pas de grpc.env (suivi GeckoTerminal toutes les 15 s)"
echo "mise à jour terminée"
