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
   ALLOWED_USERS = "123456789,987654321"  # comma-separated Telegram IDs
   LLM_PROVIDER = "groq"                        # groq | openai | anthropic | gemini
   LLM_MODEL = "..."   # model name for chosen provider
   GROQ_API_KEY = "gsk_..."                      # if LLM_PROVIDER = "groq"
   OPENAI_API_KEY = "sk-..."                     # if LLM_PROVIDER = "openai"
   ANTHROPIC_API_KEY = "sk-ant-..."              # if LLM_PROVIDER = "anthropic"
   GOOGLE_API_KEY = "AIza..."                    # if LLM_PROVIDER = "gemini"
   EZBOOKKEEPING_URL = "https://..."
   ```

2. Run `uv sync` (deps managed via `pyproject.toml`).

3. Install at least one LLM provider:
   ```bash
   uv pip install -e ".[groq]"      # for Groq (default)
   uv pip install -e ".[openai]"    # for OpenAI
   uv pip install -e ".[anthropic]" # for Anthropic
   uv pip install -e ".[gemini]"    # for Google Gemini
   uv pip install -e ".[all]"       # all providers
   ```

## Architecture

- **Entrypoint**: `src/main.py` (FastAPI app)
- **Webhook**: `POST /webhook/telegram`
- **Routers**: `src/routers/telegram/` (photo processing, webhook dispatch)
- **Services**: `src/services/` (Groq AI, ezBookkeeping, Telegram file)
- **Repositories**: `src/repositories/` (UserRepository - SQLite)
- **DI**: `src/routers/telegram/webhook.py` (get_user_repository)
- **Schemas**: `src/schemas.py` (Pydantic models for Telegram updates)
- **Config**: `src/config.py` (logging, database path)
- **Database**: `data/finanzas.db` (SQLite - users, accounts, categories)
- **Templates**: `src/templates/voucher_prompt.md` (Groq AI prompt)

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
- `data/finanzas.db` stores users, accounts, categories in SQLite.
