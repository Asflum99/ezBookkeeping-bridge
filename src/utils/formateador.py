import logging
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

logger = logging.getLogger("bot_finanzas")


def validate_and_sanitize_voucher_data(raw_data: dict[str, Any]) -> dict[str, Any]:
    """
    Validates the 'date_time' field inside the LLM raw data dictionary.
    If the date is invalid, out of the 2-week range, or missing, it falls back
    to the current system time.

    Returns the updated dictionary with the sanitized ISO date string.
    """
    sanitized_data = raw_data.copy()

    now = datetime.now()
    two_weeks_ago = now - timedelta(days=14)
    fallback_date_str = now.strftime("%Y-%m-%d %H:%M:%S")

    extracted_date_str = sanitized_data.get("date_time")

    if not extracted_date_str:
        logger.warning(
            "No 'date_time' field found in LLM raw data. Falling back to current system time."
        )
        sanitized_data["date_time"] = fallback_date_str
        return sanitized_data

    try:
        extracted_date = datetime.strptime(extracted_date_str, "%Y-%m-%d %H:%M:%S")

        if two_weeks_ago <= extracted_date <= now:
            logger.debug(f"Voucher date successfully validated: {extracted_date_str}")
            return sanitized_data

        logger.warning(
            f"Extracted date '{extracted_date_str}' is out of the 2-week range. "
            f"Sanitizing to current system time: {fallback_date_str}"
        )
        sanitized_data["date_time"] = fallback_date_str

    except (ValueError, TypeError) as e:
        logger.warning(
            f"Failed to parse extracted date '{extracted_date_str}'. "
            f"Error: {e}. Sanitizing to current system time: {fallback_date_str}"
        )
        sanitized_data["date_time"] = fallback_date_str

    return sanitized_data


def preparar_mensaje_confirmacion(datos_crudos: dict) -> str:
    """
    Toma los datos originales de la IA (legibles) y arma un mensaje
    estético y amigable para el usuario en Telegram.
    """
    logger.info("Iniciando limpieza de datos para enviárselo al usuario por Telegram")

    monto = datos_crudos.get("monto", "0.00")
    descripcion = datos_crudos.get("comentario", "Desconocido")
    fecha = datos_crudos.get("fecha_hora")

    try:
        if fecha:
            timestamp_segundos = float(fecha)
            fecha_objeto = datetime.fromtimestamp(
                timestamp_segundos, tz=ZoneInfo("America/Lima")
            )
            fecha_bonita = fecha_objeto.strftime("%d-%m-%Y %I:%M %p").lower()
        else:
            logger.warning("No se encontró fecha, usando valor placeholder")
            fecha_bonita = "No detectada"
    except Exception as e:
        logger.warning(f"⚠️ No se pudo formatear el timestamp para el usuario: {e}")
        fecha_bonita = "Formato inválido"

    medio_pago_raw = datos_crudos.get("medio_pago", "")
    medios_traducidos = {
        "billetera_digital": "📱 Billetera Digital (Yape/Plin/Débito)",
        "tarjeta_credito": "💳 Tarjeta de Crédito",
    }
    medio_pago_bonito = medios_traducidos.get(medio_pago_raw, "❓ Desconocido")

    categoria_bonita = datos_crudos.get("categoria", "❓ Desconocida")

    mensaje = (
        f"✅ ¡Gasto registrado con éxito!\n\n"
        f"💰 Monto: S/. {monto}\n"
        f"📝 Descripción: {descripcion}\n"
        f"📅 Fecha: {fecha_bonita}\n"
        f"💳 Método: {medio_pago_bonito}\n"
        f"🏷️ Categoría: {categoria_bonita}"
    )
    return mensaje
