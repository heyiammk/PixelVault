from rest_framework import serializers
from .models import AnalysisReport


class AnalysisReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisReport
        fields = ["id", "job_id", "report_payload", "generated_at"]
