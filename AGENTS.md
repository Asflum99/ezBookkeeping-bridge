 # AGENTS.md
 
 ## Project Overview
 
 Telegram finance bot built with **FastAPI** (Python 3.12) that receives voucher photos via Telegram webhook, extracts expense data using Groq/LangChain AI, and registers transactions in ezBookkeeping.
 
 ## Key Commands
 
 - **Development server**: `mise run dev` (starts uvicorn with `--reload` on `src/main`)
 - **Set Telegram webhook**: `mise run set-webhook <cloudflared-url>`
 - **Production server**: `mise run start` (uvicorn, no reload)
 
 ## Environment Setup
 
 1. Create `mise.local.toml` in repo root (git-ignored) with:
    ```toml
    [env]
    TELEGRAM_BOT_TOKEN = "your_token"
    USUARIOS_PERMITIDOS = "123456789,987654321"  # comma-separated Telegram IDs
    ```
 
 2. Run `uv sync` to install dependencies (managed via `pyproject.toml`).
 
 ## Architecture
 
 - **Entrypoint**: `src/main.py` (FastAPI app)
 - **Webhook endpoint**: `POST /webhook`
 - **Services**: `src/services/` (auth, Groq AI, ezBookkeeping, Telegram, user categories)
 - **Schemas**: `src/schemas.py` (Pydantic models for Telegram updates and business objects)
 - **Config**: `src/config/logger.py` (logging setup)
 - **Core**: `src/core/file_manager.py` (photo download/cleanup)
+- **Data**: `data/cuentas.json` (git-ignored, user-specific ezBookkeeping account mappings)
 - **Templates**: `src/templates/voucher_prompt.md` (Groq AI prompt for expense extraction; categories are dynamically inserted)
 
 ## Development Workflow
 
 1. Start dev server: `mise run dev`
 2. Start Cloudflare tunnel: `cloudflared tunnel --url http://localhost:8000`
 3. Set webhook: `mise run set-webhook <tunnel-url>`
 4. Verify webhook: `curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"`
 
 ## Important Notes
 
 - No test suite exists yet.
 - No linting/formatting configuration found.
 - The app requires `cloudflared` for local development (Telegram needs HTTPS).
 - Photos are downloaded to `tmp/` and deleted after processing.
 - Logs are written to `logs/` directory.
-- `cuentas.json` (git-ignored) stores user-specific ezBookkeeping account mappings.
+- `data/cuentas.json` (git-ignored) stores user-specific ezBookkeeping account mappings.
