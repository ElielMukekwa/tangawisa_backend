from functools import lru_cache
import json
import os
from pathlib import Path
import tempfile
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import AliasChoices, Field, field_validator, model_validator
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


def _default_cors_origins() -> str:
    origins = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8000",
    ]
    vercel_url = os.getenv("VERCEL_URL", "").strip().strip("/")
    if vercel_url:
        origins.append(f"https://{vercel_url}")
    return ",".join(origins)


def _parse_cors_origins(value: str) -> list[str]:
    cleaned_value = value.strip()
    if not cleaned_value:
        return []

    if cleaned_value.startswith("["):
        decoded_value = json.loads(cleaned_value)
        if not isinstance(decoded_value, list):
            raise ValueError("CORS_ORIGINS JSON value must be a list")
        return [
            str(origin).strip().rstrip("/")
            for origin in decoded_value
            if str(origin).strip()
        ]

    return [
        origin.strip().rstrip("/")
        for origin in cleaned_value.split(",")
        if origin.strip()
    ]


def _normalize_database_url(value: str) -> str:
    database_url = value.strip()
    if database_url.startswith("postgres://"):
        database_url = f"postgresql://{database_url.removeprefix('postgres://')}"

    parsed_url = urlparse(database_url)
    hostname = parsed_url.hostname or ""
    if parsed_url.scheme.startswith("postgresql") and "supabase" in hostname:
        query_items = dict(parse_qsl(parsed_url.query, keep_blank_values=True))
        query_items.setdefault("sslmode", "require")
        database_url = urlunparse(parsed_url._replace(query=urlencode(query_items)))

    return database_url


class Settings(BaseSettings):
    app_name: str = "Tangawisa API"
    app_env: str = _DEFAULT_APP_ENV
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    database_url: str = _DEFAULT_DATABASE_URL
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    supabase_url: str | None = None
    supabase_secret_key: str | None = None
    supabase_storage_bucket: str = "site-presentation"
    media_storage_backend: Literal["local", "supabase"] = (
        "supabase" if _IS_VERCEL else "local"
    )
    cors_origins_raw: str = Field(
        default_factory=_default_cors_origins,
        validation_alias=AliasChoices("CORS_ORIGINS", "cors_origins"),
    )
    cors_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    bootstrap_database: bool = Field(
        default=not _IS_VERCEL,
        validation_alias=AliasChoices("BOOTSTRAP_DATABASE", "bootstrap_database"),
    )
    seed_development_data: bool = Field(
        default=not _IS_VERCEL,
        validation_alias=AliasChoices("SEED_DEVELOPMENT_DATA", "seed_development_data"),
    )
    disable_database_pooling: bool = Field(
        default=_IS_VERCEL,
        validation_alias=AliasChoices("DISABLE_DATABASE_POOLING", "disable_database_pooling"),
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def cors_origins(self) -> list[str]:
        return _parse_cors_origins(self.cors_origins_raw)

    @property
    def should_seed_development_data(self) -> bool:
        return self.seed_development_data and self.app_env.lower() in {"dev", "development", "local"}

    @property
    def uses_supabase_storage(self) -> bool:
        return self.media_storage_backend == "supabase"

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
        if isinstance(value, str):
            return _normalize_database_url(value)
        return value

    @field_validator("access_token_expire_minutes", mode="before")
    @classmethod
    def use_default_token_expiration_when_empty(cls, value: object) -> object:
        if value is None:
            return 60
        if isinstance(value, str) and not value.strip():
            return 60
        return value

    @field_validator("supabase_url", mode="before")
    @classmethod
    def normalize_supabase_url(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().rstrip("/") or None
        return value

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        if self.app_env.lower() not in {"prod", "production"}:
            return self

        errors: list[str] = []
        if self.database_url.startswith("sqlite"):
            errors.append("DATABASE_URL doit pointer vers PostgreSQL/Supabase")
        if self.jwt_secret_key == "change-me-in-production" or len(self.jwt_secret_key) < 32:
            errors.append("JWT_SECRET_KEY doit contenir au moins 32 caracteres aleatoires")
        if self.uses_supabase_storage:
            if not self.supabase_url:
                errors.append("SUPABASE_URL est obligatoire avec MEDIA_STORAGE_BACKEND=supabase")
            if not self.supabase_secret_key:
                errors.append(
                    "SUPABASE_SECRET_KEY est obligatoire avec MEDIA_STORAGE_BACKEND=supabase"
                )

        if errors:
            raise ValueError("Configuration de production invalide: " + "; ".join(errors))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
