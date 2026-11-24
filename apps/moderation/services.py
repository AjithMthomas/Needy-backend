"""moderation services — reports quarantine only on corroboration; blocks
filter feeds."""

from __future__ import annotations

from django.conf import settings
from django.db import transaction

from apps.accounts.models import Member
from apps.core.exceptions import BusinessRuleError
from apps.moderation.models import Block, QuarantineAction, Report


def quarantine_threshold(reason: str) -> int:
    """Distinct reporters needed before a post is hidden.

    A safety concern hides on the first report; every other reason needs
    corroboration from independent members, because a single report used to
    take any post down — a free censorship tool.
    """
    if reason == Report.Reason.SAFETY:
        return 1
    return int(settings.NUVRA.get("REPORT_QUARANTINE_THRESHOLD", 3))


@transaction.atomic
def file_report(
    reporter: Member,
    *,
    task=None,
    target_member: Member | None = None,
    reason: str,
    details: str,
) -> Report:
    if task is not None and task.creator_id == reporter.id:
        raise BusinessRuleError("You can't report your own post.")
    if target_member is not None and target_member.id == reporter.id:
        raise BusinessRuleError("You can't report yourself.")
    if Report.objects.filter(
        reporter=reporter,
        target_task=task,
        target_member=target_member,
    ).exists():
        raise BusinessRuleError("You already reported this.")

    report = Report.objects.create(
        reporter=reporter,
        target_task=task,
        target_member=target_member,
        reason=reason,
        details=details,
    )
    if task is not None:
        distinct_reporters = (
            Report.objects.filter(target_task=task)
            .values("reporter_id")
            .distinct()
            .count()
        )
        if distinct_reporters >= quarantine_threshold(reason):
            quarantine_task(
                task,
                reason=f"reported as {reason}",
                actor=reporter,
                actor_label="report",
            )
    return report


def quarantine_task(task, *, reason: str, actor: Member | None, actor_label: str) -> None:
    from apps.posts.models import Task

    Task.objects.filter(pk=task.pk).update(
        quarantined=True,
        quarantine_reason=reason[:200],
    )
    QuarantineAction.objects.create(
        task=task,
        actor=actor,
        actor_label=actor_label,
        reason=reason[:200],
    )
    if task.creator_id:
        from apps.accounts.models import Member
        from apps.notifications.services import notify

        creator = Member.objects.filter(pk=task.creator_id).first()
        if creator is not None:
            notify(
                recipient=creator,
                title="Post quarantined",
                body=f"A post was hidden pending review — {reason}",
                target=f"task:{task.id}",
            )


def unquarantine_task(task, *, admin_member: Member | None = None) -> None:
    from apps.posts.models import Task

    Task.objects.filter(pk=task.pk).update(quarantined=False, quarantine_reason="")
    QuarantineAction.objects.create(
        task=task,
        actor=admin_member,
        actor_label="admin",
        reason="restored by review",
    )


@transaction.atomic
def block_member(blocker: Member, blocked: Member) -> dict:
    if blocker.id == blocked.id:
        raise BusinessRuleError("You can't block yourself.")
    _, created = Block.objects.get_or_create(blocker=blocker, blocked=blocked)
    return {"blocked": True, "already_blocked": not created}


@transaction.atomic
def unblock_member(blocker: Member, blocked: Member) -> dict:
    Block.objects.filter(blocker=blocker, blocked=blocked).delete()
    return {"blocked": False}


def blocked_ids_for(member: Member) -> set:
    """IDs this member has blocked OR been blocked by (both directions)."""
    given = set(Block.objects.filter(blocker=member).values_list("blocked_id", flat=True))
    received = set(Block.objects.filter(blocked=member).values_list("blocker_id", flat=True))
    return given | received
