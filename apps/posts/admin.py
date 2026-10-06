from django.contrib import admin

from apps.posts.models import Application, Rating, Repost, SavedPost, Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "kind",
        "type",
        "status",
        "creator",
        "area",
        "reward_amount",
        "capacity",
        "applicant_count",
        "quarantined",
        "created_at",
    )
    list_filter = ("kind", "type", "status", "risk", "quarantined", "exchange")
    search_fields = ("title", "description", "creator__email", "area")
    date_hierarchy = "created_at"


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("task", "member", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("task__title", "member__email")


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("task", "rater", "ratee", "stars", "created_at")
    search_fields = ("task__title", "rater__email", "ratee__email")


admin.site.register(SavedPost)
admin.site.register(Repost)
