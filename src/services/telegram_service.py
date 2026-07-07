import logging

import httpx

logger = logging.getLogger("bot_finanzas")


def enviar_mensaje_telegram(token_bot: str, chat_id: int, texto: str):
    """Función auxiliar para enviarle un mensaje de texto de vuelta al usuario"""
    url = f"https://api.telegram.org/bot{token_bot}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto}
    try:
        with httpx.Client() as client:
            client.post(url, json=payload)
    except Exception:
        logger.exception("❌ Error al enviar mensaje a Telegram:")
