from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import BatchJob
from .serializers import BatchJobStatusSerializer


class BatchJobDetailAPIView(APIView):
    """
    GET /api/v1/jobs/{job_id}/
    Returns batch processing progress, per-file statuses, and metadata records.
    """

    def get(self, request, job_id, *args, **kwargs):
        job = get_object_or_404(
            BatchJob.objects.prefetch_related("images__metadata_record"),
            id=job_id,
        )
        serializer = BatchJobStatusSerializer(job)
        return Response(serializer.data, status=status.HTTP_200_OK)
