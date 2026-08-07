# ezBookkeeping-bridge

Backend built with **FastAPI** for recording expenses sent as voucher photos from a private Telegram bot. Uses AI to extract structured data and registers transactions in ezBookkeeping.
It currently works only on Telegram bots.

## Features

- **Access control**: Filtered by authorized Telegram IDs.
- **AI extraction**: Sends voucher photos to LLM, returns category, amount, date, and payment method as JSON.
- **Automatic registration**: Creates transactions in ezBookkeeping via REST API.
- **User confirmation**: Replies on Telegram with the recorded data.

## Project Structure

```
src/
├── main.py                          # FastAPI entrypoint
├── config.py                        # Logging, paths, env vars
├── schemas.py                       # Pydantic models for Telegram webhook
├── database.py                      # SQLite connection + schema
├── formatter.py                     # Date validation, confirmation messages
├── routers/
│   └── telegram/
│       ├── __init__.py              # Router re-export
│       ├── webhook.py               # POST /, DI, dispatcher
│       ├── photo.py                 # Photo processing
│       └── utils.py                 # send_telegram_message
├── repositories/
│   └── user_repository.py           # SQLite CRUD
├── services/
│   ├── llm_service.py               # Multi-provider LLM integration (Groq, OpenAI, Anthropic, Gemini via init_chat_model)
│   ├── ezbookkeeping_service.py     # ezBookkeeping API
│   └── telegram_file_service.py     # Photo download/cleanup
└── templates/
    └── voucher_prompt.md            # System prompt for LLM
```

## Requirements

- **mise** — Python version management and task runner.
- **uv** — Dependency management.
- **cloudflared** — HTTPS tunnel for local development.

## Setup

Create `mise.local.toml` in the project root (git-ignored):

```toml
[env]
TELEGRAM_BOT_TOKEN = "your_botfather_token"
ALLOWED_USERS = "123456789,987654321"    # Authorized Telegram IDs
LLM_PROVIDER = "groq"                    # groq | openai | anthropic | gemini
LLM_MODEL = "..."
GROQ_API_KEY = "gsk_..."                 # if LLM_PROVIDER = "groq"
OPENAI_API_KEY = "sk-..."                # if LLM_PROVIDER = "openai"
ANTHROPIC_API_KEY = "sk-ant-..."         # if LLM_PROVIDER = "anthropic"
GOOGLE_API_KEY = "AIza..."               # if LLM_PROVIDER = "gemini"
EZBOOKKEEPING_URL = "https://..."
```

Then install dependencies:

```bash
uv sync
```

Install the LLM provider you'll use:

```bash
uv pip install -e ".[groq]"      # for Groq
uv pip install -e ".[openai]"    # for OpenAI
uv pip install -e ".[anthropic]" # for Anthropic
uv pip install -e ".[gemini]"    # for Google Gemini
uv pip install -e ".[all]"       # all providers
```

## Local Development

### 1. Start the server

```bash
mise run dev
```

Server listens on `http://127.0.0.1:8000`.

### 2. Open Cloudflared tunnel

```bash
cloudflared tunnel --url http://localhost:8000
```

Copy the generated public URL (ends in `.trycloudflare.com`).

### 3. Set the webhook

```bash
mise run set-webhook https://YOUR_URL.trycloudflare.com
```

Or manually:

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://YOUR_URL.trycloudflare.com/webhook/telegram/"}'
```

### 4. Verify

```bash
mise run verify-webhook
```

or manually:

```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```
