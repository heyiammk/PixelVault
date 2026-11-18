from rest_framework import serializers
from .models import MetadataRecord


class AnalyzeRequestSerializer(serializers.Serializer):
    job_id = serializers.UUIDField(required=True)
    image_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True
    )


class MetadataRecordSerializer(serializers.ModelSerializer):
    file_id = serializers.UUIDField(source="image.id", read_only=True)
    original_filename = serializers.CharField(source="image.original_filename", read_only=True)
    file_format = serializers.CharField(source="image.file_format", read_only=True)
    width = serializers.IntegerField(source="image.width", read_only=True)
    height = serializers.IntegerField(source="image.height", read_only=True)
    file_size_bytes = serializers.IntegerField(source="image.file_size_bytes", read_only=True)
    cleaned_size_bytes = serializers.IntegerField(source="image.cleaned_size_bytes", read_only=True)
    pixel_hash_before = serializers.CharField(source="image.pixel_hash_before", read_only=True)
    pixel_hash_after = serializers.CharField(source="image.pixel_hash_after", read_only=True)
    image_status = serializers.CharField(source="image.status", read_only=True)

    class Meta:
        model = MetadataRecord
        fields = [
            "id",
            "file_id",
            "original_filename",
            "file_format",
            "width",
            "height",
            "file_size_bytes",
            "cleaned_size_bytes",
            "pixel_hash_before",
            "pixel_hash_after",
            "image_status",
            "exif_before",
            "xmp_before",
            "iptc_before",
            "png_chunks_before",
            "gps_before",
            "camera_before",
            "software_before",
            "c2pa_before",
            "personal_fields_detected",
            "preserved_provenance_fields",
            "synthid_status",
            "synthid_provider",
            "synthid_details",
            "exif_after",
            "xmp_after",
            "iptc_after",
            "png_chunks_after",
            "gps_after",
            "camera_after",
            "software_after",
            "c2pa_after",
            "removed_fields_summary",
            "privacy_risk_score",
            "analyzed_at",
            "cleaned_at",
        ]
