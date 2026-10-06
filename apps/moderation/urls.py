"""moderation URL routes (mounted under /api/v1/)."""

from django.urls import path

from apps.moderation import views

urlpatterns = [
    path("reports", views.ReportView.as_view(), name="report"),
    path("block/<str:action>", views.BlockView.as_view(), name="block-action"),
]
