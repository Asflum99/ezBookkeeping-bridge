from fastapi import APIRouter

from routers.telegram.webhook import router as _webhook_router

router = APIRouter(prefix="/webhook/telegram")
router.include_router(_webhook_router)

__all__ = ["router", "init_config"]

# Re-export init_config for main.py
from routers.telegram.utils import init_config  # noqa: E402, F401
