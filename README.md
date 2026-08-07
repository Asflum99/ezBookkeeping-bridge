[English](README.en.md) | [Español](README.md)

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
│   ├── llm_service.py               # Integración multi-proveedor LLM
│   ├── ezbookkeeping_service.py     # API ezBookkeeping
│   └── telegram_file_service.py     # Descarga/eliminación de fotos
└── templates/
    └── voucher_prompt.md            # Prompt del sistema para LLM
```

## Requisitos

- [**mise**](https://github.com/jdx/mise) — gestión de versiones de Python y tareas.
- [**uv**](https://github.com/astral-sh/uv) — gestión de dependencias.
- [**cloudflared**](https://github.com/cloudflare/cloudflared) — túnel HTTPS para desarrollo local.

## Configuración

Copia `mise.local.toml.example` y luego modificalo con tus propias credenciales:

```bash
cp mise.local.toml.example mise.local.toml
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

Hasta el momento, el proyecto solo funciona con bots de Telegram. Para una guía sobre cómo crear uno, haz clic [aquí.](src/routers/telegram/README.md)

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

### 4. Verificar

```bash
mise run verify-webhook
```

## Desplegar en producción

### 1. Prerrequisitos

1. Bot de Telegram
2. ezBookkeeping

En el servidor donde se aloja ezBookkeeping deberás clonar este repositorio

```bash
git clone https://github.com/Asflum99/ezBookkeeping-bridge
```

### 2. Levantar el servidor

```bash
mise run prod
```

### 3. Vincular el webhook

```bash
mise run set-webhook https://TU_URL
```

### 4. Verificar

```bash
mise run verify-webhook
```
