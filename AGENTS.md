# AGENTS.md

## Project Overview

Telegram finance bot. **FastAPI** (Python 3.12). Receives voucher photos via Telegram webhook, extracts expense data with Groq/LangChain AI, registers transactions in ezBookkeeping.

## Key Commands

- **Dev server**: `mise run dev` (uvicorn `--reload` on `src/main`)
- **Set webhook**: `mise run set-webhook <cloudflared-url>`
- **Prod server**: `mise run start` (uvicorn, no reload)

## Environment Setup

1. Create `mise.local.toml` in repo root (git-ignored):
   ```toml
   [env]
   TELEGRAM_BOT_TOKEN = "your_token"
   USUARIOS_PERMITIDOS = "123456789,987654321"  # comma-separated Telegram IDs
   ```

2. Run `uv sync` (deps managed via `pyproject.toml`).

## Architecture

- **Entrypoint**: `src/main.py` (FastAPI app)
- **Webhook**: `POST /webhook`
- **Services**: `src/services/` (auth, Groq AI, ezBookkeeping, Telegram, user categories)
- **Schemas**: `src/schemas.py` (Pydantic models for Telegram updates + business objects)
- **Config**: `src/config.py` (logging setup)
- **Data**: `data/cuentas.json` (git-ignored, user-specific ezBookkeeping account mappings)
- **Templates**: `src/templates/voucher_prompt.md` (Groq AI prompt for expense extraction; categories dynamically inserted)

## Dev Workflow

1. Start dev server: `mise run dev`
2. Start Cloudflare tunnel: `cloudflared tunnel --url http://localhost:8000`
3. Set webhook: `mise run set-webhook <tunnel-url>`
4. Verify webhook: `curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"`

## Version Control

- If `.jj/` folder exists in repo root → use `jj` (jujutsu).
- Otherwise → use `git`.

## Notes

- Tests in `tests/`.
- No linting/formatting config.
- App needs `cloudflared` for local dev (Telegram requires HTTPS).
- Photos downloaded to `tmp/`, deleted after processing.
- Logs written to `logs/`.
- `data/cuentas.json` (git-ignored) stores user-specific ezBookkeeping account mappings.
