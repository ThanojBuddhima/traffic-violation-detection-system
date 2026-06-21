"""Inference pipeline — sole USE_MOCK_MODELS switch point."""

import io

from inference.config import settings
from inference.types import MediaMetadata, PipelineResult, ViolationResult


def run_inference_pipeline(media_path: str, video_id: str = "mock") -> PipelineResult:
    if settings.USE_MOCK_MODELS:
        return _mock_pipeline(media_path, video_id)
    if _is_image(media_path):
        return _real_pipeline_image(media_path)
    return _real_pipeline_video(media_path)


def _is_image(path: str) -> bool:
    from pathlib import Path

    image_extensions = {
        ".jpg", ".jpeg", ".png", ".webp", ".bmp",
        ".heic", ".heif", ".jfif", ".tif", ".tiff",
    }
    return Path(path).suffix.lower() in image_extensions


def _load_image_bgr(path: str):
    """Load image as BGR; OpenCV first, then Pillow for HEIC/HEIF and other formats."""
    import cv2

    frame_bgr = cv2.imread(path)
    if frame_bgr is not None:
        return frame_bgr

    from PIL import Image
    import numpy as np

    try:
        rgb = np.array(Image.open(path).convert("RGB"))
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except Exception:
        return None


def _mock_pipeline(media_path: str, video_id: str) -> PipelineResult:
    """Return 1-2 fake violations with placeholder evidence and plate images."""
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
        evidence = buf.getvalue()

        plate_img = Image.new("RGB", (120, 40), color=(30, 30, 30))
        plate_draw = ImageDraw.Draw(plate_img)
        plate_draw.text((8, 10), plate, fill=(255, 255, 0))
        plate_buf = io.BytesIO()
        plate_img.save(plate_buf, format="JPEG")

        t = float(i * 2.5)
        results.append(
            ViolationResult(
                track_id=i + 1,
                plate_number=plate,
                plate_confidence=0.85,
                helmet_confidence=0.92,
                frame_timestamp=t,
                evidence_image_bytes=evidence,
                plate_image_bytes=plate_buf.getvalue(),
                overlay_frames=[
                    {"t": t, "x1": 20, "y1": 20, "x2": 300, "y2": 160},
                    {"t": t + 0.04, "x1": 22, "y1": 22, "x2": 302, "y2": 162},
                ],
                frame_width=320,
                frame_height=180,
            )
        )
    return PipelineResult(
        violations=results,
        media=MediaMetadata(width=320, height=180, duration_seconds=5.0),
    )


def _real_pipeline_video(video_path: str) -> PipelineResult:
    """Full detection → tracking → plate OCR pipeline for video."""
    import cv2

    from inference.detector import detect_plate_crop
    from inference.plate_reader import read_plate
    from inference.tracker import track_video
    from inference.violation_logic import (
        accumulate_track_stats,
        encode_bgr_jpeg,
        filter_violation_tracks,
    )

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    duration = frame_count / fps if fps > 0 and frame_count > 0 else 0.0
    cap.release()

    results_iter = track_video(video_path)
    track_state = accumulate_track_stats(results_iter, fps)
    violation_tracks = filter_violation_tracks(track_state)

    if not width or not height:
        for state in track_state.values():
            for frame in state.get("overlay_frames", []):
                width = max(width, frame["x2"])
                height = max(height, frame["y2"])

    violations: list[ViolationResult] = []
    for track_id, state in violation_tracks:
        import numpy as np

        nparr = np.frombuffer(state["best_crop"], np.uint8)
        crop_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if crop_bgr is None:
            continue

        plate_crop, _ = detect_plate_crop(crop_bgr)
        plate_text, ocr_conf = read_plate(plate_crop if plate_crop is not None else crop_bgr)
        plate_bytes = encode_bgr_jpeg(plate_crop) if plate_crop is not None else None

        violations.append(
            ViolationResult(
                track_id=track_id,
                plate_number=plate_text,
                plate_confidence=ocr_conf,
                helmet_confidence=state["best_conf"],
                frame_timestamp=state["frame_timestamp"],
                evidence_image_bytes=state["best_crop"],
                plate_image_bytes=plate_bytes,
                overlay_frames=state.get("overlay_frames", []),
                frame_width=width,
                frame_height=height,
            )
        )

    return PipelineResult(
        violations=violations,
        media=MediaMetadata(width=width, height=height, duration_seconds=duration),
    )


def _real_pipeline_image(image_path: str) -> PipelineResult:
    """Single-frame detection for uploaded images (no tracking)."""
    import cv2

    from inference.detector import detect_plate_crop, get_helmet_model
    from inference.plate_reader import read_plate
    from inference.violation_logic import encode_bgr_jpeg, extract_crop, overlay_entry

    frame_bgr = _load_image_bgr(image_path)
    if frame_bgr is None:
        return PipelineResult()

    height, width = frame_bgr.shape[:2]
    model = get_helmet_model()
    results = model(frame_bgr, verbose=False)
    if not results or not results[0].boxes:
        return PipelineResult(media=MediaMetadata(width=width, height=height, duration_seconds=0.0))

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
        plate_bytes = encode_bgr_jpeg(plate_crop) if plate_crop is not None else None

        violations.append(
            ViolationResult(
                track_id=track_id,
                plate_number=plate_text,
                plate_confidence=ocr_conf,
                helmet_confidence=conf,
                frame_timestamp=0.0,
                evidence_image_bytes=crop_bytes,
                plate_image_bytes=plate_bytes,
                overlay_frames=[overlay_entry(0.0, box, frame_bgr)],
                frame_width=width,
                frame_height=height,
            )
        )

    return PipelineResult(
        violations=violations,
        media=MediaMetadata(width=width, height=height, duration_seconds=0.0),
    )
