# godcares_backend/settings.py  — Development-ready (OpenAPI enabled)

import os
import importlib
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv
import dj_database_url

# -------------------------------------------------------------------
# Paths & Base
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------------------------
# Core Security (ENV)
# -------------------------------------------------------------------
SECRET_KEY = config("SECRET_KEY", default="dev-insecure-change-me")
DEBUG = config("DEBUG", default=True, cast=bool)

# Hosts
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1,[::1]",
    cast=Csv(),
)

# CSRF trusted origins (ongeza kama unatumia vite/next/React)
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default=(
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "http://localhost:5173,"
        "http://127.0.0.1:5173"
    ),
    cast=Csv(),
)

# -------------------------------------------------------------------
# Applications
# -------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "django_filters",
    "corsheaders",
    "drf_spectacular",  # OpenAPI generator
]

LOCAL_APPS = [
    "content.apps.ContentConfig",
    "notifications.apps.NotificationsConfig",
    "discipleship.apps.DiscipleshipConfig",
    "progress",  # kama haina AppConfig maalum
    "core",      # middleware yako ipo hapa
    # "shop",      # optional — itaongezwa chini endapo ipo
    # "mentorship" # optional — itaongezwa chini endapo ipo
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Ongeza apps za hiari ikiwa zipo (epuka error wakati wa dev)
for _optional in ("shop", "mentorship"):
    try:
        importlib.import_module(_optional)
        if _optional not in INSTALLED_APPS:
            INSTALLED_APPS.append(_optional)
    except ImportError:
        # Kama app haipo bado, ruka tu bila kufanya crash
        pass

SITE_ID = config("SITE_ID", default=1, cast=int)

# -------------------------------------------------------------------
# Middleware
# -------------------------------------------------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",

    # Core custom middlewares
    "core.middleware.ReferralCodeCaptureMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    # Activity & journey tracking
    "core.middleware.MissionTrackingMiddleware",
    "core.middleware.DiscipleshipJourneyMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# -------------------------------------------------------------------
# URLs / WSGI
# -------------------------------------------------------------------
ROOT_URLCONF = "godcares_backend.urls"
WSGI_APPLICATION = "godcares_backend.wsgi.application"
# ASGI_APPLICATION = "godcares_backend.asgi.application"  # kama utaongeza ASGI

# -------------------------------------------------------------------
# Templates
# -------------------------------------------------------------------
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
                # Context processors zako
                "notifications.context_processors.unread_notifications",
                "notifications.context_processors.notif_counts",
                "content.context_processors.site_settings",
            ],
        },
    },
]

# -------------------------------------------------------------------
# Database (sqlite kwa dev; DATABASE_URL ikipo, itatumika)
# -------------------------------------------------------------------
DATABASE_URL = config("DATABASE_URL", default="")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0 if DEBUG else 600,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# -------------------------------------------------------------------
# Password Validators
# -------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "MinimumLengthValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "CommonPasswordValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "NumericPasswordValidator"
    },
]

# -------------------------------------------------------------------
# I18N / TZ
# -------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Dar_es_Salaam"
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------
# Static & Media
# -------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django 4.2+ preferred storages config (WhiteNoise)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -------------------------------------------------------------------
# DRF / JWT / Schema
# -------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "content.permissions.AdminOrReadOnly",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": config("PAGE_SIZE", default=20, cast=int),
    # OpenAPI via drf-spectacular
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# Renderers: weka Browsable API wakati wa dev tu
if DEBUG:
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ]
else:
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
        "rest_framework.renderers.JSONRenderer",
    ]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=config("JWT_ACCESS_MIN", default=30, cast=int)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("JWT_REFRESH_DAYS", default=7, cast=int)
    ),
}

# ======== Mipangilio ya drf-spectacular (OpenAPI) ========
SPECTACULAR_SETTINGS = {
    "TITLE": "GOD CARES 365 API",
    "DESCRIPTION": (
        "DRF schema for Content, Discipleship, Notifications, "
        "Progress, Core, Shop, Mentorship"
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    # "SCHEMA_PATH_PREFIX": r"/api/v1",  # optional
}

# -------------------------------------------------------------------
# CORS / CSRF
# -------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = config(
    "CORS_ALLOW_ALL_ORIGINS", default=DEBUG, cast=bool
)

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default=(
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "http://localhost:5173,"
        "http://127.0.0.1:5173"
    ),
    cast=Csv(),
)

CORS_ALLOW_CREDENTIALS = True

# -------------------------------------------------------------------
# Security (prod tu)
# -------------------------------------------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# -------------------------------------------------------------------
# Auth redirects
# -------------------------------------------------------------------
LOGOUT_REDIRECT_URL = config("LOGOUT_REDIRECT_URL", default="home")
LOGIN_REDIRECT_URL = config("LOGIN_REDIRECT_URL", default="home")

# -------------------------------------------------------------------
# Email (Dev: Console by default; override na env kwa SMTP)
# -------------------------------------------------------------------
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)

if EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend":
    EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
    EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
    EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
    EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
    DEFAULT_FROM_EMAIL = config(
        "DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER or "no-reply@example.com"
    )
    SERVER_EMAIL = EMAIL_HOST_USER

# Token ya password reset
PASSWORD_RESET_TIMEOUT = config(
    "PASSWORD_RESET_TIMEOUT", default=60 * 30, cast=int
)

# (Hiari) sera zako
STRICT_EMAIL_VALIDATION = config(
    "STRICT_EMAIL_VALIDATION", default=True, cast=bool
)
EMAIL_VALIDATION_TIMEOUT = config(
    "EMAIL_VALIDATION_TIMEOUT", default=3, cast=int
)
RESET_REQUIRE_VERIFIED_EMAIL = config(
    "RESET_REQUIRE_VERIFIED_EMAIL", default=True, cast=bool
)

# -------------------------------------------------------------------
# Project-specific constants
# -------------------------------------------------------------------
SITE_NAME = config("SITE_NAME", default="GOD CARES 365")
SITE_FROM_NAME = config("SITE_FROM_NAME", default="GOD CARES 365")
DEFAULT_START_COURSE = config(
    "DEFAULT_START_COURSE",
    default="god-cares-365-foundations",
)

REFERRAL_ACTIVATION_POLICY = config(
    "REFERRAL_ACTIVATION_POLICY",
    default="HYBRID",  # MANUAL | AUTO_EMAIL | AUTO_EMAIL_AND_LEVEL1 | HYBRID
)
REFERRAL_LEVEL1_CODES = config(
    "REFERRAL_LEVEL1_CODES",
    default="level-1,discovery-1",
    cast=Csv(),
)
MENTORSHIP_SIGNUP_URL_NAME = config(
    "MENTORSHIP_SIGNUP_URL_NAME", default="content:signup"
)

# -------------------------------------------------------------------
# Logging (Dev-friendly)
# -------------------------------------------------------------------
LOG_LEVEL = "DEBUG" if DEBUG else "INFO"
LOG_DIR = BASE_DIR / "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name}: {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": LOG_LEVEL,
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "django.log",
            "formatter": "verbose",
            "level": LOG_LEVEL,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": LOG_LEVEL,
    },
}

# -------------------------------------------------------------------
# Dev niceties
# -------------------------------------------------------------------
APPEND_SLASH = True

# Hakikisha media dir ipo
os.makedirs(MEDIA_ROOT, exist_ok=True)
