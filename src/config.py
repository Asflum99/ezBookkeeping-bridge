import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from zoneinfo import ZoneInfo

import colorlog
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# --- Main routes ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)


# --- Config Class ---
class Settings(BaseSettings):
    # Routes
    database_path: Path = DATA_DIR / "bot.db"
    log_file: Path = LOGS_DIR / "bot.log"
    prompt_template_path: Path = (
        PROJECT_ROOT / "src" / "templates" / "voucher_prompt.md"
    )

    # Required environment variables
    llm_model: str
    ezbookkeeping_url: str
    llm_provider: str
    timezone_str: str = Field(alias="TIMEZONE")

    # Optional environment variables
    telegram_bot_token: str = ""
    allowed_users_raw: str = Field(default="", alias="ALLOWED_USERS")
    log_level: str = "INFO"

    # API Key per provider
    groq_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    _PROVIDER_API_KEY_FIELDS = {
        "groq": "groq_api_key",
        "openai": "openai_api_key",
        "anthropic": "anthropic_api_key",
        "gemini": "google_api_key",
    }

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Properties calculated and validations ---
    @property
    def allowed_users(self) -> set[int]:
        if not self.allowed_users_raw.strip():
            return set()
        return {int(uid) for uid in self.allowed_users_raw.split(",") if uid.strip()}

    @property
    def timezone(self) -> ZoneInfo:
        return ZoneInfo(self.timezone_str)

    @property
    def llm_api_key(self) -> str:
        field = self._PROVIDER_API_KEY_FIELDS.get(self.llm_provider)
        if not field:
            raise ValueError(f"Unsupported LLM provider: '{self.llm_provider}'")
        key = getattr(self, field)
        if not key:
            raise ValueError(f"Missing API key for LLM provider '{self.llm_provider}'")
        return key

    @property
    def system_prompt_template(self) -> str:
        if not self.prompt_template_path.exists():
            raise FileNotFoundError(
                f"System prompt template not found at {self.prompt_template_path}"
            )
        return self.prompt_template_path.read_text(encoding="utf-8")


# --- Settings' global instance ---
settings = Settings()


# --- Logging's configuration ---
def setup_logger() -> logging.Logger:
    log_numeric = getattr(logging, settings.log_level.upper(), logging.INFO)

    file_handler = RotatingFileHandler(
        settings.log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(
        colorlog.ColoredFormatter(
            fmt="%(log_color)s[%(asctime)s] [%(levelname)s]%(reset)s %(purple)s[%(filename)s:%(lineno)d]%(reset)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "magenta",
            },
        )
    )

    logging.basicConfig(level=log_numeric, handlers=[file_handler, stream_handler])

    # Silence external libraries to avoid tokens leak
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Silence external libraries to avoid tokens leak
    logging.getLogger("groq").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("gemini").setLevel(logging.WARNING)

    return logging.getLogger("bot_finanzas")


logger = setup_logger()
