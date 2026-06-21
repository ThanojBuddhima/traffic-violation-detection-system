"""YOLO detector wrappers for helmet and plate models."""

from pathlib import Path

from inference.config import settings

_helmet_model = None
_plate_model = None


def get_helmet_model():
    global _helmet_model
    if _helmet_model is None:
        from ultralytics import YOLO

        path = Path(settings.HELMET_MODEL_PATH)
        if not path.exists():
            raise FileNotFoundError(f"Helmet model not found: {path}")
        _helmet_model = YOLO(str(path))
    return _helmet_model


def get_plate_model():
    global _plate_model
    if _plate_model is None:
        from ultralytics import YOLO

        path = Path(settings.PLATE_MODEL_PATH)
        if not path.exists():
            raise FileNotFoundError(f"Plate model not found: {path}")
        _plate_model = YOLO(str(path))
    return _plate_model


def detect_plate_crop(image_bgr) -> tuple[object | None, float]:
    """Run plate detector on a BGR crop; return (crop_array, confidence) or (None, 0)."""
    import cv2
    import numpy as np

    model = get_plate_model()
    results = model(image_bgr, verbose=False)
    if not results or not results[0].boxes:
        return None, 0.0

    best_box = max(results[0].boxes, key=lambda b: float(b.conf))
    conf = float(best_box.conf)
    x1, y1, x2, y2 = map(int, best_box.xyxy[0].tolist())
    h, w = image_bgr.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    crop = image_bgr[y1:y2, x1:x2]
    if crop.size == 0:
        return None, 0.0
    return crop, conf
