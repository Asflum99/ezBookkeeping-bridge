import json
import os
from typing import Any

from config.logger import logger

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
ACCOUNTS_JSON_PATH = os.path.join(PROJECT_ROOT, "data", "cuentas.json")


def get_user_categories(telegram_id: int) -> list[str]:
    """
    Retrieves the list of category names for a specific user from the JSON storage.
    If the user is not found, returns an empty list.
    """
    if not os.path.exists(ACCOUNTS_JSON_PATH):
        logger.error(f"Accounts JSON file not found at: {ACCOUNTS_JSON_PATH}")
        return []

    try:
        with open(ACCOUNTS_JSON_PATH, "r", encoding="utf-8") as file:
            accounts_data = json.load(file)

        user_config: dict[str, Any] = accounts_data.get(str(telegram_id))
        if not user_config:
            logger.warning(f"User {telegram_id} config not found in JSON storage.")
            return []

        # Extract only the keys (category names) from the mapping dict
        # E.g. {"Comida": "382610...", "Transporte": "382610..."} -> ["Comida", "Transporte"]
        categories = list(user_config.get("categorias", {}).keys())
        logger.debug(
            f"Successfully retrieved {len(categories)} categories for user {telegram_id}"
        )
        return categories

    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to read or parse accounts JSON file: {e}")
        return []


def get_user_configuration(user_id: int) -> dict[str, Any]:
    """
    Retrieves the complete configuration dictionary for a specific user from the JSON file.
    Returns an empty dict if the user is not found or if an error occurs.
    """
    if not os.path.exists(ACCOUNTS_JSON_PATH):
        logger.error(f"Accounts file not found at path: {ACCOUNTS_JSON_PATH}")
        return {}

    try:
        with open(ACCOUNTS_JSON_PATH, "r", encoding="utf-8") as file:
            accounts_data = json.load(file)
            user_config = accounts_data.get(str(user_id))

            return user_config if user_config is not None else {}

    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to read or parse accounts JSON file: {e}")
        return {}
