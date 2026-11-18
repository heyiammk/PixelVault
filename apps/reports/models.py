import uuid
from django.db import models
from apps.batch_processor.models import BatchJob


class AnalysisReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.OneToOneField(
        BatchJob, on_delete=models.CASCADE, related_name="analysis_report"
    )
    report_payload = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Analysis Report"
        verbose_name_plural = "Analysis Reports"

    def __str__(self) -> str:
        return f"AnalysisReport for Job {self.job_id}"
