import uuid
from django.db import models
from apps.batch_processor.models import BatchJob
from apps.image_upload.models import ImageFile


class DownloadAudit(models.Model):
    TYPE_SINGLE = "SINGLE"
    TYPE_ZIP = "ZIP"
    TYPE_REPORT = "REPORT"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        BatchJob, on_delete=models.CASCADE, null=True, blank=True, related_name="downloads"
    )
    image = models.ForeignKey(
        ImageFile, on_delete=models.SET_NULL, null=True, blank=True
    )
    download_type = models.CharField(max_length=16, default=TYPE_SINGLE)
    bytes_served = models.BigIntegerField(default=0)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-downloaded_at"]
