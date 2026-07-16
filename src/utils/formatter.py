from datetime import datetime, timedelta
from typing import Any

from config.logger import logger


def validate_and_sanitize_voucher_data(raw_llm_data: dict[str, Any]) -> dict[str, Any]:
    """
    Validates the 'date_time' field inside the LLM raw data dictionary.
    If the date is invalid, out of the 2-week range, or missing, it falls back
    to the current system time.

    Returns the updated dictionary with the sanitized ISO date string.
    """
    sanitized_data = raw_llm_data.copy()

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


def prepare_confirmation_message(sanitized_data: dict[str, Any]) -> str:
    """
    Takes the sanitized LLM data and builds an aesthetically pleasing,
    friendly confirmation message in Spanish for the Telegram user.
    """
    logger.info("Building confirmation message for Telegram UI.")

    amount = sanitized_data.get("amount", "0.00")  # TODO: Revisar
    comment = sanitized_data.get("comment", "Desconocido")
    date_time_str = sanitized_data.get("date_time")

    try:
        if date_time_str:
            parsed_date = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
            formatted_date = parsed_date.strftime("%d-%m-%Y %I:%M %p")
        else:
            logger.warning("No date_time found in sanitized data. Using placeholder.")
            formatted_date = "No detectada"
    except (ValueError, TypeError) as e:
        logger.warning(f"⚠️ Failed to format date for user message: {e}")
        formatted_date = "Formato inválido"

    payment_method_raw = sanitized_data.get("payment_method", "")
    translated_payment_methods = {
        "billetera_digital": "📱 Billetera Digital (Yape/Plin/Débito)",
        "tarjeta_credito": "💳 Tarjeta de Crédito",
    }
    payment_method_friendly = translated_payment_methods.get(
        payment_method_raw, "❓ Desconocido"
    )

    category_name = sanitized_data.get("category", "❓ Desconocida")

    message = (
        f"✅ ¡Gasto registrado con éxito!\n\n"
        f"💰 Monto: S/. {amount}\n"
        f"📝 Descripción: {comment}\n"
        f"📅 Fecha: {formatted_date}\n"
        f"💳 Método: {payment_method_friendly}\n"
        f"🏷️ Categoría: {category_name}"
    )
    return message
