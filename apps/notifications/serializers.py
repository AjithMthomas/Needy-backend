from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "title", "body", "read", "target", "created_at"]


class DeviceRegisterSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)
    platform = serializers.ChoiceField(
        choices=["android", "ios", "web"],
        default="android",
    )
    device_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default="",
    )


class DeviceUnregisterSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255)

