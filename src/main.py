import os
import sys

from fastapi import FastAPI

from config.logger import logger
from routers.telegram import init_config
from routers.telegram import router as telegram_router

# ==========================================
# Global configuration
# ==========================================

telegram_bot_token_raw = os.getenv("TELEGRAM_BOT_TOKEN")
usuarios_raw = os.getenv("USUARIOS_PERMITIDOS")

if not telegram_bot_token_raw or not usuarios_raw:
    logger.critical(
        "❌ Missing BOT_TOKEN or ALLOWED_USERS environment variables"
    )
    sys.exit(1)

TELEGRAM_BOT_TOKEN = telegram_bot_token_raw
ALLOWED_USERS = set(int(uid.strip()) for uid in usuarios_raw.split(","))

init_config(TELEGRAM_BOT_TOKEN, ALLOWED_USERS)

app = FastAPI()

app.include_router(telegram_router)


# ==========================================
# Endpoints
# ==========================================


@app.get("/")
def health_check():
    return {"status": "ok"}
