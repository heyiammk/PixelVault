from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.batch_processor.models import BatchJob
from apps.image_upload.models import ImageFile
from apps.reports.services import build_job_report_payload
from .models import DownloadAudit
from .services import (
    resolve_safe_download_path,
    build_safe_job_zip_buffer,
    DownloadSecurityError,
)


class SingleImageDownloadAPIView(APIView):
    """
    GET /api/v1/download/{file_id}/
    Downloads an individual processed image with path traversal protection.
    """

    def get(self, request, file_id, *args, **kwargs):
        img_obj = get_object_or_404(ImageFile, id=file_id)
        try:
            abs_path, dl_name = resolve_safe_download_path(img_obj)
        except DownloadSecurityError as sec_err:
            return Response(
                {"status": "error", "error": str(sec_err)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except FileNotFoundError as fnf_err:
            return Response(
                {"status": "error", "error": str(fnf_err)},
                status=status.HTTP_404_NOT_FOUND,
            )

        DownloadAudit.objects.create(
            job=img_obj.job,
            image=img_obj,
            download_type=DownloadAudit.TYPE_SINGLE,
            bytes_served=abs_path.stat().st_size,
        )

        response = FileResponse(
            open(abs_path, "rb"),
            as_attachment=True,
            filename=dl_name,
            content_type=img_obj.mime_type,
        )
        return response


class BatchZipDownloadAPIView(APIView):
    """
    GET /api/v1/download-zip/{job_id}/
    Downloads all processed images in a BatchJob packaged inside a safe ZIP archive.
    """

    def get(self, request, job_id, *args, **kwargs):
        job = get_object_or_404(BatchJob, id=job_id)
        report_payload = build_job_report_payload(job)
        zip_buffer, zip_filename = build_safe_job_zip_buffer(job, include_report_payload=report_payload)
        zip_bytes = zip_buffer.getvalue()

        DownloadAudit.objects.create(
            job=job,
            download_type=DownloadAudit.TYPE_ZIP,
            bytes_served=len(zip_bytes),
        )

        response = HttpResponse(zip_bytes, content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{zip_filename}"'
        response["Content-Length"] = str(len(zip_bytes))
        return response
