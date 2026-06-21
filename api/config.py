"""Application configuration via environment variables."""

from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "sqlite:///./database/violations.db"

    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    STORAGE_LOCAL_UPLOADS_DIR: str = "uploads"
    STORAGE_LOCAL_VIOLATIONS_DIR: str = "violations"

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET: str = ""
    S3_REGION: str = "us-east-1"

    USE_CELERY: bool = False
    CELERY_BROKER_URL: str = ""

    USE_MOCK_MODELS: bool = True
    HELMET_MODEL_PATH: str = "models/helmet_best.pt"
    PLATE_MODEL_PATH: str = "models/plate_best.pt"
    MIN_TRACK_FRAMES: int = 5
    NO_HELMET_RATIO: float = 0.5
    DEDUP_WINDOW_MINUTES: int = 5
    DELETE_RAW_VIDEO_AFTER_PROCESS: bool = False

    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @model_validator(mode="after")
    def validate_v1_constraints(self) -> "Settings":
        if not self.USE_CELERY and self.STORAGE_BACKEND != "local":
            raise ValueError(
                "STORAGE_BACKEND must be 'local' in V1. "
                "Set USE_CELERY=true and deploy V2 infra before using s3."
            )
        if not self.USE_CELERY and self.CELERY_BROKER_URL:
            raise ValueError("CELERY_BROKER_URL is set but USE_CELERY=false.")
        if self.USE_CELERY and not self.CELERY_BROKER_URL:
            raise ValueError("USE_CELERY=true requires CELERY_BROKER_URL.")
        if self.STORAGE_BACKEND == "s3" and not self.S3_BUCKET:
            raise ValueError("STORAGE_BACKEND=s3 requires S3_BUCKET.")
        return self


settings = Settings()
