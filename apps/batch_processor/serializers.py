from rest_framework import serializers
from apps.image_upload.serializers import ImageFileSerializer
from apps.image_analyzer.serializers import MetadataRecordSerializer
from .models import BatchJob


class BatchJobStatusSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.IntegerField(read_only=True)
    images = ImageFileSerializer(many=True, read_only=True)
    metadata_records = serializers.SerializerMethodField()
    download_zip_url = serializers.SerializerMethodField()
    report_url = serializers.SerializerMethodField()

    class Meta:
        model = BatchJob
        fields = [
            "id",
            "status",
            "total_files",
            "processed_files",
            "failed_files",
            "progress_percentage",
            "cleaning_options",
            "error_summary",
            "created_at",
            "updated_at",
            "completed_at",
            "download_zip_url",
            "report_url",
            "images",
            "metadata_records",
        ]

    def get_metadata_records(self, obj: BatchJob):
        records = [
            img.metadata_record
            for img in obj.images.all()
            if hasattr(img, "metadata_record")
        ]
        return MetadataRecordSerializer(records, many=True).data

    def get_download_zip_url(self, obj: BatchJob) -> str:
        return f"/api/v1/download-zip/{obj.id}/"

    def get_report_url(self, obj: BatchJob) -> str:
        return f"/api/v1/report/{obj.id}/"
