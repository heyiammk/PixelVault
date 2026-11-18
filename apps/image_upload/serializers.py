from django.conf import settings
from rest_framework import serializers
from .models import ImageFile


class ImageUploadRequestSerializer(serializers.Serializer):
    images = serializers.ListField(
        child=serializers.FileField(allow_empty_file=False),
        allow_empty=False,
        max_length=settings.MAX_UPLOAD_BATCH_SIZE,
        help_text="Upload between 1 and 40 image files (JPG, JPEG, PNG, WEBP, TIFF, up to 40MB each).",
    )
    job_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_images(self, files):
        if len(files) > settings.MAX_UPLOAD_BATCH_SIZE:
            raise serializers.ValidationError(
                f"Batch limit exceeded: maximum {settings.MAX_UPLOAD_BATCH_SIZE} images per batch."
            )
        return files


class ImageFileSerializer(serializers.ModelSerializer):
    preview_url = serializers.SerializerMethodField()
    cleaned_url = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = ImageFile
        fields = [
            "id",
            "job_id",
            "original_filename",
            "file_format",
            "mime_type",
            "file_size_bytes",
            "cleaned_size_bytes",
            "width",
            "height",
            "sha256_before",
            "sha256_after",
            "pixel_hash_before",
            "pixel_hash_after",
            "signature_valid",
            "status",
            "error_message",
            "preview_url",
            "cleaned_url",
            "download_url",
            "created_at",
        ]

    def get_preview_url(self, obj: ImageFile) -> str:
        return f"{settings.MEDIA_URL}{obj.temp_rel_path}"

    def get_cleaned_url(self, obj: ImageFile) -> str:
        if obj.processed_rel_path:
            return f"{settings.MEDIA_URL}{obj.processed_rel_path}"
        return ""

    def get_download_url(self, obj: ImageFile) -> str:
        return f"/api/v1/download/{obj.id}/"
