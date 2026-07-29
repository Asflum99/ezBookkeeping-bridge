import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

SAMPLE_PHOTO = {
    "file_id": "photo_large_id",
    "file_unique_id": "uniq_large",
    "width": 1280,
    "height": 720,
    "file_size": 1048576,
}

VALID_USER_INFO = {
    "nombre": "Test User",
    "ez_token": "fake-jwt-token",
    "cuentas": {"billetera_digital": "3826102909318201344"},
    "categorias": {"Comida": "3826101146502561820"},
}

SANITIZED_DATA = {
    "amount": 25.50,
    "date_time": "2026-07-19 12:30:00",
    "payment_method": "billetera_digital",
    "category": "Comida",
    "comment": "Tambo",
}

WEBHOOK_PATH = "/webhook/telegram/"


def _make_update(**overrides):
    """Helper: build a TelegramUpdate payload dict."""
    base = {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "date": 1700000000,
            "chat": {"id": 12345, "type": "private"},
            "from": {"id": 12345, "is_bot": False, "first_name": "Test"},
            "photo": [SAMPLE_PHOTO],
        },
    }
    base.update(overrides)
    return base


def _build_client(user_repo_mock):
    """Create a TestClient with a mocked UserRepository."""
    from routers.telegram.webhook import get_user_repository
    from routers.telegram import router

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_user_repository] = lambda: user_repo_mock
    return TestClient(app)


