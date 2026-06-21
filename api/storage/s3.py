"""S3 object storage backend (V2)."""

import tempfile
from pathlib import Path
from typing import BinaryIO

from api.config import settings
from api.storage.base import StorageBackend


class S3StorageBackend(StorageBackend):
    def __init__(self) -> None:
        import boto3

        self.bucket = settings.S3_BUCKET
        self.client = boto3.client(
            "s3",
            region_name=settings.S3_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        )
        self._temp_files: list[str] = []

    def save_upload(self, video_id: str, file_obj: BinaryIO, filename: str) -> str:
        ext = Path(filename).suffix or ".mp4"
        key = f"uploads/{video_id}{ext}"
        self.client.upload_fileobj(file_obj, self.bucket, key)
        return key

    def save_evidence(self, key: str, image_bytes: bytes) -> str:
        if not key.startswith("violations/"):
            key = f"violations/{key}"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=image_bytes, ContentType="image/jpeg")
        return key

    def read(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def get_url(self, key: str) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=3600,
        )

    def materialize_for_processing(self, key: str) -> str:
        suffix = Path(key).suffix or ".mp4"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(self.read(key))
        tmp.close()
        self._temp_files.append(tmp.name)
        return tmp.name
