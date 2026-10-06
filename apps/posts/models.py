"""posts models — Task (every kind), Applications, Saves, Reposts, Ratings.

The Task table serves ALL verticals (regular feed, emergency SOS, shop
gigs, room finder, teams, trips) exactly like the Flutter ``Task``:
one pipeline — feed → apply → chat → confirm → complete → rate.
"""

from __future__ import annotations

import uuid

from django.db import models

from apps.accounts.models import Member
from apps.core.models import UUIDModel


class Task(UUIDModel):
    class PostType(models.TextChoices):
        TASK = "task", "Task"
        COMPANY = "company", "Company"
        OFFER = "offer", "Offer"

    class PostKind(models.TextChoices):
        REGULAR = "regular", "Post"
        EMERGENCY = "emergency", "SOS"
        GIG = "gig", "Gig"
        ROOM = "room", "Room"
        TEAM = "team", "Team"
        TRIP = "trip", "Trip"

    class ExchangeMode(models.TextChoices):
        PAID = "paid", "Paid"
        FREE = "free", "Free"
        TREAT = "treat", "I'll treat"
        EXPENSES_COVERED = "expensesCovered", "Expenses covered"
        NEGOTIABLE = "negotiable", "Negotiable"
        BARTER = "barter", "Skill barter"

    class GenderPreference(models.TextChoices):
        ANYONE = "anyone", "Everyone"
        FEMALE_ONLY = "femaleOnly", "Girls only"
        MALE_ONLY = "maleOnly", "Boys only"

    class TaskRisk(models.TextChoices):
        LOW = "low", "Low risk"
        MEDIUM = "medium", "Medium risk"
        HIGH = "high", "High risk"

    class TaskStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        SAFETY_CHECK = "safetyCheck", "Safety check"
        PUBLISHED = "published", "Published"
        CONFIRMED = "confirmed", "Confirmed"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"
        DISPUTED = "disputed", "Disputed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="posts")

    # Merchant-facing name override (shop gigs show the shop, not the person).
    creator_name_override = models.CharField(max_length=80, blank=True, default="")

    type = models.CharField(max_length=10, choices=PostType.choices, default=PostType.TASK)
    kind = models.CharField(max_length=10, choices=PostKind.choices, default=PostKind.REGULAR)

    title = models.CharField(max_length=140)
    description = models.TextField()
    category = models.CharField(max_length=40, default="Errands")

    # Kind-specific note: gig payout terms, room budget, trip destination.
    payout_note = models.CharField(max_length=120, blank=True, default="")

    scheduled_at = models.DateTimeField(db_index=True)
    duration_minutes = models.PositiveIntegerField(default=60)

    area = models.CharField(max_length=120)
    # distance_km is denormalised at write time (haversine from the poster's
    # coordinates; 1.0 fallback when location is off) — filters stay indexable.
    distance_km = models.FloatField(default=1.0)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)

    exchange = models.CharField(
        max_length=16,
        choices=ExchangeMode.choices,
        default=ExchangeMode.PAID,
    )
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    capacity = models.PositiveIntegerField(default=1)
    applicant_count = models.PositiveIntegerField(default=0)  # denormalised counter
    gender_preference = models.CharField(
        max_length=10,
        choices=GenderPreference.choices,
        default=GenderPreference.ANYONE,
    )

    risk = models.CharField(max_length=6, choices=TaskRisk.choices, default=TaskRisk.LOW)
    status = models.CharField(
        max_length=12,
        choices=TaskStatus.choices,
        default=TaskStatus.PUBLISHED,
        db_index=True,
    )

    meeting_preference = models.CharField(max_length=120, default="Public meeting point")
    has_checkin = models.BooleanField(default=False)

    # Moderation (Phase 8): a report hides the post from every feed.
    quarantined = models.BooleanField(default=False, db_index=True)
    quarantine_reason = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        ordering = ["scheduled_at"]
        indexes = [
            models.Index(fields=["status", "kind", "quarantined"]),
            models.Index(fields=["creator", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"[{self.kind}] {self.title}"

    @property
    def display_creator_name(self) -> str:
        return self.creator_name_override or self.creator.public_name

    def admits(self, gender: str | None) -> bool:
        """The core safety rule: may a member of `gender` join this post?"""
        gp = self.gender_preference
        if gp == self.GenderPreference.ANYONE:
            return True
        if gender is None:
            return False
        return (gp == self.GenderPreference.FEMALE_ONLY and gender == Member.Gender.FEMALE) or (
            gp == self.GenderPreference.MALE_ONLY and gender == Member.Gender.MALE
        )

    def selected_count(self) -> int:
        return self.applications.filter(status=Application.ApplicationStatus.SELECTED).count()


class Application(UUIDModel):
    """One per member per task."""

    class ApplicationStatus(models.TextChoices):
        INTERESTED = "interested", "Interested"
        CHATTING = "chatting", "In chat"
        SELECTED = "selected", "Selected"
        DECLINED = "declined", "Not selected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="applications")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="applications")
    intro_message = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=10,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.CHATTING,
        db_index=True,
    )
    unread_for_creator = models.PositiveIntegerField(default=1)
    unread_for_member = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["task", "member"], name="uniq_application_per_task"),
        ]
        indexes = [models.Index(fields=["task", "status"])]

    def __str__(self) -> str:
        return f"{self.member.public_name} → {self.task.title}"


class SavedPost(UUIDModel):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="saved_posts")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="saved_by")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["member", "task"], name="uniq_saved_post"),
        ]


class Repost(UUIDModel):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="reposts")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="reposted_by")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["member", "task"], name="uniq_repost"),
        ]


class Rating(UUIDModel):
    """Post-session mutual review — updates trust stats server-side."""

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="ratings")
    rater = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="ratings_given")
    ratee = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="ratings_received")
    stars = models.DecimalField(max_digits=2, decimal_places=1)
    note = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["task", "rater"], name="uniq_rating_per_task_rater"),
        ]
