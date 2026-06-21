"""Storage backend abstraction."""

from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageBackend(ABC):
    @abstractmethod
    def save_upload(self, video_id: str, file_obj: BinaryIO, filename: str) -> str:
        """Save uploaded video; return storage key."""

    @abstractmethod
    def save_evidence(self, key: str, image_bytes: bytes) -> str:
        """Save evidence image; return storage key."""

    @abstractmethod
    def read(self, key: str) -> bytes:
        """Read file bytes by storage key."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete file by storage key."""

    @abstractmethod
    def get_url(self, key: str) -> str:
        """Return local path or presigned URL for client access."""

    @abstractmethod
    def materialize_for_processing(self, key: str) -> str:
        """Return local filesystem path suitable for OpenCV/YOLO."""
