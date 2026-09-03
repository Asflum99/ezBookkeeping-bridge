from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from config import logger, settings
from repositories.user_repository import UserRepository
from routers.telegram.photo import handle_photo
from routers.telegram.sync import handle_update_accounts, handle_update_categories
from routers.telegram.utils import send_telegram_message
from schemas import TelegramUpdate

router = APIRouter(prefix="/webhook/telegram")


@lru_cache(1)
def get_user_repository() -> UserRepository:
    """FastAPI dependency: returns singleton UserRepository instance."""
    return UserRepository()


UserRepoDep = Annotated[UserRepository, Depends(get_user_repository)]


@router.post("/")
async def webhook(
    payload: TelegramUpdate,
    user_repo: UserRepoDep,
):
    """Single webhook endpoint for Telegram updates."""
    if not payload.message:
        logger.info(f"Update {payload.update_id} ignored: no message.")
        return {"status": "success", "detail": "No message"}

    user_id = payload.message.from_user.id
    chat_id = payload.message.chat.id

    if user_id not in settings.allowed_users:
        logger.warning(f"Access denied for Telegram ID: {user_id}")
        raise HTTPException(status_code=403, detail="Unauthorized access")

    user_info = user_repo.get_user(user_id)
    if not user_info:
        send_telegram_message(
            settings.telegram_bot_token,
            chat_id,
            "No estás registrado en el sistema del bot financiero. Pídele al administrador que te agregue.",
        )
        return {"status": "success", "detail": "Unregistered user"}

    if payload.message.photo:
        return await handle_photo(payload, user_info, chat_id)

    if payload.message.text:
        text = payload.message.text.strip()
        if text == "/update-accounts":
            return await handle_update_accounts(payload, user_info, chat_id, user_repo)
        elif text == "/update-categories":
            return await handle_update_categories(payload, user_info, chat_id, user_repo)
        else:
            logger.info(f"Update {payload.update_id} ignored: unknown command '{text}'")
            return {"status": "success", "detail": "Unknown command"}

    logger.info(f"Update {payload.update_id} ignored: no photo or text.")
    return {"status": "success", "detail": "Unsupported message type"}
