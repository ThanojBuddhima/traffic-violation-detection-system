"""Violation detection result."""

from dataclasses import dataclass, field


@dataclass
class MediaMetadata:
    width: int = 0
    height: int = 0
    duration_seconds: float = 0.0


@dataclass
class PipelineResult:
    violations: list["ViolationResult"]
    media: MediaMetadata = field(default_factory=MediaMetadata)


@dataclass
class ViolationResult:
    track_id: int
    plate_number: str
    plate_confidence: float
    helmet_confidence: float
    frame_timestamp: float
    evidence_image_bytes: bytes
    plate_image_bytes: bytes | None = None
    overlay_frames: list[dict] = field(default_factory=list)
    frame_width: int = 0
    frame_height: int = 0
