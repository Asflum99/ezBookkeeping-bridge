from pathlib import Path
from typing import Any

from config import DATABASE_PATH, logger
from database import get_db


class UserRepository:
    """User configuration repository backed by SQLite."""

    def __init__(self, db_path: Path = DATABASE_PATH):
        self._db_path = db_path

    def get_user(self, telegram_id: int) -> dict[str, Any] | None:
        """Load user config by Telegram ID. Returns None if not found."""
        with get_db(self._db_path) as conn:
            # Get user
            row = conn.execute(
                "SELECT nombre, ez_token FROM users WHERE telegram_id = ?",
                (telegram_id,),
            ).fetchone()

            if not row:
                logger.info(f"Unregistered user attempt: {telegram_id}")
                return None

            nombre, ez_token = row["nombre"], row["ez_token"]

            # Get accounts
            accounts = {}
            for acc in conn.execute(
                "SELECT name, ez_account_id FROM user_accounts WHERE user_id = ?",
                (telegram_id,),
            ):
                accounts[acc["name"]] = acc["ez_account_id"]

            # Get categories
            categories = {}
            for cat in conn.execute(
                "SELECT name, ez_category_id FROM user_categories WHERE user_id = ?",
                (telegram_id,),
            ):
                categories[cat["name"]] = cat["ez_category_id"]

            user_config = {
                "nombre": nombre,
                "ez_token": ez_token,
                "cuentas": accounts,
                "categorias": categories,
            }

            logger.debug(
                f"Configuration recovered for Telegram ID ({telegram_id}): {user_config}"
            )
            return user_config
