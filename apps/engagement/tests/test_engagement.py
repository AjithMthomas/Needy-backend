"""Engagement rule tests — karma economy integrity + daily caps."""

import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Member
from apps.core.exceptions import KarmaInsufficientError
from apps.engagement import services
from apps.engagement.models import BoardIdea, PartnerPerk, PlayChallenge

pytestmark = pytest.mark.django_db


def auth_for(member):
    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(member).access_token!s}"}


@pytest.fixture
def member():
    return Member.objects.create_member("wallet@test.dev", public_name="Wallet", karma=500)


def test_karma_grant_and_spend(member):
    assert services.grant_karma(member, 50, "test grant") == 550
    assert services.spend_karma(member, 200, "test spend") == 350
    from apps.engagement.models import KarmaLedger

    assert KarmaLedger.objects.filter(member=member).count() == 2


def test_karma_cannot_go_negative(member):
    with pytest.raises(KarmaInsufficientError):
        services.spend_karma(member, 10_000, "too much")


def test_perk_claim_once_and_receipt(client, member):
    perk = PartnerPerk.objects.create(
        merchant="Test Cafe",
        title="Free chai",
        cost_karma=100,
        area="Madiwala",
        valid_hours=24,
    )
    auth = auth_for(member)
    url = f"/api/v1/perks/{perk.id}/claim"

    first = client.post(url, content_type="application/json", **auth)
    assert first.status_code == 201
    assert first.json()["code"].startswith("NEEDY-")

    second = client.post(url, content_type="application/json", **auth)
    assert second.status_code == 400  # one voucher per member


def test_perk_claim_insufficient_karma(client):
    broke = Member.objects.create_member("broke@test.dev", public_name="Broke", karma=10)
    perk = PartnerPerk.objects.create(
        merchant="Test Cafe",
        title="Free chai",
        cost_karma=100,
        area="Madiwala",
        valid_hours=24,
    )
    response = client.post(
        f"/api/v1/perks/{perk.id}/claim",
        content_type="application/json",
        **auth_for(broke),
    )
    assert response.status_code == 402
    assert response.json()["code"] == "karma_insufficient"


def test_challenge_daily_cap(client, member):
    challenge = PlayChallenge.objects.create(
        code="testgame",
        title="Test Game",
        target=10,
        reward_karma=60,
    )
    auth = auth_for(member)

    win = client.post(
        f"/api/v1/challenges/{challenge.id}/play",
        {"score": 30},
        content_type="application/json",
        **auth,
    )
    assert win.status_code == 200
    assert win.json() == {"score": 30, "won": True, "reward": 60}

    replay = client.post(
        f"/api/v1/challenges/{challenge.id}/play",
        {"score": 99},
        content_type="application/json",
        **auth,
    )
    assert replay.status_code == 400  # one play per day, server-enforced


def test_idea_vote_toggle(client, member):
    idea = BoardIdea.objects.create(
        author=member,
        title="Test idea",
        details="",
        tag="Feature",
        upvotes=1,
    )
    other = Member.objects.create_member("voter@test.dev", public_name="Voter")
    auth = auth_for(other)

    first = client.post(
        f"/api/v1/community/ideas/{idea.id}/vote", content_type="application/json", **auth
    )
    assert first.json() == {"voted": True, "upvotes": 2}
    second = client.post(
        f"/api/v1/community/ideas/{idea.id}/vote", content_type="application/json", **auth
    )
    assert second.json() == {"voted": False, "upvotes": 1}


def test_idea_submission_awards_karma(client, member):
    response = client.post(
        "/api/v1/community/ideas/create",
        {"title": "A lovely idea", "details": "detail", "tag": "Feature"},
        content_type="application/json",
        **auth_for(member),
    )
    assert response.status_code == 201
    member.refresh_from_db()
    assert member.karma == 500 + 15  # IDEA_PUBLISH_KARMA default
