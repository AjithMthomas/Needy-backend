from rest_framework import serializers

from apps.chat.models import ChatRoom, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.public_name", read_only=True)
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "seq", "sender", "sender_name", "body", "is_mine", "created_at"]

    def get_is_mine(self, obj) -> bool:
        request = self.context.get("request")
        return bool(request and request.user and request.user.id == obj.sender_id)


class ChatRoomSerializer(serializers.ModelSerializer):
    task_id = serializers.UUIDField(source="application.task_id")
    task_title = serializers.CharField(source="application.task.title")
    # The Flutter UI keys chat by application id — expose it for parity.
    application_id = serializers.UUIDField(source="application.id")
    application_status = serializers.CharField(source="application.status")
    counterpart = serializers.SerializerMethodField()
    unread_for_me = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            "id", "application_id", "task_id", "task_title",
            "application_status", "counterpart", "unread_for_me",
            "last_message_at", "created_at",
        ]

    def get_counterpart(self, obj) -> dict:
        member = obj.counterpart(self.context["request"].user)
        return {
            "id": str(member.id),
            "public_name": member.public_name,
            "photo_url": member.photo_url,
        }

    def get_unread_for_me(self, obj) -> int:
        return obj.unread_for(self.context["request"].user)
