import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from helpers import SAMPLE_PHOTO, SANITIZED_DATA, VALID_USER_INFO, WEBHOOK_PATH

from routers.telegram.webhook import get_user_repository, router


def _build_client(user_repo_mock):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_user_repository] = lambda: user_repo_mock
    return TestClient(app)


def _make_photo_update(**overrides):
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


class TestPhotoHandler:
    @pytest.mark.parametrize("mock_send", ["photo"], indirect=True)
    def test_full_flow(self, mocker, mock_send):
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

        resp = client.post(WEBHOOK_PATH, json=_make_photo_update())

        assert resp.status_code == 200
        mock_download.assert_called_once()
        mock_llm.assert_called_once()
        mock_validate.assert_called_once()
        mock_register.assert_called_once()
        mock_delete.assert_called_once_with("/tmp/photo.jpg")
        assert mock_send.call_count == 1
        assert "Gasto registrado" in mock_send.call_args[0][2]

    @pytest.mark.parametrize("mock_send", ["photo"], indirect=True)
    def test_transaction_fails_sends_error(self, mocker, mock_send):
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

        resp = client.post(WEBHOOK_PATH, json=_make_photo_update())

        assert resp.status_code == 200
        mock_delete.assert_called_once()
        assert "Error al guardar" in mock_send.call_args[0][2]

    @pytest.mark.parametrize("mock_send", ["photo"], indirect=True)
    def test_file_not_found_sends_system_error(self, mocker, mock_send):
        mock_delete = mocker.patch("routers.telegram.photo.delete_local_file")
        mocker.patch(
            "routers.telegram.photo.download_telegram_photo",
            side_effect=FileNotFoundError,
        )

        user_repo = mocker.MagicMock()
        user_repo.get_user.return_value = VALID_USER_INFO
        client = _build_client(user_repo)

        resp = client.post(WEBHOOK_PATH, json=_make_photo_update())

        assert resp.status_code == 200
        mock_delete.assert_not_called()
        assert "fallas técnicas" in mock_send.call_args[0][2]

    @pytest.mark.parametrize("mock_send", ["photo"], indirect=True)
    def test_general_exception_sends_error(self, mocker, mock_send):
        mock_delete = mocker.patch("routers.telegram.photo.delete_local_file")
        mocker.patch(
            "routers.telegram.photo.download_telegram_photo",
            side_effect=RuntimeError("boom"),
        )

        user_repo = mocker.MagicMock()
        user_repo.get_user.return_value = VALID_USER_INFO
        client = _build_client(user_repo)

        resp = client.post(WEBHOOK_PATH, json=_make_photo_update())

        assert resp.status_code == 200
        mock_delete.assert_not_called()
        assert "problema al procesar" in mock_send.call_args[0][2]
