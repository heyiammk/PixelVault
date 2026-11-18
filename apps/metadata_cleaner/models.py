import uuid
from django.db import models
from apps.image_upload.models import ImageFile


class CleaningLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ForeignKey(
        ImageFile, on_delete=models.CASCADE, related_name="cleaning_logs"
    )
    engine_used = models.CharField(max_length=64)
    removed_gps = models.BooleanField(default=True)
    removed_serial_numbers = models.BooleanField(default=True)
    removed_owner_info = models.BooleanField(default=True)
    removed_contact_info = models.BooleanField(default=True)
    preserved_copyright = models.BooleanField(default=True)
    preserved_c2pa = models.BooleanField(default=True)
    preserved_original_pixels = models.BooleanField(default=True)
    reencoded = models.BooleanField(default=False)
    removed_keys = models.JSONField(default=list, blank=True)
    preserved_keys = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Cleaning Log"
        verbose_name_plural = "Cleaning Logs"

    def __str__(self) -> str:
        return f"CleaningLog ({self.engine_used}) for {self.image.original_filename}"
