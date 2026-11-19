"""Pytest configuration for Django tests."""
import os
from pathlib import Path

import django
from django.conf import settings

# Must configure before any Django imports
if not settings.configured:
    TEST_BASE = Path("/tmp/test_pixelvault")
    TEST_BASE.mkdir(parents=True, exist_ok=True)
    (TEST_BASE / "static").mkdir(exist_ok=True)
    (TEST_BASE / "media" / "temp").mkdir(parents=True, exist_ok=True)
    (TEST_BASE / "media" / "processed").mkdir(parents=True, exist_ok=True)

    settings.configure(
        DEBUG=True,
        SECRET_KEY="test-secret-key-for-testing-only",
        ALLOWED_HOSTS=["*"],
        INSTALLED_APPS=[
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "rest_framework",
            "apps.dashboard",
            "apps.image_upload",
            "apps.image_analyzer",
            "apps.metadata_cleaner",
            "apps.batch_processor",
            "apps.downloads",
            "apps.reports",
        ],
        MIDDLEWARE=[
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
        ],
        ROOT_URLCONF="config.urls",
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [],
                "APP_DIRS": True,
                "OPTIONS": {
                    "context_processors": [
                        "django.template.context_processors.debug",
                        "django.template.context_processors.request",
                        "django.contrib.auth.context_processors.auth",
                        "django.contrib.messages.context_processors.messages",
                    ],
                },
            }
        ],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        STATIC_URL="/static/",
        STATICFILES_DIRS=[TEST_BASE / "static"],
        MEDIA_URL="/media/",
        MEDIA_ROOT=TEST_BASE / "media",
        TEMP_MEDIA_ROOT=TEST_BASE / "media" / "temp",
        PROCESSED_MEDIA_ROOT=TEST_BASE / "media" / "processed",
        MAX_UPLOAD_BATCH_SIZE=40,
        MAX_UPLOAD_FILE_SIZE_MB=40,
        MAX_UPLOAD_FILE_SIZE_BYTES=40 * 1024 * 1024,
        ALLOWED_IMAGE_FORMATS=["JPG", "JPEG", "PNG", "WEBP", "TIFF"],
        TEMP_FILE_RETENTION_HOURS=24,
        EXIFTOOL_PATH="exiftool",
        SYNTHID_PROVIDER_MODULE="",
        SYNTHID_API_ENDPOINT="",
        REST_FRAMEWORK={
            "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
            "DEFAULT_PARSER_CLASSES": [
                "rest_framework.parsers.JSONParser",
                "rest_framework.parsers.MultiPartParser",
                "rest_framework.parsers.FormParser",
            ],
            "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
            "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
        },
    )

django.setup()

# Run migrations
from django.core.management import call_command
call_command("migrate", verbosity=0, interactive=False)