from typing import Any

from config.logger import logger
from services.telegram_service import send_telegram_message
from services.user_service import get_user_configuration


def verify_user_registration(
    bot_token: str, user_id: int, chat_id: int
) -> dict[str, Any]:
    """
    Verifies if a user is registered in the system.
    If they are not found, sends an alert message via Telegram and returns an empty dict.
    """
    user_info = get_user_configuration(user_id)
    logger.debug(f"Configuration recovered for Telegram ID ({user_id}): {user_info}")

    if not user_info:
        logger.warning(f"🚫 Unregistered user attempt for Telegram ID: {user_id}")

        send_telegram_message(
            bot_token,
            chat_id,
            "⛔ No estás registrado en el sistema del bot financiero. Pídele al administrador que te agregue.",
        )
        return {}

    return user_info
