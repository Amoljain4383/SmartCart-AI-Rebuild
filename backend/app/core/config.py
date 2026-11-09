"""Application configuration via Pydantic BaseSettings."""
from typing import List, Union, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for SmartCart AI backend."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    APP_NAME: str = "SmartCart AI"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"

    # Security & JWT
    SECRET_KEY: str = "temporary_dev_secret_key_never_use_in_prod_1234567890abcdef"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str = "sqlite:///./smartcart.db"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        """Fix legacy postgres:// prefixes for SQLAlchemy 2.0 compatibility."""
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a list of strings."""
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Currency & Localization
    CURRENCY: str = "INR"

    # Out-of-band Admin Bootstrapping defaults
    ADMIN_INITIAL_EMAIL: str = "admin@smartcart.local"
    ADMIN_INITIAL_PASSWORD: str = "ChangeMeAdmin123!"
    ADMIN_INITIAL_NAME: str = "System Administrator"

    # PayPal Sandbox (for payment integration in Phase 4)
    PAYPAL_MODE: str = "sandbox"
    PAYPAL_CLIENT_ID: str = "sandbox_client_id_placeholder"
    PAYPAL_CLIENT_SECRET: str = "sandbox_client_secret_placeholder"
    PAYPAL_BASE_URL: str = "https://api-m.sandbox.paypal.com"
    PAYPAL_CURRENCY: str = "INR"
    PAYPAL_WEBHOOK_ID: Optional[str] = None

    # AI Shopping Copilot (Google Gemini)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.8-flash"

    @field_validator("GEMINI_API_KEY", mode="before")
    @classmethod
    def normalize_gemini_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Convert None, empty, or whitespace-only API keys to None, preserving non-empty keys."""
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v


settings = Settings()
