import sqlite3

from database import init_db


class TestInitDb:
    def test_creates_tables_and_runs_migrations(self, tmp_path):
        db_path = tmp_path / "test.db"

        init_db(db_path)

        conn = sqlite3.connect(str(db_path))
        # Tables exist
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert {"users", "user_accounts", "user_categories"} <= tables

        # hints column present
        columns = {
            r[1]
            for r in conn.execute("PRAGMA table_info(user_accounts)").fetchall()
        }
        assert "hints" in columns

        # user_version set to 1
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        assert version == 1

        conn.close()

    def test_skips_already_applied_migrations(self, tmp_path):
        db_path = tmp_path / "test.db"

        # First run applies migrations
        init_db(db_path)

        # Second run skips them
        init_db(db_path)

        conn = sqlite3.connect(str(db_path))
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        assert version == 1
        conn.close()

    def test_idempotent(self, tmp_path):
        db_path = tmp_path / "test.db"

        init_db(db_path)
        init_db(db_path)

        conn = sqlite3.connect(str(db_path))
        # No duplicate tables (sqlite_sequence is internal for AUTOINCREMENT)
        user_tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'"
            ).fetchall()
        }
        assert len(user_tables) == 3

        # Schema unchanged — insert should still work
        conn.execute(
            "INSERT INTO users (telegram_id, nombre, ez_token) VALUES (?, ?, ?)",
            (1, "Test", "tok"),
        )
        conn.commit()
        conn.close()
