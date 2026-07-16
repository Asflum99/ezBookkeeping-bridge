from typing import List

from fastapi import APIRouter, HTTPException

from config.logger import logger
from schemas import TelegramPhotoSize, TelegramUpdate
from services.auth_service import verify_user_registration
from services.ezbookkeeping_service import register_transaction
from services.groq_service import process_expense_with_ai
from services.guardian_service import validate_and_extract_message
from services.telegram_file_service import delete_local_file, download_telegram_photo
from services.telegram_service import send_telegram_message
from services.user_service import get_user_categories
from utils.formatter import (
    prepare_confirmation_message,
    validate_and_sanitize_voucher_data,
)

router = APIRouter()

_config = {}


def init_config(telegram_bot_token: str, allowed_users: set[int]):
    _config["token"] = telegram_bot_token
    _config["allowed_users"] = allowed_users


def _get_token() -> str:
    return _config["token"]


def _get_allowed_users() -> set[int]:
    return _config["allowed_users"]


def _validate_access_and_content(message, user_id: int, chat_id: int) -> bool:
    if user_id not in _get_allowed_users():
        logger.warning(f"🚫 Access denied attempt for Telegram ID: {user_id}")
        raise HTTPException(status_code=403, detail="Unauthorized access")

    if not message.photo:
        logger.info(f"💡 User {user_id} sent a message without photos.")
        send_telegram_message(
            _get_token(),
            chat_id,
            "Por ahora solo puedo recibir fotos de vouchers o boletas para registrar tus gastos. 📸",
        )
        return False

    return True


def _get_optimal_photo_id(photo_sizes: List[TelegramPhotoSize]) -> str:
    if not photo_sizes:
        logger.warning("Empty photo sizes list received. Cannot extract file_id.")
        raise ValueError("Photo sizes list is empty.")

    optimal_photo = photo_sizes[-1]
    file_id = optimal_photo.file_id

    logger.debug(
        f"Optimal photo detected for processing: {file_id} "
        f"({optimal_photo.width}x{optimal_photo.height}px)"
    )
    return file_id


@router.post("/webhook")
async def telegram_webhook(payload: TelegramUpdate):
    token = _get_token()

    message = validate_and_extract_message(payload)
    if isinstance(message, dict):
        logger.info(f"Webhook execution halted: {message.get('detail')}")
        return message

    chat_id = message.chat.id
    user_id = message.from_user.id

    if not _validate_access_and_content(message, user_id, chat_id):
        return {
            "status": "success",
            "detail": "Contenido no soportado o flujo controlado.",
        }

    if not message.photo:
        logger.info(
            f"No se pudo encontrar imágenes en el mensaje de Telegram (ID: {payload.message})"
        )
        return {
            "status": "success",
            "detail": "No hay imágenes en el mensaje de Telegram.",
        }

    file_id = _get_optimal_photo_id(message.photo)

    user_info = verify_user_registration(token, user_id, chat_id)
    if not user_info:
        return

    local_photo_path = None
    try:
        local_photo_path = await download_telegram_photo(token, file_id)

        user_categories = get_user_categories(user_id)
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
