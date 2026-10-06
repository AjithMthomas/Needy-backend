"""Upload endpoint tests — auth, type, and size rules."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

pytestmark = pytest.mark.django_db

UPLOAD = "/api/v1/uploads"

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 128


def _auth(client, settings):
    client.post(
        "/api/v1/auth/otp/request",
        {"email": "up@needy.app"},
        content_type="application/json",
    )
    response = client.post(
        "/api/v1/auth/otp/verify",
        {"email": "up@needy.app", "code": settings.NUVRA["DEMO_OTP"]},
        content_type="application/json",
    )
    client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {response.json()['access']}"
    return client


def test_upload_requires_auth(client):
    response = client.post(
        UPLOAD,
        {"file": SimpleUploadedFile("x.png", PNG_BYTES)},
    )
    assert response.status_code == 401


def test_upload_png_returns_usable_url(client, settings):
    _auth(client, settings)
    response = client.post(
        UPLOAD,
        {"file": SimpleUploadedFile("photo.png", PNG_BYTES, content_type="image/png")},
    )
    assert response.status_code == 201
    url = response.json()["url"]
    assert "/media/uploads/" in url
    assert url.endswith(".png")


def test_upload_rejects_non_image(client, settings):
    _auth(client, settings)
    # Text bytes masquerading as a PNG — the declared type must not win.
    fake = SimpleUploadedFile(
        "payload.png",
        b"#!/usr/bin/env python3\nprint('nope')\n",
        content_type="image/png",
    )
    response = client.post(UPLOAD, {"file": fake})
    assert response.status_code == 400
    assert response.json()["code"] == "invalid"


def test_upload_rejects_non_webp_riff(client, settings):
    _auth(client, settings)
    fake = SimpleUploadedFile(
        "sound.webp",
        b"RIFF" + bytes(4) + b"WAVE" + bytes(16),
        content_type="image/webp",
    )
    response = client.post(UPLOAD, {"file": fake})
    assert response.status_code == 400


def test_upload_rejects_oversize(client, settings):
    _auth(client, settings)
    big = SimpleUploadedFile(
        "big.png",
        PNG_BYTES + b"0" * (6 * 1024 * 1024),
        content_type="image/png",
    )
    response = client.post(UPLOAD, {"file": big})
    assert response.status_code == 400
    assert "too large" in response.json()["detail"]
