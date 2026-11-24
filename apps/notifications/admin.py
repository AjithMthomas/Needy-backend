from django.contrib import admin

from apps.notifications.models import DeviceToken, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "title", "read", "created_at")
    search_fields = ("recipient__email", "title")
    list_filter = ("read",)


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ("member", "platform", "device_name", "is_active", "updated_at")
    search_fields = ("member__email", "token", "device_name")
    list_filter = ("platform", "is_active")

