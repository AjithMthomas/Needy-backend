from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "title", "read", "created_at")
    search_fields = ("recipient__email", "title")
    list_filter = ("read",)
