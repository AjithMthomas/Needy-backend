"""/config tests — the launch controls the app reads on cold start.

The app has no kill switch unless this endpoint tells the truth, so these
assert the contract the Flutter client depends on.
"""

import pytest
from django.conf import settings
from django.test import override_settings

pytestmark = pytest.mark.django_db


def test_config_is_public_and_exposes_launch_controls(client):
    response = client.get("/api/v1/config")
    assert response.status_code == 200
    body = response.json()

    # Maintenance gate
    assert body["maintenance"]["active"] is False
    assert body["maintenance_mode"] is False

    # Force-update gate (per-platform build numbers, not version strings)
    assert body["min_build"]["ios"] >= 1
    assert body["min_build"]["android"] >= 1
    assert body["store_urls"]["ios"].startswith("https://")
    assert body["store_urls"]["android"].startswith("https://")

    # Money features stay dark for the pilot
    assert body["feature_flags"]["payments"] is False
    assert body["feature_flags"]["auctions"] is False


def test_maintenance_mode_can_be_switched_on_without_a_release(client):
    flipped = {
        **settings.NUVRA,
        "MAINTENANCE_MODE": True,
        "MAINTENANCE_MESSAGE": "Back at 6 PM.",
        "APP_MIN_ANDROID_BUILD": 7,
    }
    with override_settings(NUVRA=flipped):
        body = client.get("/api/v1/config").json()

    assert body["maintenance"] == {"active": True, "message": "Back at 6 PM."}
    assert body["maintenance_mode"] is True
    assert body["min_build"]["android"] == 7
