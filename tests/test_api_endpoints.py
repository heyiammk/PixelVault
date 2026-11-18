"""
Django & DRF Integration Test Suite covering all 7 REST API endpoints:
- POST /api/v1/upload/
- POST /api/v1/analyze/
- POST /api/v1/clean/
- GET /api/v1/jobs/{job_id}/
- GET /api/v1/download/{file_id}/
- GET /api/v1/download-zip/{job_id}/
- GET /api/v1/report/{job_id}/
"""
import io
import zipfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from tests.test_services_and_pipeline import inject_png_text_and_c2pa


class ImagePrivacyCleanerAPITests(TestCase):
    def _create_test_png_file(self, filename="test_image.png") -> SimpleUploadedFile:
        buf = io.BytesIO()
        img = Image.new("RGB", (48, 48), color=(20, 160, 120))
        img.save(buf, format="PNG")
        enriched = inject_png_text_and_c2pa(
            buf.getvalue(),
            {
                "GPSLatitude": "22.8456 N",
                "SerialNumber": "CAM-SN-5555",
                "OwnerName": "Jane Doe",
                "Copyright": "Copyright 2026 Jane Doe",
            },
            include_c2pa=True,
        )
        return SimpleUploadedFile(filename, enriched, content_type="image/png")

    def test_full_api_workflow_upload_analyze_clean_status_downloads_and_report(self):
        # 1. POST /api/v1/upload/
        png_file = self._create_test_png_file("camera_shot.png")
        up_res = self.client.post("/api/v1/upload/", {"images": [png_file]}, format="multipart")
        self.assertEqual(up_res.status_code, 201)
        up_json = up_res.json()
        self.assertEqual(up_json["status"], "success")
        job_id = up_json["job_id"]
        file_id = up_json["uploaded"][0]["id"]

        # 2. POST /api/v1/analyze/
        an_res = self.client.post(
            "/api/v1/analyze/",
            data={"job_id": job_id},
            content_type="application/json",
        )
        self.assertEqual(an_res.status_code, 200)
        an_json = an_res.json()
        self.assertIn(an_json["results"][0]["synthid_status"], ("Detected", "Unable to verify"))
        self.assertIn("GPSLatitude", an_json["results"][0]["png_chunks_before"])

        # 3. POST /api/v1/clean/
        cl_res = self.client.post(
            "/api/v1/clean/",
            data={
                "job_id": job_id,
                "remove_gps": True,
                "remove_serial_numbers": True,
                "remove_owner_info": True,
                "remove_contact_info": True,
            },
            content_type="application/json",
        )
        self.assertEqual(cl_res.status_code, 200)
        cl_json = cl_res.json()
        self.assertEqual(cl_json["job_status"], "COMPLETED")
        self.assertTrue(cl_json["cleaning_logs"][0]["preserved_original_pixels"])

        # 4. GET /api/v1/jobs/{job_id}/
        job_res = self.client.get(f"/api/v1/jobs/{job_id}/")
        self.assertEqual(job_res.status_code, 200)
        self.assertEqual(job_res.json()["progress_percentage"], 100)

        # 5. GET /api/v1/download/{file_id}/
        dl_res = self.client.get(f"/api/v1/download/{file_id}/")
        self.assertEqual(dl_res.status_code, 200)
        self.assertIn("cleaned_camera_shot.png", dl_res["Content-Disposition"])

        # 6. GET /api/v1/download-zip/{job_id}/
        zip_res = self.client.get(f"/api/v1/download-zip/{job_id}/")
        self.assertEqual(zip_res.status_code, 200)
        zf = zipfile.ZipFile(io.BytesIO(zip_res.content))
        names = zf.namelist()
        self.assertIn("cleaned_camera_shot.png", names)
        self.assertIn("metadata_privacy_report.json", names)

        # 7. GET /api/v1/report/{job_id}/
        rep_res = self.client.get(f"/api/v1/report/{job_id}/")
        self.assertEqual(rep_res.status_code, 200)
        rep_json = rep_res.json()
        self.assertTrue(rep_json["summary"]["all_cleaned_images_preserved_exact_pixels"])
