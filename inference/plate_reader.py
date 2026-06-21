"""PaddleOCR plate reading."""

import re

_ocr = None


def get_ocr():
    global _ocr
    if _ocr is None:
        from paddleocr import PaddleOCR

        _ocr = PaddleOCR(
            lang="en",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=True,
        )
    return _ocr


def clean_plate_text(raw_text: str) -> str:
    return re.sub(r"[^A-Z0-9\-]", "", raw_text.upper())


def _parse_ocr_result(result) -> tuple[list[str], list[float]]:
    """Support PaddleOCR 3.x predict() output and legacy ocr() tuples."""
    if not result:
        return [], []

    page = result[0]
    if isinstance(page, dict):
        texts = page.get("rec_texts") or []
        scores = page.get("rec_scores") or []
        return list(texts), [float(s) for s in scores]

    texts: list[str] = []
    scores: list[float] = []
    for line in page:
        texts.append(line[1][0])
        scores.append(float(line[1][1]))
    return texts, scores


def read_plate(crop_bgr) -> tuple[str, float]:
    """Read plate text from BGR crop. Returns (text, confidence)."""
    import cv2

    if crop_bgr is None or crop_bgr.size == 0:
        return "UNKNOWN", 0.0

    ocr = get_ocr()
    rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)

    if hasattr(ocr, "predict"):
        result = ocr.predict(rgb)
    else:
        result = ocr.ocr(rgb, cls=True)

    texts, confs = _parse_ocr_result(result)
    if not texts:
        return "UNKNOWN", 0.0

    raw = " ".join(texts)
    cleaned = clean_plate_text(raw)
    avg_conf = sum(confs) / len(confs) if confs else 0.0
    return cleaned or "UNKNOWN", avg_conf
