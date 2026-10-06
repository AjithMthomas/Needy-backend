"""Auth service layer — all OTP business rules live here, not in views.

Rules (all server-enforced):
- resend cooldown (default 60 s) per email
- code single-use, expires (default 10 min), hashed at rest
- max attempts (default 5) per code, then it is dead
- unknown emails are indistinguishable from known ones in responses
  (no account enumeration)
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.accounts.models import Member, OtpCode


@dataclass(frozen=True)
class OtpRequestResult:
    sent: bool
    cooldown_seconds: int


def request_otp(email: str) -> OtpRequestResult:
    """Issue + email an OTP. Creates the Member record on first contact."""
    email = email.strip().lower()
    cooldown = settings.NUVRA["OTP_RESEND_COOLDOWN_SECONDS"]

    latest = OtpCode.objects.filter(email=email).first()
    if latest and not latest.consumed and not latest.is_expired:
        elapsed = (timezone.now() - latest.created_at).total_seconds()
        if elapsed < cooldown:
            return OtpRequestResult(sent=False, cooldown_seconds=int(cooldown - elapsed))

    member = Member.objects.filter(email=email).first()
    if member is None:
        member = Member.objects.create_member(email)
    elif not member.is_active:
        # Banned/deactivated members still can't be probed via responses.
        return OtpRequestResult(sent=False, cooldown_seconds=cooldown)

    code = _new_code()
    OtpCode.objects.issue(email=email, member=member, code=code)
    _send_code_email(email, code)
    return OtpRequestResult(sent=True, cooldown_seconds=cooldown)


def verify_otp(email: str, code: str) -> Member:
    """Return the verified Member or raise BusinessRuleError."""
    from apps.core.exceptions import BusinessRuleError

    email = email.strip().lower()
    otp = OtpCode.objects.filter(email=email, consumed=False).first()
    if otp is None:
        raise BusinessRuleError("No active code. Request a new one.")
    if otp.is_expired:
        raise BusinessRuleError("This code expired. Request a new one.")

    max_attempts = settings.NUVRA["OTP_MAX_ATTEMPTS"]
    if otp.attempts >= max_attempts:
        otp.consumed = True
        otp.save(update_fields=["consumed"])
        raise BusinessRuleError("Too many attempts. Request a new code.")

    if not otp.matches(code):
        otp.attempts += 1
        otp.save(update_fields=["attempts"])
        left = max_attempts - otp.attempts
        raise BusinessRuleError(f"Wrong code. {left} attempt(s) left." if left else "Wrong code.")

    otp.consumed = True
    otp.save(update_fields=["consumed"])

    member = otp.member or Member.objects.filter(email=email).first()
    if member is None:
        raise BusinessRuleError("Account not found. Request a new code.")
    member.is_email_verified = True
    member.age_gate_passed = True  # 18+ gate acknowledged during OTP screen
    member.save(update_fields=["is_email_verified", "age_gate_passed"])
    return member


def _new_code() -> str:
    # DEMO_MODE (dev/test) uses the fixed 424242; prod generates random codes.
    if settings.NUVRA.get("DEMO_MODE"):
        return settings.NUVRA["DEMO_OTP"]
    return f"{secrets.randbelow(1000000):06d}"


def _send_code_email(email: str, code: str) -> None:
    send_mail(
        subject="Your needy sign-in code",
        message=(
            f"Your needy verification code is {code}.\n\n"
            "It expires in 10 minutes and can be used once.\n"
            "If you didn't request it, ignore this email."
        ),
        from_email=None,
        recipient_list=[email],
        fail_silently=True,  # console backend in dev; never block signup on SMTP hiccups
    )
