"""Storage factory."""

from functools import lru_cache

from api.config import settings
from api.storage.base import StorageBackend
from api.storage.local import LocalStorageBackend
from api.storage.s3 import S3StorageBackend


@lru_cache
def get_storage() -> StorageBackend:
    if settings.STORAGE_BACKEND == "s3":
        return S3StorageBackend()
    return LocalStorageBackend()
