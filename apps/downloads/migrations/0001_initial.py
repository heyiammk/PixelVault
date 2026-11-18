import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("batch_processor", "0001_initial"),
        ("image_upload", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DownloadAudit",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("download_type", models.CharField(default="SINGLE", max_length=16)),
                ("bytes_served", models.BigIntegerField(default=0)),
                ("downloaded_at", models.DateTimeField(auto_now_add=True)),
                ("image", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="image_upload.imagefile")),
                ("job", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="downloads", to="batch_processor.batchjob")),
            ],
            options={
                "ordering": ["-downloaded_at"],
            },
        ),
    ]
