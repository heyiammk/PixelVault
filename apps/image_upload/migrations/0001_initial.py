import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("batch_processor", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ImageFile",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("original_filename", models.CharField(max_length=255)),
                ("stored_temp_name", models.CharField(max_length=255, unique=True)),
                ("stored_processed_name", models.CharField(blank=True, default="", max_length=255)),
                ("temp_rel_path", models.CharField(max_length=512)),
                ("processed_rel_path", models.CharField(blank=True, default="", max_length=512)),
                ("file_format", models.CharField(max_length=16)),
                ("mime_type", models.CharField(max_length=64)),
                ("file_size_bytes", models.BigIntegerField(default=0)),
                ("cleaned_size_bytes", models.BigIntegerField(blank=True, null=True)),
                ("width", models.PositiveIntegerField(default=0)),
                ("height", models.PositiveIntegerField(default=0)),
                ("sha256_before", models.CharField(max_length=64)),
                ("sha256_after", models.CharField(blank=True, default="", max_length=64)),
                ("pixel_hash_before", models.CharField(blank=True, default="", max_length=64)),
                ("pixel_hash_after", models.CharField(blank=True, default="", max_length=64)),
                ("signature_valid", models.BooleanField(default=True)),
                ("status", models.CharField(
                    choices=[
                        ("UPLOADED", "Uploaded"),
                        ("ANALYZED", "Analyzed"),
                        ("CLEANED", "Cleaned"),
                        ("ERROR", "Error"),
                    ],
                    db_index=True,
                    default="UPLOADED",
                    max_length=20,
                )),
                ("error_message", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("job", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="batch_processor.batchjob")),
            ],
            options={
                "verbose_name": "Image File",
                "verbose_name_plural": "Image Files",
                "ordering": ["created_at"],
            },
        ),
    ]
