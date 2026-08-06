import pytest
from helpers import SAMPLE_PHOTO, VALID_USER_INFO, WEBHOOK_PATH
from routers.telegram.webhook import get_user_repository

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers.telegram import router


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


def _make_text_update(**overrides):
    base = {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "date": 1700000000,
            "chat": {"id": 12345, "type": "private"},
            "from": {"id": 12345, "is_bot": False, "first_name": "Test"},
            "text": "/update-accounts",
        },
    }
    base.update(overrides)
    return base


class TestTelegramWebhook:
    def test_ignored_when_no_message(self, mocker):
        user_repo = mocker.MagicMock()
        client = _build_client(user_repo)

        resp = client.post(WEBHOOK_PATH, json={"update_id": 1})

        assert resp.status_code == 200
        assert resp.json()["detail"] == "No message"

    def test_ignored_when_no_photo(self, mocker):
        user_repo = mocker.MagicMock()
        client = _build_client(user_repo)

        payload = _make_photo_update(
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

    def test_returns_403_for_unauthorized_user(self, mocker):
        user_repo = mocker.MagicMock()
        client = _build_client(user_repo)

        payload = _make_photo_update()
        payload["message"]["from"]["id"] = 99999
        resp = client.post(WEBHOOK_PATH, json=payload)

        assert resp.status_code == 403
        user_repo.get_user.assert_not_called()

    @pytest.mark.parametrize("mock_send", ["webhook"], indirect=True)
    def test_unregistered_user_sends_warning(self, mocker, mock_send):
        user_repo = mocker.MagicMock()
        user_repo.get_user.return_value = None
        client = _build_client(user_repo)

        resp = client.post(WEBHOOK_PATH, json=_make_photo_update())

        assert resp.status_code == 200
        mock_send.assert_called_once()
        assert "No estás registrado" in mock_send.call_args[0][2]

    def test_photo_dispatches_to_handler(self, mocker):
        mock_handle = mocker.patch(
            "routers.telegram.webhook.handle_photo",
            return_value={"status": "success", "detail": "Photo processed"},
        )
        user_repo = mocker.MagicMock()
        user_repo.get_user.return_value = VALID_USER_INFO
        client = _build_client(user_repo)

        resp = client.post(WEBHOOK_PATH, json=_make_photo_update())

        assert resp.status_code == 200
        mock_handle.assert_called_once()
        assert resp.json()["detail"] == "Photo processed"

    def test_text_dispatches_to_accounts(self, mocker):
        mock_handle = mocker.patch(
            "routers.telegram.webhook.handle_update_accounts",
            return_value={"status": "success", "detail": "Accounts synced"},
        )
        user_repo = mocker.MagicMock()
        user_repo.get_user.return_value = VALID_USER_INFO
        client = _build_client(user_repo)

        resp = client.post(WEBHOOK_PATH, json=_make_text_update())

        assert resp.status_code == 200
        mock_handle.assert_called_once()
        assert resp.json()["detail"] == "Accounts synced"

    def test_update_accounts_command(self, mocker):
        mocker.patch(
            "routers.telegram.accounts.get_user_accounts",
            return_value=[{"id": "acc-1", "name": "BCP"}],
        )
        user_repo = mocker.MagicMock()
        user_repo.get_user.return_value = VALID_USER_INFO
        user_repo.sync_accounts.return_value = {
            "added": [{"id": "acc-1", "name": "BCP"}],
            "removed": [],
        }
        client = _build_client(user_repo)

        payload = _make_text_update(
            message={
                "message_id": 1,
                "date": 1700000000,
                "chat": {"id": 12345, "type": "private"},
                "from": {"id": 12345, "is_bot": False, "first_name": "Test"},
                "text": "/update-accounts",
            }
        )
        resp = client.post(WEBHOOK_PATH, json=payload)

        assert resp.status_code == 200
        user_repo.sync_accounts.assert_called_once()
