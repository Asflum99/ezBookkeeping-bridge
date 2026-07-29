from pathlib import Path

import httpx
import pytest
import respx

from services.telegram_file_service import delete_local_file, download_telegram_photo


class TestDownloadTelegramPhoto:
    TELEGRAM_BOT_TOKEN = "TOKEN"
    FILE_ID = "file123"

    @pytest.fixture(autouse=True)
    def setup_tmp_dir(self, monkeypatch, tmp_path):
        monkeypatch.setattr("services.telegram_file_service.TMP_DIR", tmp_path)

    @respx.mock
    async def test_download_raises_on_404(self):
        respx.get(
            f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/getFile?file_id={self.FILE_ID}"
        ).mock(return_value=httpx.Response(404))

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await download_telegram_photo(self.TELEGRAM_BOT_TOKEN, self.FILE_ID)

        assert exc_info.value.response.status_code == 404

    @respx.mock
    async def test_runtime_error_on_invalid_ok(self):
        respx.get(
            f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/getFile?file_id={self.FILE_ID}"
        ).mock(return_value=httpx.Response(200, json={"ok": False}))

        with pytest.raises(
            RuntimeError, match="Telegram was unable to process the file_id."
        ):
            await download_telegram_photo(self.TELEGRAM_BOT_TOKEN, self.FILE_ID)

    @respx.mock
    async def test_stream_download_raises_on_404(self):
        file_path = "photo.jpg"

        respx.get(
            f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/getFile?file_id={self.FILE_ID}"
        ).mock(
            return_value=httpx.Response(
                200, json={"ok": True, "result": {"file_path": file_path}}
            )
        )
        respx.get(
            f"https://api.telegram.org/file/bot{self.TELEGRAM_BOT_TOKEN}/{file_path}"
        ).mock(return_value=httpx.Response(404))

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await download_telegram_photo(self.TELEGRAM_BOT_TOKEN, self.FILE_ID)

        assert exc_info.value.response.status_code == 404

    @respx.mock
    async def test_download_success(self, tmp_path):
        file_path = "photo.jpg"

        respx.get(
            f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}/getFile?file_id={self.FILE_ID}"
        ).mock(
            return_value=httpx.Response(
                200, json={"ok": True, "result": {"file_path": "photo.jpg"}}
            )
        )

        respx.get(
            f"https://api.telegram.org/file/bot{self.TELEGRAM_BOT_TOKEN}/{file_path}"
        ).mock(return_value=httpx.Response(200, content=b"fake image bytes"))

        result = await download_telegram_photo(self.TELEGRAM_BOT_TOKEN, self.FILE_ID)

        assert result == str(tmp_path / f"{self.FILE_ID}.jpg")
        assert Path(result).read_bytes() == b"fake image bytes"


class TestDeleteLocalFile:
    def test_delete_existing_file(self, tmp_path):
        fake_file = tmp_path / "photo.jpg"
        fake_file.write_bytes(b"fake content")

        delete_local_file(str(fake_file))

        assert not fake_file.exists()

    def test_delete_logs_on_error(self, tmp_path, caplog, mocker):
        fake_file = tmp_path / "photo.jpg"
        fake_file.write_bytes(b"content")

        mocker.patch.object(
            Path, "unlink", side_effect=PermissionError("access denied")
        )

        delete_local_file(str(fake_file))

        assert "Failed to delete temporary file" in caplog.text
        assert fake_file.exists()
