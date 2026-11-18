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
            name="CleaningLog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("engine_used", models.CharField(max_length=64)),
                ("removed_gps", models.BooleanField(default=True)),
                ("removed_serial_numbers", models.BooleanField(default=True)),
                ("removed_owner_info", models.BooleanField(default=True)),
                ("removed_contact_info", models.BooleanField(default=True)),
                ("preserved_copyright", models.BooleanField(default=True)),
                ("preserved_c2pa", models.BooleanField(default=True)),
                ("preserved_original_pixels", models.BooleanField(default=True)),
                ("reencoded", models.BooleanField(default=False)),
                ("removed_keys", models.JSONField(blank=True, default=list)),
                ("preserved_keys", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("image", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cleaning_logs", to="image_upload.imagefile")),
            ],
            options={
                "verbose_name": "Cleaning Log",
                "verbose_name_plural": "Cleaning Logs",
                "ordering": ["-created_at"],
            },
        ),
    ]
