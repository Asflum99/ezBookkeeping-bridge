import json
import os
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException

from config import ACCOUNTS_JSON_PATH, logger
from schemas import TelegramUpdate
from services.ezbookkeeping_service import register_transaction
from services.groq_service import process_expense_with_ai
from services.telegram_file_service import delete_local_file, download_telegram_photo
from utils.formatter import (
    prepare_confirmation_message,
    validate_and_sanitize_voucher_data,
)

router = APIRouter()

_config = {}

if not os.path.exists(ACCOUNTS_JSON_PATH):
    logger.error(f"Accounts file not found at path: {ACCOUNTS_JSON_PATH}")
    raise FileNotFoundError

with open(ACCOUNTS_JSON_PATH, "r", encoding="utf-8") as _f:
    _ACCOUNTS_DATA: dict[str, Any] = json.load(_f)


def init_config():
    _config["token"] = os.getenv("TELEGRAM_BOT_TOKEN")
    _config["allowed_users"] = os.getenv("ALLOWED_USERS")


def _get_user_configuration(user_id: int) -> dict[str, Any]:
    """Load user config from cuentas.json. Returns {} if not found."""
    user_config = _ACCOUNTS_DATA.get(str(user_id))
    if not user_config:
        logger.info(f"Unregistered user attempt: {user_id}")
        return {}
    logger.debug(f"Configuration recovered for Telegram ID ({user_id}): {user_config}")
    return user_config


def send_telegram_message(token: str, chat_id: int, texto: str):
    """Send a text message to the user."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto}
    try:
        with httpx.Client() as client:
            client.post(url, json=payload)
    except Exception:
        logger.exception("❌ Failed to send Telegram message:")


@router.post("/webhook")
async def telegram_webhook(payload: TelegramUpdate):
    token = _config["token"]

    if not payload.message or not payload.message.photo:
        logger.info(f"Update {payload.update_id} ignored: no message or no photo.")
        return {
            "status": "success",
            "detail": "Update without supported content",
        }

    chat_id = payload.message.chat.id
    user_id = payload.message.from_user.id

    if user_id not in _config["allowed_users"]:
        logger.warning(f"🚫 Access denied attempt for Telegram ID: {user_id}")
        raise HTTPException(status_code=403, detail="Unauthorized access")

    optimal_photo = payload.message.photo[-1]
    file_id = optimal_photo.file_id
    logger.debug(
        f"Optimal photo detected for processing: {file_id} "
        f"({optimal_photo.width}x{optimal_photo.height}px)"
    )

    user_info = _get_user_configuration(user_id)
    if not user_info:
        send_telegram_message(
            token,
            chat_id,
            "⛔ No estás registrado en el sistema del bot financiero. Pídele al administrador que te agregue.",
        )
        return

    local_photo_path = None
    try:
        local_photo_path = await download_telegram_photo(token, file_id)

        user_categories = list(user_info.get("categorias", {}).keys())
        if not user_categories:
            logger.error(
                f"Cannot process voucher: No categories found for user {user_id}"
            )
            return {
                "status": "success",
                "detail": "Failed to retrieve user categories.",
            }

        raw_llm_data = process_expense_with_ai(local_photo_path, user_categories)
        sanitized_data = validate_and_sanitize_voucher_data(raw_llm_data)

        transaction_registered = await register_transaction(sanitized_data, user_info)

        if transaction_registered:
            send_telegram_message(
                token,
                chat_id,
                prepare_confirmation_message(sanitized_data),
            )
        else:
            send_telegram_message(
                token,
                chat_id,
                "⚠️ Error al guardar en tu cuenta de ezBookkeeping.",
            )

    except FileNotFoundError:
        logger.critical(
            "⚠️ Notificando al usuario sobre fallo del sistema interno (Falta de Prompt)."
        )
        send_telegram_message(
            token,
            chat_id,
            "⚙️ Lo siento, nuestro sistema interno está experimentando fallas técnicas en este momento. Por favor, vuelve a intentarlo más tarde. 🙏",
        )

    except Exception:
        logger.critical("❌ General processing error:")
        send_telegram_message(
            token,
            chat_id,
            "Hubo un problema al procesar la imagen de tu voucher. Inténtalo de nuevo. 😞",
        )

    finally:
        if local_photo_path:
            logger.info("Starting voucher photo cleanup")
            delete_local_file(local_photo_path)
