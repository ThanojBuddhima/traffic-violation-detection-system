"""Shared upload media type helpers."""

from pathlib import Path

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
ALLOWED_EXTENSIONS = VIDEO_EXTENSIONS | IMAGE_EXTENSIONS


def is_allowed_upload(filename: str | None, content_type: str | None = None) -> bool:
    if not filename:
        return False
    ext = Path(filename).suffix.lower()
    if ext in ALLOWED_EXTENSIONS:
        return True
    if content_type:
        return content_type.startswith("video/") or content_type.startswith("image/")
    return False


def is_image_path(path: str) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTENSIONS


def is_video_path(path: str) -> bool:
    return Path(path).suffix.lower() in VIDEO_EXTENSIONS
