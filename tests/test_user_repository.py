import sqlite3

import pytest

from database import MIGRATIONS, SCHEMA, get_db
from repositories.user_repository import UserRepository


@pytest.fixture
def db(tmp_path):
    """Create a temporary SQLite database for each test."""
    db_path = tmp_path / "test.db"

    # Create tables
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA)
    v = conn.execute("PRAGMA user_version").fetchone()[0]
    for to, sql in MIGRATIONS:
        if v < to:
            conn.executescript(sql)
            conn.execute(f"PRAGMA user_version = {to}")
    conn.commit()
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
                "INSERT INTO user_accounts (user_id, name, ez_account_id, hints) VALUES (?, ?, ?, ?)",
                (12345, "billetera_digital", "acc-123", "Yape, BCP Transfer, purple"),
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
        assert result["cuentas_hints"] == [
            ("billetera_digital", "Yape, BCP Transfer, purple")
        ]
        assert result["categorias"] == {"Comida": "cat-456"}

    def test_returns_empty_accounts_and_categories(self, repo, db):
        with get_db(db) as conn:
            conn.execute(
                "INSERT INTO users (telegram_id, nombre, ez_token) VALUES (?, ?, ?)",
                (12345, "Test User", "fake-token"),
            )

        result = repo.get_user(12345)

        assert result["cuentas"] == {}
        assert result["cuentas_hints"] == []
        assert result["categorias"] == {}


class TestSyncAccounts:
    def _seed_user(self, conn, telegram_id):
        conn.execute(
            "INSERT INTO users (telegram_id, nombre, ez_token) VALUES (?, ?, ?)",
            (telegram_id, "Test", "tok"),
        )

    def test_adds_new_accounts(self, db):
        with get_db(db) as conn:
            self._seed_user(conn, 12345)

        repo = UserRepository(db_path=db)
        remote = [{"id": "acc-1", "name": "BCP"}, {"id": "acc-2", "name": "Yape"}]

        result = repo.sync_accounts(12345, remote)

        assert len(result["added"]) == 2
        assert len(result["removed"]) == 0
        assert len(result["updated"]) == 0

    def test_removes_deleted_accounts(self, db):
        with get_db(db) as conn:
            self._seed_user(conn, 12345)
            conn.execute(
                "INSERT INTO user_accounts (user_id, name, ez_account_id, hints) VALUES (?, ?, ?, ?)",
                (12345, "BCP", "acc-old", "old hint"),
            )

        repo = UserRepository(db_path=db)
        remote = [{"id": "acc-new", "name": "Yape"}]

        result = repo.sync_accounts(12345, remote)

        assert len(result["added"]) == 1
        assert result["added"][0]["name"] == "Yape"
        assert len(result["removed"]) == 1
        assert result["removed"][0] == "BCP"
        assert len(result["updated"]) == 0

    def test_updates_renamed_account(self, db):
        with get_db(db) as conn:
            self._seed_user(conn, 12345)
            conn.execute(
                "INSERT INTO user_accounts (user_id, name, ez_account_id, hints) VALUES (?, ?, ?, ?)",
                (12345, "BCP", "acc-1", "hint"),
            )

        repo = UserRepository(db_path=db)
        remote = [{"id": "acc-1", "name": "BCP (Débito)"}]

        result = repo.sync_accounts(12345, remote)

        assert len(result["added"]) == 0
        assert len(result["removed"]) == 0
        assert len(result["updated"]) == 1
        assert result["updated"][0] == {"id": "acc-1", "old_name": "BCP", "new_name": "BCP (Débito)"}

    def test_no_changes(self, db):
        with get_db(db) as conn:
            self._seed_user(conn, 12345)
            conn.execute(
                "INSERT INTO user_accounts (user_id, name, ez_account_id, hints) VALUES (?, ?, ?, ?)",
                (12345, "BCP", "acc-1", "hint"),
            )

        repo = UserRepository(db_path=db)
        remote = [{"id": "acc-1", "name": "BCP"}]

        result = repo.sync_accounts(12345, remote)

        assert result["added"] == []
        assert result["removed"] == []
        assert result["updated"] == []


class TestSyncCategories:
    def _seed_user(self, conn, telegram_id):
        conn.execute(
            "INSERT INTO users (telegram_id, nombre, ez_token) VALUES (?, ?, ?)",
            (telegram_id, "Test", "tok"),
        )

    def test_adds_new_categories(self, db):
        with get_db(db) as conn:
            self._seed_user(conn, 12345)

        repo = UserRepository(db_path=db)
        remote = [
            {"id": "cat-1", "name": "Food"},
            {"id": "cat-2", "name": "Transport"},
        ]

        result = repo.sync_categories(12345, remote)

        assert len(result["added"]) == 2
        assert len(result["removed"]) == 0
        assert len(result["updated"]) == 0

    def test_removes_deleted_categories(self, db):
        with get_db(db) as conn:
            self._seed_user(conn, 12345)
            conn.execute(
                "INSERT INTO user_categories (user_id, name, ez_category_id) VALUES (?, ?, ?)",
                (12345, "Food", "cat-old"),
            )

        repo = UserRepository(db_path=db)
        remote = [{"id": "cat-new", "name": "Transport"}]

        result = repo.sync_categories(12345, remote)

        assert len(result["added"]) == 1
        assert result["added"][0]["name"] == "Transport"
        assert len(result["removed"]) == 1
        assert result["removed"][0] == "Food"
        assert len(result["updated"]) == 0

    def test_updates_renamed_category(self, db):
        with get_db(db) as conn:
            self._seed_user(conn, 12345)
            conn.execute(
                "INSERT INTO user_categories (user_id, name, ez_category_id) VALUES (?, ?, ?)",
                (12345, "Food", "cat-1"),
            )

        repo = UserRepository(db_path=db)
        remote = [{"id": "cat-1", "name": "Food > Groceries"}]

        result = repo.sync_categories(12345, remote)

        assert len(result["added"]) == 0
        assert len(result["removed"]) == 0
        assert len(result["updated"]) == 1
        assert result["updated"][0] == {
            "id": "cat-1",
            "old_name": "Food",
            "new_name": "Food > Groceries",
        }

    def test_no_changes(self, db):
        with get_db(db) as conn:
            self._seed_user(conn, 12345)
            conn.execute(
                "INSERT INTO user_categories (user_id, name, ez_category_id) VALUES (?, ?, ?)",
                (12345, "Food", "cat-1"),
            )

        repo = UserRepository(db_path=db)
        remote = [{"id": "cat-1", "name": "Food"}]

        result = repo.sync_categories(12345, remote)

        assert result["added"] == []
        assert result["removed"] == []
        assert result["updated"] == []
