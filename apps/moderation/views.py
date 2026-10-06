"""moderation views — one-tap report (auto-quarantine) + block/unblock."""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Member
from apps.moderation import services
from apps.moderation.serializers import ReportCreateSerializer


class ReportView(APIView):
    """POST /reports — file a report; posts are auto-quarantined."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        task = None
        if data.get("task_id"):
            from apps.posts.models import Task

            task = Task.objects.filter(id=data["task_id"]).first()
        target_member = None
        if data.get("member_id"):
            target_member = Member.objects.filter(id=data["member_id"]).first()

        if task is None and target_member is None:
            return Response(
                {"detail": "Provide task_id or member_id.", "code": "invalid"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        report = services.file_report(
            request.user,
            task=task,
            target_member=target_member,
            reason=data["reason"],
            details=data["details"],
        )
        return Response(
            {
                "id": str(report.id),
                "status": "received",
                "message": "Our safety team will review your report within 24 hours.",
                "quarantined": task is not None,
            },
            status=status.HTTP_201_CREATED,
        )


class BlockView(APIView):
    """POST /block {member_id} | POST /unblock {member_id}."""

    permission_classes = [IsAuthenticated]

    def post(self, request, action):
        member_id = (request.data or {}).get("member_id")
        if not member_id:
            return Response(
                {"detail": "member_id required", "code": "invalid"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        target = get_object_or_404(Member, id=member_id)
        try:
            if action == "block":
                result = services.block_member(request.user, target)
            elif action == "unblock":
                result = services.unblock_member(request.user, target)
            else:
                return Response(
                    {"detail": "Unknown action.", "code": "not_found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        except Exception as exc:  # BusinessRuleError
            from apps.core.exceptions import BusinessRuleError

            if isinstance(exc, BusinessRuleError):
                return Response(
                    {"detail": str(exc.detail), "code": exc.default_code},
                    status=exc.status_code,
                )
            raise
        return Response(result)
