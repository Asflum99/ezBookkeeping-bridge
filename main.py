import os

from fastapi import FastAPI, HTTPException, Request

# Validar que los secretos críticos existan antes de levantar el servidor
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
usuarios_raw = os.getenv("USUARIOS_PERMITIDOS")

# Validación inicial de seguridad
if not TELEGRAM_BOT_TOKEN or not usuarios_raw:
    raise ValueError(
        "❌ Falta configurar el BOT_TOKEN o la lista de USUARIOS_PERMITIDOS"
    )

USUARIOS_PERMITIDOS = set(os.getenv("USUARIOS_PERMITIDOS", "").split(","))

app = FastAPI(title="Agente Financiero - Telegram Bot")


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    payload = await request.json()

    user_id = str(payload["message"]["from"]["id"])

    if user_id not in USUARIOS_PERMITIDOS:
        print(f"🚫 Intento de acceso denegado para el ID: {user_id}")
        raise HTTPException(status_code=403, detail="Acceso no autorizado")

    print(f"📥 Mensaje recibido del usuario autorizado: {user_id}")
    return {"status": "success", "user_received": user_id}
