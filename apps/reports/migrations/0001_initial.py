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
            name="AnalysisReport",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("report_payload", models.JSONField(default=dict)),
                ("generated_at", models.DateTimeField(auto_now=True)),
                ("job", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="analysis_report", to="batch_processor.batchjob")),
            ],
            options={
                "verbose_name": "Analysis Report",
                "verbose_name_plural": "Analysis Reports",
            },
        ),
    ]
