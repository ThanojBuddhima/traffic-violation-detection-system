#!/usr/bin/env python3
"""Seed a mock violation for local development."""

import uuid
from datetime import datetime, timezone

from api.storage import get_storage
from database.models import Video, VideoStatus, Violation
from database.session import SessionLocal, init_db
from inference.pipeline import _mock_violations


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
    )
    db.add(video)

    for v in _mock_violations("seed", video_id):
        key = storage.save_evidence(f"{video_id}_{v.track_id}.jpg", v.evidence_image_bytes)
        db.add(
            Violation(
                video_id=video_id,
                track_id=v.track_id,
                plate_number=v.plate_number,
                plate_confidence=v.plate_confidence,
                helmet_confidence=v.helmet_confidence,
                frame_timestamp=v.frame_timestamp,
                evidence_image_path=key,
            )
        )

    db.commit()
    db.close()
    print(f"Seeded video {video_id} with mock violations")


if __name__ == "__main__":
    main()
