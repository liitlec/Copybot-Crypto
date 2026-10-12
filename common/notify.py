"""Alertes Telegram. Variables d'environnement : TELEGRAM_TOKEN (jeton du bot, via @BotFather) et TELEGRAM_CHAT_ID.
Sans ces variables, rien n'est envoye (le texte est seulement affiche)."""
import os

import requests


def telegram(text):
    tok, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not chat:
        return False
    try:
        r = requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                          data={"chat_id": chat, "text": text[:4000]}, timeout=20)
        return r.ok
    except requests.RequestException:
        return False
