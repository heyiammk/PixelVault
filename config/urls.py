"""
Root URL configuration for Image Privacy Cleaner.
Uses explicit re_path + django.views.static.serve for /media/ and /static/
so local offline runs with DEBUG=False still serve image previews properly.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.dashboard.urls")),
    path("api/v1/upload/", include("apps.image_upload.urls")),
    path("api/v1/analyze/", include("apps.image_analyzer.urls")),
    path("api/v1/clean/", include("apps.metadata_cleaner.urls")),
    path("api/v1/jobs/", include("apps.batch_processor.urls")),
    path("api/v1/", include("apps.downloads.urls")),
    path("api/v1/report/", include("apps.reports.urls")),
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATICFILES_DIRS[0]}),
]
