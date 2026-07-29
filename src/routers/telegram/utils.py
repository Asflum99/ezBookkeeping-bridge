import httpx

from config import logger


def send_telegram_message(token: str, chat_id: int, texto: str):
    """Send a text message to the user."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto}
    try:
        with httpx.Client() as client:
            client.post(url, json=payload)
    except Exception:
        logger.exception("❌ Failed to send Telegram message:")
