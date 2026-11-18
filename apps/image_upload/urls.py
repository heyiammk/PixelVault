from django.urls import path
from .views import ImageUploadAPIView

app_name = "image_upload"

urlpatterns = [
    path("", ImageUploadAPIView.as_view(), name="upload_images"),
]
