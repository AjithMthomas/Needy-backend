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


def test_capacity_above_one_does_not_close_post_early(client, creator, published_task):
    """A team/trip post with capacity 3 must survive the first choice.

    Regression: selecting one applicant used to decline everyone else and set
    the post to CONFIRMED, so any post with capacity > 1 could never fill.
    """
    published_task.capacity = 3
    published_task.save(update_fields=["capacity"])
    people = [
        Member.objects.create_member(f"member{i}@test.dev", public_name=f"Member {i}")
        for i in range(3)
    ]
    for person in people:
        assert _apply(client, person, published_task).status_code == 201

    apps = [Application.objects.get(task=published_task, member=p) for p in people]

    for app in apps[:2]:
        response = client.post(
            f"/api/v1/applications/{app.id}/select",
            content_type="application/json",
            **auth_for(creator),
        )
        assert response.status_code == 200
        published_task.refresh_from_db()
        # Still open, and the third applicant is still in the running.
        assert published_task.status == Task.TaskStatus.PUBLISHED
        assert (
            Application.objects.get(pk=apps[2].pk).status
            != Application.ApplicationStatus.DECLINED
        )

    # Third selection fills the post.
    assert client.post(
        f"/api/v1/applications/{apps[2].id}/select",
        content_type="application/json",
        **auth_for(creator),
    ).status_code == 200
    published_task.refresh_from_db()
    assert published_task.status == Task.TaskStatus.CONFIRMED
    assert (
        Application.objects.filter(
            task=published_task, status=Application.ApplicationStatus.SELECTED
        ).count()
        == 3
    )


def test_feed_accepts_comma_joined_filters(client, creator, helper):
    """The app sends multi-select filters comma-joined (?types=task,offer).

    Regression: getlist() returned the whole string as a single value, so any
    feed with two or more filters active came back empty.
    """
    base = dict(
        creator=creator,
        kind=Task.PostKind.REGULAR,
        category="Errands",
        scheduled_at="2026-10-05T10:00:00Z",
        duration_minutes=60,
        area="Madiwala",
        status=Task.TaskStatus.PUBLISHED,
    )
    Task.objects.create(
        type=Task.PostType.TASK,
        title="Paid task",
        description="Move a sofa.",
        exchange=Task.ExchangeMode.PAID,
        reward_amount=200,
        capacity=1,
        **base,
    )
    Task.objects.create(
        type=Task.PostType.OFFER,
        title="Free offer",
        description="Spare textbooks.",
        exchange=Task.ExchangeMode.FREE,
        reward_amount=0,
        capacity=1,
        **base,
    )

    combined = client.get(
        "/api/v1/posts?types=task,offer&exchanges=paid,free&source=city",
        **auth_for(helper),
    )
    assert combined.status_code == 200
    assert len(combined.json()["results"]) == 2

    # Repeated-key form keeps working too.
    repeated = client.get(
        "/api/v1/posts?types=task&types=offer&source=city",
        **auth_for(helper),
    )
    assert len(repeated.json()["results"]) == 2

    # And a single filter still narrows correctly.
    narrowed = client.get("/api/v1/posts?types=task&source=city", **auth_for(helper))
    assert len(narrowed.json()["results"]) == 1


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


def _report(client, member, task, reason="spam"):
    return client.post(
        "/api/v1/reports",
        {"task_id": str(task.id), "reason": reason, "details": "junk"},
        content_type="application/json",
        **auth_for(member),
    )


def test_one_report_does_not_quarantine(client, helper, published_task):
    """Corroboration is required: a single member must not be able to
    censor any post they dislike."""
    response = _report(client, helper, published_task)
    assert response.status_code == 201
    assert response.json()["quarantined"] is False
    published_task.refresh_from_db()
    assert published_task.quarantined is False

    # Still in the feed.
    feed = client.get("/api/v1/posts", **auth_for(helper)).json()
    assert str(published_task.id) in [row["id"] for row in feed["results"]]

    # The same member cannot pile on to push it over the threshold.
    assert _report(client, helper, published_task).status_code == 400


def test_reports_quarantine_after_threshold(client, helper, published_task):
    reporters = [helper] + [
        Member.objects.create_member(f"reporter{i}@test.dev", public_name=f"R{i}")
        for i in range(2)
    ]
    results = [_report(client, member, published_task) for member in reporters]
    assert [r.status_code for r in results] == [201, 201, 201]
    assert [r.json()["quarantined"] for r in results] == [False, False, True]

    published_task.refresh_from_db()
    assert published_task.quarantined is True

    # Quarantined posts vanish from the feed…
    feed = client.get("/api/v1/posts", **auth_for(helper)).json()
    assert str(published_task.id) not in [row["id"] for row in feed["results"]]
    # …and from the detail endpoint for everyone but the creator.
    detail = client.get(f"/api/v1/posts/{published_task.id}", **auth_for(helper))
    assert detail.status_code == 404


