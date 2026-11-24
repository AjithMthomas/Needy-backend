"""Notification service — the single way anything creates notifications."""

from apps.accounts.models import Member
from apps.notifications.models import DeviceToken, Notification
from apps.notifications.push import send_push


def notify(recipient: Member, title: str, body: str = "", target: str = "") -> Notification:
    """Create in-app notification and dispatch remote push (FCM / APNs)."""
    notif = Notification.objects.create(recipient=recipient, title=title, body=body, target=target)
    send_push(recipient=recipient, title=title, body=body, target=target)
    return notif


def unread_count(member: Member) -> int:
    return member.notifications.filter(read=False).count()


def mark_all_read(member: Member) -> None:
    member.notifications.filter(read=False).update(read=True)


def mark_read(member: Member, notification_id) -> None:
    member.notifications.filter(id=notification_id).update(read=True)


def register_device(
    member: Member,
    token: str,
    platform: str = DeviceToken.Platform.ANDROID,
    device_name: str = "",
) -> DeviceToken:
    """Register or update an FCM/APNs device token for a member."""
    device, _ = DeviceToken.objects.update_or_create(
        token=token,
        defaults={
            "member": member,
            "platform": platform,
            "device_name": device_name,
            "is_active": True,
        },
    )
    return device


def unregister_device(token: str) -> None:
    """Deactivate or remove a device token upon sign-out."""
    DeviceToken.objects.filter(token=token).update(is_active=False)


def bulk_notify(recipients, title: str, body: str = "", target: str = "") -> int:
    """Create the same notification for many members efficiently and dispatch push."""
    rows = [
        Notification(recipient=member, title=title, body=body, target=target)
        for member in recipients
    ]
    Notification.objects.bulk_create(rows, batch_size=500)
    for member in recipients:
        send_push(recipient=member, title=title, body=body, target=target)
    return len(rows)

