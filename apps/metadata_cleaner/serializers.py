from rest_framework import serializers
from .models import CleaningLog


class CleanMetadataRequestSerializer(serializers.Serializer):
    job_id = serializers.UUIDField(required=True)
    image_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True
    )
    remove_gps = serializers.BooleanField(default=True, required=False)
    remove_serial_numbers = serializers.BooleanField(default=True, required=False)
    remove_owner_info = serializers.BooleanField(default=True, required=False)
    remove_contact_info = serializers.BooleanField(default=True, required=False)
    remove_ai_and_c2pa = serializers.BooleanField(default=False, required=False)
    scrub_pixel_watermark = serializers.BooleanField(default=False, required=False)
    nuclear_clean = serializers.BooleanField(default=False, required=False)


class CleaningLogSerializer(serializers.ModelSerializer):
    file_id = serializers.UUIDField(source="image.id", read_only=True)
    original_filename = serializers.CharField(source="image.original_filename", read_only=True)

    class Meta:
        model = CleaningLog
        fields = [
            "id",
            "file_id",
            "original_filename",
            "engine_used",
            "removed_gps",
            "removed_serial_numbers",
            "removed_owner_info",
            "removed_contact_info",
            "preserved_copyright",
            "preserved_c2pa",
            "preserved_original_pixels",
            "reencoded",
            "removed_keys",
            "preserved_keys",
            "created_at",
        ]
