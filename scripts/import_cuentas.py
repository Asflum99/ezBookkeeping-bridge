#!/usr/bin/env python3
"""Import cuentas.json into SQLite database."""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config import ACCOUNTS_JSON_PATH, DATABASE_PATH
from database import get_db, init_db


def import_cuentas():
    """Import data from cuentas.json into SQLite."""
    if not Path(ACCOUNTS_JSON_PATH).exists():
        print(f"Error: {ACCOUNTS_JSON_PATH} not found")
        sys.exit(1)

    # Initialize database
    init_db()

    # Load JSON data
    with open(ACCOUNTS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    imported = 0
    for telegram_id_str, user_data in data.items():
        telegram_id = int(telegram_id_str)
        nombre = user_data.get("nombre", "")
        ez_token = user_data.get("ez_token", "")

        with get_db() as conn:
            # Insert user
            conn.execute(
                "INSERT OR REPLACE INTO users (telegram_id, nombre, ez_token) VALUES (?, ?, ?)",
                (telegram_id, nombre, ez_token),
            )

            # Insert accounts
            for name, ez_account_id in user_data.get("cuentas", {}).items():
                conn.execute(
                    "INSERT OR REPLACE INTO user_accounts (user_id, name, ez_account_id) VALUES (?, ?, ?)",
                    (telegram_id, name, ez_account_id),
                )

            # Insert categories
            for name, ez_category_id in user_data.get("categorias", {}).items():
                conn.execute(
                    "INSERT OR REPLACE INTO user_categories (user_id, name, ez_category_id) VALUES (?, ?, ?)",
                    (telegram_id, name, ez_category_id),
                )

        imported += 1
        print(f"✓ Imported user {telegram_id} ({nombre})")

    print(f"\nDone: {imported} users imported to {DATABASE_PATH}")


if __name__ == "__main__":
    import_cuentas()
