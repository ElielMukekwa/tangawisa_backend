from functools import lru_cache
import json
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_BACKEND_DIR = Path(__file__).resolve().parents[2]
_DEFAULT_DATABASE_URL = f"sqlite:///{(_BACKEND_DIR / 'tangawisa_dev.db').as_posix()}"
_DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000,"
    "http://localhost:8080,"
    "http://127.0.0.1:8000,"
    "null"
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
    app_env: str = "development"
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
    cors_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return _parse_cors_origins(self.cors_origins_raw)

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
