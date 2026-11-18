"""
Safe File & ZIP Packaging Service.
Enforces strict path traversal protection and safe archive member naming
(prevents Zip Slip / absolute path injection / duplicate collisions).
"""
import io
import os
import re
import zipfile
from pathlib import Path
from typing import Tuple
from django.conf import settings
from apps.batch_processor.models import BatchJob
from apps.image_upload.models import ImageFile


class DownloadSecurityError(PermissionError):
    """Raised when a download path fails sandbox or traversal validation."""
    pass


def resolve_safe_download_path(image_obj: ImageFile) -> Tuple[Path, str]:
    """
    Resolves the processed file path (or original temp path if not yet cleaned)
    and verifies that the resolved file sits strictly inside MEDIA_ROOT.
    """
    rel_path = image_obj.processed_rel_path or image_obj.temp_rel_path
    if not rel_path:
        raise DownloadSecurityError("No file path available for this image.")

    media_root_resolved = settings.MEDIA_ROOT.resolve()
    candidate = (media_root_resolved / rel_path).resolve()

    if not str(candidate).startswith(str(media_root_resolved)):
        raise DownloadSecurityError("Path traversal detected during download resolution.")

    if not candidate.exists() or not candidate.is_file():
        raise FileNotFoundError("Requested image file does not exist on disk.")

    base_name = os.path.basename(image_obj.original_filename)
    safe_base = re.sub(r"[^A-Za-z0-9._\- ()]", "_", base_name)
    prefix = "cleaned_" if image_obj.processed_rel_path else ""
    download_filename = f"{prefix}{safe_base}"
    return candidate, download_filename


def build_safe_job_zip_buffer(job: BatchJob, include_report_payload: dict = None) -> Tuple[io.BytesIO, str]:
    """
    Creates an in-memory ZIP archive containing all processed images for a BatchJob
    plus an optional metadata_privacy_report.json.
    Guarantees every archive member name is flat (no '/' or '..' segments) and deduplicated.
    """
    import json

    zip_buffer = io.BytesIO()
    seen_names = set()

    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for img_obj in job.images.all():
            if img_obj.status == ImageFile.STATUS_ERROR:
                continue
            try:
                abs_path, dl_name = resolve_safe_download_path(img_obj)
            except Exception:
                continue

            # Ensure flat archive entry name (anti-Zip-Slip)
            flat_name = os.path.basename(dl_name).replace("..", "").replace("/", "_").replace("\\", "_")
            stem, ext = os.path.splitext(flat_name)
            counter = 1
            unique_name = flat_name
            while unique_name in seen_names:
                unique_name = f"{stem}_{counter}{ext}"
                counter += 1
            seen_names.add(unique_name)

            zf.write(abs_path, arcname=unique_name)

        if include_report_payload is not None:
            report_bytes = json.dumps(include_report_payload, indent=2).encode("utf-8")
            zf.writestr("metadata_privacy_report.json", report_bytes)

    zip_buffer.seek(0)
    archive_filename = f"image_privacy_cleaned_{str(job.id)[:8]}.zip"
    return zip_buffer, archive_filename
