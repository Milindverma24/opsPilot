import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "OpsPilot"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    SECRET_KEY: str = "opspilot-super-secret-key-change-in-production-min-32-chars"
    JWT_SECRET: str = "opspilot-jwt-secret-key-change-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    DATABASE_URL: str = "sqlite:///./opspilot.db"

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_ALWAYS_EAGER: bool = True

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    DEFAULT_AI_PROVIDER: str = "deterministic"
    CONFIDENCE_THRESHOLD: float = 0.80

    # Phase 7 — LLM & Agent Configuration
    LLM_PROVIDER: str = "deterministic"          # "deterministic" or "openai"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.1
    MAX_OUTPUT_TOKENS: int = 2000
    MAX_AGENT_STEPS: int = 12
    MAX_REPLANS: int = 3
    AGENT_TIMEOUT_SECONDS: int = 120
    CONFIDENCE_THRESHOLD_AUTO: float = 0.90      # >= auto action allowed (risk-dependent)
    CONFIDENCE_THRESHOLD_REVIEW: float = 0.70    # 0.70-0.89 → human review depending on risk

    STORAGE_PATH: str = "./storage/uploads"
    MAX_UPLOAD_SIZE_MB: int = 25

    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
