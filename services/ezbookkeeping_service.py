import os

import httpx

EZBOOKKEEPING_URL = os.getenv("EZBOOKKEEPING_URL")
if not EZBOOKKEEPING_URL:
    print(
        "❌ ERROR CRÍTICO: La variable de entorno EZBOOKKEEPING_URL no está configurada."
    )


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

    try:
        with httpx.Client() as client:
            respuesta = client.post(url, json=body, headers=headers, timeout=10.0)
            if respuesta.status_code == 200 and respuesta.json().get("success"):
                return True
            print(f"❌ Error API ezBookkeeping: {respuesta.text}")
            return False
    except Exception as e:
        print(f"❌ Error de red en ezBookkeeping: {e}")
        return False
