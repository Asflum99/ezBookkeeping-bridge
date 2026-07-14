import logging
import os
import sys
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

logger = logging.getLogger("bot_finanzas")

EZBOOKKEEPING_URL = os.getenv("EZBOOKKEEPING_URL")
if not EZBOOKKEEPING_URL:
    logger.critical(
        "❌ ERROR CRÍTICO: La variable de entorno EZBOOKKEEPING_URL no está configurada."
    )
    sys.exit(1)


async def register_transaction(
    sanitized_data: dict[str, Any], user_info: dict[str, Any]
) -> bool:
    """
    Submits the transaction to the ezBookkeeping API using the user's specific token.
    Resolves category IDs and source account IDs dynamically from user_info.
    """
    logger.info("Starting transaction registration in ezBookkeeping.")
    url = f"{EZBOOKKEEPING_URL}/api/v1/transactions/add.json"

    category_name = sanitized_data.get("category")
    user_categories = user_info.get("categorias", {})

    category_id = user_categories.get(category_name)
    if not category_id:
        logger.error(
            f"❌ Failed to resolve category ID for name: '{category_name}'. "
            f"Allowed user categories: {list(user_categories.keys())}"
        )
        return False

    payment_method = sanitized_data.get("payment_method")
    user_accounts = user_info.get("cuentas", {})

    source_account_id = user_accounts.get(payment_method)
    if not source_account_id:
        logger.error(
            f"❌ Failed to resolve source account ID for payment method: '{payment_method}'. "
            f"Available user accounts: {list(user_accounts.keys())}"
        )
        return False

    amount_cents = int(round(float(sanitized_data["amount"]) * 100))

    iso_time_str = sanitized_data["date_time"]
    try:
        parsed_datetime = datetime.strptime(iso_time_str, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=ZoneInfo("America/Lima")
        )
        unix_timestamp = int(parsed_datetime.timestamp())

    except (ValueError, TypeError) as e:
        logger.error(
            f"❌ Failed to convert date '{iso_time_str}' to Unix timestamp: {e}. Falling back to now."
        )
        unix_timestamp = int(datetime.now(ZoneInfo("America/Lima")).timestamp())

    headers = {
        "Authorization": f"Bearer {user_info['ez_token']}",
        "Content-Type": "application/json",
        "X-Timezone-Name": "America/Lima",
        "X-Timezone-Offset": "-300",
    }

    body = {
        "type": 3,
        "categoryId": category_id,
        "sourceAmount": amount_cents,
        "time": unix_timestamp,
        "comment": sanitized_data["comment"],
        "sourceAccountId": source_account_id,
        "utcOffset": -300,
    }

    logger.debug(f"Submitting transaction with payload: {body}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=body, headers=headers, timeout=10.0)
            logger.debug(
                f"ezBookkeeping API responded with status code: {response.status_code}"
            )

            if response.status_code == 200:
                try:
                    res_json = response.json()
                    if res_json.get("success"):
                        logger.info(
                            "🎉 Transaction successfully registered in ezBookkeeping!"
                        )
                        return True
                except ValueError:
                    logger.error(
                        "❌ ezBookkeeping returned 200 OK but body is not a valid JSON."
                    )

            logger.error(
                f"❌ ezBookkeeping API Error. Status: {response.status_code}. Response: {response.text}"
            )
            return False

    except httpx.RequestError as e:
        logger.exception(
            f"❌ Network or Timeout error connecting to ezBookkeeping: {e}"
        )
        return False
    except Exception as e:
        logger.exception(f"❌ Unexpected error in register_transaction: {e}")
        return False
