from datetime import datetime
from typing import Any, cast
from zoneinfo import ZoneInfo

import httpx

from config import logger, settings


async def register_transaction(
    sanitized_data: dict[str, Any], user_info: dict[str, Any]
) -> bool:
    """
    Submits the transaction to the ezBookkeeping API using the user's specific token.

    Expects sanitized_data from validate_and_sanitize_voucher_data:
    - amount: int (cents, > 0)
    - date_time: str ("%Y-%m-%d %H:%M:%S", America/Lima)
    - payment_account: str (valid account name)
    - comment: str
    - transaction_type: int (3 or 4)
    - category_id: str (resolved category ID)
    - destination_account_id: str | None (for type 4 transfers)
    """
    logger.info("Starting transaction registration in ezBookkeeping.")
    url = f"{settings.ezbookkeeping_url}/api/v1/transactions/add.json"

    transaction_type = sanitized_data.get("transaction_type", 3)
    category_id = sanitized_data.get("category_id")
    if not category_id:
        logger.error("❌ Failed to resolve category ID.")
        return False

    payment_account = sanitized_data.get("payment_account")
    user_accounts = user_info.get("cuentas", {})

    source_account_id = user_accounts.get(payment_account)
    if not source_account_id:
        logger.error(
            f"❌ Failed to resolve source account ID for payment method: '{payment_account}'. "
            f"Available user accounts: {list(user_accounts.keys())}"
        )
        return False

    amount_cents = round(float(sanitized_data["amount"]) * 100)

    iso_time_str = cast(str, sanitized_data["date_time"])
    parsed_datetime = datetime.strptime(iso_time_str, "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=ZoneInfo("America/Lima")
    )
    unix_timestamp = int(parsed_datetime.timestamp())

    headers = {
        "Authorization": f"Bearer {user_info['ez_token']}",
        "Content-Type": "application/json",
        "X-Timezone-Name": "America/Lima",
        "X-Timezone-Offset": "-300",
    }

    body = {
        "type": transaction_type,
        "categoryId": category_id,
        "sourceAmount": amount_cents,
        "time": unix_timestamp,
        "comment": sanitized_data.get("comment", ""),
        "sourceAccountId": source_account_id,
        "utcOffset": -300,
    }

    # Type 4: Transfer — add destination account and amount
    if transaction_type == 4:
        destination_account_id = sanitized_data.get("destination_account_id")
        if not destination_account_id:
            logger.error("❌ Type 4 transfer missing destination_account_id.")
            return False
        body["destinationAccountId"] = destination_account_id
        body["destinationAmount"] = amount_cents

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


async def _fetch_ez_list(
    ez_token: str,
    endpoint: str,
    label: str,
    extract_fn=None,
) -> list[dict] | None:
    """Generic GET list from ezBookkeeping API."""
    url = f"{settings.ezbookkeeping_url}{endpoint}"
    headers = {"Authorization": f"Bearer {ez_token}"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code != 200:
                logger.error(
                    f"ezBookkeeping {label} API error. Status: {response.status_code}"
                )
                return None
            res_json = response.json()
            if not res_json.get("success"):
                logger.error(f"ezBookkeeping {label} API returned success=false")
                return None
            result = res_json["result"]
            return extract_fn(result) if extract_fn else result
    except httpx.HTTPError as e:
        logger.exception(f"Network or HTTP error fetching {label}: {e}")
        return None
    except (ValueError, KeyError) as e:
        logger.exception(f"Invalid JSON payload received from ezBookkeeping: {e}")
        return None


def _flatten_categories(raw: dict) -> list[dict]:
    """Flatten all category types and preserve hierarchy and type."""
    result = []

    def flatten(cats, category_type, parent_name=""):
        for cat in cats:
            name = f"{parent_name} > {cat['name']}" if parent_name else cat["name"]
            result.append({"id": cat["id"], "name": name, "type": int(category_type)})
            if cat.get("subCategories"):
                flatten(cat["subCategories"], category_type, name)

    for category_type, categories in raw.items():
        flatten(categories, category_type)
    return result


async def get_user_accounts(ez_token: str) -> list[dict] | None:
    return await _fetch_ez_list(ez_token, "/api/v1/accounts/list.json", "accounts")


async def get_user_categories(ez_token: str) -> list[dict] | None:
    return await _fetch_ez_list(
        ez_token,
        "/api/v1/transaction/categories/list.json",
        "categories",
        extract_fn=_flatten_categories,
    )
