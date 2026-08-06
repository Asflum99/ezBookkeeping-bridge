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

    logger.info(f"Processing accounts update for user {user_id}")

    remote_accounts = await get_user_accounts(user_info["ez_token"])
    if remote_accounts is None:
        logger.error(f"Failed to fetch remote accounts for user {user_id}")
        send_telegram_message(
            token,
            chat_id,
            "Error al obtener tus cuentas de ezBookkeeping. Inténtalo de nuevo.",
        )
        return {"status": "success", "detail": "API error"}

    result = user_repo.sync_accounts(user_id, remote_accounts)

    added = result["added"]
    removed = result["removed"]
    updated = result["updated"]
    logger.info(f"Accounts synced for user {user_id}: +{len(added)} -{len(removed)} ~{len(updated)}")

    lines = [f"Cuentas actualizadas: +{len(added)} -{len(removed)} ~{len(updated)}"]
    if added:
        lines.append(f"Añadidas: {', '.join(acc['name'] for acc in added)}")
    if removed:
        lines.append(f"Eliminadas: {', '.join(removed)}")
    if updated:
        renamed = [f"{u['old_name']} → {u['new_name']}" for u in updated]
        lines.append(f"Renombradas: {', '.join(renamed)}")

    send_telegram_message(token, chat_id, "\n".join(lines))

    return {"status": "success", "detail": "Accounts synced"}
