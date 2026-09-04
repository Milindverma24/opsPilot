import hashlib
import os
from typing import Tuple
from fastapi import HTTPException, status
from apps.api.app.core.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".csv", ".txt", ".json", ".eml", ".md", ".markdown"}
MAX_SIZE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def compute_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def validate_file(filename: str, content: bytes) -> Tuple[str, int, str]:
    """
    Validates file extension, size, and returns (file_ext, file_size, file_hash).
    Raises HTTPException if file is invalid.
    """
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a filename"
        )

    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    size = len(content)
    if size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty"
        )

    if size > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum upload limit of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    file_hash = compute_sha256(content)
    return ext.lstrip("."), size, file_hash
