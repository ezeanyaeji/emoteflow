import os
from pathlib import Path

from pydantic_settings import BaseSettings
from functools import lru_cache

# Resolve .env relative to the api/ directory
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    # App
    APP_NAME: str = "EmoteFlow API"
    DEBUG: bool = False

    # MongoDB — no defaults; must be provided via .env or environment
    MONGODB_HOST: str
    MONGODB_USER: str
    MONGODB_PASSWORD: str
    MONGODB_DB_NAME: str = "emoteflowDB"

    # JWT — no default for secret; must be provided via .env or environment
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS (comma-separated string to avoid pydantic-settings JSON parsing issues)
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [s.strip() for s in self.CORS_ORIGINS.split(",") if s.strip()]

    # Hugging Face model
    HF_REPO_ID: str = "charlykso/emoteflow-emotion-cnn"
    ONNX_FILENAME: str = "emoteflow_model.onnx"

    # Seed admin credentials
    ADMIN_EMAIL: str = "admin@gmail.com"
    ADMIN_PASSWORD: str = "password"

    model_config = {"env_file": str(_ENV_FILE), "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
