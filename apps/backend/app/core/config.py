from __future__ import annotations

import os
from functools import lru_cache
from typing import Self
from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _build_mysql_url(*, async_driver: bool) -> str | None:
    host = os.getenv("MYSQL_HOST", "").strip()
    user = os.getenv("MYSQL_USER", "").strip()
    database = os.getenv("MYSQL_DATABASE", "").strip()
    password = os.getenv("MYSQL_PASSWORD", "")
    if not (host and user and database):
        return None
    driver = "mysql+aiomysql" if async_driver else "mysql+pymysql"
    return f"{driver}://{user}:{quote_plus(password)}@{host}:3306/{database}"


def _resolve_database_url(current: str, *, async_driver: bool) -> str:
    current = (current or "").strip()
    if current:
        return current
    docker_key = "DATABASE_URL_DOCKER" if async_driver else "DATABASE_URL_SYNC_DOCKER"
    local_key = "DATABASE_URL" if async_driver else "DATABASE_URL_SYNC"
    for key in (docker_key, local_key):
        value = os.getenv(key, "").strip()
        if value:
            return value
    built = _build_mysql_url(async_driver=async_driver)
    return built or ""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "mysql+aiomysql://attendance:attendance@localhost:3306/attendance"
    database_url_sync: str = "mysql+pymysql://attendance:attendance@localhost:3306/attendance"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-jwt-secret-min-32-chars-long"
    jwt_refresh_secret: str = "change-me-refresh-secret-min-32-chars"
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7

    embedding_encryption_key: str = "change-me-fernet-key-base64"

    match_threshold: float = 0.70
    match_margin: float = 0.05
    gray_zone_low: float = 0.60
    gray_zone_high: float = 0.65
    duplicate_window_seconds: int = 300
    use_faiss_index: bool = True
    faiss_top_k: int = 100
    min_det_score: float = 0.50
    min_blur_variance: float = 20.0
    min_enrollment_pairwise_similarity: float = 0.40

    recognition_service_url: str = "http://localhost:6003"
    deepface_enabled: bool = True

    cors_origins: str = "http://localhost:6001"
    upload_dir: str = "./uploads"
    min_enrollment_images: int = 5
    max_enrollment_images: int = 10

    half_day_hours: float = 4.0
    overtime_threshold_minutes: int = 30

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_tls: bool = True
    notify_from: str = "attendance@company.com"

    @model_validator(mode="after")
    def resolve_database_urls(self) -> Self:
        object.__setattr__(
            self,
            "database_url",
            _resolve_database_url(self.database_url, async_driver=True),
        )
        object.__setattr__(
            self,
            "database_url_sync",
            _resolve_database_url(self.database_url_sync, async_driver=False),
        )
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL is empty. For Docker, set DATABASE_URL_DOCKER and "
                "DATABASE_URL_SYNC_DOCKER in the repo root .env (host: host.docker.internal "
                "or your MySQL IP; URL-encode # in passwords as %23). For local uvicorn, "
                "set DATABASE_URL in apps/backend/.env."
            )
        if not self.database_url_sync:
            object.__setattr__(self, "database_url_sync", self.database_url.replace(
                "mysql+aiomysql", "mysql+pymysql", 1
            ))
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
