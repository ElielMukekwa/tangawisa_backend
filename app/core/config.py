from functools import lru_cache
import json
import os
from pathlib import Path
import tempfile

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_BACKEND_DIR = Path(__file__).resolve().parents[2]
_IS_VERCEL = bool(os.getenv("VERCEL"))
_DEFAULT_DATABASE_PATH = (
    Path(tempfile.gettempdir()) / "tangawisa_vercel.db"
    if _IS_VERCEL
    else _BACKEND_DIR / "tangawisa_dev.db"
)
_DEFAULT_APP_ENV = "production" if _IS_VERCEL else "development"
_DEFAULT_DATABASE_URL = f"sqlite:///{_DEFAULT_DATABASE_PATH.as_posix()}"
_DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000,"
    "http://localhost:8080,"
    "http://127.0.0.1:8000,"
    "null,"
    "https://tangawisa-backend-k7qwjdt3t-raphaell2000.vercel.app/"
)


def _parse_cors_origins(value: str) -> list[str]:
    cleaned_value = value.strip()
    if not cleaned_value:
        return []

    if cleaned_value.startswith("["):
        decoded_value = json.loads(cleaned_value)
        if not isinstance(decoded_value, list):
            raise ValueError("CORS_ORIGINS JSON value must be a list")
        return [str(origin).strip() for origin in decoded_value if str(origin).strip()]

    return [origin.strip() for origin in cleaned_value.split(",") if origin.strip()]


class Settings(BaseSettings):
    app_name: str = "Tangawisa API"
    app_env: str = _DEFAULT_APP_ENV
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    database_url: str = _DEFAULT_DATABASE_URL
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins_raw: str = Field(
        default=_DEFAULT_CORS_ORIGINS,
        validation_alias=AliasChoices("CORS_ORIGINS", "cors_origins"),
    )
    cors_origin_regex: str = r"^(https?://(localhost|127\.0\.0\.1)(:\d+)?|https://.*\.vercel\.app)$"
    bootstrap_database: bool = Field(
        default=True,
        validation_alias=AliasChoices("BOOTSTRAP_DATABASE", "bootstrap_database"),
    )
    seed_development_data: bool = Field(
        default=True,
        validation_alias=AliasChoices("SEED_DEVELOPMENT_DATA", "seed_development_data"),
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return _parse_cors_origins(self.cors_origins_raw)

    @property
    def should_seed_development_data(self) -> bool:
        return self.seed_development_data and self.app_env.lower() in {"dev", "development", "local"}

    @field_validator("app_name", mode="before")
    @classmethod
    def use_default_app_name_when_empty(cls, value: object) -> object:
        if value is None:
            return "Tangawisa API"
        if isinstance(value, str) and not value.strip():
            return "Tangawisa API"
        return value

    @field_validator("app_version", mode="before")
    @classmethod
    def use_default_app_version_when_empty(cls, value: object) -> object:
        if value is None:
            return "0.1.0"
        if isinstance(value, str) and not value.strip():
            return "0.1.0"
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def use_default_database_url_when_empty(cls, value: object) -> object:
        if value is None:
            return _DEFAULT_DATABASE_URL
        if isinstance(value, str) and not value.strip():
            return _DEFAULT_DATABASE_URL
        return value

    @field_validator("access_token_expire_minutes", mode="before")
    @classmethod
    def use_default_token_expiration_when_empty(cls, value: object) -> object:
        if value is None:
            return 60
        if isinstance(value, str) and not value.strip():
            return 60
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