def test_safety_report_quarantines_immediately(client, helper, published_task):
    response = _report(client, helper, published_task, reason="safety")
    assert response.status_code == 201
    published_task.refresh_from_db()
    assert published_task.quarantined is True


def test_creator_cannot_report_own_post(client, creator, published_task):
    assert _report(client, creator, published_task).status_code == 400


def test_feed_query_count_does_not_scale_with_rows(
    client, creator, helper, published_task, django_assert_max_num_queries
):
    """Guard against the per-card N+1 (saved/reposted/applied/badges)."""
    extra = [
        Task.objects.create(
            creator=creator,
            type=Task.PostType.TASK,
            kind=Task.PostKind.REGULAR,
            title=f"Post {i}",
            description="desc",
            category="Errands",
            scheduled_at="2026-10-05T10:00:00Z",
            duration_minutes=60,
            area="Madiwala",
            exchange=Task.ExchangeMode.PAID,
            reward_amount=100,
            capacity=1,
            status=Task.TaskStatus.PUBLISHED,
        )
        for i in range(10)
    ]
    assert len(extra) == 10
    auth = auth_for(helper)  # build the token outside the measured block

    # 11 posts in the page; a per-row regression would need 30+ queries here.
    with django_assert_max_num_queries(10):
        response = client.get(
            "/api/v1/posts?source=city&page_size=20",
            **auth,
        )
    assert response.status_code == 200
    assert len(response.json()["results"]) == 11


def test_block_hides_posts_and_blocks_applying(client, creator, helper, published_task):
    """The Block model was documented as enforced but nothing read it."""
    response = client.post(
        "/api/v1/block/block",
        {"member_id": str(creator.id)},
        content_type="application/json",
        **auth_for(helper),
    )
    assert response.status_code == 200

    feed = client.get("/api/v1/posts", **auth_for(helper)).json()
    assert str(published_task.id) not in [row["id"] for row in feed["results"]]
    assert (
        client.get(f"/api/v1/posts/{published_task.id}", **auth_for(helper)).status_code
        == 404
    )
    assert _apply(client, helper, published_task).status_code == 400

    # Unblocking restores visibility.
    client.post(
        "/api/v1/block/unblock",
        {"member_id": str(creator.id)},
        content_type="application/json",
        **auth_for(helper),
    )
    feed = client.get("/api/v1/posts", **auth_for(helper)).json()
    assert str(published_task.id) in [row["id"] for row in feed["results"]]


def test_rating_requires_completed_task_participation_and_uniqueness(
    client, creator, helper, published_task
):
    _apply(client, helper, published_task)
    application = Application.objects.get(task=published_task, member=helper)
    client.post(
        f"/api/v1/applications/{application.id}/select",
        content_type="application/json",
        **auth_for(creator),
    )
    rate_url = f"/api/v1/posts/{published_task.id}/rate"

    # Not completed yet.
    assert (
        client.post(
            rate_url,
            {"stars": 5},
            content_type="application/json",
            **auth_for(creator),
        ).status_code
        == 400
    )

    published_task.status = Task.TaskStatus.COMPLETED
    published_task.save(update_fields=["status"])

    # A stranger who never joined cannot rate.
    stranger = Member.objects.create_member("stranger@test.dev", public_name="Stranger")
    assert (
        client.post(
            rate_url,
            {"stars": 1},
            content_type="application/json",
            **auth_for(stranger),
        ).status_code
        == 400
    )

    # The creator may rate once.
    assert (
        client.post(
            rate_url,
            {"stars": 5, "note": "Great help"},
            content_type="application/json",
            **auth_for(creator),
        ).status_code
        == 200
    )
    assert (
        client.post(
            rate_url,
            {"stars": 1},
            content_type="application/json",
            **auth_for(creator),
        ).status_code
        == 400
    )


def test_saved_and_repost_toggles(client, helper, published_task):
    auth = auth_for(helper)
    url = f"/api/v1/posts/{published_task.id}/save"
    assert client.post(url, content_type="application/json", **auth).json() == {"saved": True}
    assert client.post(url, content_type="application/json", **auth).json() == {"saved": False}
