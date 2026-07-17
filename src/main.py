import os
import sys

from fastapi import FastAPI

from config import logger
from routers.telegram import init_config
from routers.telegram import router as telegram_router

# ==========================================
# Global configuration
# ==========================================

if not os.getenv("TELEGRAM_BOT_TOKEN") or not os.getenv("ALLOWED_USERS"):
    logger.critical("❌ Missing BOT_TOKEN or ALLOWED_USERS environment variables")
    sys.exit(1)

init_config()

app = FastAPI()

app.include_router(telegram_router)


# ==========================================
# Endpoints
# ==========================================


@app.get("/")
def health_check():
    return {"status": "ok"}
