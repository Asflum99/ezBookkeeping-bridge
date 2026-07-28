import os

import httpx

from config import logger

settings = {}


def init_config():
    settings["token"] = os.getenv("TELEGRAM_BOT_TOKEN")
    settings["allowed_users"] = {
        int(uid) for uid in os.getenv("ALLOWED_USERS", "").split(",") if uid.strip()
    }


def send_telegram_message(token: str, chat_id: int, texto: str):
    """Send a text message to the user."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto}
    try:
        with httpx.Client() as client:
            client.post(url, json=payload)
    except Exception:
        logger.exception("❌ Failed to send Telegram message:")
