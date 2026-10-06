"""moderation models — reports, blocks, quarantine audit trail."""

import uuid

from django.db import models

from apps.accounts.models import Member
from apps.core.models import UUIDModel


class Report(UUIDModel):
    """One-tap report; reporting a post auto-quarantines it (mock parity),
    a human reviews it in the Django admin."""

    class Reason(models.TextChoices):
        SPAM = "spam", "Spam or scam"
        INAPPROPRIATE = "inappropriate", "Inappropriate content"
        HARASSMENT = "harassment", "Harassment"
        FAKE = "fake", "Fake or misleading"
        SAFETY = "safety", "Safety concern"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="reports_filed",
    )
    # Generic-ish pointer kept explicit + typed for queryability.
    target_task = models.ForeignKey(
        "posts.Task",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="reports",
    )
    target_member = models.ForeignKey(
        Member,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="reports_against",
    )
    reason = models.CharField(max_length=20, choices=Reason.choices)
    details = models.TextField(blank=True, default="")
    reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        Member,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviews_moderated",
    )

    def __str__(self) -> str:
        return f"{self.reason} → {self.target_task or self.target_member}"


class Block(UUIDModel):
    """A blocks B: B's posts stop appearing for A, and B cannot apply to
    A's posts or message A. Enforced in feeds/services."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blocker = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="blocks_given")
    blocked = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="blocks_received")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["blocker", "blocked"], name="uniq_block"),
            models.CheckConstraint(
                check=~models.Q(blocker=models.F("blocked")),
                name="no_self_block",
            ),
        ]


class QuarantineAction(UUIDModel):
    """Audit trail: every hide/unhide with the reason and actor."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey("posts.Task", on_delete=models.CASCADE, related_name="quarantine_log")
    actor = models.ForeignKey(
        Member,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    actor_label = models.CharField(max_length=40, default="report")  # report | admin | auto
    reason = models.CharField(max_length=200)

    class Meta:
        ordering = ["-created_at"]
