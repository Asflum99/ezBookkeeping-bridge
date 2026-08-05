from typing import cast

from fastapi import HTTPException

from config import ALLOWED_USERS, TELEGRAM_BOT_TOKEN, logger
from formatter import (
    prepare_confirmation_message,
    validate_and_sanitize_voucher_data,
)
from repositories.user_repository import UserRepository
from routers.telegram.utils import send_telegram_message
from schemas import TelegramMessage, TelegramPhotoSize, TelegramUpdate
from services.ezbookkeeping_service import register_transaction
from services.llm_service import process_expense_with_ai
from services.telegram_file_service import delete_local_file, download_telegram_photo


async def handle_photo(
    payload: TelegramUpdate,
    user_repo: UserRepository,
) -> dict:
    """Process a photo message (voucher)."""
    token = TELEGRAM_BOT_TOKEN
    payload_message = cast(TelegramMessage, payload.message)
    chat_id = payload_message.chat.id
    user_id = payload_message.from_user.id

    if user_id not in ALLOWED_USERS:
        logger.warning(f"🚫 Access denied attempt for Telegram ID: {user_id}")
        raise HTTPException(status_code=403, detail="Unauthorized access")

    payload_message_photo = cast(list[TelegramPhotoSize], payload_message.photo)
    optimal_photo = payload_message_photo[-1]
    file_id = optimal_photo.file_id
    logger.debug(
        f"Optimal photo detected for processing: {file_id} "
        f"({optimal_photo.width}x{optimal_photo.height}px)"
    )

    user_info = user_repo.get_user(user_id)
    if not user_info:
        send_telegram_message(
            token,
            chat_id,
            "⛔ No estás registrado en el sistema del bot financiero. Pídele al administrador que te agregue.",
        )
        return {"status": "success", "detail": "Unregistered user"}

    local_photo_path = None
    try:
        local_photo_path = await download_telegram_photo(token, file_id)

        user_categories = list(user_info.get("categorias", {}).keys())
        user_accounts_hints = list(user_info.get("cuentas_hints", []))

        raw_llm_data = process_expense_with_ai(
            local_photo_path, user_categories, user_accounts_hints
        )
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
        logger.critical("❌ General processing error")
        send_telegram_message(
            token,
            chat_id,
            "Hubo un problema al procesar la imagen de tu voucher. Inténtalo de nuevo. 😞",
        )

    finally:
        if local_photo_path:
            logger.info("Starting voucher photo cleanup")
            delete_local_file(local_photo_path)

    return {"status": "success", "detail": "Photo processed"}
