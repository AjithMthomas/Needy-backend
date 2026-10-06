"""Development settings — SQLite, console email, verbose errors."""

from config.settings.base import *
from config.settings.base import NUVRA

DEBUG = True

ALLOWED_HOSTS = ["*"]  # LAN phone testing (serve-phone.js on :8090).

# Dev keeps the fixed demo OTP 424242; prod generates random codes.
NUVRA = {**NUVRA, "DEMO_MODE": True}

# Plain, non-compressed static storage for quicker iteration.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
