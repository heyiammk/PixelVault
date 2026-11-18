"""
Batch Processing Service & Temporary File Cleanup Utility.
Provides error isolation per image, individual status updates, progress tracking,
and automatic cleanup of expired temporary uploads.
"""
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from django.conf import settings
from django.utils import timezone
from apps.batch_processor.models import BatchJob
from apps.image_upload.models import ImageFile
from apps.image_analyzer.models import MetadataRecord
from apps.image_analyzer.services import analyze_image_file
from apps.metadata_cleaner.models import CleaningLog
from apps.metadata_cleaner.services import clean_image_personal_metadata
from apps.reports.services import generate_or_update_job_report


def run_batch_analysis(job: BatchJob, image_ids: Optional[List[str]] = None) -> BatchJob:
    """
    Runs metadata and SynthID analysis across all (or specified) images in a BatchJob
    with strict per-image error isolation.
    """
    qs = job.images.all()
    if image_ids:
        qs = qs.filter(id__in=image_ids)

    job.status = BatchJob.STATUS_ANALYZING
    job.save(update_fields=["status", "updated_at"])

    failed_count = 0
    processed_count = 0

    for img_obj in qs:
        try:
            abs_path = (settings.MEDIA_ROOT / img_obj.temp_rel_path).resolve()
            analysis = analyze_image_file(
                file_path=abs_path,
                exiftool_path=settings.EXIFTOOL_PATH,
                synthid_provider_module=settings.SYNTHID_PROVIDER_MODULE,
            )

            MetadataRecord.objects.update_or_create(
                image=img_obj,
                defaults={
                    "exif_before": analysis["exif"],
                    "xmp_before": analysis["xmp"],
                    "iptc_before": analysis["iptc"],
                    "png_chunks_before": analysis["png_chunks"],
                    "gps_before": analysis["gps"],
                    "camera_before": analysis["camera"],
                    "software_before": analysis["software"],
                    "c2pa_before": analysis["c2pa"],
                    "personal_fields_detected": analysis["personal_fields_detected"],
                    "preserved_provenance_fields": analysis["preserved_provenance_fields"],
                    "synthid_status": analysis["synthid"]["status"],
                    "synthid_provider": analysis["synthid"]["provider"],
                    "synthid_details": analysis["synthid"]["details"],
                    "privacy_risk_score": analysis["privacy_risk_score"],
                },
            )
            if img_obj.status == ImageFile.STATUS_UPLOADED:
                img_obj.status = ImageFile.STATUS_ANALYZED
                img_obj.error_message = ""
                img_obj.save(update_fields=["status", "error_message", "updated_at"])
            processed_count += 1
        except Exception as exc:
            failed_count += 1
            img_obj.status = ImageFile.STATUS_ERROR
            img_obj.error_message = f"Analysis failed: {exc}"
            img_obj.save(update_fields=["status", "error_message", "updated_at"])

    total = job.images.count()
    job.total_files = total
    job.processed_files = processed_count
    job.failed_files = failed_count
    if failed_count == total and total > 0:
        job.status = BatchJob.STATUS_FAILED
    elif failed_count > 0:
        job.status = BatchJob.STATUS_PARTIAL_FAILURE
    else:
        job.status = BatchJob.STATUS_ANALYZED
    job.save()

    generate_or_update_job_report(job)
    return job


