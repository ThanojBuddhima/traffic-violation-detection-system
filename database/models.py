"""SQLAlchemy ORM models."""

import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class VideoStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class Base(DeclarativeBase):
    pass


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(String(512))
    storage_key: Mapped[str] = mapped_column(String(1024))
    upload_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    status: Mapped[str] = mapped_column(String(32), default=VideoStatus.QUEUED.value)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    violations: Mapped[list["Violation"]] = relationship(back_populates="video", cascade="all, delete-orphan")


class Violation(Base):
    __tablename__ = "violations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id"), index=True)
    track_id: Mapped[int] = mapped_column(Integer)
    plate_number: Mapped[str] = mapped_column(String(64), index=True)
    plate_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    helmet_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    frame_timestamp: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_image_path: Mapped[str] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)

    video: Mapped["Video"] = relationship(back_populates="violations")
