from pathlib import Path
from typing import Any

from config import logger, settings
from database import get_db


class UserRepository:
    """User configuration repository backed by SQLite."""

    def __init__(self, db_path: Path = settings.database_path):
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
            accounts_with_hints = []

            for acc in conn.execute(
                "SELECT name, ez_account_id, hints FROM user_accounts WHERE user_id = ?",
                (telegram_id,),
            ):
                accounts[acc["name"]] = acc["ez_account_id"]
                hint_text = acc["hints"] if acc["hints"] else acc["name"]
                accounts_with_hints.append((acc["name"], hint_text))

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
                "cuentas_hints": accounts_with_hints,
                "categorias": categories,
            }

            logger.debug(
                f"Configuration recovered for Telegram ID ({telegram_id}): {user_config}"
            )
            return user_config

    def sync_accounts(self, telegram_id: int, remote_accounts: list[dict]) -> dict:
        """Sync local user_accounts with remote ezBookkeeping accounts."""
        remote_map = {acc["id"]: acc["name"] for acc in remote_accounts}
        remote_ids = set(remote_map.keys())

        with get_db(self._db_path) as conn:
            local_rows = conn.execute(
                "SELECT name, ez_account_id FROM user_accounts WHERE user_id = ?",
                (telegram_id,),
            ).fetchall()

            local_ids = {row["ez_account_id"] for row in local_rows}
            local_names = {row["ez_account_id"]: row["name"] for row in local_rows}

            # Remove accounts no longer in remote
            to_remove = local_ids - remote_ids
            for ez_id in to_remove:
                conn.execute(
                    "DELETE FROM user_accounts WHERE user_id = ? AND ez_account_id = ?",
                    (telegram_id, ez_id),
                )

            # Add accounts not in local
            to_add = remote_ids - local_ids
            added = []
            for ez_id in to_add:
                name = remote_map[ez_id]
                conn.execute(
                    "INSERT INTO user_accounts (user_id, name, ez_account_id, hints) VALUES (?, ?, ?, ?)",
                    (telegram_id, name, ez_id, ""),
                )
                added.append({"id": ez_id, "name": name})

            removed = [local_names[eid] for eid in to_remove]

        return {"added": added, "removed": removed}
