"""
Frontend views serving the Premium Dark SaaS Dashboard and its 6 core sections:
- Dashboard
- Image Upload
- Image Analysis
- Metadata Report
- Batch Processing
- Download Center
"""
from django.conf import settings
from django.views.generic import TemplateView
from apps.batch_processor.models import BatchJob
from apps.image_upload.models import ImageFile


class DashboardSPAView(TemplateView):
    template_name = "dashboard/index.html"
    active_page = "dashboard"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        recent_jobs = BatchJob.objects.prefetch_related("images__metadata_record")[:10]
        total_jobs = BatchJob.objects.count()
        total_images = ImageFile.objects.count()
        cleaned_images = ImageFile.objects.filter(status=ImageFile.STATUS_CLEANED).count()
        ctx.update({
            "active_page": self.active_page,
            "recent_jobs": recent_jobs,
            "stats": {
                "total_jobs": total_jobs,
                "total_images": total_images,
                "cleaned_images": cleaned_images,
                "max_batch": settings.MAX_UPLOAD_BATCH_SIZE,
                "max_file_size_mb": settings.MAX_UPLOAD_FILE_SIZE_MB,
                "allowed_formats": ", ".join(settings.ALLOWED_IMAGE_FORMATS),
            },
        })
        return ctx
