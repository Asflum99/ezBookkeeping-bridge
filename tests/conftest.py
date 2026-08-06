import pytest

from config import settings


@pytest.fixture
def mock_send(mocker, request):
    if not hasattr(request, "param"):
        raise ValueError(
            "Debes parametrizar la fixture 'mock_send'. "
            "Ejemplo: @pytest.mark.parametrize('mock_send', ['text'], indirect=True)"
        )

    module_name = request.param
    return mocker.patch(f"routers.telegram.{module_name}.send_telegram_message")


@pytest.fixture(autouse=True)
def mock_config(monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "TOKEN")
    monkeypatch.setattr(settings, "allowed_users_raw", "12345")


@pytest.fixture()
def _mock_ezbookkeeping_url(monkeypatch):
    monkeypatch.setattr(settings, "ezbookkeeping_url", "http://test")
