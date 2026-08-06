from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException

from config import ALLOWED_USERS, TELEGRAM_BOT_TOKEN, logger
from repositories.user_repository import UserRepository
from routers.telegram.accounts import handle_update_accounts
from routers.telegram.photo import handle_photo
from routers.telegram.utils import send_telegram_message
from schemas import TelegramUpdate

router = APIRouter(prefix="/webhook/telegram")


@lru_cache(1)
def get_user_repository() -> UserRepository:
    """FastAPI dependency: returns singleton UserRepository instance."""
    return UserRepository()


@router.post("/")
async def webhook(
    payload: TelegramUpdate,
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Single webhook endpoint for Telegram updates."""
    if not payload.message:
        logger.info(f"Update {payload.update_id} ignored: no message.")
        return {"status": "success", "detail": "No message"}

    user_id = payload.message.from_user.id
    chat_id = payload.message.chat.id

    if user_id not in ALLOWED_USERS:
        logger.warning(f"Access denied for Telegram ID: {user_id}")
        raise HTTPException(status_code=403, detail="Unauthorized access")

    user_info = user_repo.get_user(user_id)
    if not user_info:
        send_telegram_message(
            TELEGRAM_BOT_TOKEN,
            chat_id,
            "No estás registrado en el sistema del bot financiero. Pídele al administrador que te agregue.",
        )
        return {"status": "success", "detail": "Unregistered user"}

    if payload.message.photo:
        return await handle_photo(payload, user_info, chat_id)

    if payload.message.text:
        return await handle_update_accounts(payload, user_info, chat_id, user_repo)

    logger.info(f"Update {payload.update_id} ignored: no photo or text.")
    return {"status": "success", "detail": "Unsupported message type"}
