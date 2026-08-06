import sys

from fastapi import FastAPI

from config import logger, settings
from routers.telegram.webhook import router as telegram_router

# ==========================================
# Global configuration
# ==========================================

if not settings.telegram_bot_token or not settings.allowed_users_raw:
    logger.critical("❌ Missing BOT_TOKEN or ALLOWED_USERS environment variables")
    sys.exit(1)

app = FastAPI(redirect_slashes=False)

app.include_router(telegram_router)


# ==========================================
# Endpoints
# ==========================================


@app.get("/")
def health_check():
    return {"status": "ok"}
