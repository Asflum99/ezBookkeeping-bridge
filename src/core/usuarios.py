import json
import logging
import os

from services.telegram_service import enviar_mensaje_telegram

logger = logging.getLogger("bot_finanzas")


def obtener_configuracion_usuario(user_id: int) -> dict:
    """Busca el token del usuario en cuentas.json"""
    ruta_cuentas = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cuentas.json"
    )
    logger.debug(f"Ruta usada: {ruta_cuentas}")
    try:
        with open(ruta_cuentas, "r", encoding="utf-8") as f:
            cuentas = json.load(f)
            return cuentas.get(str(user_id))
    except Exception:
        logger.exception("❌ Error al leer cuentas.json:")
        return {}


def verificar_registro_usuario(token_bot: str, user_id: int, chat_id: int) -> dict:
    """Busca la configuración del usuario. Si no existe, le notifica por Telegram."""
    user_info = obtener_configuracion_usuario(user_id)
    logger.debug(f"Información recuperada del usuario ({user_id}):\n{user_info}")

    if not user_info:
        logger.warning(
            f"🚫 Usuario no registrado en cuentas.json para el user_id: {user_id}"
        )
        enviar_mensaje_telegram(
            token_bot,
            chat_id,
            "⛔ No estás registrado en el sistema del bot financiero. Pídele al administrador que te agregue.",
        )
        return {}

    return user_info
