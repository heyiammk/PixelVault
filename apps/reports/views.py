import json
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.batch_processor.models import BatchJob
from apps.downloads.models import DownloadAudit
from .services import generate_or_update_job_report


class JobAnalysisReportAPIView(APIView):
    """
    GET /api/v1/report/{job_id}/
    Returns or downloads the comprehensive JSON analysis and before/after metadata report.
    Pass ?download=1 to trigger an attachment download.
    """

    def get(self, request, job_id, *args, **kwargs):
        job = get_object_or_404(
            BatchJob.objects.prefetch_related("images__metadata_record"),
            id=job_id,
        )
        report_obj = generate_or_update_job_report(job)
        payload = report_obj.report_payload

        if request.GET.get("download") in ("1", "true", "yes"):
            raw_json = json.dumps(payload, indent=2)
            DownloadAudit.objects.create(
                job=job,
                download_type=DownloadAudit.TYPE_REPORT,
                bytes_served=len(raw_json.encode("utf-8")),
            )
            response = HttpResponse(raw_json, content_type="application/json")
            filename = f"metadata_report_{str(job.id)[:8]}.json"
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response

        return Response(payload, status=status.HTTP_200_OK)
