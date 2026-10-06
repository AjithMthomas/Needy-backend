"""Notification centre endpoints."""

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications import services
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    """GET /notifications?unread=1 — newest first, cursor-paginated."""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Notification.objects.filter(recipient=self.request.user)
        if self.request.query_params.get("unread") == "1":
            qs = qs.filter(read=False)
        return qs


class UnreadCountView(APIView):
    """GET /notifications/unread-count — cheap poll target."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({"unread": services.unread_count(request.user)})


class MarkAllReadView(APIView):
    """POST /notifications/read-all."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        services.mark_all_read(request.user)
        return Response({"ok": True})
