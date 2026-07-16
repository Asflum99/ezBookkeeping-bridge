from typing import Any

from config.logger import logger
from schemas import TelegramMessage, TelegramUpdate


def validate_and_extract_message(
    payload: TelegramUpdate,
) -> TelegramMessage | dict[str, Any]:
    """
    Validates the Telegram webhook payload infrastructure.
    """
    if not payload.message:
        logger.info(
            f"Telegram update {payload.update_id} does not contain a standard message. Ignoring stream."
        )
        return {
            "status": "success",
            "detail": "Update received but lacks a valid message object.",
        }

    message = payload.message

    if not message.photo:
        logger.info(
            f"Telegram message {message.message_id} from user {message.from_user.id} has no photos."
        )
        return {
            "status": "success",
            "detail": "No image attachments found in the message.",
        }

    logger.debug(
        f"Payload infrastructure successfully validated for message {message.message_id}"
    )
    return message
