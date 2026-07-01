import os

import httpx

TMP_DIR = "tmp"


def asegurar_carpeta_temporal():
    """Crea la carpeta tmp si no existe"""
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)
        print(f"📁 Carpeta temporal '{TMP_DIR}' creada.")


def descargar_foto_telegram(telegram_token_bot: str, file_id: str) -> str:
    """
    Pide la ruta a Telegram, descarga la foto en tmp/ y retorna la ruta local.
    """
    asegurar_carpeta_temporal()

    url_info = (
        f"https://api.telegram.org/bot{telegram_token_bot}/getFile?file_id={file_id}"
    )

    with httpx.Client() as client:
        response = client.get(url_info)
        response.raise_for_status()
        datos_archivo = response.json()

        if not datos_archivo.get("ok"):
            raise Exception("Telegram no pudo procesar el file_id")

        file_path = datos_archivo["result"]["file_path"]
        print(file_path)

        url_descarga = (
            f"https://api.telegram.org/file/bot{telegram_token_bot}/{file_path}"
        )

        extension = os.path.splitext(file_path)[1]
        ruta_local_destino = os.path.join(TMP_DIR, f"{file_id}{extension}")

        with client.stream("GET", url_descarga) as stream_response:
            stream_response.raise_for_status()
            with open(ruta_local_destino, "wb") as f:
                for chunk in stream_response.iter_bytes():
                    f.write(chunk)

        print(f"⬇️ Archivo guardado localmente en: {ruta_local_destino}")
        return ruta_local_destino


def borrar_archivo_local(ruta_archivo: str):
    """Elimina el archivo temporal de forma segura"""
    try:
        if os.path.exists(ruta_archivo):
            os.remove(ruta_archivo)
            print(f"🗑️ Archivo temporal eliminado: {ruta_archivo}")
    except Exception as e:
        print(f"⚠️ No se pudo borrar el archivo {ruta_archivo}: {e}")
