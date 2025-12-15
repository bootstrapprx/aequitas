import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Determine which .env file to load
app_env = os.getenv("APP_ENV", "development")
env_file = ".env.dev" if app_env == "development" else ".env"

class Settings(BaseSettings):
    """
    Manages application-wide settings, loading from environment variables and .env files.
    Provides safe fallbacks for all integration-related settings, allowing the
    backend to boot and operate in a "manual" or "local-only" mode.
    """
    # --- Core Application Settings ---
    APP_ENV: str = "development"
    SECRET_KEY: str = "dev_key"
    ALLOW_MANUAL_DATA_FALLBACK: bool = True

    # --- Database Settings ---
    DATABASE_URL: str = "postgresql+psycopg2://user:password@localhost:5432/chartforge_dev"
    
    # --- Superuser Settings ---
    # New naming convention (preferred)
    DEFAULT_SUPERUSER_EMAIL: Optional[str] = None
    DEFAULT_SUPERUSER_PASSWORD: Optional[str] = None
    # Legacy naming (backward compatibility)
    FIRST_SUPERUSER: str = "admin@chartforge.com"
    FIRST_SUPERUSER_PASSWORD: str = "ChangeMe!123"

    # --- Registration Settings ---
    ALLOW_PUBLIC_SIGNUP: bool = False
    ALLOW_MOCK_PAYMENTS: bool = True  # Allow mock payments when Stripe not configured

    # --- OAuth Settings (Google, Microsoft, Apple) ---
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None
    OAUTH_STATE_SECRET: Optional[str] = None  # For signing CSRF state tokens

    # --- Stripe Settings (Optional) ---
    STRIPE_API_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_MOCK_MODE: bool = True  # Deprecated, use ALLOW_MOCK_PAYMENTS

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
    
    # Pydantic-Settings configuration
    model_config = SettingsConfigDict(
        env_file=env_file,
        env_file_encoding='utf-8',
        extra="ignore"  # Ignore unknown environment variables
    )

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
        return all([self.GOOGLE_CLIENT_ID, self.GOOGLE_CLIENT_SECRET, self.GOOGLE_REDIRECT_URI])

    @property
    def OAUTH_STATE_SECRET_KEY(self) -> str:
        """Returns the OAuth state signing secret, falling back to SECRET_KEY."""
        return self.OAUTH_STATE_SECRET or self.SECRET_KEY

# Instantiate the settings object
settings = Settings()

