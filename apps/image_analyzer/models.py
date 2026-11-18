import uuid
from django.db import models
from apps.image_upload.models import ImageFile


class MetadataRecord(models.Model):
    SYNTHID_DETECTED = "Detected"
    SYNTHID_NOT_DETECTED = "Not detected"
    SYNTHID_UNABLE = "Unable to verify"

    SYNTHID_CHOICES = [
        (SYNTHID_DETECTED, "Detected"),
        (SYNTHID_NOT_DETECTED, "Not detected"),
        (SYNTHID_UNABLE, "Unable to verify"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.OneToOneField(
        ImageFile, on_delete=models.CASCADE, related_name="metadata_record"
    )
    exif_before = models.JSONField(default=dict, blank=True)
    xmp_before = models.JSONField(default=dict, blank=True)
    iptc_before = models.JSONField(default=dict, blank=True)
    png_chunks_before = models.JSONField(default=dict, blank=True)
    gps_before = models.JSONField(default=dict, blank=True)
    camera_before = models.JSONField(default=dict, blank=True)
    software_before = models.JSONField(default=dict, blank=True)
    c2pa_before = models.JSONField(default=dict, blank=True)
    personal_fields_detected = models.JSONField(default=list, blank=True)
    preserved_provenance_fields = models.JSONField(default=dict, blank=True)

    synthid_status = models.CharField(
        max_length=32, choices=SYNTHID_CHOICES, default=SYNTHID_UNABLE
    )
    synthid_provider = models.CharField(max_length=128, default="Official Verifier Not Configured")
    synthid_details = models.TextField(
        blank=True,
        default="No official SynthID detector integration is configured locally; watermark status cannot be verified without an official detector."
    )

    exif_after = models.JSONField(default=dict, blank=True)
    xmp_after = models.JSONField(default=dict, blank=True)
    iptc_after = models.JSONField(default=dict, blank=True)
    png_chunks_after = models.JSONField(default=dict, blank=True)
    gps_after = models.JSONField(default=dict, blank=True)
    camera_after = models.JSONField(default=dict, blank=True)
    software_after = models.JSONField(default=dict, blank=True)
    c2pa_after = models.JSONField(default=dict, blank=True)
    removed_fields_summary = models.JSONField(default=list, blank=True)

    privacy_risk_score = models.PositiveSmallIntegerField(default=0)
    analyzed_at = models.DateTimeField(auto_now_add=True)
    cleaned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Metadata Record"
        verbose_name_plural = "Metadata Records"

    def __str__(self) -> str:
        return f"MetadataRecord for {self.image.original_filename}"
