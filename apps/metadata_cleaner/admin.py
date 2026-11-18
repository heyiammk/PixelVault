from django.contrib import admin
from .models import CleaningLog


@admin.register(CleaningLog)
class CleaningLogAdmin(admin.ModelAdmin):
    list_display = (
        "image",
        "engine_used",
        "preserved_original_pixels",
        "reencoded",
        "created_at",
    )
