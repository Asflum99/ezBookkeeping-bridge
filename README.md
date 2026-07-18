# Telegram Finance Bot

Backend ligero desarrollado con **FastAPI** para registrar gastos enviados como fotos de vouchers desde un bot privado de Telegram. Usa IA (Groq Vision) para extraer datos estructurados y los registra en ezBookkeeping.

## Características

- **Control de acceso**: Filtrado por IDs de Telegram autorizados.
- **Extracción con IA**: Envía la foto del voucher a Groq Vision, obtiene categoría, monto, fecha y método de pago en JSON.
- **Registro automático**: Crea la transacción en ezBookkeeping vía API REST.
- **Confirmación al usuario**: Responde por Telegram con los datos registrados.

## Estructura del Proyecto

```
src/
├── main.py                          # Entrypoint FastAPI
├── config.py                        # Logging y paths
├── schemas.py                       # Modelos Pydantic para Telegram webhook
├── routers/
│   └── telegram.py                  # Webhook handler, auth, flujo principal
├── services/
│   ├── groq_service.py              # Integración con Groq Vision API
│   ├── ezbookkeeping_service.py     # API ezBookkeeping
│   └── telegram_file_service.py     # Descarga/eliminación de fotos
├── utils/
│   └── formatter.py                 # Validación de fechas, mensajes de confirmación
└── templates/
    └── voucher_prompt.md            # Prompt del sistema para Groq AI
```

## Requisitos

- **mise** — gestión de versiones de Python y tareas.
- **uv** — gestión de dependencias.
- **cloudflared** — túnel HTTPS para desarrollo local.

## Configuración

Crea `mise.local.toml` en la raíz del proyecto (git-ignored):

```toml
[env]
TELEGRAM_BOT_TOKEN = "tu_token_de_botfather"
ALLOWED_USERS = "123456789,987654321"
```

Luego instala dependencias:

```bash
uv sync
```

## Desarrollo Local

### 1. Levantar el servidor

```bash
mise run dev
```

El servidor escucha en `http://127.0.0.1:8000`.

### 2. Abrir túnel con Cloudflared

```bash
cloudflared tunnel --url http://localhost:8000
```

Copia la URL pública generada (termina en `.trycloudflare.com`).

### 3. Vincular el webhook

```bash
mise run set-webhook https://TU_URL.trycloudflare.com
```

O manualmente:

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://TU_URL.trycloudflare.com/webhook"}'
```

### 4. Verificar

```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```
