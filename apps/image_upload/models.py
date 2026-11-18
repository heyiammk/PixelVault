import uuid
from django.db import models
from apps.batch_processor.models import BatchJob


class ImageFile(models.Model):
    STATUS_UPLOADED = "UPLOADED"
    STATUS_ANALYZED = "ANALYZED"
    STATUS_CLEANED = "CLEANED"
    STATUS_ERROR = "ERROR"

    STATUS_CHOICES = [
        (STATUS_UPLOADED, "Uploaded"),
        (STATUS_ANALYZED, "Analyzed"),
        (STATUS_CLEANED, "Cleaned"),
        (STATUS_ERROR, "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        BatchJob, on_delete=models.CASCADE, related_name="images"
    )
    original_filename = models.CharField(max_length=255)
    stored_temp_name = models.CharField(max_length=255, unique=True)
    stored_processed_name = models.CharField(max_length=255, blank=True, default="")
    temp_rel_path = models.CharField(max_length=512)
    processed_rel_path = models.CharField(max_length=512, blank=True, default="")
    file_format = models.CharField(max_length=16)
    mime_type = models.CharField(max_length=64)
    file_size_bytes = models.BigIntegerField(default=0)
    cleaned_size_bytes = models.BigIntegerField(null=True, blank=True)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    sha256_before = models.CharField(max_length=64)
    sha256_after = models.CharField(max_length=64, blank=True, default="")
    pixel_hash_before = models.CharField(max_length=64, blank=True, default="")
    pixel_hash_after = models.CharField(max_length=64, blank=True, default="")
    signature_valid = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_UPLOADED, db_index=True
    )
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Image File"
        verbose_name_plural = "Image Files"

    def __str__(self) -> str:
        return f"{self.original_filename} ({self.status})"
