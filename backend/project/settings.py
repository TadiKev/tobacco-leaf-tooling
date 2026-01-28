# settings.py
from pathlib import Path
import os
from datetime import timedelta

# --------------------------------------------------
# BASE
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------
# SECURITY
# --------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
DEBUG = os.environ.get("DEBUG", "1") == "1"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,10.0.2.2").split(",")


# --------------------------------------------------
# APPLICATIONS
# --------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "inference_logs",
    "recommendations",
    "accounts",
    "corsheaders",
    "core",
]

# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]

# Ensure corsheaders.middleware.CorsMiddleware is present at the top (no-op if already present)
MIDDLEWARE = (
    ["corsheaders.middleware.CorsMiddleware"] + [m for m in MIDDLEWARE if m != "corsheaders.middleware.CorsMiddleware"]
) if "corsheaders.middleware.CorsMiddleware" not in MIDDLEWARE else MIDDLEWARE

# --------------------------------------------------
# URL / TEMPLATES
# --------------------------------------------------
ROOT_URLCONF = "project.urls"

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

WSGI_APPLICATION = "project.wsgi.application"

# --------------------------------------------------
# DATABASE (Postgres via docker-compose)
# --------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "tobaccodb"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}
APPEND_SLASH = False

# --------------------------------------------------
# PASSWORDS
# --------------------------------------------------
AUTH_PASSWORD_VALIDATORS = []

# --------------------------------------------------
# CORS (dev)
# --------------------------------------------------
# Development convenience — set to False / restrict origins in production
CORS_ALLOW_ALL_ORIGINS = True

# --------------------------------------------------
# REST FRAMEWORK + SIMPLE JWT
# --------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    # You can add other settings here if needed, e.g.:
    # "ALGORITHM": "HS256",
    # "SIGNING_KEY": SECRET_KEY,
    # "AUTH_HEADER_TYPES": ("Bearer",),
}

# --------------------------------------------------
# I18N
# --------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------
# STATIC & MEDIA
# --------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --------------------------------------------------
# 🔥 ML / TFLITE CONFIG (CONNECTED TO YOUR SCRIPT)
# --------------------------------------------------

# Root workspace (Docker-friendly)
WORKSPACE_DIR = Path(os.environ.get("WORKSPACE_DIR", BASE_DIR))

# Data directories
ML_DATA_DIR = WORKSPACE_DIR / "data"
ML_REP_SAMPLES_DIR = ML_DATA_DIR / "rep_samples"

# Model directories
ML_MODELS_DIR = WORKSPACE_DIR / "models"
ML_TFLITE_DIR = ML_MODELS_DIR / "tflite"
ML_HARDENED_DIR = ML_MODELS_DIR / "hardened"

# Default model paths
ML_DEFAULT_KERAS_MODEL = ML_HARDENED_DIR / "best_model.keras"
ML_TFLITE_FP16_MODEL = ML_TFLITE_DIR / "model_fp16.tflite"
ML_TFLITE_INT8_MODEL = ML_TFLITE_DIR / "model_int8.tflite"
