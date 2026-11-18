"""
Django settings for Image Privacy Cleaner.
Local-first image analysis and personal metadata cleaning application.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-local-image-privacy-cleaner-default-key-change-me"
)

# Security requirement: never expose debug mode publicly; defaults to False
DEBUG = os.getenv("DEBUG", "False").strip().lower() in ("true", "1", "yes")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    # Modular local apps
    "apps.dashboard",
    "apps.image_upload",
    "apps.image_analyzer",
    "apps.metadata_cleaner",
    "apps.batch_processor",
    "apps.downloads",
    "apps.reports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
TEMP_MEDIA_ROOT = MEDIA_ROOT / "temp"
PROCESSED_MEDIA_ROOT = MEDIA_ROOT / "processed"

os.makedirs(TEMP_MEDIA_ROOT, exist_ok=True)
os.makedirs(PROCESSED_MEDIA_ROOT, exist_ok=True)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Upload & Batch Limits
MAX_UPLOAD_BATCH_SIZE = int(os.getenv("MAX_UPLOAD_BATCH_SIZE", "40"))
MAX_UPLOAD_FILE_SIZE_MB = int(os.getenv("MAX_UPLOAD_FILE_SIZE_MB", "40"))
MAX_UPLOAD_FILE_SIZE_BYTES = MAX_UPLOAD_FILE_SIZE_MB * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_FILE_SIZE_BYTES * 2
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_FILE_SIZE_BYTES

ALLOWED_IMAGE_FORMATS = ["JPG", "JPEG", "PNG", "WEBP", "TIFF"]
TEMP_FILE_RETENTION_HOURS = int(os.getenv("TEMP_FILE_RETENTION_HOURS", "24"))
EXIFTOOL_PATH = os.getenv("EXIFTOOL_PATH", "exiftool")
SYNTHID_PROVIDER_MODULE = os.getenv("SYNTHID_PROVIDER_MODULE", "").strip()
SYNTHID_API_ENDPOINT = os.getenv("SYNTHID_API_ENDPOINT", "").strip()

# Security Headers & Local Protection
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "SAMEORIGIN"
SECURE_CONTENT_TYPE_NOSNIFF = True

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}
