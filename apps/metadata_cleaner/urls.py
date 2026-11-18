from django.urls import path
from .views import MetadataCleanAPIView

app_name = "metadata_cleaner"

urlpatterns = [
    path("", MetadataCleanAPIView.as_view(), name="clean_metadata"),
]
