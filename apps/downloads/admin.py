from django.contrib import admin
from .models import DownloadAudit


@admin.register(DownloadAudit)
class DownloadAuditAdmin(admin.ModelAdmin):
    list_display = ("id", "download_type", "job", "image", "bytes_served", "downloaded_at")
