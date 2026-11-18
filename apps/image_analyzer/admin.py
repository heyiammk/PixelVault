from django.contrib import admin
from .models import MetadataRecord


@admin.register(MetadataRecord)
class MetadataRecordAdmin(admin.ModelAdmin):
    list_display = ("image", "synthid_status", "privacy_risk_score", "analyzed_at", "cleaned_at")
    list_filter = ("synthid_status",)
