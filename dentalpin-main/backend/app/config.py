"""Application configuration via environment variables."""

import warnings

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    # Independent secret used to sign the public-budget verification
    # cookies (ADR 0006). Falls back to ``SECRET_KEY`` for local/dev
    # convenience, but production deploys must set it explicitly so a
    # leak of one key does not compromise the other.
    BUDGET_PUBLIC_SECRET_KEY: str = ""

    # Environment
    ENVIRONMENT: str = "development"
    # Public demo instance: blocks operations that would lock out or break
    # the shared demo (user edits/removal, module install/uninstall/restart).
    DEMO_MODE: bool = False
    ALLOWED_ORIGINS: str = ""

    # Rate limiting
    LOGIN_RATE_LIMIT: str = "5/minute"
    REGISTER_RATE_LIMIT: str = "3/hour"

    # Testing
    TESTING: bool = False

    # Module system
    DENTAPEX_DEV_MODULE_SCAN: bool = True
    DENTAPEX_FRONTEND_ROOT: str = "/host_frontend"
    DENTAPEX_MODULE_LAYERS_MOUNT: str = "/module_layers"
    DENTAPEX_MODULE_PKG_ROOT: str = "/app/app/modules"

    DENTALPIN_DEV_MODULE_SCAN: bool = True  # Compatibility alias
    DENTALPIN_FRONTEND_ROOT: str = "/host_frontend"
    DENTALPIN_MODULE_LAYERS_MOUNT: str = "/module_layers"
    DENTALPIN_MODULE_PKG_ROOT: str = "/app/app/modules"

    # Storage configuration
    STORAGE_BACKEND: str = "local"
    STORAGE_LOCAL_PATH: str = "/app/storage"
    STORAGE_MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    STORAGE_ALLOWED_MIME_TYPES: str = "application/pdf,image/jpeg,image/png"

    @property
    def storage_allowed_mime_types_list(self) -> list[str]:
        """Parse allowed MIME types as list."""
        return [t.strip() for t in self.STORAGE_ALLOWED_MIME_TYPES.split(",")]

    # Email configuration
    EMAIL_ENABLED: bool = True
    EMAIL_PROVIDER: str = "console"  # console, smtp (sendgrid, mailgun in future)

    # SMTP configuration
    EMAIL_SMTP_HOST: str = "smtp.gmail.com"
    EMAIL_SMTP_PORT: int = 587
    EMAIL_SMTP_TLS: bool = True
    EMAIL_SMTP_USER: str = ""
    EMAIL_SMTP_PASSWORD: str = ""

    # Default sender
    EMAIL_FROM_ADDRESS: str = "noreply@dentapex.com"
    EMAIL_FROM_NAME: str = "DentApex"

    # Copilot / agentic layer (app/core/llm/).
    # Google Gemini Flash is the mandatory default to protect low-end clinic hardware.
    LLM_PROVIDER: str = "gemini"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    COPILOT_PROVIDER_DEFAULT: str = "gemini"
    COPILOT_MODEL_CHAT_GEMINI: str = "gemini-3.6-flash"
    COPILOT_MODEL_CHAT_GROQ: str = "openai/gpt-oss-120b"
    COPILOT_MODEL_CHAT_OLLAMA: str = "llama3.2"
    COPILOT_MODEL_CHAT_OPENAI: str = "gpt-5.4-mini"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434/v1"
    OLLAMA_MODELS_PATH: str = "data/ollama_models"
    COPILOT_MAX_TOKENS: int = 4096
    COPILOT_REDACTION_DEFAULT: bool = True

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse ALLOWED_ORIGINS as comma-separated list."""
        if not self.ALLOWED_ORIGINS:
            return []
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @model_validator(mode="after")
    def _validate_secret_key_strength(self) -> "Settings":
        """Reject a weak SECRET_KEY in production; warn everywhere else.

        SECRET_KEY signs JWTs and derives the Fernet key used to encrypt
        SMTP passwords and Veri*Factu tax certificates at rest (see
        GHSA-hcg9-cm67-2g8f) — a short/weak value compromises all three.
        A model_validator (not a field_validator on SECRET_KEY) is used
        because ENVIRONMENT is declared after SECRET_KEY, so a
        field_validator's `info.data` would not see it yet.
        """
        if len(self.SECRET_KEY) < MIN_SECRET_KEY_LENGTH:
            message = (
                f"SECRET_KEY must be at least {MIN_SECRET_KEY_LENGTH} "
                "characters (see .env.example: openssl rand -hex 32)."
            )
            if self.ENVIRONMENT == "production":
                raise ValueError(message)
            warnings.warn(message, stacklevel=2)
        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
