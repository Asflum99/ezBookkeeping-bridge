import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

import colorlog

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ACCOUNTS_JSON_PATH = PROJECT_ROOT / "data" / "cuentas.json"
DATABASE_PATH = PROJECT_ROOT / "data" / "bot.db"
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "bot.log"
PROMPT_TEMPLATE_PATH = PROJECT_ROOT / "src" / "templates" / "voucher_prompt.md"
LLM_MODEL = os.getenv("LLM_MODEL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or ""
ALLOWED_USERS = {
    int(uid) for uid in os.getenv("ALLOWED_USERS", "").split(",") if uid.strip()
}

SUPPORTED_PROVIDERS = {"groq", "openai", "anthropic", "gemini"}

LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO").upper().strip()
LOG_LEVEL_NUMERIC = getattr(logging, LOG_LEVEL_STR, logging.INFO)

# Log file rotation config
file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
file_formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
file_handler.setFormatter(file_formatter)

# Console output config
stream_handler = logging.StreamHandler()
color_formatter = colorlog.ColoredFormatter(
    # '%(log_color)s' sets color by level
    # '%(purple)s' is fixed for file location to keep it tidy
    fmt="%(log_color)s[%(asctime)s] [%(levelname)s]%(reset)s %(purple)s[%(filename)s:%(lineno)d]%(reset)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    },
)
stream_handler.setFormatter(color_formatter)

# Logger configuration
logging.basicConfig(
    level=LOG_LEVEL_NUMERIC,
    handlers=[file_handler, stream_handler],
)

logger = logging.getLogger("bot_finanzas")

if not LLM_MODEL:
    logger.critical(
        "❌ CRITICAL CONFIGURATION ERROR: 'LLM_MODEL' environment variable is not defined or is empty. "
        "Please specify a valid vision model in your mise.local.toml."
    )
    raise RuntimeError("Missing required environment variable: LLM_MODEL")

EZBOOKKEEPING_URL = os.getenv("EZBOOKKEEPING_URL")
if not EZBOOKKEEPING_URL:
    logger.critical(
        "❌ ERROR CRÍTICO: La variable de entorno EZBOOKKEEPING_URL no está configurada."
    )
    raise RuntimeError("Missing required environment variable: EZBOOKKEEPING_URL")

LLM_PROVIDER = os.getenv("LLM_PROVIDER")
if not LLM_PROVIDER:
    logger.critical("❌ CRITICAL CONFIGURATION ERROR: 'LLM_PROVIDER' not configured")
    raise RuntimeError("Missing required environment variable: LLM_PROVIDER")

if LLM_PROVIDER not in SUPPORTED_PROVIDERS:
    logger.critical(
        f"❌ CRITICAL CONFIGURATION ERROR: 'LLM_PROVIDER' value '{LLM_PROVIDER}' is not supported. "
        f"Must be one of: {', '.join(sorted(SUPPORTED_PROVIDERS))}"
    )
    raise RuntimeError(f"Unsupported LLM provider: {LLM_PROVIDER}")

_PROVIDER_API_KEY_MAP = {
    "groq": "GROQ_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GOOGLE_API_KEY",
}

LLM_API_KEY = os.getenv(_PROVIDER_API_KEY_MAP[LLM_PROVIDER])
if not LLM_API_KEY:
    logger.critical(
        f"❌ CRITICAL CONFIGURATION ERROR: API key for provider '{LLM_PROVIDER}' "
        f"({_PROVIDER_API_KEY_MAP[LLM_PROVIDER]}) is not set."
    )
    raise RuntimeError(
        f"Missing API key for LLM provider: {_PROVIDER_API_KEY_MAP[LLM_PROVIDER]}"
    )

try:
    with open(PROMPT_TEMPLATE_PATH, encoding="utf-8") as f:
        SYSTEM_PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    logger.critical(
        f"❌ CRITICAL: System prompt template not found at {PROMPT_TEMPLATE_PATH}. "
        "The application cannot start without it."
    )
    raise
