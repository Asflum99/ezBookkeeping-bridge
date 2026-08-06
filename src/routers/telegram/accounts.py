from typing import cast

from config import logger, settings
from repositories.user_repository import UserRepository
from routers.telegram.utils import send_telegram_message
from schemas import TelegramMessage, TelegramUpdate
from services.ezbookkeeping_service import get_user_accounts


async def handle_update_accounts(
    payload: TelegramUpdate,
    user_info: dict,
    chat_id: int,
    user_repo: UserRepository,
) -> dict:
    """Sync user_accounts with ezBookkeeping remote accounts."""
    token = settings.telegram_bot_token
    message = cast(TelegramMessage, payload.message)
    user_id = message.from_user.id

    remote_accounts = await get_user_accounts(user_info["ez_token"])
    if remote_accounts is None:
        send_telegram_message(
            token,
            chat_id,
            "Error al obtener tus cuentas de ezBookkeeping. Inténtalo de nuevo.",
        )
        return {"status": "success", "detail": "API error"}

    result = user_repo.sync_accounts(user_id, remote_accounts)

    added = len(result["added"])
    removed = len(result["removed"])
    send_telegram_message(
        token,
        chat_id,
        f"Cuentas actualizadas: +{added} -{removed}",
    )

    return {"status": "success", "detail": "Accounts synced"}
