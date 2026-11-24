"""Push notification dispatch via Firebase Cloud Messaging (FCM)."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from apps.accounts.models import Member

logger = logging.getLogger(__name__)

_FIREBASE_INITIALIZED = False


def _get_firebase_app():
    global _FIREBASE_INITIALIZED
    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError:
        logger.debug("firebase-admin package not available")
        return None

    try:
        return firebase_admin.get_app()
    except ValueError:
        pass  # Not yet initialized

    # Try JSON string from env
    raw_json = getattr(settings, "FIREBASE_CREDENTIALS_JSON", "")
    if raw_json:
        try:
            cert_data = json.loads(raw_json)
            cred = credentials.Certificate(cert_data)
            _FIREBASE_INITIALIZED = True
            return firebase_admin.initialize_app(cred)
        except Exception as exc:
            logger.warning("Failed to initialize Firebase from JSON: %s", exc)

    # Try path from env
    path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", "")
    if path:
        try:
            cred = credentials.Certificate(path)
            _FIREBASE_INITIALIZED = True
            return firebase_admin.initialize_app(cred)
        except Exception as exc:
            logger.warning("Failed to initialize Firebase from path '%s': %s", path, exc)

    # Try default application credentials
    try:
        _FIREBASE_INITIALIZED = True
        return firebase_admin.initialize_app()
    except Exception:
        # Expected in development or test environments where no credentials exist
        return None


def send_push(recipient: Member, title: str, body: str = "", target: str = "") -> int:
    """Send a push notification to all active devices of the recipient.

    Returns the number of devices targeted. Never raises exceptions.
    """
    from apps.notifications.models import DeviceToken

    active_tokens = list(
        DeviceToken.objects.filter(member=recipient, is_active=True).values_list("token", flat=True)
    )
    if not active_tokens:
        return 0

    app = _get_firebase_app()
    if not app:
        logger.debug(
            "[Push MOCK] To %s (%d device%s): '%s' — '%s' (target: %s)",
            recipient.id,
            len(active_tokens),
            "s" if len(active_tokens) > 1 else "",
            title,
            body,
            target,
        )
        return len(active_tokens)

    try:
        from firebase_admin import messaging

        messages = [
            messaging.Message(
                token=token,
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={
                    "target": target,
                    "click_action": "FLUTTER_NOTIFICATION_CLICK",
                },
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        sound="default",
                        channel_id="needy_notifications",
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound="default",
                            badge=1,
                        ),
                    ),
                ),
            )
            for token in active_tokens
        ]
        response = messaging.send_each(messages)


        # Clean up stale / unregistered tokens
        failed_tokens = []
        for idx, resp in enumerate(response.responses):
            if not resp.success:
                err = resp.exception
                # Check for token expiry/invalidation
                if hasattr(err, "code") and err.code in (
                    "messaging/invalid-registration-token",
                    "messaging/registration-token-not-registered",
                ):
                    failed_tokens.append(active_tokens[idx])

        if failed_tokens:
            DeviceToken.objects.filter(token__in=failed_tokens).update(is_active=False)
            logger.info(
                "Deactivated %d stale device tokens for %s",
                len(failed_tokens),
                recipient.id,
            )


        return response.success_count
    except Exception as exc:
        logger.warning("FCM push delivery failed for %s: %s", recipient.id, exc)
        return 0
