"""Centralised application settings.

All configuration is loaded from environment variables (or a local ``.env``
file) so that no secret is ever hard-coded. This is the single source of
truth for configuration across the whole application.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed, validated application settings.

    Using ``pydantic-settings`` gives us validation and type coercion for
    free: an invalid value fails fast at start-up instead of surfacing as a
    confusing runtime error later.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ------------------------------------------------------
    app_name: str = "MarketPulse Analytics API"
    environment: str = Field(default="development")
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # --- Security ---------------------------------------------------------
    # NEVER commit a real secret. In production this MUST be provided via the
    # environment. The default exists only so tests and local dev can run.
    secret_key: str = Field(
        default="dev-only-insecure-secret-change-me-in-production-0123456789"
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # --- Database ---------------------------------------------------------
    # Async driver URL used by the app at runtime.
    database_url: str = "sqlite+aiosqlite:///./marketpulse.db"
    # Sync driver URL used by Alembic migrations (Alembic is not async-aware).
    sync_database_url: str = "sqlite:///./marketpulse.db"
    db_echo: bool = False

    # --- External data sources -------------------------------------------
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    frankfurter_base_url: str = "https://api.frankfurter.dev/v1"
    http_timeout_seconds: float = 10.0

    # --- CORS -------------------------------------------------------------
    # Keep browser access explicit by default. For local frontend development,
    # set CORS_ORIGINS as a JSON list, e.g. ["http://localhost:3000"].
    cors_origins: list[str] = []
    cors_allow_credentials: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance.

    Caching avoids re-parsing the environment on every access and makes the
    settings object a de-facto singleton, which is what we want.
    """
    return Settings()


settings = get_settings()
