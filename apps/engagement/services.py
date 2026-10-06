"""engagement services — karma economy + perks + challenges + ideas."""

from __future__ import annotations

import secrets

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.accounts.models import Member
from apps.core.exceptions import BusinessRuleError, KarmaInsufficientError
from apps.engagement.models import (
    BoardIdea,
    ChallengePlay,
    IdeaVote,
    KarmaLedger,
    PartnerPerk,
    PerkClaim,
    PlayChallenge,
)
from apps.notifications.services import notify


# ---------------------------------------------------------------------------
# Karma
# ---------------------------------------------------------------------------
@transaction.atomic
def grant_karma(member: Member, amount: int, reason: str) -> int:
    if amount <= 0:
        raise BusinessRuleError("Karma amount must be positive.")
    Member.objects.filter(pk=member.pk).update(karma=F("karma") + amount)
    member.refresh_from_db(fields=["karma"])
    KarmaLedger.objects.create(
        member=member,
        kind=KarmaLedger.Kind.EARN,
        amount=amount,
        reason=reason,
        balance_after=member.karma,
    )
    notify(recipient=member, title=f"+{amount} Time Credits", body=reason)
    return member.karma


@transaction.atomic
def spend_karma(member: Member, amount: int, reason: str) -> int:
    """Atomically deduct; raises KarmaInsufficientError when short."""
    locked = Member.objects.select_for_update().get(pk=member.pk)
    if locked.karma < amount:
        raise KarmaInsufficientError(
            f"You need {amount - locked.karma} more Time Credits for this."
        )
    locked.karma -= amount
    locked.save(update_fields=["karma", "updated_at"])
    KarmaLedger.objects.create(
        member=locked,
        kind=KarmaLedger.Kind.SPEND,
        amount=amount,
        reason=reason,
        balance_after=locked.karma,
    )
    return locked.karma


def karma_statement(member: Member) -> dict:
    entries = member.karma_entries.all()[:50]
    return {
        "balance": member.karma,
        "entries": [
            {
                "id": str(e.id),
                "kind": e.kind,
                "amount": e.amount,
                "reason": e.reason,
                "balance_after": e.balance_after,
                "created_at": e.created_at,
            }
            for e in entries
        ],
    }


# ---------------------------------------------------------------------------
# Perks
# ---------------------------------------------------------------------------
@transaction.atomic
def claim_perk(member: Member, perk: PartnerPerk) -> PerkClaim:
    if not perk.is_active:
        raise BusinessRuleError("This offer is no longer available.")
    if PerkClaim.objects.filter(perk=perk, member=member).exists():
        raise BusinessRuleError("You already claimed this voucher.")
    spend_karma(member, perk.cost_karma, f"{perk.merchant} voucher claimed.")
    return PerkClaim.objects.create(
        perk=perk,
        member=member,
        code=f"NEEDY-{secrets.token_hex(3).upper()}",
        expires_at=timezone.now() + timezone.timedelta(hours=perk.valid_hours),
    )


# ---------------------------------------------------------------------------
# Play & Earn
# ---------------------------------------------------------------------------
@transaction.atomic
def record_play(member: Member, challenge: PlayChallenge, score: int) -> dict:
    today = timezone.localdate()
    if ChallengePlay.objects.filter(
        challenge=challenge,
        member=member,
        played_on=today,
    ).exists():
        raise BusinessRuleError("You already played this challenge today. Come back tomorrow!")

    from django.conf import settings

    consolation = settings.NUVRA["PLAY_DAILY_CONSOLATION_KARMA"]
    won = score >= challenge.target
    reward = challenge.reward_karma if won else consolation
    ChallengePlay.objects.create(
        challenge=challenge,
        member=member,
        score=score,
        reward=reward,
        played_on=today,
    )
    grant_karma(
        member,
        reward,
        "You beat the target in a Play & Earn challenge!"
        if won
        else "Thanks for playing — come back tomorrow!",
    )
    return {"score": score, "won": won, "reward": reward}


def has_played_today(member: Member, challenge: PlayChallenge) -> bool:
    return ChallengePlay.objects.filter(
        challenge=challenge,
        member=member,
        played_on=timezone.localdate(),
    ).exists()


# ---------------------------------------------------------------------------
# Community board
# ---------------------------------------------------------------------------
@transaction.atomic
def submit_idea(member: Member, title: str, details: str, tag: str) -> BoardIdea:
    idea = BoardIdea.objects.create(
        author=member,
        title=title,
        details=details,
        tag=tag,
        upvotes=1,
    )
    IdeaVote.objects.create(idea=idea, member=member)  # auto self-vote (mock parity)
    grant_karma(member, _idea_karma(), "Idea published on the community board.")
    return idea


def _idea_karma() -> int:
    from django.conf import settings

    return settings.NUVRA["IDEA_PUBLISH_KARMA"]


@transaction.atomic
def toggle_idea_vote(idea: BoardIdea, member: Member) -> dict:
    vote = IdeaVote.objects.filter(idea=idea, member=member).first()
    if vote:
        vote.delete()
        idea.upvotes = F("upvotes") - 1
        voted = False
    else:
        IdeaVote.objects.create(idea=idea, member=member)
        idea.upvotes = F("upvotes") + 1
        voted = True
    idea.save(update_fields=["upvotes", "updated_at"])
    idea.refresh_from_db(fields=["upvotes"])
    return {"voted": voted, "upvotes": idea.upvotes}
