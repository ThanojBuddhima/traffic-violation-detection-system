"""Violation detection result."""

from dataclasses import dataclass


@dataclass
class ViolationResult:
    track_id: int
    plate_number: str
    plate_confidence: float
    helmet_confidence: float
    frame_timestamp: float
    evidence_image_bytes: bytes
