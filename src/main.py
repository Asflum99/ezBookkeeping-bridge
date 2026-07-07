import os
import sys
from typing import List

from fastapi import FastAPI, HTTPException

from config.logger import logger
from core.file_manager import borrar_archivo_local, descargar_foto_telegram
from core.usuarios import verificar_registro_usuario
from schemas import TelegramMessage, TelegramPhotoSize, TelegramUpdate
from services.ezbookkeeping_service import registrar_transaccion
from services.groq_service import procesar_gasto_con_ia
from services.telegram_service import enviar_mensaje_telegram
from utils.formateador import (
    preparar_fecha_para_ezbookkeeping,
    preparar_mensaje_confirmacion,
)

# ==========================================
# ⚙️ CONFIGURACIONES GLOBALES E INICIALIZACIÓN
# ==========================================

telegram_bot_token_raw = os.getenv("TELEGRAM_BOT_TOKEN")
usuarios_raw = os.getenv("USUARIOS_PERMITIDOS")

if not telegram_bot_token_raw or not usuarios_raw:
    logger.critical(
        "❌ Falta configurar el BOT_TOKEN o la lista de USUARIOS_PERMITIDOS"
    )
    sys.exit(1)

TELEGRAM_TOKEN_BOT = telegram_bot_token_raw
USUARIOS_PERMITIDOS = set(
    int(uid.strip()) for uid in usuarios_raw.split(",")
)  # TODO: Preguntar por qué funciona

app = FastAPI()

# ==========================================
# Functions auxiliares
# ==========================================


def validar_acceso_y_contenido(
    message: TelegramMessage, user_id: int, chat_id: int
) -> bool:
    """
    Valida si el usuario está en la lista blanca y si envió una foto.
    Devuelve True si todo está correcto, False si debe detenerse el flujo.
    """
    if user_id not in USUARIOS_PERMITIDOS:
        logger.warning(
            f"🚫 Intento de acceso denegado para el ID de Telegram: {user_id}"
        )
        raise HTTPException(status_code=403, detail="Acceso no autorizado")

    if not message.photo:
        logger.info(f"💡 El usuario {user_id} envió algo que no es una foto.")
        enviar_mensaje_telegram(
            TELEGRAM_TOKEN_BOT,
            chat_id=chat_id,
            texto="Por ahora solo puedo recibir fotos de vouchers o boletas para registrar tus gastos. 📸",
        )
        return False

    return True


def obtener_foto_optima_id(photo: List[TelegramPhotoSize]) -> str:
    """Extrae el file_id de la imagen con mayor resolución."""
    fotos = photo
    foto_optima = fotos[-1]  # El último elemento siempre es el más grande
    file_id = foto_optima.file_id
    logger.debug(f"Foto óptima detectada a procesar: {file_id}")
    return file_id


# ==========================================
# Endpoints
# ==========================================


@app.get("/")
def health_check():
    return {"status": "ok"}


