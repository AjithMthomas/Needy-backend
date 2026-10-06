"""In-app notification centre items."""

from django.db import models

from apps.accounts.models import Member
from apps.core.models import UUIDModel


class Notification(UUIDModel):
    recipient = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=120)
    body = models.TextField(blank=True, default="")
    read = models.BooleanField(default=False, db_index=True)
    # Optional deep-link hint, e.g. "task:<id>" or "auction:<id>".
    target = models.CharField(max_length=120, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "read", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.recipient_id}: {self.title}"
