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
