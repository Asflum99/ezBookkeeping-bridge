from collections.abc import Awaitable, Callable
from typing import cast

from config import logger, settings
from repositories.user_repository import UserRepository
from routers.telegram.utils import send_telegram_message
from schemas import TelegramMessage, TelegramUpdate
from services.ezbookkeeping_service import get_user_accounts, get_user_categories


async def _handle_sync_remote_data(
    payload: TelegramUpdate,
    user_info: dict,
    chat_id: int,
    fetch_fn: Callable[[str], Awaitable[list[dict] | None]],
    sync_fn: Callable[[int, list[dict]], dict],
    label: str,
    label_es: str,
    error_msg: str,
) -> dict:
    """Generic handler: fetch remote data, sync to local DB, notify user."""
    token = settings.telegram_bot_token
    message = cast(TelegramMessage, payload.message)
    user_id = message.from_user.id

    logger.info(f"Processing {label} update for user {user_id}")

    remote_items = await fetch_fn(user_info["ez_token"])
    if remote_items is None:
        logger.error(f"Failed to fetch remote {label} for user {user_id}")
        send_telegram_message(token, chat_id, error_msg)
        return {"status": "success", "detail": "API error"}

    result = sync_fn(user_id, remote_items)

    added = result["added"]
    removed = result["removed"]
    updated = result["updated"]
    logger.info(
        f"{label} synced for user {user_id}: +{len(added)} -{len(removed)} ~{len(updated)}"
    )

    lines = [f"{label_es} actualizadas: +{len(added)} -{len(removed)} ~{len(updated)}"]
    if added:
        lines.append(f"Añadidas: {', '.join(item['name'] for item in added)}")
    if removed:
        lines.append(f"Eliminadas: {', '.join(removed)}")
    if updated:
        renamed = [f"{u['old_name']} → {u['new_name']}" for u in updated]
        lines.append(f"Renombradas: {', '.join(renamed)}")

    send_telegram_message(token, chat_id, "\n".join(lines))
    return {"status": "success", "detail": f"{label} synced"}


async def handle_update_accounts(
    payload: TelegramUpdate,
    user_info: dict,
    chat_id: int,
    user_repo: UserRepository,
) -> dict:
    return await _handle_sync_remote_data(
        payload,
        user_info,
        chat_id,
        fetch_fn=get_user_accounts,
        sync_fn=user_repo.sync_accounts,
        label="accounts",
        label_es="Cuentas",
        error_msg="Error al obtener tus cuentas de ezBookkeeping. Inténtalo de nuevo.",
    )


async def handle_update_categories(
    payload: TelegramUpdate,
    user_info: dict,
    chat_id: int,
    user_repo: UserRepository,
) -> dict:
    return await _handle_sync_remote_data(
        payload,
        user_info,
        chat_id,
        fetch_fn=get_user_categories,
        sync_fn=user_repo.sync_categories,
        label="categories",
        label_es="Categorías",
        error_msg="Error al obtener tus categorías de ezBookkeeping. Inténtalo de nuevo.",
    )
