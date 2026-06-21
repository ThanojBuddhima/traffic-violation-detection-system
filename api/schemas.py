"""Pydantic schemas for API responses."""

from datetime import datetime

from pydantic import BaseModel


class VideoResponse(BaseModel):
    id: str
    filename: str
    status: str
    upload_time: datetime
    duration_seconds: float | None = None
    processed_at: datetime | None = None
    error_message: str | None = None

    model_config = {"from_attributes": True}


class VideoUploadResponse(BaseModel):
    video_id: str
    status: str


class ViolationResponse(BaseModel):
    id: int
    video_id: str
    track_id: int
    plate_number: str
    plate_confidence: float
    helmet_confidence: float
    frame_timestamp: float
    evidence_image_path: str
    created_at: datetime
    reviewed: bool

    model_config = {"from_attributes": True}


class ViolationUpdate(BaseModel):
    plate_number: str | None = None
    reviewed: bool | None = None


class HealthResponse(BaseModel):
    status: str
    storage_backend: str
    use_celery: bool
    use_mock_models: bool
    database_dialect: str
