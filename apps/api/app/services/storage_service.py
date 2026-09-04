import os
import hashlib
from typing import Optional, Tuple
from pathlib import Path


class ObjectStorage:
    """Interface for raw object storage."""

    def put_object(self, key: str, data: bytes, content_type: str = "text/plain") -> str:
        raise NotImplementedError

    def get_object(self, key: str) -> Optional[bytes]:
        raise NotImplementedError

    def delete_object(self, key: str) -> bool:
        raise NotImplementedError


class LocalObjectStorage(ObjectStorage):
    """
    Local filesystem-backed object storage implementation.
    Stores files in `storage/` directory organized by organization and content hash.
    Drop-in replaceable with S3 / MinIO storage.
    """

    def __init__(self, base_dir: str = "storage"):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def put_object(self, key: str, data: bytes, content_type: str = "text/plain") -> str:
        safe_key = key.replace("/", "_").replace("\\", "_")
        file_path = self.base_dir / safe_key
        file_path.write_bytes(data)
        return str(file_path)

    def get_object(self, key: str) -> Optional[bytes]:
        safe_key = key.replace("/", "_").replace("\\", "_")
        file_path = self.base_dir / safe_key
        if file_path.exists():
            return file_path.read_bytes()
        return None

    def delete_object(self, key: str) -> bool:
        safe_key = key.replace("/", "_").replace("\\", "_")
        file_path = self.base_dir / safe_key
        if file_path.exists():
            file_path.unlink()
            return True
        return False


# Global default storage singleton
storage_service = LocalObjectStorage()
