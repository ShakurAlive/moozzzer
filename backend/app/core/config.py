import secrets
from functools import lru_cache
from typing import Literal, Self

from pydantic import PostgresDsn, RedisDsn, SecretStr, model_validator
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

    # HS256 key for access JWTs. Required in prod; dev/test get a random per-process key.
    jwt_secret: SecretStr = SecretStr("")
    access_token_ttl_seconds: int = 15 * 60
    refresh_token_ttl_days: int = 30
    # Fixed-window limits for /auth/login and /auth/register.
    auth_rate_limit_per_minute: int = 5
    auth_rate_limit_ip_per_minute: int = 20

    # Enabled provider keys (comma-separated); see app/providers/registry.py.
    providers_metadata: str = "youtube_music"
    providers_audio: str = "youtube_music,soundcloud"
    providers_timeout_seconds: float = 10.0
    providers_cache_ttl_seconds: int = 300
    providers_stream_cache_ttl_seconds: int = 1800
    # yt-dlp cookies (Netscape format) — YouTube blocks datacenter IPs without auth.
    ytdlp_cookie_file: str = "/data/cookies.txt"
    # Yandex Music OAuth token (for the yandex_music metadata provider).
    yandex_music_token: str | None = None

    # --- media storage & streaming (stage 3) ---
    # Signing key for short-lived streaming URLs (/media/{id}?exp=&sig=). Required in prod;
    # empty in dev/test = random per process.
    media_signing_secret: SecretStr = SecretStr("")
    media_url_ttl_seconds: int = 3600
    # GC grace period: files of orphaned tracks survive this long before deletion.
    gc_grace_days: int = 7

    @model_validator(mode="after")
    def _check_jwt_secret(self) -> Self:
        secret = self.jwt_secret.get_secret_value()
        if not secret:
            if self.app_env == "prod":
                raise ValueError("JWT_SECRET is required in prod")
            self.jwt_secret = SecretStr(secrets.token_urlsafe(32))
        elif len(secret) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters")
        return self

    @model_validator(mode="after")
    def _check_media_secret(self) -> Self:
        secret = self.media_signing_secret.get_secret_value()
        if not secret:
            if self.app_env == "prod":
                raise ValueError("MEDIA_SIGNING_SECRET is required in prod")
            self.media_signing_secret = SecretStr(secrets.token_urlsafe(32))
        elif len(secret) < 32:
            raise ValueError("MEDIA_SIGNING_SECRET must be at least 32 characters")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
