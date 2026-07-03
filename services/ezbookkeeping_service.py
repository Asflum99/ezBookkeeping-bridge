import logging
import os
import sys

import httpx

logger = logging.getLogger("bot_finanzas")

EZBOOKKEEPING_URL = os.getenv("EZBOOKKEEPING_URL")
if not EZBOOKKEEPING_URL:
    logger.critical(
        "❌ ERROR CRÍTICO: La variable de entorno EZBOOKKEEPING_URL no está configurada."
    )
    sys.exit(1)


def registrar_transaccion(
    datos_gasto: dict, token_usuario: str, source_account_id: str
) -> bool:
    """
    Envía el gasto usando el token específico del usuario que mandó el voucher.
    """
    url = f"{EZBOOKKEEPING_URL}/api/v1/transactions/add.json"

    headers = {
        "Authorization": f"Bearer {token_usuario}",
        "Content-Type": "application/json",
        "X-Timezone-Name": "America/Lima",
        "X-Timezone-Offset": "-300",
    }

    monto_centimos_entero = int(round(datos_gasto["monto"] * 100))

    body = {
        "type": 3,
        "categoryId": datos_gasto["categoria"],
        "sourceAmount": monto_centimos_entero,
        "time": datos_gasto["fecha_hora"],
        "comment": datos_gasto["comentario"],
        "sourceAccountId": source_account_id,
        "utcOffset": -300,
    }
    logger.debug(
        f"Iniciando registro de transacción con los siguientes valores:\n{body}"
    )

    try:
        with httpx.Client() as client:
            respuesta = client.post(url, json=body, headers=headers, timeout=10.0)
            logger.debug(f"respuesta de la solicitud POST: {respuesta.status_code}")
            if respuesta.status_code == 200:
                try:
                    res_json = respuesta.json()
                    if res_json.get("success"):
                        logger.info(
                            "¡Transacción registrada exitosamente en ezBookkeeping!"
                        )
                        return True
                except ValueError:
                    logger.error(
                        "❌ La API devolvió un estado 200 pero el cuerpo no era un JSON válido."
                    )
            logger.error(
                f"❌ Error API ezBookkeeping. Código: {respuesta.status_code}. Respuesta: {respuesta.text}"
            )
            return False
    except httpx.RequestError:
        logger.exception(
            "❌ Error de red o Timeout al intentar conectar con ezBookkeeping"
        )
        return False
    except Exception:
        logger.exception("❌ Error inesperado en la función registrar_transaccion")
        return False
