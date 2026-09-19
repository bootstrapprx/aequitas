import os
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine which .env file to load
app_env = os.getenv("APP_ENV", "development")
env_file = (".env.dev", ".env") if app_env == "development" else ".env"

class Settings(BaseSettings):
    """
    Manages application-wide settings, loading from environment variables and .env files.
    Provides safe fallbacks for all integration-related settings, allowing the
    backend to boot and operate in a "manual" or "local-only" mode.
    """
    # --- Core Application Settings ---
    APP_ENV: str = "development"
    # No usable secret defaults: production must fail closed when misconfigured.
    SECRET_KEY: str = ""
    ALLOW_MANUAL_DATA_FALLBACK: bool = False

    # --- Database Settings ---
    DATABASE_URL: str = "postgresql+psycopg2://user:password@localhost:5432/chartforge_dev"
    BACKEND_CORS_ORIGINS: str = ""
    
    # --- Superuser Settings ---
    # New naming convention (preferred)
    DEFAULT_SUPERUSER_EMAIL: Optional[str] = None
    DEFAULT_SUPERUSER_PASSWORD: Optional[str] = None
    # Legacy naming (backward compatibility)
    FIRST_SUPERUSER: str = "admin@chartforge.com"
    FIRST_SUPERUSER_PASSWORD: Optional[str] = None

    # --- Registration Settings ---
    ALLOW_PUBLIC_SIGNUP: bool = False
    ALLOW_MOCK_PAYMENTS: bool = False  # Enabled only for explicit development/test environments

    # --- AUTH RECOVERY – REMOVE AFTER FIXING GOOGLE OAUTH ---
    AUTH_RECOVERY_MODE: bool = False
    RECOVERY_ADMIN_EMAIL: Optional[str] = None
    RECOVERY_ADMIN_PASSWORD: Optional[str] = None
    ENABLE_GOOGLE_AUTH: bool = True

    # --- OAuth Settings (Google, Microsoft, Apple) ---
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None

    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_REDIRECT_URI: Optional[str] = None
    MICROSOFT_TENANT: str = "common"  # "common" for personal+org, "organizations", or specific tenant ID

    APPLE_CLIENT_ID: Optional[str] = None
    APPLE_TEAM_ID: Optional[str] = None
    APPLE_KEY_ID: Optional[str] = None
    APPLE_PRIVATE_KEY: Optional[str] = None  # Base64 encoded or file path
    APPLE_REDIRECT_URI: Optional[str] = None

    OAUTH_STATE_SECRET: Optional[str] = None  # For signing CSRF state tokens

    # --- Stripe Settings (Optional) ---
    STRIPE_API_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_MOCK_MODE: bool = False  # Deprecated, retained for compatibility

    # --- QuickBooks Online (QBO) Integration (Optional) ---
    QBO_CLIENT_ID: Optional[str] = None
    QBO_CLIENT_SECRET: Optional[str] = None
    QBO_REDIRECT_URI: Optional[str] = None
    QBO_ENVIRONMENT: str = "sandbox"

    # --- Organizer AI (Ollama) Settings (Optional) ---
    OLLAMA_HOST: Optional[str] = None
    OLLAMA_BASE_URL: Optional[str] = None
    OLLAMA_MODEL: Optional[str] = None
    ORGANIZER_MODEL_NAME: Optional[str] = None
    ORGANIZER_MAX_FEWSHOT: int = 10

    # --- Cloudflare AI Settings ---
    AI_PROVIDER: str = "ollama" # "ollama" or "cloudflare"
    CLOUDFLARE_ACCOUNT_ID: Optional[str] = None
    CLOUDFLARE_API_TOKEN: Optional[str] = None

    # --- Code Generator Settings ---
    CODE_PATTERN: str = "X.XX.XX.XX"
    CODE_SEGMENT_PAD: str = "0"
    CODE_SEPARATOR: str = "."
    CODE_MAX_LEVEL: int = 5

    # --- Integration Worker Service (Go) ---
    AEQUITAS_WORKER_URL: str = "http://localhost:8080"  # Go worker service URL

    # Pydantic-Settings configuration
    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding='utf-8',
        extra="ignore"  # Ignore unknown environment variables
    )

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        """Reject unsafe configuration before the application can serve traffic."""
        environment = self.APP_ENV.lower().strip()
        if environment != "test" and not self.SECRET_KEY:
            raise ValueError("SECRET_KEY must be configured outside test environments")

        if environment in {"production", "prod", "staging"}:
            if len(self.SECRET_KEY) < 32 or self.SECRET_KEY in {"dev_key", "changeme", "change-me"}:
                raise ValueError("SECRET_KEY must be a strong, unique value in production")
            if self.ALLOW_MOCK_PAYMENTS or self.STRIPE_MOCK_MODE:
                raise ValueError("Mock payments are forbidden outside development/test environments")
            if self.OAUTH_STATE_SECRET and len(self.OAUTH_STATE_SECRET) < 32:
                raise ValueError("OAUTH_STATE_SECRET must be a strong value in production")

        return self

    @property
    def SUPERUSER_EMAIL(self) -> str:
        """Returns the superuser email, preferring new naming."""
        return self.DEFAULT_SUPERUSER_EMAIL or self.FIRST_SUPERUSER

    @property
    def SUPERUSER_PASSWORD(self) -> Optional[str]:
        """Returns the superuser password, preferring new naming."""
        return self.DEFAULT_SUPERUSER_PASSWORD or self.FIRST_SUPERUSER_PASSWORD

    @property
    def QBO_INTEGRATION_ENABLED(self) -> bool:
        """Returns True if QBO is fully configured."""
        return all([self.QBO_CLIENT_ID, self.QBO_CLIENT_SECRET, self.QBO_REDIRECT_URI])

    @property
    def OLLAMA_INTEGRATION_ENABLED(self) -> bool:
        """Returns True if the Organizer AI (Ollama) is fully configured."""
        return all([self.OLLAMA_HOST, self.OLLAMA_MODEL])

    @property
    def STRIPE_ENABLED(self) -> bool:
        """Returns True if Stripe is configured."""
        return bool(self.STRIPE_API_KEY)

    @property
    def GOOGLE_OAUTH_ENABLED(self) -> bool:
        """Returns True if Google OAuth is fully configured."""
        if not self.ENABLE_GOOGLE_AUTH:
            return False
        return all([self.GOOGLE_CLIENT_ID, self.GOOGLE_CLIENT_SECRET, self.GOOGLE_REDIRECT_URI])

    @property
    def MICROSOFT_OAUTH_ENABLED(self) -> bool:
        """Returns True if Microsoft OAuth is fully configured."""
        return all([self.MICROSOFT_CLIENT_ID, self.MICROSOFT_CLIENT_SECRET, self.MICROSOFT_REDIRECT_URI])

    @property
    def APPLE_OAUTH_ENABLED(self) -> bool:
        """Returns True if Apple Sign-In is fully configured."""
        return all([
            self.APPLE_CLIENT_ID,
            self.APPLE_TEAM_ID,
            self.APPLE_KEY_ID,
            self.APPLE_PRIVATE_KEY,
            self.APPLE_REDIRECT_URI
        ])

    @property
    def OAUTH_STATE_SECRET_KEY(self) -> str:
        """Returns the OAuth state signing secret, falling back to SECRET_KEY."""
        return self.OAUTH_STATE_SECRET or self.SECRET_KEY

# Instantiate the settings object
settings = Settings()


def get_settings() -> Settings:
    """
    FastAPI dependency to inject settings.
    Returns the global settings instance.
    """
    return settings
