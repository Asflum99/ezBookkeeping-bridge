from collections.abc import Callable
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
                "SELECT name, ez_account_id, hints, category FROM user_accounts WHERE user_id = ?",
                (telegram_id,),
            ):
                accounts[acc["name"]] = acc["ez_account_id"]
                hint_text = acc["hints"] if acc["hints"] else acc["name"]
                accounts_with_hints.append((acc["name"], hint_text, acc["category"]))

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

    def _sync_local_remote(
        self,
        telegram_id: int,
        table: str,
        id_column: str,
        remote_items: list[dict],
        label: str,
        extra_insert_cols: dict[str, str] | None = None,
        item_extract_fn: Callable[[dict], dict] | None = None,
    ) -> dict:
        """Generic sync: local SQLite table ↔ remote ezBookkeeping items."""
        logger.info(f"Syncing {label.lower()}s for user {telegram_id}")
        remote_map = {item["id"]: item for item in remote_items}
        remote_ids = set(remote_map.keys())
        logger.debug(f"Remote ids: {remote_ids}")

        with get_db(self._db_path) as conn:
            select_extra = ", category" if item_extract_fn else ""
            local_rows = conn.execute(
                f"SELECT name, {id_column}{select_extra} FROM {table} WHERE user_id = ?",
                (telegram_id,),
            ).fetchall()

            local_ids = {row[id_column] for row in local_rows}
            logger.debug(f"Local ids: {local_ids}")
            local_by_id = {row[id_column]: dict(row) for row in local_rows}
            local_names = {eid: r["name"] for eid, r in local_by_id.items()}
            logger.debug(f"Local names: {local_names}")

            to_remove = local_ids - remote_ids
            for ez_id in to_remove:
                logger.debug(f"Removing {label.lower()} {ez_id} for user {telegram_id}")
                conn.execute(
                    f"DELETE FROM {table} WHERE user_id = ? AND {id_column} = ?",
                    (telegram_id, ez_id),
                )

            to_add = remote_ids - local_ids
            added = []
            for ez_id in to_add:
                name = remote_map[ez_id]["name"]
                if item_extract_fn:
                    extra_cols = item_extract_fn(remote_map[ez_id])
                else:
                    extra_cols = extra_insert_cols or {}
                col_names = ", ".join(extra_cols.keys())
                placeholders = ", ".join(["?"] * len(extra_cols))
                logger.debug(
                    f"Adding {label.lower()} {name} ({ez_id}) for user {telegram_id}"
                )
                conn.execute(
                    f"INSERT INTO {table} (user_id, name, {id_column}{', ' + col_names if col_names else ''}) "
                    f"VALUES (?, ?, ?{', ' + placeholders if placeholders else ''})",
                    (telegram_id, name, ez_id, *extra_cols.values()),
                )
                added.append({"id": ez_id, "name": name})

            to_update = local_ids & remote_ids
            updated = []
            for ez_id in to_update:
                remote_item = remote_map[ez_id]
                remote_name = remote_item["name"]
                local_name = local_by_id[ez_id]["name"]

                sets = {}
                if local_name != remote_name:
                    sets["name"] = remote_name

                if item_extract_fn:
                    extra = item_extract_fn(remote_item)
                    local_val = local_by_id[ez_id].get("category")
                    remote_val = extra.get("category")
                    if remote_val is not None and remote_val != local_val:
                        sets["category"] = remote_val

                if sets:
                    set_clause = ", ".join(f"{k} = ?" for k in sets)
                    logger.debug(f"Updating {label.lower()} {ez_id}: {sets}")
                    conn.execute(
                        f"UPDATE {table} SET {set_clause} WHERE user_id = ? AND {id_column} = ?",
                        (*sets.values(), telegram_id, ez_id),
                    )
                    updated.append(
                        {
                            "id": ez_id,
                            **(
                                {"old_name": local_name, "new_name": remote_name}
                                if "name" in sets
                                else {}
                            ),
                        }
                    )

            removed = [local_names[eid] for eid in to_remove]

        logger.info(
            f"{label} sync complete for user {telegram_id}: +{len(added)} -{len(removed)} ~{len(updated)}"
        )
        return {"added": added, "removed": removed, "updated": updated}

    def sync_accounts(self, telegram_id: int, remote_accounts: list[dict]) -> dict:
        """Sync local user_accounts with remote ezBookkeeping accounts."""
        return self._sync_local_remote(
            telegram_id,
            "user_accounts",
            "ez_account_id",
            remote_accounts,
            "Account",
            item_extract_fn=lambda item: {
                "hints": "",
                "category": item["category"],
            },
        )

    def sync_categories(self, telegram_id: int, remote_categories: list[dict]) -> dict:
        """Sync local user_categories with remote ezBookkeeping categories."""
        return self._sync_local_remote(
            telegram_id,
            "user_categories",
            "ez_category_id",
            remote_categories,
            "Category",
        )
