import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("image_upload", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MetadataRecord",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("exif_before", models.JSONField(blank=True, default=dict)),
                ("xmp_before", models.JSONField(blank=True, default=dict)),
                ("iptc_before", models.JSONField(blank=True, default=dict)),
                ("png_chunks_before", models.JSONField(blank=True, default=dict)),
                ("gps_before", models.JSONField(blank=True, default=dict)),
                ("camera_before", models.JSONField(blank=True, default=dict)),
                ("software_before", models.JSONField(blank=True, default=dict)),
                ("c2pa_before", models.JSONField(blank=True, default=dict)),
                ("personal_fields_detected", models.JSONField(blank=True, default=list)),
                ("preserved_provenance_fields", models.JSONField(blank=True, default=dict)),
                ("synthid_status", models.CharField(
                    choices=[
                        ("Detected", "Detected"),
                        ("Not detected", "Not detected"),
                        ("Unable to verify", "Unable to verify"),
                    ],
                    default="Unable to verify",
                    max_length=32,
                )),
                ("synthid_provider", models.CharField(default="Official Verifier Not Configured", max_length=128)),
                ("synthid_details", models.TextField(blank=True, default="No official SynthID detector integration is configured locally; watermark status cannot be verified without an official detector.")),
                ("exif_after", models.JSONField(blank=True, default=dict)),
                ("xmp_after", models.JSONField(blank=True, default=dict)),
                ("iptc_after", models.JSONField(blank=True, default=dict)),
                ("png_chunks_after", models.JSONField(blank=True, default=dict)),
                ("gps_after", models.JSONField(blank=True, default=dict)),
                ("camera_after", models.JSONField(blank=True, default=dict)),
                ("software_after", models.JSONField(blank=True, default=dict)),
                ("c2pa_after", models.JSONField(blank=True, default=dict)),
                ("removed_fields_summary", models.JSONField(blank=True, default=list)),
                ("privacy_risk_score", models.PositiveSmallIntegerField(default=0)),
                ("analyzed_at", models.DateTimeField(auto_now_add=True)),
                ("cleaned_at", models.DateTimeField(blank=True, null=True)),
                ("image", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="metadata_record", to="image_upload.imagefile")),
            ],
            options={
                "verbose_name": "Metadata Record",
                "verbose_name_plural": "Metadata Records",
            },
        ),
    ]
