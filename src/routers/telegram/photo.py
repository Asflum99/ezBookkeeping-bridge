from typing import cast

from config import logger, settings
from formatter import (
    prepare_confirmation_message,
    validate_and_sanitize_voucher_data,
)
from routers.telegram.utils import send_telegram_message
from schemas import TelegramMessage, TelegramPhotoSize, TelegramUpdate
from services.ezbookkeeping_service import register_transaction
from services.llm_service import process_expense_with_ai
from services.telegram_file_service import delete_local_file, download_telegram_photo


async def handle_photo(
    payload: TelegramUpdate,
    user_info: dict,
    chat_id: int,
) -> dict:
    """Process a photo message (voucher)."""
    token = settings.telegram_bot_token
    payload_message = cast(TelegramMessage, payload.message)

    payload_message_photo = cast(list[TelegramPhotoSize], payload_message.photo)
    optimal_photo = payload_message_photo[-1]
    file_id = optimal_photo.file_id
    logger.debug(
        f"Optimal photo detected for processing: {file_id} "
        f"({optimal_photo.width}x{optimal_photo.height}px)"
    )

    local_photo_path = None
    try:
        local_photo_path = await download_telegram_photo(token, file_id)

        user_categories = user_info["categorias"]
        user_accounts_hints = list(user_info.get("cuentas_hints", []))

        raw_llm_data = process_expense_with_ai(
            local_photo_path, user_categories, user_accounts_hints
        )
        sanitized_data = validate_and_sanitize_voucher_data(
            raw_llm_data, user_info, user_accounts_hints, user_categories
        )

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

    except Exception:  # noqa: BLE001
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
