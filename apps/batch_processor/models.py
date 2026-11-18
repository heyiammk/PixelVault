import uuid
from django.db import models


class BatchJob(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_ANALYZING = "ANALYZING"
    STATUS_ANALYZED = "ANALYZED"
    STATUS_CLEANING = "CLEANING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_PARTIAL_FAILURE = "PARTIAL_FAILURE"
    STATUS_FAILED = "FAILED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ANALYZING, "Analyzing"),
        (STATUS_ANALYZED, "Analyzed"),
        (STATUS_CLEANING, "Cleaning"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_PARTIAL_FAILURE, "Partial Failure"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(
        max_length=24, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True
    )
    total_files = models.PositiveIntegerField(default=0)
    processed_files = models.PositiveIntegerField(default=0)
    failed_files = models.PositiveIntegerField(default=0)
    cleaning_options = models.JSONField(default=dict, blank=True)
    error_summary = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Batch Job"
        verbose_name_plural = "Batch Jobs"

    def __str__(self) -> str:
        return f"BatchJob {self.id} ({self.status})"

    @property
    def progress_percentage(self) -> int:
        if self.total_files == 0:
            return 0
        return min(100, int(round((self.processed_files / self.total_files) * 100)))
