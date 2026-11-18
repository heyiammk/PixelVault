from django.urls import path
from .views import DashboardSPAView

app_name = "dashboard"

urlpatterns = [
    path("", DashboardSPAView.as_view(active_page="dashboard"), name="home"),
    path("upload/", DashboardSPAView.as_view(active_page="upload"), name="upload"),
    path("analysis/", DashboardSPAView.as_view(active_page="analysis"), name="analysis"),
    path("report/", DashboardSPAView.as_view(active_page="report"), name="report"),
    path("batch/", DashboardSPAView.as_view(active_page="batch"), name="batch"),
    path("downloads/", DashboardSPAView.as_view(active_page="downloads"), name="downloads"),
]
