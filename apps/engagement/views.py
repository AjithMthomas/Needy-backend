"""engagement views — karma wallet, perks, play & earn, community board, radar."""

from __future__ import annotations

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Member
from apps.core.exceptions import BusinessRuleError
from apps.engagement import services
from apps.engagement.models import BoardIdea, PartnerPerk, PlayChallenge, RadarPing
from apps.engagement.serializers import (
    BoardIdeaSerializer,
    IdeaCreateSerializer,
    KarmaEntrySerializer,
    PartnerPerkSerializer,
    PlayChallengeSerializer,
)
from apps.posts.models import Task


def _err(exc: BusinessRuleError):
    return Response(
        {"detail": str(exc.detail), "code": exc.default_code},
        status=exc.status_code,
    )


class KarmaView(APIView):
    """GET /karma — balance + last 50 ledger entries."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        statement = services.karma_statement(request.user)
        return Response(
            {
                "balance": statement["balance"],
                "entries": KarmaEntrySerializer(statement["entries"], many=True).data,
            }
        )


class PerkListView(generics.ListAPIView):
    """GET /perks — partner offers with my claim state."""

    serializer_class = PartnerPerkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PartnerPerk.objects.filter(is_active=True)

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "member": self.request.user}


class PerkClaimView(APIView):
    """POST /perks/{id}/claim — spends karma, returns the voucher code."""

    permission_classes = [IsAuthenticated]

    def post(self, request, perk_id):
        perk = get_object_or_404(PartnerPerk, id=perk_id, is_active=True)
        try:
            claim = services.claim_perk(request.user, perk)
        except BusinessRuleError as exc:
            return _err(exc)
        return Response(
            {
                "id": str(claim.id),
                "code": claim.code,
                "expires_at": claim.expires_at,
                "merchant": perk.merchant,
                "title": perk.title,
                "karma_spent": perk.cost_karma,
            },
            status=status.HTTP_201_CREATED,
        )


class ChallengeListView(generics.ListAPIView):
    """GET /challenges — Play & Earn catalog with played-today state."""

    serializer_class = PlayChallengeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PlayChallenge.objects.filter(is_active=True)

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "member": self.request.user}


class ChallengePlayView(APIView):
    """POST /challenges/{id}/play {score} — once per day, server-verified."""

    permission_classes = [IsAuthenticated]

    def post(self, request, challenge_id):
        challenge = get_object_or_404(PlayChallenge, id=challenge_id, is_active=True)
        score = (request.data or {}).get("score")
        if score is None:
            return Response(
                {"detail": "score required", "code": "invalid"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            score = int(score)
        except (TypeError, ValueError):
            return Response(
                {"detail": "score must be an integer", "code": "invalid"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = services.record_play(request.user, challenge, score)
        except BusinessRuleError as exc:
            return _err(exc)
        return Response(result)


class IdeaListView(generics.ListAPIView):
    """GET /community/ideas — sorted by upvotes (mock parity)."""

    serializer_class = BoardIdeaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BoardIdea.objects.select_related("author").order_by("-upvotes", "-created_at")

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "member": self.request.user}


class IdeaCreateView(APIView):
    """POST /community/ideas — publishes + awards idea karma."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = IdeaCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        idea = services.submit_idea(
            request.user,
            data["title"],
            data["details"],
            data["tag"],
        )
        return Response(
            BoardIdeaSerializer(idea, context={"member": request.user}).data,
            status=status.HTTP_201_CREATED,
        )


class IdeaVoteView(APIView):
    """POST /community/ideas/{id}/vote — toggle upvote."""

    permission_classes = [IsAuthenticated]

    def post(self, request, idea_id):
        idea = get_object_or_404(BoardIdea, id=idea_id)
        return Response(services.toggle_idea_vote(idea, request.user))


class RadarView(APIView):
    """GET /radar — the Bored Radar Stage-2 payload:

    zone aggregates (last 30 min pings), available-now + guardian counts,
    and live SOS posts. Zones stay coarse (no member locations) by design.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        cutoff = timezone.now() - timezone.timedelta(minutes=30)

        zones: dict[str, dict] = {}
        for ping in RadarPing.objects.filter(created_at__gte=cutoff).order_by("created_at"):
            zone = zones.setdefault(
                ping.zone,
                {"zone": ping.zone, "free": 0, "tasks": 0, "tea": 0},
            )
            zone["free"] += 1
            if ping.up_for == "tasks":
                zone["tasks"] += 1
            elif ping.up_for == "tea":
                zone["tea"] += 1

        counts = Member.objects.aggregate(
            available_now=Q_count("available_now"),
            guardians=Q_count("is_guardian"),
        )
        sos = Task.objects.filter(
            kind=Task.PostKind.EMERGENCY,
            status=Task.TaskStatus.PUBLISHED,
            quarantined=False,
            created_at__gte=timezone.now() - timezone.timedelta(hours=6),
        ).order_by("-created_at")[:10]

        return Response(
            {
                "zones": list(zones.values()),
                "available_now_count": counts["available_now"],
                "guardian_count": counts["guardians"],
                "sos": [
                    {
                        "id": str(t.id),
                        "title": t.title,
                        "area": t.area,
                        "created_at": t.created_at,
                    }
                    for t in sos
                ],
            }
        )


def Q_count(field: str):
    """Count rows where a boolean field is True, as an aggregate kwarg."""
    from django.db.models import Count

    return Count("id", filter=Q(**{field: True}))
