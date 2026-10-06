"""chat models — one room per application, messages with unread counters.

Polling-friendly: ``since_id`` incremental fetch is the primary read
pattern; unread counters are denormalised onto ChatRoom.
"""

from __future__ import annotations

import uuid

from django.db import models

from apps.accounts.models import Member
from apps.core.models import TimeStampedModel


class ChatRoom(TimeStampedModel):
    """One room per application. Creator + applicant are the members."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField(
        "posts.Application",
        on_delete=models.CASCADE,
        related_name="chat_room",
    )
    creator = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="rooms_as_creator",
    )
    applicant = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="rooms_as_applicant",
    )
    unread_for_creator = models.PositiveIntegerField(default=0)
    unread_for_applicant = models.PositiveIntegerField(default=0)
    last_message_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-last_message_at", "-created_at"]

    def unread_for(self, member: Member) -> int:
        return (
            self.unread_for_creator if member.id == self.creator_id else self.unread_for_applicant
        )

    def counterpart(self, member: Member) -> Member:
        return self.applicant if member.id == self.creator_id else self.creator

    def is_participant(self, member: Member) -> bool:
        return member.id in {self.creator_id, self.applicant_id}


class Message(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="messages")
    body = models.TextField()
    # Monotonic per-room sequence for since_id polling.
    seq = models.PositiveIntegerField(db_index=True)

    class Meta:
        ordering = ["seq"]
        constraints = [
            models.UniqueConstraint(fields=["room", "seq"], name="uniq_room_seq"),
        ]

    def __str__(self) -> str:
        return f"#{self.seq} {self.sender_id}: {self.body[:24]}"
