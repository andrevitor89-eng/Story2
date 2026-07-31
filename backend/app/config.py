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

    # local | db | s3  (db = Postgres LargeBinary; bom no Render free)
    storage_backend: str = "s3"
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
    gemini_model: str = "gemini-2.5-flash-image"
    # Modelos alternativos se o principal estiver em 503/alta demanda
    gemini_fallback_models: str = "gemini-2.0-flash-preview-image-generation"
    gemini_max_retries: int = 6
    gemini_retry_base_seconds: float = 5.0

    # Animacao / narrado animado
    # Preferir KLING_API_KEY (gateway Bearer, ex. api-key-kling-...) quando o console
    # so mostra uma chave. Alternativa oficial: ACCESS + SECRET (JWT em api.klingai.com).
    kling_api_key: str = ""
    kling_access_key: str = ""
    kling_secret_key: str = ""
    kling_model_name: str = "kling-v2-1"
    default_video_duration_s: int = 5
    video_poll_interval_s: float = 10.0
    video_poll_timeout_s: float = 600.0

    # V�deo narrado (TTS)
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    @property
    def sql_database_url(self) -> str:
        return normalize_database_url(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
