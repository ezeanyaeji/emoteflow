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

    # MongoDB
    MONGODB_HOST: str = "localhost:27017"
    MONGODB_USER: str = ""
    MONGODB_PASSWORD: str = ""
    MONGODB_DB_NAME: str = "emoteflow"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Hugging Face model
    HF_REPO_ID: str = "charlykso/emoteflow-emotion-cnn"
    ONNX_FILENAME: str = "emoteflow_model.onnx"

    model_config = {"env_file": str(_ENV_FILE), "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
