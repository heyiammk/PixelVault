from django.apps import AppConfig


class ImageAnalyzerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.image_analyzer"
    verbose_name = "Image Metadata & SynthID Analyzer"
