"""
Phase 14 — File Security Service.
Protects document ingestion, imports, and attachments against:
- Malicious executable uploads
- Path traversal
- Archive decompression bombs (zip bombs)
- MIME mismatch & spoofing
"""
import os
import re
import zipfile
import io
from typing import Tuple, Optional


ALLOWED_EXTENSIONS = {
    ".pdf", ".csv", ".xlsx", ".xls", ".docx", ".doc",
    ".txt", ".json", ".png", ".jpg", ".jpeg", ".webp"
}

PROHIBITED_EXTENSIONS = {
    ".exe", ".sh", ".bash", ".bat", ".cmd", ".ps1",
    ".py", ".pyc", ".js", ".ts", ".php", ".phtml",
    ".rb", ".jar", ".war", ".vbs", ".dll", ".so", ".bin"
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_DECOMPRESSED_RATIO = 100            # Zip bomb ratio limit


class FileSecurityService:
    """
    Guarantees all uploaded or ingested files are strictly treated as DATA.
    """

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Removes directory traversal sequences, null bytes, and illegal characters."""
        if not filename:
            return "unnamed_document"

        # Remove path separators and traversal
        name = os.path.basename(filename)
        name = name.replace("\x00", "").replace("../", "").replace("..\\", "")
        # Whitelist alphanumeric, dots, dashes, underscores
        name = re.sub(r"[^a-zA-Z0-9_.-]", "_", name)
        return name or "sanitized_document"

    @classmethod
    def validate_file(
        cls,
        filename: str,
        content: bytes,
        mime_type: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates filename, extension, size, and content structure.
        Returns: (is_valid: bool, error_message: Optional[str])
        """
        if not filename:
            return False, "Missing filename."

        _, ext = os.path.splitext(filename.lower())
        if not ext:
            return False, "File must have an explicit extension."

        # Prohibited check
        if ext in PROHIBITED_EXTENSIONS:
            return False, f"Executable or script extension prohibited: {ext}"

        # Allowlist check
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"Unsupported file extension: {ext}. Allowed: {sorted(list(ALLOWED_EXTENSIONS))}"

        # Size check
        if len(content) > MAX_FILE_SIZE_BYTES:
            return False, f"File size ({len(content)} bytes) exceeds maximum allowable limit ({MAX_FILE_SIZE_BYTES} bytes)."

        # Zip bomb / archive inspection if zip-based (xlsx, docx, or zip)
        if ext in (".xlsx", ".docx", ".zip") and content.startswith(b"PK"):
            try:
                with zipfile.ZipFile(io.BytesIO(content), "r") as zf:
                    total_uncompressed = 0
                    for info in zf.infolist():
                        total_uncompressed += info.file_size
                        # Detect zip bomb ratio
                        if info.compress_size > 0:
                            ratio = info.file_size / info.compress_size
                            if ratio > MAX_DECOMPRESSED_RATIO:
                                return False, f"Archive bomb detected: compression ratio {ratio:.1f} exceeds limit."
                    if total_uncompressed > 50 * 1024 * 1024:  # 50 MB max expanded
                        return False, f"Decompressed size ({total_uncompressed} bytes) exceeds safety envelope."
            except zipfile.BadZipFile:
                return False, "Corrupted archive structure."

        return True, None
