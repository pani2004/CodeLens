"""
Application configuration using Pydantic BaseSettings.
Loads from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "CodeLens AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # ── Server ───────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # ── Database (PostgreSQL + pgvector) ─────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/codelens"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/codelens"

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── GitHub OAuth ─────────────────────────────────────
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:3000/auth/callback"

    # ── JWT ──────────────────────────────────────────────
    JWT_SECRET: str = "super-secret-change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── Gemini AI ────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-001"

    # ── Encryption ───────────────────────────────────────
    FERNET_KEY: str = ""  # Generate with: from cryptography.fernet import Fernet; Fernet.generate_key()

    # ── Rate Limits ──────────────────────────────────────
    RATE_LIMIT_CHAT_FREE: str = "50/hour"
    RATE_LIMIT_REPOS_FREE: str = "5/day"
    RATE_LIMIT_AUTH: str = "5/15minutes"

    # ── Storage ──────────────────────────────────────────
    REPO_CLONE_DIR: str = "./tmp/repos"
    MAX_REPO_SIZE_MB: int = 500

    # ── Celery ───────────────────────────────────────────
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    @property
    def celery_broker(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def celery_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
