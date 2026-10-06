"""Abstract base models — every app model inherits from these.

UUID primary keys: opaque, non-enumerable, URL-safe, and shard-friendly.
Timestamps: cursor pagination + incremental sync depend on them.
"""

import uuid

from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
