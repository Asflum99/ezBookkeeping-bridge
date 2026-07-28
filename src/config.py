import logging
import os
from logging.handlers import RotatingFileHandler

import colorlog

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNTS_JSON_PATH = os.path.join(PROJECT_ROOT, "data", "cuentas.json")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, "bot.log")
LLM_MODEL = os.getenv("LLM_MODEL")

LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO").upper().strip()
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
LOG_LEVEL_NUMERIC = LOG_LEVELS.get(LOG_LEVEL_STR, logging.INFO)

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
logger.setLevel(LOG_LEVEL_NUMERIC)

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
