"""Standalone video processing job — no FastAPI imports."""

from datetime import datetime, timezone

from api.config import settings
from api.storage import get_storage
from database.models import Video, VideoStatus, Violation
from database.session import SessionLocal
from inference.pipeline import run_inference_pipeline
from inference.violation_logic import is_duplicate_plate


def process_video_job(video_id: str, storage_key: str) -> None:
    """Process uploaded video: inference → evidence → DB. Callable from BackgroundTasks or Celery."""
    db = SessionLocal()
    storage = get_storage()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            return

        video.status = VideoStatus.PROCESSING.value
        db.commit()

        local_path = storage.materialize_for_processing(storage_key)
        violation_results = run_inference_pipeline(local_path, video_id=video_id)

        for v in violation_results:
            if is_duplicate_plate(db, v.plate_number, v.frame_timestamp, video.upload_time):
                continue

            evidence_key = f"{video_id}_{v.track_id}.jpg"
            saved_key = storage.save_evidence(evidence_key, v.evidence_image_bytes)

            db.add(
                Violation(
                    video_id=video_id,
                    track_id=v.track_id,
                    plate_number=v.plate_number,
                    plate_confidence=v.plate_confidence,
                    helmet_confidence=v.helmet_confidence,
                    frame_timestamp=v.frame_timestamp,
                    evidence_image_path=saved_key,
                )
            )

        video.status = VideoStatus.DONE.value
        video.processed_at = datetime.now(timezone.utc)
        db.commit()

        if settings.DELETE_RAW_VIDEO_AFTER_PROCESS:
            storage.delete(storage_key)

    except Exception as e:
        db.rollback()
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.status = VideoStatus.FAILED.value
            video.error_message = str(e)
            db.commit()
    finally:
        db.close()
