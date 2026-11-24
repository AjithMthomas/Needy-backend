"""Base settings shared by dev/test/prod.

Layering: base.py (shared) -> {dev,test,prod}.py (environment-specific).
Env access goes through nuvra_env() so every knob has a sane default and
nothing crashes when .env is absent (e.g. a fresh free-tier deploy).
"""

from datetime import timedelta
from pathlib import Path

from config.env import Cast, needy_env, nuvra_env

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
SECRET_KEY = nuvra_env("SECRET_KEY", default="dev-only-insecure-key")
DEBUG = False
ALLOWED_HOSTS = nuvra_env(
    "ALLOWED_HOSTS",
    default="127.0.0.1,localhost,10.0.2.2",
    cast=Cast.csv,
)

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "whitenoise.runserver_nostatic",
    # Local
    "apps.core",
    "apps.accounts",
    "apps.posts",
    "apps.chat",
    "apps.auctions",
    "apps.engagement",
    "apps.moderation",
    "apps.notifications",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
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
                "django.template.context_processors.request",
                "django.template.context_processors.debug",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Database — dev/test default to SQLite; prod reads DATABASE_URL.
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    },
}

# ---------------------------------------------------------------------------
# DRF
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.NeedyPagination",
    "PAGE_SIZE": 30,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "EXCEPTION_HANDLER": "apps.core.errors.needy_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "120/min",
        "user": "600/min",
        "otp": "10/min",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ---------------------------------------------------------------------------
# i18n / static / models
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"  # display only — datetimes are stored UTC.
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# User uploads (auction product photos, later: profile/task photos).
# Local disk for the pilot — ephemeral on Render; wire S3 at the 25k
# rung of the scale ladder (STANDARDS.md §6).
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# Media storage — local disk in dev, S3-compatible (Cloudflare R2) in prod.
#
# Without this every uploaded image 404s in production: MEDIA_URL is only
# served by Django when DEBUG=True, and container disks are ephemeral.
# Setting R2_BUCKET_NAME switches storage without any code change.
# ---------------------------------------------------------------------------
R2_BUCKET_NAME = nuvra_env("R2_BUCKET_NAME", default="")
R2_PUBLIC_URL = nuvra_env("R2_PUBLIC_URL", default="").rstrip("/")

if R2_BUCKET_NAME:
    _r2_options = {
        "bucket_name": R2_BUCKET_NAME,
        "access_key": nuvra_env("R2_ACCESS_KEY_ID", default=""),
        "secret_key": nuvra_env("R2_SECRET_ACCESS_KEY", default=""),
        "endpoint_url": nuvra_env("R2_ENDPOINT_URL", default="") or None,
        "region_name": nuvra_env("R2_REGION", default="auto"),
        # R2 does not support S3 ACLs, and objects stay private: serve
        # presigned URLs unless a public bucket domain is configured.
        "default_acl": None,
        "querystring_auth": not R2_PUBLIC_URL,
        "file_overwrite": False,
    }
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage", "OPTIONS": _r2_options},
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        },
    }
    if R2_PUBLIC_URL:
        MEDIA_URL = f"{R2_PUBLIC_URL}/"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.Member"

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = nuvra_env(
    "CORS_ALLOWED_ORIGINS",
    default="",
    cast=Cast.csv,
) or [
    "http://localhost:8090",
    "http://127.0.0.1:8090",
    "http://localhost:3000",
]

