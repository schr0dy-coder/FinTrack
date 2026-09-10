"""Application Configuration Module using Pydantic Settings."""

from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    # General metadata
    PROJECT_NAME: str = "FinTrack"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite:///./fintrack.db"

    # Security / JWT
    JWT_SECRET_KEY: str = "super-secret-fintrack-key-for-development-change-in-production-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Risk Engine Rules & Thresholds
    HIGH_AMOUNT_THRESHOLD: float = 50000.0
    RAPID_TRANSACTION_WINDOW_SECONDS: int = 120
    RAPID_TRANSACTION_COUNT: int = 5
    FAILED_ATTEMPT_WINDOW_SECONDS: int = 300
    FAILED_ATTEMPT_COUNT: int = 3

    # Risk Classification Thresholds
    RISK_HIGH_THRESHOLD: float = 60.0
    RISK_CRITICAL_THRESHOLD: float = 80.0

    # Risk Score Weights
    RULE_WEIGHT: float = 0.60
    ML_WEIGHT: float = 0.40

    # ML Pipeline
    ML_MODEL_PATH: str = "models/artifacts/isolation_forest.joblib"
    ML_METADATA_PATH: str = "models/artifacts/model_metadata.json"

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)


# Singleton settings instance
settings = Settings()
