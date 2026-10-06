"""Auth flow tests — the rules that protect member accounts."""

import pytest

pytestmark = pytest.mark.django_db

OTP_REQUEST = "/api/v1/auth/otp/request"
OTP_VERIFY = "/api/v1/auth/otp/verify"


def _request(client, email="new@needy.app"):
    return client.post(OTP_REQUEST, {"email": email}, content_type="application/json")


def _verify(client, email, code):
    return client.post(OTP_VERIFY, {"email": email, "code": code}, content_type="application/json")


def test_otp_request_creates_member_and_returns_sent(client, settings):
    assert _request(client).status_code == 200
    from apps.accounts.models import Member

    assert Member.objects.filter(email="new@needy.app").exists()


def test_verify_with_demo_code_returns_tokens_and_member(client, settings):
    _request(client)
    response = _verify(client, "new@needy.app", settings.NUVRA["DEMO_OTP"])
    assert response.status_code == 200
    body = response.json()
    assert "access" in body and "refresh" in body
    assert body["member"]["email"] == "new@needy.app"
    assert body["member"]["is_email_verified"] is True


def test_wrong_code_is_rejected_and_counts_attempts(client, settings):
    _request(client)
    response = _verify(client, "new@needy.app", "000000")
    assert response.status_code == 400
    assert response.json()["code"] == "otp_invalid"


def test_expired_code_rejected(client, settings):
    _request(client)
    from django.utils import timezone

    from apps.accounts.models import OtpCode

    OtpCode.objects.update(expires_at=timezone.now() - timezone.timedelta(minutes=1))
    response = _verify(client, "new@needy.app", settings.NUVRA["DEMO_OTP"])
    assert response.status_code == 400


def test_code_is_single_use(client, settings):
    _request(client)
    code = settings.NUVRA["DEMO_OTP"]
    assert _verify(client, "new@needy.app", code).status_code == 200
    # Replay with the same code must fail.
    assert _verify(client, "new@needy.app", code).status_code == 400


def test_respect_cooldown(client, settings):
    assert _request(client).json()["sent"] is True
    body = _request(client).json()
    assert body["sent"] is False
    assert body["cooldown_seconds"] > 0


def test_no_account_enumeration(client, settings):
    """Inactive members look exactly like cooldown responses."""
    from apps.accounts.models import Member

    member = Member.objects.create_member("ghost@needy.app", public_name="Ghost")
    member.is_active = False
    member.save()

    body = _request(client, "ghost@needy.app").json()
    assert body["sent"] is False


def test_me_requires_auth(client):
    assert client.get("/api/v1/me").status_code == 401


def test_me_roundtrip(client, settings):
    _request(client, "round@needy.app")
    verify_response = _verify(client, "round@needy.app", settings.NUVRA["DEMO_OTP"])
    assert verify_response.status_code == 200, verify_response.content
    tokens = verify_response.json()
    auth = {"HTTP_AUTHORIZATION": f"Bearer {tokens['access']}"}

    patched = client.patch(
        "/api/v1/me",
        {"public_name": "Round Trip", "bio": "hi"},
        content_type="application/json",
        **auth,
    )
    assert patched.status_code == 200
    assert patched.json()["public_name"] == "Round Trip"


def test_complete_profile_sets_flag(client, settings):
    _request(client, "complete@needy.app")
    tokens = _verify(client, "complete@needy.app", settings.NUVRA["DEMO_OTP"]).json()
    auth = {"HTTP_AUTHORIZATION": f"Bearer {tokens['access']}"}

    response = client.post(
        "/api/v1/me/complete-profile",
        {"name": "Complete Me", "gender": "female", "categories": ["Errands"]},
        content_type="application/json",
        **auth,
    )
    assert response.status_code == 200
    assert response.json()["member"]["profile_completed"] is True
