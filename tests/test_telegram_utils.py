import httpx
import respx

from routers.telegram.utils import settings, init_config, send_telegram_message


class TestInitConfig:
    def test_populates_settings_from_env(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token-123")
        monkeypatch.setenv("ALLOWED_USERS", "111,222,333")

        init_config()

        assert settings["token"] == "test-token-123"
        assert settings["allowed_users"] == {111, 222, 333}

    def test_settings_empty_before_init(self):
        settings.clear()

        assert settings == {}

    def test_settings_overwrites_previous_values(self, monkeypatch):
        settings["token"] = "old-token"
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "new-token")
        monkeypatch.setenv("ALLOWED_USERS", "999")

        init_config()

        assert settings["token"] == "new-token"


class TestSendTelegramMessage:
    TELEGRAM_URL = "https://api.telegram.org/bot{token}/sendMessage"

    @respx.mock
    def test_sends_message_successfully(self):
        token = "test-token"
        chat_id = 12345
        text = "Hola mundo"

        respx.post(self.TELEGRAM_URL.format(token=token)).mock(
            return_value=httpx.Response(200, json={"ok": True})
        )

        send_telegram_message(token, chat_id, text)

        assert respx.calls.call_count == 1
        request = respx.calls[0].request
        assert request.content is not None

    @respx.mock
    def test_handles_exception_gracefully(self, caplog):
        token = "test-token"
        chat_id = 12345
        text = "Test message"

        respx.post(self.TELEGRAM_URL.format(token=token)).mock(
            side_effect=RuntimeError("Unexpected error")
        )

        send_telegram_message(token, chat_id, text)

        assert "Failed to send Telegram message" in caplog.text

    def test_handles_network_error_gracefully(self, caplog):
        token = "test-token"
        chat_id = 12345
        text = "Test message"

        with respx.mock:
            respx.post(self.TELEGRAM_URL.format(token=token)).mock(
                side_effect=httpx.ConnectError("Connection refused")
            )

            send_telegram_message(token, chat_id, text)

        assert "Failed to send Telegram message" in caplog.text
