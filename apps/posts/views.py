"""posts views — thin controllers over services."""

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import BusinessRuleError
from apps.posts import services
from apps.posts.models import Application, Repost, SavedPost, Task
from apps.posts.serializers import (
    ApplicationSerializer,
    TaskCreateSerializer,
    TaskDetailSerializer,
    TaskListSerializer,
)


class FeedView(generics.ListAPIView):
    """GET /posts — the whole marketplace feed, filterable + cursor-paginated.

    Special query params: saved=1 (my saved), mine=1 (my posts).
    POST /posts also creates (REST-idiomatic alias of /posts/create).
    """

    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return services.feed_queryset(self.request.user, params=self.request.query_params)

    def post(self, request, *args, **kwargs):
        return TaskCreateView().post(request, *args, **kwargs)


class TaskDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        return Response(TaskDetailSerializer(task, context={"request": request}).data)


class TaskCreateView(APIView):
    """POST /posts — every create flow lands here (wizard, SOS, gig, room, team)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save(creator=request.user)
        return Response(
            TaskDetailSerializer(task, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class TaskActionView(APIView):
    """POST /posts/{id}/start|complete|cancel."""

    permission_classes = [IsAuthenticated]
    ACTIONS = {
        "start": services.start_task,
        "complete": services.complete_task,
        "cancel": services.cancel_task,
    }

    def post(self, request, task_id, action):
        task = get_object_or_404(Task, id=task_id)
        handler = self.ACTIONS.get(action)
        if handler is None:
            return Response(
                {"detail": "Unknown action.", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            handler(task, request.user)
        except BusinessRuleError as exc:
            return Response(
                {"detail": str(exc.detail), "code": exc.default_code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(TaskDetailSerializer(task, context={"request": request}).data)


class ApplyView(APIView):
    """POST /posts/{id}/apply  {intro_message}."""

    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        intro = (request.data or {}).get("intro_message", "")
        try:
            application = services.apply_to_task(task, request.user, intro)
        except BusinessRuleError as exc:
            return Response(
                {"detail": str(exc.detail), "code": exc.default_code},
                status=exc.status_code,
            )
        return Response(
            ApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED,
        )


class ApplicationsForTaskView(APIView):
    """GET /posts/{id}/applications — creator only."""

    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        if task.creator_id != request.user.id:
            return Response(
                {"detail": "Only the creator can view applicants.", "code": "forbidden"},
                status=status.HTTP_403_FORBIDDEN,
            )
        apps = task.applications.select_related("member").all()
        return Response(ApplicationSerializer(apps, many=True).data)


class ApplicationActionView(APIView):
    """POST /applications/{id}/withdraw (applicant) | /select (creator)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, application_id, action):
        application = get_object_or_404(Application, id=application_id)
        try:
            if action == "withdraw":
                services.withdraw_application(application, request.user)
            elif action == "select":
                services.select_applicant(application, request.user)
            else:
                return Response(
                    {"detail": "Unknown action.", "code": "not_found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        except BusinessRuleError as exc:
            return Response(
                {"detail": str(exc.detail), "code": exc.default_code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(ApplicationSerializer(application).data)


class SaveToggleView(APIView):
    """POST /posts/{id}/save — idempotent toggle."""

    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        saved = SavedPost.objects.filter(member=request.user, task=task).first()
        if saved:
            saved.delete()
            return Response({"saved": False})
        SavedPost.objects.create(member=request.user, task=task)
        return Response({"saved": True})


class RepostToggleView(APIView):
    """POST /posts/{id}/repost — idempotent toggle."""

    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        repost = Repost.objects.filter(member=request.user, task=task).first()
        if repost:
            repost.delete()
            return Response({"reposted": False})
        Repost.objects.create(member=request.user, task=task)
        return Response({"reposted": True})


class RateView(APIView):
    """POST /posts/{id}/rate {stars, note} — mutual post-session review.

    The counterparty (selected helper, or the creator when rated by the
    helper) receives the stars; their trust stats update server-side.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        from django.db.models import Avg

        from apps.accounts.models import Member
        from apps.posts.models import Rating

        task = get_object_or_404(Task, id=task_id)
        stars = (request.data or {}).get("stars")
        note = (request.data or {}).get("note", "")
        if stars is None:
            return Response(
                {"detail": "stars required", "code": "invalid"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            stars = float(stars)
        except (TypeError, ValueError):
            return Response(
                {"detail": "stars must be a number", "code": "invalid"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        stars = max(0.5, min(5.0, stars))

        counterparty_id = (
            task.applications.filter(status=Application.ApplicationStatus.SELECTED)
            .values_list("member_id", flat=True)
            .first()
        )
        if counterparty_id is None:
            counterparty_id = task.creator_id

        if request.user.id == counterparty_id:
            return Response(
                {"detail": "Cannot rate yourself.", "code": "invalid"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        Rating.objects.create(
            task=task,
            rater=request.user,
            ratee_id=counterparty_id,
            stars=stars,
            note=note,
        )
        agg = Rating.objects.filter(ratee_id=counterparty_id).aggregate(
            avg=Avg("stars"),
            n=models_count(),
        )
        Member.objects.filter(pk=counterparty_id).update(
            rating=round(agg["avg"] or stars, 2),
            rating_count=agg["n"],
        )
        return Response({"ok": True, "stars": stars})


def models_count():
    from django.db.models import Count

    return Count("id")
