from django.urls import path
from .views import JobAnalysisReportAPIView

app_name = "reports"

urlpatterns = [
    path("<uuid:job_id>/", JobAnalysisReportAPIView.as_view(), name="job_report"),
]
