"""chat services — all room/message rules in one place."""

from __future__ import annotations

from django.db import transaction
from django.db.models import F

from apps.accounts.models import Member
from apps.chat.models import ChatRoom, Message
from apps.core.exceptions import BusinessRuleError


def get_or_create_room_for_application(application) -> ChatRoom:
    """Every application gets a chat room the moment it exists."""
    room, _ = ChatRoom.objects.get_or_create(
        application=application,
        defaults={
            "creator": application.task.creator,
            "applicant": application.member,
        },
    )
    return room


@transaction.atomic
def send_message(room: ChatRoom, sender: Member, body: str) -> Message:
    if not room.is_participant(sender):
        raise BusinessRuleError("You are not in this room.")
    body = body.strip()
    if not body:
        raise BusinessRuleError("Message cannot be empty.")

    last_seq = (
        Message.objects.filter(room=room).order_by("-seq").values_list("seq", flat=True).first()
        or 0
    )
    message = Message.objects.create(room=room, sender=sender, body=body, seq=last_seq + 1)

    if sender.id == room.creator_id:
        room.unread_for_applicant = F("unread_for_applicant") + 1
    else:
        room.unread_for_creator = F("unread_for_creator") + 1
    room.last_message_at = message.created_at
    room.save()
    return message


def mark_read(room: ChatRoom, member: Member) -> None:
    if member.id == room.creator_id:
        room.unread_for_creator = 0
    else:
        room.unread_for_applicant = 0
    room.save(update_fields=["unread_for_creator", "unread_for_applicant", "updated_at"])
