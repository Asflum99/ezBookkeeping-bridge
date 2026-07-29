from pathlib import Path

import httpx

from config import PROJECT_ROOT, logger

TMP_DIR = PROJECT_ROOT / "tmp"


async def download_telegram_photo(telegram_bot_token: str, file_id: str) -> str:
    """
    Retrieves the file path from Telegram, downloads the photo to the tmp/ folder,
    and returns the local file path.
    """
    TMP_DIR.mkdir(exist_ok=True)

    info_url = (
        f"https://api.telegram.org/bot{telegram_bot_token}/getFile?file_id={file_id}"
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(info_url)
        response.raise_for_status()
        file_data = response.json()

        if not file_data.get("ok"):
            logger.error(f"Telegram API failed to process file_id: {file_id}")
            raise RuntimeError("Telegram was unable to process the file_id.")

        file_path = file_data["result"]["file_path"]
        download_url = (
            f"https://api.telegram.org/file/bot{telegram_bot_token}/{file_path}"
        )

        file_extension = Path(file_path).suffix
        local_destination = TMP_DIR / f"{file_id}{file_extension}"

        async with client.stream("GET", download_url) as stream_response:
            stream_response.raise_for_status()
            with open(local_destination, "wb") as f:
                async for chunk in stream_response.aiter_bytes():
                    f.write(chunk)

        logger.info(f"⬇️ File downloaded successfully to: {local_destination}")
        return str(local_destination)


def delete_local_file(file_path: str) -> None:
    """
    Safely deletes the specified local file if it exists.
    """
    try:
        Path(file_path).unlink(missing_ok=True)
        logger.info(f"🗑️ Temporary file deleted: {file_path}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to delete temporary file {file_path}. Error: {e}")
