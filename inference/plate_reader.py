"""PaddleOCR plate reading."""

import re

_ocr = None


def get_ocr():
    global _ocr
    if _ocr is None:
        from paddleocr import PaddleOCR

        _ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    return _ocr


def clean_plate_text(raw_text: str) -> str:
    return re.sub(r"[^A-Z0-9\-]", "", raw_text.upper())


def read_plate(crop_bgr) -> tuple[str, float]:
    """Read plate text from BGR crop. Returns (text, confidence)."""
    import cv2

    if crop_bgr is None or crop_bgr.size == 0:
        return "UNKNOWN", 0.0

    ocr = get_ocr()
    rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
    result = ocr.ocr(rgb, cls=True)
    if not result or not result[0]:
        return "UNKNOWN", 0.0

    texts = []
    confs = []
    for line in result[0]:
        texts.append(line[1][0])
        confs.append(float(line[1][1]))

    raw = " ".join(texts)
    cleaned = clean_plate_text(raw)
    avg_conf = sum(confs) / len(confs) if confs else 0.0
    return cleaned or "UNKNOWN", avg_conf
