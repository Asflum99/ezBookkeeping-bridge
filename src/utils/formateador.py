import logging
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger("bot_finanzas")


def preparar_fecha_para_ezbookkeeping(datos_ia: dict) -> dict:
    """
    Toma la fecha de la IA y procesa tanto formato de 24 horas
    como de 12 horas (AM/PM) tradicional en vouchers peruanos.
    """
    logger.info("Iniciando limpieza de fecha para poder registrarlo en ezbookkeeping")
    logger.debug(f"Datos recibidos:\n{datos_ia}")

    fecha_limpia = datos_ia.get("fecha_hora", "").strip()

    fecha_procesada = (
        fecha_limpia.replace("p.m.", "PM")
        .replace("p. m.", "PM")
        .replace("a.m.", "AM")
        .replace("a. m.", "AM")
        .replace("pm", "PM")
        .replace("am", "AM")
    )
    fecha_procesada = " ".join(fecha_procesada.split())

    formatos_a_intentar = [
        "%d-%m-%Y %H:%M:%S",  # 29-06-2026 18:28:00
        "%d-%m-%Y %H:%M",  # 29-06-2026 18:28
        "%d-%m-%Y %I:%M:%S %p",  # 29-06-2026 06:28:00 PM
        "%d-%m-%Y %I:%M %p",  # 29-06-2026 06:28 PM
    ]

    fecha_objeto = None

    for formato in formatos_a_intentar:
        try:
            fecha_objeto = datetime.strptime(fecha_procesada, formato)
            break
        except ValueError:
            continue

    if fecha_objeto:
        datos_ia["fecha_hora"] = int(fecha_objeto.timestamp())
    else:
        logger.warning(
            f"⚠️ No se pudo reconocer el formato de fecha: {fecha_limpia} (Procesada como: {fecha_procesada}). Usando fecha actual."
        )
        datos_ia["fecha_hora"] = int(datetime.now().timestamp())

    logger.info("Retornando fecha ya procesada")
    return datos_ia


def preparar_mensaje_confirmacion(datos_crudos: dict) -> str:
    """
    Toma los datos originales de la IA (legibles) y arma un mensaje
    estético y amigable para el usuario en Telegram.
    """
    logger.info("Iniciando limpieza de datos para enviárselo al usuario por Telegram")

    monto = datos_crudos.get("monto", "0.00")
    descripcion = datos_crudos.get("comentario", "Desconocido")
    fecha = datos_crudos.get("fecha_hora")

    try:
        if fecha:
            timestamp_segundos = float(fecha)
            fecha_objeto = datetime.fromtimestamp(
                timestamp_segundos, tz=ZoneInfo("America/Lima")
            )
            fecha_bonita = fecha_objeto.strftime("%d-%m-%Y %I:%M %p").lower()
        else:
            logger.warning("No se encontró fecha, usando valor placeholder")
            fecha_bonita = "No detectada"
    except Exception as e:
        logger.warning(f"⚠️ No se pudo formatear el timestamp para el usuario: {e}")
        fecha_bonita = "Formato inválido"

    medio_pago_raw = datos_crudos.get("medio_pago", "")
    medios_traducidos = {
        "billetera_digital": "📱 Billetera Digital (Yape/Plin/Débito)",
        "tarjeta_credito": "💳 Tarjeta de Crédito",
    }
    medio_pago_bonito = medios_traducidos.get(medio_pago_raw, "❓ Desconocido")

    categoria_bonita = datos_crudos.get("categoria", "❓ Desconocida")

    mensaje = (
        f"✅ ¡Gasto registrado con éxito!\n\n"
        f"💰 Monto: S/. {monto}\n"
        f"📝 Descripción: {descripcion}\n"
        f"📅 Fecha: {fecha_bonita}\n"
        f"💳 Método: {medio_pago_bonito}\n"
        f"🏷️ Categoría: {categoria_bonita}"
    )
    return mensaje
