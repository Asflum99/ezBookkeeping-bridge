from functools import lru_cache

from fastapi import APIRouter, Depends

from config import logger
from repositories.user_repository import UserRepository
from routers.telegram.photo import handle_photo
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

    if payload.message.photo:
        return await handle_photo(payload, user_repo)

    logger.info(f"Update {payload.update_id} ignored: no photo or text.")
    return {"status": "success", "detail": "Unsupported message type"}
