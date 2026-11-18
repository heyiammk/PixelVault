from django.conf import settings
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.batch_processor.models import BatchJob
from apps.batch_processor.services import cleanup_expired_temp_files
from .models import ImageFile
from .serializers import ImageUploadRequestSerializer, ImageFileSerializer
from .services import validate_and_store_upload, ImageValidationError


class ImageUploadAPIView(APIView):
    """
    POST /api/v1/upload/
    Accepts 1..40 image files via multipart/form-data, validates binary file signatures
    and 40MB file size limits, stores randomized temporary filenames, and returns job_id
    with per-image validation results.
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        # Opportunistically clean expired temp files
        cleanup_expired_temp_files()

        # Accept either 'images' or 'files' key from form data
        incoming_files = request.FILES.getlist("images") or request.FILES.getlist("files")
        data_input = {"images": incoming_files}
        if request.data.get("job_id"):
            data_input["job_id"] = request.data.get("job_id")

        serializer = ImageUploadRequestSerializer(data=data_input)
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_files = serializer.validated_data["images"]
        job_id = serializer.validated_data.get("job_id")

        if job_id:
            job = BatchJob.objects.filter(id=job_id).first()
            if not job:
                job = BatchJob.objects.create(total_files=len(validated_files))
        else:
            job = BatchJob.objects.create(total_files=len(validated_files))

        created_images = []
        rejected_files = []

        for f_obj in validated_files:
            try:
                meta = validate_and_store_upload(
                    uploaded_file=f_obj,
                    temp_root=settings.TEMP_MEDIA_ROOT,
                    max_file_size_bytes=settings.MAX_UPLOAD_FILE_SIZE_BYTES,
                )
                img_record = ImageFile.objects.create(
                    job=job,
                    original_filename=meta["original_filename"],
                    stored_temp_name=meta["stored_temp_name"],
                    temp_rel_path=meta["temp_rel_path"],
                    file_format=meta["file_format"],
                    mime_type=meta["mime_type"],
                    file_size_bytes=meta["file_size_bytes"],
                    width=meta["width"],
                    height=meta["height"],
                    sha256_before=meta["sha256_before"],
                    pixel_hash_before=meta["pixel_hash_before"],
                    signature_valid=True,
                    status=ImageFile.STATUS_UPLOADED,
                )
                created_images.append(img_record)
            except ImageValidationError as val_err:
                rejected_files.append({
                    "filename": getattr(f_obj, "name", "unknown"),
                    "error": str(val_err),
                })
            except Exception as exc:
                rejected_files.append({
                    "filename": getattr(f_obj, "name", "unknown"),
                    "error": f"Unexpected validation error: {exc}",
                })

        job.total_files = job.images.count()
        if job.total_files == 0 and rejected_files:
            job.status = BatchJob.STATUS_FAILED
            job.error_summary = "; ".join(r["error"] for r in rejected_files)
            job.save()
            return Response(
                {
                    "status": "error",
                    "job_id": str(job.id),
                    "uploaded": [],
                    "rejected": rejected_files,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        job.save()
        return Response(
            {
                "status": "success",
                "job_id": str(job.id),
                "total_uploaded": len(created_images),
                "uploaded": ImageFileSerializer(created_images, many=True).data,
                "rejected": rejected_files,
            },
            status=status.HTTP_201_CREATED,
        )
