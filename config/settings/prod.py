"""Production settings — Postgres via DATABASE_URL, hardened defaults."""

from config.settings.base import *
from config.settings.base import NUVRA

DEBUG = False

SECRET_KEY = nuvra_env("SECRET_KEY", default="")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY must be set in production. "
        'Generate one: python -c "import secrets; print(secrets.token_urlsafe(50))"'
    )

# Fail closed: an empty allow-list used to fall back to ['*'], which let any
# Host header through. Set ALLOWED_HOSTS to your deployed host(s).
ALLOWED_HOSTS = nuvra_env("ALLOWED_HOSTS", default="", cast=Cast.csv)
if not ALLOWED_HOSTS:
    raise RuntimeError(
        "ALLOWED_HOSTS must be set in production "
        '(comma-separated, e.g. "needy-api-xxxx.run.app,api.needy.app").'
    )

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = nuvra_env("SECURE_SSL_REDIRECT", default="1", cast=Cast.bool)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
CSRF_TRUSTED_ORIGINS = nuvra_env("CSRF_TRUSTED_ORIGINS", default="", cast=Cast.csv)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

_database_url = nuvra_env("DATABASE_URL", default="")
if _database_url:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.parse(
            _database_url, conn_max_age=600, ssl_require=True
        ),
    }
else:
    raise RuntimeError(
        "DATABASE_URL must be set in production (Neon/Supabase/Render Postgres)."
    )

NUVRA = {**NUVRA, "DEMO_MODE": False}

CORS_ALLOWED_ORIGINS = nuvra_env(
    "CORS_ALLOWED_ORIGINS",
    default="",
    cast=Cast.csv,
)

# Crash reporting — optional: only activates when SENTRY_DSN is provided.
SENTRY_DSN = nuvra_env("SENTRY_DSN", default="")
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=float(nuvra_env("SENTRY_TRACES_RATE", default="0.05")),
            send_default_pii=False,
            environment=nuvra_env("SENTRY_ENVIRONMENT", default="production"),
        )
    except ImportError:  # pragma: no cover - optional dependency
        import warnings

        warnings.warn("SENTRY_DSN is set but sentry-sdk is not installed.", stacklevel=1)

# Quiet, structured-enough logging for a free-tier container.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
