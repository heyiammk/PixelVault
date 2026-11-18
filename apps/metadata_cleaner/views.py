from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.batch_processor.models import BatchJob
from apps.batch_processor.services import run_batch_cleaning
from apps.image_analyzer.models import MetadataRecord
from apps.image_analyzer.serializers import MetadataRecordSerializer
from .models import CleaningLog
from .serializers import CleanMetadataRequestSerializer, CleaningLogSerializer


class MetadataCleanAPIView(APIView):
    """
    POST /api/v1/clean/
    Removes selected personal metadata and optionally strips AI/C2PA manifests
    and scrubs invisible pixel watermarks.
    """

    def post(self, request, *args, **kwargs):
        serializer = CleanMetadataRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        vdata = serializer.validated_data
        job = get_object_or_404(BatchJob, id=vdata["job_id"])
        options = {
            "remove_gps": vdata.get("remove_gps", True),
            "remove_serial_numbers": vdata.get("remove_serial_numbers", True),
            "remove_owner_info": vdata.get("remove_owner_info", True),
            "remove_contact_info": vdata.get("remove_contact_info", True),
            "remove_ai_and_c2pa": vdata.get("remove_ai_and_c2pa", False),
            "scrub_pixel_watermark": vdata.get("scrub_pixel_watermark", False),
        }

        job = run_batch_cleaning(
            job=job,
            options=options,
            image_ids=vdata.get("image_ids"),
        )

        logs = CleaningLog.objects.filter(image__job=job).select_related("image")
        records = MetadataRecord.objects.filter(image__job=job).select_related("image")

        return Response(
            {
                "status": "success",
                "job_id": str(job.id),
                "job_status": job.status,
                "progress_percentage": job.progress_percentage,
                "total_files": job.total_files,
                "processed_files": job.processed_files,
                "failed_files": job.failed_files,
                "cleaning_logs": CleaningLogSerializer(logs, many=True).data,
                "metadata_records": MetadataRecordSerializer(records, many=True).data,
                "download_zip_url": f"/api/v1/download-zip/{job.id}/",
                "report_url": f"/api/v1/report/{job.id}/",
            },
            status=status.HTTP_200_OK,
        )
