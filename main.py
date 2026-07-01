import json
import os

import httpx
from fastapi import FastAPI, HTTPException, Request

from file_manager import borrar_archivo_local, descargar_foto_telegram
from services.ezbookkeeping_service import registrar_transaccion
from services.groq_service import procesar_gasto_con_ia
from utils.formateador import (
    preparar_gasto_para_ezbookkeeping,
    preparar_mensaje_confirmacion,
)

telegram_token_bot_raw = os.getenv("TELEGRAM_BOT_TOKEN")
usuarios_raw = os.getenv("USUARIOS_PERMITIDOS")

if not telegram_token_bot_raw or not usuarios_raw:
    raise ValueError(
        "❌ Falta configurar el BOT_TOKEN o la lista de USUARIOS_PERMITIDOS"
    )

TELEGRAM_TOKEN_BOT = telegram_token_bot_raw
USUARIOS_PERMITIDOS = set(os.getenv("USUARIOS_PERMITIDOS", "").split(","))

app = FastAPI()


def enviar_mensaje_telegram(chat_id: int, texto: str):
    """Función auxiliar para enviarle un mensaje de texto de vuelta al usuario"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN_BOT}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto}
    try:
        with httpx.Client() as client:
            client.post(url, json=payload)
    except Exception as e:
        print(f"❌ Error al enviar mensaje a Telegram: {e}")


@app.get("/")
def health_check():
    return {"status": "ok"}


def obtener_configuracion_usuario(chat_id: str) -> dict | None:
    """Busca el token del usuario en cuentas.json usando su chat_id de Telegram"""
    ruta_cuentas = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "cuentas.json"
    )
    try:
        with open(ruta_cuentas, "r", encoding="utf-8") as f:
            cuentas = json.load(f)
            return cuentas.get(str(chat_id))
    except Exception as e:
        print(f"❌ Error al leer cuentas.json: {e}")
        return None


@app.post("/webhook")
async def telegram_webhook(request: Request):
    payload = await request.json()

    chat_id = payload["message"]["chat"]["id"]
    user_id = str(payload["message"]["from"]["id"])

    if user_id not in USUARIOS_PERMITIDOS:
        print(f"🚫 Intento de acceso denegado para el ID: {user_id}")
        raise HTTPException(status_code=403, detail="Acceso no autorizado")

    if "photo" not in payload["message"]:
        print(f"⚠️ El usuario {user_id} envió algo que no es una foto.")
        enviar_mensaje_telegram(
            chat_id=chat_id,
            texto="Por ahora solo puedo recibir fotos de vouchers o boletas para registrar tus gastos. 📸",
        )
        return {
            "status": "success",
            "detail": "Contenido no soportado, advertencia enviada.",
        }

    fotos = payload["message"]["photo"]
    foto_optima = fotos[-1]  # El último elemento siempre es el de mayor tamaño
    file_id = foto_optima["file_id"]

    config_usuario = obtener_configuracion_usuario(chat_id)
    if not config_usuario:
        print(f"🚫 Acceso denegado o usuario no registrado para el chat_id: {chat_id}")
        enviar_mensaje_telegram(
            chat_id,
            "⛔ No estás registrado en el sistema del bot financiera. Pídele al administrador que te agregue.",
        )
        return {"status": "unauthorized"}

    try:
        ruta_foto_local = descargar_foto_telegram(TELEGRAM_TOKEN_BOT, file_id)

        datos_crudos_ia = procesar_gasto_con_ia(ruta_foto_local)

        datos_limpios = preparar_gasto_para_ezbookkeeping(datos_crudos_ia)

        medio_pago_ia: str = datos_limpios.get("medio_pago", "")
        cuentas_usuario: dict = config_usuario.get("cuentas", {})
        source_account_id: str = cuentas_usuario.get(medio_pago_ia, "")

        gasto_guardado = registrar_transaccion(
            datos_limpios, config_usuario["ez_token"], source_account_id
        )

        mensaje_para_usuario = preparar_mensaje_confirmacion(datos_crudos_ia)

        if gasto_guardado:
            enviar_mensaje_telegram(
                chat_id,
                mensaje_para_usuario,
            )
        else:
            enviar_mensaje_telegram(
                chat_id, "⚠️ Error al guardar en tu cuenta de ezBookkeeping."
            )

    except FileNotFoundError:
        print(
            "⚠️ Notificando al usuario sobre fallo del sistema interno (Falta de Prompt)."
        )
        enviar_mensaje_telegram(
            chat_id=chat_id,
            texto="⚙️ Lo siento, nuestro sistema interno está experimentando fallas técnicas en este momento. Por favor, vuelve a intentarlo más tarde. 🙏",
        )

    except Exception as e:
        print(f"❌ Error durante el procesamiento general: {e}")
        enviar_mensaje_telegram(
            chat_id=chat_id,
            texto="Hubo un problema al procesar la imagen de tu voucher. Inténtalo de nuevo. 😞",
        )

    finally:
        if ruta_foto_local:
            borrar_archivo_local(ruta_foto_local)
