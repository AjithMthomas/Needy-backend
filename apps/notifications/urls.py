"""notifications URL routes (mounted under /api/v1/)."""

from django.urls import path

from apps.notifications import views

urlpatterns = [
    path("notifications", views.NotificationListView.as_view(), name="notifications"),
    path("notifications/unread-count", views.UnreadCountView.as_view(), name="notif-unread"),
    path("notifications/read-all", views.MarkAllReadView.as_view(), name="notif-read-all"),
]
