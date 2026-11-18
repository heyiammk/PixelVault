from django.urls import path
from .views import SingleImageDownloadAPIView, BatchZipDownloadAPIView

app_name = "downloads"

urlpatterns = [
    path("download/<uuid:file_id>/", SingleImageDownloadAPIView.as_view(), name="download_single"),
    path("download-zip/<uuid:job_id>/", BatchZipDownloadAPIView.as_view(), name="download_zip"),
]