# TODO: Cambiar el path a /webhook/telegram
@app.post("/webhook")
async def telegram_webhook(payload: TelegramUpdate):
    if not payload.message:
        logger.info(
            f"💡 Se recibió un update de Telegram (ID: {payload.update_id}) que no contiene un mensaje común. Ignorando flujo."
        )
        return {
            "status": "success",
            "detail": "Update recibido pero no contiene un 'message' válido para procesar.",
        }

    chat_id = payload.message.chat.id
    if not payload.message.from_user:
        logger.info(
            f"No se pudo encontrar el usuario autor del mensaje de Telegram (ID: {payload.message})"
        )
        return {
            "status": "success",
            "detail": "Mensaje recibido, pero no se pudo identificar al autor.",
        }
    user_id = payload.message.from_user.id

    if not validar_acceso_y_contenido(payload.message, user_id, chat_id):
        return {
            "status": "success",
            "detail": "Contenido no soportado o flujo controlado.",
        }

    if not payload.message.photo:
        logger.info(
            f"No se pudo encontrar imágenes en el mensaje de Telegram (ID: {payload.message})"
        )
        return {
            "status": "success",
            "detail": "No hay imágenes en el mensaje de Telegram.",
        }

    file_id = obtener_foto_optima_id(payload.message.photo)

    user_info = verificar_registro_usuario(TELEGRAM_TOKEN_BOT, user_id, chat_id)
    if not user_info:
        return

    ruta_foto_local = None
    try:
        ruta_foto_local = descargar_foto_telegram(TELEGRAM_TOKEN_BOT, file_id)

        datos_crudos_ia = procesar_gasto_con_ia(ruta_foto_local)
        datos_limpios = preparar_fecha_para_ezbookkeeping(datos_crudos_ia)

        medio_pago_ia: str = datos_limpios.get("medio_pago", "")
        cuentas_usuario: dict = user_info.get("cuentas", {})
        source_account_id: str = cuentas_usuario.get(medio_pago_ia, "")

        # Guarda el texto original entregado por la IA (ej: "Comida")
        categoria_texto_original = datos_limpios.get("categoria", "")
        mapa_categorias_usuario = user_info.get("categorias", {})

        # Busca el ID numérico correspondiente en el JSON del usuario
        id_categoria_final = mapa_categorias_usuario.get(
            categoria_texto_original, mapa_categorias_usuario.get("Otros Gastos")
        )

        if not id_categoria_final:
            logger.error(
                f"❌ No se pudo determinar un ID de categoría válido para el usuario {user_id}. "
                f"Texto IA: '{categoria_texto_original}'. Asegúrate de que 'Otros Gastos' exista en cuentas.json."
            )
            enviar_mensaje_telegram(
                TELEGRAM_TOKEN_BOT,
                chat_id,
                "⚠️ No pude clasificar este gasto. Por favor, verifica la categoría en el voucher.",
            )
            return {
                "status": "error",
                "detail": "Categoría no encontrada o no mapeada.",
            }

        # Reemplaza el texto por el ID numérico final antes de enviar a la API
        datos_limpios["categoria"] = id_categoria_final

        gasto_guardado = registrar_transaccion(
            datos_limpios, user_info, source_account_id
        )

        # Reemplaza el campo con el nombre bonito original para armar la confirmación de Telegram
        datos_crudos_ia["categoria"] = f"📝 {categoria_texto_original}"
        mensaje_para_usuario = preparar_mensaje_confirmacion(datos_crudos_ia)

        if gasto_guardado:
            enviar_mensaje_telegram(
                TELEGRAM_TOKEN_BOT,
                chat_id,
                mensaje_para_usuario,
            )
        else:
            enviar_mensaje_telegram(
                TELEGRAM_TOKEN_BOT,
                chat_id,
                "⚠️ Error al guardar en tu cuenta de ezBookkeeping.",
            )

    except FileNotFoundError:
        logger.critical(
            "⚠️ Notificando al usuario sobre fallo del sistema interno (Falta de Prompt)."
        )
        enviar_mensaje_telegram(
            TELEGRAM_TOKEN_BOT,
            chat_id=chat_id,
            texto="⚙️ Lo siento, nuestro sistema interno está experimentando fallas técnicas en este momento. Por favor, vuelve a intentarlo más tarde. 🙏",
        )

    except Exception:
        logger.critical("❌ Error durante el procesamiento general:")
        enviar_mensaje_telegram(
            TELEGRAM_TOKEN_BOT,
            chat_id=chat_id,
            texto="Hubo un problema al procesar la imagen de tu voucher. Inténtalo de nuevo. 😞",
        )

    finally:
        # 💡 Se unificó el log para que solo se ejecute si realmente hay algo que borrar
        if ruta_foto_local:
            logger.info("Iniciando proceso de borrado de la foto del voucher")
            borrar_archivo_local(ruta_foto_local)
