from urllib.parse import urlsplit
from typing import Literal
from pydantic import model_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "backend/.env"), extra="ignore")
    app_env: Literal["development", "testing", "production"] = "development"
    database_url: str = "sqlite+aiosqlite:///./studymind.db"
    secret_key: str = ""
    api_origin: str = "http://localhost:8000"
    web_origin: str = "http://localhost:5173"
    proxy_token: str = ""
    anthropic_api_key: str = ""
    anthropic_model: str = ""
    access_token_expire_minutes: int = 60
    require_email_verification: bool = True
    test_auto_schema: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    generation_daily_limit: int = 20
    generation_concurrency: int = 2
    generation_global_daily_limit: int = 200

    @field_validator("database_url", mode="before")
    @classmethod
    def async_database_url(cls, value):
        if isinstance(value, str):
            if value.startswith("postgres://"):
                value = "postgresql+asyncpg://" + value[len("postgres://") :]
            elif value.startswith("postgresql://"):
                value = "postgresql+asyncpg://" + value[len("postgresql://") :]
            value = value.replace("sslmode=", "ssl=")
        return value

    @property
    def production(self) -> bool:
        return self.app_env == "production"

    @property
    def mail_ready(self) -> bool:
        return bool(self.smtp_host and self.smtp_from)

    @model_validator(mode="after")
    def validate_security(self):
        if (
            self.secret_key
            == "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
        ):
            raise ValueError(
                "Rotate the signing key published in the original repository"
            )
        if (
            "replace-with" in self.secret_key.lower()
            or "change-me" in self.secret_key.lower()
        ):
            raise ValueError("Replace the example SECRET_KEY with a generated secret")
        if len(self.secret_key) < 32:
            raise ValueError("Set SECRET_KEY to at least 32 random characters")
        for origin in (self.api_origin, self.web_origin):
            parts = urlsplit(origin)
            if (
                parts.scheme not in ("http", "https")
                or origin != f"{parts.scheme}://{parts.netloc}"
                or not parts.hostname
                or parts.username
                or parts.password
            ):
                raise ValueError(
                    "API_ORIGIN and WEB_ORIGIN must be canonical origins without paths"
                )
            if self.production and parts.scheme != "https":
                raise ValueError("Production origins require HTTPS")
        if self.production and not self.database_url.startswith(
            "postgresql+asyncpg://"
        ):
            raise ValueError("Production requires PostgreSQL with asyncpg")
        if self.production and not self.require_email_verification:
            raise ValueError("Production registration requires email verification")
        if self.test_auto_schema and self.app_env != "testing":
            raise ValueError(
                "TEST_AUTO_SCHEMA is only available to automated tests; use Alembic"
            )
        if self.anthropic_api_key and not self.anthropic_model:
            raise ValueError(
                "Set ANTHROPIC_MODEL to an available model in your provider account"
            )
        if self.proxy_token and (
            len(self.proxy_token) != 64
            or any(c not in "0123456789abcdef" for c in self.proxy_token)
        ):
            raise ValueError("PROXY_TOKEN must be 64 lowercase hex characters")
        if not 5 <= self.access_token_expire_minutes <= 60:
            raise ValueError("Access tokens must expire within 5–60 minutes")
        if (
            not 1 <= self.generation_daily_limit <= 100
            or not 1 <= self.generation_concurrency <= 4
        ):
            raise ValueError("Generation limits exceed supported bounds")
        if not 1 <= self.generation_global_daily_limit <= 10000:
            raise ValueError("Set a bounded global generation allowance")
        return self
