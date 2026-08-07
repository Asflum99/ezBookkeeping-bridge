# ezBookkeeping-bridge

Backend desarrollado con **FastAPI** para registrar gastos enviados como fotos de vouchers. Usa IA para extraer datos estructurados y los registra en ezBookkeeping.
Actualmente solo funciona en bots de Telegram.

## Características

- **Control de acceso**: Filtrado por IDs de Telegram autorizados.
- **Extracción con IA**: Envía la foto del voucher a LLM, obtiene categoría, monto, fecha y método de pago en JSON.
- **Registro automático**: Crea la transacción en ezBookkeeping vía API REST.
- **Confirmación al usuario**: Responde por Telegram con los datos registrados.

## Estructura del Proyecto

```
src/
├── main.py                          # Entrypoint FastAPI
├── config.py                        # Logging, paths, env vars
├── schemas.py                       # Modelos Pydantic para Telegram webhook
├── database.py                      # Conexión SQLite + esquema
├── formatter.py                     # Validación de fechas, mensajes
├── routers/
│   └── telegram/
│       ├── __init__.py              # Router re-export
│       ├── webhook.py               # POST /, DI, dispatcher
│       ├── photo.py                 # Procesamiento de fotos
│       └── utils.py                 # send_telegram_message
├── repositories/
│   └── user_repository.py           # CRUD SQLite
├── services/
│   ├── llm_service.py               # Integración multi-proveedor LLM (Groq, OpenAI, Anthropic, Gemini via init_chat_model)
│   ├── ezbookkeeping_service.py     # API ezBookkeeping
│   └── telegram_file_service.py     # Descarga/eliminación de fotos
└── templates/
    └── voucher_prompt.md            # Prompt del sistema para LLM
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
ALLOWED_USERS = "123456789,987654321"    # IDs de Telegram autorizados
LLM_PROVIDER = "groq"                    # groq | openai | anthropic | gemini
LLM_MODEL = "..."
GROQ_API_KEY = "gsk_..."                 # si LLM_PROVIDER = "groq"
OPENAI_API_KEY = "sk-..."                # si LLM_PROVIDER = "openai"
ANTHROPIC_API_KEY = "sk-ant-..."         # si LLM_PROVIDER = "anthropic"
GOOGLE_API_KEY = "AIza..."               # si LLM_PROVIDER = "gemini"
EZBOOKKEEPING_URL = "https://..."
```

Luego instala dependencias:

```bash
uv sync
```

Instala el proveedor LLM que vayas a usar:

```bash
uv pip install -e ".[groq]"      # para Groq
uv pip install -e ".[openai]"    # para OpenAI
uv pip install -e ".[anthropic]" # para Anthropic
uv pip install -e ".[gemini]"    # para Google Gemini
uv pip install -e ".[all]"       # todos los proveedores
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
     -d '{"url": "https://TU_URL.trycloudflare.com/webhook/telegram/"}'
```

### 4. Verificar

```bash
mise run verify-webhook
```

o manualmente:

```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```
