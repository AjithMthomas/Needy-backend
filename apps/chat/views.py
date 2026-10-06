"""chat views — polling-first chat API.

GET /chat/rooms                            → my rooms (with unread counts)
GET /chat/rooms/{id}/messages?since_seq=N  → only messages after N
POST /chat/rooms/{id}/send  {body}
POST /chat/rooms/{id}/read
"""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat.models import ChatRoom
from apps.chat.serializers import ChatRoomSerializer, MessageSerializer
from apps.chat.services import mark_read, send_message
from apps.core.exceptions import BusinessRuleError


def _room_for(request, room_id) -> ChatRoom:
    room = get_object_or_404(
        ChatRoom.objects.select_related("application__task"),
        id=room_id,
    )
    if not room.is_participant(request.user):
        raise PermissionDenied("Not your room.")
    return room


class ChatRoomListView(generics.ListAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        member = self.request.user
        return ChatRoom.objects.filter(Q(creator=member) | Q(applicant=member)).select_related(
            "application__task", "creator", "applicant"
        )


class MessageListView(generics.ListAPIView):
    """Incremental fetch: pass ?since_seq=LAST to receive only newer messages."""

    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        room = _room_for(self.request, self.kwargs["room_id"])
        qs = room.messages.select_related("sender")
        since = self.request.query_params.get("since_seq")
        if since:
            try:
                qs = qs.filter(seq__gt=int(since))
            except ValueError:
                pass
        return qs


class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, room_id):
        room = _room_for(request, room_id)
        body = (request.data or {}).get("body", "")
        try:
            message = send_message(room, request.user, body)
        except BusinessRuleError as exc:
            return Response(
                {"detail": str(exc.detail), "code": exc.default_code},
                status=exc.status_code,
            )
        return Response(MessageSerializer(message, context={"request": request}).data)


class MarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, room_id):
        room = _room_for(request, room_id)
        mark_read(room, request.user)
        return Response({"ok": True})
