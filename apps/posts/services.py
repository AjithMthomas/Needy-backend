"""posts services — feed assembly + application & lifecycle rules.

Every rule the mock enforced client-side is enforced here, server-side,
where it cannot be bypassed: moderation screen, gender admission,
capacity, status transitions.
"""

from __future__ import annotations

from django.db import transaction
from django.db.models import F, Q

from apps.accounts.models import Member
from apps.core.exceptions import (
    BusinessRuleError,
    CapacityFullError,
    GenderRestrictedError,
)
from apps.notifications.services import notify
from apps.posts.models import Application, Task


# ---------------------------------------------------------------------------
# Feed
# ---------------------------------------------------------------------------
def feed_queryset(member: Member, *, params):
    """Assemble the Discover/Home feed. All filters are query params:
    kind, radius_km, source (nearby|city), types, exchanges, free,
    gender, category, q (text search), saved=1, mine=1."""

    qs = Task.objects.filter(
        status=Task.TaskStatus.PUBLISHED,
        quarantined=False,
    ).select_related("creator")

    kind = params.get("kind")
    if kind:
        qs = qs.filter(kind=kind)

    # Radius / source: 'city' widens to metro scale.
    source = params.get("source", "nearby")
    max_km = 25.0 if source == "city" else _float(params.get("radius_km"), 3.0)
    qs = qs.filter(distance_km__lte=max_km)

    types = params.getlist("types")
    if types:
        qs = qs.filter(type__in=types)

    exchanges = params.getlist("exchanges")
    if exchanges:
        qs = qs.filter(exchange__in=exchanges)

    if params.get("free") == "1":
        qs = qs.filter(Q(exchange__in=["free", "treat"]) | Q(exchange="paid", reward_amount=0))

    gender = params.get("gender")
    if gender:
        qs = qs.filter(gender_preference=gender)

    category = params.get("category")
    if category and category != "All":
        qs = qs.filter(category=category)

    q = params.get("q")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

    if params.get("saved") == "1":
        qs = qs.filter(saved_by__member=member)

    if params.get("mine") == "1":
        qs = Task.objects.filter(creator=member).exclude(status=Task.TaskStatus.CANCELLED)

    # Feed sort: soonest first (matches the app).
    return qs.order_by("scheduled_at")


def _float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
@transaction.atomic
def apply_to_task(task: Task, member: Member, intro: str) -> Application:
    if task.creator_id == member.id:
        raise BusinessRuleError("You can't apply to your own post.")
    if task.status != Task.TaskStatus.PUBLISHED:
        raise BusinessRuleError("This post is no longer open.")
    if Application.objects.filter(task=task, member=member).exists():
        raise BusinessRuleError("You already applied to this post.")
    if not task.admits(member.gender):
        # Safety feature — enforced here, not just in the UI.
        raise GenderRestrictedError("This post is restricted by the creator's safety preference.")
    if task.selected_count() >= task.capacity:
        raise CapacityFullError("This post is full.")

    application = Application.objects.create(
        task=task,
        member=member,
        intro_message=intro,
    )
    Task.objects.filter(pk=task.pk).update(applicant_count=F("applicant_count") + 1)

    # Chat room opens the moment an application exists (mock parity), and
    # the creator's canned greeting arrives as the first unread message.
    from apps.chat.services import get_or_create_room_for_application, send_message

    room = get_or_create_room_for_application(application)
    send_message(
        room,
        task.creator,
        "Hi! Thanks for showing interest. Tell me a bit about yourself?",
    )

    notify(
        recipient=task.creator,
        title="New application",
        body=f'{member.public_name} applied to "{task.title}".',
        target=f"task:{task.id}",
    )
    return application


@transaction.atomic
def withdraw_application(application: Application, member: Member) -> None:
    if application.member_id != member.id:
        raise BusinessRuleError("Not your application.")
    if application.status == Application.ApplicationStatus.WITHDRAWN:
        return
    application.status = Application.ApplicationStatus.WITHDRAWN
    application.save(update_fields=["status", "updated_at"])
    Task.objects.filter(pk=application.task_id, applicant_count__gt=0).update(
        applicant_count=F("applicant_count") - 1,
    )


@transaction.atomic
def select_applicant(application: Application, member: Member) -> Task:
    task = application.task
    if task.creator_id != member.id:
        raise BusinessRuleError("Only the creator can select applicants.")
    if application.status == Application.ApplicationStatus.WITHDRAWN:
        raise BusinessRuleError("That application was withdrawn.")

    application.status = Application.ApplicationStatus.SELECTED
    application.save(update_fields=["status", "updated_at"])

    # Everyone else in the room is declined (mock parity).
    (
        Application.objects.filter(task=task)
        .exclude(pk=application.pk)
        .exclude(status=Application.ApplicationStatus.WITHDRAWN)
        .update(status=Application.ApplicationStatus.DECLINED)
    )

    task.status = Task.TaskStatus.CONFIRMED
    task.save(update_fields=["status", "updated_at"])
    notify(
        recipient=application.member,
        title="You were selected!",
        body=f'Your application to "{task.title}" was accepted. Open chat to coordinate.',
        target=f"task:{task.id}",
    )
    return task


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def start_task(task: Task, member: Member) -> Task:
    _ensure_creator(task, member)
    if task.status != Task.TaskStatus.CONFIRMED:
        raise BusinessRuleError("Select an applicant before starting.")
    task.status = Task.TaskStatus.ACTIVE
    task.save(update_fields=["status", "updated_at"])
    return task


def complete_task(task: Task, member: Member) -> Task:
    _ensure_creator(task, member)
    if task.status not in {Task.TaskStatus.ACTIVE, Task.TaskStatus.CONFIRMED}:
        raise BusinessRuleError("Only active tasks can be completed.")
    task.status = Task.TaskStatus.COMPLETED
    task.save(update_fields=["status", "updated_at"])
    selected = task.applications.filter(status=Application.ApplicationStatus.SELECTED).first()
    if selected:
        Member.objects.filter(pk=selected.member_id).update(
            completed_count=F("completed_count") + 1,
        )
        karma_amount = max(10, int(float(task.reward_amount or 0) // 10))
        from apps.engagement.services import grant_karma

        grant_karma(selected.member, karma_amount, f'Completed "{task.title}".')
    return task


def cancel_task(task: Task, member: Member) -> Task:
    _ensure_creator(task, member)
    task.status = Task.TaskStatus.CANCELLED
    task.save(update_fields=["status", "updated_at"])
    for application in task.applications.exclude(
        status=Application.ApplicationStatus.WITHDRAWN,
    ):
        notify(
            recipient=application.member,
            title="Post cancelled",
            body=f'"{task.title}" was cancelled by the creator.',
            target=f"task:{task.id}",
        )
    return task


def _ensure_creator(task: Task, member: Member) -> None:
    if task.creator_id != member.id:
        raise BusinessRuleError("Only the creator can do that.")
