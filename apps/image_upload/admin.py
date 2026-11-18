from django.contrib import admin
from .models import ImageFile


@admin.register(ImageFile)
class ImageFileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "original_filename",
        "file_format",
        "file_size_bytes",
        "width",
        "height",
        "status",
        "created_at",
    )
    list_filter = ("status", "file_format")
    search_fields = ("original_filename", "stored_temp_name")
