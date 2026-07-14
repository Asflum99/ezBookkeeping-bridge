import os
import sys
from typing import List

from fastapi import FastAPI, HTTPException

from config.logger import logger
from core.file_manager import delete_local_file, download_telegram_photo
from schemas import TelegramMessage, TelegramPhotoSize, TelegramUpdate
from services.auth_service import verify_user_registration
from services.ezbookkeeping_service import register_transaction
from services.groq_service import process_expense_with_ai
from services.guardian import validate_and_extract_message
from services.telegram_service import send_telegram_message
from services.user_service import get_user_categories
from utils.formatter import (
    prepare_confirmation_message,
    validate_and_sanitize_voucher_data,
)

# ==========================================
# Configuraciones globales
# ==========================================

telegram_bot_token_raw = os.getenv("TELEGRAM_BOT_TOKEN")
usuarios_raw = os.getenv("USUARIOS_PERMITIDOS")

if not telegram_bot_token_raw or not usuarios_raw:
    logger.critical(
        "❌ Falta configurar el BOT_TOKEN o la lista de USUARIOS_PERMITIDOS"
    )
    sys.exit(1)

TELEGRAM_BOT_TOKEN = telegram_bot_token_raw
ALLOWED_USERS = set(int(uid.strip()) for uid in usuarios_raw.split(","))

app = FastAPI()

# ==========================================
# Funciones auxiliares
# ==========================================


def validate_access_and_content(
    message: TelegramMessage, user_id: int, chat_id: int
) -> bool:
    """
    Validates if the user is in the whitelist and has sent a photo.
    Returns True if valid, False if the flow should be halted.
    """
    if user_id not in ALLOWED_USERS:
        logger.warning(f"🚫 Access denied attempt for Telegram ID: {user_id}")
        raise HTTPException(status_code=403, detail="Unauthorized access")

    if not message.photo:
        logger.info(f"💡 User {user_id} sent a message without photos.")

        send_telegram_message(
            TELEGRAM_BOT_TOKEN,
            chat_id,
            "Por ahora solo puedo recibir fotos de vouchers o boletas para registrar tus gastos. 📸",
        )
        return False

    return True


def get_optimal_photo_id(photo_sizes: List[TelegramPhotoSize]) -> str:
    """
    Extracts the file_id of the highest resolution photo from the list.
    Telegram always appends the largest image size at the end of the array.
    """
    if not photo_sizes:
        logger.warning("Empty photo sizes list received. Cannot extract file_id.")
        raise ValueError("Photo sizes list is empty.")

    # Grab the last element (highest resolution)
    optimal_photo = photo_sizes[-1]
    file_id = optimal_photo.file_id

    logger.debug(
        f"Optimal photo detected for processing: {file_id} "
        f"({optimal_photo.width}x{optimal_photo.height}px)"
    )
    return file_id


# ==========================================
# Endpoints
# ==========================================


@app.get("/")
def health_check():
    return {"status": "ok"}


# TODO: Cambiar el path a /webhook/telegram
@app.post("/webhook")
async def telegram_webhook(payload: TelegramUpdate):
    message = validate_and_extract_message(payload)
    if isinstance(message, dict):
        logger.info(f"Webhook execution halted: {message.get('detail')}")
        return message

    chat_id = message.chat.id
    user_id = message.from_user.id

    if not validate_access_and_content(message, user_id, chat_id):
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

    file_id = get_optimal_photo_id(message.photo)

    user_info = verify_user_registration(TELEGRAM_BOT_TOKEN, user_id, chat_id)
    if not user_info:
        return

    local_photo_path = None
    try:
        local_photo_path = await download_telegram_photo(TELEGRAM_BOT_TOKEN, file_id)

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
                TELEGRAM_BOT_TOKEN,
                chat_id,
                prepare_confirmation_message(sanitized_data),
            )
        else:
            send_telegram_message(
                TELEGRAM_BOT_TOKEN,
                chat_id,
                "⚠️ Error al guardar en tu cuenta de ezBookkeeping.",
            )

    except FileNotFoundError:
        logger.critical(
            "⚠️ Notificando al usuario sobre fallo del sistema interno (Falta de Prompt)."
        )
        send_telegram_message(
            TELEGRAM_BOT_TOKEN,
            chat_id,
            "⚙️ Lo siento, nuestro sistema interno está experimentando fallas técnicas en este momento. Por favor, vuelve a intentarlo más tarde. 🙏",
        )

    except Exception:
        logger.critical("❌ Error durante el procesamiento general:")
        send_telegram_message(
            TELEGRAM_BOT_TOKEN,
            chat_id,
            "Hubo un problema al procesar la imagen de tu voucher. Inténtalo de nuevo. 😞",
        )

    finally:
        if local_photo_path:
            logger.info("Iniciando proceso de borrado de la foto del voucher")
            delete_local_file(local_photo_path)