class TestTelegramWebhook:
    @pytest.fixture(autouse=True)
    def _mock_config(self, mocker):
        mocker.patch("routers.telegram.photo.TELEGRAM_BOT_TOKEN", "TOKEN")
        mocker.patch("routers.telegram.photo.ALLOWED_USERS", {12345})

    # --- No photo / no message ---

    def test_ignored_when_no_message(self, mocker):
        user_repo = mocker.MagicMock()
        client = _build_client(user_repo)

        resp = client.post(WEBHOOK_PATH, json={"update_id": 1})

        assert resp.status_code == 200
        assert resp.json()["detail"] == "No message"

    def test_ignored_when_no_photo(self, mocker):
        user_repo = mocker.MagicMock()
        client = _build_client(user_repo)

        payload = _make_update(
            message={
                "message_id": 1,
                "date": 1700000000,
                "chat": {"id": 12345, "type": "private"},
                "from": {"id": 12345, "is_bot": False, "first_name": "Test"},
            }
        )
        resp = client.post(WEBHOOK_PATH, json=payload)

        assert resp.status_code == 200
        assert resp.json()["detail"] == "Unsupported message type"

    # --- Auth ---

    def test_returns_403_for_unauthorized_user(self, mocker):
        user_repo = mocker.MagicMock()
        client = _build_client(user_repo)

        payload = _make_update()
        payload["message"]["from"]["id"] = 99999
        resp = client.post(WEBHOOK_PATH, json=payload)

        assert resp.status_code == 403
        user_repo.get_user.assert_not_called()

    # --- Unregistered user ---

    def test_unregistered_user_sends_warning(self, mocker):
        mock_send = mocker.patch("routers.telegram.photo.send_telegram_message")
        user_repo = mocker.MagicMock()
        user_repo.get_user.return_value = None
        client = _build_client(user_repo)

        resp = client.post(WEBHOOK_PATH, json=_make_update())

        assert resp.status_code == 200
        mock_send.assert_called_once()
        assert "No estás registrado" in mock_send.call_args[0][2]

    # --- No categories ---

    def test_no_categories_returns_error(self, mocker):
        mocker.patch(
            "routers.telegram.photo.download_telegram_photo",
            return_value="/tmp/photo.jpg",
        )
        mocker.patch("routers.telegram.photo.delete_local_file")
        user_repo = mocker.MagicMock()
        user_repo.get_user.return_value = {"categorias": {}}
        client = _build_client(user_repo)

        resp = client.post(WEBHOOK_PATH, json=_make_update())

        assert resp.status_code == 200
        assert resp.json()["detail"] == "Failed to retrieve user categories."

    # --- Happy path ---

    def test_full_flow(self, mocker):
        mock_send = mocker.patch("routers.telegram.photo.send_telegram_message")
        mock_delete = mocker.patch("routers.telegram.photo.delete_local_file")
        mock_download = mocker.patch(
            "routers.telegram.photo.download_telegram_photo",
            return_value="/tmp/photo.jpg",
        )
        mock_llm = mocker.patch(
            "routers.telegram.photo.process_expense_with_ai",
            return_value={"amount": 25.50},
        )
        mock_validate = mocker.patch(
            "routers.telegram.photo.validate_and_sanitize_voucher_data",
            return_value=SANITIZED_DATA,
        )
        mock_register = mocker.patch(
            "routers.telegram.photo.register_transaction", return_value=True
        )

        user_repo = mocker.MagicMock()
        user_repo.get_user.return_value = VALID_USER_INFO
        client = _build_client(user_repo)

        resp = client.post(WEBHOOK_PATH, json=_make_update())

        assert resp.status_code == 200
        mock_download.assert_called_once()
        mock_llm.assert_called_once()
        mock_validate.assert_called_once()
        mock_register.assert_called_once()
        mock_delete.assert_called_once_with("/tmp/photo.jpg")
        assert mock_send.call_count == 1
        assert "Gasto registrado" in mock_send.call_args[0][2]

    # --- Transaction fails ---

    def test_transaction_fails_sends_error(self, mocker):
        mock_send = mocker.patch("routers.telegram.photo.send_telegram_message")
        mock_delete = mocker.patch("routers.telegram.photo.delete_local_file")
        mocker.patch(
            "routers.telegram.photo.download_telegram_photo",
            return_value="/tmp/photo.jpg",
        )
        mocker.patch(
            "routers.telegram.photo.process_expense_with_ai",
            return_value={"amount": 25.50},
        )
        mocker.patch(
            "routers.telegram.photo.validate_and_sanitize_voucher_data",
            return_value=SANITIZED_DATA,
        )
        mocker.patch("routers.telegram.photo.register_transaction", return_value=False)

        user_repo = mocker.MagicMock()
        user_repo.get_user.return_value = VALID_USER_INFO
        client = _build_client(user_repo)

        resp = client.post(WEBHOOK_PATH, json=_make_update())

        assert resp.status_code == 200
        mock_delete.assert_called_once()
        assert "Error al guardar" in mock_send.call_args[0][2]

    # --- FileNotFoundError ---

    def test_file_not_found_sends_system_error(self, mocker):
        mock_send = mocker.patch("routers.telegram.photo.send_telegram_message")
        mock_delete = mocker.patch("routers.telegram.photo.delete_local_file")
        mocker.patch(
            "routers.telegram.photo.download_telegram_photo",
            side_effect=FileNotFoundError,
        )

        user_repo = mocker.MagicMock()
        user_repo.get_user.return_value = VALID_USER_INFO
        client = _build_client(user_repo)

        resp = client.post(WEBHOOK_PATH, json=_make_update())

        assert resp.status_code == 200
        mock_delete.assert_not_called()
        assert "fallas técnicas" in mock_send.call_args[0][2]

    # --- General exception ---

    def test_general_exception_sends_error(self, mocker):
        mock_send = mocker.patch("routers.telegram.photo.send_telegram_message")
        mock_delete = mocker.patch("routers.telegram.photo.delete_local_file")
        mocker.patch(
            "routers.telegram.photo.download_telegram_photo",
            side_effect=RuntimeError("boom"),
        )

        user_repo = mocker.MagicMock()
        user_repo.get_user.return_value = VALID_USER_INFO
        client = _build_client(user_repo)

        resp = client.post(WEBHOOK_PATH, json=_make_update())

        assert resp.status_code == 200
        mock_delete.assert_not_called()
        assert "problema al procesar" in mock_send.call_args[0][2]
