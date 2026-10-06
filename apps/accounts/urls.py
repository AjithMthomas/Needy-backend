"""accounts URL routes (mounted under /api/v1/)."""

from django.urls import path

from apps.accounts import views

urlpatterns = [
    path("auth/otp/request", views.OtpRequestView.as_view(), name="otp-request"),
    path("auth/otp/verify", views.OtpVerifyView.as_view(), name="otp-verify"),
    path("auth/refresh", views.TokenRefreshView.as_view(), name="token-refresh"),
    path("me", views.MeView.as_view(), name="me"),
    path("me/complete-profile", views.CompleteProfileView.as_view(), name="complete-profile"),
    path("me/toggle-available", views.ToggleAvailableNowView.as_view(), name="toggle-available"),
    path("me/toggle-guardian", views.ToggleGuardianView.as_view(), name="toggle-guardian"),
    path("me/applications", views.MyApplicationsView.as_view(), name="my-applications"),
    path("members", views.MemberListView.as_view(), name="member-list"),
    path("members/<uuid:member_id>", views.PublicMemberView.as_view(), name="member-public"),
]
