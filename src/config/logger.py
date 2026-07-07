import logging
import os
from logging.handlers import RotatingFileHandler

RUTA_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_LOGS = os.path.join(RUTA_RAIZ, "logs")

os.makedirs(CARPETA_LOGS, exist_ok=True)

ARCHIVO_LOG = os.path.join(CARPETA_LOGS, "bot.log")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

handler = RotatingFileHandler(
    ARCHIVO_LOG,
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(ARCHIVO_LOG, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("bot_finanzas")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
