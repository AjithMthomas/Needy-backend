"""engagement models — karma, perks, challenges, community board, radar."""

from __future__ import annotations

import uuid

from django.db import models

from apps.accounts.models import Member
from apps.core.models import UUIDModel


class KarmaLedger(UUIDModel):
    """Append-only karma journal. ``Member.karma`` is the cached balance;
    this table is the source of truth and the audit trail."""

    class Kind(models.TextChoices):
        EARN = "earn", "Earn"
        SPEND = "spend", "Spend"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="karma_entries")
    kind = models.CharField(max_length=5, choices=Kind.choices)
    amount = models.PositiveIntegerField()
    reason = models.CharField(max_length=200)
    balance_after = models.IntegerField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.kind} {self.amount} — {self.reason}"


class PartnerPerk(UUIDModel):
    """Phase 7 — merchant offer with a claimable footfall voucher."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.CharField(max_length=80)
    title = models.CharField(max_length=120)
    details = models.TextField(blank=True, default="")
    icon = models.CharField(max_length=40, default="local_cafe")
    cost_karma = models.PositiveIntegerField()
    area = models.CharField(max_length=120)
    valid_hours = models.PositiveIntegerField(default=24)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["cost_karma"]

    def __str__(self) -> str:
        return f"{self.merchant}: {self.title}"


class PerkClaim(UUIDModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perk = models.ForeignKey(PartnerPerk, on_delete=models.CASCADE, related_name="claims")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="perk_claims")
    code = models.CharField(max_length=12)  # shown at the counter
    expires_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["perk", "member"], name="uniq_perk_claim"),
        ]


class PlayChallenge(UUIDModel):
    """Phase 6 — Play & Earn challenge (targets + karma rewards)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=40, unique=True)  # 'tap30', 'memory'
    title = models.CharField(max_length=80)
    rules = models.TextField(blank=True, default="")
    target = models.PositiveIntegerField()
    reward_karma = models.PositiveIntegerField()
    icon = models.CharField(max_length=40, default="touch_app")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.title


class ChallengePlay(UUIDModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(PlayChallenge, on_delete=models.CASCADE, related_name="plays")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="challenge_plays")
    score = models.PositiveIntegerField()
    reward = models.PositiveIntegerField(default=0)
    played_on = models.DateField(db_index=True)

    class Meta:
        ordering = ["-created_at"]


class BoardIdea(UUIDModel):
    """Phase 9 — community wishlist idea with Reddit-style upvotes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="board_ideas")
    title = models.CharField(max_length=140)
    details = models.TextField(blank=True, default="")
    tag = models.CharField(max_length=40, default="Feature")
    upvotes = models.PositiveIntegerField(default=1)
    scheduled = models.BooleanField(default=False)

    class Meta:
        ordering = ["-upvotes", "-created_at"]

    def __str__(self) -> str:
        return self.title


class IdeaVote(UUIDModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    idea = models.ForeignKey(BoardIdea, on_delete=models.CASCADE, related_name="votes")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="idea_votes")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["idea", "member"], name="uniq_idea_vote"),
        ]


class RadarPing(UUIDModel):
    """Presence ping powering the Bored Radar zone aggregates."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="radar_pings")
    zone = models.CharField(max_length=80, db_index=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    up_for = models.CharField(max_length=20, default="tasks")  # tasks|tea|walk|play

    class Meta:
        ordering = ["-created_at"]
