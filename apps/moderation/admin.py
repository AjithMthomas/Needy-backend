from django.contrib import admin

from apps.moderation.models import Block, QuarantineAction, Report
from apps.moderation.services import unquarantine_task


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "reason",
        "target_task",
        "target_member",
        "reporter",
        "reviewed",
        "created_at",
    )
    list_filter = ("reason", "reviewed")
    search_fields = ("reporter__email", "details")
    actions = ["mark_reviewed"]

    @admin.action(description="Mark selected reports reviewed (restore nothing)")
    def mark_reviewed(self, request, queryset):
        queryset.update(reviewed=True)


@admin.register(QuarantineAction)
class QuarantineActionAdmin(admin.ModelAdmin):
    list_display = ("task", "actor_label", "reason", "created_at")
    list_filter = ("actor_label",)
    search_fields = ("task__title", "reason")

    actions = ["restore_posts"]

    @admin.action(description="Restore selected quarantined posts to the feed")
    def restore_posts(self, request, queryset):
        for action in queryset.select_related("task"):
            unquarantine_task(action.task)
            from apps.moderation.models import Report

            Report.objects.filter(target_task=action.task).update(reviewed=True)


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ("blocker", "blocked", "created_at")
    search_fields = ("blocker__email", "blocked__email")
