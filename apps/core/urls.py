"""core URL routes: health, config; app routers mount below."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.core.health import ConfigView, HealthView
from apps.core.uploads import UploadView

router = DefaultRouter()

urlpatterns = [
    path("health", HealthView.as_view(), name="health"),
    path("config", ConfigView.as_view(), name="config"),
    path("uploads", UploadView.as_view(), name="uploads"),
    path("", include("apps.accounts.urls")),
    path("", include("apps.posts.urls")),
    path("", include("apps.chat.urls")),
    path("", include("apps.auctions.urls")),
    path("", include("apps.engagement.urls")),
    path("", include("apps.moderation.urls")),
    path("", include("apps.notifications.urls")),
]
