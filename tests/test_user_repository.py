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


class TestAddUser:
    def test_adds_user(self, repo):
        repo.add_user(12345, "Test User", "fake-token")

        result = repo.get_user(12345)
        assert result["nombre"] == "Test User"

    def test_replaces_existing_user(self, repo):
        repo.add_user(12345, "Test User", "old-token")
        repo.add_user(12345, "Updated User", "new-token")

        result = repo.get_user(12345)
        assert result["nombre"] == "Updated User"
        assert result["ez_token"] == "new-token"


class TestAddAccount:
    def test_adds_account(self, repo):
        repo.add_user(12345, "Test User", "fake-token")
        result = repo.add_account(12345, "billetera_digital", "acc-123")

        assert result is True
        user = repo.get_user(12345)
        assert user["cuentas"]["billetera_digital"] == "acc-123"

    def test_rejects_duplicate(self, repo):
        repo.add_user(12345, "Test User", "fake-token")
        repo.add_account(12345, "billetera_digital", "acc-123")
        result = repo.add_account(12345, "billetera_digital", "acc-456")

        assert result is False
        user = repo.get_user(12345)
        assert user["cuentas"]["billetera_digital"] == "acc-123"


class TestRemoveAccount:
    def test_removes_account(self, repo):
        repo.add_user(12345, "Test User", "fake-token")
        repo.add_account(12345, "billetera_digital", "acc-123")
        result = repo.remove_account(12345, "billetera_digital")

        assert result is True
        user = repo.get_user(12345)
        assert user["cuentas"] == {}

    def test_returns_false_when_not_found(self, repo):
        repo.add_user(12345, "Test User", "fake-token")
        result = repo.remove_account(12345, "nonexistent")

        assert result is False


class TestListAccounts:
    def test_returns_account_names(self, repo):
        repo.add_user(12345, "Test User", "fake-token")
        repo.add_account(12345, "billetera_digital", "acc-123")
        repo.add_account(12345, "tarjeta_credito", "acc-456")

        result = repo.list_accounts(12345)

        assert sorted(result) == ["billetera_digital", "tarjeta_credito"]

    def test_returns_empty_list(self, repo):
        repo.add_user(12345, "Test User", "fake-token")
        result = repo.list_accounts(12345)

        assert result == []


class TestAddCategory:
    def test_adds_category(self, repo):
        repo.add_user(12345, "Test User", "fake-token")
        result = repo.add_category(12345, "Comida", "cat-123")

        assert result is True
        user = repo.get_user(12345)
        assert user["categorias"]["Comida"] == "cat-123"

    def test_rejects_duplicate(self, repo):
        repo.add_user(12345, "Test User", "fake-token")
        repo.add_category(12345, "Comida", "cat-123")
        result = repo.add_category(12345, "Comida", "cat-456")

        assert result is False
        user = repo.get_user(12345)
        assert user["categorias"]["Comida"] == "cat-123"


class TestRemoveCategory:
    def test_removes_category(self, repo):
        repo.add_user(12345, "Test User", "fake-token")
        repo.add_category(12345, "Comida", "cat-123")
        result = repo.remove_category(12345, "Comida")

        assert result is True
        user = repo.get_user(12345)
        assert user["categorias"] == {}

    def test_returns_false_when_not_found(self, repo):
        repo.add_user(12345, "Test User", "fake-token")
        result = repo.remove_category(12345, "nonexistent")

        assert result is False


class TestListCategories:
    def test_returns_category_names(self, repo):
        repo.add_user(12345, "Test User", "fake-token")
        repo.add_category(12345, "Comida", "cat-123")
        repo.add_category(12345, "Ropa", "cat-456")

        result = repo.list_categories(12345)

        assert sorted(result) == ["Comida", "Ropa"]

    def test_returns_empty_list(self, repo):
        repo.add_user(12345, "Test User", "fake-token")
        result = repo.list_categories(12345)

        assert result == []
