"""Management command to dispatch re-engagement notifications to inactive users.

Run manually or schedule via cron-job.org / GitHub Actions:
    python manage.py dispatch_engagement
"""

from __future__ import annotations

import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import Member
from apps.notifications import services
from apps.notifications.models import Notification
from apps.posts.models import Task

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Dispatch re-engagement and local opportunity pushes to members."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print candidates without creating notifications or sending pushes.",
        )
        parser.add_argument(
            "--hours-inactive",
            type=int,
            default=24,
            help="Hours of inactivity before sending a re-engagement push (default: 24).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        hours = options["hours_inactive"]
        now = timezone.now()
        threshold = now - timedelta(hours=hours)

        # 1. Count recent active tasks to highlight
        recent_tasks = Task.objects.filter(
            status=Task.TaskStatus.ACTIVE,
            created_at__gte=now - timedelta(hours=48),
        ).exclude(status__in=[Task.TaskStatus.COMPLETED, Task.TaskStatus.CANCELLED])
        recent_task_count = recent_tasks.count()

        # 2. Find candidate members with registered devices who haven't received
        # a re-engagement notification in the last `hours`
        candidates = Member.objects.filter(
            devices__is_active=True,
        ).distinct()

        dispatched = 0
        skipped = 0

        for member in candidates:
            # Check if recently notified
            recent_notif = Notification.objects.filter(
                recipient=member,
                created_at__gte=threshold,
                target__startswith="reengagement:",
            ).exists()

            if recent_notif:
                skipped += 1
                continue

            if recent_task_count > 0:
                title = f"{recent_task_count} new tasks in your neighborhood!"
                body = "People need help nearby. Complete a quick errand or task to earn rewards."
                target = "reengagement:tasks"
            else:
                title = "Got some free time today?"
                body = "Check out what's happening around Madiwala or post a need."
                target = "reengagement:explore"

            if dry_run:
                self.stdout.write(f"[DRY-RUN] Would notify {member.email}: '{title}'")
            else:
                services.notify(recipient=member, title=title, body=body, target=target)
                self.stdout.write(f"Notified {member.email}: '{title}'")

            dispatched += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Engagement dispatch: {dispatched} sent, {skipped} skipped."
            )
        )

