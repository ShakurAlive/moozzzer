from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["dev", "test", "prod"] = "dev"
    log_level: str = "INFO"

    database_url: PostgresDsn = PostgresDsn(
        "postgresql+asyncpg://moozzzer:moozzzer@localhost:5432/moozzzer"
    )
    redis_url: RedisDsn = RedisDsn("redis://localhost:6379/0")

    media_root: str = "/data/media"
    health_timeout_seconds: float = 2.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
