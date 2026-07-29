from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    database_url: str = "postgresql+psycopg://story2:story2@localhost:5432/story2"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    # local = filesystem (bom para Render free sem R2); s3 = MinIO/R2
    storage_backend: str = "local"
    storage_local_path: str = "/tmp/story2-storage"
    storage_endpoint_url: str = "http://localhost:9000"
    storage_public_endpoint_url: str = "http://localhost:9000"
    storage_access_key: str = "story2"
    storage_secret_key: str = "story2123456"
    storage_bucket: str = "story2"
    storage_region: str = "us-east-1"

    gemini_api_key: str = ""
    gemini_ssl_verify: bool = True
    offline_fallback: bool = True

    @property
    def sql_database_url(self) -> str:
        return normalize_database_url(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
