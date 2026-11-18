from django.urls import path
from .views import BatchJobDetailAPIView

app_name = "batch_processor"

urlpatterns = [
    path("<uuid:job_id>/", BatchJobDetailAPIView.as_view(), name="job_detail"),
]
