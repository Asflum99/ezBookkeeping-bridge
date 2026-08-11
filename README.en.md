English | [Español](README.md)

# ezBookkeeping-bridge

Backend built with **FastAPI** for recording expenses sent as voucher photos. Uses AI to extract structured data and registers transactions in ezBookkeeping.
Currently only works with Telegram bots.

## Features

- **Access control**: Filtered by authorized Telegram IDs.
- **AI extraction**: Sends voucher photos to LLM, gets category, amount, date, and payment method as JSON.
- **Automatic registration**: Creates transactions in ezBookkeeping via REST API.
- **User confirmation**: Replies on Telegram with the recorded data.

## Project Structure

```
src/
├── main.py                          # FastAPI entrypoint
├── config.py                        # Logging, paths, env vars
├── schemas.py                       # Pydantic models for Telegram webhook
├── database.py                      # SQLite connection + schema
├── formatter.py                     # Date validation, messages
├── routers/
│   └── telegram/
│       ├── __init__.py              # Router re-export
│       ├── webhook.py               # POST /, DI, dispatcher
│       ├── photo.py                 # Photo processing
│       └── utils.py                 # send_telegram_message
├── repositories/
│   └── user_repository.py           # SQLite CRUD
├── services/
│   ├── llm_service.py               # Multi-provider LLM integration
│   ├── ezbookkeeping_service.py     # ezBookkeeping API
│   └── telegram_file_service.py     # Photo download/cleanup
└── templates/
    └── voucher_prompt.md            # System prompt for LLM
```

## Requirements

- [**mise**](https://github.com/jdx/mise) — Python version management and task runner.
- [**uv**](https://github.com/astral-sh/uv) — Dependency management.
- [**cloudflared**](https://github.com/cloudflare/cloudflared) — HTTPS tunnel for local development.

## Setup

Copy `mise.local.toml.example` and modify it with your own credentials:

```bash
cp mise.local.toml.example mise.local.toml
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

Currently, the project only works with Telegram bots. For a guide on how to create one, click [here.](src/routers/telegram/README.en.md)

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

### 4. Verify

```bash
mise run verify-webhook
```

## Production Deployment

### 1. Prerequisites

1. [Telegram bot](src/routers/telegram/README.en.md)
2. [ezBookkeeping](https://github.com/mayswind/ezbookkeeping)

On the server hosting ezBookkeeping, clone this repository:

```bash
git clone https://github.com/Asflum99/ezBookkeeping-bridge
```

### 2. Start the server

```bash
mise run prod
```

### 3. Set the webhook

```bash
mise run set-webhook https://YOUR_URL
```

### 4. Verify

```bash
mise run verify-webhook
```
