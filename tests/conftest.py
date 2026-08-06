import pytest


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
def mock_config(mocker):
    mocker.patch("routers.telegram.webhook.ALLOWED_USERS", {12345})
    mocker.patch("routers.telegram.webhook.TELEGRAM_BOT_TOKEN", "TOKEN")
    mocker.patch("routers.telegram.photo.TELEGRAM_BOT_TOKEN", "TOKEN")
    mocker.patch("routers.telegram.accounts.TELEGRAM_BOT_TOKEN", "TOKEN")


@pytest.fixture(autouse=True)
def mock_ezbookkeeping_url(monkeypatch):
    monkeypatch.setattr(
        "services.ezbookkeeping_service.EZBOOKKEEPING_URL", "http://test"
    )
