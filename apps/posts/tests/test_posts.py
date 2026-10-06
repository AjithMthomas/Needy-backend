"""Posts business-rule tests — the safety rules that must never drift."""

import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Member
from apps.posts.models import Application, Task

pytestmark = pytest.mark.django_db


def auth_for(member):
    return {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(member).access_token!s}"}


@pytest.fixture
def creator():
    return Member.objects.create_member(
        "creator@test.dev",
        public_name="Creator",
        gender=Member.Gender.FEMALE,
    )


@pytest.fixture
def helper():
    return Member.objects.create_member(
        "helper@test.dev",
        public_name="Helper",
        gender=Member.Gender.MALE,
    )


@pytest.fixture
def published_task(creator):
    return Task.objects.create(
        creator=creator,
        type=Task.PostType.TASK,
        kind=Task.PostKind.REGULAR,
        title="Help me move a sofa",
        description="Two flights of stairs.",
        category="Errands",
        scheduled_at="2026-10-05T10:00:00Z",
        duration_minutes=60,
        area="Madiwala",
        exchange=Task.ExchangeMode.PAID,
        reward_amount=200,
        capacity=1,
        status=Task.TaskStatus.PUBLISHED,
    )


def _apply(client, member, task):
    return client.post(
        f"/api/v1/posts/{task.id}/apply",
        {"intro_message": "I can help!"},
        content_type="application/json",
        **auth_for(member),
    )


def test_apply_happy_path(client, creator, helper, published_task):
    response = _apply(client, helper, published_task)
    assert response.status_code == 201
    published_task.refresh_from_db()
    assert published_task.applicant_count == 1
    # Chat room + creator greeting (mock parity)
    room = published_task.applications.first().chat_room
    assert room.messages.count() == 1


def test_gender_restriction_blocks_apply(client, creator, helper, published_task):
    """Girls-only posts reject male applicants at the API layer."""
    published_task.gender_preference = Task.GenderPreference.FEMALE_ONLY
    published_task.save()

    response = _apply(client, helper, published_task)
    assert response.status_code == 403
    assert response.json()["code"] == "gender_restricted"


def test_double_apply_rejected(client, creator, helper, published_task):
    assert _apply(client, helper, published_task).status_code == 201
    assert _apply(client, helper, published_task).status_code == 400


def test_own_post_apply_rejected(client, creator, published_task):
    assert _apply(client, creator, published_task).status_code == 400


def test_capacity_enforced(client, creator, helper, published_task):
    second = Member.objects.create_member("second@test.dev", public_name="Second")
    assert _apply(client, helper, published_task).status_code == 201

    application = Application.objects.get(task=published_task, member=helper)
    client.post(
        f"/api/v1/applications/{application.id}/select",
        content_type="application/json",
        **auth_for(creator),
    )
    # Post is confirmed + full; a new applicant is refused.
    published_task.refresh_from_db()
    assert published_task.status == Task.TaskStatus.CONFIRMED
    assert _apply(client, second, published_task).status_code == 400


def test_select_declines_others(client, creator, helper, published_task):
    other = Member.objects.create_member("other@test.dev", public_name="Other")
    _apply(client, helper, published_task)
    _apply(client, other, published_task)

    for member in (helper, other):
        application = Application.objects.get(task=published_task, member=member)
        client.post(
            f"/api/v1/applications/{application.id}/select",
            content_type="application/json",
            **auth_for(creator),
        )
        break

    helper_app = Application.objects.get(task=published_task, member=helper)
    other_app = Application.objects.get(task=published_task, member=other)
    assert helper_app.status == Application.ApplicationStatus.SELECTED
    assert other_app.status == Application.ApplicationStatus.DECLINED


def test_moderation_blocks_vulgar_post(client, creator):
    response = client.post(
        "/api/v1/posts",
        {
            "type": "task",
            "kind": "regular",
            "title": "S3xy massage service",
            "description": "full body available",
            "category": "Errands",
            "scheduled_at": "2026-10-05T10:00:00Z",
            "duration_minutes": 30,
            "area": "Madiwala",
            "exchange": "paid",
            "reward_amount": 100,
            "capacity": 1,
            "gender_preference": "anyone",
        },
        content_type="application/json",
        **auth_for(creator),
    )
    assert response.status_code == 400
    assert Task.objects.filter(creator=creator).count() == 0


def test_lifecycle_and_karma_on_completion(client, creator, helper, published_task):
    auth_creator = auth_for(creator)
    _apply(client, helper, published_task)
    application = Application.objects.get(task=published_task, member=helper)
    client.post(
        f"/api/v1/applications/{application.id}/select",
        content_type="application/json",
        **auth_creator,
    )

    karma_before = helper.karma
    client.post(
        f"/api/v1/posts/{published_task.id}/start", content_type="application/json", **auth_creator
    )
    client.post(
        f"/api/v1/posts/{published_task.id}/complete",
        content_type="application/json",
        **auth_creator,
    )

    published_task.refresh_from_db()
    helper.refresh_from_db()
    assert published_task.status == Task.TaskStatus.COMPLETED
    assert helper.completed_count == 1
    assert helper.karma > karma_before  # time-credit reward granted


def test_only_creator_can_cancel(client, creator, helper, published_task):
    response = client.post(
        f"/api/v1/posts/{published_task.id}/cancel",
        content_type="application/json",
        **auth_for(helper),
    )
    assert response.status_code == 400


def test_report_auto_quarantines(client, creator, helper, published_task):
    response = client.post(
        "/api/v1/reports",
        {"task_id": str(published_task.id), "reason": "spam", "details": "junk"},
        content_type="application/json",
        **auth_for(helper),
    )
    assert response.status_code == 201
    published_task.refresh_from_db()
    assert published_task.quarantined is True

    # Quarantined posts vanish from the feed.
    feed = client.get("/api/v1/posts", **auth_for(helper)).json()
    ids = [row["id"] for row in feed["results"]]
    assert str(published_task.id) not in ids


def test_saved_and_repost_toggles(client, helper, published_task):
    auth = auth_for(helper)
    url = f"/api/v1/posts/{published_task.id}/save"
    assert client.post(url, content_type="application/json", **auth).json() == {"saved": True}
    assert client.post(url, content_type="application/json", **auth).json() == {"saved": False}
