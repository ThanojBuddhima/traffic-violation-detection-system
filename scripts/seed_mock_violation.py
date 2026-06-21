#!/usr/bin/env python3
"""Seed a mock violation for local development."""

import json
import uuid
from datetime import datetime, timezone

from api.storage import get_storage
from database.models import Video, VideoStatus, Violation
from database.session import SessionLocal, init_db
from inference.pipeline import run_inference_pipeline


def main():
    init_db()
    db = SessionLocal()
    storage = get_storage()

    video_id = str(uuid.uuid4())
    video = Video(
        id=video_id,
        filename="seed_mock.mp4",
        storage_key=f"uploads/{video_id}.mp4",
        status=VideoStatus.DONE.value,
        processed_at=datetime.now(timezone.utc),
        width=320,
        height=180,
        duration_seconds=5.0,
    )
    db.add(video)

    result = run_inference_pipeline("seed", video_id=video_id)
    for v in result.violations:
        key = storage.save_evidence(f"{video_id}_{v.track_id}.jpg", v.evidence_image_bytes)
        plate_path = None
        if v.plate_image_bytes:
            plate_path = storage.save_evidence(f"{video_id}_{v.track_id}_plate.jpg", v.plate_image_bytes)
        db.add(
            Violation(
                video_id=video_id,
                track_id=v.track_id,
                plate_number=v.plate_number,
                plate_confidence=v.plate_confidence,
                helmet_confidence=v.helmet_confidence,
                frame_timestamp=v.frame_timestamp,
                evidence_image_path=key,
                plate_image_path=plate_path,
                overlay_frames=json.dumps(v.overlay_frames),
            )
        )

    db.commit()
    db.close()
    print(f"Seeded video {video_id} with mock violations")


if __name__ == "__main__":
    main()
