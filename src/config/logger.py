import logging
import os
from logging.handlers import RotatingFileHandler

import colorlog

RUTA_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_LOGS = os.path.join(RUTA_RAIZ, "logs")
os.makedirs(CARPETA_LOGS, exist_ok=True)
ARCHIVO_LOG = os.path.join(CARPETA_LOGS, "bot.log")

LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO").upper().strip()
NIVELES = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
LOG_LEVEL_NUMERIC = NIVELES.get(LOG_LEVEL_STR, logging.INFO)

# Configuración de rotación y formato para el archivo log
file_handler = RotatingFileHandler(
    ARCHIVO_LOG, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
file_formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
file_handler.setFormatter(file_formatter)

# Configuración para lo que se imprimirá en la terminal/consola
stream_handler = logging.StreamHandler()
color_formatter = colorlog.ColoredFormatter(
    # El '%(log_color)s' define dónde empieza el color según el nivel
    # Usamos '%(purple)s' fijo para la ubicación del archivo para que se vea ordenado
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

# Configuración del logger
logging.basicConfig(
    level=LOG_LEVEL_NUMERIC,
    handlers=[file_handler, stream_handler],
)

logger = logging.getLogger("bot_finanzas")
logger.setLevel(LOG_LEVEL_NUMERIC)
