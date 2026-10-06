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

ALLOWED_HOSTS = nuvra_env(
    "ALLOWED_HOSTS",
    default="",
    cast=Cast.csv,
) or ["*"]  # tighten on Render: set ALLOWED_HOSTS to your .onrender.com host

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = nuvra_env("SECURE_SSL_REDIRECT", default="0", cast=Cast.bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

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

# Quiet, structured-enough logging for a free-tier container.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
