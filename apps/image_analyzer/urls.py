from django.urls import path
from .views import ImageAnalyzeAPIView

app_name = "image_analyzer"

urlpatterns = [
    path("", ImageAnalyzeAPIView.as_view(), name="analyze_images"),
]