# ---------------------------------------------------------------------------
# App tunables — every value env-overridable.
# ---------------------------------------------------------------------------
NEEDY = {
    "OTP_VALIDITY_MINUTES": int(needy_env("OTP_VALIDITY_MINUTES", default="10")),
    "OTP_RESEND_COOLDOWN_SECONDS": int(
        needy_env("OTP_RESEND_COOLDOWN_SECONDS", default="60")
    ),
    "OTP_MAX_ATTEMPTS": int(needy_env("OTP_MAX_ATTEMPTS", default="5")),
    "SERVICE_FEE_PERCENT": float(needy_env("SERVICE_FEE_PERCENT", default="5.0")),
    "PLAY_DAILY_CONSOLATION_KARMA": int(
        needy_env("PLAY_DAILY_CONSOLATION_KARMA", default="10")
    ),
    "IDEA_PUBLISH_KARMA": int(needy_env("IDEA_PUBLISH_KARMA", default="15")),
    # Distinct reporters needed before a post is hidden. One report must not be
    # enough, or a single member can censor the whole marketplace.
    "REPORT_QUARANTINE_THRESHOLD": int(
        needy_env("REPORT_QUARANTINE_THRESHOLD", default="3")
    ),
    # How many ideas per member per day actually earn credits.
    "IDEA_DAILY_KARMA_LIMIT": int(needy_env("IDEA_DAILY_KARMA_LIMIT", default="1")),
    # ── Launch controls (read by /config, no store release needed) ──
    "MAINTENANCE_MODE": needy_env("MAINTENANCE_MODE", default="0") == "1",
    "MAINTENANCE_MESSAGE": needy_env(
        "MAINTENANCE_MESSAGE",
        default="Needy is briefly off for maintenance. Please try again in a few minutes.",
    ),
    "APP_MIN_IOS_BUILD": int(needy_env("APP_MIN_IOS_BUILD", default="1")),
    "APP_MIN_ANDROID_BUILD": int(needy_env("APP_MIN_ANDROID_BUILD", default="1")),
    "APP_STORE_IOS_URL": needy_env(
        "APP_STORE_IOS_URL", default="https://apps.apple.com/app/id0000000000"
    ),
    "APP_STORE_ANDROID_URL": needy_env(
        "APP_STORE_ANDROID_URL",
        default="https://play.google.com/store/apps/details?id=app.needy.mobile",
    ),
    # Money features are off for the pilot until payments/compliance land.
    "FEATURE_FLAGS": {
        "auctions": needy_env("FEATURE_AUCTIONS", default="0") == "1",
        "payments": needy_env("FEATURE_PAYMENTS", default="0") == "1",
        "gigs": needy_env("FEATURE_GIGS", default="1") == "1",
    },
    # Fixed code while email delivery is console-only in dev. Prod sends a
    # random 6-digit code by email; DEMO_OTP only applies when settings.DEBUG.
    "DEMO_OTP": "424242",
    "MODERATION_HARD_WORDS": [
        "escort",
        "douche",
        "nude",
        "nudes",
        "naked",
        "porn",
        "sex ",
        "sexy",
        "hookup",
        "one night",
        "weed",
        "ganja",
        "md ",
        "mdma",
        "cocaine",
        "meth",
    ],
    "MODERATION_SOFT_WORDS": [
        "massages",
        "full body",
        "private party",
        "alone at home",
        "wife not",
        "parents not",
        "cash only no questions",
    ],
}
NUVRA = NEEDY

# ---------------------------------------------------------------------------
# Email — console in dev; SMTP (e.g. Resend free tier) via env in prod.
# ---------------------------------------------------------------------------
EMAIL_BACKEND = needy_env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = needy_env("EMAIL_HOST", default="")
EMAIL_PORT = needy_env("EMAIL_PORT", default="587")
EMAIL_HOST_USER = needy_env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = needy_env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = needy_env(
    "DEFAULT_FROM_EMAIL", default="needy <noreply@needy.app>"
)

# ---------------------------------------------------------------------------
# Firebase Cloud Messaging (FCM) — Push notifications
# ---------------------------------------------------------------------------
FIREBASE_CREDENTIALS_PATH = needy_env("FIREBASE_CREDENTIALS_PATH", default="")
FIREBASE_CREDENTIALS_JSON = needy_env("FIREBASE_CREDENTIALS_JSON", default="")

