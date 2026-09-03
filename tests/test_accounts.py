import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from helpers import VALID_USER_INFO, WEBHOOK_PATH, make_text_update

from routers.telegram.webhook import get_user_repository, router


def _build_client(user_repo_mock):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_user_repository] = lambda: user_repo_mock
    return TestClient(app)


class TestUpdateAccounts:
    @pytest.mark.parametrize("mock_send", ["sync"], indirect=True)
    def test_api_failure(self, mocker, mock_send):
        user_repo = mocker.MagicMock()
        user_repo.get_user.return_value = VALID_USER_INFO
        client = _build_client(user_repo)

        resp = client.post(WEBHOOK_PATH, json=make_text_update())

        assert resp.status_code == 200
        assert "Error" in mock_send.call_args[0][2]

    @pytest.mark.parametrize("mock_send", ["sync"], indirect=True)
    def test_happy_path(self, mocker, mock_send):
        mocker.patch(
            "routers.telegram.sync.get_user_accounts",
            return_value=[{"id": "acc-1", "name": "BCP"}],
        )
        user_repo = mocker.MagicMock()
        user_repo.get_user.return_value = VALID_USER_INFO
        user_repo.sync_accounts.return_value = {
            "added": [{"id": "acc-1", "name": "BCP"}],
            "removed": [],
            "updated": [],
        }
        client = _build_client(user_repo)

        resp = client.post(WEBHOOK_PATH, json=make_text_update())

        assert resp.status_code == 200
        user_repo.sync_accounts.assert_called_once()
        assert "+1" in mock_send.call_args[0][2]
