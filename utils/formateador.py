import json
import os
from datetime import datetime


def preparar_gasto_para_ezbookkeeping(datos_ia: dict) -> dict:
    """
    Toma la fecha de la IA y procesa tanto formato de 24 horas
    como de 12 horas (AM/PM) tradicional en vouchers peruanos.
    """
    fecha_limpia = datos_ia.get("fecha_hora", "").strip()

    fecha_procesada = (
        fecha_limpia.replace("p.m.", "PM")
        .replace("p. m.", "PM")
        .replace("a.m.", "AM")
        .replace("a. m.", "AM")
        .replace("pm", "PM")
        .replace("am", "AM")
    )
    # Reemplazamos múltiples espacios por uno solo por si acaso quedó "10:24  PM"
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
        print(
            f"⚠️ No se pudo reconocer el formato de fecha: {fecha_limpia} (Procesada como: {fecha_procesada}). Usando fecha actual."
        )
        datos_ia["fecha_hora"] = int(datetime.now().timestamp())

    return datos_ia


def obtener_nombre_categoria(category_id: str) -> str:
    """Busca el nombre legible de la categoría en el JSON usando el ID"""
    ruta_json = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "categorias.json"
    )
    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            cat_map = json.load(f)
            return cat_map.get(str(category_id), "🛒 Otros Gastos (No mapeado)")
    except Exception:
        return "🛒 Otros Gastos"


def preparar_mensaje_confirmacion(datos_crudos: dict) -> str:
    """
    Toma los datos originales de la IA (legibles) y arma un mensaje
    estético y amigable para el usuario en Telegram.
    """
    monto = datos_crudos.get("monto", "0.00")
    descripcion = datos_crudos.get("comentario", "Desconocido")
    fecha = datos_crudos.get("fecha_hora")

    try:
        if fecha:
            timestamp_segundos = float(fecha)

            fecha_objeto = datetime.fromtimestamp(timestamp_segundos)

            fecha_bonita = fecha_objeto.strftime("%d-%m-%Y %I:%M %p").lower()
        else:
            fecha_bonita = "No detectada"
    except Exception as e:
        print(f"⚠️ No se pudo formatear el timestamp para el usuario: {e}")
        fecha_bonita = "Formato inválido"

    medio_pago_raw = datos_crudos.get("medio_pago", "")
    medios_traducidos = {
        "billetera_digital": "📱 Billetera Digital (Yape/Plin/Débito)",
        "tarjeta_credito": "💳 Tarjeta de Crédito BCP",
    }
    medio_pago_bonito = medios_traducidos.get(medio_pago_raw, "❓ Desconocido")

    id_categoria_ia = datos_crudos.get("categoria", "")
    categoria_bonita = obtener_nombre_categoria(id_categoria_ia)

    mensaje = (
        f"✅ ¡Gasto registrado con éxito!\n"
        f"💰 Monto: S/. {monto}\n"
        f"📝 *Descripción:* {descripcion}\n"
        f"📅 Fecha: {fecha_bonita}\n"
        f"💳 Método: {medio_pago_bonito}\n"
        f"🏷️ Categoría ID: {categoria_bonita}"
    )
    return mensaje
