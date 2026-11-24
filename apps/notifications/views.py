"""Notification centre endpoints."""

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications import services
from apps.notifications.models import Notification
from apps.notifications.serializers import (
    DeviceRegisterSerializer,
    DeviceUnregisterSerializer,
    NotificationSerializer,
)


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


class DeviceRegisterView(APIView):
    """POST /devices/register — Register FCM/APNs device token."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DeviceRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = services.register_device(
            member=request.user,
            token=serializer.validated_data["token"],
            platform=serializer.validated_data.get("platform", "android"),
            device_name=serializer.validated_data.get("device_name", ""),
        )
        return Response({
            "registered": True,
            "device_id": str(device.id),
            "platform": device.platform,
        })


class DeviceUnregisterView(APIView):
    """POST /devices/unregister — Unregister FCM/APNs device token on sign out."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DeviceUnregisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.unregister_device(token=serializer.validated_data["token"])
        return Response({"unregistered": True})

