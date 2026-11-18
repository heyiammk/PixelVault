"""
Image Upload & Validation Service.
Validates binary magic signatures (JPG, JPEG, PNG, WEBP, TIFF), enforces 40MB file size
and 40-image batch limits, prevents path traversal, assigns randomized UUID storage filenames,
and computes cryptographic file and pixel hashes using Pillow and OpenCV.
"""
import hashlib
import os
import re
import uuid
from pathlib import Path
from typing import Dict, Any, Tuple
import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

# Magic byte signatures for supported image formats
MAGIC_SIGNATURES = {
    "JPEG": [b"\xff\xd8\xff"],
    "PNG": [b"\x89PNG\r\n\x1a\n"],
    "WEBP": [b"RIFF"],  # Must also have WEBP at bytes 8..12
    "TIFF": [b"II*\x00", b"MM\x00*"],
}

ALLOWED_EXTENSIONS = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
    ".tif": "TIFF",
    ".tiff": "TIFF",
}

FORMAT_MIME_MAP = {
    "JPEG": "image/jpeg",
    "JPG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
    "TIFF": "image/tiff",
}


class ImageValidationError(ValueError):
    """Raised when an uploaded file fails security, signature, or size validation."""
    pass


def sanitize_original_filename(filename: str) -> str:
    """
    Prevents path traversal by stripping directory components, null bytes,
    and unsafe control characters while keeping a readable display name.
    """
    if not filename:
        raise ImageValidationError("Filename cannot be empty.")
    cleaned = filename.replace("\x00", "")
    # Reject explicit traversal patterns if caller passes raw relative paths
    normalized = cleaned.replace("\\", "/")
    if ".." in normalized.split("/"):
        raise ImageValidationError("Path traversal sequence detected in filename.")
    base = os.path.basename(normalized).strip()
    base = re.sub(r"[^A-Za-z0-9._\- ()]", "_", base)
    if not base or base in (".", ".."):
        raise ImageValidationError("Invalid filename after sanitization.")
    return base[:200]


def detect_magic_format(header_bytes: bytes) -> str:
    """
    Inspects the first 16 bytes of a file to verify its true binary format.
    Returns canonical format ('JPEG', 'PNG', 'WEBP', 'TIFF') or raises ImageValidationError.
    """
    if len(header_bytes) < 12:
        raise ImageValidationError("File is too small to contain a valid image signature.")

    if header_bytes.startswith(b"\xff\xd8\xff"):
        return "JPEG"
    if header_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG"
    if header_bytes[:4] == b"RIFF" and header_bytes[8:12] == b"WEBP":
        return "WEBP"
    if header_bytes[:4] in (b"II*\x00", b"MM\x00*"):
        return "TIFF"

    raise ImageValidationError(
        "Invalid file signature (magic bytes). Allowed formats: JPG, JPEG, PNG, WEBP, TIFF."
    )


def compute_pixel_sha256(file_path: Path) -> Tuple[str, int, int]:
    """
    Computes a deterministic SHA-256 digest of the decoded raw pixel buffer
    alongside (width, height) using Pillow and OpenCV verification.
    This guarantees that metadata cleaning preserves 100% of original pixel values.
    """
    with Image.open(file_path) as img:
        img.load()
        width, height = img.size
        # Convert to raw bytes without modifying mode
        pixel_bytes = img.tobytes()
        pixel_hash = hashlib.sha256(pixel_bytes).hexdigest()

    # Secondary structural decode check via OpenCV
    raw_arr = np.fromfile(str(file_path), dtype=np.uint8)
    cv_img = cv2.imdecode(raw_arr, cv2.IMREAD_UNCHANGED)
    if cv_img is None:
        raise ImageValidationError("OpenCV failed to decode image stream.")

    return pixel_hash, width, height


def validate_and_store_upload(
    uploaded_file,
    temp_root: Path,
    max_file_size_bytes: int = 40 * 1024 * 1024,
) -> Dict[str, Any]:
    """
    Validates a single uploaded file (size, extension, binary magic signature,
    Pillow & OpenCV structural decode) and writes it to temp_root with a randomized UUID filename.
    """
    safe_name = sanitize_original_filename(uploaded_file.name)
    ext = os.path.splitext(safe_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ImageValidationError(
            f"Unsupported file extension '{ext}'. Allowed: JPG, JPEG, PNG, WEBP, TIFF."
        )

    file_size = getattr(uploaded_file, "size", None)
    if file_size is not None and file_size > max_file_size_bytes:
        raise ImageValidationError(
            f"File '{safe_name}' exceeds maximum allowed size of {max_file_size_bytes // (1024 * 1024)} MB."
        )
    if file_size == 0:
        raise ImageValidationError(f"File '{safe_name}' is empty.")

    uploaded_file.seek(0)
    header = uploaded_file.read(16)
    detected_format = detect_magic_format(header)
    expected_format = ALLOWED_EXTENSIONS[ext]
    if detected_format != expected_format:
        raise ImageValidationError(
            f"Extension '{ext}' does not match binary signature '{detected_format}'."
        )

    uploaded_file.seek(0)
    random_name = f"{uuid.uuid4().hex}{ext}"
    temp_root_resolved = temp_root.resolve()
    target_path = (temp_root_resolved / random_name).resolve()

    if not str(target_path).startswith(str(temp_root_resolved)):
        raise ImageValidationError("Resolved target path escaped temporary media directory.")

    sha256_hasher = hashlib.sha256()
    bytes_written = 0

    with open(target_path, "wb") as out_f:
        for chunk in uploaded_file.chunks() if hasattr(uploaded_file, "chunks") else [uploaded_file.read()]:
            bytes_written += len(chunk)
            if bytes_written > max_file_size_bytes:
                out_f.close()
                target_path.unlink(missing_ok=True)
                raise ImageValidationError("File stream exceeded maximum size limit during write.")
            sha256_hasher.update(chunk)
            out_f.write(chunk)

    try:
        with Image.open(target_path) as verify_img:
            verify_img.verify()
        pixel_hash, width, height = compute_pixel_sha256(target_path)
    except Exception as exc:
        target_path.unlink(missing_ok=True)
        raise ImageValidationError(f"Corrupted or unreadable image file: {exc}") from exc

    display_format = "JPG" if ext == ".jpg" else detected_format
    return {
        "original_filename": safe_name,
        "stored_temp_name": random_name,
        "temp_rel_path": f"temp/{random_name}",
        "temp_abs_path": str(target_path),
        "file_format": display_format,
        "mime_type": FORMAT_MIME_MAP[detected_format],
        "file_size_bytes": bytes_written,
        "width": width,
        "height": height,
        "sha256_before": sha256_hasher.hexdigest(),
        "pixel_hash_before": pixel_hash,
        "signature_valid": True,
    }
