"""chat URL routes (mounted under /api/v1/)."""

from django.urls import path

from apps.chat import views

urlpatterns = [
    path("chat/rooms", views.ChatRoomListView.as_view(), name="chat-rooms"),
    path(
        "chat/rooms/<uuid:room_id>/messages", views.MessageListView.as_view(), name="chat-messages"
    ),
    path("chat/rooms/<uuid:room_id>/send", views.SendMessageView.as_view(), name="chat-send"),
    path("chat/rooms/<uuid:room_id>/read", views.MarkReadView.as_view(), name="chat-read"),
]
