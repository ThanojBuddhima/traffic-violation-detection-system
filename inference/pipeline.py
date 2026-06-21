"""Inference pipeline — sole USE_MOCK_MODELS switch point."""

import io

from inference.config import settings
from inference.types import ViolationResult


def run_inference_pipeline(media_path: str, video_id: str = "mock") -> list[ViolationResult]:
    if settings.USE_MOCK_MODELS:
        return _mock_violations(media_path, video_id)
    if _is_image(media_path):
        return _real_pipeline_image(media_path)
    return _real_pipeline_video(media_path)


def _is_image(path: str) -> bool:
    from pathlib import Path

    return Path(path).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def _mock_violations(video_path: str, video_id: str) -> list[ViolationResult]:
    """Return 1-2 fake violations with placeholder evidence images."""
    from PIL import Image, ImageDraw

    results = []
    suffix = video_id[:8].upper()
    plates = [f"ABC-{suffix}", f"XYZ-{suffix}"]
    for i, plate in enumerate(plates):
        img = Image.new("RGB", (320, 180), color=(40, 40, 40))
        draw = ImageDraw.Draw(img)
        draw.rectangle([20, 20, 300, 160], outline=(255, 0, 0), width=3)
        draw.text((40, 70), f"MOCK {plate}", fill=(255, 255, 255))
        draw.text((40, 110), f"track={i+1}", fill=(200, 200, 200))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        results.append(
            ViolationResult(
                track_id=i + 1,
                plate_number=plate,
                plate_confidence=0.85,
                helmet_confidence=0.92,
                frame_timestamp=float(i * 2.5),
                evidence_image_bytes=buf.getvalue(),
            )
        )
    return results


def _real_pipeline_video(video_path: str) -> list[ViolationResult]:
    """Full detection → tracking → plate OCR pipeline for video."""
    import cv2

    from inference.detector import detect_plate_crop
    from inference.plate_reader import read_plate
    from inference.tracker import track_video
    from inference.violation_logic import accumulate_track_stats, filter_violation_tracks

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    cap.release()

    results_iter = track_video(video_path)
    track_state = accumulate_track_stats(results_iter, fps)
    violation_tracks = filter_violation_tracks(track_state)

    violations: list[ViolationResult] = []
    for track_id, state in violation_tracks:
        import numpy as np

        nparr = np.frombuffer(state["best_crop"], np.uint8)
        crop_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if crop_bgr is None:
            continue

        plate_crop, plate_det_conf = detect_plate_crop(crop_bgr)
        plate_text, ocr_conf = read_plate(plate_crop if plate_crop is not None else crop_bgr)

        violations.append(
            ViolationResult(
                track_id=track_id,
                plate_number=plate_text,
                plate_confidence=ocr_conf,
                helmet_confidence=state["best_conf"],
                frame_timestamp=state["frame_timestamp"],
                evidence_image_bytes=state["best_crop"],
            )
        )

    return violations


def _real_pipeline_image(image_path: str) -> list[ViolationResult]:
    """Single-frame detection for uploaded images (no tracking)."""
    import cv2

    from inference.detector import detect_plate_crop, get_helmet_model
    from inference.plate_reader import read_plate
    from inference.violation_logic import extract_crop

    frame_bgr = cv2.imread(image_path)
    if frame_bgr is None:
        return []

    model = get_helmet_model()
    results = model(frame_bgr, verbose=False)
    if not results or not results[0].boxes:
        return []

    violations: list[ViolationResult] = []
    track_id = 0
    for box in results[0].boxes:
        if int(box.cls.item()) != 1:  # no_helmet
            continue
        track_id += 1
        conf = float(box.conf.item())
        crop_bytes = extract_crop(frame_bgr, box)
        if not crop_bytes:
            continue

        import numpy as np

        crop_bgr = cv2.imdecode(np.frombuffer(crop_bytes, np.uint8), cv2.IMREAD_COLOR)
        if crop_bgr is None:
            continue

        plate_crop, _ = detect_plate_crop(crop_bgr)
        plate_text, ocr_conf = read_plate(plate_crop if plate_crop is not None else crop_bgr)

        violations.append(
            ViolationResult(
                track_id=track_id,
                plate_number=plate_text,
                plate_confidence=ocr_conf,
                helmet_confidence=conf,
                frame_timestamp=0.0,
                evidence_image_bytes=crop_bytes,
            )
        )

    return violations
