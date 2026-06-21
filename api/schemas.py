"""Pydantic schemas for API responses."""

import json
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class VideoResponse(BaseModel):
    id: str
    filename: str
    status: str
    upload_time: datetime
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    processed_at: datetime | None = None
    error_message: str | None = None

    model_config = {"from_attributes": True}


class VideoUploadResponse(BaseModel):
    video_id: str
    status: str


class OverlayFrame(BaseModel):
    t: float
    x1: int
    y1: int
    x2: int
    y2: int


class ViolationResponse(BaseModel):
    id: int
    video_id: str
    track_id: int
    plate_number: str
    plate_confidence: float
    helmet_confidence: float
    frame_timestamp: float
    evidence_image_path: str
    plate_image_path: str | None = None
    overlay_frames: list[OverlayFrame] = Field(default_factory=list)
    created_at: datetime
    reviewed: bool

    model_config = {"from_attributes": True}

    @field_validator("overlay_frames", mode="before")
    @classmethod
    def parse_overlay_frames(cls, value):
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return json.loads(value)
        return value


class ViolationUpdate(BaseModel):
    plate_number: str | None = None
    reviewed: bool | None = None


class HealthResponse(BaseModel):
    status: str
    storage_backend: str
    use_celery: bool
    use_mock_models: bool
    database_dialect: str
