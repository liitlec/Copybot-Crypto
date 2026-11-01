#!/bin/sh
# Mise à jour du test papier memecoins sur le VPS (ne touche à rien d'autre, notamment pas à /opt/g15).
# Usage : curl -fsSL <url>/installer.sh | sh -s JETON
set -e
[ -n "$1" ] || { echo "usage : sh installer.sh JETON"; exit 1; }
D=/opt/memes_paper
U=https://raw.githubusercontent.com/liitlec/Copybot-Crypto/claude/polymarket-weather-sigma-resolution-olv0bs/copy_sim/memes
cd "$D"
for f in memes_paper.py apprend.py serveur.py; do curl -fsSL -o "$f.new" "$U/$f" && mv "$f.new" "$f"; done
umask 077
printf '%s\n' "$1" > "$D/jeton"
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
echo "mise à jour terminée"
