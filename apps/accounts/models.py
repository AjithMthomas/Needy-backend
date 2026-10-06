"""accounts models — Member + email OTP.

Member mirrors the Flutter ``Member`` model 1:1 (see
``time_need_app/lib/core/models/user.dart``); trust rules (gender
admission, capacity, moderation) are enforced server-side here and in
the posts app.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

from apps.core.models import TimeStampedModel


class MemberManager(BaseUserManager):
    def create_member(self, email: str, **extra):
        email = self.normalize_email(email).lower()
        member = self.model(email=email, **extra)
        member.set_unusable_password()
        member.save(using=self._db)
        return member

    def create_superuser(self, email: str, password: str, **extra):
        member = self.create_member(email, is_staff=True, is_superuser=True, **extra)
        member.set_password(password)
        member.save(using=self._db)
        return member

    def create_member_with_otp(self, email: str, code: str, **extra):
        """Dev/test convenience: create member + valid OTP in one call."""
        member = self.create_member(email, **extra)
        OtpCode.objects.issue(email=email, member=member, code=code)
        return member


class Member(AbstractBaseUser, TimeStampedModel):
    """A nuvra member. PII is intentionally minimal: email-only auth."""

    class Gender(models.TextChoices):
        FEMALE = "female", "Female"
        MALE = "male", "Male"
        OTHER = "other", "Other"

    class TrustBadge(models.TextChoices):
        PUNCTUAL = "punctual", "Punctual"
        FRIENDLY = "friendly", "Friendly"
        SAFE_HELPER = "safeHelper", "Safe Helper"
        VERIFIED_SCOUT = "verifiedScout", "Verified Scout"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    public_name = models.CharField(max_length=60)
    photo_url = models.URLField(blank=True, default="")
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.OTHER)
    bio = models.TextField(blank=True, default="")

    # Trust signals (behaviour-based, never wealth-based).
    completed_count = models.PositiveIntegerField(default=0)
    rating = models.FloatField(default=5.0)
    rating_count = models.PositiveIntegerField(default=0)
    cancellations = models.PositiveIntegerField(default=0)
    no_shows = models.PositiveIntegerField(default=0)
    verified_badge = models.BooleanField(default=False)

    date_of_birth = models.DateField(null=True, blank=True)  # age gate, DPDP-conscious
    age_gate_passed = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    categories = models.JSONField(default=list, blank=True)
    is_email_verified = models.BooleanField(default=False)
    profile_completed = models.BooleanField(default=False)

    # Safety centre.
    safety_contact_name = models.CharField(max_length=80, blank=True, default="")
    safety_contact_phone = models.CharField(max_length=20, blank=True, default="")
    availability_hours = models.CharField(max_length=120, blank=True, default="Flexible")

    # Community layer.
    karma = models.IntegerField(default=0)
    is_guardian = models.BooleanField(default=False)
    available_now = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = MemberManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self) -> str:
        return f"{self.public_name} <{self.email}>"

    @property
    def is_established(self) -> bool:
        return self.completed_count >= 40

    @property
    def reliability_percent(self) -> int:
        attempts = self.completed_count + self.cancellations + self.no_shows
        if attempts == 0:
            return 100
        return round(self.completed_count * 100 / attempts)

    @property
    def badge_codes(self) -> list[str]:
        return list(self.badges_earned.values_list("badge", flat=True))

    def add_badge(self, badge: str) -> None:
        Badge.objects.get_or_create(member=self, badge=badge)


class Badge(TimeStampedModel):
    """Trust badge earned from post-session mutual reviews (never self-declared)."""

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="badges_earned")
    badge = models.CharField(max_length=20, choices=Member.TrustBadge.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["member", "badge"], name="uniq_member_badge"),
        ]


class OtpCodeManager(models.Manager):
    def issue(self, email: str, member: Member | None, code: str) -> OtpCode:
        """Issue an OTP: single-use, hashed, expiring; invalidates older ones."""
        from django.conf import settings
        from django.utils import timezone

        validity = settings.NUVRA["OTP_VALIDITY_MINUTES"]
        self.filter(email=email).update(consumed=True)
        return self.create(
            email=email,
            member=member,
            code_hash=OtpCode.hash_code(code),
            expires_at=timezone.now() + timedelta(minutes=validity),
        )


class OtpCode(TimeStampedModel):
    """One-time passcode. Codes are stored hashed (sha256), single-use,
    with server-side attempt counting — an intercepted DB dump alone is
    not enough to brute-force an account."""

    email = models.EmailField(db_index=True)
    member = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL)
    code_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    consumed = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)

    objects = OtpCodeManager()

    class Meta:
        ordering = ["-created_at"]

    @staticmethod
    def hash_code(code: str) -> str:
        import hashlib

        from django.conf import settings

        return hashlib.sha256(f"{settings.SECRET_KEY}:{code}".encode()).hexdigest()

    @property
    def is_expired(self) -> bool:
        from django.utils import timezone

        return timezone.now() >= self.expires_at

    def matches(self, code: str) -> bool:
        # NOTE: named `matches`, not `check` — `Model.check()` is reserved
        # by Django's system-check framework.
        return secrets.compare_digest(self.code_hash, self.hash_code(code))
