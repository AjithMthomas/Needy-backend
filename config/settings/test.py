"""Test settings — in-memory DB, deterministic OTP, no throttling."""

from datetime import timedelta

from config.settings.base import *
from config.settings.base import NUVRA

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

NUVRA = {**NUVRA, "DEMO_MODE": True}

# Deterministic, fast, and no rate limits so tests don't flap.
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": (),
    "DEFAULT_THROTTLE_RATES": {},
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Shorten token lifetimes so expiry paths are testable quickly.
SIMPLE_JWT = {
    **SIMPLE_JWT,
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
}