def run_batch_cleaning(
    job: BatchJob,
    options: Optional[Dict[str, bool]] = None,
    image_ids: Optional[List[str]] = None,
) -> BatchJob:
    """
    Runs selective personal metadata cleaning across all (or specified) images in a BatchJob
    with strict per-image error isolation, followed by post-cleaning verification analysis.
    """
    if options is None:
        options = {
            "remove_gps": True,
            "remove_serial_numbers": True,
            "remove_owner_info": True,
            "remove_contact_info": True,
        }

    job.status = BatchJob.STATUS_CLEANING
    job.cleaning_options = options
    job.processed_files = 0
    job.failed_files = 0
    job.save(update_fields=["status", "cleaning_options", "processed_files", "failed_files", "updated_at"])

    qs = job.images.all()
    if image_ids:
        qs = qs.filter(id__in=image_ids)

    processed_count = 0
    failed_count = 0

    for img_obj in qs:
        try:
            src_abs = (settings.MEDIA_ROOT / img_obj.temp_rel_path).resolve()
            if not src_abs.exists():
                raise FileNotFoundError(f"Source file missing for {img_obj.original_filename}")

            # Ensure before-analysis exists
            if not hasattr(img_obj, "metadata_record"):
                before_analysis = analyze_image_file(
                    file_path=src_abs,
                    exiftool_path=settings.EXIFTOOL_PATH,
                    synthid_provider_module=settings.SYNTHID_PROVIDER_MODULE,
                )
                meta_rec = MetadataRecord.objects.create(
                    image=img_obj,
                    exif_before=before_analysis["exif"],
                    xmp_before=before_analysis["xmp"],
                    iptc_before=before_analysis["iptc"],
                    png_chunks_before=before_analysis["png_chunks"],
                    gps_before=before_analysis["gps"],
                    camera_before=before_analysis["camera"],
                    software_before=before_analysis["software"],
                    c2pa_before=before_analysis["c2pa"],
                    personal_fields_detected=before_analysis["personal_fields_detected"],
                    preserved_provenance_fields=before_analysis["preserved_provenance_fields"],
                    synthid_status=before_analysis["synthid"]["status"],
                    synthid_provider=before_analysis["synthid"]["provider"],
                    synthid_details=before_analysis["synthid"]["details"],
                    privacy_risk_score=before_analysis["privacy_risk_score"],
                )
            else:
                meta_rec = img_obj.metadata_record

            ext = os.path.splitext(img_obj.stored_temp_name)[1].lower()
            processed_filename = f"cleaned_{img_obj.stored_temp_name}" if not img_obj.stored_processed_name else img_obj.stored_processed_name
            dst_abs = (settings.PROCESSED_MEDIA_ROOT / processed_filename).resolve()

            clean_res = clean_image_personal_metadata(
                src_path=src_abs,
                dst_path=dst_abs,
                file_format=img_obj.file_format,
                options=options,
                exiftool_path=settings.EXIFTOOL_PATH,
            )

            # Re-analyze cleaned file to populate authentic after-report
            after_analysis = analyze_image_file(
                file_path=dst_abs,
                exiftool_path=settings.EXIFTOOL_PATH,
                synthid_provider_module=settings.SYNTHID_PROVIDER_MODULE,
            )

            meta_rec.exif_after = after_analysis["exif"]
            meta_rec.xmp_after = after_analysis["xmp"]
            meta_rec.iptc_after = after_analysis["iptc"]
            meta_rec.png_chunks_after = after_analysis["png_chunks"]
            meta_rec.gps_after = after_analysis["gps"]
            meta_rec.camera_after = after_analysis["camera"]
            meta_rec.software_after = after_analysis["software"]
            meta_rec.c2pa_after = after_analysis["c2pa"]
            meta_rec.synthid_status = after_analysis["synthid"]["status"]
            meta_rec.synthid_provider = after_analysis["synthid"]["provider"]
            meta_rec.synthid_details = after_analysis["synthid"]["details"]
            meta_rec.privacy_risk_score = after_analysis["privacy_risk_score"]
            meta_rec.removed_fields_summary = clean_res["removed_keys"]
            meta_rec.cleaned_at = timezone.now()
            meta_rec.save()

            CleaningLog.objects.create(
                image=img_obj,
                engine_used=clean_res["engine_used"],
                removed_gps=options.get("remove_gps", True),
                removed_serial_numbers=options.get("remove_serial_numbers", True),
                removed_owner_info=options.get("remove_owner_info", True),
                removed_contact_info=options.get("remove_contact_info", True),
                preserved_copyright=True,
                preserved_c2pa=True,
                preserved_original_pixels=clean_res["preserved_original_pixels"],
                reencoded=clean_res["reencoded"],
                removed_keys=clean_res["removed_keys"],
                preserved_keys=clean_res["preserved_keys"],
            )

            img_obj.stored_processed_name = processed_filename
            img_obj.processed_rel_path = f"processed/{processed_filename}"
            img_obj.cleaned_size_bytes = clean_res["cleaned_size_bytes"]
            img_obj.sha256_after = clean_res["sha256_after"]
            img_obj.pixel_hash_after = clean_res["pixel_hash_after"]
            img_obj.status = ImageFile.STATUS_CLEANED
            img_obj.error_message = ""
            img_obj.save()

            processed_count += 1
        except Exception as exc:
            failed_count += 1
            img_obj.status = ImageFile.STATUS_ERROR
            img_obj.error_message = f"Cleaning failed: {exc}"
            img_obj.save(update_fields=["status", "error_message", "updated_at"])

        job.processed_files = processed_count + failed_count
        job.failed_files = failed_count
        job.save(update_fields=["processed_files", "failed_files", "updated_at"])

    total = job.images.count()
    job.total_files = total
    job.completed_at = timezone.now()
    if failed_count == total and total > 0:
        job.status = BatchJob.STATUS_FAILED
    elif failed_count > 0:
        job.status = BatchJob.STATUS_PARTIAL_FAILURE
    else:
        job.status = BatchJob.STATUS_COMPLETED
    job.save()

    generate_or_update_job_report(job)
    return job


def cleanup_expired_temp_files(max_age_hours: Optional[int] = None) -> int:
    """
    Removes temporary files in media/temp/ older than max_age_hours.
    Returns count of deleted files.
    """
    retention_hours = max_age_hours if max_age_hours is not None else settings.TEMP_FILE_RETENTION_HOURS
    cutoff = time.time() - (retention_hours * 3600)
    deleted = 0
    for root_dir in (settings.TEMP_MEDIA_ROOT,):
        if not root_dir.exists():
            continue
        for item in root_dir.iterdir():
            if item.name == ".gitkeep" or not item.is_file():
                continue
            if item.stat().st_mtime < cutoff:
                item.unlink(missing_ok=True)
                deleted += 1
    return deleted
