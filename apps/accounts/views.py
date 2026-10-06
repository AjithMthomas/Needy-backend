"""accounts views — auth, profile, toggles.

Views are thin: validate input, call services, shape the response.
Business rules live in services.py (STANDARDS.md rule 3).
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView  # noqa: F401 (re-exported in urls)

from apps.accounts import services
from apps.accounts.auth_serializers import OtpRequestSerializer, OtpVerifySerializer
from apps.accounts.models import Member
from apps.accounts.serializers import (
    MemberPublicSerializer,
    MemberSelfSerializer,
    ProfileUpdateSerializer,
    SignupProfileSerializer,
)
from apps.core.exceptions import BusinessRuleError


def _tokens_for(member: Member) -> dict:
    refresh = RefreshToken.for_user(member)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class OtpRequestView(APIView):
    """POST /auth/otp/request  {email} → {sent, cooldown_seconds}.

    Always returns 200 for well-formed requests; throttling + cooldowns
    handle abuse. No account enumeration.
    """

    permission_classes = []

    def post(self, request):
        serializer = OtpRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.request_otp(serializer.validated_data["email"])
        return Response(
            {"sent": result.sent, "cooldown_seconds": result.cooldown_seconds},
        )


class OtpVerifyView(APIView):
    """POST /auth/otp/verify  {email, code} → tokens + member."""

    permission_classes = []

    def post(self, request):
        serializer = OtpVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            member = services.verify_otp(
                email=serializer.validated_data["email"],
                code=serializer.validated_data["code"],
            )
        except BusinessRuleError as exc:
            return Response(
                {"detail": str(exc.detail), "code": "otp_invalid"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                **_tokens_for(member),
                "member": MemberSelfSerializer(member).data,
                "profile_completed": member.profile_completed,
            }
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MemberSelfSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(MemberSelfSerializer(request.user).data)


class CompleteProfileView(APIView):
    """POST /me/complete-profile — onboarding step after first OTP verify."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SignupProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = serializer.save(request.user)
        member.profile_completed = True
        member.save(update_fields=["profile_completed"])
        return Response(
            {
                **_tokens_for(member),  # fresh tokens embedding updated claims
                "member": MemberSelfSerializer(member).data,
            }
        )


class ToggleAvailableNowView(APIView):
    """POST /me/toggle-available — Available-Now roster toggle."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.available_now = not request.user.available_now
        request.user.save(update_fields=["available_now"])
        return Response({"available_now": request.user.available_now})


class ToggleGuardianView(APIView):
    """POST /me/toggle-guardian — Guardian Shield toggle."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.is_guardian = not request.user.is_guardian
        request.user.save(update_fields=["is_guardian"])
        from apps.notifications.services import notify

        notify(
            recipient=request.user,
            title="Guardian Shield active 🛡️"
            if request.user.is_guardian
            else "Guardian Shield paused",
            body=(
                "You now receive priority SOS dispatches in Madiwala."
                if request.user.is_guardian
                else "You can re-enable any time from your profile."
            ),
        )
        return Response({"is_guardian": request.user.is_guardian})


class MyApplicationsView(APIView):
    """GET /me/applications — every application I have placed."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.posts.models import Application

        apps = (
            Application.objects.filter(member=request.user)
            .select_related("task")
            .order_by("-created_at")
        )
        from apps.posts.serializers import ApplicationSerializer

        return Response(ApplicationSerializer(apps, many=True).data)


class MemberListView(APIView):
    """GET /members — the emergency roster: guardians + available-now
    members first (mock parity with availableHelpers)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        members = Member.objects.filter(is_active=True).order_by(
            "-is_guardian", "-available_now", "-rating"
        )
        return Response(MemberPublicSerializer(members, many=True).data)


class PublicMemberView(APIView):
    """GET /members/{id} — public projection only."""

    permission_classes = [IsAuthenticated]

    def get(self, request, member_id):
        member = Member.objects.filter(id=member_id).first()
        if member is None:
            return Response(
                {"detail": "Member not found.", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(MemberPublicSerializer(member).data)
