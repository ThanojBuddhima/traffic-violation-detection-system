"""Track-level violation logic and cross-video deduplication."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from database.models import Violation
from inference.config import settings
from inference.types import ViolationResult


def extract_crop(frame_bgr, box) -> bytes:
    """Extract JPEG bytes from bounding box on frame."""
    import cv2

    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
    h, w = frame_bgr.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    crop = frame_bgr[y1:y2, x1:x2]
    if crop.size == 0:
        return b""
    _, buf = cv2.imencode(".jpg", crop)
    return buf.tobytes()


def accumulate_track_stats(results_iter, fps: float) -> dict[int, dict]:
    """Process tracking results and build per-track statistics."""
    import cv2

    track_state: dict[int, dict] = {}

    for frame_idx, result in enumerate(results_iter):
        if result.boxes is None:
            continue
        frame_bgr = result.orig_img
        timestamp = frame_idx / fps if fps > 0 else float(frame_idx)

        for box in result.boxes:
            if box.id is None:
                continue
            track_id = int(box.id.item())
            cls = int(box.cls.item())
            conf = float(box.conf.item())

            state = track_state.setdefault(
                track_id,
                {
                    "no_helmet_frames": 0,
                    "total_frames": 0,
                    "best_crop": b"",
                    "best_conf": 0.0,
                    "frame_timestamp": timestamp,
                },
            )
            state["total_frames"] += 1
            if cls == 1:  # no_helmet
                state["no_helmet_frames"] += 1
            if conf > state["best_conf"]:
                state["best_crop"] = extract_crop(frame_bgr, box)
                state["best_conf"] = conf
                state["frame_timestamp"] = timestamp

    return track_state


def filter_violation_tracks(track_state: dict[int, dict]) -> list[tuple[int, dict]]:
    """Return track ids that exceed no-helmet ratio threshold."""
    violations = []
    for track_id, state in track_state.items():
        if state["total_frames"] < settings.MIN_TRACK_FRAMES:
            continue
        ratio = state["no_helmet_frames"] / state["total_frames"]
        if ratio > settings.NO_HELMET_RATIO and state["best_crop"]:
            violations.append((track_id, state))
    return violations


def is_duplicate_plate(
    db: Session,
    plate_number: str,
    frame_timestamp: float,
    video_upload_time: datetime | None,
) -> bool:
    """Check if same plate was logged within dedup window."""
    if not plate_number or plate_number == "UNKNOWN":
        return False

    ref_time = video_upload_time or datetime.now(timezone.utc)
    if ref_time.tzinfo is None:
        ref_time = ref_time.replace(tzinfo=timezone.utc)

    window = timedelta(minutes=settings.DEDUP_WINDOW_MINUTES)
    existing = (
        db.query(Violation)
        .filter(Violation.plate_number == plate_number)
        .all()
    )
    for v in existing:
        v_time = v.created_at
        if v_time.tzinfo is None:
            v_time = v_time.replace(tzinfo=timezone.utc)
        if abs((v_time - ref_time).total_seconds()) <= window.total_seconds():
            return True
    return False
