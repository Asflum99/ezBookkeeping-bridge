# Telegram Finance Bot

Lightweight backend built with **FastAPI** for recording expenses sent as voucher photos from a private Telegram bot. Uses AI (Groq Vision) to extract structured data and registers transactions in ezBookkeeping.

## Features

- **Access control**: Filtered by authorized Telegram IDs.
- **AI extraction**: Sends voucher photos to Groq Vision, returns category, amount, date, and payment method as JSON.
- **Automatic registration**: Creates transactions in ezBookkeeping via REST API.
- **User confirmation**: Replies on Telegram with the recorded data.

## Project Structure

```
src/
├── main.py                          # FastAPI entrypoint
├── config.py                        # Logging and paths
├── schemas.py                       # Pydantic models for Telegram webhook
├── routers/
│   └── telegram.py                  # Webhook handler, auth, main flow
├── services/
│   ├── groq_service.py              # Groq Vision API integration
│   ├── ezbookkeeping_service.py     # ezBookkeeping API
│   └── telegram_file_service.py     # Photo download/cleanup
├── utils/
│   └── formatter.py                 # Date validation, confirmation messages
└── templates/
    └── voucher_prompt.md            # System prompt for Groq AI
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
ALLOWED_USERS = "123456789,987654321"
```

Then install dependencies:

```bash
uv sync
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
     -d '{"url": "https://YOUR_URL.trycloudflare.com/webhook"}'
```

### 4. Verify

```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```
