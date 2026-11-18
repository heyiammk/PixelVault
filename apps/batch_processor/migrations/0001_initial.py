import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BatchJob",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(
                    choices=[
                        ("PENDING", "Pending"),
                        ("ANALYZING", "Analyzing"),
                        ("ANALYZED", "Analyzed"),
                        ("CLEANING", "Cleaning"),
                        ("COMPLETED", "Completed"),
                        ("PARTIAL_FAILURE", "Partial Failure"),
                        ("FAILED", "Failed"),
                    ],
                    db_index=True,
                    default="PENDING",
                    max_length=24,
                )),
                ("total_files", models.PositiveIntegerField(default=0)),
                ("processed_files", models.PositiveIntegerField(default=0)),
                ("failed_files", models.PositiveIntegerField(default=0)),
                ("cleaning_options", models.JSONField(blank=True, default=dict)),
                ("error_summary", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Batch Job",
                "verbose_name_plural": "Batch Jobs",
                "ordering": ["-created_at"],
            },
        ),
    ]
