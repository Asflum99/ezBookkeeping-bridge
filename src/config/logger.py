import logging
import os
from logging.handlers import RotatingFileHandler

RUTA_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_LOGS = os.path.join(RUTA_RAIZ, "logs")

os.makedirs(CARPETA_LOGS, exist_ok=True)

ARCHIVO_LOG = os.path.join(CARPETA_LOGS, "bot.log")

LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL_NUMERIC = getattr(logging, LOG_LEVEL_STR, logging.INFO)

file_handler = RotatingFileHandler(
    ARCHIVO_LOG,
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)

stream_handler = logging.StreamHandler()

logging.basicConfig(
    level=LOG_LEVEL_NUMERIC,
    format="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[file_handler, stream_handler],
)

logger = logging.getLogger("bot_finanzas")
logger.setLevel(LOG_LEVEL_NUMERIC)
