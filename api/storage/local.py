"""Local filesystem storage backend (V1)."""

import shutil
from pathlib import Path
from typing import BinaryIO

from api.config import settings
from api.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    def __init__(self) -> None:
        self.uploads_dir = Path(settings.STORAGE_LOCAL_UPLOADS_DIR)
        self.violations_dir = Path(settings.STORAGE_LOCAL_VIOLATIONS_DIR)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.violations_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        path = Path(key)
        if path.is_absolute():
            return path
        if key.startswith("uploads/"):
            return Path(key)
        if key.startswith("violations/"):
            return Path(key)
        candidate = self.uploads_dir / key
        if candidate.exists():
            return candidate
        return self.violations_dir / key

    def save_upload(self, video_id: str, file_obj: BinaryIO, filename: str) -> str:
        ext = Path(filename).suffix or ".mp4"
        key = f"uploads/{video_id}{ext}"
        dest = Path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as out:
            shutil.copyfileobj(file_obj, out)
        return key

    def save_evidence(self, key: str, image_bytes: bytes) -> str:
        if not key.startswith("violations/"):
            key = f"violations/{key}"
        dest = Path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(image_bytes)
        return key

    def read(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.exists():
            raise FileNotFoundError(key)
        return path.read_bytes()

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.exists():
            path.unlink()

    def get_url(self, key: str) -> str:
        return str(self._resolve(key).resolve())

    def materialize_for_processing(self, key: str) -> str:
        return str(self._resolve(key).resolve())
