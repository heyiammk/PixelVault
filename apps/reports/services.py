"""
JSON Analysis & Before/After Report Builder Service.
Compiles complete per-image and batch-level metadata comparison, SynthID verification,
pixel integrity verification, and provenance preservation reports.
"""
from typing import Dict, Any
from django.utils import timezone
from apps.batch_processor.models import BatchJob
from apps.reports.models import AnalysisReport


def build_job_report_payload(job: BatchJob) -> Dict[str, Any]:
    """
    Constructs a structured JSON report for a BatchJob suitable for API responses
    and downloadable JSON audit files.
    """
    images_report = []
    total_personal_removed = 0
    all_pixels_preserved = True

    for img in job.images.select_related("metadata_record").all():
        meta = getattr(img, "metadata_record", None)
        removed_list = meta.removed_fields_summary if meta else []
        total_personal_removed += len(removed_list)

        pixel_verified = (
            bool(img.pixel_hash_before and img.pixel_hash_after)
            and img.pixel_hash_before == img.pixel_hash_after
        )
        if img.status == "CLEANED" and not pixel_verified:
            all_pixels_preserved = False

        images_report.append({
            "file_id": str(img.id),
            "original_filename": img.original_filename,
            "file_format": img.file_format,
            "mime_type": img.mime_type,
            "dimensions": {"width": img.width, "height": img.height},
            "file_size_before_bytes": img.file_size_bytes,
            "file_size_after_bytes": img.cleaned_size_bytes,
            "sha256_before": img.sha256_before,
            "sha256_after": img.sha256_after,
            "pixel_hash_before": img.pixel_hash_before,
            "pixel_hash_after": img.pixel_hash_after,
            "original_pixels_preserved": pixel_verified if img.status == "CLEANED" else True,
            "status": img.status,
            "error_message": img.error_message,
            "synthid_detection": {
                "status": meta.synthid_status if meta else "Unable to verify",
                "provider": meta.synthid_provider if meta else "Not Analyzed",
                "details": meta.synthid_details if meta else "",
                "watermark_removal_performed": False,
            },
            "privacy_risk_score_before": meta.privacy_risk_score if meta else 0,
            "personal_fields_detected": meta.personal_fields_detected if meta else [],
            "preserved_provenance_fields": meta.preserved_provenance_fields if meta else {},
            "removed_personal_fields": removed_list,
            "metadata_before": {
                "EXIF": meta.exif_before if meta else {},
                "XMP": meta.xmp_before if meta else {},
                "IPTC": meta.iptc_before if meta else {},
                "PNG_Text_Chunks": meta.png_chunks_before if meta else {},
                "GPS": meta.gps_before if meta else {},
                "Camera": meta.camera_before if meta else {},
                "Software": meta.software_before if meta else {},
                "C2PA_Content_Credentials": meta.c2pa_before if meta else {},
            },
            "metadata_after": {
                "EXIF": meta.exif_after if meta else {},
                "XMP": meta.xmp_after if meta else {},
                "IPTC": meta.iptc_after if meta else {},
                "PNG_Text_Chunks": meta.png_chunks_after if meta else {},
                "GPS": meta.gps_after if meta else {},
                "Camera": meta.camera_after if meta else {},
                "Software": meta.software_after if meta else {},
                "C2PA_Content_Credentials": meta.c2pa_after if meta else {},
            },
        })

    return {
        "project": "Image Privacy Cleaner",
        "processing_mode": "100% Local Offline Processing",
        "job_id": str(job.id),
        "job_status": job.status,
        "generated_at": timezone.now().isoformat(),
        "summary": {
            "total_files": job.total_files,
            "processed_files": job.processed_files,
            "failed_files": job.failed_files,
            "progress_percentage": job.progress_percentage,
            "total_personal_metadata_fields_removed": total_personal_removed,
            "all_cleaned_images_preserved_exact_pixels": all_pixels_preserved,
            "provenance_and_c2pa_policy": "Preserved (Copyright, Authorship, Licensing, AI disclosure, C2PA provenance, Content credentials)",
            "synthid_policy": "Honest verification only; watermark removal is strictly prohibited and disabled.",
        },
        "cleaning_options_applied": job.cleaning_options,
        "images": images_report,
    }


def generate_or_update_job_report(job: BatchJob) -> AnalysisReport:
    payload = build_job_report_payload(job)
    report_obj, _ = AnalysisReport.objects.update_or_create(
        job=job,
        defaults={"report_payload": payload},
    )
    return report_obj
