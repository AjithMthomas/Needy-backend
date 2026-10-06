"""Notification service — the single way anything creates notifications."""

from apps.accounts.models import Member
from apps.notifications.models import Notification


def notify(recipient: Member, title: str, body: str = "", target: str = "") -> None:
    Notification.objects.create(recipient=recipient, title=title, body=body, target=target)


def unread_count(member: Member) -> int:
    return member.notifications.filter(read=False).count()


def mark_all_read(member: Member) -> None:
    member.notifications.filter(read=False).update(read=True)


def mark_read(member: Member, notification_id) -> None:
    member.notifications.filter(id=notification_id).update(read=True)


def bulk_notify(recipients, title: str, body: str = "", target: str = "") -> int:
    """Create the same notification for many members efficiently."""
    rows = [
        Notification(recipient=member, title=title, body=body, target=target)
        for member in recipients
    ]
    Notification.objects.bulk_create(rows, batch_size=500)
    return len(rows)
