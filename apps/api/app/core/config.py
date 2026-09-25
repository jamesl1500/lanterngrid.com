from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../../.env", ".env"), extra="ignore")

    environment: Literal["development", "test", "staging", "production"] = "development"
    database_url: str = "postgresql+asyncpg://lanterngrid:lanterngrid@localhost:5434/lanterngrid"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    # Public URL of the web app. Links in emails and OAuth redirects point here.
    web_url: str = "http://localhost:3000"

    session_cookie_name: str = "lg_session"
    session_ttl_days: int = 30

    github_client_id: str | None = None
    github_client_secret: str | None = None

    # smtp sends real mail (Mailpit locally, Resend SMTP in production); console logs it;
    # memory keeps it in a list for tests.
    email_backend: Literal["smtp", "console", "memory"] = "console"
    email_from: str = "Lantern Grid <hello@lanterngrid.com>"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_starttls: bool = False

    # S3-compatible storage for uploads: MinIO locally, Cloudflare R2 in production.
    # 127.0.0.1 rather than localhost: browsers send every localhost cookie (from any port) to
    # localhost:9000, and MinIO rejects requests whose headers pass 8 KB.
    storage_endpoint_url: str | None = "http://127.0.0.1:9000"
    storage_region: str = "us-east-1"
    storage_bucket: str = "lanterngrid-media"
    storage_access_key: str = "lanterngrid"
    storage_secret_key: str = "lanterngrid"
    # Where browsers read uploaded files from (a public bucket URL or a CDN domain).
    storage_public_url: str = "http://127.0.0.1:9000/lanterngrid-media"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def secure_cookies(self) -> bool:
        return self.environment in ("staging", "production")

    @property
    def github_enabled(self) -> bool:
        return bool(self.github_client_id and self.github_client_secret)

    @property
    def trusted_origins(self) -> set[str]:
        return {*self.cors_origins, self.web_url.rstrip("/")}


@lru_cache
def get_settings() -> Settings:
    return Settings()
