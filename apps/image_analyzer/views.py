from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.batch_processor.models import BatchJob
from apps.batch_processor.services import run_batch_analysis
from .models import MetadataRecord
from .serializers import AnalyzeRequestSerializer, MetadataRecordSerializer


class ImageAnalyzeAPIView(APIView):
    """
    POST /api/v1/analyze/
    Analyzes image metadata (EXIF, XMP, IPTC, PNG text chunks, GPS, Camera, Software, C2PA)
    and SynthID verification status for a BatchJob.
    """

    def post(self, request, *args, **kwargs):
        serializer = AnalyzeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job = get_object_or_404(BatchJob, id=serializer.validated_data["job_id"])
        image_ids = serializer.validated_data.get("image_ids")
        job = run_batch_analysis(job=job, image_ids=image_ids)

        records = MetadataRecord.objects.filter(image__job=job).select_related("image")
        return Response(
            {
                "status": "success",
                "job_id": str(job.id),
                "job_status": job.status,
                "total_files": job.total_files,
                "processed_files": job.processed_files,
                "failed_files": job.failed_files,
                "results": MetadataRecordSerializer(records, many=True).data,
            },
            status=status.HTTP_200_OK,
        )
