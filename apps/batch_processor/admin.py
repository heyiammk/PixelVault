from django.contrib import admin
from .models import BatchJob


@admin.register(BatchJob)
class BatchJobAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "total_files", "processed_files", "failed_files", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id",)
