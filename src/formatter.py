from datetime import datetime, timedelta
from typing import Any, cast

from config import logger, settings


def resolve_transaction_type(
    types: list[int],
    destination_account: str | None,
    user_accounts_hints: list[tuple[str, str, int]],
) -> int:
    """Returns 4 if destination_account matches a user account hint, else 3."""
    if 4 in types and destination_account:
        for name, _, _ in user_accounts_hints:
            if destination_account in name:
                return 4
    return 3


def get_transfer_category_id(
    destination_account_category: int,
    user_categories: dict[str, str],
) -> str | None:
    """Returns transfer category ID based on destination account type."""
    if destination_account_category == 3:  # Credit Card
        return user_categories.get("Pago de Tarjetas de Crédito")
    else:
        return user_categories.get("Transferencia Bancaria")


def validate_and_sanitize_voucher_data(
    raw_llm_data: dict[str, Any],
    user_info: dict[str, Any],
    user_accounts_hints: list[tuple[str, str, int]],
    user_categories: dict[str, str],
) -> dict[str, Any]:
    """
    Validates LLM response data. Raises ValueError if required fields are missing.
    Falls back to current time for invalid/missing date_time.
    """
    sanitized_data = raw_llm_data.copy()

    amount = sanitized_data.get("amount")
    if amount is None or amount <= 0:
        logger.error(
            "Amount is missing or zero from LLM extraction. Cannot process expense."
        )
        raise ValueError("Amount is required but not provided.")

    payment_account = sanitized_data.get("payment_account")
    if not payment_account:
        logger.error("Payment method is missing from LLM extraction.")
        raise ValueError("Payment method is required but not provided.")

    # Resolve transaction type
    types = sanitized_data.get("types", [3])
    destination_account = sanitized_data.get("destination_account")
    transaction_type = resolve_transaction_type(
        types, destination_account, user_accounts_hints
    )
    sanitized_data["transaction_type"] = transaction_type

    # Handle category based on transaction type
    if transaction_type == 4:
        # Type 4: Transfer — no category from LLM, resolve from destination account
        sanitized_data["category"] = None
        dest_account_id = None
        dest_account_category = 0
        for account_name, hints, category in user_accounts_hints:
            if cast(str, destination_account) in hints:
                dest_account_id = user_info.get("cuentas", {}).get(account_name)
                dest_account_category = category
                break
        sanitized_data["destination_account_id"] = dest_account_id
        sanitized_data["category_id"] = get_transfer_category_id(
            dest_account_category, user_categories
        )
    else:
        # Type 3: Expense — require category from LLM
        category = sanitized_data.get("category")
        if not category:
            logger.error("Category is missing from LLM extraction.")
            raise ValueError("Category is required but not provided.")
        user_categories = user_info.get("categorias", {})
        sanitized_data["category_id"] = user_categories.get(category)
        sanitized_data["destination_account_id"] = None

    if not sanitized_data.get("comment"):
        sanitized_data["comment"] = ""

    now = datetime.now(settings.timezone)
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
        extracted_date = datetime.strptime(
            extracted_date_str, "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=settings.timezone)

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
    amount = sanitized_data.get("amount")
    comment = sanitized_data.get("comment", "Desconocido")
    date_time_str = cast(str, sanitized_data.get("date_time"))

    try:
        parsed_date = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=settings.timezone
        )
        formatted_date = parsed_date.strftime("%d-%m-%Y %I:%M %p")
    except (ValueError, TypeError) as e:
        logger.warning(f"⚠️ Failed to format date for user message: {e}")
        now = datetime.now(settings.timezone)
        formatted_date = now.strftime("%d-%m-%Y %I:%M %p")

    payment_account = sanitized_data.get("payment_account", "❓ Desconocido")

    transaction_type = sanitized_data.get("transaction_type", 3)

    if transaction_type == 4:
        dest_category = sanitized_data.get("destination_account_category", 0)
        if dest_category == 3:  # Credit Card
            header = "✅ ¡Tarjeta de crédito pagada con éxito!"
        else:
            header = "✅ ¡Transferencia registrada con éxito!"
        category_line = ""
    else:
        header = "✅ ¡Gasto registrado con éxito!"
        category_name = sanitized_data.get("category", "❓ Desconocida")
        category_line = f"\n🏷️ Categoría: {category_name}"

    message = (
        f"{header}\n\n"
        f"💰 Monto: S/. {amount}\n"
        f"📝 Descripción: {comment}\n"
        f"📅 Fecha: {formatted_date}\n"
        f"💳 Cuenta de pago: {payment_account}{category_line}"
    )
    return message
