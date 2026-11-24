"""Notification and device token tests."""

import pytest
from django.core.management import call_command

from apps.accounts.models import Member
from apps.notifications import services
from apps.notifications.models import DeviceToken, Notification

pytestmark = pytest.mark.django_db


@pytest.fixture
def member():
    return Member.objects.create(
        email="device.test@needy.app",
        public_name="Device Tester",
        is_email_verified=True,
    )


@pytest.fixture
def auth_client(client, member):
    from rest_framework_simplejwt.tokens import RefreshToken

    token = str(RefreshToken.for_user(member).access_token)
    client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return client


def test_device_register_and_unregister(auth_client, member):
    # 1. Register device
    res = auth_client.post(
        "/api/v1/devices/register",
        {
            "token": "fcm_test_token_123",
            "platform": "android",
            "device_name": "Pixel 8 Pro",
        },
        content_type="application/json",
    )
    assert res.status_code == 200
    assert res.json()["registered"] is True

    device = DeviceToken.objects.get(token="fcm_test_token_123")
    assert device.member == member
    assert device.platform == "android"
    assert device.is_active is True

    # 2. Register same token again (update)
    res = auth_client.post(
        "/api/v1/devices/register",
        {
            "token": "fcm_test_token_123",
            "platform": "ios",
            "device_name": "iPhone 15",
        },
        content_type="application/json",
    )
    assert res.status_code == 200
    device.refresh_from_db()
    assert device.platform == "ios"
    assert device.device_name == "iPhone 15"

    # 3. Unregister device
    res = auth_client.post(
        "/api/v1/devices/unregister",
        {"token": "fcm_test_token_123"},
        content_type="application/json",
    )
    assert res.status_code == 200
    device.refresh_from_db()
    assert device.is_active is False


def test_notify_service_creates_notification_and_dispatches_push(member):
    # Register an active device
    services.register_device(member, "token_abc", platform="android")

    # Call notify
    notif = services.notify(
        recipient=member,
        title="Test Notification",
        body="This is a test notification body",
        target="task:123",
    )
    assert notif.recipient == member
    assert notif.title == "Test Notification"
    assert notif.read is False
    assert services.unread_count(member) == 1

    services.mark_all_read(member)
    assert services.unread_count(member) == 0


def test_dispatch_engagement_command(member):
    services.register_device(member, "token_xyz", platform="android")

    # Run dispatch
    call_command("dispatch_engagement")

    # Member should have received an engagement notification
    assert Notification.objects.filter(
        recipient=member,
        target__startswith="reengagement:",
    ).exists()

    count_before = Notification.objects.filter(recipient=member).count()

    # Second run should skip because of rate limiting
    call_command("dispatch_engagement")
    count_after = Notification.objects.filter(recipient=member).count()
    assert count_after == count_before
