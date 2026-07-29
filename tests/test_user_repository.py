import sqlite3

import pytest

from database import SCHEMA, get_db
from repositories.user_repository import UserRepository


@pytest.fixture
def db(tmp_path):
    """Create a temporary SQLite database for each test."""
    db_path = tmp_path / "test.db"

    # Create tables
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA)
    conn.close()

    return str(db_path)


@pytest.fixture
def repo(db):
    """Create a UserRepository with temporary database."""
    return UserRepository(db_path=db)


class TestGetUser:
    def test_returns_none_for_unknown_user(self, repo):
        result = repo.get_user(99999)
        assert result is None

    def test_returns_user_with_accounts_and_categories(self, repo, db):
        # Seed data
        with get_db(db) as conn:
            conn.execute(
                "INSERT INTO users (telegram_id, nombre, ez_token) VALUES (?, ?, ?)",
                (12345, "Test User", "fake-token"),
            )
            conn.execute(
                "INSERT INTO user_accounts (user_id, name, ez_account_id) VALUES (?, ?, ?)",
                (12345, "billetera_digital", "acc-123"),
            )
            conn.execute(
                "INSERT INTO user_categories (user_id, name, ez_category_id) VALUES (?, ?, ?)",
                (12345, "Comida", "cat-456"),
            )

        result = repo.get_user(12345)

        assert result is not None
        assert result["nombre"] == "Test User"
        assert result["ez_token"] == "fake-token"
        assert result["cuentas"] == {"billetera_digital": "acc-123"}
        assert result["categorias"] == {"Comida": "cat-456"}

    def test_returns_empty_accounts_and_categories(self, repo, db):
        with get_db(db) as conn:
            conn.execute(
                "INSERT INTO users (telegram_id, nombre, ez_token) VALUES (?, ?, ?)",
                (12345, "Test User", "fake-token"),
            )

        result = repo.get_user(12345)

        assert result["cuentas"] == {}
        assert result["categorias"] == {}
