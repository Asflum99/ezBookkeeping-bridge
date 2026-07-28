import sqlite3
from contextlib import contextmanager

from config import DATABASE_PATH, logger

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    ez_token TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    ez_account_id TEXT NOT NULL,
    UNIQUE(user_id, name)
);

CREATE TABLE IF NOT EXISTS user_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    ez_category_id TEXT NOT NULL,
    UNIQUE(user_id, name)
);
"""


def init_db(db_path: str = DATABASE_PATH) -> None:
    """Create tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
        logger.info(f"Database initialized at {db_path}")
    finally:
        conn.close()


@contextmanager
def get_db(db_path: str = DATABASE_PATH):
    """Context manager for database connections."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
